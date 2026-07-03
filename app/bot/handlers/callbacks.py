"""Shared callback handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.anime import show_anime_detail
from app.bot.texts.i18n import I18n
from app.database.repositories.anime_repo import AnimeRepository
from app.services.tracking_service import TrackingService
from app.services.user_service import UserService

router = Router(name="callbacks")


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("toggle:"))
async def toggle_tracking(callback: CallbackQuery, session: AsyncSession) -> None:
    anilist_id = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    i18n = I18n(user.language)
    tracking_service = TrackingService(session)
    anime_repo = AnimeRepository(session)

    anime = await anime_repo.get_by_anilist_id(anilist_id)
    if anime and await tracking_service.tracking_repo.is_tracked(user.id, anime.id):
        await tracking_service.remove_anime(user, anime.id)
        await callback.answer(i18n.t("removed"))
    else:
        try:
            await tracking_service.add_anime(user, anilist_id)
            await callback.answer(i18n.t("added"))
        except ValueError:
            await callback.answer(i18n.t("not_found"), show_alert=True)


@router.callback_query(F.data.startswith("detail:"))
async def show_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    anilist_id = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    await show_anime_detail(callback.message, session, anilist_id)  # type: ignore[arg-type]
    await callback.answer()


@router.callback_query(F.data.startswith("remove:"))
async def remove_anime(callback: CallbackQuery, session: AsyncSession) -> None:
    anime_id = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    i18n = I18n(user.language)
    tracking_service = TrackingService(session)
    await tracking_service.remove_anime(user, anime_id)
    await callback.answer(i18n.t("removed"))


@router.callback_query(F.data.startswith("mute:"))
async def mute_anime(callback: CallbackQuery, session: AsyncSession) -> None:
    anime_id = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    tracking_service = TrackingService(session)
    enabled = await tracking_service.toggle_notifications(user, anime_id)
    status = "🔔" if enabled else "🔕"
    await callback.answer(f"{status}")


@router.callback_query(F.data.startswith("watched:"))
async def mark_watched(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":")  # type: ignore[union-attr]
    anime_id = int(parts[1])
    episode = int(parts[2]) if len(parts) > 2 else None
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    tracking_service = TrackingService(session)
    await tracking_service.mark_watched(user, anime_id, episode)
    await callback.answer("✓")