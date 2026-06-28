"""Integration tests for /dashboard KPIs and top-exceptions."""
from tests.factories import COMPANY_ID, make_audit_exception


def test_kpis_count_exceptions_by_severity(api):
    user = api.seed_user()
    api.add(make_audit_exception(severity="critical", status="open"))
    api.add(make_audit_exception(severity="critical", status="open"))
    api.add(make_audit_exception(severity="high", status="open"))
    api.add(make_audit_exception(severity="low", status="open"))

    resp = api.auth_get(f"/api/v1/dashboard/kpis?company_id={COMPANY_ID}", user)

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_exceptions"] == 4
    assert body["critical"] == 2
    assert body["high"] == 1
    assert body["low"] == 1
    # nothing seeded for these -> sensible defaults
    assert body["fraud_indicators"] == 0
    assert body["gst_risk_amount"] == 0.0
    assert body["risk_band"] == "low"


def test_kpis_empty_company_returns_zeroes(api):
    user = api.seed_user()

    resp = api.auth_get(f"/api/v1/dashboard/kpis?company_id={COMPANY_ID}", user)

    body = resp.json()
    assert body["total_exceptions"] == 0
    assert body["composite_risk_score"] == 0.0


def test_top_exceptions_orders_by_financial_impact(api):
    user = api.seed_user()
    api.add(make_audit_exception(title="Small", financial_impact=1000, status="open"))
    api.add(make_audit_exception(title="Huge", financial_impact=9_000_000, status="open"))
    api.add(make_audit_exception(title="Medium", financial_impact=50_000, status="open"))

    resp = api.auth_get(f"/api/v1/dashboard/top-exceptions?company_id={COMPANY_ID}&limit=2", user)

    assert resp.status_code == 200
    titles = [e["title"] for e in resp.json()]
    assert titles == ["Huge", "Medium"]


def test_dashboard_requires_authentication(api):
    resp = api.client.get(f"/api/v1/dashboard/kpis?company_id={COMPANY_ID}")
    assert resp.status_code == 403
