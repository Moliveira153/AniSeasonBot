"""Notification detection and delivery service."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database.models.anime import Anime
from app.database.models.tracking import Tracking
from app.database.repositories.anime_repo import AnimeRepository
from app.database.repositories.notification_repo import NotificationRepository
from app.database.repositories.tracking_repo import TrackingRepository
from app.database.repositories.user_repo import UserRepository
from app.services.anime_service import AnimeService
from app.utils.datetime_fmt import format_datetime, format_relative
from app.utils.logging import get_logger

logger = get_logger(__name__)

EVENT_NEW_EPISODE = "new_episode"
EVENT_SCHEDULE_CHANGE = "schedule_change"
EVENT_HIATUS = "hiatus"
EVENT_RETURN = "return_from_hiatus"
EVENT_STATUS_CHANGE = "status_change"
EVENT_FINISHED = "finished"
EVENT_EPISODE_COUNT = "episode_count_change"
EVENT_TRAILER = "trailer_added"


class NotificationService:
    def __init__(
        self,
        session: AsyncSession,
        bot: Bot | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.session = session
        self.bot = bot
        self.settings = settings or get_settings()
        self.anime_repo = AnimeRepository(session)
        self.tracking_repo = TrackingRepository(session)
        self.notification_repo = NotificationRepository(session)
        self.user_repo = UserRepository(session)
        self.anime_service = AnimeService(session)

    @staticmethod
    def make_idempotency_key(
        user_id: int,
        anime_id: int,
        event_type: str,
        episode: int | None = None,
        extra: str = "",
    ) -> str:
        raw = f"{user_id}:{anime_id}:{event_type}:{episode}:{extra}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def make_event_key(anime_id: int, event_type: str, episode: int | None = None, extra: str = "") -> str:
        raw = f"event:{anime_id}:{event_type}:{episode}:{extra}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    async def detect_changes(old: Anime, new: Anime) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        if old.status != new.status:
            event_type = EVENT_FINISHED if new.status == "FINISHED" else EVENT_STATUS_CHANGE
            if new.status == "HIATUS" or (old.status == "RELEASING" and new.status == "HIATUS"):
                event_type = EVENT_HIATUS
            if old.status == "HIATUS" and new.status == "RELEASING":
                event_type = EVENT_RETURN
            events.append({
                "type": event_type,
                "old": {"status": old.status},
                "new": {"status": new.status},
            })

        if old.episodes != new.episodes and new.episodes:
            events.append({
                "type": EVENT_EPISODE_COUNT,
                "old": {"episodes": old.episodes},
                "new": {"episodes": new.episodes},
            })

        if old.next_airing_at != new.next_airing_at or old.next_episode != new.next_episode:
            if new.next_episode and old.next_episode and new.next_episode > old.next_episode:
                events.append({
                    "type": EVENT_NEW_EPISODE,
                    "episode": old.next_episode,
                    "old": {"episode": old.next_episode, "airing_at": str(old.next_airing_at)},
                    "new": {"episode": new.next_episode, "airing_at": str(new.next_airing_at)},
                })
            elif old.next_airing_at and new.next_airing_at and old.next_airing_at != new.next_airing_at:
                events.append({
                    "type": EVENT_SCHEDULE_CHANGE,
                    "episode": new.next_episode,
                    "old": {"airing_at": str(old.next_airing_at)},
                    "new": {"airing_at": str(new.next_airing_at)},
                })

        if not old.trailer_url and new.trailer_url:
            events.append({
                "type": EVENT_TRAILER,
                "new": {"trailer_url": new.trailer_url},
            })

        return events

    async def process_anime_sync(self, anilist_id: int) -> int:
        old_anime = await self.anime_repo.get_by_anilist_id(anilist_id)
        if not old_anime:
            new_anime = await self.anime_service.sync_from_anilist(anilist_id)
            return 0 if not new_anime else 0

        snapshot = {
            "status": old_anime.status,
            "episodes": old_anime.episodes,
            "next_episode": old_anime.next_episode,
            "next_airing_at": old_anime.next_airing_at,
            "trailer_url": old_anime.trailer_url,
        }

        new_anime = await self.anime_service.sync_from_anilist(anilist_id)
        if not new_anime:
            return 0

        from copy import copy

        old_copy = copy(old_anime)
        for k, v in snapshot.items():
            setattr(old_copy, k, v)

        events = await NotificationService.detect_changes(old_copy, new_anime)
        created = 0
        for event_data in events:
            event_key = self.make_event_key(
                new_anime.id,
                event_data["type"],
                event_data.get("episode"),
                extra=str(event_data.get("new", {})),
            )
            event = await self.notification_repo.create_event(
                anime_id=new_anime.id,
                event_type=event_data["type"],
                idempotency_key=event_key,
                episode=event_data.get("episode"),
                old_data=event_data.get("old"),
                new_data=event_data.get("new"),
            )
            if event:
                created += await self._queue_deliveries(event, new_anime, event_data)
        return created

    async def _queue_deliveries(
        self,
        event: Any,
        anime: Anime,
        event_data: dict[str, Any],
    ) -> int:
        trackings = await self.tracking_repo.get_users_tracking_anime(anime.id)
        count = 0
        for tracking in trackings:
            user = tracking.user
            if not user.notifications_enabled or user.bot_blocked:
                continue
            if not self._should_notify(user, tracking, event_data["type"]):
                continue

            idem_key = self.make_idempotency_key(
                user.id,
                anime.id,
                event_data["type"],
                event_data.get("episode"),
            )
            delivery = await self.notification_repo.create_delivery(
                user_id=user.id,
                anime_id=anime.id,
                event_id=event.id,
                event_type=event_data["type"],
                idempotency_key=idem_key,
                episode=event_data.get("episode"),
                payload=event_data,
            )
            if delivery:
                count += 1
        return count

    def _should_notify(self, user: Any, tracking: Tracking, event_type: str) -> bool:
        if not tracking.notifications_enabled:
            return False
        prefs = user.preferences
        mapping = {
            EVENT_NEW_EPISODE: prefs.get("alert_on_release", True),
            EVENT_SCHEDULE_CHANGE: prefs.get("alert_on_delay", True),
            EVENT_HIATUS: prefs.get("alert_on_hiatus", True),
            EVENT_FINISHED: prefs.get("alert_on_finish", True),
        }
        return mapping.get(event_type, True)

    async def send_pending(self) -> int:
        if not self.bot:
            return 0
        deliveries = await self.notification_repo.get_pending_deliveries()
        sent = 0
        for delivery in deliveries:
            try:
                anime = await self.anime_repo.get_by_id(delivery.anime_id)
                if not anime:
                    continue
                from sqlalchemy import select
                from app.database.models.user import User

                result = await self.session.execute(
                    select(User).where(User.id == delivery.user_id)
                )
                user = result.scalar_one_or_none()
                if not user or user.bot_blocked:
                    continue

                text, keyboard = self._build_message(user, anime, delivery)
                if user.preferences.get("send_images", True) and anime.cover_image:
                    await self.bot.send_photo(
                        user.telegram_id,
                        anime.cover_image,
                        caption=text,
                        parse_mode="Markdown",
                        reply_markup=keyboard,
                    )
                else:
                    await self.bot.send_message(
                        user.telegram_id,
                        text,
                        parse_mode="Markdown",
                        reply_markup=keyboard,
                    )
                await self.notification_repo.mark_sent(delivery.id)
                sent += 1
            except TelegramForbiddenError:
                if user:
                    await self.user_repo.mark_bot_blocked(user.telegram_id)
            except Exception as exc:
                logger.error("notification_send_failed", delivery_id=delivery.id, error=str(exc))
                await self.notification_repo.mark_failed(delivery.id, str(exc))
        return sent

    def _build_message(
        self,
        user: Any,
        anime: Anime,
        delivery: Any,
    ) -> tuple[str, InlineKeyboardMarkup | None]:
        lang = user.language
        event_type = delivery.event_type
        episode = delivery.episode or anime.next_episode

        if event_type == EVENT_NEW_EPISODE:
            title = "🎬 Novo episódio lançado!" if lang.startswith("pt") else "🎬 New episode released!"
            rel = format_relative(anime.next_airing_at, user.timezone, lang) if anime.next_airing_at else "—"
            lines = [
                title,
                "",
                f"*{anime.display_title}*",
                f"Episódio: {episode}" if lang.startswith("pt") else f"Episode: {episode}",
            ]
            if anime.next_airing_at:
                lines.append(
                    f"Lançamento: {rel}" if lang.startswith("pt") else f"Released: {rel}"
                )
        elif event_type == EVENT_FINISHED:
            title = "✅ Anime finalizado!" if lang.startswith("pt") else "✅ Anime finished!"
            lines = [
                title,
                "",
                f"*{anime.display_title}*",
                f"Total: {anime.episodes} episódios" if lang.startswith("pt") else f"Total: {anime.episodes} episodes",
            ]
            if anime.average_score:
                lines.append(f"Nota: {anime.average_score / 10:.1f}/10")
        elif event_type == EVENT_SCHEDULE_CHANGE:
            title = "📅 Horário alterado" if lang.startswith("pt") else "📅 Schedule changed"
            dt = format_datetime(anime.next_airing_at, user.timezone, lang)
            lines = [title, "", f"*{anime.display_title}*", f"Novo horário: {dt}" if lang.startswith("pt") else f"New time: {dt}"]
        elif event_type == EVENT_HIATUS:
            title = "⏸️ Anime em hiato" if lang.startswith("pt") else "⏸️ Anime on hiatus"
            lines = [title, "", f"*{anime.display_title}*"]
        else:
            lines = [f"📢 *{anime.display_title}*", f"Evento: {event_type}"]

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Detalhes" if lang.startswith("pt") else "Details",
                        callback_data=f"detail:{anime.anilist_id}",
                    ),
                    InlineKeyboardButton(
                        text="✓ Assistido" if lang.startswith("pt") else "✓ Watched",
                        callback_data=f"watched:{anime.id}:{episode or 0}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔕 Silenciar" if lang.startswith("pt") else "🔕 Mute",
                        callback_data=f"mute:{anime.id}",
                    ),
                    InlineKeyboardButton(
                        text="❌ Remover" if lang.startswith("pt") else "❌ Remove",
                        callback_data=f"remove:{anime.id}",
                    ),
                ],
            ]
        )
        return "\n".join(lines), keyboard