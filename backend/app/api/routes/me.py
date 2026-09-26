"""Ручки мини-приложения. Все требуют валидную initData."""

import logging

from fastapi import APIRouter

from app.api.deps import BotDep, CurrentUser, InitDataDep, SessionDep, SettingsDep
from app.api.schemas import HelloOut, MeOut
from app.services.users import increment_hello

log = logging.getLogger(__name__)

router = APIRouter(tags=["mini-app"])


@router.get("/me")
async def get_me(user: CurrentUser, init_data: InitDataDep) -> MeOut:
    return MeOut(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        hello_count=user.hello_count,
        start_param=init_data.start_param,
        chat_type=init_data.chat.type if init_data.chat else None,
    )


@router.post("/hello")
async def say_hello(
    user: CurrentUser, session: SessionDep, bot: BotDep, settings: SettingsDep
) -> HelloOut:
    """Полный круг hello world: мини-апп → API → БД → бот пишет в чат."""
    count = await increment_hello(session, user.id)

    notified = False
    if settings.has_real_token:
        try:
            # user_id — личный диалог с пользователем. Он открыл мини-апп
            # из чата с ботом, значит диалог уже существует.
            await bot.send_message(
                user_id=user.id,
                text=f"👋 Привет из мини-приложения! Счётчик нажатий: {count}",
            )
            notified = True
        except Exception:
            # Ошибка бота не должна ронять запрос мини-аппа
            log.exception("Не удалось отправить сообщение пользователю %s", user.id)

    return HelloOut(hello_count=count, notified=notified)
