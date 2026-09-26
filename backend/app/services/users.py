"""Бизнес-логика пользователей.

Сервисный слой не знает, откуда пришёл вызов — из хендлера бота или из
HTTP-ручки. Поэтому бот и API используют одни и те же функции.
"""

from sqlalchemy import func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def upsert_user(
    session: AsyncSession,
    *,
    user_id: int,
    first_name: str,
    last_name: str | None = None,
    username: str | None = None,
    language_code: str | None = None,
) -> User:
    """Создать пользователя или обновить его профиль (INSERT ... ON CONFLICT)."""
    values = {
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "language_code": language_code,
    }
    stmt = (
        insert(User)
        .values(id=user_id, **values)
        # onupdate из модели сюда не применяется, поэтому last_seen_at ставим явно
        .on_conflict_do_update(
            index_elements=[User.id], set_={**values, "last_seen_at": func.now()}
        )
        .returning(User)
    )
    # populate_existing — если объект уже есть в сессии, перечитываем его из результата
    user = (await session.execute(stmt, execution_options={"populate_existing": True})).scalar_one()
    await session.commit()
    return user


async def increment_hello(session: AsyncSession, user_id: int) -> int:
    """Атомарно увеличить счётчик (UPDATE ... SET x = x + 1) и вернуть новое значение."""
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(hello_count=User.hello_count + 1)
        .returning(User.hello_count)
    )
    count = (await session.execute(stmt)).scalar_one()
    await session.commit()
    return count
