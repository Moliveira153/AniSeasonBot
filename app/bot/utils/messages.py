"""Safe Telegram message helpers."""

from __future__ import annotations

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.utils.logging import get_logger

logger = get_logger(__name__)


async def answer_callback(callback: CallbackQuery, text: str | None = None) -> None:
    """Answer callback to remove loading spinner."""
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


def _callback_chat_id(callback: CallbackQuery) -> int:
    if callback.message and isinstance(callback.message, Message):
        return callback.message.chat.id
    return callback.from_user.id


async def edit_or_send(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> None:
    """Edit originating message or send a new one as fallback."""
    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            return
        except TelegramAPIError as exc:
            logger.warning("edit_or_send_edit_failed", error=str(exc))

        try:
            await callback.message.answer(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            return
        except TelegramAPIError as exc:
            logger.warning("edit_or_send_answer_failed", error=str(exc))

    try:
        await callback.bot.send_message(
            _callback_chat_id(callback),
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except TelegramAPIError as exc:
        logger.error("edit_or_send_send_failed", error=str(exc))
        raise


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