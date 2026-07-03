"""Anime model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, TimestampMixin


class Anime(Base, TimestampMixin):
    __tablename__ = "animes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    anilist_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    mal_id: Mapped[int | None] = mapped_column(Integer, index=True)
    title_romaji: Mapped[str | None] = mapped_column(String(512))
    title_english: Mapped[str | None] = mapped_column(String(512))
    title_native: Mapped[str | None] = mapped_column(String(512))
    synonyms: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(32))
    format: Mapped[str | None] = mapped_column(String(32))
    season: Mapped[str | None] = mapped_column(String(16))
    season_year: Mapped[int | None] = mapped_column(Integer)
    episodes: Mapped[int | None] = mapped_column(Integer)
    duration: Mapped[int | None] = mapped_column(Integer)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_episode: Mapped[int | None] = mapped_column(Integer)
    next_airing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    genres: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    studios: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    producers: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    cover_image: Mapped[str | None] = mapped_column(String(1024))
    banner_image: Mapped[str | None] = mapped_column(String(1024))
    trailer_url: Mapped[str | None] = mapped_column(String(1024))
    trailer_site: Mapped[str | None] = mapped_column(String(32))
    site_url: Mapped[str | None] = mapped_column(String(1024))
    is_adult: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    average_score: Mapped[int | None] = mapped_column(Integer)
    popularity: Mapped[int | None] = mapped_column(Integer)
    favourites: Mapped[int | None] = mapped_column(Integer)
    trending: Mapped[int | None] = mapped_column(Integer)
    airing_day: Mapped[int | None] = mapped_column(Integer)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    sync_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    trackings: Mapped[list["Tracking"]] = relationship(  # noqa: F821
        back_populates="anime",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["AnimeEvent"]] = relationship(  # noqa: F821
        back_populates="anime",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("anilist_id", name="uq_animes_anilist_id"),
        Index("ix_animes_status", "status"),
        Index("ix_animes_next_airing_at", "next_airing_at"),
        Index("ix_animes_next_sync_at", "next_sync_at"),
    )

    @property
    def display_title(self) -> str:
        return self.title_english or self.title_romaji or self.title_native or f"Anime #{self.anilist_id}"