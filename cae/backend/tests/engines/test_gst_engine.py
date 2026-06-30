"""Tests for GSTEngine — GSTR-1/3B/2B vs books reconciliation.

Regression note: these tests originally exposed a bug where the engine queried
columns that do not exist on the ORM models (``taxable_value``, ``cgst``,
``is_cancelled``).  The engine now uses the real columns (``taxable_amount``,
``cgst_amount``, ``status``), and these tests pin that behaviour.
"""
from datetime import date, datetime

import pytest

from app.engines.gst_engine import GSTEngine
from app.models.risk import GSTReconciliation
from tests.factories import COMPANY_ID, make_purchase_invoice, make_sales_invoice

MARCH = date(2024, 3, 15)
FEBRUARY = date(2024, 2, 15)


def _seed_march_books(db):
    """Books for 2024-03: turnover 150,000 and input tax credit 36,000."""
    db.add(make_sales_invoice(invoice_date=MARCH, taxable_amount=100000, status="confirmed"))
    db.add(make_sales_invoice(invoice_date=MARCH, taxable_amount=50000, status="confirmed"))
    # Out-of-scope rows that must be excluded:
    db.add(make_sales_invoice(invoice_date=MARCH, taxable_amount=999999, status="cancelled"))
    db.add(make_sales_invoice(invoice_date=FEBRUARY, taxable_amount=888888, status="confirmed"))

    db.add(make_purchase_invoice(invoice_date=MARCH, cgst_amount=9000, sgst_amount=9000,
                                 itc_eligible=True))
    db.add(make_purchase_invoice(invoice_date=MARCH, igst_amount=18000, itc_eligible=True))
    # ITC-ineligible purchase must be excluded from books_itc.
    db.add(make_purchase_invoice(invoice_date=MARCH, igst_amount=50000, itc_eligible=False))
    db.commit()


def test_books_turnover_and_itc_from_ledger(db):
    _seed_march_books(db)

    result = GSTEngine(db, str(COMPANY_ID)).reconcile(
        "2024-03",
        {"turnover": 150000, "itc_available": 30000, "itc_claimed": 36000},
    )

    assert result["books_turnover"] == 150000      # cancelled + Feb excluded
    assert result["books_itc"] == 36000            # ITC-ineligible excluded


def test_itc_variance_and_risk_amount(db):
    _seed_march_books(db)

    result = GSTEngine(db, str(COMPANY_ID)).reconcile(
        "2024-03",
        {"turnover": 150000, "itc_available": 30000, "itc_claimed": 36000},
    )

    # Turnover matches GSTR-1, so only the ITC gap drives risk.
    assert result["variance_turnover"] == 0
    assert result["variance_itc"] == 6000          # |36,000 books - 30,000 GSTR-2B|
    assert result["risk_amount"] == pytest.approx(6000.0)


def test_turnover_variance_contributes_18pct_to_risk(db):
    _seed_march_books(db)

    result = GSTEngine(db, str(COMPANY_ID)).reconcile(
        "2024-03",
        {"turnover": 200000, "itc_available": 36000, "itc_claimed": 36000},
    )

    assert result["variance_turnover"] == 50000
    assert result["variance_itc"] == 0
    # risk = 50,000 * 0.18 + 0
    assert result["risk_amount"] == pytest.approx(9000.0)


def test_reconcile_persists_and_upserts(db):
    _seed_march_books(db)
    engine = GSTEngine(db, str(COMPANY_ID))

    engine.reconcile("2024-03", {"turnover": 150000, "itc_available": 30000, "itc_claimed": 36000})
    engine.reconcile("2024-03", {"turnover": 150000, "itc_available": 31000, "itc_claimed": 36000})

    rows = db.query(GSTReconciliation).all()
    assert len(rows) == 1                          # second run updates the same period
    assert float(rows[0].gstr2b_itc) == 31000
    assert rows[0].status == "reconciled"


def test_next_month_rolls_over_december():
    assert GSTEngine._next_month(2024, 12) == datetime(2025, 1, 1)
    assert GSTEngine._next_month(2024, 3) == datetime(2024, 4, 1)
