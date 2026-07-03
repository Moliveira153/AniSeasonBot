"""Anime events and notification delivery models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, TimestampMixin


class AnimeEvent(Base, TimestampMixin):
    """Detected change in anime data (shared across users)."""

    __tablename__ = "anime_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey("animes.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    episode: Mapped[int | None] = mapped_column(Integer)
    old_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    new_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)

    anime: Mapped["Anime"] = relationship(back_populates="events")  # noqa: F821
    deliveries: Mapped[list["NotificationDelivery"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_anime_events_anime_id", "anime_id"),
        Index("ix_anime_events_event_type", "event_type"),
    )


class NotificationDelivery(Base, TimestampMixin):
    """Per-user notification delivery record for idempotency."""

    __tablename__ = "notification_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    anime_id: Mapped[int] = mapped_column(ForeignKey("animes.id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("anime_events.id", ondelete="SET NULL"))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    episode: Mapped[int | None] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    user: Mapped["User"] = relationship(back_populates="notifications")  # noqa: F821
    event: Mapped["AnimeEvent | None"] = relationship(back_populates="deliveries")

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_notification_idempotency"),
        Index("ix_notification_deliveries_user_id", "user_id"),
        Index("ix_notification_deliveries_status", "status"),
    )