import json
from datetime import datetime, timedelta, timezone
from typing import Optional

import redis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import db_models
from db_config import get_db
from dependencies import get_current_user
from models import ClickResponse, ClickStats, LinkCreate, LinkResponse, LinkUpdate
from redis_config import get_redis
from utils.short_code import generate_short_code, is_valid_custom_code

link_router = APIRouter(prefix="/links", tags=["links"])
click_router = APIRouter(prefix="/clicks", tags=["clicks"])


@link_router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
def create_link(
    link_data: LinkCreate,
    db_session: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Create a short link"""
    if link_data.custom_code:
        if not is_valid_custom_code(link_data.custom_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid custom code format",
            )

        existing_link = (
            db_session.query(db_models.Link)
            .filter(db_models.Link.short_code == link_data.custom_code)
            .first()
        )

        if existing_link:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Custom link code already exists",
            )
        short_code = link_data.custom_code
    else:
        max_attempts = 3
        short_code = None

        for _ in range(max_attempts):
            candidate = generate_short_code(6)

            existing = (
                db_session.query(db_models.Link)
                .filter(db_models.Link.short_code == candidate)
                .first()
            )
            if not existing:
                short_code = candidate
                break

        if short_code is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not generate unique short code afer multiple attempts",
            )

    new_link = db_models.Link(
        user_id=current_user.id,
        short_code=short_code,
        original_url=str(link_data.original_url),
        custom_code=link_data.custom_code is not None,
        expires_at=link_data.expires_at,
    )

    db_session.add(new_link)
    db_session.commit()
    db_session.refresh(new_link)

    cache_key = f"link:{short_code}"
    cache_data = {
        "id": new_link.id,
        "url": str(new_link.original_url),
        "expires_at": new_link.expires_at.isoformat() if new_link.expires_at else None,  # type: ignore
    }
    redis_client.set(cache_key, json.dumps(cache_data))

    return new_link


@link_router.get("", response_model=list[LinkResponse])
def get_links(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: db_models.User = Depends(get_current_user),
    db_session: Session = Depends(get_db),
):
    """
    Get all links created by current user

    Returns links ordered by creation date
    """
    links = (
        db_session.query(db_models.Link)
        .filter(db_models.Link.user_id == current_user.id)
        .order_by(db_models.Link.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return links


@click_router.get("/stats", response_model=ClickStats)
def get_click_stats(
    db_session: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Get aggregated click stats per user"""

    cache_key = f"stats:user_{current_user.id}"
    cached_stats = redis_client.get(cache_key)

    if cached_stats:
        stats_dict = json.loads(cached_stats)  # type: ignore
        return stats_dict

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    def user_clicks():
        """Returns a base query for user's clicks"""
        return (
            db_session.query(db_models.Click)
            .join(db_models.Link)
            .filter(db_models.Link.user_id == current_user.id)
        )

    total_clicks = user_clicks().count()
    clicks_today = (
        user_clicks().filter(db_models.Click.clicked_at >= today_start).count()
    )
    clicks_this_week = (
        user_clicks().filter(db_models.Click.clicked_at >= week_start).count()
    )
    clicks_this_month = (
        user_clicks().filter(db_models.Click.clicked_at >= month_start).count()
    )

    referrers_results = (
        db_session.query(
            db_models.Click.referrer, func.count(db_models.Click.id).label("count")
        )
        .join(db_models.Link)
        .filter(
            db_models.Link.user_id == current_user.id,
            db_models.Click.referrer.isnot(None),
        )
        .group_by(db_models.Click.referrer)
        .order_by(func.count(db_models.Click.id).desc())
        .limit(5)
        .all()
    )

    top_referrers = [
        {"referrer": ref, "count": count} for ref, count in referrers_results
    ]

    stats = {
        "total_clicks": total_clicks,
        "clicks_today": clicks_today,
        "clicks_this_week": clicks_this_week,
        "clicks_this_month": clicks_this_month,
        "top_referrers": top_referrers,
    }

    redis_client.setex(cache_key, 300, json.dumps(stats))

    return stats


@link_router.patch("/{link_id}", response_model=LinkResponse)
def update_link(
    link_id: int,
    link_data: LinkUpdate,
    db_session: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Update a link's URL or expiration time"""

    link = db_session.query(db_models.Link).filter(db_models.Link.id == link_id).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link not found"
        )

    if link.user_id != current_user.id:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this link",
        )

    updated = False

    if link_data.original_url is not None:
        link.original_url = str(link_data.original_url)  # type: ignore
        updated = True

    if link_data.expires_at is not None:
        link.expires_at = link_data.expires_at  # type: ignore
        updated = True

    if not updated:
        return link

    link.updated_at = datetime.now(timezone.utc)  # type: ignore

    db_session.commit()
    db_session.refresh(link)

    cache_key = f"link:{link.short_code}"
    cache_data = {
        "id": link.id,
        "url": link.original_url,
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,  # type: ignore
    }

    redis_client.set(cache_key, json.dumps(cache_data))

    return link


@link_router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(
    link_id: int,
    db_session: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Delete a link and invalidate its cache"""

    link = db_session.query(db_models.Link).filter(db_models.Link.id == link_id).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link not found"
        )

    if link.user_id != current_user.id:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this link",
        )

    cache_key = f"link:{link.short_code}"
    redis_client.delete(cache_key)

    db_session.delete(link)
    db_session.commit()


@click_router.get("/{link_id}", response_model=list[ClickResponse])
def get_clicks(
    link_id: int,
    db_session: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """Get all clicks for a link"""
    link = db_session.query(db_models.Link).filter(db_models.Link.id == link_id).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Links not found"
        )

    if link.user_id != current_user.id:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this link",
        )

    clicks = link.clicks

    return clicks
