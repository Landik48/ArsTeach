# syntax=docker/dockerfile:1.7
#
# Один Dockerfile — два таргета:
#   dev  — зависимости + dev-инструменты, код монтируется томом (hot reload)
#   prod — код запечён в образ, без dev-зависимостей, непривилегированный пользователь

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # venv вне /app: в dev /app перекрывается томом с исходниками, а venv должен остаться
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH" \
    # aiohttp (клиент бота) берёт системное хранилище сертификатов
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

# --- Сертификаты Минцифры (опционально) ---------------------------------------
# MAX просит добавить корневой сертификат Минцифры в доверенные. Если исходящие
# запросы к platform-api2.max.ru падают с ошибкой проверки сертификата, соберите
# образ с --build-arg INSTALL_RU_CA=true (в docker-compose.yaml есть закомментированный пример).
# Отпечаток корня выводится в лог сборки — сверьте его с опубликованным на gosuslugi.ru
ARG INSTALL_RU_CA=false
RUN if [ "$INSTALL_RU_CA" = "true" ]; then \
      set -eux; \
      apt-get update; \
      apt-get install -y --no-install-recommends curl openssl ca-certificates; \
      for name in root sub; do \
        curl -fsSL "https://gu-st.ru/content/Other/doc/russian_trusted_${name}_ca.cer" -o /tmp/ru.cer; \
        dst="/usr/local/share/ca-certificates/russian_trusted_${name}_ca.crt"; \
        openssl x509 -inform DER -in /tmp/ru.cer -out "$dst" 2>/dev/null \
          || openssl x509 -inform PEM -in /tmp/ru.cer -out "$dst"; \
        openssl x509 -in "$dst" -noout -subject -fingerprint -sha256; \
      done; \
      update-ca-certificates; \
      apt-get purge -y curl; apt-get autoremove -y; rm -rf /var/lib/apt/lists/* /tmp/ru.cer; \
    fi

WORKDIR /app


# ============================== dev ==========================================
FROM base AS dev

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Команда переопределяется в docker-compose.yaml (api-dev / bot-dev / migrate-dev)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# ============================== prod =========================================
FROM base AS prod

# Сначала только зависимости — этот слой кешируется, пока не меняется uv.lock
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .

RUN useradd --system --uid 10001 --no-create-home app
USER app

EXPOSE 8000
# --proxy-headers: берём реальный IP клиента из X-Forwarded-For от Caddy.
# Один воркер: подписка на вебхук делается на старте. Для масштабирования
# лучше несколько контейнеров за Caddy, чем --workers.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips=*"]
