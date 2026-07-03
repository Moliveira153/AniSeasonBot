"""User repository tests."""

from __future__ import annotations

import pytest

from app.database.models.user import User
from app.database.repositories.user_repo import UserRepository


@pytest.mark.asyncio
async def test_get_or_create_does_not_shadow_timezone(db_session) -> None:
    """Regression: parameter named timezone must not break datetime.now(UTC)."""
    repo = UserRepository(db_session)
    user = await repo.get_or_create(
        telegram_id=999888,
        first_name="Test",
        user_timezone="America/Sao_Paulo",
    )
    assert user.telegram_id == 999888
    assert user.timezone == "America/Sao_Paulo"
    assert user.last_activity is not None

    again = await repo.get_or_create(telegram_id=999888, first_name="Test2")
    assert again.id == user.id
    assert again.first_name == "Test2"