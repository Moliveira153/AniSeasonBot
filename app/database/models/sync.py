"""Sync cache model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, TimestampMixin


class SyncCache(Base, TimestampMixin):
    __tablename__ = "sync_cache"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    resource: Mapped[str] = mapped_column(String(512), nullable=False)
    etag: Mapped[str | None] = mapped_column(String(128))
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_state: Mapped[str] = mapped_column(String(32), default="ok", nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "resource", name="uq_sync_cache_source_resource"),
        Index("ix_sync_cache_next_sync_at", "next_sync_at"),
    )