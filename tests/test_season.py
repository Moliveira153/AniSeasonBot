"""Season detection tests."""

from datetime import date

from app.utils.season import Season, detect_current_season, season_from_month


def test_winter_december() -> None:
    info = detect_current_season(date(2026, 12, 15))
    assert info.season == Season.WINTER
    assert info.year == 2027


def test_winter_january() -> None:
    info = detect_current_season(date(2026, 1, 10))
    assert info.season == Season.WINTER
    assert info.year == 2026


def test_spring() -> None:
    info = detect_current_season(date(2026, 4, 1))
    assert info.season == Season.SPRING
    assert info.year == 2026


def test_summer() -> None:
    info = detect_current_season(date(2026, 7, 15))
    assert info.season == Season.SUMMER


def test_fall() -> None:
    info = detect_current_season(date(2026, 10, 1))
    assert info.season == Season.FALL


def test_season_from_month() -> None:
    info = season_from_month(3, 2026)
    assert info.season == Season.SPRING