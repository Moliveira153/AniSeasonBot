"""Bot and dispatcher factory."""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import BotCommand

from app.bot.handlers import register_handlers
from app.bot.middlewares.db import DatabaseMiddleware
from app.bot.middlewares.errors import ErrorHandlerMiddleware
from app.bot.middlewares.maintenance import MaintenanceMiddleware
from app.bot.middlewares.throttle import ThrottleMiddleware
from app.config import Settings, get_settings


async def set_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Iniciar o bot"),
        BotCommand(command="temporada", description="Animes da temporada"),
        BotCommand(command="buscar", description="Buscar anime"),
        BotCommand(command="anime", description="Detalhes do anime"),
        BotCommand(command="minhalista", description="Minha lista"),
        BotCommand(command="proximos", description="Próximos episódios"),
        BotCommand(command="hoje", description="Episódios de hoje"),
        BotCommand(command="semana", description="Calendário semanal"),
        BotCommand(command="lancamentos", description="Lançamentos recentes"),
        BotCommand(command="configuracoes", description="Configurações"),
        BotCommand(command="pausar", description="Pausar notificações"),
        BotCommand(command="retomar", description="Reativar notificações"),
        BotCommand(command="ajuda", description="Ajuda"),
        BotCommand(command="sobre", description="Sobre o bot"),
        BotCommand(command="privacidade", description="Privacidade"),
        BotCommand(command="excluirme", description="Excluir meus dados"),
        BotCommand(command="cancelar", description="Cancelar operação"),
    ]
    await bot.set_my_commands(commands)


def create_bot(settings: Settings | None = None) -> Bot:
    settings = settings or get_settings()
    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )


def create_dispatcher(storage: BaseStorage) -> Dispatcher:
    dp = Dispatcher(storage=storage)

    # Middlewares no nível do observer (recebem Message/CallbackQuery, não Update)
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())
    dp.inline_query.middleware(ErrorHandlerMiddleware())

    dp.message.middleware(MaintenanceMiddleware())
    dp.callback_query.middleware(MaintenanceMiddleware())

    dp.message.middleware(ThrottleMiddleware())
    dp.callback_query.middleware(ThrottleMiddleware())

    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.inline_query.middleware(DatabaseMiddleware())

    register_handlers(dp)
    return dp