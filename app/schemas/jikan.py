"""Pydantic schemas for Jikan API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class JikanTitle(BaseModel):
    type: str | None = None
    title: str | None = None


class JikanAnime(BaseModel):
    mal_id: int
    url: str | None = None
    titles: list[JikanTitle] = Field(default_factory=list)
    title: str | None = None
    title_english: str | None = None
    title_japanese: str | None = None
    synopsis: str | None = None
    status: str | None = None
    airing: bool = False
    episodes: int | None = None
    score: float | None = None
    scored_by: int | None = None
    rank: int | None = None
    popularity: int | None = None
    members: int | None = None
    favorites: int | None = None
    images: dict[str, dict[str, str]] | None = None
    trailer: dict[str, str | None] | None = None
    genres: list[dict[str, str]] = Field(default_factory=list)
    studios: list[dict[str, str]] = Field(default_factory=list)
    producers: list[dict[str, str]] = Field(default_factory=list)
    aired: dict[str, str | None] | None = None
    duration: str | None = None


class JikanSearchResult(BaseModel):
    data: list[JikanAnime] = Field(default_factory=list)
    pagination: dict[str, object] | None = None


class JikanSingleResult(BaseModel):
    data: JikanAnime | None = None