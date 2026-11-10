"""Creates .env with random secrets. Does nothing if .env already exists."""
import secrets
from pathlib import Path

env = Path(__file__).resolve().parents[1] / ".env"
if env.exists():
    print(".env already exists - left unchanged")
else:
    env.write_text(
        f"POSTGRES_PASSWORD={secrets.token_hex(24)}\n"
        f"CAE_SECRET_KEY={secrets.token_hex(32)}\n"
        "CAE_BIND=127.0.0.1\n"
        "CAE_PORT=8080\n"
    )
    env.chmod(0o600)
    print("Created .env")
