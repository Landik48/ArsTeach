"""Сборка бота: клиент API, диспетчер, команды, подписка на вебхук.

Бот используется в двух местах:
  * процесс API (app.main) — в режиме webhook принимает апдейты на /max/webhook,
    а в любом режиме умеет отправлять сообщения (например, из ручки /api/hello);
  * отдельный процесс app.bot.polling — long polling для разработки.
"""

import logging

from maxapi import Bot, Dispatcher
from maxapi.types import BotCommand
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot.handlers import routers
from app.bot.middlewares import DbSessionMiddleware
from app.config import Settings

log = logging.getLogger(__name__)

# Команды, которые MAX покажет в меню бота
BOT_COMMANDS = [
    BotCommand(name="start", description="Открыть приложение"),
    BotCommand(name="help", description="Что умеет бот"),
]


def create_bot(settings: Settings) -> Bot:
    # Базовый адрес https://platform-api2.max.ru зашит в библиотеку,
    # токен уходит в заголовке Authorization без префикса Bearer.
    #
    # auto_requests=False: по умолчанию maxapi на КАЖДЫЙ апдейт делает лишний
    # GET /chats/{id}, чтобы заполнить event.chat, причём ещё до ответа вебхуку.
    # Это +1 запрос к лимитам API, а если MAX в этот момент ответит ошибкой,
    # вебхук вернёт 500 и MAX начнёт ретраи. Всё нужное (user, chat_id, текст)
    # уже есть в самом апдейте; если чат действительно нужен — await event.chat.fetch()
    bot = Bot(token=settings.bot_token, auto_requests=False)
    if settings.max_api_url:
        bot.set_api_url(settings.max_api_url.rstrip("/"))
    return bot


def create_dispatcher(
    session_factory: async_sessionmaker[AsyncSession], *, use_create_task: bool
) -> Dispatcher:
    # use_create_task=True: апдейт обрабатывается в фоновой задаче, а вебхук сразу
    # отвечает 200. MAX ждёт ответа не дольше 30 секунд, иначе считает доставку
    # проваленной и повторяет её (до 10 раз, а через 8 часов ошибок отписывает бота).
    dp = Dispatcher(use_create_task=use_create_task)

    # Inner-middleware запускается только если нашёлся подходящий хендлер,
    # поэтому сессию БД открываем не на каждый апдейт, а только когда она нужна
    dp.register_inner_middleware(DbSessionMiddleware(session_factory))

    dp.include_routers(*routers)
    return dp


async def setup_bot_commands(bot: Bot) -> None:
    try:
        await bot.set_commands(*BOT_COMMANDS)
    except Exception:  # не критично для старта
        log.exception("Не удалось установить команды бота")


async def ensure_webhook(bot: Bot, url: str, secret: str) -> None:
    """Подписать бота на вебхук. Повторный POST /subscriptions обновляет подписку.

    Требования MAX к вебхуку: только HTTPS, только порт 443, сертификат от
    доверенного УЦ (Let's Encrypt, который выдаёт Caddy, подходит),
    ответ 200 в течение 30 секунд.
    """
    current = await bot.get_subscriptions()
    for sub in current.subscriptions or []:
        if sub.url != url:
            log.warning("Удаляю чужую подписку на вебхук: %s", sub.url)
            await bot.unsubscribe_webhook(sub.url)

    # update_types=None — получать все типы событий
    await bot.subscribe_webhook(url=url, secret=secret, update_types=None)
    log.info("Вебхук подписан: %s", url)
