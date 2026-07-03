"""User preference schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    notifications_enabled: bool = True
    alert_on_release: bool = True
    alert_before_minutes: int = 0
    alert_on_delay: bool = True
    alert_on_hiatus: bool = True
    alert_on_finish: bool = True
    alert_on_sequel: bool = True
    daily_digest: bool = False
    weekly_digest: bool = False
    quiet_hours_start: str | None = None  # HH:MM
    quiet_hours_end: str | None = None
    hide_spoilers: bool = False
    hide_adult: bool = True
    send_images: bool = True
    compact_messages: bool = False
    date_format: str = "short"
    time_format: str = "24h"


class TrackingPreferences(BaseModel):
    notifications_enabled: bool | None = None
    hide_spoilers: bool | None = None
    alert_on_release: bool | None = None


DEFAULT_PREFERENCES = UserPreferences()