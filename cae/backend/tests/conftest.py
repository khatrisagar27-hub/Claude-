"""Shared fixtures.

* An in-memory DuckDB with the CAE table shapes, and a rule stub (rule tests).
* An in-memory SQLite ORM session, ``db`` (engine, API and connector tests). The app targets
  PostgreSQL; two Postgres-only constructs are shimmed so the schema builds on SQLite:
  ``JSONB`` renders as ``JSON``, and ``gen_random_uuid()`` server defaults are stripped
  (tests always supply primary keys).
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


def _strip_pg_only_server_defaults() -> None:
    """Drop ``gen_random_uuid()`` server defaults that SQLite cannot evaluate."""
    # Importing the models package registers every ORM class on the shared Base. Done here,
    # not at import time, so tests/test_integration_pg.py can point the app at Postgres first.
    import app.models  # noqa: F401
    from app.database import Base

    for table in Base.metadata.tables.values():
        for column in table.columns:
            default = column.server_default
            arg = getattr(default, "arg", None)
            text_value = str(getattr(arg, "text", "")) if arg is not None else ""
            if "gen_random_uuid" in text_value:
                column.server_default = None


@pytest.fixture(autouse=True)
def _sqlite_schema(request):
    """Strip Postgres-only defaults before any SQLite schema is built. The Postgres
    end-to-end suite is left alone: it must import the app only after setting DATABASE_URL."""
    if "test_integration_pg" not in request.node.nodeid:
        _strip_pg_only_server_defaults()


@pytest.fixture
def db():
    """Yield a clean, isolated in-memory SQLite session for a single test."""
    from app.database import Base

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


# ---------------------------------------------------------------- DuckDB rule harness
from tests.duckdb_harness import build_conn  # noqa: E402


@pytest.fixture
def conn_factory():
    return build_conn
