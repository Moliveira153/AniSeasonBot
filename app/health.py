"""Health and readiness checks."""

from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.config import get_settings
from app.database.session import get_session_factory
from app.utils.redis_client import create_redis


async def check_health() -> dict[str, str]:
    settings = get_settings()
    status = {"database": "unknown", "redis": "unknown", "overall": "unhealthy"}

    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
        status["database"] = "ok"
    except Exception as exc:
        status["database"] = f"error: {exc}"

    try:
        redis = create_redis(settings)
        await redis.ping()
        await redis.aclose()
        status["redis"] = "ok"
    except Exception as exc:
        status["redis"] = f"error: {exc}"

    if status["database"] == "ok" and status["redis"] == "ok":
        status["overall"] = "healthy"
    return status


if __name__ == "__main__":
    print(asyncio.run(check_health()))