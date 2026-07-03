"""Search handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import search_results_keyboard
from app.bot.states.onboarding import SearchStates
from app.bot.texts.i18n import I18n
from app.services.anime_service import AnimeService
from app.services.user_service import UserService
from app.utils.pagination import paginate

router = Router(name="search")


@router.message(Command("buscar", "search"))
async def cmd_search(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    i18n = I18n(user.language)

    args = message.text.split(maxsplit=1) if message.text else []  # type: ignore[union-attr]
    if len(args) > 1:
        await _do_search(message, session, user, args[1], page=1)
        return

    await message.answer(i18n.t("search_prompt"))
    await state.set_state(SearchStates.waiting_query)


@router.message(SearchStates.waiting_query)
async def on_search_query(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(message.from_user.id)  # type: ignore[union-attr]
    await state.clear()
    if message.text:
        await _do_search(message, session, user, message.text, page=1)


async def _do_search(
    message: Message,
    session: AsyncSession,
    user: object,
    query: str,
    page: int = 1,
) -> None:
    from app.database.models.user import User

    assert isinstance(user, User)
    i18n = I18n(user.language)
    anime_service = AnimeService(session)
    results = await anime_service.search(query, page=page, hide_adult=user.hide_adult)
    if not results:
        await message.answer(i18n.t("not_found"))
        return

    page_obj = paginate(results, page=page, per_page=5)
    text = i18n.t("search_results", query=query)
    keyboard = search_results_keyboard(
        list(page_obj.items), page_obj.page, page_obj.total_pages, query
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


@router.callback_query(F.data.startswith("search_page:"))
async def on_search_page(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":", 2)  # type: ignore[union-attr]
    page = int(parts[1])
    query = parts[2] if len(parts) > 2 else ""
    user_service = UserService(session)
    user = await user_service.get_or_create_from_telegram(callback.from_user.id)
    await _do_search(callback.message, session, user, query, page=page)  # type: ignore[arg-type]
    await callback.answer()


@router.inline_query()
async def inline_search(inline_query: InlineQuery, session: AsyncSession) -> None:
    if not inline_query.query or len(inline_query.query) < 2:
        await inline_query.answer([], cache_time=1)
        return

    anime_service = AnimeService(session)
    results = await anime_service.search(inline_query.query, page=1)
    articles = []
    for anime in results[:20]:
        articles.append(
            InlineQueryResultArticle(
                id=str(anime.anilist_id),
                title=anime.display_title,
                description=f"{anime.format or ''} | {anime.status or ''}",
                input_message_content=InputTextMessageContent(
                    message_text=f"/anime {anime.anilist_id}",
                ),
                thumbnail_url=anime.cover_image,
            )
        )
    await inline_query.answer(articles, cache_time=60)