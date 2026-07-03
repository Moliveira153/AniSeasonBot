"""Tracking repository."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.anime import Anime
from app.database.models.tracking import Tracking


class TrackingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_tracking(self, user_id: int, anime_id: int) -> Tracking | None:
        result = await self.session.execute(
            select(Tracking).where(
                Tracking.user_id == user_id,
                Tracking.anime_id == anime_id,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, user_id: int, anime_id: int) -> Tracking:
        existing = await self.get_tracking(user_id, anime_id)
        if existing:
            return existing
        tracking = Tracking(user_id=user_id, anime_id=anime_id)
        self.session.add(tracking)
        await self.session.flush()
        return tracking

    async def remove(self, user_id: int, anime_id: int) -> bool:
        result = await self.session.execute(
            delete(Tracking).where(
                Tracking.user_id == user_id,
                Tracking.anime_id == anime_id,
            )
        )
        return result.rowcount > 0

    async def list_for_user(
        self,
        user_id: int,
        sort_by: str = "next_airing",
    ) -> list[Tracking]:
        query = (
            select(Tracking)
            .where(Tracking.user_id == user_id)
            .options(selectinload(Tracking.anime))
        )
        result = await self.session.execute(query)
        trackings = list(result.scalars().all())

        if sort_by == "title":
            trackings.sort(key=lambda t: t.anime.display_title.lower())
        elif sort_by == "popularity":
            trackings.sort(key=lambda t: t.anime.popularity or 0, reverse=True)
        elif sort_by == "score":
            trackings.sort(key=lambda t: t.anime.average_score or 0, reverse=True)
        elif sort_by == "added":
            trackings.sort(key=lambda t: t.added_at, reverse=True)
        elif sort_by == "status":
            trackings.sort(key=lambda t: t.anime.status or "")
        else:
            trackings.sort(
                key=lambda t: t.anime.next_airing_at or t.anime.start_date,
            )

        return trackings

    async def get_users_tracking_anime(self, anime_id: int) -> list[Tracking]:
        result = await self.session.execute(
            select(Tracking)
            .where(Tracking.anime_id == anime_id, Tracking.notifications_enabled.is_(True))
            .options(selectinload(Tracking.user))
        )
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(Tracking))
        return result.scalar_one()

    async def is_tracked(self, user_id: int, anime_id: int) -> bool:
        result = await self.session.execute(
            select(func.count())
            .select_from(Tracking)
            .where(Tracking.user_id == user_id, Tracking.anime_id == anime_id)
        )
        return result.scalar_one() > 0