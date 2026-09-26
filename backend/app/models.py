"""ORM-модели.

Новую таблицу добавляем здесь, затем генерируем миграцию:
    docker compose --profile dev run --rm api-dev alembic revision --autogenerate -m "описание"
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, MetaData, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Единые имена для индексов и ограничений — чтобы autogenerate в Alembic
# давал стабильные, предсказуемые миграции
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class User(Base):
    """Пользователь MAX. Первичный ключ — его user_id в MAX."""

    __tablename__ = "users"

    # user_id в MAX — 64-битное число, поэтому BigInteger
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    first_name: Mapped[str] = mapped_column(String(256))
    last_name: Mapped[str | None] = mapped_column(String(256))
    username: Mapped[str | None] = mapped_column(String(256))
    language_code: Mapped[str | None] = mapped_column(String(16))

    # Счётчик для hello world: сколько раз нажали кнопку в мини-аппе
    hello_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
