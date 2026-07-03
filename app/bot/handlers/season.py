"""Season listing handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import season_anime_keyboard
from app.bot.texts.i18n import I18n
from app.services.anime_service import AnimeService
from app.services.season_service import SeasonService
from app.services.tracking_service import TrackingService
from app.services.user_service import UserService
from app.utils.pagination import Page

router = Router(name="season")


async def show_season_page(
    event: Message | CallbackQuery,
    session: AsyncSession,
    page: int = 1,
    onboarding: bool = False,
) -> None:
    user_service = UserService(session)
    if isinstance(event, CallbackQuery):
        user = await user_service.get_or_create_from_telegram(event.from_user.id)
    else:
        user = await user_service.get_or_create_from_telegram(event.from_user.id)  # type: ignore[union-attr]

    i18n = I18n(user.language)
    season_service = SeasonService(session)
    tracking_service = TrackingService(session)

    tracked = await tracking_service.get_tracked_anilist_ids(user)
    from app.services.season_service import SeasonFilters

    filters = SeasonFilters(hide_adult=user.hide_adult, hide_tracked=False, tracked_ids=tracked)
    animes, total, season_info = await season_service.get_season_page(
        page=page, per_page=5, filters=filters
    )

    per_page = 5
    total_pages = max(1, (total + per_page - 1) // per_page)
    page_obj = Page(items=animes, page=page, per_page=per_page, total=total)

    anime_service = AnimeService(session)
    text_parts = [i18n.t("season_title", season=season_info.label_pt if user.language.startswith("pt") else season_info.label_en)]
    for anime in animes:
        text_parts.append(anime_service.format_anime_card(anime, user.language))
        text_parts.append("—")

    text = "\n\n".join(text_parts)
    keyboard = season_anime_keyboard(animes, page_obj, tracked, i18n, onboarding=onboarding)

    if isinstance(event, CallbackQuery):
        try:
            if animes and animes[0].cover_image:
                await event.message.delete()  # type: ignore[union-attr]
                await event.message.answer_photo(  # type: ignore[union-attr]
                    animes[0].cover_image,
                    caption=text[:1024],
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            else:
                await event.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)  # type: ignore[union-attr]
        except Exception:
            await event.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)  # type: ignore[union-attr]
    else:
        await event.answer(text, parse_mode="Markdown", reply_markup=keyboard)


@router.message(Command("temporada", "season"))
async def cmd_season(message: Message, session: AsyncSession) -> None:
    await show_season_page(message, session, page=1)


@router.callback_query(F.data.startswith("season_page:"))
async def on_season_page(callback: CallbackQuery, session: AsyncSession) -> None:
    page = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    await show_season_page(callback, session, page=page)
    await callback.answer()