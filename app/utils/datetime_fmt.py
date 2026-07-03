"""Date and time formatting with timezone support."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def to_user_timezone(dt: datetime | None, tz_name: str) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo(tz_name))


def format_datetime(
    dt: datetime | None,
    tz_name: str,
    language: str = "pt-BR",
    date_format: str = "short",
    time_format: str = "24h",
) -> str:
    if dt is None:
        return "—"
    local = to_user_timezone(dt, tz_name)
    if local is None:
        return "—"

    if language.startswith("pt"):
        date_fmt = "%d/%m/%Y" if date_format == "short" else "%d de %B de %Y"
        time_fmt = "%H:%M" if time_format == "24h" else "%I:%M %p"
        return f"{local.strftime(date_fmt)} às {local.strftime(time_fmt)}"

    date_fmt = "%m/%d/%Y" if date_format == "short" else "%B %d, %Y"
    time_fmt = "%H:%M" if time_format == "24h" else "%I:%M %p"
    return f"{local.strftime(date_fmt)} at {local.strftime(time_fmt)}"


def format_relative(
    dt: datetime | None,
    tz_name: str,
    language: str = "pt-BR",
    now: datetime | None = None,
) -> str:
    if dt is None:
        return "—"
    local = to_user_timezone(dt, tz_name)
    if local is None:
        return "—"
    if now is None:
        now = datetime.now(ZoneInfo(tz_name))
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(tz_name))

    delta = local.date() - now.date()
    if delta.days == 0:
        prefix = "hoje" if language.startswith("pt") else "today"
        time_str = local.strftime("%H:%M")
        return f"{prefix}, às {time_str}" if language.startswith("pt") else f"{prefix} at {time_str}"
    if delta.days == 1:
        return "amanhã" if language.startswith("pt") else "tomorrow"
    if delta.days == -1:
        return "ontem" if language.startswith("pt") else "yesterday"
    return format_datetime(dt, tz_name, language)


def countdown(dt: datetime | None, tz_name: str, now: datetime | None = None) -> str:
    if dt is None:
        return "—"
    local = to_user_timezone(dt, tz_name)
    if local is None:
        return "—"
    if now is None:
        now = datetime.now(ZoneInfo(tz_name))
    diff = local - now
    if diff.total_seconds() <= 0:
        return "agora" if True else "now"
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes = remainder // 60
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def week_start(dt: datetime, tz_name: str) -> datetime:
    local = to_user_timezone(dt, tz_name) or dt
    start = local - timedelta(days=local.weekday())
    return start.replace(hour=0, minute=0, second=0, microsecond=0)