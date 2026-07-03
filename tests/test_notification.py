"""Notification deduplication and detection tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.database.models.anime import Anime
from app.services.notification_service import (
    EVENT_FINISHED,
    EVENT_NEW_EPISODE,
    EVENT_SCHEDULE_CHANGE,
    NotificationService,
)


def _make_anime(**kwargs: object) -> Anime:
    anime = Anime(anilist_id=1, title_romaji="Test")
    for k, v in kwargs.items():
        setattr(anime, k, v)
    return anime


@pytest.mark.asyncio
async def test_detect_new_episode() -> None:
    old = _make_anime(
        status="RELEASING",
        next_episode=5,
        next_airing_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    new = _make_anime(
        status="RELEASING",
        next_episode=6,
        next_airing_at=datetime(2026, 1, 8, tzinfo=timezone.utc),
    )
    events = await NotificationService.detect_changes(old, new)
    types = [e["type"] for e in events]
    assert EVENT_NEW_EPISODE in types


@pytest.mark.asyncio
async def test_detect_finished() -> None:
    old = _make_anime(status="RELEASING", episodes=12)
    new = _make_anime(status="FINISHED", episodes=12)
    events = await NotificationService.detect_changes(old, new)
    assert any(e["type"] == EVENT_FINISHED for e in events)


@pytest.mark.asyncio
async def test_detect_schedule_change() -> None:
    old = _make_anime(
        next_episode=5,
        next_airing_at=datetime(2026, 1, 1, 17, 0, tzinfo=timezone.utc),
    )
    new = _make_anime(
        next_episode=5,
        next_airing_at=datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc),
    )
    events = await NotificationService.detect_changes(old, new)
    assert any(e["type"] == EVENT_SCHEDULE_CHANGE for e in events)


def test_idempotency_key_deterministic() -> None:
    key1 = NotificationService.make_idempotency_key(1, 2, "new_episode", 5)
    key2 = NotificationService.make_idempotency_key(1, 2, "new_episode", 5)
    key3 = NotificationService.make_idempotency_key(1, 2, "new_episode", 6)
    assert key1 == key2
    assert key1 != key3