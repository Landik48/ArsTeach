"""Схемы ответов API (то, что видит фронт)."""

from pydantic import BaseModel


class MeOut(BaseModel):
    id: int
    first_name: str
    last_name: str | None
    username: str | None
    hello_count: int
    # Контекст запуска мини-аппа — полезно показать на экране для отладки
    start_param: str | None
    chat_type: str | None


class HelloOut(BaseModel):
    hello_count: int
    # Удалось ли боту отправить сообщение в чат (в dev без токена — False)
    notified: bool


class DevInitDataOut(BaseModel):
    init_data: str
