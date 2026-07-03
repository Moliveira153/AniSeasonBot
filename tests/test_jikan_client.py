"""Jikan client tests."""

from app.clients.jikan import JikanClient
from app.schemas.jikan import JikanAnime


def test_supplement_anime_dict() -> None:
    base = {"anilist_id": 1, "title_romaji": "Test"}
    jikan = JikanAnime(
        mal_id=100,
        synopsis="A great anime",
        episodes=24,
        images={"jpg": {"large_image_url": "http://example.com/img.jpg"}},
    )
    result = JikanClient.supplement_anime_dict(base, jikan)
    assert result["mal_id"] == 100
    assert result["description"] == "A great anime"
    assert result["episodes"] == 24
    assert result["_jikan_supplemented"] is True


def test_supplement_does_not_overwrite() -> None:
    base = {"anilist_id": 1, "description": "From AniList", "episodes": 12}
    jikan = JikanAnime(mal_id=100, synopsis="From Jikan", episodes=24)
    result = JikanClient.supplement_anime_dict(base, jikan)
    assert result["description"] == "From AniList"
    assert result["episodes"] == 12