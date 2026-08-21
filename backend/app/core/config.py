from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/cryptotracker"

    # JWT
    SECRET_KEY: str = "change-me-in-production-must-be-at-least-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_SECONDS: int = 86400  # 24h

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
