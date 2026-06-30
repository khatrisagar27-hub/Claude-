"""HTTP integration harness: a TestClient over the real FastAPI app.

``get_db`` is overridden to a fresh in-memory SQLite engine (shared via
StaticPool) that the test also seeds through, so seeded rows are visible to the
request handlers.  Requests carry real JWTs, so the full HTTPBearer ->
get_current_user -> role-check -> handler stack is exercised end to end.

The Postgres->SQLite shims (JSONB->JSON, gen_random_uuid() stripping,
string-tolerant UUID binds) are applied by the top-level tests/conftest.py.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.utils.security import create_access_token
from tests.factories import make_user


class ApiHarness:
    def __init__(self, client: TestClient, session_factory):
        self.client = client
        self.db = session_factory()

    def add(self, obj):
        self.db.add(obj)
        self.db.commit()
        return obj

    def seed_user(self, **kwargs):
        return self.add(make_user(**kwargs))

    def headers_for(self, user) -> dict:
        token = create_access_token({"sub": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    def auth_get(self, url, user, **kw):
        return self.client.get(url, headers=self.headers_for(user), **kw)

    def auth_post(self, url, user, **kw):
        return self.client.post(url, headers=self.headers_for(user), **kw)

    def auth_patch(self, url, user, **kw):
        return self.client.patch(url, headers=self.headers_for(user), **kw)


@pytest.fixture
def api():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        session = Session()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    harness = ApiHarness(TestClient(app), Session)
    try:
        yield harness
    finally:
        harness.db.close()
        app.dependency_overrides.clear()
        engine.dispose()
