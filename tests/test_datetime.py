"""Datetime formatting tests."""

from datetime import datetime, timezone

from app.utils.datetime_fmt import format_datetime, to_user_timezone


def test_to_user_timezone() -> None:
    dt = datetime(2026, 1, 15, 17, 0, tzinfo=timezone.utc)
    local = to_user_timezone(dt, "America/Sao_Paulo")
    assert local is not None
    assert local.hour == 14  # UTC-3 in January


def test_format_datetime_pt() -> None:
    dt = datetime(2026, 6, 15, 12, 30, tzinfo=timezone.utc)
    result = format_datetime(dt, "America/Sao_Paulo", "pt-BR")
    assert "15" in result
    assert "às" in result