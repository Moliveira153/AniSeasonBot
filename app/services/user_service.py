"""User management service."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.repositories.tracking_repo import TrackingRepository
from app.database.repositories.user_repo import UserRepository
from app.schemas.preferences import UserPreferences


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.tracking_repo = TrackingRepository(session)

    async def get_or_create_from_telegram(
        self,
        telegram_id: int,
        first_name: str | None = None,
        username: str | None = None,
    ) -> User:
        return await self.user_repo.get_or_create(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
        )

    async def update_language(self, user: User, language: str) -> User:
        user.language = language
        await self.session.flush()
        return user

    async def update_timezone(self, user: User, timezone: str) -> User:
        user.timezone = timezone
        await self.session.flush()
        return user

    async def update_preferences(self, user: User, prefs: dict) -> User:
        return await self.user_repo.update_preferences(user, prefs)

    async def pause_notifications(self, user: User) -> User:
        return await self.user_repo.update_preferences(user, {"notifications_enabled": False})

    async def resume_notifications(self, user: User) -> User:
        return await self.user_repo.update_preferences(user, {"notifications_enabled": True})

    async def delete_user(self, user: User) -> None:
        await self.user_repo.delete_user_data(user.id)

    def get_preferences(self, user: User) -> UserPreferences:
        return UserPreferences.model_validate(user.preferences)

    async def get_stats(self) -> dict[str, int]:
        return {
            "users": await self.user_repo.count_active(),
            "trackings": await self.tracking_repo.count_all(),
        }