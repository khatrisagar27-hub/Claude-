"""Tests for AuditEngine — company_id injection guard, loader types, dedup.

AuditEngine interpolates self.company_id into the DuckDB load queries via an
f-string. The constructor validates that company_id is a real UUID, which both
normalises it and closes that SQL-injection vector.
"""
import uuid
from datetime import date

import pandas as pd
import pytest

from app.engines.audit_engine import AuditEngine
from app.models.audit import AuditException, AuditRule, RuleExecution
from app.rules import get_rule_fn
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


# ---------------------------------------------------------------------------
# Loader type normalisation, dedup and unregistered rules
# ---------------------------------------------------------------------------
def _engine_with(db, **frames):
    """AuditEngine with DuckDB tables registered from frames (skips the Postgres load)."""
    engine = AuditEngine(db, str(COMPANY_ID))
    for name, df in frames.items():
        engine._register(name, df)
    engine._data_loaded = True
    return engine


def _rule(db, code, **kw):
    rule = AuditRule(id=uuid.uuid4(), company_id=COMPANY_ID, rule_code=code, rule_name=code,
                     category="revenue", severity="high", rule_type="python",
                     run_frequency="daily", is_active=True, auto_raise_exception=True,
                     requires_approval=False, **kw)
    db.add(rule)
    db.commit()
    return rule


def test_jsonb_dicts_are_queryable_with_json_operators(db):
    """JSONB used to reach DuckDB as a STRUCT, making PUR-002 error on every run."""
    cid = str(COMPANY_ID)
    df = pd.DataFrame([
        {"id": "p1", "company_id": cid, "vendor_id": "v", "invoice_number": "OVER",
         "total_amount": 120000.0, "raw_data": {"po_value": 100000}},
        {"id": "p2", "company_id": cid, "vendor_id": "v", "invoice_number": "NONE",
         "total_amount": 120000.0, "raw_data": None},
    ])
    engine = _engine_with(db, purchase_invoices=df)

    results = get_rule_fn("PUR-002")(engine.conn, cid, None)

    assert [r["evidence"]["invoice_number"] for r in results] == ["OVER"]


def test_timestamptz_columns_compare_on_ist_calendar(db):
    """TIMESTAMPTZ used to make SAL-004 fail with a DuckDB binder error."""
    cid = str(COMPANY_ID)
    df = pd.DataFrame([
        {"id": "s1", "company_id": cid, "invoice_number": "LATE", "invoice_date": pd.Timestamp("2025-01-10").date(),
         "created_at": pd.Timestamp("2025-03-20 10:00", tz="UTC"), "total_amount": 200000.0, "status": "confirmed"},
        {"id": "s2", "company_id": cid, "invoice_number": "ONTIME", "invoice_date": pd.Timestamp("2025-01-10").date(),
         "created_at": pd.Timestamp("2025-01-11 10:00", tz="UTC"), "total_amount": 200000.0, "status": "confirmed"},
    ])
    engine = _engine_with(db, sales_invoices=df)

    results = get_rule_fn("SAL-004")(engine.conn, cid, None)

    assert [r["evidence"]["invoice_number"] for r in results] == ["LATE"]
    # 18:40 UTC on 31 Mar is already 1 Apr in India.
    engine._register("t", pd.DataFrame({"ts": [pd.Timestamp("2025-03-31 18:40", tz="UTC")]}))
    assert str(engine.conn.execute("SELECT CAST(ts AS DATE) FROM t").fetchone()[0]) == "2025-04-01"


def _dup_sales(n_numbers):
    cid = str(COMPANY_ID)
    rows = []
    for i in range(n_numbers):
        for _ in range(2):
            rows.append({"id": uuid.uuid4().hex, "company_id": cid, "invoice_number": f"D{i}",
                         "total_amount": 1000.0, "status": "confirmed"})
    return pd.DataFrame(rows)


def test_rerun_does_not_duplicate_and_false_positive_stays_suppressed(db):
    rule = _rule(db, "SAL-001")
    engine = _engine_with(db, sales_invoices=_dup_sales(3))

    assert engine._run_rule(rule).exceptions_found == 3
    assert engine._run_rule(rule).exceptions_found == 0

    fp = db.query(AuditException).filter(AuditException.title == "Duplicate Invoice No: D0").one()
    fp.status = "false_positive"
    db.commit()
    assert engine._run_rule(rule).exceptions_found == 0

    closed = db.query(AuditException).filter(AuditException.title == "Duplicate Invoice No: D1").one()
    closed.status = "closed"
    db.commit()
    assert engine._run_rule(rule).exceptions_found == 1   # still in the data -> raised again


def test_same_title_different_key_is_not_merged(db):
    """Dedup is on the rule's key, so two findings sharing a title both survive."""
    rule = _rule(db, "SAL-001")
    engine = _engine_with(db, sales_invoices=_dup_sales(1))
    db.add(AuditException(id=uuid.uuid4(), company_id=COMPANY_ID, rule_id=rule.id,
                          title="Duplicate Invoice No: D0", category="revenue", severity="high",
                          status="open", detected_on=date.today(),
                          supporting_data={"dedup_key": "invoice_number=OTHER"}))
    db.commit()

    assert engine._run_rule(rule).exceptions_found == 1


def test_rule_without_code_fails_instead_of_reporting_clean(db):
    rule = _rule(db, "XXX-999")
    engine = _engine_with(db)

    with pytest.raises(LookupError):
        engine._run_rule(rule)

    execution = db.query(RuleExecution).filter(RuleExecution.rule_id == rule.id).one()
    assert execution.status == "failed"
    assert "No rule code registered" in execution.error_message
