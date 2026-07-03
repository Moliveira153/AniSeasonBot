"""Season anime listing service."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.anilist import AniListClient
from app.config import get_settings
from app.database.models.anime import Anime
from app.services.anime_service import AnimeService
from app.utils.logging import get_logger
from app.utils.season import SeasonInfo, detect_current_season

logger = get_logger(__name__)


@dataclass
class SeasonFilters:
    tv_only: bool = False
    genre: str | None = None
    airing_day: int | None = None
    airing_only: bool = False
    not_aired: bool = False
    min_score: int | None = None
    hide_adult: bool = True
    hide_tracked: bool = False
    sequels_only: bool = False
    tracked_ids: set[int] = field(default_factory=set)


class SeasonService:
    def __init__(self, session: AsyncSession, anilist: AniListClient | None = None) -> None:
        self.session = session
        self.settings = get_settings()
        self.anilist = anilist or AniListClient(settings=self.settings)
        self.anime_service = AnimeService(session, self.anilist)

    def current_season(self) -> SeasonInfo:
        return detect_current_season()

    async def get_season_page(
        self,
        page: int = 1,
        per_page: int = 5,
        season_info: SeasonInfo | None = None,
        filters: SeasonFilters | None = None,
    ) -> tuple[list[Anime], int, SeasonInfo]:
        season_info = season_info or self.current_season()
        filters = filters or SeasonFilters()

        result = await self.anilist.get_season_anime(
            season=season_info.season.value,
            year=season_info.year,
            page=page,
            per_page=25,
            hide_adult=filters.hide_adult,
        )

        animes: list[Anime] = []
        for media in result.media:
            if filters.tv_only and media.format != "TV":
                continue
            if filters.genre and filters.genre.lower() not in [g.lower() for g in media.genres]:
                continue
            if filters.airing_only and media.status != "RELEASING":
                continue
            if filters.not_aired and media.status != "NOT_YET_RELEASED":
                continue
            if filters.min_score and (media.averageScore or 0) < filters.min_score:
                continue
            if filters.sequels_only:
                tags = media.tag_names()
                if not any("sequel" in t.lower() for t in tags):
                    continue

            anime = await self.anime_service._persist_media(media)
            if filters.hide_tracked and anime.id in filters.tracked_ids:
                continue
            animes.append(anime)

        total = result.pageInfo.total if result.pageInfo and result.pageInfo.total else len(animes)
        start = 0
        end = per_page
        return animes[start:end], total, season_info