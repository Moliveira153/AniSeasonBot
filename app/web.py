"""FastAPI web server for Render.com — webhook + health checks."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from app.bot.factory import (
    create_bot,
    create_dispatcher,
    create_fsm_storage_redis,
    set_bot_commands,
)
from app.utils.redis_client import create_redis
from app.bot.middlewares.errors import on_dispatcher_error
from app.config import get_settings
from app.database.session import dispose_engine
from app.health import check_health
from app.utils.logging import get_logger, setup_logging
from app.utils.migrate import run_migrations_async
from app.workers.embedded import EmbeddedWorker

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.log_level)

    if settings.run_migrations_on_startup:
        try:
            await run_migrations_async()
        except Exception as exc:
            logger.error("migration_failed", error=str(exc))
            raise

    fsm_redis = create_fsm_storage_redis(settings)
    cache_redis = create_redis(settings)
    bot = create_bot(settings)
    dp = create_dispatcher(fsm_redis, settings)
    dp.errors.register(on_dispatcher_error)

    await set_bot_commands(bot)

    if settings.bot_mode == "webhook":
        webhook_url = settings.webhook_url
        if not webhook_url:
            raise RuntimeError("WEBHOOK mode requires RENDER_EXTERNAL_URL")
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=dp.resolve_used_update_types(),
        )
        logger.info("webhook_registered", url=webhook_url)
    else:
        await bot.delete_webhook(drop_pending_updates=True)

    app.state.bot = bot
    app.state.dp = dp
    app.state.redis = cache_redis
    app.state.fsm_redis = fsm_redis
    app.state.settings = settings

    embedded: EmbeddedWorker | None = None
    if settings.embedded_worker:
        embedded = EmbeddedWorker(bot, settings)
        await embedded.start()
        app.state.embedded_worker = embedded

    logger.info(
        "app_started",
        mode=settings.bot_mode,
        embedded_worker=settings.embedded_worker,
    )
    yield

    if embedded:
        await embedded.stop()

    if settings.bot_mode == "webhook":
        await bot.delete_webhook(drop_pending_updates=False)
    await bot.session.close()
    await fsm_redis.aclose()
    await cache_redis.aclose()
    await dispose_engine()
    logger.info("app_stopped")


app = FastAPI(
    title="Anime Season Bot",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "anime-season-bot", "status": "running"}


@app.get("/health")
async def health() -> JSONResponse:
    result = await check_health()
    status_code = 200 if result["overall"] == "healthy" else 503
    return JSONResponse(content=result, status_code=status_code)


@app.get("/ready")
async def ready(request: Request) -> JSONResponse:
    if not hasattr(request.app.state, "bot"):
        return JSONResponse({"ready": False}, status_code=503)
    return JSONResponse({"ready": True})


@app.post("/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request) -> Response:
    settings = request.app.state.settings
    if secret != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    try:
        payload = await request.json()
        update = Update.model_validate(payload)
        update_kind = "message" if update.message else "callback" if update.callback_query else "other"
        logger.info(
            "webhook_received",
            update_id=update.update_id,
            kind=update_kind,
            user_id=(
                update.callback_query.from_user.id
                if update.callback_query and update.callback_query.from_user
                else update.message.from_user.id
                if update.message and update.message.from_user
                else None
            ),
            data=update.callback_query.data if update.callback_query else None,
        )
        bot = request.app.state.bot
        dp = request.app.state.dp
        await dp.feed_update(bot, update)
        logger.info("webhook_processed", update_id=update.update_id)
    except Exception as exc:
        logger.exception("webhook_processing_error", error=str(exc))
        return Response(status_code=200)

    return Response(status_code=200)