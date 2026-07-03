"""Pydantic schemas for AniList API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AniListFuzzyDate(BaseModel):
    year: int | None = None
    month: int | None = None
    day: int | None = None


class AniListTitle(BaseModel):
    romaji: str | None = None
    english: str | None = None
    native: str | None = None


class AniListCoverImage(BaseModel):
    large: str | None = None
    medium: str | None = None


class AniListTrailer(BaseModel):
    id: str | None = None
    site: str | None = None
    thumbnail: str | None = None


class AniListNextAiringEpisode(BaseModel):
    airingAt: int
    episode: int
    timeUntilAiring: int


class AniListStudio(BaseModel):
    name: str


class AniListStudioNode(BaseModel):
    studios: list[AniListStudio] = Field(default_factory=list)


class AniListExternalLink(BaseModel):
    site: str | None = None
    url: str | None = None


class AniListRelationNode(BaseModel):
    id: int
    title: AniListTitle | None = None
    format: str | None = None
    status: str | None = None


class AniListRelation(BaseModel):
    relationType: str | None = None
    node: AniListRelationNode | None = None


class AniListCharacter(BaseModel):
    name: dict[str, str | None] | None = None


class AniListCharacterEdge(BaseModel):
    role: str | None = None
    node: AniListCharacter | None = None
    voiceActors: list[dict[str, Any]] = Field(default_factory=list)


class AniListMediaBrief(BaseModel):
    id: int
    title: AniListTitle | None = None
    coverImage: AniListCoverImage | None = None
    format: str | None = None
    status: str | None = None
    averageScore: int | None = None


class AniListRecommendation(BaseModel):
    rating: int | None = None
    mediaRecommendation: AniListMediaBrief | None = None


class AniListMedia(BaseModel):
    id: int
    idMal: int | None = None
    title: AniListTitle | None = None
    synonyms: list[str] = Field(default_factory=list)
    description: str | None = None
    status: str | None = None
    format: str | None = None
    season: str | None = None
    seasonYear: int | None = None
    episodes: int | None = None
    duration: int | None = None
    startDate: AniListFuzzyDate | None = None
    endDate: AniListFuzzyDate | None = None
    genres: list[str] = Field(default_factory=list)
    tags: list[dict[str, Any]] = Field(default_factory=list)
    studios: AniListStudioNode | None = None
    coverImage: AniListCoverImage | None = None
    bannerImage: str | None = None
    trailer: AniListTrailer | None = None
    siteUrl: str | None = None
    isAdult: bool = False
    averageScore: int | None = None
    popularity: int | None = None
    favourites: int | None = None
    trending: int | None = None
    nextAiringEpisode: AniListNextAiringEpisode | None = None
    relations: dict[str, Any] | None = None
    characters: dict[str, Any] | None = None
    recommendations: dict[str, Any] | None = None
    externalLinks: list[AniListExternalLink] = Field(default_factory=list)
    source: str | None = None
    countryOfOrigin: str | None = None
    hashtag: str | None = None

    def tag_names(self) -> list[str]:
        return [t.get("name", "") for t in self.tags if t.get("name")]


class AniListPageInfo(BaseModel):
    total: int | None = None
    perPage: int | None = None
    currentPage: int | None = None
    lastPage: int | None = None
    hasNextPage: bool = False


class AniListPage(BaseModel):
    pageInfo: AniListPageInfo | None = None
    media: list[AniListMedia] = Field(default_factory=list)


class AniListAiringSchedule(BaseModel):
    id: int
    airingAt: int
    episode: int
    mediaId: int
    media: AniListMedia | None = None


class AniListAiringPage(BaseModel):
    pageInfo: AniListPageInfo | None = None
    airingSchedules: list[AniListAiringSchedule] = Field(default_factory=list)


def fuzzy_date_to_datetime(fd: AniListFuzzyDate | None) -> datetime | None:
    from datetime import timezone

    if fd is None or fd.year is None:
        return None
    month = fd.month or 1
    day = fd.day or 1
    try:
        return datetime(fd.year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return datetime(fd.year, month, 1, tzinfo=timezone.utc)