"""AniList GraphQL API client."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.clients.base import BaseAPIClient
from app.schemas.anilist import (
    AniListAiringPage,
    AniListMedia,
    AniListPage,
    fuzzy_date_to_datetime,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

MEDIA_FIELDS = """
id
idMal
title { romaji english native }
synonyms
description(asHtml: false)
status
format
season
seasonYear
episodes
duration
startDate { year month day }
endDate { year month day }
genres
tags { name rank isAdult }
studios(isMain: true) { nodes { name } }
coverImage { large medium }
bannerImage
trailer { id site thumbnail }
siteUrl
isAdult
averageScore
popularity
favourites
trending
nextAiringEpisode { airingAt episode timeUntilAiring }
source
countryOfOrigin
hashtag
externalLinks { site url }
"""

MEDIA_DETAIL_FIELDS = MEDIA_FIELDS + """
relations { edges { relationType node { id title { romaji english } format status } } }
characters(perPage: 5, sort: ROLE) {
  edges { role node { name { full } } voiceActors(language: JAPANESE) { name { full } } }
}
recommendations(perPage: 5, sort: RATING_DESC) {
  edges { node { mediaRecommendation { id title { romaji english } coverImage { medium } averageScore } } }
}
"""

QUERY_SEASON = """
query ($page: Int, $perPage: Int, $season: MediaSeason, $seasonYear: Int, $isAdult: Boolean) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { total perPage currentPage lastPage hasNextPage }
    media(season: $season, seasonYear: $seasonYear, type: ANIME, isAdult: $isAdult, sort: POPULARITY_DESC) {
      """ + MEDIA_FIELDS + """
    }
  }
}
"""

QUERY_SEARCH = """
query ($page: Int, $perPage: Int, $search: String, $isAdult: Boolean) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { total perPage currentPage lastPage hasNextPage }
    media(search: $search, type: ANIME, isAdult: $isAdult, sort: SEARCH_MATCH) {
      """ + MEDIA_FIELDS + """
    }
  }
}
"""

QUERY_MEDIA_BY_ID = """
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    """ + MEDIA_DETAIL_FIELDS + """
  }
}
"""

QUERY_AIRING = """
query ($page: Int, $perPage: Int, $airingAt_greater: Int, $airingAt_lesser: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { hasNextPage currentPage lastPage }
    airingSchedules(airingAt_greater: $airingAt_greater, airingAt_lesser: $airingAt_lesser, sort: TIME) {
      id airingAt episode mediaId
      media { """ + MEDIA_FIELDS + """ }
    }
  }
}
"""


class AniListClient(BaseAPIClient):
    """Dedicated AniList GraphQL client."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        from app.config import get_settings

        settings = kwargs.pop("settings", None) or get_settings()
        kwargs.pop("base_url", None)
        super().__init__(settings.anilist_api_url, *args, settings=settings, **kwargs)

    async def _graphql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        cache_prefix: str | None = None,
    ) -> dict[str, Any]:
        payload = {"query": query, "variables": variables or {}}
        cache_key = None
        if cache_prefix:
            import json

            cache_key = self._cache_key(cache_prefix, json.dumps(payload, sort_keys=True))
            cached = await self._get_cached(cache_key)
            if cached:
                return cached

        response = await self._request("POST", "", json_data=payload)
        data = response.json()

        if "errors" in data:
            errors = data["errors"]
            logger.error("anilist_graphql_error", errors=errors)
            raise ValueError(f"AniList GraphQL error: {errors[0].get('message', 'unknown')}")

        result = data.get("data", {})
        if cache_key:
            await self._set_cached(cache_key, result)
        return result

    async def get_season_anime(
        self,
        season: str,
        year: int,
        page: int = 1,
        per_page: int = 25,
        hide_adult: bool = True,
    ) -> AniListPage:
        data = await self._graphql(
            QUERY_SEASON,
            {
                "page": page,
                "perPage": per_page,
                "season": season,
                "seasonYear": year,
                "isAdult": not hide_adult,
            },
            cache_prefix="season",
        )
        return AniListPage.model_validate(data.get("Page", {}))

    async def search_anime(
        self,
        query: str,
        page: int = 1,
        per_page: int = 25,
        hide_adult: bool = True,
    ) -> AniListPage:
        data = await self._graphql(
            QUERY_SEARCH,
            {"page": page, "perPage": per_page, "search": query, "isAdult": not hide_adult},
            cache_prefix="search",
        )
        return AniListPage.model_validate(data.get("Page", {}))

    async def get_media_by_id(self, media_id: int) -> AniListMedia | None:
        data = await self._graphql(
            QUERY_MEDIA_BY_ID,
            {"id": media_id},
            cache_prefix=f"media_{media_id}",
        )
        media = data.get("Media")
        if not media:
            return None
        return AniListMedia.model_validate(media)

    async def get_airing_schedules(
        self,
        start_ts: int,
        end_ts: int,
        page: int = 1,
        per_page: int = 50,
    ) -> AniListAiringPage:
        data = await self._graphql(
            QUERY_AIRING,
            {
                "page": page,
                "perPage": per_page,
                "airingAt_greater": start_ts,
                "airingAt_lesser": end_ts,
            },
            cache_prefix="airing",
        )
        return AniListAiringPage.model_validate(data.get("Page", {}))

    @staticmethod
    def media_to_dict(media: AniListMedia) -> dict[str, Any]:
        """Convert AniList media to DB-compatible dict."""
        trailer_url = None
        if media.trailer and media.trailer.id and media.trailer.site:
            site = media.trailer.site.lower()
            if site == "youtube":
                trailer_url = f"https://www.youtube.com/watch?v={media.trailer.id}"
            elif site == "dailymotion":
                trailer_url = f"https://www.dailymotion.com/video/{media.trailer.id}"

        next_airing_at = None
        if media.nextAiringEpisode:
            next_airing_at = datetime.fromtimestamp(
                media.nextAiringEpisode.airingAt, tz=timezone.utc
            )

        studios = []
        if media.studios and media.studios.studios:
            studios = [s.name for s in media.studios.studios]

        return {
            "anilist_id": media.id,
            "mal_id": media.idMal,
            "title_romaji": media.title.romaji if media.title else None,
            "title_english": media.title.english if media.title else None,
            "title_native": media.title.native if media.title else None,
            "synonyms": media.synonyms,
            "description": media.description,
            "status": media.status,
            "format": media.format,
            "season": media.season,
            "season_year": media.seasonYear,
            "episodes": media.episodes,
            "duration": media.duration,
            "start_date": fuzzy_date_to_datetime(media.startDate),
            "end_date": fuzzy_date_to_datetime(media.endDate),
            "next_episode": media.nextAiringEpisode.episode if media.nextAiringEpisode else None,
            "next_airing_at": next_airing_at,
            "genres": media.genres,
            "tags": media.tag_names(),
            "studios": studios,
            "cover_image": media.coverImage.large if media.coverImage else None,
            "banner_image": media.bannerImage,
            "trailer_url": trailer_url,
            "trailer_site": media.trailer.site if media.trailer else None,
            "site_url": media.siteUrl,
            "is_adult": media.isAdult,
            "average_score": media.averageScore,
            "popularity": media.popularity,
            "favourites": media.favourites,
            "trending": media.trending,
            "raw_data": media.model_dump(),
        }