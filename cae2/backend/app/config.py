"""Runtime settings. Everything is overridable by environment variable (prefix CAE_)."""
import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CAE_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/cae.db"
    data_dir: Path = Path("./data")
    # Blank means "generate one and keep it in data_dir" — never a shared default.
    secret_key: str = ""
    token_minutes: int = 480
    max_upload_mb: int = 50
    static_dir: Path = Path("./static")

    def resolved_secret(self) -> str:
        if self.secret_key:
            return self.secret_key
        self.data_dir.mkdir(parents=True, exist_ok=True)
        key_file = self.data_dir / "secret.key"
        if not key_file.exists():
            key_file.write_text(secrets.token_urlsafe(48))
            key_file.chmod(0o600)
        return key_file.read_text().strip()


settings = Settings()
