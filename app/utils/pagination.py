"""Pagination helpers."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Generic, Sequence, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    items: Sequence[T]
    page: int
    per_page: int
    total: int

    @property
    def total_pages(self) -> int:
        return max(1, ceil(self.total / self.per_page))

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


def paginate(items: Sequence[T], page: int = 1, per_page: int = 5) -> Page[T]:
    page = max(1, page)
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    return Page(items=items[start:end], page=page, per_page=per_page, total=total)