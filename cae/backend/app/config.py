"""
Application configuration using pydantic-settings.
All settings can be overridden via environment variables.
"""
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql://cae_user:cae_password@localhost:5432/cae_db"

    # JWT / Security
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI
    ANTHROPIC_API_KEY: str = ""

    # Runtime environment
    ENVIRONMENT: str = "development"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # File uploads
    UPLOAD_DIR: str = "/tmp/cae_uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # App metadata
    APP_NAME: str = "Continuous Audit Engine"
    APP_VERSION: str = "1.0.0"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()
