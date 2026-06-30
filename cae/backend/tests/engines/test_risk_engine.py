"""Tests for RiskEngine — composite risk scoring and banding."""
from datetime import date

import pytest

from app.engines.risk_engine import BUSINESS_AREAS, RiskEngine, _risk_band
from app.models.risk import RiskScore
from tests.factories import COMPANY_ID, make_audit_exception


# Old enough (factory default 2024-03-15) that detected_on is > 30 days ago,
# so it never counts toward the "recent" frequency multiplier.
OLD = date(2024, 3, 15)


@pytest.mark.parametrize(
    "score,expected_band",
    [
        (0, "low"),
        (20, "low"),
        (21, "moderate"),
        (50, "moderate"),
        (51, "high"),
        (80, "high"),
        (81, "critical"),
        (150, "critical"),
    ],
)
def test_risk_band_boundaries(score, expected_band):
    assert _risk_band(score) == expected_band


def test_no_exceptions_defaults_every_area_to_low(db):
    engine = RiskEngine(db, str(COMPANY_ID))

    written = engine.compute_and_store()

    assert written == len(BUSINESS_AREAS)
    rows = {r.entity_name: r for r in db.query(RiskScore).all()}
    assert set(rows) == set(BUSINESS_AREAS)
    for row in rows.values():
        assert row.risk_band == "low"
        assert float(row.composite_score) == 1.0


def test_composite_score_matches_formula(db):
    """revenue: one critical + one medium exception, low materiality, not recent.

    avg_severity     = (5 + 3) / 2 = 4
    max_severity     = 5
    materiality      = clamp(2,000,000 / 10,000,000, 0.5, 2.0) = 0.5
    frequency        = 1.0 (nothing detected in the last 30 days)
    control_weakness = 1 critical / 2 = 0.5
    composite        = 4 * 5 * 0.5 * 1.0 * (1 + 0.5) = 15.0  -> band "low"
    """
    db.add(make_audit_exception(category="revenue", severity="critical",
                                financial_impact=1_000_000, detected_on=OLD))
    db.add(make_audit_exception(category="revenue", severity="medium",
                                financial_impact=1_000_000, detected_on=OLD))
    db.commit()

    engine = RiskEngine(db, str(COMPANY_ID))
    engine.compute_and_store()

    revenue = db.query(RiskScore).filter(RiskScore.entity_name == "revenue").one()
    assert float(revenue.composite_score) == 15.0
    assert revenue.risk_band == "low"
    assert float(revenue.impact) == 5.0
    assert float(revenue.likelihood) == 4.0


def test_composite_score_capped_at_100(db):
    """Many recent critical, highly material exceptions saturate the score at 100."""
    for _ in range(5):
        db.add(make_audit_exception(category="revenue", severity="critical",
                                    financial_impact=50_000_000, detected_on=date.today()))
    db.commit()

    RiskEngine(db, str(COMPANY_ID)).compute_and_store()

    revenue = db.query(RiskScore).filter(RiskScore.entity_name == "revenue").one()
    assert float(revenue.composite_score) == 100.0
    assert revenue.risk_band == "critical"


def test_only_open_exceptions_count(db):
    """Resolved/closed exceptions are excluded; an all-closed area stays low."""
    db.add(make_audit_exception(category="payroll", severity="critical",
                                financial_impact=9_000_000, status="closed"))
    db.commit()

    RiskEngine(db, str(COMPANY_ID)).compute_and_store()

    payroll = db.query(RiskScore).filter(RiskScore.entity_name == "payroll").one()
    assert payroll.risk_band == "low"
    assert float(payroll.composite_score) == 1.0


def test_exceptions_for_other_company_are_ignored(db):
    """Tenant isolation: another company's exceptions must not affect our scores."""
    from tests.factories import OTHER_COMPANY_ID

    db.add(make_audit_exception(company_id=OTHER_COMPANY_ID, category="revenue",
                                severity="critical", financial_impact=50_000_000,
                                detected_on=date.today()))
    db.commit()

    RiskEngine(db, str(COMPANY_ID)).compute_and_store()

    revenue = db.query(RiskScore).filter(RiskScore.entity_name == "revenue").one()
    assert revenue.risk_band == "low"
