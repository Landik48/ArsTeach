"""Настройки приложения.

Все значения берутся из переменных окружения (в Docker — из файла .env в корне
репозитория, см. .env.example). Один и тот же код работает и в dev, и в prod:
отличаются только значения APP_ENV и BOT_MODE, которые задаёт docker-compose.yaml.
"""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Подставляется вместо токена в dev, если настоящего бота ещё нет.
# Тогда API и мини-апп в браузере работают, а бот просто не запускается.
DEV_PLACEHOLDER_TOKEN = "dev-placeholder-token"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Окружение ---------------------------------------------------------
    app_env: Literal["dev", "prod"] = "dev"
    log_level: str = "INFO"

    # --- MAX ---------------------------------------------------------------
    # Токен выдаётся после модерации бота на business.max.ru
    max_bot_token: str = ""
    # Имя бота (без @). Нужно кнопке open_app; если пусто — берём из GET /me
    max_bot_username: str = ""
    # polling — для разработки, webhook — единственный вариант для прода
    bot_mode: Literal["polling", "webhook"] = "polling"
    # Публичный адрес сервиса, например https://app.example.ru
    # (вебхук будет на {public_url}/max/webhook, порт только 443)
    public_url: str = ""
    # Секрет вебхука: MAX присылает его в заголовке X-Max-Bot-Api-Secret.
    # Разрешены A-Z a-z 0-9 _ -, длина 5–256
    max_webhook_secret: str = ""
    # Сколько секунд считаем initData свежими (MAX рекомендует 1 час)
    init_data_ttl: int = 3600
    # Необязательно: другой адрес Bot API (по умолчанию https://platform-api2.max.ru).
    # Нужен для тестов с фейковым сервером или для исходящего прокси
    max_api_url: str = ""

    # --- PostgreSQL --------------------------------------------------------
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_user: str = "app"
    postgres_password: str = "app"
    postgres_db: str = "app"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_dev(self) -> bool:
        return self.app_env == "dev"

    @property
    def bot_token(self) -> str:
        """Токен для подписи/проверки initData и для клиента бота."""
        return self.max_bot_token or DEV_PLACEHOLDER_TOKEN

    @property
    def has_real_token(self) -> bool:
        return bool(self.max_bot_token)

    @property
    def webhook_url(self) -> str:
        return f"{self.public_url.rstrip('/')}/max/webhook"

    @model_validator(mode="after")
    def _check_prod(self) -> "Settings":
        # В проде лучше упасть на старте, чем молча работать с неполным конфигом
        if self.app_env == "prod":
            missing = [
                name
                for name, value in {
                    "MAX_BOT_TOKEN": self.max_bot_token,
                    "PUBLIC_URL": self.public_url if self.bot_mode == "webhook" else "-",
                    "MAX_WEBHOOK_SECRET": (
                        self.max_webhook_secret if self.bot_mode == "webhook" else "-"
                    ),
                }.items()
                if not value
            ]
            if missing:
                raise ValueError(f"В prod не заданы переменные: {', '.join(missing)}")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
