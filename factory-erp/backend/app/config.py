from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, overridable via environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = (
        "postgresql+psycopg2://factory:factory@db:5432/factory_erp"
    )
    SECRET_KEY: str = "dev-only-change-me"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8081"]


settings = Settings()
