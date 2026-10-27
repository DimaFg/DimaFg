from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Все параметры окружения. Значения по умолчанию подходят только для local."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    environment: Literal["local", "test", "staging", "production"] = "local"
    database_url: str = "postgresql+psycopg://postgres@127.0.0.1:5433/photo"

    # Секрет для HMAC IP-адресов и прочих производных значений. В production обязателен.
    app_secret: SecretStr = SecretStr("dev-insecure-secret-change-me")

    cors_origins: list[str] = Field(default_factory=list)
    max_body_bytes: int = 64 * 1024

    # Публичный CDN, с которого раздаются производные версии фотографий.
    media_public_base_url: str = "https://cdn.example.com"

    privacy_policy_version: str = "2026-10-draft"
    lead_expected_response: str = "обычно в течение суток"

    # Антиспам
    lead_min_fill_seconds: float = 3.0
    lead_rate_limit_per_ip_hour: int = 5
    lead_rate_limit_per_contact_day: int = 3
    lead_dedup_window_minutes: int = 10
    ip_hash_retention_days: int = 30

    # Уведомления. Если ничего не настроено, worker пишет обезличенную запись в лог.
    telegram_bot_token: SecretStr | None = None
    telegram_chat_id: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    smtp_starttls: bool = True
    notify_email_from: str | None = None
    notify_email_to: str | None = None
    admin_base_url: str = "http://localhost:3000/admin"

    outbox_max_attempts: int = 8
    outbox_retry_base_seconds: float = 30.0
    outbox_retry_max_seconds: float = 3600.0
    outbox_lock_timeout_seconds: float = 600.0
    worker_poll_seconds: float = 2.0
    # Worker раз в цикл обновляет файл; healthcheck контейнера проверяет его свежесть.
    heartbeat_dir: str = "/tmp/photo-health"  # noqa: S108


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.environment == "production" and settings.app_secret.get_secret_value().startswith(
        "dev-"
    ):
        raise RuntimeError("APP_SECRET must be set in production")
    return settings
