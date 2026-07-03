"""Start and onboarding handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import language_keyboard, timezone_keyboard, yes_no_keyboard
from app.bot.states.onboarding import OnboardingStates
from app.bot.texts.i18n import I18n
from app.bot.utils.messages import (
    answer_callback,
    edit_or_send,
    safe_fsm_clear,
    safe_fsm_set_state,
    safe_reply,
)
from app.services.user_service import UserService
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = Router(name="start")

LANG_BY_CALLBACK: dict[str, str] = {
    "pt": "pt-BR",
    "pt-BR": "pt-BR",
    "en": "en",
}


def _parse_lang(data: str | None) -> str | None:
    if not data or not data.startswith("lang:"):
        return None
    code = data.split(":", 1)[1]
    return LANG_BY_CALLBACK.get(code)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(
        telegram_id=message.from_user.id,  # type: ignore[union-attr]
        first_name=message.from_user.first_name,  # type: ignore[union-attr]
        username=message.from_user.username,  # type: ignore[union-attr]
    )
    i18n = I18n(user.language)
    await safe_fsm_clear(state)
    await safe_reply(message, i18n.t("welcome"), parse_mode=None)
    await safe_reply(
        message,
        i18n.t("choose_language"),
        reply_markup=language_keyboard(),
        parse_mode=None,
    )
    await safe_fsm_set_state(state, OnboardingStates.language)
    logger.info("onboarding_started", user_id=message.from_user.id)  # type: ignore[union-attr]


@router.callback_query(F.data.startswith("lang:"))
async def on_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    lang = _parse_lang(callback.data)
    if not lang:
        await answer_callback(callback, "Idioma inválido.")
        return

    logger.info("language_selected", user_id=callback.from_user.id, lang=lang)

    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    await user_service.update_language(user, lang)
    i18n = I18n(lang)

    await edit_or_send(
        callback,
        i18n.t("choose_timezone"),
        reply_markup=timezone_keyboard(),
        parse_mode=None,
    )
    await safe_fsm_set_state(state, OnboardingStates.timezone)
    await answer_callback(callback)


@router.callback_query(F.data.startswith("tz:"))
async def on_timezone(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    if not callback.data or ":" not in callback.data:
        await answer_callback(callback, "Fuso horário inválido.")
        return
    tz = callback.data.split(":", 1)[1]
    logger.info("timezone_selected", user_id=callback.from_user.id, tz=tz)

    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    await user_service.update_timezone(user, tz)
    i18n = I18n(user.language)

    await edit_or_send(
        callback,
        i18n.t("onboarding_season"),
        reply_markup=yes_no_keyboard("onboard:season_yes", "onboard:season_no"),
        parse_mode=None,
    )
    await safe_fsm_set_state(state, OnboardingStates.season_choice)
    await answer_callback(callback)


@router.callback_query(F.data == "onboard:season_yes")
async def onboard_season_yes(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    from app.bot.handlers.season import show_season_page

    await safe_fsm_set_state(state, OnboardingStates.season_browse)
    await show_season_page(callback, session, page=1, onboarding=True)
    await answer_callback(callback)


@router.callback_query(F.data == "onboard:season_no")
async def onboard_season_no(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    i18n = I18n(user.language)
    await safe_fsm_clear(state)
    await edit_or_send(
        callback,
        f"{i18n.t('welcome')}\n\nUse /ajuda para ver os comandos.",
        parse_mode=None,
    )
    await answer_callback(callback)


@router.callback_query(F.data == "onboard:finish")
async def onboard_finish(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    i18n = I18n(user.language)
    await safe_fsm_clear(state)
    await edit_or_send(
        callback,
        f"✅ {i18n.t('finish_selection')}\n\nUse /minhalista para ver seus animes.",
        parse_mode=None,
    )
    await answer_callback(callback)


@router.message(Command("ajuda", "help"))
async def cmd_help(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    i18n = I18n(user.language)
    await message.answer(i18n.t("help"), parse_mode="Markdown")


@router.message(Command("sobre", "about"))
async def cmd_about(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    i18n = I18n(user.language)
    await message.answer(i18n.t("about"), parse_mode="Markdown")


@router.message(Command("privacidade", "privacy"))
async def cmd_privacy(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    i18n = I18n(user.language)
    await message.answer(i18n.t("privacy"), parse_mode="Markdown")


@router.message(Command("cancelar", "cancel"))
async def cmd_cancel(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    i18n = I18n(user.language)
    await state.clear()
    await message.answer(i18n.t("cancelled"))