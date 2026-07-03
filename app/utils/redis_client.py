"""Redis connection helpers with TLS support for Render."""

from __future__ import annotations

import ssl

from redis.asyncio import Redis

from app.config import Settings, get_settings


def _base_kwargs(settings: Settings) -> dict:
    kwargs: dict = {
        "socket_connect_timeout": 10,
        "socket_timeout": 10,
        "retry_on_timeout": True,
        "health_check_interval": 30,
    }
    if settings.redis_use_ssl:
        kwargs["ssl_cert_reqs"] = ssl.CERT_NONE
    return kwargs


def create_redis(settings: Settings | None = None) -> Redis:
    """General-purpose Redis client (cache, locks)."""
    settings = settings or get_settings()
    return Redis.from_url(
        settings.redis_url,
        decode_responses=False,
        **_base_kwargs(settings),
    )


def create_fsm_redis(settings: Settings | None = None) -> Redis:
    """Redis client for Aiogram FSM — MUST use decode_responses=True."""
    settings = settings or get_settings()
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        **_base_kwargs(settings),
    )