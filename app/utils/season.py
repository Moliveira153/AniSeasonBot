"""Season detection utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class Season(str, Enum):
    WINTER = "WINTER"
    SPRING = "SPRING"
    SUMMER = "SUMMER"
    FALL = "FALL"


SEASON_MONTHS: dict[Season, tuple[int, ...]] = {
    Season.WINTER: (12, 1, 2),
    Season.SPRING: (3, 4, 5),
    Season.SUMMER: (6, 7, 8),
    Season.FALL: (9, 10, 11),
}


@dataclass(frozen=True)
class SeasonInfo:
    season: Season
    year: int

    @property
    def label_pt(self) -> str:
        names = {
            Season.WINTER: "Inverno",
            Season.SPRING: "Primavera",
            Season.SUMMER: "Verão",
            Season.FALL: "Outono",
        }
        return f"{names[self.season]} {self.year}"

    @property
    def label_en(self) -> str:
        return f"{self.season.value.title()} {self.year}"


def detect_current_season(dt: date | datetime | None = None) -> SeasonInfo:
    """Detect the current anime season based on date."""
    if dt is None:
        dt = date.today()
    elif isinstance(dt, datetime):
        dt = dt.date()

    month = dt.month
    year = dt.year

    if month in (12, 1, 2):
        season = Season.WINTER
        season_year = year if month != 12 else year + 1
    elif month in (3, 4, 5):
        season = Season.SPRING
        season_year = year
    elif month in (6, 7, 8):
        season = Season.SUMMER
        season_year = year
    else:
        season = Season.FALL
        season_year = year

    return SeasonInfo(season=season, year=season_year)


def season_from_month(month: int, year: int) -> SeasonInfo:
    for s, months in SEASON_MONTHS.items():
        if month in months:
            season_year = year + 1 if month == 12 and s == Season.WINTER else year
            if s == Season.WINTER and month in (1, 2):
                season_year = year
            return SeasonInfo(season=s, year=season_year)
    return detect_current_season(date(year, month, 1))