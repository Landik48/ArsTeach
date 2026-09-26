"""Проверка подписи initData мини-приложения MAX.

Алгоритм из документации (https://dev.max.ru/docs/webapps/validation):
  1. initData — строка вида key1=value1&key2=value2&...&hash=...
     (на фронте это window.WebApp.initData)
  2. каждый ключ встречается ровно один раз, hash — обязательно
  3. значения URL-декодируем, пары сортируем по ключу a→z, hash исключаем
  4. launch_params = "key1=value1\\nkey2=value2..."
  5. secret_key = HMAC_SHA256(key="WebAppData", msg=BOT_TOKEN)
  6. hash == hex(HMAC_SHA256(key=secret_key, msg=launch_params))

Главное правило: user_id берём ТОЛЬКО из проверенной initData, никогда
из тела запроса. Это же требование проверяют на модерации MAX.
"""

import hashlib
import hmac
import json
import time
from urllib.parse import quote, unquote

from pydantic import BaseModel


class InitDataError(Exception):
    """initData отсутствует, подделана или устарела."""


class InitDataUser(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    photo_url: str | None = None


class InitDataChat(BaseModel):
    id: int
    type: str  # DIALOG | CHAT | CHANNEL


class InitData(BaseModel):
    user: InitDataUser
    chat: InitDataChat | None = None
    auth_date: int
    query_id: str | None = None
    start_param: str | None = None  # payload из ссылки https://max.ru/<bot>?startapp=<payload>


def _secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()


def _launch_params(pairs: dict[str, str]) -> str:
    return "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs) if k != "hash")


def validate_init_data(init_data: str, bot_token: str, *, max_age: int | None = 3600) -> InitData:
    """Проверить подпись и свежесть initData. Возвращает распарсенные данные."""
    if not init_data:
        raise InitDataError("initData пустая")

    pairs: dict[str, str] = {}
    for chunk in init_data.split("&"):
        key, sep, value = chunk.partition("=")
        if not sep:
            raise InitDataError(f"Некорректная пара: {chunk!r}")
        if key in pairs:
            # Дубли ключей (в т.ч. hash) — признак подделки
            raise InitDataError(f"Ключ {key!r} встречается больше одного раза")
        # unquote, а не unquote_plus: так же, как decodeURIComponent в эталоне MAX
        pairs[key] = unquote(value)

    received_hash = pairs.get("hash")
    if not received_hash:
        raise InitDataError("В initData нет hash")

    expected_hash = hmac.new(
        _secret_key(bot_token), _launch_params(pairs).encode(), hashlib.sha256
    ).hexdigest()
    # compare_digest — сравнение за постоянное время (защита от timing-атак)
    if not hmac.compare_digest(expected_hash, received_hash):
        raise InitDataError("Подпись initData не совпадает")

    try:
        auth_date = int(pairs["auth_date"])
    except (KeyError, ValueError) as exc:
        raise InitDataError("Некорректный auth_date") from exc

    if max_age is not None and time.time() - auth_date > max_age:
        raise InitDataError("initData устарела, переоткройте мини-приложение")

    try:
        return InitData(
            user=json.loads(pairs["user"]),
            chat=json.loads(pairs["chat"]) if pairs.get("chat") else None,
            auth_date=auth_date,
            query_id=pairs.get("query_id"),
            start_param=pairs.get("start_param") or None,
        )
    except (KeyError, ValueError) as exc:
        raise InitDataError("Не удалось разобрать user/chat") from exc


def sign_init_data(fields: dict[str, str | int | dict], bot_token: str) -> str:
    """Собрать подписанную initData — как это делает клиент MAX.

    Нужна только для разработки и тестов: эндпоинт /api/dev/init-data отдаёт
    такую строку фронту, чтобы мини-апп работал в обычном браузере.
    """

    def _encode(value: str | int | dict) -> str:
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        return str(value)

    pairs = {k: _encode(v) for k, v in fields.items()}
    signature = hmac.new(
        _secret_key(bot_token), _launch_params(pairs).encode(), hashlib.sha256
    ).hexdigest()
    encoded = "&".join(f"{k}={quote(v, safe='')}" for k, v in pairs.items())
    return f"{encoded}&hash={signature}"
