"""User repository."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.tracking import Tracking
from app.database.models.user import User
from app.schemas.preferences import DEFAULT_PREFERENCES


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        first_name: str | None = None,
        username: str | None = None,
        language: str = "pt-BR",
        timezone: str = "America/Sao_Paulo",
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.first_name = first_name or user.first_name
            user.username = username or user.username
            user.last_activity = datetime.now(timezone.utc)
            if user.bot_blocked:
                user.bot_blocked = False
            return user

        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            language=language,
            timezone=timezone,
            preferences=DEFAULT_PREFERENCES.model_dump(),
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_preferences(self, user: User, prefs: dict) -> User:
        merged = {**user.preferences, **prefs}
        user.preferences = merged
        await self.session.flush()
        return user

    async def mark_bot_blocked(self, telegram_id: int) -> None:
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(bot_blocked=True)
        )

    async def delete_user_data(self, user_id: int) -> None:
        from app.database.models.event import NotificationDelivery

        await self.session.execute(
            delete(NotificationDelivery).where(NotificationDelivery.user_id == user_id)
        )
        await self.session.execute(delete(Tracking).where(Tracking.user_id == user_id))
        await self.session.execute(delete(User).where(User.id == user_id))

    async def count_active(self, days: int = 7) -> int:
        from sqlalchemy import func

        cutoff = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.bot_blocked.is_(False))
        )
        return result.scalar_one()

    async def list_all_telegram_ids(self) -> list[int]:
        result = await self.session.execute(
            select(User.telegram_id).where(
                User.bot_blocked.is_(False),
                User.is_admin_blocked.is_(False),
            )
        )
        return list(result.scalars().all())