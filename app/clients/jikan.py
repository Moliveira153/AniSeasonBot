"""Jikan REST API client (fallback)."""

from __future__ import annotations

from typing import Any

from app.clients.base import BaseAPIClient
from app.schemas.jikan import JikanAnime, JikanSearchResult, JikanSingleResult
from app.utils.logging import get_logger

logger = get_logger(__name__)


class JikanClient(BaseAPIClient):
    """Optional Jikan API client for MAL data fallback."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        from app.config import get_settings

        settings = kwargs.get("settings") or get_settings()
        super().__init__(settings.jikan_api_url, *args, **kwargs)

    async def get_anime_by_mal_id(self, mal_id: int) -> JikanAnime | None:
        cache_key = self._cache_key("jikan_anime", str(mal_id))
        cached = await self._get_cached(cache_key)
        if cached:
            return JikanAnime.model_validate(cached)

        try:
            response = await self._request("GET", f"/anime/{mal_id}")
            result = JikanSingleResult.model_validate(response.json())
            if result.data:
                await self._set_cached(cache_key, result.data.model_dump(), ttl=7200)
                return result.data
        except Exception as exc:
            logger.warning("jikan_fetch_failed", mal_id=mal_id, error=str(exc))
        return None

    async def search_anime(self, query: str, page: int = 1, limit: int = 25) -> list[JikanAnime]:
        cache_key = self._cache_key("jikan_search", f"{query}:{page}")
        cached = await self._get_cached(cache_key)
        if cached:
            return [JikanAnime.model_validate(item) for item in cached]

        try:
            response = await self._request(
                "GET",
                "/anime",
                params={"q": query, "page": page, "limit": limit},
            )
            result = JikanSearchResult.model_validate(response.json())
            await self._set_cached(
                cache_key,
                [a.model_dump() for a in result.data],
                ttl=1800,
            )
            return result.data
        except Exception as exc:
            logger.warning("jikan_search_failed", query=query, error=str(exc))
            return []

    @staticmethod
    def supplement_anime_dict(base: dict[str, Any], jikan: JikanAnime) -> dict[str, Any]:
        """Fill missing fields from Jikan without overwriting AniList data."""
        result = dict(base)
        if not result.get("mal_id"):
            result["mal_id"] = jikan.mal_id
        if not result.get("description") and jikan.synopsis:
            result["description"] = jikan.synopsis
        if not result.get("episodes") and jikan.episodes:
            result["episodes"] = jikan.episodes
        if not result.get("cover_image") and jikan.images:
            jpg = jikan.images.get("jpg", {})
            result["cover_image"] = jpg.get("large_image_url") or jpg.get("image_url")
        if not result.get("trailer_url") and jikan.trailer:
            url = jikan.trailer.get("url")
            if url:
                result["trailer_url"] = url
        result["_jikan_supplemented"] = True
        return result