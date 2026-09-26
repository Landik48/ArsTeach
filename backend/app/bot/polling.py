"""Запуск бота в режиме long polling (только для разработки).

    python -m app.bot.polling

В dev-профиле compose запускает это через watchfiles, поэтому бот
перезапускается при каждом сохранении файла, как uvicorn --reload.

Long polling и вебхук взаимоисключающие: пока у бота есть подписка на вебхук,
polling ничего не получит. Поэтому для разработки заведите отдельного
тестового бота, а не отключайте вебхук у боевого.
"""

import asyncio
import logging

from app.bot import create_bot, create_dispatcher, setup_bot_commands
from app.config import get_settings
from app.db import create_engine, create_session_factory

log = logging.getLogger("app.bot.polling")


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    if not settings.has_real_token:
        log.warning(
            "MAX_BOT_TOKEN не задан — бот не запущен. API и мини-апп в браузере "
            "работают и без него. Впишите токен в .env и пересоздайте контейнер: "
            "docker compose --profile dev up -d bot-dev"
        )
        return

    engine = create_engine(settings.database_url)
    dp = create_dispatcher(create_session_factory(engine), use_create_task=False)
    bot = create_bot(settings)

    await setup_bot_commands(bot)
    try:
        # skip_updates=True — не разгребать то, что накопилось, пока бот лежал
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.close_session()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
