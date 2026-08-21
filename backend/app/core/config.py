from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/cryptotracker"
    REDIS_URL: str = "redis://redis:6379/0"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
