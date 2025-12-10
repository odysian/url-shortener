import json

import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import db_models
from db_config import get_db
from dependencies import get_current_user
from models import LinkCreate, LinkResponse
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
        .all()
    )

    return links
