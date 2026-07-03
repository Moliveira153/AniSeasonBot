"""Notification and event repository."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.event import AnimeEvent, NotificationDelivery


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def event_exists(self, idempotency_key: str) -> bool:
        result = await self.session.execute(
            select(AnimeEvent.id).where(AnimeEvent.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none() is not None

    async def create_event(
        self,
        anime_id: int,
        event_type: str,
        idempotency_key: str,
        episode: int | None = None,
        old_data: dict[str, Any] | None = None,
        new_data: dict[str, Any] | None = None,
    ) -> AnimeEvent | None:
        if await self.event_exists(idempotency_key):
            return None
        event = AnimeEvent(
            anime_id=anime_id,
            event_type=event_type,
            episode=episode,
            old_data=old_data,
            new_data=new_data,
            idempotency_key=idempotency_key,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def delivery_exists(self, idempotency_key: str) -> bool:
        result = await self.session.execute(
            select(NotificationDelivery.id).where(
                NotificationDelivery.idempotency_key == idempotency_key
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_delivery(
        self,
        user_id: int,
        anime_id: int,
        event_type: str,
        idempotency_key: str,
        event_id: int | None = None,
        episode: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> NotificationDelivery | None:
        if await self.delivery_exists(idempotency_key):
            return None
        delivery = NotificationDelivery(
            user_id=user_id,
            anime_id=anime_id,
            event_id=event_id,
            event_type=event_type,
            episode=episode,
            idempotency_key=idempotency_key,
            payload=payload,
            status="pending",
        )
        self.session.add(delivery)
        await self.session.flush()
        return delivery

    async def mark_sent(self, delivery_id: int) -> None:
        await self.session.execute(
            update(NotificationDelivery)
            .where(NotificationDelivery.id == delivery_id)
            .values(
                status="sent",
                sent_at=datetime.now(timezone.utc),
                attempts=NotificationDelivery.attempts + 1,
            )
        )

    async def mark_failed(self, delivery_id: int, error: str) -> None:
        await self.session.execute(
            update(NotificationDelivery)
            .where(NotificationDelivery.id == delivery_id)
            .values(
                status="failed",
                last_error=error[:2000],
                attempts=NotificationDelivery.attempts + 1,
            )
        )

    async def get_pending_deliveries(self, limit: int = 100) -> list[NotificationDelivery]:
        result = await self.session.execute(
            select(NotificationDelivery)
            .where(NotificationDelivery.status == "pending")
            .order_by(NotificationDelivery.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_failed_deliveries(self, limit: int = 50) -> list[NotificationDelivery]:
        result = await self.session.execute(
            select(NotificationDelivery)
            .where(NotificationDelivery.status == "failed", NotificationDelivery.attempts < 5)
            .order_by(NotificationDelivery.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_sent_today(self) -> int:
        from sqlalchemy import func

        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count())
            .select_from(NotificationDelivery)
            .where(NotificationDelivery.status == "sent", NotificationDelivery.sent_at >= today)
        )
        return result.scalar_one()