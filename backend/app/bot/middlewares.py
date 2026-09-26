"""Middleware бота: прокидываем сессию БД в хендлеры.

Работает как в aiogram: всё, что положили в data, придёт в хендлер
по имени аргумента. Хендлер с параметром `session` получит AsyncSession.
"""

from typing import Any

from maxapi.filters.middleware import BaseMiddleware, HandlerCallable
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def __call__(
        self, handler: HandlerCallable, event_object: Any, data: dict[str, Any]
    ) -> Any:
        async with self.session_factory() as session:
            data["session"] = session
            return await handler(event_object, data)
