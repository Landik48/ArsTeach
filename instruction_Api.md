# MAX Bot API: как он устроен и как писать бота без лишнего кода

Коротко о главном: **OpenAPI-схема — это справочник, а не способ писать бота.** Если сгенерировать из неё клиент, получится гора моделей и ручная диспетчеризация. Отсюда ощущение «много лишнего кода». Бота мы пишем на **maxapi**: это почти aiogram, и хендлер в нём такой же короткий.

```
 ┌──────────────────────────────┐
 │ твой код: handlers/*.py      │  ← здесь проводишь 95% времени
 ├──────────────────────────────┤
 │ maxapi (Router, F, FSM, ...) │  ← «aiogram для MAX»
 ├──────────────────────────────┤
 │ Bot API MAX (REST + JSON)    │  ← то, что описывает OpenAPI-схема
 └──────────────────────────────┘
```

Содержание:
1. [Сырое API за 5 минут](#1-сырое-api-за-5-минут)
2. [Почему не клиент из OpenAPI](#2-почему-не-клиент-из-openapi)
3. [Шпаргалка aiogram → maxapi](#3-шпаргалка-aiogram--maxapi)
4. [Рецепты](#4-рецепты)
5. [Что в шаблоне пишется один раз](#5-что-в-шаблоне-пишется-один-раз)
6. [Грабли](#6-грабли)

---

## 1. Сырое API за 5 минут

Это понимать полезно, даже если руками в API ты не ходишь: так проще читать логи, ошибки и документацию.

### Запросы

- **База:** `https://platform-api2.max.ru`.
- **Авторизация:** заголовок `Authorization: <токен>`, **без** `Bearer`. Токен в URL, как `/bot<token>/` в Telegram, больше не поддерживается.
- **Стиль:** REST, тело — JSON. Получатель передаётся **в query**, а не в теле: `POST /messages?chat_id=123`.

```bash
curl https://platform-api2.max.ru/me -H "Authorization: $TOKEN"
```

### Методы, которые нужны в 90% случаев

| Метод | Что делает | Аналог в Telegram |
|---|---|---|
| `GET /me` | инфо о боте | `getMe` |
| `POST /messages?user_id=…` или `?chat_id=…` | отправить сообщение | `sendMessage` |
| `PUT /messages?message_id=…` | изменить сообщение | `editMessageText` + `editMessageReplyMarkup` |
| `DELETE /messages?message_id=…` | удалить сообщение | `deleteMessage` |
| `POST /answers?callback_id=…` | ответить на нажатие кнопки (+ сразу поменять сообщение) | `answerCallbackQuery` |
| `POST /uploads?type=image\|video\|audio\|file` | получить URL для загрузки файла | — (в TG файл шлётся сразу) |
| `POST /subscriptions` / `DELETE` / `GET` | вебхук: подписаться, отписаться, посмотреть | `setWebhook` / `deleteWebhook` |
| `GET /updates?marker=…` | long polling | `getUpdates` (`offset` → `marker`) |
| `PATCH /me/commands` | команды в меню бота | `setMyCommands` |
| `/chats/{chatId}/…` | групповые чаты: участники, админы, закреп | `getChat`, `pinChatMessage`, … |

### Тело сообщения (`NewMessageBody`)

```json
{
  "text": "Привет, **мир**",
  "format": "markdown",
  "attachments": [],
  "notify": true,
  "link": null
}
```

- **`text`** — до 4000 символов.
- **`format`** — `markdown` или `html`.
- **`attachments`** — список вложений: `image`, `video`, `audio`, `file`, `sticker`, `contact`, `location`, `share` и **`inline_keyboard`**.
- **`link`** — ответ или пересылка другого сообщения.

При редактировании (`PUT /messages`) поле `attachments` работает так:
- `null` — вложения не трогать;
- `[]` — удалить все, включая клавиатуру.

В maxapi есть нюанс, см. [грабли](#6-грабли).

### Клавиатура — это вложение

В Telegram клавиатура передаётся в `reply_markup`, а в MAX — обычным элементом `attachments`:

```json
{
  "text": "Выбери",
  "attachments": [{
    "type": "inline_keyboard",
    "payload": {
      "buttons": [
        [{ "type": "callback", "text": "Ping", "payload": "ping" }],
        [{ "type": "open_app", "text": "Открыть приложение", "web_app": "my_bot" }]
      ]
    }
  }]
}
```

Типы кнопок:

| Тип | Что делает |
|---|---|
| `callback` | присылает боту апдейт `message_callback`; `payload` до 1024 символов |
| `link` | открывает ссылку |
| `open_app` | открывает мини-апп; `web_app` = username бота, `payload` до 512 символов |
| `request_contact` | просит у пользователя контакт |
| `request_geo_location` | просит геолокацию |
| `message` | отправляет боту текст от имени пользователя — замена reply-клавиатуре, которой в MAX нет |
| `clipboard` | копирует текст в буфер обмена |

Лимиты:
- текст кнопки — до 128 символов;
- всего до 210 кнопок, до 30 рядов;
- в ряду до 7 кнопок, но не больше 3, если это `link`, `open_app`, `request_contact` или `request_geo_location`.

### Апдейты

Каждый апдейт — это JSON с полями `update_type` и `timestamp`. Остальные поля зависят от типа. Всего в схеме 19 типов:

- **сообщения:** `message_created`, `message_edited`, `message_removed`, `message_callback`;
- **бот и диалог:** `bot_started`, `bot_stopped`, `bot_added`, `bot_removed`, `dialog_cleared`, `dialog_removed`, `dialog_muted`, `dialog_unmuted`;
- **чаты:** `user_added`, `user_removed`, `chat_title_changed`, `bot_admin_permissions_changed`;
- **комментарии:** `comment_created`, `comment_edited`, `comment_removed`.

Три апдейта, которые встречаются постоянно:

```jsonc
// Пользователь нажал «Начать» (первый вход или ссылка https://max.ru/<bot>?start=<payload>)
{ "update_type": "bot_started", "timestamp": 1790280000000,
  "chat_id": 555, "user": { "user_id": 42, "first_name": "Данила", "is_bot": false, ... },
  "payload": "ref_123", "user_locale": "ru" }

// Новое сообщение
{ "update_type": "message_created", "timestamp": 1790280000000,
  "message": {
    "sender":    { "user_id": 42, "first_name": "Данила", ... },
    "recipient": { "chat_id": 555, "chat_type": "dialog" },
    "timestamp": 1790280000000,
    "body": { "mid": "mid.abc", "seq": 1, "text": "/start", "attachments": [] }
  } }

// Нажатие callback-кнопки
{ "update_type": "message_callback", "timestamp": 1790280000000,
  "callback": { "callback_id": "cb.xyz", "payload": "ping", "user": { "user_id": 42, ... } },
  "message": { ...исходное сообщение с клавиатурой... } }
```

Где что лежит:

| Нужно | `message_created` | `message_callback` | `bot_started` |
|---|---|---|---|
| id пользователя | `message.sender.user_id` | `callback.user.user_id` | `user.user_id` |
| id чата | `message.recipient.chat_id` | `message.recipient.chat_id` | `chat_id` |
| текст | `message.body.text` | — | — |
| id сообщения | `message.body.mid` | `message.body.mid` | — |
| данные кнопки/ссылки | — | `callback.payload` | `payload` |

> **Важно для новичков из Telegram:** первый вход пользователя в бота приходит как отдельное событие **`bot_started`**, а не как сообщение `/start`. Команду `/start` набранную руками обрабатывай отдельно, через `message_created`.

### Получение апдейтов: вебхук или polling

- **Вебхук** — единственный вариант для прода.
  - Подписка: `POST /subscriptions` с `{url, secret, update_types}`.
  - MAX шлёт `POST` на твой URL, а секрет кладёт в заголовок `X-Max-Bot-Api-Secret`.
  - Требования: только HTTPS, только порт 443, сертификат от доверенного УЦ, ответ `200` в течение 30 секунд.
  - При ошибках MAX повторяет доставку до 10 раз, а после 8 часов неудач снимает подписку.
- **Long polling** (`GET /updates`) подходит только для разработки: у него ограничена скорость и срок хранения событий.
- **Одновременно нельзя.** Пока есть подписка на вебхук, polling ничего не получает.

### Загрузка файлов — в три шага

1. `POST /uploads?type=image` → `{ "url": "..." }`.
2. `POST <url>` с файлом (`multipart/form-data`, поле `data`) → в ответе `token`.
3. Отправка сообщения с вложением `{"type": "image", "payload": {"token": "..."}}`.

Сразу после загрузки файл может ещё обрабатываться, и отправка вернёт ошибку `attachment.not.ready`. **maxapi делает все три шага и повторы сам** — достаточно передать `InputMedia("photo.jpg")`.

### Так выглядит бот вообще без библиотек

Весь протокол — это один POST-эндпоинт и `match` по `update_type`. Никакой магии нет:

```python
import httpx
from fastapi import FastAPI, HTTPException, Request

TOKEN, SECRET = "...", "..."
api = httpx.AsyncClient(base_url="https://platform-api2.max.ru", headers={"Authorization": TOKEN})
app = FastAPI()


@app.post("/max/webhook")
async def webhook(request: Request):
    if request.headers.get("X-Max-Bot-Api-Secret") != SECRET:
        raise HTTPException(403)
    u = await request.json()

    match u["update_type"]:
        case "bot_started":
            await api.post("/messages", params={"chat_id": u["chat_id"]}, json={"text": "Привет!"})
        case "message_created":
            msg = u["message"]
            text = (msg.get("body") or {}).get("text") or ""
            await api.post("/messages", params={"chat_id": msg["recipient"]["chat_id"]},
                           json={"text": f"Ты написал: {text}"})
        case "message_callback":
            await api.post("/answers", params={"callback_id": u["callback"]["callback_id"]},
                           json={"notification": "pong"})
    return {"ok": True}
```

Проблемы начинаются, когда хендлеров становится 50: нужны фильтры, роутеры, FSM, клавиатуры, middleware и типизация. Именно это и даёт maxapi.

---

## 2. Почему не клиент из OpenAPI

MAX предлагает сгенерировать клиент из `schema.yaml` (`openapi-python-client` и другие генераторы). Для бота это плохая идея:

- **Генератор даёт только модели и функции-обёртки над HTTP.** Диспетчера, фильтров, FSM и билдера клавиатур нет. Всё это пришлось бы писать самому, отсюда и «много лишнего кода».
- **Полиморфизм ломается.** В API полиморфные почти все ключевые типы: `Update`, `Button`, `Attachment`. MAX сам пишет, что генераторы обрабатывают их по-разному, а для Python апдейты нужно раскладывать по `update_type` вручную.
- **Вокруг клиента много мелочей.** Сгенерированный Python-клиент по умолчанию добавляет к токену `Bearer`, и это нужно отключать через `prefix=""`. Некоторые поля кнопок доступны только через словарь.

Когда генератор всё же уместен: интеграция на другом языке, где нет библиотеки, или разовый скрипт. Схема как **справочник** полезна всегда: какие есть поля, лимиты и типы.

---

## 3. Шпаргалка aiogram → maxapi

Импорты, которые покрывают почти всё:

```python
from maxapi import Bot, Dispatcher, F, Router
from maxapi.context import MemoryContext, State, StatesGroup
from maxapi.enums import ParseMode
from maxapi.filters.callback_payload import CallbackPayload
from maxapi.types import (
    BotStarted, Command, ErrorEvent, InputMedia, MessageCallback, MessageCreated,
    CallbackButton, LinkButton, MessageButton, OpenAppButton, RequestContactButton,
)
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
```

| aiogram | maxapi |
|---|---|
| `Bot(token)` | `Bot(token, auto_requests=False)` — [почему](#6-грабли) |
| `dp.include_router(r)` | `dp.include_routers(r1, r2)` |
| `@router.message(Command("start"))` | `@router.message_created(Command("start"))` |
| `CommandStart(deep_link=True)` | `@router.bot_started()` → `event.payload` |
| `F.text` | `F.message.body.text` |
| `message.text` | `event.message.body.text` |
| `message.from_user.id` | `event.message.sender.user_id` |
| `message.chat.id` | `event.message.recipient.chat_id` |
| `message.answer("…")` / `message.reply("…")` | `event.message.answer("…")` / `event.message.reply("…")` |
| `bot.send_message(chat_id, "…")` | `bot.send_message(chat_id=…, text="…")` или `user_id=…` |
| `@router.callback_query(F.data == "x")` | `@router.message_callback(F.callback.payload == "x")` |
| `callback.data` | `event.callback.payload` |
| `callback.answer("…")` | `event.ack(notification="…")` |
| `callback.message.edit_text("…")` | `event.answer(new_text="…", notification="…")` |
| `class Cb(CallbackData, prefix="buy")` | `class Cb(CallbackPayload, prefix="buy")` |
| `Cb.filter(F.action == "x")` → `callback_data` | `Cb.filter(F.action == "x")` → аргумент `payload` |
| `reply_markup=kb.as_markup()` | `attachments=[kb.as_markup()]` |
| `InlineKeyboardButton(web_app=WebAppInfo(url=…))` | `OpenAppButton(text=…, web_app="username_бота")` — URL мини-аппа задаётся в кабинете бота |
| `ReplyKeyboardMarkup` | нет; ближе всего `MessageButton` |
| `parse_mode="HTML"` | `format=ParseMode.HTML` (есть только `HTML` и `MARKDOWN`) |
| `FSMContext` (аргумент `state`) | `MemoryContext` (аргумент **`context`**) |
| `@router.message(Form.name)` | `@router.message_created(Form.name)` |
| `state.set_state / update_data / get_data / clear` | `context.set_state / update_data / get_data / clear` — те же имена |
| `RedisStorage` | `Dispatcher(storage=RedisContext, redis_client=Redis(...))` |
| `dp.message.middleware(m)` | `dp.register_inner_middleware(m)`; сигнатура `__call__(handler, event, data)` та же |
| `@router.errors()` | `@router.errors()` → `event.exception` |
| `dp.start_polling(bot)` | `dp.start_polling(bot)` |
| `SimpleRequestHandler` (вебхук) | `FastAPIMaxWebhook(dp=dp, bot=bot, secret=…).setup(app, path)` |
| `FSInputFile("a.jpg")` | `InputMedia("a.jpg")` в `attachments` |
| `bot.set_my_commands([...])` | `bot.set_commands(BotCommand(name=…, description=…), …)` |
| `create_start_link(...)` | `maxapi.utils.deep_linking.create_start_link / create_startapp_link` |

Отличия, о которые спотыкаются:
- **Только первый подходящий хендлер.** Как и в aiogram, апдейт получает первый хендлер, чьи фильтры прошли. Поэтому ловушку всего (echo) подключай последней.
- **Аргументы хендлера подставляются по имени.** Можно запросить `context`, `payload`, `session` (из нашего middleware) и всё, что положил middleware в `data`. Лишние имена просто не придут.

---

## 4. Рецепты

Все примеры проверены: я прогонял их через вебхук против фейкового MAX API.

### Минимальный бот (polling)

```python
import asyncio
from maxapi import Bot, Dispatcher, F, Router
from maxapi.types import BotStarted, Command, MessageCreated

router = Router()


@router.bot_started()
async def hello(event: BotStarted):
    await event.bot.send_message(chat_id=event.chat_id, text=f"Привет, {event.user.first_name}!")


@router.message_created(Command("start"))
async def start(event: MessageCreated):
    await event.message.answer("С возвращением!")


@router.message_created(F.message.body.text)
async def echo(event: MessageCreated):
    await event.message.answer(f"Ты написал: {event.message.body.text}")


async def main():
    dp = Dispatcher()
    dp.include_routers(router)
    await dp.start_polling(Bot("TOKEN", auto_requests=False))

asyncio.run(main())
```

### Клавиатура с разными кнопками

```python
kb = InlineKeyboardBuilder()
kb.row(OpenAppButton(text="🚀 Открыть приложение", web_app="my_bot", payload="from_menu"))
kb.row(
    CallbackButton(text="Да", payload="yes"),
    CallbackButton(text="Нет", payload="no"),
)
kb.row(LinkButton(text="Сайт", url="https://example.ru"))
kb.row(RequestContactButton(text="📱 Поделиться номером"))

await event.message.answer("Меню", attachments=[kb.as_markup()])
```

### Callback с типизированным payload (как `CallbackData`)

```python
class BuyPayload(CallbackPayload, prefix="buy"):   # упакуется в "buy|42|buy"
    item_id: int
    action: str


@router.message_created(Command("shop"))
async def shop(event: MessageCreated):
    kb = InlineKeyboardBuilder()
    kb.row(
        CallbackButton(text="Купить", payload=BuyPayload(item_id=42, action="buy").pack()),
        CallbackButton(text="Отмена", payload=BuyPayload(item_id=42, action="cancel").pack()),
    )
    await event.message.answer("Товар #42", attachments=[kb.as_markup()])


@router.message_callback(BuyPayload.filter(F.action == "buy"))
async def buy(event: MessageCallback, payload: BuyPayload):
    # всплывашка + замена текста; attachments не переданы → maxapi подставит
    # вложения исходного сообщения, клавиатура останется
    await event.answer(notification=f"Куплен {payload.item_id}", new_text="Оплачено ✅")
```

Варианты ответа на callback:
- `event.ack(notification="…")` — только всплывашка, сообщение не меняется;
- `event.answer(new_text=…, attachments=[])` — заменить текст и убрать клавиатуру.

### FSM (диалог из нескольких шагов)

```python
class Form(StatesGroup):
    name = State()
    age = State()


@router.message_created(Command("form"))
async def form_start(event: MessageCreated, context: MemoryContext):
    await context.set_state(Form.name)
    await event.message.answer("Как тебя зовут?")


@router.message_created(Form.name, F.message.body.text)
async def form_name(event: MessageCreated, context: MemoryContext):
    await context.update_data(name=event.message.body.text)
    await context.set_state(Form.age)
    await event.message.answer("Сколько лет?")


@router.message_created(Form.age, F.message.body.text)
async def form_age(event: MessageCreated, context: MemoryContext):
    data = await context.get_data()
    await context.clear()
    await event.message.answer(f"{data['name']}, {event.message.body.text} лет")
```

`MemoryContext` живёт в памяти процесса и пропадает при рестарте. Для прода используй Redis:

```python
from redis.asyncio import Redis
from maxapi.context import RedisContext

dp = Dispatcher(storage=RedisContext, redis_client=Redis.from_url("redis://redis:6379/0"))
```

### Написать пользователю не из хендлера (из API, задачи, крона)

```python
await bot.send_message(user_id=user_id, text="Заказ готов 🎉")   # личка
await bot.send_message(chat_id=chat_id, text="Всем привет")      # группа/диалог по chat_id
```

Так работает `POST /api/hello` в шаблоне (`backend/app/api/routes/me.py`). Бот берётся из `app.state.bot`, а в ручку попадает через зависимость `BotDep`.

### Редактирование и удаление

```python
sent = await event.message.answer("Считаю…", attachments=[kb.as_markup()])
mid = sent.message.body.mid

# ВНИМАНИЕ: bot.edit_message без attachments отправляет "attachments": [] —
# по правилам API это УДАЛЯЕТ все вложения, включая клавиатуру
await event.bot.edit_message(message_id=mid, text="Готово ✅", attachments=[kb.as_markup()])  # кнопки остались
await event.bot.edit_message(message_id=mid, text="Готово ✅")                               # кнопки удалены

await event.bot.delete_message(message_id=mid)
```

### Форматирование

```python
from maxapi.enums import ParseMode

await event.message.answer("<b>Жирный</b> и <i>курсив</i>", format=ParseMode.HTML)
await event.message.answer("**Жирный** и _курсив_", format=ParseMode.MARKDOWN)
```

### Файлы и фото

```python
await event.message.answer("Держи", attachments=[InputMedia("static/photo.jpg")])
```

Загрузку, получение токена и повторы при `attachment.not.ready` maxapi сделает сам.

### Диплинки

```python
from maxapi.utils.deep_linking import create_start_link, create_startapp_link

create_start_link("my_bot", "ref_123")     # https://max.ru/my_bot?start=ref_123     → BotStarted.payload
create_startapp_link("my_bot", "order_5")  # https://max.ru/my_bot?startapp=order_5  → start_param в мини-аппе
```

### Обработка ошибок

```python
import logging

log = logging.getLogger(__name__)


@router.errors()
async def on_error(event: ErrorEvent):
    log.error("Хендлер упал", exc_info=event.exception)
```

### Middleware (пример из шаблона — сессия БД в каждый хендлер)

```python
class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event_object, data):
        async with self.session_factory() as session:
            data["session"] = session          # придёт в хендлер как аргумент session
            return await handler(event_object, data)

dp.register_inner_middleware(DbSessionMiddleware(session_factory))
```

Inner-middleware срабатывает только когда нашёлся хендлер. Outer (`register_outer_middleware`) срабатывает на каждый апдейт.

---

## 5. Что в шаблоне пишется один раз

Если открыть `backend/app/bot/` и ужаснуться, стоит понимать: почти всё там — инфраструктура, которую ты больше не трогаешь.

| Файл | Что это | Трогать? |
|---|---|---|
| `bot/__init__.py` | создать `Bot` и `Dispatcher`, подключить middleware и роутеры, подписать вебхук | почти никогда |
| `bot/middlewares.py` | сессия БД в хендлеры | когда нужен новый «инжект» (например, текущий юзер из БД) |
| `bot/polling.py` | точка входа для dev | нет |
| `main.py` (блок вебхука) | `FastAPIMaxWebhook` — приём апдейтов в prod | нет |
| **`bot/handlers/*.py`** | **логика бота** | **постоянно** |
| **`bot/keyboards.py`** | **клавиатуры** | **постоянно** |
| **`services/*.py`** | **бизнес-логика**, общая с API мини-аппа | **постоянно** |

Как добавить новую фичу:

1. Создай `bot/handlers/orders.py` с `router = Router(router_id="orders")` и хендлерами.
2. Добавь его в `bot/handlers/__init__.py` в список `routers`, **перед** `echo.router`.
3. Логику, которая нужна и боту, и мини-аппу, клади в `services/`. Хендлер и HTTP-ручка просто её вызывают.

Шаблон хендлера:

```python
from maxapi import F, Router
from maxapi.types import Command, MessageCreated
from sqlalchemy.ext.asyncio import AsyncSession

router = Router(router_id="orders")


@router.message_created(Command("orders"))
async def my_orders(event: MessageCreated, session: AsyncSession):
    orders = await list_orders(session, user_id=event.message.sender.user_id)
    await event.message.answer("\n".join(o.title for o in orders) or "Заказов нет")
```

---

## 6. Грабли

- **`auto_requests=False`.** По умолчанию maxapi на каждый апдейт делает лишний `GET /chats/{id}`, чтобы заполнить `event.chat`, причём ещё до ответа вебхуку. Это лишний запрос в лимиты. Если MAX ответит ошибкой, вебхук вернёт 500 и начнутся ретраи. Всё нужное уже есть в апдейте. Если чат правда нужен — `await event.chat.fetch()`.
- **Вебхук должен ответить за 30 секунд.** Поэтому в шаблоне `Dispatcher(use_create_task=True)`: вебхук сразу отвечает 200, а хендлер работает в фоне. Долгие задачи (генерация PDF, внешние API) всё равно лучше выносить в очередь.
- **Webhook и polling взаимоисключающие.** Для разработки нужен отдельный тестовый бот.
- **`bot_started` ≠ `/start`.** Первый вход пользователя — это отдельное событие. Обрабатывай оба, как в `handlers/start.py`.
- **Нет reply-клавиатуры.** Все кнопки инлайновые, клавиатура — это вложение `inline_keyboard`.
- **Клавиатура пропадает после правки.** В сыром API в `PUT /messages` действует правило: `attachments: null` — не трогать, `[]` — удалить всё. Но в maxapi:
  - `bot.edit_message(...)` без `attachments` всегда отправляет `[]`, так что клавиатура исчезнет. Если она нужна, передавай её заново;
  - в callback `event.answer(new_text=…)` без `attachments` сам подставляет вложения исходного сообщения, и клавиатура остаётся.
- **Лимиты:**
  - текст сообщения — до 4000 символов;
  - текст кнопки — до 128;
  - `payload` callback-кнопки — до 1024, `open_app` — до 512;
  - при превышении частоты запросов API отвечает `429`.
- **Токен без `Bearer`.** Если ходишь в API руками или через сгенерированный клиент, это первое, что ломается.
- **Сертификат Минцифры.** MAX просит добавить его в доверенные на сервере. Если исходящие запросы падают на TLS, смотри `INSTALL_RU_CA` в `backend/Dockerfile`.

## Ссылки

- Документация API: https://dev.max.ru/docs-api
- OpenAPI-схема: https://github.com/max-messenger/api-schema/blob/main/schema.yaml
- maxapi (проверенный MAX форк): https://github.com/max-messenger/max-botapi-python · примеры: `examples/` в репозитории
- JS-библиотека (для сравнения): https://dev.max.ru/docs/chatbots/bots-coding/js
