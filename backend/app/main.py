"""Точка входа HTTP-сервиса: uvicorn app.main:app

Один процесс обслуживает:
  * /api/*        — REST для мини-приложения (авторизация по initData);
  * /max/webhook  — приём апдейтов бота (только при BOT_MODE=webhook);
  * /api/docs     — Swagger (только в dev).
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from maxapi.webhook.fastapi import FastAPIMaxWebhook

from app.api import build_api_router
from app.bot import create_bot, create_dispatcher, ensure_webhook, setup_bot_commands
from app.config import get_settings
from app.db import create_engine, create_session_factory

log = logging.getLogger("app")


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    # Всё создаётся синхронно и без сетевых запросов: движок БД подключается
    # лениво, HTTP-сессия бота — при первом вызове API
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    bot = create_bot(settings)

    webhook_mode = settings.bot_mode == "webhook"
    dp = create_dispatcher(session_factory, use_create_task=True) if webhook_mode else None

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if dp is not None:
            # GET /me, подготовка хендлеров; затем подписка на вебхук
            await dp.startup(bot)
            await setup_bot_commands(bot)
            await ensure_webhook(bot, settings.webhook_url, settings.max_webhook_secret)
        log.info("Старт: env=%s bot_mode=%s", settings.app_env, settings.bot_mode)
        yield
        await bot.close_session()
        await engine.dispose()

    app = FastAPI(
        title="MAX mini app API",
        lifespan=lifespan,
        # Swagger только в dev. Путь под /api, чтобы Caddy проксировал его без доп. правил
        docs_url="/api/docs" if settings.is_dev else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.is_dev else None,
    )
    app.state.session_factory = session_factory
    app.state.bot = bot

    app.include_router(build_api_router(include_dev=settings.is_dev), prefix="/api")

    if dp is not None:
        # Готовая интеграция maxapi: POST-роут, проверка X-Max-Bot-Api-Secret
        # (403 при несовпадении) и передача апдейта в диспетчер
        FastAPIMaxWebhook(dp=dp, bot=bot, secret=settings.max_webhook_secret).setup(
            app, path="/max/webhook"
        )

    return app


app = create_app()
