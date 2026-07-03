"""Register all bot handlers."""

from aiogram import Dispatcher

from app.bot.handlers import admin, anime, callbacks, list_cmd, schedule, search, settings, start


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(settings.router)
    dp.include_router(list_cmd.router)
    dp.include_router(search.router)
    dp.include_router(anime.router)
    dp.include_router(schedule.router)
    dp.include_router(callbacks.router)
    dp.include_router(admin.router)