"""Зависимости FastAPI: сессия БД, бот, авторизация по initData."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from maxapi import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models import User
from app.security.init_data import InitData, InitDataError, validate_init_data
from app.services.users import upsert_user


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


def get_bot(request: Request) -> Bot:
    return request.app.state.bot


def get_init_data(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> InitData:
    """Фронт шлёт заголовок `Authorization: max <window.WebApp.initData>`.

    Именно Authorization, а не свой X-заголовок: такие ответы не кешируют
    промежуточные прокси, и это привычная схема «тип + креды».
    """
    scheme, _, raw = (authorization or "").partition(" ")
    if scheme.lower() != "max" or not raw:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Нужен заголовок Authorization: max <initData>"
        )
    try:
        return validate_init_data(raw, settings.bot_token, max_age=settings.init_data_ttl)
    except InitDataError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc


async def get_current_user(
    init_data: Annotated[InitData, Depends(get_init_data)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    # Для простоты обновляем профиль на каждом запросе. В реальном проекте
    # обычно делают отдельный POST /api/auth, который меняет initData на
    # короткоживущую сессию/JWT, и дальше пишут в базу только при логине.
    u = init_data.user
    return await upsert_user(
        session,
        user_id=u.id,
        first_name=u.first_name,
        last_name=u.last_name,
        username=u.username,
        language_code=u.language_code,
    )


SessionDep = Annotated[AsyncSession, Depends(get_session)]
BotDep = Annotated[Bot, Depends(get_bot)]
InitDataDep = Annotated[InitData, Depends(get_init_data)]
CurrentUser = Annotated[User, Depends(get_current_user)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
