"""Airing schedule and calendar service."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.anilist import AniListClient
from app.config import get_settings
from app.database.models.anime import Anime
from app.database.models.user import User
from app.services.tracking_service import TrackingService
from app.utils.datetime_fmt import format_datetime, week_start


class ScheduleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.anilist = AniListClient(settings=self.settings)
        self.tracking_service = TrackingService(session)

    async def get_week_calendar(
        self,
        user: User,
        week_offset: int = 0,
    ) -> dict[str, list[tuple[Anime, int, datetime]]]:
        tz = ZoneInfo(user.timezone)
        now = datetime.now(tz)
        start = week_start(now + timedelta(weeks=week_offset), user.timezone)
        end = start + timedelta(days=7)

        start_ts = int(start.astimezone(timezone.utc).timestamp())
        end_ts = int(end.astimezone(timezone.utc).timestamp())

        page = await self.anilist.get_airing_schedules(start_ts, end_ts)
        tracked_ids = await self.tracking_service.get_tracked_anilist_ids(user)

        calendar: dict[str, list[tuple[Anime, int, datetime]]] = defaultdict(list)
        from app.services.anime_service import AnimeService

        anime_service = AnimeService(self.session, self.anilist)

        for schedule in page.airingSchedules:
            if not schedule.media:
                continue
            anime = await anime_service._persist_media(schedule.media)
            airing_at = datetime.fromtimestamp(schedule.airingAt, tz=timezone.utc)
            local = airing_at.astimezone(tz)
            day_key = local.strftime("%Y-%m-%d")
            calendar[day_key].append((anime, schedule.episode, airing_at))

        for day in calendar:
            calendar[day].sort(key=lambda x: x[2])

        return dict(calendar)

    def format_day_schedule(
        self,
        day: str,
        items: list[tuple[Anime, int, datetime]],
        user: User,
    ) -> str:
        lang = user.language
        lines = [f"📅 *{day}*"]
        for anime, episode, airing_at in items:
            time_str = format_datetime(airing_at, user.timezone, lang)
            marker = "⭐" if anime.anilist_id in set() else ""
            lines.append(f"{marker} {time_str} — {anime.display_title} ep.{episode}")
        return "\n".join(lines)

    async def get_today_episodes(self, user: User) -> list[tuple[Anime, int, datetime]]:
        calendar = await self.get_week_calendar(user, 0)
        tz = ZoneInfo(user.timezone)
        today = datetime.now(tz).strftime("%Y-%m-%d")
        return calendar.get(today, [])

    async def get_upcoming_from_list(self, user: User, limit: int = 10) -> list[tuple[Anime, int | None, datetime | None]]:
        trackings = await self.tracking_service.get_user_list(user, sort_by="next_airing")
        result: list[tuple[Anime, int | None, datetime | None]] = []
        for t in trackings:
            anime = t.anime
            if anime.next_airing_at:
                result.append((anime, anime.next_episode, anime.next_airing_at))
            if len(result) >= limit:
                break
        return result