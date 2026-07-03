"""Rate limiting middleware."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import get_settings


class ThrottleMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.settings = get_settings()
        self._buckets: dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id and not self._check_rate(user_id):
            if isinstance(event, CallbackQuery):
                await event.answer("⏳ Muitas requisições. Aguarde.", show_alert=True)
            elif isinstance(event, Message):
                await event.answer("⏳ Muitas requisições. Aguarde um momento.")
            return None

        return await handler(event, data)

    def _check_rate(self, user_id: int) -> bool:
        now = time.time()
        window = self.settings.user_command_rate_window
        limit = self.settings.user_command_rate_limit
        self._buckets[user_id] = [t for t in self._buckets[user_id] if now - t < window]
        if len(self._buckets[user_id]) >= limit:
            return False
        self._buckets[user_id].append(now)
        return True