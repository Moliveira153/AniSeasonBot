"""HTML sanitization for API descriptions."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup


def clean_html(text: str | None, max_length: int | None = None) -> str:
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    cleaned = soup.get_text(separator=" ").strip()
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    if max_length and len(cleaned) > max_length:
        return cleaned[: max_length - 3] + "..."
    return cleaned


def split_telegram_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        if len(current) + len(paragraph) + 2 <= limit:
            current = f"{current}\n\n{paragraph}".strip()
        else:
            if current:
                parts.append(current)
            if len(paragraph) <= limit:
                current = paragraph
            else:
                for i in range(0, len(paragraph), limit):
                    parts.append(paragraph[i : i + limit])
                current = ""
    if current:
        parts.append(current)
    return parts


def escape_markdown_v2(text: str) -> str:
    special = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)