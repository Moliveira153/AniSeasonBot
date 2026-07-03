"""FSM storage with Redis and in-memory fallback."""

from __future__ import annotations

from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from app.config import Settings, get_settings
from app.utils.logging import get_logger
from app.utils.redis_client import create_fsm_redis

logger = get_logger(__name__)


async def create_storage(settings: Settings | None = None) -> BaseStorage:
    """Try Redis FSM storage; fall back to memory if Redis is unreachable."""
    settings = settings or get_settings()
    redis = create_fsm_redis(settings)
    try:
        await redis.ping()
        logger.info("fsm_storage_redis_ok")
        return RedisStorage(redis=redis)
    except Exception as exc:
        logger.warning("fsm_storage_redis_failed_using_memory", error=str(exc))
        try:
            await redis.aclose()
        except Exception:
            pass
        return MemoryStorage()