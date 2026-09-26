"""Клавиатуры бота.

В MAX клавиатура — это вложение (attachment) типа inline_keyboard.
Лимиты: до 210 кнопок, до 30 рядов, до 7 кнопок в ряду
(но не больше 3 для link / open_app / request_contact / request_geo_location).
"""

from maxapi import Bot
from maxapi.types import CallbackButton, OpenAppButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from app.config import get_settings


def main_menu(bot: Bot, *, start_param: str | None = None):
    me = bot.me  # заполняется при старте диспетчера (GET /me)
    username = get_settings().max_bot_username or (me.username if me else None)

    builder = InlineKeyboardBuilder()
    builder.row(
        OpenAppButton(
            text="🚀 Открыть приложение",
            # чьё мини-приложение открыть: username бота или его user_id
            web_app=username,
            contact_id=None if username else (me.user_id if me else None),
            # попадёт во фронт как window.WebApp.initDataUnsafe.start_param
            payload=start_param,
        )
    )
    builder.row(CallbackButton(text="🏓 Ping", payload="ping"))
    return builder.as_markup()
