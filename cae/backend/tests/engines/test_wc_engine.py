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
RECENT = TODAY - timedelta(days=10)   # inside the 90-day window
OVERDUE = TODAY - timedelta(days=5)   # due date already passed


def _seed_known_scenario(db):
    """Seed a deterministic book so DSO=30, DPO=20, DIO=45, CCC=55.

    avg_daily_sales      = 90,000 / 90 = 1,000
    overdue_receivables  = 30,000  -> DSO = 30
    avg_daily_purchases  = 90,000 / 90 = 1,000
    overdue_payables     = 20,000  -> DPO = 20
    inventory_value      = 1,35,000 received - 90,000 issued = 45,000
    avg_daily_issues     = 90,000 / 90 = 1,000  -> DIO = 45
    """
    # 9 sales invoices of 10,000 each (turnover 90,000). 3 are overdue & unpaid.
    for i in range(9):
        overdue = i < 3
        db.add(
            make_sales_invoice(
                invoice_date=RECENT,
                total_amount=10000,
                status="confirmed",
                due_date=OVERDUE if overdue else TODAY + timedelta(days=30),
                outstanding_amount=10000 if overdue else 0,
            )
        )
    # 9 purchase invoices of 10,000 each (90,000). 2 are overdue & unpaid.
    for i in range(9):
        overdue = i < 2
        db.add(
            make_purchase_invoice(
                invoice_date=RECENT,
                total_amount=10000,
                status="approved",
                due_date=OVERDUE if overdue else TODAY + timedelta(days=30),
                outstanding_amount=10000 if overdue else 0,
            )
        )
    # Closing stock 45,000 at cost; 90,000 issued in the window.
    db.add(make_inventory_movement(total_value=135000))
    db.add(make_inventory_movement(movement_type="goods_issue", total_value=90000, movement_date=RECENT))
    db.commit()


def test_metrics_match_hand_computed_values(db):
    _seed_known_scenario(db)

    metrics = WorkingCapitalEngine(db, str(COMPANY_ID)).compute_and_store()

    assert metrics["dso"] == 30.0
    assert metrics["dpo"] == 20.0
    assert metrics["dio"] == 45.0
    assert metrics["ccc"] == 55.0
    # CCC / 180 * 100 = 30.555... -> rounded to 1 dp
    assert metrics["wc_stress_score"] == 30.6


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


def test_stress_score_is_clamped_to_100(db):
    """A pathological cash-conversion cycle saturates the stress score at 100."""
    # Tiny sales -> tiny avg_daily_sales -> enormous DSO/DIO -> CCC well over 180.
    db.add(
        make_sales_invoice(
            invoice_date=RECENT,
            total_amount=100,
            status="confirmed",
            due_date=OVERDUE,
            outstanding_amount=1_000_000,
        )
    )
    db.commit()

    metrics = WorkingCapitalEngine(db, str(COMPANY_ID)).compute_and_store()

    assert metrics["wc_stress_score"] == 100.0


def test_cancelled_sales_excluded_from_turnover(db):
    """Cancelled invoices must not inflate average daily sales."""
    db.add(make_sales_invoice(invoice_date=RECENT, total_amount=90000, status="confirmed",
                              due_date=TODAY + timedelta(days=30), outstanding_amount=0))
    db.add(make_sales_invoice(invoice_date=RECENT, total_amount=900000, status="cancelled",
                              due_date=TODAY + timedelta(days=30), outstanding_amount=0))
    db.commit()

    metrics = WorkingCapitalEngine(db, str(COMPANY_ID)).compute_and_store()

    # Only the 90,000 confirmed invoice counts: avg_daily_sales = 1,000.
    # No overdue receivables -> DSO 0; the cancelled invoice is ignored entirely.
    assert metrics["dso"] == 0.0


def test_inventory_nets_issues_and_ignores_transfers(db):
    """Gross movements must net to closing stock; a transfer does not change it."""
    db.add(make_inventory_movement(total_value=100000))
    db.add(make_inventory_movement(movement_type="goods_issue", total_value=60000, movement_date=RECENT))
    db.add(make_inventory_movement(movement_type="transfer", total_value=30000))
    db.add(make_inventory_movement(movement_type="adjustment", total_value=-5000))
    db.commit()

    metrics = WorkingCapitalEngine(db, str(COMPANY_ID)).compute_and_store()

    assert metrics["inventory_value"] == 35000


def test_receivables_total_includes_balances_not_yet_due(db):
    db.add(make_sales_invoice(invoice_date=RECENT, total_amount=90000, status="confirmed",
                              due_date=TODAY + timedelta(days=30), outstanding_amount=90000))
    db.commit()

    metrics = WorkingCapitalEngine(db, str(COMPANY_ID)).compute_and_store()

    assert metrics["receivables_total"] == 90000
    assert metrics["receivables_overdue"] == 0
    assert metrics["dso"] == 90.0           # 90,000 / (90,000 / 90)
