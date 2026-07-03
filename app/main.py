"""Bot application entry point (polling mode for local dev)."""

from __future__ import annotations

import asyncio
import sys

from app.bot.factory import create_bot, create_dispatcher, set_bot_commands
from app.bot.middlewares.errors import on_dispatcher_error
from app.bot.storage import create_storage
from app.config import get_settings
from app.database.session import dispose_engine
from app.utils.logging import setup_logging


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    if settings.bot_mode == "webhook":
        print("BOT_MODE=webhook: use 'sh scripts/start_web.sh'")
        sys.exit(1)

    storage = await create_storage(settings)
    bot = create_bot(settings)
    dp = create_dispatcher(storage)
    dp.errors.register(on_dispatcher_error)

    await set_bot_commands(bot)

    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "inline_query"])
    finally:
        await bot.session.close()
        await dispose_engine()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)