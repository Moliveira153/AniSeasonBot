"""ARQ worker settings and cron scheduler."""

from __future__ import annotations

from arq import cron
from arq.connections import RedisSettings

from app.config import get_settings
from app.workers.tasks import (
    health_check,
    retry_failed_notifications,
    send_notifications,
    shutdown,
    startup,
    sync_tracked_animes,
)


class WorkerSettings:
    """ARQ worker configuration."""

    @staticmethod
    def redis_settings() -> RedisSettings:
        settings = get_settings()
        return RedisSettings.from_dsn(settings.redis_url)

    functions = [
        sync_tracked_animes,
        send_notifications,
        retry_failed_notifications,
        health_check,
    ]

    on_startup = startup
    on_shutdown = shutdown

    @staticmethod
    def cron_jobs():
        settings = get_settings()
        interval = settings.notification_check_interval
        return [
            cron(sync_tracked_animes, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}, run_at_startup=True),
            cron(send_notifications, second={0, 30}),
            cron(retry_failed_notifications, hour={0, 6, 12, 18}, minute=0),
            cron(health_check, minute={0, 30}),
        ]


# ARQ expects module-level attributes
redis_settings = WorkerSettings.redis_settings()
functions = WorkerSettings.functions
on_startup = WorkerSettings.on_startup
on_shutdown = WorkerSettings.on_shutdown
cron_jobs = WorkerSettings.cron_jobs()