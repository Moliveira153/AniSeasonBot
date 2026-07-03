"""User tracking service."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.anime import Anime
from app.database.models.tracking import Tracking
from app.database.models.user import User
from app.database.repositories.anime_repo import AnimeRepository
from app.database.repositories.tracking_repo import TrackingRepository
from app.services.anime_service import AnimeService
from app.utils.datetime_fmt import format_datetime, format_relative


class TrackingService:
    def __init__(self, session: AsyncSession, anime_service: AnimeService | None = None) -> None:
        self.session = session
        self.tracking_repo = TrackingRepository(session)
        self.anime_repo = AnimeRepository(session)
        self.anime_service = anime_service or AnimeService(session)

    async def add_anime(self, user: User, anilist_id: int) -> Tracking:
        anime = await self.anime_service.get_or_fetch(anilist_id)
        if not anime:
            raise ValueError("Anime not found")
        return await self.tracking_repo.add(user.id, anime.id)

    async def remove_anime(self, user: User, anime_id: int) -> bool:
        return await self.tracking_repo.remove(user.id, anime_id)

    async def toggle_notifications(self, user: User, anime_id: int) -> bool:
        tracking = await self.tracking_repo.get_tracking(user.id, anime_id)
        if not tracking:
            return False
        tracking.notifications_enabled = not tracking.notifications_enabled
        await self.session.flush()
        return tracking.notifications_enabled

    async def mark_watched(self, user: User, anime_id: int, episode: int | None = None) -> Tracking | None:
        tracking = await self.tracking_repo.get_tracking(user.id, anime_id)
        if not tracking:
            return None
        anime = await self.anime_repo.get_by_id(anime_id)
        if episode is None and anime and anime.next_episode:
            episode = anime.next_episode - 1
        if episode:
            tracking.last_watched_episode = max(tracking.last_watched_episode, episode)
        await self.session.flush()
        return tracking

    async def get_user_list(self, user: User, sort_by: str = "next_airing") -> list[Tracking]:
        return await self.tracking_repo.list_for_user(user.id, sort_by=sort_by)

    def format_tracking_item(self, tracking: Tracking, user: User) -> str:
        anime = tracking.anime
        lang = user.language
        lines = [f"*{anime.display_title}*"]
        if anime.status:
            lines.append(f"Status: {anime.status}")
        if anime.episodes:
            progress = f"Ep. {tracking.last_watched_episode}/{anime.episodes}"
            lines.append(progress)
        if anime.next_episode and anime.next_airing_at:
            rel = format_relative(anime.next_airing_at, user.timezone, lang)
            dt = format_datetime(anime.next_airing_at, user.timezone, lang)
            ep = "Próximo" if lang.startswith("pt") else "Next"
            lines.append(f"{ep} ep. {anime.next_episode}: {rel} ({dt})")
        muted = "🔕" if not tracking.notifications_enabled else ""
        lines[0] = f"{muted} {lines[0]}".strip()
        return "\n".join(lines)

    async def get_tracked_anilist_ids(self, user: User) -> set[int]:
        trackings = await self.get_user_list(user)
        return {t.anime.anilist_id for t in trackings}