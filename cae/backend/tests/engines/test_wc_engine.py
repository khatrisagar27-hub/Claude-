"""Tests for WorkingCapitalEngine — DSO/DPO/DIO, cash-conversion cycle, stress score."""
from datetime import date, timedelta

import pytest

from app.engines.wc_engine import WorkingCapitalEngine
from app.models.risk import WorkingCapitalMetric
from tests.factories import (
    COMPANY_ID,
    make_inventory_movement,
    make_purchase_invoice,
    make_sales_invoice,
)

TODAY = date.today()
REF = TODAY - timedelta(days=10)          # latest sale: the engine's as-at date
YEAR_START = REF - timedelta(days=364)    # first day of the 365-day window
OVERDUE = REF - timedelta(days=5)         # due date already passed on the as-at date


def _seed_known_scenario(db):
    """Seed a deterministic book so DSO=30, DPO=20, DIO=45, CCC=55 (days).

    Window = 365 days to REF (the books start on its first day).
    sales      365,000 -> 1,000 a day; open receivables 30,000 -> DSO 30
    purchases  365,000 -> 1,000 a day; open payables    20,000 -> DPO 20
    goods issued 365,000 at cost; stock on hand 45,000          -> DIO 45
    """
    db.add(make_sales_invoice(invoice_date=YEAR_START, total_amount=335000, status="paid", outstanding_amount=0))
    for _ in range(3):
        db.add(make_sales_invoice(invoice_date=REF, total_amount=10000, status="confirmed",
                                  due_date=OVERDUE, outstanding_amount=10000))
    db.add(make_purchase_invoice(invoice_date=YEAR_START, total_amount=345000, status="paid", outstanding_amount=0))
    for _ in range(2):
        db.add(make_purchase_invoice(invoice_date=REF, total_amount=10000, status="approved",
                                     due_date=OVERDUE, outstanding_amount=10000))
    db.add(make_inventory_movement(item_code="ITEM-1", movement_date=YEAR_START, total_value=410000))
    db.add(make_inventory_movement(item_code="ITEM-1", movement_date=REF, movement_type="goods_issue",
                                   total_value=365000))
    db.commit()


def test_metrics_match_hand_computed_values(db):
    _seed_known_scenario(db)

    metrics = WorkingCapitalEngine(db, str(COMPANY_ID)).compute_and_store()

    assert metrics["as_of"] == REF.isoformat() and metrics["days_in_period"] == 365
    assert metrics["dso"] == 30.0
    assert metrics["dpo"] == 20.0
    assert metrics["dio"] == 45.0
    assert metrics["ccc"] == 55.0
    # Weighted signals: receivables overdue 100% x 0.20 + DSO 30/180 x 0.20
    # + payables overdue 100% x 0.15 + CCC 55/180 x 0.15 = 42.9 out of 100
    assert metrics["wc_stress_score"] == 42.9


def test_compute_and_store_persists_one_row(db):
    _seed_known_scenario(db)

    WorkingCapitalEngine(db, str(COMPANY_ID)).compute_and_store()

    rows = db.query(WorkingCapitalMetric).all()
    assert len(rows) == 1
    assert float(rows[0].dso) == 30.0
    assert rows[0].metric_date == TODAY


def test_idempotent_for_same_day_updates_in_place(db):
    """A second run on the same day must update, not duplicate, the metric row."""
    _seed_known_scenario(db)
    engine = WorkingCapitalEngine(db, str(COMPANY_ID))

    engine.compute_and_store()
    engine.compute_and_store()

    assert db.query(WorkingCapitalMetric).count() == 1


def test_no_data_yields_zeroed_metrics_without_dividing_by_zero(db):
    """Empty books must not raise ZeroDivisionError; all ratios fall back to 0."""
    metrics = WorkingCapitalEngine(db, str(COMPANY_ID)).compute_and_store()

    assert metrics["dso"] == 0
    assert metrics["dpo"] == 0
    assert metrics["dio"] == 0
    assert metrics["wc_stress_score"] == 0.0


def test_stress_score_is_clamped_to_100():
    """Every warning sign saturated: the stress score stops at 100."""
    ar = {"total": 100.0, "overdue": 100.0, "aging": {"d90_plus": 100.0}}
    ap = {"total": 100.0, "overdue": 100.0}
    score, parts = WorkingCapitalEngine._stress_score(ar, ap, dso=5000, ccc=5000)
    assert score == 100.0 and parts["dso_vs_180"] == 100.0


def test_cancelled_sales_excluded_from_turnover(db):
    """Cancelled invoices must not inflate average daily sales."""
    db.add(make_sales_invoice(invoice_date=REF, total_amount=90000, status="confirmed",
                              due_date=TODAY + timedelta(days=30), outstanding_amount=0))
    db.add(make_sales_invoice(invoice_date=REF, total_amount=900000, status="cancelled",
                              due_date=TODAY + timedelta(days=30), outstanding_amount=0))
    db.commit()

    metrics = WorkingCapitalEngine(db, str(COMPANY_ID)).compute_and_store()

    # Only the 90,000 confirmed invoice counts; nothing is outstanding, so DSO is 0
    # and the cancelled invoice is ignored entirely.
    assert metrics["dso"] == 0.0
