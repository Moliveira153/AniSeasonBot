"""Tracking (user-anime follow) model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, TimestampMixin


class Tracking(Base, TimestampMixin):
    __tablename__ = "trackings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    anime_id: Mapped[int] = mapped_column(ForeignKey("animes.id", ondelete="CASCADE"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_watched_episode: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    personal_status: Mapped[str] = mapped_column(String(32), default="watching", nullable=False)
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    user: Mapped["User"] = relationship(back_populates="trackings")  # noqa: F821
    anime: Mapped["Anime"] = relationship(back_populates="trackings")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("user_id", "anime_id", name="uq_trackings_user_anime"),
        Index("ix_trackings_user_id", "user_id"),
        Index("ix_trackings_anime_id", "anime_id"),
    )