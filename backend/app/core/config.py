from __future__ import annotations

import os

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project
    PROJECT_NAME: str = "AI Content Intelligence Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)

    # CORS
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = Field(default=[
        "http://localhost:3000",
        "http://localhost:8000",
    ])

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls, v: str | list[str]
    ) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database — fall back to DATABASE_URL (Render auto-inject) if APP_DATABASE_URL not set
    DATABASE_URL: str = Field(
        default_factory=lambda: os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_content_intel",
        ).replace("postgresql://", "postgresql+asyncpg://") if os.environ.get("DATABASE_URL") else "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_content_intel"
    )
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=10)
    DATABASE_ECHO: bool = Field(default=False)

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379")

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")

    # Rate Limiting
    RATE_LIMIT_TTL: int = Field(default=60)
    RATE_LIMIT_MAX: int = Field(default=100)

    # Auth
    JWT_SECRET: str = Field(default="change-me-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_MINUTES: int = Field(default=15)

    # OpenTelemetry
    OTLP_ENDPOINT: str | None = Field(default=None)
    METRICS_PORT: int = Field(default=9464)


settings = Settings()
