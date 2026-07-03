"""Onboarding helper tests."""

from app.bot.handlers.start import LANG_BY_CALLBACK, _parse_lang


def test_parse_lang_pt() -> None:
    assert _parse_lang("lang:pt") == LANG_BY_CALLBACK["pt"]


def test_parse_lang_pt_br_legacy() -> None:
    assert _parse_lang("lang:pt-BR") == "pt-BR"


def test_parse_lang_en() -> None:
    assert _parse_lang("lang:en") == "en"


def test_parse_lang_invalid() -> None:
    assert _parse_lang("lang:fr") is None
    assert _parse_lang(None) is None
    assert _parse_lang("tz:America/Sao_Paulo") is None