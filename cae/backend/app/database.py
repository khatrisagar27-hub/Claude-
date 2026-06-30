"""
SQLAlchemy database engine, session factory, and base model.
Provides get_db() dependency for FastAPI route injection.
"""
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.config import settings


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# Connection-pool tuning only applies to server-backed databases (e.g. Postgres).
# SQLite uses a SingletonThreadPool that rejects pool_size/max_overflow/pool_timeout,
# so those options are omitted when running against SQLite (e.g. in tests).
_engine_kwargs: dict = {
    "pool_pre_ping": True,           # Detect stale connections before checkout
    "echo": settings.is_development,  # Log SQL in dev only
}
if not settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(
        pool_size=10,                # Default pool size
        max_overflow=20,             # Extra connections beyond pool_size
        pool_timeout=30,             # Seconds to wait for a connection
        pool_recycle=1800,           # Recycle connections after 30 minutes
    )

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,      # Avoid lazy-load after commit in async patterns
)

# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session and ensure it is closed after the request.

    Usage in FastAPI routes:
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
