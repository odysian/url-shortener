"""
Redis client configuration for caching.

Redis will store: short_code -> original_url mappings
Goal: Sub-millisecond redirect lookups
"""

import redis

from db_config import settings

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)


def get_redis():
    """
    Dependency function for FastAPI routes.

    Returns the Redis client.
    Doesn't need try/finally like database because Redis
    client manages its own connection pool.

    Usage:
        def my_route(redis: redis.Redis = Depends(get_redis)):
    """
    return redis_client


def test_redis_connection():
    """
    Test Redis connection on startup.
    Raises exception if Redis is unreachable.
    """
    try:
        redis_client.ping()
        return True
    except redis.ConnectionError as e:
        raise RuntimeError(f"Could not connect to Redis: {e}") from e
