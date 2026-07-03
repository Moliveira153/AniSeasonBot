"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-03

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="pt-BR"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="America/Sao_Paulo"),
        sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("last_activity", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("bot_blocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_admin_blocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "animes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("anilist_id", sa.Integer(), nullable=False),
        sa.Column("mal_id", sa.Integer(), nullable=True),
        sa.Column("title_romaji", sa.String(length=512), nullable=True),
        sa.Column("title_english", sa.String(length=512), nullable=True),
        sa.Column("title_native", sa.String(length=512), nullable=True),
        sa.Column("synonyms", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("format", sa.String(length=32), nullable=True),
        sa.Column("season", sa.String(length=16), nullable=True),
        sa.Column("season_year", sa.Integer(), nullable=True),
        sa.Column("episodes", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_episode", sa.Integer(), nullable=True),
        sa.Column("next_airing_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("genres", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("studios", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("producers", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("cover_image", sa.String(length=1024), nullable=True),
        sa.Column("banner_image", sa.String(length=1024), nullable=True),
        sa.Column("trailer_url", sa.String(length=1024), nullable=True),
        sa.Column("trailer_site", sa.String(length=32), nullable=True),
        sa.Column("site_url", sa.String(length=1024), nullable=True),
        sa.Column("is_adult", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("average_score", sa.Integer(), nullable=True),
        sa.Column("popularity", sa.Integer(), nullable=True),
        sa.Column("favourites", sa.Integer(), nullable=True),
        sa.Column("trending", sa.Integer(), nullable=True),
        sa.Column("airing_day", sa.Integer(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("sync_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("anilist_id", name="uq_animes_anilist_id"),
    )
    op.create_index("ix_animes_mal_id", "animes", ["mal_id"])
    op.create_index("ix_animes_status", "animes", ["status"])
    op.create_index("ix_animes_next_airing_at", "animes", ["next_airing_at"])
    op.create_index("ix_animes_next_sync_at", "animes", ["next_sync_at"])

    op.create_table(
        "trackings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("anime_id", sa.Integer(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_watched_episode", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("personal_status", sa.String(length=32), nullable=False, server_default="watching"),
        sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["anime_id"], ["animes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "anime_id", name="uq_trackings_user_anime"),
    )
    op.create_index("ix_trackings_user_id", "trackings", ["user_id"])
    op.create_index("ix_trackings_anime_id", "trackings", ["anime_id"])

    op.create_table(
        "anime_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("anime_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("episode", sa.Integer(), nullable=True),
        sa.Column("old_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("idempotency_key", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["anime_id"], ["animes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_anime_events_anime_id", "anime_events", ["anime_id"])
    op.create_index("ix_anime_events_event_type", "anime_events", ["event_type"])

    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("anime_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("episode", sa.Integer(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["anime_id"], ["animes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["anime_events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_notification_idempotency"),
    )
    op.create_index("ix_notification_deliveries_user_id", "notification_deliveries", ["user_id"])
    op.create_index("ix_notification_deliveries_status", "notification_deliveries", ["status"])

    op.create_table(
        "sync_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("resource", sa.String(length=512), nullable=False),
        sa.Column("etag", sa.String(length=128), nullable=True),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_state", sa.String(length=32), nullable=False, server_default="ok"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "resource", name="uq_sync_cache_source_resource"),
    )
    op.create_index("ix_sync_cache_next_sync_at", "sync_cache", ["next_sync_at"])


def downgrade() -> None:
    op.drop_table("sync_cache")
    op.drop_table("notification_deliveries")
    op.drop_table("anime_events")
    op.drop_table("trackings")
    op.drop_table("animes")
    op.drop_table("users")