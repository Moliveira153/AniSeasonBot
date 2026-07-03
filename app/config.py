"""Application configuration via environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_database_url(url: str) -> str:
    """Convert Render/Heroku postgres URLs to asyncpg driver."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class Settings(BaseSettings):
    """Centralized application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")
    anilist_api_url: str = Field(
        "https://graphql.anilist.co",
        alias="ANILIST_API_URL",
    )
    jikan_api_url: str = Field(
        "https://api.jikan.moe/v4",
        alias="JIKAN_API_URL",
    )
    default_language: str = Field("pt-BR", alias="DEFAULT_LANGUAGE")
    default_timezone: str = Field("America/Sao_Paulo", alias="DEFAULT_TIMEZONE")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    sentry_dsn: str | None = Field(None, alias="SENTRY_DSN")
    admin_telegram_ids: list[int] = Field(default_factory=list, alias="ADMIN_TELEGRAM_IDS")
    notification_check_interval: int = Field(300, alias="NOTIFICATION_CHECK_INTERVAL")
    cache_ttl: int = Field(3600, alias="CACHE_TTL")
    maintenance_mode: bool = Field(False, alias="MAINTENANCE_MODE")

    # Deployment
    bot_mode: Literal["polling", "webhook"] = Field("polling", alias="BOT_MODE")
    port: int = Field(8000, alias="PORT")
    webhook_secret: str = Field("change-me", alias="WEBHOOK_SECRET")
    render_external_url: str | None = Field(None, alias="RENDER_EXTERNAL_URL")
    run_migrations_on_startup: bool = Field(False, alias="RUN_MIGRATIONS_ON_STARTUP")
    is_render: bool = Field(False, alias="IS_RENDER")
    embedded_worker: bool = Field(False, alias="EMBEDDED_WORKER")

    # Rate limits
    user_command_rate_limit: int = 30
    user_command_rate_window: int = 60

    # Sync intervals (seconds)
    sync_interval_airing_soon: int = 300
    sync_interval_airing: int = 900
    sync_interval_upcoming: int = 3600
    sync_interval_finished: int = 86400

    # DB pool (smaller on Render free tier)
    db_pool_size: int = Field(5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(10, alias="DB_MAX_OVERFLOW")

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_db_url(cls, value: object) -> object:
        if isinstance(value, str):
            return _normalize_database_url(value)
        return value

    @field_validator("admin_telegram_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: object) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(v) for v in value]
        if isinstance(value, int):
            return [value]
        return [int(x.strip()) for x in str(value).split(",") if x.strip()]

    @field_validator("embedded_worker", mode="before")
    @classmethod
    def default_embedded_on_render(cls, value: object) -> bool:
        if value is not None and value != "":
            return str(value).lower() in ("1", "true", "yes")
        return bool(os.getenv("RENDER"))

    @field_validator("is_render", mode="before")
    @classmethod
    def detect_render(cls, value: object) -> bool:
        if value is not None and value != "":
            return str(value).lower() in ("1", "true", "yes")
        return bool(os.getenv("RENDER"))

    @field_validator("run_migrations_on_startup", mode="before")
    @classmethod
    def default_migrations_on_render(cls, value: object, info: object) -> bool:
        if value is not None and value != "":
            return str(value).lower() in ("1", "true", "yes")
        return bool(os.getenv("RENDER"))

    @field_validator("bot_mode", mode="before")
    @classmethod
    def default_webhook_on_render(cls, value: object) -> str:
        if value is not None and str(value).strip():
            return str(value).lower()
        if os.getenv("RENDER"):
            return "webhook"
        return "polling"

    @property
    def is_production(self) -> bool:
        return bool(self.telegram_bot_token and "localhost" not in self.database_url)

    @property
    def public_url(self) -> str | None:
        if self.render_external_url:
            return self.render_external_url.rstrip("/")
        return None

    @property
    def webhook_path(self) -> str:
        return f"/webhook/{self.webhook_secret}"

    @property
    def webhook_url(self) -> str | None:
        base = self.public_url
        if not base:
            return None
        return f"{base}{self.webhook_path}"

    @property
    def redis_use_ssl(self) -> bool:
        return self.redis_url.startswith("rediss://")

    def validate_required(self) -> Self:
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")
        if self.bot_mode == "webhook" and not self.webhook_url:
            raise ValueError(
                "WEBHOOK mode requires RENDER_EXTERNAL_URL or a public base URL"
            )
        if (
            self.bot_mode == "webhook"
            and self.is_render
            and self.webhook_secret in ("change-me", "")
        ):
            raise ValueError("Set a strong WEBHOOK_SECRET in production")
        return self


@lru_cache
def get_settings() -> Settings:
    settings = Settings()  # type: ignore[call-arg]
    return settings.validate_required()