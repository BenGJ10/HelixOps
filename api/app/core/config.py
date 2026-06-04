from __future__ import annotations

from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "HelixOps API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_not_be_default(cls, v: str, info: object) -> str:
        # In production, reject the placeholder value
        import os

        env = os.getenv("ENVIRONMENT", "development")
        if env == "production" and "change-me" in v.lower():
            raise ValueError("SECRET_KEY must be changed in production. Use: openssl rand -hex 32")
        return v


settings = Settings()
