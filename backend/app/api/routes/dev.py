"""Ручки только для разработки. В prod этот роутер не подключается вовсе.

Проблема: вне MAX у мини-аппа нет initData, а без неё API отвечает 401.
Решение: бэкенд сам подписывает initData тем же алгоритмом, что и клиент MAX.
Фронт в dev-режиме берёт её отсюда, и весь путь авторизации работает
по-настоящему даже в обычном браузере на localhost.
"""

import time
import uuid

from fastapi import APIRouter

from app.api.deps import SettingsDep
from app.api.schemas import DevInitDataOut
from app.security.init_data import sign_init_data

router = APIRouter(prefix="/dev", tags=["dev"])


@router.get("/init-data")
def dev_init_data(
    settings: SettingsDep,
    user_id: int = 100500,
    first_name: str = "Dev",
    start_param: str | None = None,
) -> DevInitDataOut:
    fields: dict = {
        "auth_date": int(time.time()),
        "query_id": str(uuid.uuid4()),
        "user": {
            "id": user_id,
            "first_name": first_name,
            "last_name": "User",
            "username": None,
            "language_code": "ru",
            "photo_url": None,
        },
        "chat": {"id": user_id, "type": "DIALOG"},
    }
    if start_param:
        fields["start_param"] = start_param
    return DevInitDataOut(init_data=sign_init_data(fields, settings.bot_token))
