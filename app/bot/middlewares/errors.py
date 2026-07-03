"""Global error handler — prevents crashes from killing the process."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, ErrorEvent, Message, TelegramObject, Update

from app.utils.logging import get_logger

logger = get_logger(__name__)


def _extract_event(event: TelegramObject) -> Message | CallbackQuery | None:
    if isinstance(event, (Message, CallbackQuery)):
        return event
    if isinstance(event, Update):
        if event.callback_query:
            return event.callback_query
        if event.message:
            return event.message
    return None


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
            inner = _extract_event(event)
            logger.exception(
                "handler_error",
                error=str(exc),
                event_type=type(event).__name__,
                inner_type=type(inner).__name__ if inner else None,
                user_id=getattr(getattr(inner, "from_user", None), "id", None),
            )
            await self._notify_user(inner)
            return None

    async def _notify_user(self, event: Message | CallbackQuery | None) -> None:
        if event is None:
            return
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
    if event.update and event.update.callback_query:
        try:
            await event.update.callback_query.answer(
                "❌ Erro interno. Tente novamente.",
                show_alert=True,
            )
        except Exception:
            pass
    return True