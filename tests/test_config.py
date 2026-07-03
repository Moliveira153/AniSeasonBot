"""Configuration tests."""

from app.config import Settings, _normalize_database_url, get_settings


def test_normalize_postgres_url() -> None:
    url = "postgres://user:pass@host/db"
    assert _normalize_database_url(url) == "postgresql+asyncpg://user:pass@host/db"


def test_normalize_postgresql_url() -> None:
    url = "postgresql://user:pass@host/db"
    assert _normalize_database_url(url) == "postgresql+asyncpg://user:pass@host/db"


def test_webhook_url() -> None:
    settings = Settings.model_construct(
        telegram_bot_token="test",
        database_url="postgresql+asyncpg://localhost/db",
        redis_url="redis://localhost",
        bot_mode="webhook",
        render_external_url="https://myapp.onrender.com",
        webhook_secret="secret123",
    )
    assert settings.webhook_url == "https://myapp.onrender.com/webhook/secret123"
    assert settings.webhook_path == "/webhook/secret123"