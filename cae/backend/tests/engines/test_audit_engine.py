"""Tests for AuditEngine construction — company_id validation / injection guard.

AuditEngine interpolates self.company_id into the DuckDB load queries via an
f-string. The constructor validates that company_id is a real UUID, which both
normalises it and closes that SQL-injection vector.
"""
import uuid

import pytest

from app.engines.audit_engine import AuditEngine
from tests.factories import COMPANY_ID


def test_valid_company_id_is_normalised(db):
    engine = AuditEngine(db, str(COMPANY_ID))
    assert engine.company_id == str(COMPANY_ID)


def test_company_id_accepts_uuid_object(db):
    engine = AuditEngine(db, COMPANY_ID)
    assert engine.company_id == str(COMPANY_ID)


@pytest.mark.parametrize("malicious", [
    "x' OR '1'='1",
    "'; DROP TABLE sales_invoices; --",
    "not-a-uuid",
    "",
])
def test_injection_or_garbage_company_id_is_rejected(db, malicious):
    with pytest.raises(ValueError):
        AuditEngine(db, malicious)
