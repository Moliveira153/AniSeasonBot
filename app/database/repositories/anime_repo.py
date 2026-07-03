"""Anime repository."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.anime import Anime
from app.database.models.tracking import Tracking


class AnimeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_anilist_id(self, anilist_id: int) -> Anime | None:
        result = await self.session.execute(
            select(Anime).where(Anime.anilist_id == anilist_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, anime_id: int) -> Anime | None:
        result = await self.session.execute(select(Anime).where(Anime.id == anime_id))
        return result.scalar_one_or_none()

    async def upsert_from_dict(self, data: dict[str, Any]) -> Anime:
        anime = await self.get_by_anilist_id(data["anilist_id"])
        now = datetime.now(timezone.utc)
        data["last_synced_at"] = now

        if anime:
            for key, value in data.items():
                if key != "anilist_id" and value is not None:
                    setattr(anime, key, value)
            return anime

        anime = Anime(**{k: v for k, v in data.items() if k != "raw_data" or v is not None})
        if "raw_data" in data:
            anime.raw_data = data["raw_data"]
        self.session.add(anime)
        await self.session.flush()
        return anime

    async def get_tracked_anime_ids(self) -> list[int]:
        result = await self.session.execute(
            select(Anime.id).join(Tracking).distinct()
        )
        return list(result.scalars().all())

    async def get_animes_due_for_sync(self, limit: int = 50) -> list[Anime]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(Anime)
            .join(Tracking)
            .where(
                (Anime.next_sync_at.is_(None)) | (Anime.next_sync_at <= now),
            )
            .order_by(Anime.sync_priority.asc(), Anime.next_sync_at.asc().nullsfirst())
            .distinct()
            .limit(limit)
        )
        return list(result.scalars().all())

    async def schedule_next_sync(self, anime: Anime, interval_seconds: int) -> None:
        anime.next_sync_at = datetime.now(timezone.utc) + timedelta(seconds=interval_seconds)
        anime.sync_failures = 0
        await self.session.flush()

    async def record_sync_failure(self, anime: Anime) -> None:
        anime.sync_failures += 1
        backoff = min(3600, 60 * (2**anime.sync_failures))
        anime.next_sync_at = datetime.now(timezone.utc) + timedelta(seconds=backoff)
        await self.session.flush()

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(Anime))
        return result.scalar_one()