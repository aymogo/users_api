from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Auth Service"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    DATABASE_URL: str = "postgresql+asyncpg://dev:admin123@localhost:5432/users_api_db"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    VERIFICATION_CODE_EXPIRE_MINUTES: int = 30
    UNVERIFIED_USER_TTL_DAYS: int = 2

    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (avoids re-parsing env on every import)."""
    return Settings()


settings = get_settings()
