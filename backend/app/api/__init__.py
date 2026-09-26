from fastapi import APIRouter

from app.api.routes import dev, health, me


def build_api_router(*, include_dev: bool) -> APIRouter:
    """Все HTTP-ручки мини-аппа. Подключаются в app.main с префиксом /api."""
    router = APIRouter()
    router.include_router(health.router)
    router.include_router(me.router)
    if include_dev:
        router.include_router(dev.router)
    return router
