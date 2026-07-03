"""Embedded background worker for Render free tier (single web process)."""

from __future__ import annotations

import asyncio
from typing import Any

from aiogram import Bot

from app.config import Settings, get_settings
from app.database.session import get_session_factory
from app.services.notification_service import NotificationService
from app.utils.logging import get_logger
from app.workers.tasks import send_notifications, sync_tracked_animes

logger = get_logger(__name__)


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
        logger.info("embedded_worker_started")

    async def stop(self) -> None:
        self._stop.set()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("embedded_worker_stopped")

    async def _sync_loop(self) -> None:
        interval = max(60, self.settings.notification_check_interval)
        ctx: dict[str, Any] = {"redis": None}
        while not self._stop.is_set():
            try:
                from app.utils.redis_client import create_redis

                redis = create_redis(self.settings)
                ctx["redis"] = redis
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
        interval = 30
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