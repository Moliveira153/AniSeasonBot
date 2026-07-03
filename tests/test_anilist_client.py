"""AniList client tests."""

from app.clients.anilist import AniListClient
from app.schemas.anilist import AniListMedia, AniListTitle


def test_media_to_dict() -> None:
    media = AniListMedia(
        id=12345,
        idMal=67890,
        title=AniListTitle(romaji="Test Anime", english="Test Anime EN"),
        status="RELEASING",
        format="TV",
        genres=["Action"],
        averageScore=85,
    )
    data = AniListClient.media_to_dict(media)
    assert data["anilist_id"] == 12345
    assert data["mal_id"] == 67890
    assert data["title_romaji"] == "Test Anime"
    assert data["average_score"] == 85


def test_trailer_youtube_url() -> None:
    from app.schemas.anilist import AniListTrailer

    media = AniListMedia(
        id=1,
        trailer=AniListTrailer(id="abc123", site="youtube"),
    )
    data = AniListClient.media_to_dict(media)
    assert data["trailer_url"] == "https://www.youtube.com/watch?v=abc123"