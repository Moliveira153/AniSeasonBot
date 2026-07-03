"""ARQ worker tasks for sync and notifications."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from redis.asyncio import Redis

from app.config import get_settings
from app.database.repositories.anime_repo import AnimeRepository
from app.database.session import get_session_factory
from app.services.notification_service import NotificationService
from app.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

SYNC_LOCK_KEY = "lock:anime_sync"
SYNC_LOCK_TTL = 120


async def sync_tracked_animes(ctx: dict[str, Any]) -> dict[str, int]:
    """Sync all tracked animes due for update."""
    settings = get_settings()
    redis: Redis = ctx["redis"]
    lock = await redis.set(SYNC_LOCK_KEY, "1", nx=True, ex=SYNC_LOCK_TTL)
    if not lock:
        logger.info("sync_skipped_lock_held")
        return {"synced": 0, "skipped": True}

    try:
        factory = get_session_factory()
        synced = 0
        events_created = 0

        async with factory() as session:
            anime_repo = AnimeRepository(session)
            animes = await anime_repo.get_animes_due_for_sync(limit=30)

            for anime in animes:
                try:
                    notif_service = NotificationService(session)
                    count = await notif_service.process_anime_sync(anime.anilist_id)
                    events_created += count
                    synced += 1
                except Exception as exc:
                    logger.error("sync_anime_failed", anilist_id=anime.anilist_id, error=str(exc))
                    await anime_repo.record_sync_failure(anime)

            await session.commit()

        logger.info("sync_completed", synced=synced, events=events_created)
        return {"synced": synced, "events": events_created}
    finally:
        await redis.delete(SYNC_LOCK_KEY)


async def send_notifications(ctx: dict[str, Any]) -> dict[str, int]:
    """Send pending notification deliveries."""
    settings = get_settings()
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    factory = get_session_factory()

    try:
        async with factory() as session:
            notif_service = NotificationService(session, bot=bot)
            sent = await notif_service.send_pending()
            await session.commit()
        logger.info("notifications_sent", count=sent)
        return {"sent": sent}
    finally:
        await bot.session.close()


async def retry_failed_notifications(ctx: dict[str, Any]) -> dict[str, int]:
    """Retry failed notification deliveries."""
    settings = get_settings()
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    factory = get_session_factory()

    try:
        from app.database.repositories.notification_repo import NotificationRepository
        from sqlalchemy import update
        from app.database.models.event import NotificationDelivery

        async with factory() as session:
            repo = NotificationRepository(session)
            failed = await repo.get_failed_deliveries(limit=50)
            for delivery in failed:
                await session.execute(
                    update(NotificationDelivery)
                    .where(NotificationDelivery.id == delivery.id)
                    .values(status="pending")
                )
            await session.commit()

            notif_service = NotificationService(session, bot=bot)
            sent = await notif_service.send_pending()
            await session.commit()

        return {"retried": len(failed), "sent": sent}
    finally:
        await bot.session.close()


async def health_check(ctx: dict[str, Any]) -> dict[str, str]:
    """Worker health check."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("worker_started")


async def shutdown(ctx: dict[str, Any]) -> None:
    from app.database.session import dispose_engine

    await dispose_engine()
    logger.info("worker_stopped")