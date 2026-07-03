"""Settings handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import confirm_delete_keyboard, language_keyboard, settings_keyboard, timezone_keyboard
from app.bot.texts.i18n import I18n
from app.services.user_service import UserService

router = Router(name="settings")


@router.message(Command("configuracoes", "settings"))
async def cmd_settings(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    i18n = I18n(user.language)
    await message.answer(
        i18n.t("settings_title"),
        parse_mode="Markdown",
        reply_markup=settings_keyboard(i18n, user.preferences),
    )


@router.message(Command("pausar", "pause"))
async def cmd_pause(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    await user_service.pause_notifications(user)
    i18n = I18n(user.language)
    await message.answer(i18n.t("notifications_paused"))


@router.message(Command("retomar", "resume"))
async def cmd_resume(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    await user_service.resume_notifications(user)
    i18n = I18n(user.language)
    await message.answer(i18n.t("notifications_resumed"))


@router.message(Command("excluirme", "deleteme"))
async def cmd_delete(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    i18n = I18n(user.language)
    await message.answer(i18n.t("delete_confirm"), reply_markup=confirm_delete_keyboard())


@router.callback_query(F.data == "delete:confirm")
async def on_delete_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    i18n = I18n(user.language)
    await user_service.delete_user(user)
    await callback.message.edit_text(i18n.t("delete_done"))  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data == "delete:cancel")
async def on_delete_cancel(callback: CallbackQuery, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    i18n = I18n(user.language)
    await callback.message.edit_text(i18n.t("cancelled"))  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data == "set:notifications")
async def toggle_notifications(callback: CallbackQuery, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    current = user.preferences.get("notifications_enabled", True)
    await user_service.update_preferences(user, {"notifications_enabled": not current})
    i18n = I18n(user.language)
    await callback.message.edit_reply_markup(  # type: ignore[union-attr]
        reply_markup=settings_keyboard(i18n, user.preferences)
    )
    await callback.answer()


@router.callback_query(F.data == "set:language")
async def set_language(callback: CallbackQuery, session: AsyncSession) -> None:
    from app.bot.utils.messages import answer_callback, edit_or_send

    await answer_callback(callback)
    await edit_or_send(callback, "🌐 Escolha seu idioma:", reply_markup=language_keyboard())


@router.callback_query(F.data == "set:timezone")
async def set_timezone(callback: CallbackQuery, session: AsyncSession) -> None:
    from app.bot.utils.messages import answer_callback, edit_or_send

    await answer_callback(callback)
    await edit_or_send(callback, "🕐 Escolha seu fuso horário:", reply_markup=timezone_keyboard())


@router.callback_query(F.data == "set:images")
async def toggle_images(callback: CallbackQuery, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    current = user.preferences.get("send_images", True)
    await user_service.update_preferences(user, {"send_images": not current})
    i18n = I18n(user.language)
    await callback.message.edit_reply_markup(  # type: ignore[union-attr]
        reply_markup=settings_keyboard(i18n, user.preferences)
    )
    await callback.answer()


@router.callback_query(F.data == "set:spoilers")
async def toggle_spoilers(callback: CallbackQuery, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    current = user.preferences.get("hide_spoilers", False)
    await user_service.update_preferences(user, {"hide_spoilers": not current})
    i18n = I18n(user.language)
    await callback.message.edit_reply_markup(  # type: ignore[union-attr]
        reply_markup=settings_keyboard(i18n, user.preferences)
    )
    await callback.answer()


@router.callback_query(F.data == "set:delete")
async def settings_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    i18n = I18n(user.language)
    await callback.message.edit_text(  # type: ignore[union-attr]
        i18n.t("delete_confirm"),
        reply_markup=confirm_delete_keyboard(),
    )
    await callback.answer()