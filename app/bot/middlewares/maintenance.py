"""Maintenance mode middleware."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import get_settings


class MaintenanceMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        settings = get_settings()
        if not settings.maintenance_mode:
            return await handler(event, data)

        admin_ids = set(settings.admin_telegram_ids)
        user_id = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id

        if user_id in admin_ids:
            return await handler(event, data)

        msg = "🔧 Bot em manutenção. Tente mais tarde."
        if isinstance(event, CallbackQuery):
            await event.answer(msg, show_alert=True)
        elif isinstance(event, Message):
            await event.answer(msg)
        return None