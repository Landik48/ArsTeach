"""Старт бота и кнопки главного меню."""

from maxapi import F, Router
from maxapi.types import BotStarted, Command, MessageCallback, MessageCreated, User
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import main_menu
from app.services.users import upsert_user

router = Router(router_id="start")

WELCOME = (
    "Привет, {name}! 👋\n\n"
    "Это hello world мини-приложения в MAX. Нажми «Открыть приложение» — "
    "внутри будет кнопка, которая через API пришлёт тебе сообщение сюда."
)


async def _save_user(session: AsyncSession, user: User) -> None:
    await upsert_user(
        session,
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
    )


@router.bot_started()
async def on_bot_started(event: BotStarted, session: AsyncSession) -> None:
    """Пользователь нажал «Начать» в новом диалоге с ботом (аналог /start в Telegram).

    Если бота открыли по ссылке https://max.ru/<bot>?start=<payload>,
    payload придёт в event.payload.
    """
    await _save_user(session, event.user)
    await event.bot.send_message(
        chat_id=event.chat_id,
        text=WELCOME.format(name=event.user.first_name),
        attachments=[main_menu(event.bot, start_param=event.payload)],
    )


@router.message_created(Command("start"))
async def cmd_start(event: MessageCreated, session: AsyncSession) -> None:
    """Команду /start можно набрать руками в уже существующем диалоге."""
    sender = event.message.sender
    if sender:
        await _save_user(session, sender)
    await event.message.answer(
        text=WELCOME.format(name=sender.first_name if sender else "друг"),
        attachments=[main_menu(event.bot)],
    )


@router.message_created(Command("help"))
async def cmd_help(event: MessageCreated) -> None:
    await event.message.answer(
        "Я умею:\n"
        "• /start — показать кнопку мини-приложения\n"
        "• 🏓 Ping — ответить на callback-кнопку\n"
        "• повторять любой текст"
    )


@router.message_callback(F.callback.payload == "ping")
async def on_ping(event: MessageCallback) -> None:
    # Ответ на callback (POST /answers). ack() — только всплывающее уведомление,
    # исходное сообщение не меняется. Чтобы заменить текст/клавиатуру сообщения,
    # есть event.answer(notification=..., new_text=..., attachments=[...])
    await event.ack(notification="pong 🏓")
