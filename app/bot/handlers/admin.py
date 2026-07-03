"""Admin handlers."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.filters.admin import IsAdmin
from app.database.repositories.anime_repo import AnimeRepository
from app.database.repositories.notification_repo import NotificationRepository
from app.services.anime_service import AnimeService
from app.services.notification_service import NotificationService
from app.services.user_service import UserService

router = Router(name="admin")


@router.message(Command("stats"), IsAdmin())
async def cmd_stats(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    anime_repo = AnimeRepository(session)
    notif_repo = NotificationRepository(session)
    stats = await user_service.get_stats()
    animes = await anime_repo.count_all()
    sent_today = await notif_repo.count_sent_today()

    text = (
        "📊 *Estatísticas do Bot*\n\n"
        f"Usuários ativos: {stats['users']}\n"
        f"Acompanhamentos: {stats['trackings']}\n"
        f"Animes no DB: {animes}\n"
        f"Notificações hoje: {sent_today}"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("sync"), IsAdmin())
async def cmd_force_sync(message: Message, session: AsyncSession) -> None:
    args = message.text.split(maxsplit=1) if message.text else []  # type: ignore[union-attr]
    if len(args) < 2:
        await message.answer("Usage: /sync <anilist_id>")
        return
    anilist_id = int(args[1])
    notif_service = NotificationService(session)
    count = await notif_service.process_anime_sync(anilist_id)
    await message.answer(f"✅ Sincronizado. {count} notificações enfileiradas.")


@router.message(Command("retry_notifications"), IsAdmin())
async def cmd_retry(message: Message, session: AsyncSession) -> None:
    notif_repo = NotificationRepository(session)
    failed = await notif_repo.get_failed_deliveries()
    await message.answer(f"Falhas pendentes: {len(failed)}")


@router.message(Command("maintenance"), IsAdmin())
async def cmd_maintenance(message: Message) -> None:
    await message.answer(
        "Para ativar manutenção, defina MAINTENANCE_MODE=true no .env e reinicie."
    )