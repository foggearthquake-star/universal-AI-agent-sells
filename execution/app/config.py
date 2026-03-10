from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_work_chat_id: int = Field(default=0, alias="TELEGRAM_WORK_CHAT_ID")
    telegram_work_topic_id: int | None = Field(default=None, alias="TELEGRAM_WORK_TOPIC_ID")
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    database_url: str = Field(alias="DATABASE_URL")
    amo_base_url: str | None = Field(default=None, alias="AMO_BASE_URL")
    amo_access_token: str | None = Field(default=None, alias="AMO_ACCESS_TOKEN")
    default_client_id: str = Field(default="default", alias="DEFAULT_CLIENT_ID")
    clients_dir: Path = Field(default=Path("clients"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)


settings = Settings()
