"""Inline keyboard builders."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.texts.i18n import I18n
from app.database.models.anime import Anime
from app.utils.pagination import Page


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇧🇷 Português", callback_data="lang:pt-BR"),
                InlineKeyboardButton(text="🇺🇸 English", callback_data="lang:en"),
            ]
        ]
    )


def timezone_keyboard() -> InlineKeyboardMarkup:
    zones = [
        ("America/Sao_Paulo", "🇧🇷 BRT"),
        ("America/New_York", "🇺🇸 EST"),
        ("Europe/London", "🇬🇧 GMT"),
        ("Asia/Tokyo", "🇯🇵 JST"),
    ]
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"tz:{tz}")]
        for tz, label in zones
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def yes_no_keyboard(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Sim / Yes", callback_data=yes_data),
                InlineKeyboardButton(text="❌ Não / No", callback_data=no_data),
            ]
        ]
    )


def season_anime_keyboard(
    animes: list[Anime],
    page: Page[Anime],
    tracked_ids: set[int],
    i18n: I18n,
    onboarding: bool = False,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for anime in animes:
        icon = "✅" if anime.anilist_id in tracked_ids else "➕"
        rows.append([
            InlineKeyboardButton(
                text=f"{icon} {anime.display_title[:40]}",
                callback_data=f"toggle:{anime.anilist_id}",
            ),
            InlineKeyboardButton(
                text="ℹ️",
                callback_data=f"detail:{anime.anilist_id}",
            ),
        ])

    nav_row: list[InlineKeyboardButton] = []
    if page.has_prev:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"season_page:{page.page - 1}"))
    nav_row.append(
        InlineKeyboardButton(
            text=i18n.t("page_indicator", page=page.page, total=page.total_pages),
            callback_data="noop",
        )
    )
    if page.has_next:
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"season_page:{page.page + 1}"))
    rows.append(nav_row)

    if onboarding:
        rows.append([
            InlineKeyboardButton(text=i18n.t("finish_selection"), callback_data="onboard:finish")
        ])

    rows.append([
        InlineKeyboardButton(text="🔍 Filtros", callback_data="season:filters"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def anime_detail_keyboard(anime: Anime, is_tracked: bool, i18n: I18n) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    track_text = "❌ Remover" if is_tracked else "➕ Acompanhar"
    if not i18n.language.startswith("pt"):
        track_text = "❌ Remove" if is_tracked else "➕ Track"
    rows.append([
        InlineKeyboardButton(text=track_text, callback_data=f"toggle:{anime.anilist_id}"),
    ])

    if anime.trailer_url:
        rows.append([
            InlineKeyboardButton(text="▶️ Trailer", url=anime.trailer_url),
        ])

    links_row: list[InlineKeyboardButton] = []
    if anime.site_url:
        links_row.append(InlineKeyboardButton(text="AniList", url=anime.site_url))
    if anime.mal_id:
        links_row.append(
            InlineKeyboardButton(
                text="MAL",
                url=f"https://myanimelist.net/anime/{anime.mal_id}",
            )
        )
    if links_row:
        rows.append(links_row)

    rows.append([
        InlineKeyboardButton(text="◀️ Voltar", callback_data="back:season"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tracking_list_keyboard(trackings: list, page: int, total_pages: int, i18n: I18n) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for t in trackings:
        anime = t.anime
        rows.append([
            InlineKeyboardButton(
                text=f"📺 {anime.display_title[:35]}",
                callback_data=f"detail:{anime.anilist_id}",
            ),
            InlineKeyboardButton(text="❌", callback_data=f"remove:{anime.id}"),
            InlineKeyboardButton(text="🔕", callback_data=f"mute:{anime.id}"),
        ])

    nav: list[InlineKeyboardButton] = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"list_page:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"list_page:{page + 1}"))
    rows.append(nav)

    rows.append([
        InlineKeyboardButton(text="↕️ Ordenar", callback_data="list:sort"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_keyboard(i18n: I18n, prefs: dict) -> InlineKeyboardMarkup:
    enabled = prefs.get("notifications_enabled", True)
    notif_text = "🔔 ON" if enabled else "🔕 OFF"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Notificações: {notif_text}", callback_data="set:notifications")],
            [InlineKeyboardButton(text="🌐 Idioma", callback_data="set:language")],
            [InlineKeyboardButton(text="🕐 Fuso horário", callback_data="set:timezone")],
            [
                InlineKeyboardButton(
                    text=f"Imagens: {'ON' if prefs.get('send_images', True) else 'OFF'}",
                    callback_data="set:images",
                ),
                InlineKeyboardButton(
                    text=f"Spoilers: {'ON' if not prefs.get('hide_spoilers') else 'OFF'}",
                    callback_data="set:spoilers",
                ),
            ],
            [InlineKeyboardButton(text="🗑️ Excluir meus dados", callback_data="set:delete")],
        ]
    )


def confirm_delete_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚠️ Confirmar", callback_data="delete:confirm"),
                InlineKeyboardButton(text="❌ Cancelar", callback_data="delete:cancel"),
            ]
        ]
    )


def search_results_keyboard(animes: list[Anime], page: int, total_pages: int, query: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for anime in animes:
        rows.append([
            InlineKeyboardButton(
                text=anime.display_title[:40],
                callback_data=f"detail:{anime.anilist_id}",
            ),
            InlineKeyboardButton(text="➕", callback_data=f"toggle:{anime.anilist_id}"),
        ])
    nav: list[InlineKeyboardButton] = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"search_page:{page - 1}:{query[:20]}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"search_page:{page + 1}:{query[:20]}"))
    if nav:
        rows.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=rows)