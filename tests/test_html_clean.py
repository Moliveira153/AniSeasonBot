"""HTML cleaning tests."""

from app.utils.html_clean import clean_html, split_telegram_message


def test_clean_html_removes_tags() -> None:
    text = "<p>Hello <b>world</b></p>"
    assert clean_html(text) == "Hello world"


def test_clean_html_truncates() -> None:
    text = "A" * 100
    assert len(clean_html(text, max_length=50)) == 50


def test_split_long_message() -> None:
    text = "A" * 5000
    parts = split_telegram_message(text, limit=4000)
    assert len(parts) == 2
    assert all(len(p) <= 4000 for p in parts)