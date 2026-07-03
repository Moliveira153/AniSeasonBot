"""Safe Telegram message helpers."""

from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup


async def answer_callback(callback: CallbackQuery, text: str | None = None) -> None:
    """Answer callback immediately to remove loading spinner."""
    try:
        await callback.answer(text)
    except TelegramBadRequest:
        pass


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