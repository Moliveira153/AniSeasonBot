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
    """Create FSM storage. On Render uses memory (single instance, more reliable)."""
    settings = settings or get_settings()

    # Render free = 1 instância; memória evita travamentos do Redis FSM
    if settings.is_render:
        logger.info("fsm_storage_memory_render")
        return MemoryStorage()

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