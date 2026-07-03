"""Schedule and calendar handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.texts.i18n import I18n
from app.services.schedule_service import ScheduleService
from app.services.user_service import UserService
from app.utils.datetime_fmt import format_datetime

router = Router(name="schedule")


@router.message(Command("hoje", "today"))
async def cmd_today(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    i18n = I18n(user.language)
    schedule_service = ScheduleService(session)
    episodes = await schedule_service.get_today_episodes(user)

    if not episodes:
        await message.answer(f"{i18n.t('today_title')}\n\nNenhum episódio hoje.")
        return

    lines = [i18n.t("today_title"), ""]
    for anime, ep, airing_at in episodes:
        time_str = format_datetime(airing_at, user.timezone, user.language)
        lines.append(f"• {time_str} — {anime.display_title} ep.{ep}")
    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(Command("semana", "week"))
async def cmd_week(message: Message, session: AsyncSession) -> None:
    await _show_week(message, session, offset=0)


@router.callback_query(F.data.startswith("week:"))
async def on_week_nav(callback: CallbackQuery, session: AsyncSession) -> None:
    offset = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    await _show_week(callback.message, session, offset=offset)  # type: ignore[arg-type]
    await callback.answer()


async def _show_week(message: Message, session: AsyncSession, offset: int = 0) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.chat.id)
    i18n = I18n(user.language)
    schedule_service = ScheduleService(session)
    calendar = await schedule_service.get_week_calendar(user, week_offset=offset)

    lines = [i18n.t("week_title"), ""]
    for day in sorted(calendar.keys()):
        items = calendar[day]
        lines.append(f"*{day}*")
        for anime, ep, airing_at in items:
            time_str = format_datetime(airing_at, user.timezone, user.language)
            lines.append(f"  {time_str} — {anime.display_title} ep.{ep}")
        lines.append("")

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️", callback_data=f"week:{offset - 1}"),
                InlineKeyboardButton(text="▶️", callback_data=f"week:{offset + 1}"),
            ]
        ]
    )
    await message.answer("\n".join(lines)[:4000], parse_mode="Markdown", reply_markup=keyboard)


@router.message(Command("proximos", "upcoming"))
async def cmd_upcoming(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    i18n = I18n(user.language)
    schedule_service = ScheduleService(session)
    upcoming = await schedule_service.get_upcoming_from_list(user)

    if not upcoming:
        await message.answer(i18n.t("no_upcoming"))
        return

    lines = [i18n.t("upcoming_title"), ""]
    for anime, ep, airing_at in upcoming:
        if airing_at:
            dt = format_datetime(airing_at, user.timezone, user.language)
            lines.append(f"• {anime.display_title} ep.{ep} — {dt}")
    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(Command("lancamentos", "releases"))
async def cmd_releases(message: Message, session: AsyncSession) -> None:
    from app.services.season_service import SeasonService

    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    season_service = SeasonService(session)
    from app.services.season_service import SeasonFilters

    animes, _, season_info = await season_service.get_season_page(
        page=1,
        filters=SeasonFilters(airing_only=True, hide_adult=user.hide_adult),
    )
    lines = [f"📡 Lançamentos — {season_info.label_pt}", ""]
    for anime in animes[:10]:
        lines.append(f"• {anime.display_title} — {anime.status}")
    await message.answer("\n".join(lines), parse_mode="Markdown")