"""Embedded background worker for Render free tier (single web process)."""

from __future__ import annotations

import asyncio
from typing import Any

from aiogram import Bot

from app.config import Settings, get_settings
from app.database.session import get_session_factory
from app.services.notification_service import NotificationService
from app.utils.logging import get_logger
from app.workers.tasks import sync_tracked_animes

logger = get_logger(__name__)

# Aguarda o bot ficar responsivo antes de consumir DB/Redis
STARTUP_DELAY_SECONDS = 120


class EmbeddedWorker:
    """Runs sync + notification loops inside the web process."""

    def __init__(self, bot: Bot, settings: Settings | None = None) -> None:
        self.bot = bot
        self.settings = settings or get_settings()
        self._stop = asyncio.Event()
        self._tasks: list[asyncio.Task[Any]] = []

    async def start(self) -> None:
        self._tasks = [
            asyncio.create_task(self._sync_loop(), name="embedded-sync"),
            asyncio.create_task(self._notify_loop(), name="embedded-notify"),
        ]
        logger.info("embedded_worker_scheduled", startup_delay=STARTUP_DELAY_SECONDS)

    async def stop(self) -> None:
        self._stop.set()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("embedded_worker_stopped")

    async def _wait_startup_delay(self) -> None:
        try:
            await asyncio.wait_for(self._stop.wait(), timeout=STARTUP_DELAY_SECONDS)
        except TimeoutError:
            pass

    async def _sync_loop(self) -> None:
        await self._wait_startup_delay()
        interval = max(300, self.settings.notification_check_interval)
        while not self._stop.is_set():
            try:
                from app.utils.redis_client import create_redis

                redis = create_redis(self.settings)
                ctx: dict[str, Any] = {"redis": redis}
                await sync_tracked_animes(ctx)
                await redis.aclose()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("embedded_sync_error", error=str(exc))
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval)
            except TimeoutError:
                pass

    async def _notify_loop(self) -> None:
        await self._wait_startup_delay()
        interval = 60
        while not self._stop.is_set():
            try:
                factory = get_session_factory()
                async with factory() as session:
                    service = NotificationService(session, bot=self.bot)
                    sent = await service.send_pending()
                    await session.commit()
                if sent:
                    logger.info("embedded_notifications_sent", count=sent)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("embedded_notify_error", error=str(exc))
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval)
            except TimeoutError:
                pass