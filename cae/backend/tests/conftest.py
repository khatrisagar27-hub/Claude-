"""
Shared pytest fixtures for the CAE backend test suite.

The application targets PostgreSQL, but the engine/business-logic tests only need
a relational store to exercise the SQLAlchemy ORM queries.  We run them against an
in-memory SQLite database so the suite stays fast and has zero external
dependencies.  Two Postgres-specific constructs are shimmed so the schema can be
created on SQLite:

  * ``JSONB`` columns are rendered as the generic ``JSON`` type.
  * ``server_default=text("gen_random_uuid()")`` is stripped (tests always supply
    primary keys explicitly), since SQLite has no such function.
"""
import os

# Settings is instantiated at import time from the environment, so make sure the
# app never tries to reach a real Postgres/Redis instance during tests.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-cae-unit-tests-min-32chars")
os.environ.setdefault("ENVIRONMENT", "test")

import uuid

import pytest
from sqlalchemy import Uuid, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@compiles(JSONB, "sqlite")
def _compile_jsonb_as_json_on_sqlite(element, compiler, **kw):  # noqa: ANN001
    """Render Postgres JSONB columns as plain JSON when the dialect is SQLite."""
    return "JSON"


# Postgres drivers transparently coerce a UUID *string* bound against a UUID
# column (e.g. ``User.id == sub`` where ``sub`` is a JWT claim string).  SQLite's
# emulated UUID type expects a uuid.UUID object and calls ``value.hex``, so we
# widen its bind processor to accept strings and match production behaviour.
_orig_uuid_bind_processor = Uuid.bind_processor


def _string_tolerant_uuid_bind_processor(self, dialect):
    processor = _orig_uuid_bind_processor(self, dialect)
    if processor is None:
        return None

    def process(value):
        if isinstance(value, str):
            value = uuid.UUID(value)
        return processor(value)

    return process


Uuid.bind_processor = _string_tolerant_uuid_bind_processor


# Importing the models package registers every ORM class on the shared Base and
# resolves all string-based relationships, so create_all() builds the full schema.
import app.models  # noqa: E402,F401
from app.database import Base  # noqa: E402


def _strip_pg_only_server_defaults() -> None:
    """Drop ``gen_random_uuid()`` server defaults that SQLite cannot evaluate."""
    for table in Base.metadata.tables.values():
        for column in table.columns:
            default = column.server_default
            arg = getattr(default, "arg", None)
            text_value = str(getattr(arg, "text", "")) if arg is not None else ""
            if "gen_random_uuid" in text_value:
                column.server_default = None


_strip_pg_only_server_defaults()


@pytest.fixture
def db():
    """Yield a clean, isolated in-memory SQLite session for a single test."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
