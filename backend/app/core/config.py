from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Чайная Лавка"
    environment: Literal["development", "production", "test"] = "development"
    debug: bool = True
    api_prefix: str = "/api"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_port: int = 5173

    database_url: str = "postgresql+asyncpg://tea_user:tea_pass@db:5432/tea_shop"

    bot_token: str = "CHANGE_ME"
    bot_username: str = "change_me_bot"
    bot_admin_ids_raw: str = Field(default="123456789", alias="BOT_ADMIN_IDS")

    frontend_app_url: str = "http://localhost:5173"
    backend_public_url: str = "http://localhost:8000"
    media_dir: str = "media"
    channel_url: str = "https://t.me/tea_boutique_channel"
    channel_chat_id: str = "-1003357674923"
    use_ngrok_for_webapp: bool = False
    ngrok_bin: str = "ngrok"
    ngrok_api_port: int = 4040
    ngrok_config_path: str | None = None

    allow_demo_auth: bool = True
    demo_user_id: int = 900000001
    telegram_init_data_lifetime: int = 86400

    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    contact_telegram: str = "@tea_boutique_manager"
    contact_phone: str = "+7 (900) 000-00-00"
    contact_city: str = "Ташкент"
    contact_hours: str = "Ежедневно, 10:00-21:00"

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return bool(value)

    @field_validator("bot_username", mode="before")
    @classmethod
    def normalize_bot_username(cls, value: object) -> str:
        if isinstance(value, str):
            return value.strip().lstrip("@")
        return str(value)

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> str:
        raw = str(value).strip()
        if raw.startswith("postgres://"):
            return raw.replace("postgres://", "postgresql+asyncpg://", 1)
        if raw.startswith("postgresql://") and "+asyncpg" not in raw:
            return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
        if raw.startswith("sqlite:///") and "+aiosqlite" not in raw:
            return raw.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return raw

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @computed_field
    @property
    def bot_admin_ids(self) -> list[int]:
        result: list[int] = []
        for value in self.bot_admin_ids_raw.split(","):
            value = value.strip()
            if value:
                result.append(int(value))
        return result

    @computed_field
    @property
    def database_sync_url(self) -> str:
        return self.database_url.replace("+asyncpg", "").replace("+aiosqlite", "")

    @computed_field
    @property
    def webapp_base_url(self) -> str:
        return self.frontend_app_url.rstrip("/")

    @computed_field
    @property
    def ngrok_api_url(self) -> str:
        return f"http://127.0.0.1:{self.ngrok_api_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
