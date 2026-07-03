"""Redis connection helper with TLS support for Render."""

from __future__ import annotations

import ssl

from redis.asyncio import Redis

from app.config import Settings, get_settings


def create_redis(settings: Settings | None = None) -> Redis:
    settings = settings or get_settings()
    kwargs: dict = {"decode_responses": False}
    if settings.redis_use_ssl:
        kwargs["ssl_cert_reqs"] = ssl.CERT_NONE
    return Redis.from_url(settings.redis_url, **kwargs)