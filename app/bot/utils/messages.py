"""Safe Telegram message helpers."""

from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.utils.logging import get_logger

logger = get_logger(__name__)


async def answer_callback(callback: CallbackQuery, text: str | None = None) -> None:
    """Answer callback immediately to remove loading spinner."""
    try:
        await callback.answer(text)
    except TelegramBadRequest:
        pass


async def safe_reply(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> None:
    """Send message with fallback to plain text if parse mode fails."""
    try:
        await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as exc:
        logger.warning("safe_reply_retry_plain", error=str(exc))
        await message.answer(text, reply_markup=reply_markup, parse_mode=None)


async def edit_or_send(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> None:
    """Edit message or send new one if edit fails."""
    if not callback.message:
        return
    try:
        await callback.message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )


async def safe_fsm_clear(state: object) -> None:
    try:
        await state.clear()  # type: ignore[attr-defined]
    except Exception as exc:
        logger.warning("fsm_clear_failed", error=str(exc))


async def safe_fsm_set_state(state: object, new_state: object) -> None:
    try:
        await state.set_state(new_state)  # type: ignore[attr-defined]
    except Exception as exc:
        logger.warning("fsm_set_state_failed", error=str(exc))