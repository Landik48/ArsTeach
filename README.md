# MAX mini app — шаблон проекта

Бот с мини-приложением в мессенджере MAX. Этот hello world проходит полный путь от чата до базы и задаёт структуру, на которую дальше наращивается реальный проект.

| Слой | Технологии |
|---|---|
| Мини-приложение | React 19 + Vite + [MAX UI](https://dev.max.ru/ui) + MAX Bridge |
| Бэкенд | FastAPI + [maxapi](https://github.com/max-messenger/max-botapi-python) (бот в стиле aiogram) |
| База | PostgreSQL 18 + SQLAlchemy 2 (async) + Alembic |
| Прокси (только prod) | Caddy: статика, `/api`, вебхук, автоматический HTTPS |
| Запуск | Docker Compose, профили `dev` и `prod` |

> Как устроен сам Bot API MAX и как писать хендлеры без лишнего кода — в **[instruction_Api.md](instruction_Api.md)**.

## Что делает hello world

1. Пользователь пишет боту. Бот сохраняет его в БД и присылает две кнопки:
   - **«Открыть приложение»** (`open_app`);
   - **Ping** (callback).
2. Мини-апп открывается, берёт `window.WebApp.initData` и отправляет её в заголовке `Authorization: max <initData>`.
3. Бэкенд проверяет подпись initData (HMAC-SHA256 от токена бота) и показывает профиль.
4. Кнопка **«Сказать привет боту»** вызывает `POST /api/hello`. Счётчик в PostgreSQL увеличивается на 1, и бот пишет сообщение в чат.
5. Второй экран показывает системную кнопку **«Назад»** MAX.

## Как это связано

**dev** — всё на localhost, Caddy не нужен:

```
браузер / туннель ──▶ Vite :5173 ──┬── фронт с hot reload
                                   └── /api/* ──proxy──▶ api-dev :8000 ──▶ PostgreSQL
Серверы MAX ◀── long polling ── bot-dev (отдельный процесс)
```

**prod** — один домен с HTTPS:

```
MAX-клиент ──▶ Caddy :443 ──┬── /            → статика мини-аппа (собрана в frontend/Dockerfile)
Серверы MAX ─▶              ├── /api/*       → api :8000 ──▶ PostgreSQL
                            └── /max/webhook → api :8000 → хендлеры бота
```

В обоих режимах фронт ходит в относительный `/api` на своём же адресе. В dev запрос проксирует Vite, в prod — Caddy. Поэтому CORS не нужен.

## Структура

```
.
├── docker-compose.yaml     # профили dev / prod, база без профиля
├── Caddyfile               # prod: https://$DOMAIN — статика + /api + /max/webhook
├── .env.example            # все настройки → копируется в .env
├── instruction_Api.md      # как работает MAX Bot API и maxapi
├── backend/
│   ├── Dockerfile          # таргеты dev и prod
│   ├── pyproject.toml      # зависимости (uv), настройки ruff/pytest
│   ├── alembic.ini
│   ├── migrations/         # миграции (env.py берёт URL базы из app.config)
│   ├── tests/              # initData, авторизация, секрет вебхука
│   └── app/
│       ├── main.py         # FastAPI: /api, вебхук, lifespan
│       ├── config.py       # настройки из env (pydantic-settings)
│       ├── db.py           # движок и фабрика сессий
│       ├── models.py       # ORM-модели
│       ├── security/init_data.py   # проверка подписи initData ← безопасность
│       ├── services/       # бизнес-логика, общая для API и бота
│       ├── api/
│       │   ├── deps.py     # сессия, бот, текущий пользователь
│       │   ├── schemas.py  # ответы API
│       │   └── routes/     # health, me (мини-апп), dev (только в dev)
│       └── bot/
│           ├── __init__.py     # создание бота/диспетчера, подписка на вебхук
│           ├── polling.py      # long polling для dev
│           ├── middlewares.py  # сессия БД в хендлеры
│           ├── keyboards.py    # inline-клавиатуры
│           └── handlers/       # роутеры — здесь пишется логика бота
└── frontend/
    ├── Dockerfile          # dev: Vite dev server; prod: сборка Vite → Caddy со статикой
    ├── index.html          # подключение MAX Bridge (st.max.ru/js/max-web-app.js)
    ├── vite.config.ts      # dev-сервер :5173 + прокси /api на бэкенд
    └── src/
        ├── main.tsx        # MaxUI-провайдер, eruda, dev-мост
        ├── App.tsx         # загрузка профиля, переключение экранов
        ├── api/client.ts   # fetch к /api с initData
        ├── max/            # типы и обёртка MAX Bridge, dev-мост для браузера
        └── screens/        # экраны мини-аппа
```

Сервисы compose:

| Профиль | Сервис | Что делает |
|---|---|---|
| — | `db` | PostgreSQL, стартует всегда |
| dev | `migrate-dev` | `alembic upgrade head` и выход |
| dev | `api-dev` | FastAPI с `--reload`, порт 8000 |
| dev | `bot-dev` | бот через long polling, перезапуск при правках |
| dev | `web-dev` | Vite dev server, порт 5173 |
| dev | `db-port-dev` | проброс базы на `localhost:5432` |
| prod | `migrate` | миграции и выход |
| prod | `api` | FastAPI + приём вебхука |
| prod | `caddy` | образ из `frontend/Dockerfile` (статика) + `./Caddyfile`, порты 80/443 |

## Быстрый старт (dev)

Нужны Docker и Docker Compose.

```bash
cp .env.example .env
docker compose --profile dev up --build
```

| Что | Адрес |
|---|---|
| Мини-апп | http://localhost:5173 |
| Swagger | http://localhost:8000/api/docs (или http://localhost:5173/api/docs) |
| PostgreSQL | `localhost:5432`, логин и пароль из `.env` |

Правки подхватываются без перезапуска:
- `frontend/src` — через Vite HMR;
- `backend/app` — uvicorn `--reload`, а бот перезапускается через watchfiles.

Фронт можно запускать и прямо на хосте: `cd frontend && npm install && npm run dev`. Бэкенд при этом остаётся в Docker. Прокси по умолчанию смотрит на `localhost:8000`, а этот порт `api-dev` пробрасывает на хост.

### Мини-апп в браузере без MAX

Вне MAX у мини-аппа нет initData. В dev фронт сам просит бэкенд подписать тестовую initData (`GET /api/dev/init-data`) тем же алгоритмом, что и клиент MAX. Поэтому проверка подписи работает по-настоящему даже в обычном браузере.

Параметр `?startapp=promo` в адресе эмулирует ссылку `https://max.ru/<bot>?startapp=promo`. В prod этой ручки нет.

### Бот в dev

1. Заведите **отдельного тестового бота** на [business.max.ru](https://business.max.ru/self). Long polling не работает, пока у бота есть подписка на вебхук, а она будет у боевого.
2. Впишите токен в `.env`: `MAX_BOT_TOKEN=...`.
3. Пересоздайте контейнер бота: `docker compose --profile dev up -d --force-recreate bot-dev`. Без токена бот просто не стартует, а API и мини-апп работают.

### Открыть мини-апп внутри MAX

MAX открывает мини-апп только по HTTPS.

1. Поднимите туннель на `localhost:5173` (tuna.am, cloudflared, ngrok). Vite пускает любой домен и проксирует `/api`, так что через туннель работает всё.
2. Укажите адрес туннеля в настройках бота: **Чат-боты → бот → ⋮ → Настройки → ссылка на мини-приложение**.

В MAX нет DevTools, поэтому в dev-сборке включена [eruda](https://github.com/liriliri/eruda) — консоль и сеть прямо на экране телефона.

## Продакшен

1. Подготовьте сервер с Docker. A-запись домена должна указывать на его IP, порты 80 и 443 открыты.
2. Заполните в `.env`:
   - `MAX_BOT_TOKEN` и `MAX_WEBHOOK_SECRET`;
   - `PUBLIC_URL=https://домен` и `DOMAIN=домен`;
   - `ACME_EMAIL`;
   - надёжный `POSTGRES_PASSWORD`.
3. Запустите:

   ```bash
   docker compose --profile prod up -d --build
   ```

4. В настройках бота укажите URL мини-аппа: `https://домен`.

При старте:
- `migrate` применяет миграции;
- `api` подписывает бота на `${PUBLIC_URL}/max/webhook` с секретом;
- Caddy получает сертификат Let's Encrypt.

Требования MAX к вебхуку эта связка выполняет:
- HTTPS на порту 443;
- доверенный сертификат;
- ответ 200 быстрее 30 секунд — апдейты обрабатываются в фоне.

Если исходящие запросы к `platform-api2.max.ru` падают с ошибкой сертификата, соберите бэкенд с сертификатами Минцифры. Для этого раскомментируйте `INSTALL_RU_CA: "true"` в `docker-compose.yaml` и сверьте отпечаток в логе сборки.

## Как расширять

| Задача | Где |
|---|---|
| Новая таблица | `backend/app/models.py` → сгенерировать и применить миграцию (см. [Команды](#команды)) |
| Бизнес-логика | `backend/app/services/`, её вызывают и API, и бот |
| Новая ручка API | `backend/app/api/routes/` + подключить в `api/__init__.py`; пользователь берётся через `CurrentUser` |
| Новый хендлер бота | роутер в `backend/app/bot/handlers/` + добавить в список `routers`. Порядок важен, см. [instruction_Api.md](instruction_Api.md) |
| Новый экран | `frontend/src/screens/`; метод API — в `src/api/client.ts` |
| Новый метод MAX Bridge | тип в `src/max/types.ts`, обёртка в `src/max/bridge.ts` |
| Роутинг в prod | `Caddyfile` в корне; после правки: `docker compose --profile prod restart caddy` |

## Команды

Dev (все команды из корня репозитория):

```bash
# поднять / остановить (данные базы остаются в томе)
docker compose --profile dev up --build
docker compose --profile dev down

# логи
docker compose --profile dev logs -f api-dev bot-dev

# миграция по изменениям models.py → применить
docker compose --profile dev run --rm api-dev alembic revision --autogenerate -m "add orders"
docker compose --profile dev run --rm migrate-dev

# тесты и линтер бэкенда (без базы)
docker compose --profile dev run --rm --no-deps api-dev pytest
docker compose --profile dev run --rm --no-deps api-dev sh -c "ruff check . && ruff format --check ."

# консоль PostgreSQL
docker compose exec db sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB'
```

Prod:

```bash
docker compose --profile prod up -d --build     # собрать и запустить / обновить
docker compose --profile prod logs -f           # логи
docker compose --profile prod down              # остановить
```

## Грабли, которые уже учтены

- **initData проверяется только на бэкенде.** `user_id` берётся из проверенной подписи, а не из тела запроса. `initDataUnsafe` на фронте годится только для отображения. Срок жизни initData — 1 час (`INIT_DATA_TTL`).
- **`auto_requests=False` в maxapi.** По умолчанию библиотека на каждый апдейт делает лишний `GET /chats/{id}`, ещё до ответа вебхуку. Если MAX в этот момент ответит ошибкой, вебхук отдаст 500.
- **Никакого hash-роутинга.** MAX передаёт данные запуска во фрагменте URL (`#WebAppData=...`). Если понадобится роутер, берите history-режим.
- **Не запрещайте фреймы** (`X-Frame-Options`, `frame-ancestors`): веб-версия MAX может показывать мини-апп во фрейме.
- **React зафиксирован на 19.2.8**, этого требует peer-зависимость `@maxhub/max-ui` 0.5.
- **maxapi с PyPI — версия автора.** Вариант, проверенный командой MAX, ставится из GitHub (строка есть в `pyproject.toml`).

## Документация MAX

- [Bot API](https://dev.max.ru/docs-api) · [OpenAPI-схема](https://github.com/max-messenger/api-schema) · [разбор API в этом репо](instruction_Api.md)
- [Мини-приложения](https://dev.max.ru/docs/webapps/introduction) · [MAX Bridge](https://dev.max.ru/docs/webapps/bridge) · [Валидация initData](https://dev.max.ru/docs/webapps/validation)
- [MAX UI](https://dev.max.ru/ui)
