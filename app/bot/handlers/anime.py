"""Anime detail handlers."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import anime_detail_keyboard
from app.bot.states.onboarding import AnimeStates
from app.bot.texts.i18n import I18n
from app.database.repositories.tracking_repo import TrackingRepository
from app.services.anime_service import AnimeService
from app.services.user_service import UserService
from app.utils.datetime_fmt import countdown, format_datetime
from app.utils.html_clean import clean_html, split_telegram_message

router = Router(name="anime")


async def show_anime_detail(
    message: Message,
    session: AsyncSession,
    anilist_id: int,
    full_description: bool = False,
) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.chat.id)
    i18n = I18n(user.language)
    anime_service = AnimeService(session)
    anime = await anime_service.get_or_fetch(anilist_id)

    if not anime:
        await message.answer(i18n.t("not_found"))
        return

    tracking_repo = TrackingRepository(session)
    is_tracked = await tracking_repo.is_tracked(user.id, anime.id)

    lines = [f"*{anime.display_title}*"]
    if anime.title_romaji:
        lines.append(f"Romaji: {anime.title_romaji}")
    if anime.title_english and anime.title_english != anime.display_title:
        lines.append(f"English: {anime.title_english}")
    if anime.title_native:
        lines.append(f"Native: {anime.title_native}")
    if anime.synonyms:
        lines.append(f"Synonyms: {', '.join(anime.synonyms[:3])}")
    if anime.status:
        lines.append(f"Status: {anime.status}")
    if anime.format:
        lines.append(f"Format: {anime.format}")
    if anime.season and anime.season_year:
        lines.append(f"Season: {anime.season} {anime.season_year}")
    if anime.episodes:
        lines.append(f"Episodes: {anime.episodes}")
    if anime.duration:
        lines.append(f"Duration: {anime.duration} min/ep")
    if anime.genres:
        lines.append(f"Genres: {', '.join(anime.genres)}")
    if anime.studios:
        lines.append(f"Studios: {', '.join(anime.studios)}")
    if anime.average_score:
        lines.append(f"Score: {anime.average_score / 10:.1f}/10")
    if anime.popularity:
        lines.append(f"Popularity: #{anime.popularity}")
    if anime.next_episode and anime.next_airing_at:
        dt = format_datetime(anime.next_airing_at, user.timezone, user.language)
        cd = countdown(anime.next_airing_at, user.timezone)
        lines.append(f"Next ep. {anime.next_episode}: {dt} ({cd})")

    if anime.description and not user.hide_spoilers:
        desc_limit = None if full_description else 500
        desc = clean_html(anime.description, max_length=desc_limit)
        if desc:
            header = i18n.t("description_truncated") if not full_description else "📝 Description"
            lines.append(f"\n{header}:\n{desc}")

    text = "\n".join(lines)
    keyboard = anime_detail_keyboard(anime, is_tracked, i18n)

    if anime.banner_image or anime.cover_image:
        photo = anime.banner_image or anime.cover_image
        parts = split_telegram_message(text, 1024)
        await message.answer_photo(photo, caption=parts[0], parse_mode="Markdown", reply_markup=keyboard)
        for part in parts[1:]:
            await message.answer(part, parse_mode="Markdown")
    else:
        for part in split_telegram_message(text):
            await message.answer(part, parse_mode="Markdown", reply_markup=keyboard)


@router.message(Command("anime"))
async def cmd_anime(message: Message, state: FSMContext, session: AsyncSession) -> None:
    args = message.text.split(maxsplit=1) if message.text else []  # type: ignore[union-attr]
    if len(args) > 1:
        query = args[1].strip()
        if query.isdigit():
            await show_anime_detail(message, session, int(query))
            return
        anime_service = AnimeService(session)
        user_service = UserService(session)
        user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
        results = await anime_service.search(query, hide_adult=user.hide_adult)
        if results:
            await show_anime_detail(message, session, results[0].anilist_id)
            return

    i18n = I18n()
    await message.answer("Usage: /anime <id or name>")
    await state.set_state(AnimeStates.waiting_id_or_name)


@router.message(AnimeStates.waiting_id_or_name)
async def on_anime_query(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    if not message.text:
        return
    if message.text.isdigit():
        await show_anime_detail(message, session, int(message.text))
    else:
        anime_service = AnimeService(session)
        results = await anime_service.search(message.text)
        if results:
            await show_anime_detail(message, session, results[0].anilist_id)