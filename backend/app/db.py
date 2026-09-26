"""Подключение к PostgreSQL (SQLAlchemy 2.0, async)."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    # pool_pre_ping — переживаем перезапуск контейнера с базой без ошибок в логах
    return create_async_engine(database_url, echo=echo, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False — объекты остаются читаемыми после commit(),
    # иначе обращение к полю после коммита в async-коде даст ошибку
    return async_sessionmaker(engine, expire_on_commit=False)
