# syntax=docker/dockerfile:1.7
#
# Один Dockerfile — два таргета (как у бэкенда):
#   dev  — Vite dev server с hot reload, исходники монтируются томом
#   prod — собранная статика мини-аппа + Caddy, который её раздаёт
#          и проксирует /api и /max/webhook на бэкенд.
#          Конфиг Caddy (./Caddyfile в корне репо) монтируется в compose.

# ============================== dev ==========================================
FROM node:22-alpine AS dev
WORKDIR /web
EXPOSE 5173
# node_modules живёт в именованном томе (см. docker-compose.yaml), поэтому
# ставим зависимости при старте: подхватываются новые пакеты из package.json
CMD ["sh", "-c", "npm install --no-audit --no-fund && npm run dev"]


# ============================== build ========================================
FROM node:22-alpine AS build
WORKDIR /web

# Сначала только манифесты — слой с node_modules кешируется между сборками
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund

COPY . .
# Консоль eruda в prod-сборке для отладки на телефоне (по умолчанию выключена)
ARG VITE_ENABLE_ERUDA=false
ENV VITE_ENABLE_ERUDA=$VITE_ENABLE_ERUDA
RUN npm run build


# ============================== prod =========================================
FROM caddy:2-alpine AS prod
COPY --from=build /web/dist /srv
