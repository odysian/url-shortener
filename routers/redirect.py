import json
from datetime import datetime, timezone

import redis
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

import db_models
from db_config import SessionLocal, get_db
from redis_config import get_redis

router = APIRouter(tags=["Redirect"])


def record_click(link_id: int):
    """Record a click in the database"""

    db = SessionLocal()
    try:
        click = db_models.Click(link_id=link_id, clicked_at=datetime.now(timezone.utc))
        db.add(click)
        db.commit()
    finally:
        db.close()


@router.get("/{short_code}")
async def redirect_to_url(
    short_code: str,
    background_tasks: BackgroundTasks,
    redis_client: redis.Redis = Depends(get_redis),
    db_session: Session = Depends(get_db),
):
    """Redirect short code to original URL"""

    cache_key = f"link:{short_code}"
    cache_data = redis_client.get(cache_key)

    if cache_data:

        data = json.loads(cache_data)  # type: ignore
        link_id = data["id"]
        url = data["url"]
        expires_at = data["expires_at"]

        if expires_at:
            expires_dt = datetime.fromisoformat(expires_at)
            if expires_dt < datetime.now(timezone.utc):
                redis_client.delete(cache_key)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Link has expired"
                )

        background_tasks.add_task(record_click, link_id)

        return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)  # type: ignore

    link = (
        db_session.query(db_models.Link)
        .filter(db_models.Link.short_code == short_code)
        .first()
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link not found"
        )

    if link.expires_at and link.expires_at < datetime.now(timezone.utc):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link has expired"
        )

    new_cache_data = {
        "id": link.id,
        "url": link.original_url,
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,  # type: ignore
    }

    redis_client.set(cache_key, json.dumps(new_cache_data))  # type: ignore

    background_tasks.add_task(record_click, link.id)  # type: ignore

    return RedirectResponse(url=link.original_url, status_code=status.HTTP_302_FOUND)  # type: ignore
