"""In-memory SQLite test fixtures — no Postgres/Docker needed, same pattern
as cae/backend/tests/conftest.py. All models here use String(36) UUID PKs
and portable column types (see app/models/mixins.py), so unlike CAE's
Postgres-specific shims, no dialect patching is required."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import every model so Base.metadata is fully populated before create_all().
# `from app import models` (not `import app.models`) so this doesn't rebind
# the `app` name we need below for the FastAPI instance.
from app import models  # noqa: F401
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
