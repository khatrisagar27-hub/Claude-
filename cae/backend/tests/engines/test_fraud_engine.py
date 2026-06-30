"""Tests for FraudEngine — Benford, duplicate invoices, round amounts, ML anomaly."""
import pytest

from app.engines.fraud_engine import FraudEngine
from app.models.risk import FraudIndicator
from tests.factories import (
    COMPANY_ID,
    make_journal_entry,
    make_purchase_invoice,
    make_sales_invoice,
)


def _engine(db):
    return FraudEngine(db, str(COMPANY_ID))


# ---------------------------------------------------------------------------
# Benford's Law
# ---------------------------------------------------------------------------
def test_benford_skips_when_too_few_invoices(db):
    """Fewer than 50 invoices is too small a sample — no indicator is produced."""
    for _ in range(49):
        db.add(make_sales_invoice(total_amount=12345))
    db.commit()

    assert _engine(db).benford_analysis() == []


def test_benford_flags_strong_deviation(db):
    """When every amount starts with 9, the leading-digit distribution is wildly
    non-Benford and the chi-square test must raise an indicator."""
    for i in range(80):
        db.add(make_sales_invoice(total_amount=9000 + i))
    db.commit()

    indicators = _engine(db).benford_analysis()

    assert len(indicators) == 1
    assert indicators[0]["indicator_type"] == "benford_deviation"
    assert indicators[0]["details_json"]["p_value"] < 0.05


# ---------------------------------------------------------------------------
# Duplicate invoices
# ---------------------------------------------------------------------------
def test_duplicate_invoices_detected_with_exposure(db):
    """Three identical-amount invoices to one vendor -> exposure = amount * (n-1)."""
    vendor = make_purchase_invoice().vendor_id
    for _ in range(3):
        db.add(make_purchase_invoice(vendor_id=vendor, total_amount=50000))
    db.commit()

    indicators = _engine(db).detect_duplicate_invoices()

    assert len(indicators) == 1
    ind = indicators[0]
    assert ind["indicator_type"] == "duplicate_invoice"
    assert ind["affected_transactions"] == 3
    assert ind["financial_exposure"] == 50000 * 2


def test_no_duplicate_invoices_when_amounts_differ(db):
    vendor = make_purchase_invoice().vendor_id
    for amt in (50000, 60000, 70000):
        db.add(make_purchase_invoice(vendor_id=vendor, total_amount=amt))
    db.commit()

    assert _engine(db).detect_duplicate_invoices() == []


# ---------------------------------------------------------------------------
# Round-amount concentration
# ---------------------------------------------------------------------------
def test_round_amount_concentration_flagged_above_20pct(db):
    """3 round + 7 non-round high-value invoices = 30% round -> indicator."""
    for _ in range(3):
        db.add(make_purchase_invoice(total_amount=200000))   # divisible by 1000
    for _ in range(7):
        db.add(make_purchase_invoice(total_amount=123457))   # not divisible by any threshold
    db.commit()

    indicators = _engine(db).round_amount_analysis()

    assert len(indicators) == 1
    assert indicators[0]["indicator_type"] == "round_amount_concentration"
    assert indicators[0]["affected_transactions"] == 3


def test_round_amount_not_flagged_at_or_below_20pct(db):
    """Only 2 of 10 round = 20%, which is not strictly greater than 20%."""
    for _ in range(2):
        db.add(make_purchase_invoice(total_amount=200000))
    for _ in range(8):
        db.add(make_purchase_invoice(total_amount=123457))
    db.commit()

    assert _engine(db).round_amount_analysis() == []


def test_round_amount_ignores_invoices_below_threshold(db):
    """Round invoices under ₹1L are out of scope for this rule."""
    for _ in range(5):
        db.add(make_purchase_invoice(total_amount=2000))  # round but < 100,000
    db.commit()

    assert _engine(db).round_amount_analysis() == []


# ---------------------------------------------------------------------------
# Behavioural (ML) anomaly
# ---------------------------------------------------------------------------
def test_behavioral_anomaly_skips_small_samples(db):
    for _ in range(29):
        db.add(make_journal_entry(total_debit=1000))
    db.commit()

    assert _engine(db).behavioral_anomaly() == []


def test_behavioral_anomaly_flags_obvious_outlier(db):
    for _ in range(39):
        db.add(make_journal_entry(total_debit=1000))
    db.add(make_journal_entry(total_debit=10_000_000))  # glaring outlier
    db.commit()

    indicators = _engine(db).behavioral_anomaly()

    assert len(indicators) == 1
    assert indicators[0]["indicator_type"] == "ml_anomaly"
    assert indicators[0]["affected_transactions"] >= 1


# ---------------------------------------------------------------------------
# Orchestration & persistence
# ---------------------------------------------------------------------------
def test_run_all_aggregates_indicators(db):
    vendor = make_purchase_invoice().vendor_id
    for _ in range(3):
        db.add(make_purchase_invoice(vendor_id=vendor, total_amount=50000))
    db.commit()

    indicators = _engine(db).run_all()

    assert any(i["indicator_type"] == "duplicate_invoice" for i in indicators)


def test_write_indicators_persists_rows(db):
    engine = _engine(db)
    indicators = [
        {
            "indicator_type": "duplicate_invoice",
            "description": "x",
            "score": 3,
            "affected_transactions": 3,
            "financial_exposure": 100000,
            "details_json": {"count": 3},
        }
    ]

    written = engine.write_indicators(indicators)

    assert written == 1
    assert db.query(FraudIndicator).count() == 1
