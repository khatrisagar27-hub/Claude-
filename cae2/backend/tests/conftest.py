"""Tests run against a throwaway SQLite file — no Postgres, no Docker.

The demo engagement (one planted exception per rule) is loaded once per session
and treated as read-only; tests that change data build their own engagement.
"""
import os
import tempfile
from datetime import date

_tmp = tempfile.mkdtemp(prefix="cae2-test-")
# Set CAE_TEST_DATABASE_URL to run the same suite against Postgres; that database is wiped first.
os.environ["CAE_DATABASE_URL"] = os.environ.get("CAE_TEST_DATABASE_URL", f"sqlite:///{_tmp}/test.db")
os.environ["CAE_DATA_DIR"] = _tmp
os.environ["CAE_SECRET_KEY"] = "test-only-secret-key-not-used-anywhere-else"

import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.db import Base, SessionLocal, engine, init_db  # noqa: E402
from app.demo import load_demo, to_xlsx  # noqa: E402
from app.ingest.loader import import_file  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Client, Engagement, Finding, User  # noqa: E402
from app.security import create_token, hash_password  # noqa: E402

from app import models  # noqa: E402,F401

Base.metadata.drop_all(engine)
init_db()


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def demo():
    """(engagement_id, first run summary) of the demo engagement."""
    with SessionLocal() as session:
        eng, run = load_demo(session)
        return eng.id, run.summary


@pytest.fixture
def demo_findings(demo, db):
    def by_rule(code):
        return db.scalars(select(Finding).where(Finding.engagement_id == demo[0], Finding.rule_code == code)).all()
    return by_rule


@pytest.fixture
def make_engagement(db):
    """Builds an engagement from {dataset: list of row dicts}."""
    def build(settings=None, client_gstin=None, period=(date(2025, 4, 1), date(2026, 3, 31)), materiality=0, trivial=0, **datasets):
        client = Client(name="Test Co", gstin=client_gstin)
        db.add(client)
        db.flush()
        eng = Engagement(client_id=client.id, name="Test", period_start=period[0], period_end=period[1], materiality=materiality,
                         trivial_threshold=trivial, settings={"data_as_at": period[1].isoformat(), **(settings or {})})
        db.add(eng)
        db.commit()
        for dataset, records in datasets.items():
            batch = import_file(db, eng, dataset, f"{dataset}.xlsx", to_xlsx(pd.DataFrame(records)))
            assert batch.rows_rejected == 0, batch.errors
        return eng
    return build


def _user(role):
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == f"{role}@test.in"))
        if not user:
            user = User(email=f"{role}@test.in", name=role.title(), role=role, password_hash=hash_password("correct-horse-battery"))
            session.add(user)
            session.commit()
        return {"Authorization": f"Bearer {create_token(user)}"}


@pytest.fixture(scope="session")
def api():
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def partner():
    return _user("partner")


@pytest.fixture(scope="session")
def manager():
    return _user("manager")


@pytest.fixture(scope="session")
def staff():
    return _user("staff")
