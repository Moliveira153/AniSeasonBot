"""Tracking repository tests."""

from __future__ import annotations

import pytest

from app.database.models.anime import Anime
from app.database.models.user import User
from app.database.repositories.tracking_repo import TrackingRepository


@pytest.mark.asyncio
async def test_add_and_remove_tracking(db_session) -> None:
    user = User(telegram_id=12345, language="pt-BR", timezone="UTC", preferences={})
    anime = Anime(anilist_id=999, title_romaji="Test Anime")
    db_session.add_all([user, anime])
    await db_session.flush()

    repo = TrackingRepository(db_session)
    tracking = await repo.add(user.id, anime.id)
    assert tracking.user_id == user.id
    assert tracking.anime_id == anime.id

    assert await repo.is_tracked(user.id, anime.id)
    removed = await repo.remove(user.id, anime.id)
    assert removed
    assert not await repo.is_tracked(user.id, anime.id)


@pytest.mark.asyncio
async def test_add_idempotent(db_session) -> None:
    user = User(telegram_id=111, language="pt-BR", timezone="UTC", preferences={})
    anime = Anime(anilist_id=888, title_romaji="Anime")
    db_session.add_all([user, anime])
    await db_session.flush()

    repo = TrackingRepository(db_session)
    t1 = await repo.add(user.id, anime.id)
    t2 = await repo.add(user.id, anime.id)
    assert t1.id == t2.id