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
from app.services.user_service import UserService

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(
        telegram_id=message.from_user.id,  # type: ignore[union-attr]
        first_name=message.from_user.first_name,  # type: ignore[union-attr]
        username=message.from_user.username,  # type: ignore[union-attr]
    )
    i18n = I18n(user.language)
    await state.clear()
    await message.answer(i18n.t("welcome"), parse_mode="Markdown")
    await message.answer(i18n.t("choose_language"), reply_markup=language_keyboard())
    await state.set_state(OnboardingStates.language)


@router.callback_query(F.data.startswith("lang:"))
async def on_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    lang = callback.data.split(":")[1]  # type: ignore[union-attr]
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    await user_service.update_language(user, lang)
    i18n = I18n(lang)
    await callback.message.edit_text(i18n.t("choose_timezone"), reply_markup=timezone_keyboard())  # type: ignore[union-attr]
    await state.set_state(OnboardingStates.timezone)
    await callback.answer()


@router.callback_query(F.data.startswith("tz:"))
async def on_timezone(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    tz = callback.data.split(":")[1]  # type: ignore[union-attr]
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    await user_service.update_timezone(user, tz)
    i18n = I18n(user.language)
    await callback.message.edit_text(  # type: ignore[union-attr]
        i18n.t("onboarding_season"),
        reply_markup=yes_no_keyboard("onboard:season_yes", "onboard:season_no"),
    )
    await state.set_state(OnboardingStates.season_choice)
    await callback.answer()


@router.callback_query(F.data == "onboard:season_yes")
async def onboard_season_yes(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    from app.bot.handlers.season import show_season_page

    await state.set_state(OnboardingStates.season_browse)
    await show_season_page(callback, session, page=1, onboarding=True)
    await callback.answer()


@router.callback_query(F.data == "onboard:season_no")
async def onboard_season_no(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    i18n = I18n(user.language)
    await state.clear()
    await callback.message.edit_text(  # type: ignore[union-attr]
        f"{i18n.t('welcome')}\n\nUse /ajuda para ver os comandos.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "onboard:finish")
async def onboard_finish(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    i18n = I18n(user.language)
    await state.clear()
    await callback.message.edit_text(  # type: ignore[union-attr]
        f"✅ {i18n.t('finish_selection')}\n\nUse /minhalista para ver seus animes.",
        parse_mode="Markdown",
    )
    await callback.answer()


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