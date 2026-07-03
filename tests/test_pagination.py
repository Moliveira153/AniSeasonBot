"""Pagination tests."""

from app.utils.pagination import paginate


def test_paginate_first_page() -> None:
    items = list(range(12))
    page = paginate(items, page=1, per_page=5)
    assert len(page.items) == 5
    assert page.page == 1
    assert page.total_pages == 3
    assert page.has_next
    assert not page.has_prev


def test_paginate_last_page() -> None:
    items = list(range(12))
    page = paginate(items, page=3, per_page=5)
    assert len(page.items) == 2
    assert not page.has_next
    assert page.has_prev