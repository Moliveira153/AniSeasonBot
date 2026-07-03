"""Run Alembic migrations programmatically."""

from __future__ import annotations

import asyncio
from typing import Any

from alembic import command
from alembic.config import Config

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _build_alembic_config() -> Config:
    settings = get_settings()
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    return cfg


def run_migrations() -> None:
    logger.info("running_migrations")
    command.upgrade(_build_alembic_config(), "head")
    logger.info("migrations_complete")


async def run_migrations_async() -> None:
    await asyncio.to_thread(run_migrations)