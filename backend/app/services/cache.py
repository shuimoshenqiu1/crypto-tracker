from __future__ import annotations

import logging

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL, decode_responses=True
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection pool. Call on app shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def get_cached(key: str) -> str | None:
    """Get a cached value by key. Returns None on miss or error."""
    try:
        client = _get_redis()
        return await client.get(key)
    except Exception as e:
        logger.warning(f"Redis get failed for key={key}: {e}")
        return None


async def set_cached(key: str, value: str, ttl: int = 60) -> None:
    """Set a cached value with TTL in seconds."""
    try:
        client = _get_redis()
        await client.set(key, value, ex=ttl)
    except Exception as e:
        logger.warning(f"Redis set failed for key={key}: {e}")


async def delete_cached(key: str) -> None:
    """Delete a cached key."""
    try:
        client = _get_redis()
        await client.delete(key)
    except Exception as e:
        logger.warning(f"Redis delete failed for key={key}: {e}")
