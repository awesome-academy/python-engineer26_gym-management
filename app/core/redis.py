from __future__ import annotations

from datetime import timedelta

import redis.asyncio as aioredis
import hashlib

from app.core import settings

_redis: aioredis.Redis | None = None

REVOKED_PREFIX = "revoked_token:"


async def init_redis() -> None:
    global _redis
    _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized")
    return _redis


async def revoke_token(token: str, ttl: timedelta) -> None:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    await get_redis().setex(
        f"{REVOKED_PREFIX}{token_hash}", int(ttl.total_seconds()), ""
    )


async def is_token_revoked(token: str) -> bool:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    result = await get_redis().exists(f"{REVOKED_PREFIX}{token_hash}")
    return result == 1
