import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.utils.time import utcnow


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return utcnow()


class UUIDPKMixin:
    """String-UUID primary key. Stored as String(36) rather than the
    Postgres-native UUID type so the same model works unmodified against
    SQLite in tests, matching the pattern in cae/backend/tests/conftest.py."""

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
