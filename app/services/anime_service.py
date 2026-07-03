"""Anime data service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.anilist import AniListClient
from app.clients.jikan import JikanClient
from app.config import Settings, get_settings
from app.database.models.anime import Anime
from app.database.repositories.anime_repo import AnimeRepository
from app.schemas.anilist import AniListMedia
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AnimeService:
    def __init__(
        self,
        session: AsyncSession,
        anilist: AniListClient | None = None,
        jikan: JikanClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.session = session
        self.repo = AnimeRepository(session)
        self.settings = settings or get_settings()
        self.anilist = anilist or AniListClient(settings=self.settings)
        self.jikan = jikan or JikanClient(settings=self.settings)

    async def sync_from_anilist(self, anilist_id: int) -> Anime | None:
        media = await self.anilist.get_media_by_id(anilist_id)
        if not media:
            return None
        return await self._persist_media(media)

    async def _persist_media(self, media: AniListMedia) -> Anime:
        data = AniListClient.media_to_dict(media)
        if not data.get("description") or not data.get("mal_id"):
            await self._supplement_from_jikan(data)
        anime = await self.repo.upsert_from_dict(data)
        anime.sync_priority = self._compute_sync_priority(anime)
        interval = self._sync_interval(anime)
        await self.repo.schedule_next_sync(anime, interval)
        return anime

    async def _supplement_from_jikan(self, data: dict[str, Any]) -> None:
        mal_id = data.get("mal_id")
        if not mal_id:
            return
        jikan_data = await self.jikan.get_anime_by_mal_id(mal_id)
        if jikan_data:
            supplemented = JikanClient.supplement_anime_dict(data, jikan_data)
            data.update(supplemented)

    def _compute_sync_priority(self, anime: Anime) -> int:
        if anime.status == "RELEASING" and anime.next_airing_at:
            delta = (anime.next_airing_at - datetime.now(timezone.utc)).total_seconds()
            if delta < 3600:
                return 1
            if delta < 86400:
                return 2
            return 3
        if anime.status == "NOT_YET_RELEASED":
            return 4
        if anime.status == "FINISHED":
            return 10
        return 5

    def _sync_interval(self, anime: Anime) -> int:
        priority = anime.sync_priority
        if priority <= 2:
            return self.settings.sync_interval_airing_soon
        if priority <= 3:
            return self.settings.sync_interval_airing
        if priority <= 4:
            return self.settings.sync_interval_upcoming
        return self.settings.sync_interval_finished

    async def get_or_fetch(self, anilist_id: int) -> Anime | None:
        anime = await self.repo.get_by_anilist_id(anilist_id)
        if anime and anime.last_synced_at:
            age = datetime.now(timezone.utc) - anime.last_synced_at
            if age < timedelta(hours=1):
                return anime
        return await self.sync_from_anilist(anilist_id)

    async def search(self, query: str, page: int = 1, hide_adult: bool = True) -> list[Anime]:
        page_result = await self.anilist.search_anime(query, page=page, hide_adult=hide_adult)
        animes: list[Anime] = []
        for media in page_result.media:
            anime = await self._persist_media(media)
            animes.append(anime)
        return animes

    async def get_by_id(self, anime_id: int) -> Anime | None:
        return await self.repo.get_by_id(anime_id)

    def format_anime_card(self, anime: Anime, language: str = "pt-BR") -> str:
        title = anime.display_title
        lines = [f"*{title}*"]
        if anime.title_romaji and anime.title_romaji != title:
            lines.append(f"Romaji: {anime.title_romaji}")
        if anime.title_native:
            lines.append(f"日本語: {anime.title_native}")
        if anime.format:
            lines.append(f"Formato: {anime.format}" if language.startswith("pt") else f"Format: {anime.format}")
        if anime.genres:
            lines.append(f"Gêneros: {', '.join(anime.genres[:5])}" if language.startswith("pt") else f"Genres: {', '.join(anime.genres[:5])}")
        if anime.episodes:
            lines.append(f"Episódios: {anime.episodes}" if language.startswith("pt") else f"Episodes: {anime.episodes}")
        if anime.status:
            lines.append(f"Status: {anime.status}")
        if anime.average_score:
            lines.append(f"Nota: {anime.average_score / 10:.1f}/10" if language.startswith("pt") else f"Score: {anime.average_score / 10:.1f}/10")
        if anime.next_episode and anime.next_airing_at:
            from app.utils.datetime_fmt import format_relative

            rel = format_relative(anime.next_airing_at, "UTC", language)
            ep_label = "Próximo ep." if language.startswith("pt") else "Next ep."
            lines.append(f"{ep_label} {anime.next_episode}: {rel}")
        return "\n".join(lines)