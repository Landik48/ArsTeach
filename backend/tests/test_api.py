"""Тесты HTTP-слоя без базы и без сети.

TestClient создаётся без `with`, поэтому lifespan (GET /me к MAX,
подписка на вебхук) не запускается.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings


@pytest.fixture
def make_client(monkeypatch):
    def _make(**env: str) -> TestClient:
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        get_settings.cache_clear()
        from app.main import create_app

        return TestClient(create_app())

    yield _make
    get_settings.cache_clear()


def test_api_requires_init_data(make_client):
    client = make_client(APP_ENV="dev", BOT_MODE="polling")
    assert client.get("/api/me").status_code == 401
    assert client.get("/api/me", headers={"Authorization": "max garbage"}).status_code == 401


def test_dev_routes_hidden_in_prod(make_client):
    client = make_client(
        APP_ENV="prod", BOT_MODE="polling", MAX_BOT_TOKEN="t", MAX_WEBHOOK_SECRET="", PUBLIC_URL=""
    )
    assert client.get("/api/dev/init-data").status_code == 404
    assert client.get("/api/docs").status_code == 404


def test_webhook_checks_secret(make_client):
    client = make_client(APP_ENV="dev", BOT_MODE="webhook", MAX_WEBHOOK_SECRET="s3cret-value")
    update = {"update_type": "bot_started", "timestamp": 0}
    assert client.post("/max/webhook", json=update).status_code == 403
    assert (
        client.post(
            "/max/webhook", json=update, headers={"X-Max-Bot-Api-Secret": "wrong"}
        ).status_code
        == 403
    )


def test_prod_requires_webhook_config(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("BOT_MODE", "webhook")
    monkeypatch.setenv("MAX_BOT_TOKEN", "")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="MAX_BOT_TOKEN"):
        get_settings()
    get_settings.cache_clear()
