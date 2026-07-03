"""Global error handler — prevents crashes from killing the process."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, ErrorEvent, Message, TelegramObject

from app.utils.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as exc:
            logger.exception("handler_error", error=str(exc), event_type=type(event).__name__)
            await self._notify_user(event)
            return None

    async def _notify_user(self, event: TelegramObject) -> None:
        msg = "❌ Ocorreu um erro. Tente novamente em instantes."
        try:
            if isinstance(event, Message):
                await event.answer(msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(msg, show_alert=True)
        except Exception:
            pass


async def on_dispatcher_error(event: ErrorEvent) -> bool:
    logger.exception(
        "dispatcher_error",
        error=str(event.exception),
        update=event.update.model_dump(exclude_none=True) if event.update else None,
    )
    return True