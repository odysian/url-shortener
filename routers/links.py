import json
from datetime import datetime, timezone
from typing import Optional

import redis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import db_models
from db_config import get_db
from dependencies import get_current_user
from models import LinkCreate, LinkResponse, LinkUpdate
from redis_config import get_redis
from utils.short_code import generate_short_code, is_valid_custom_code

router = APIRouter(prefix="/links", tags=["links"])


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
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

        for i in range(max_attempts):
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


@router.get("", response_model=list[LinkResponse])
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


@router.patch("/{link_id}", response_model=LinkResponse)
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

    update_data = link_data.model_dump(exclude_unset=True)

    if link_data.original_url is not None:
        link.original_url = str(link_data.original_url)  # type: ignore

    if link_data.expires_at is not None:
        link.expires_at = link_data.expires_at  # type: ignore

    if update_data:
        cache_key = f"link:{link.short_code}"
        redis_client.delete(cache_key)

    if link_data.original_url or link_data.expires_at:
        link.updated_at = datetime.now(timezone.utc)  # type: ignore

    db_session.commit()
    db_session.refresh(link)

    return link


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
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
