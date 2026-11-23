"""Integration tests for /exceptions — listing, filtering, and status transitions."""
import uuid

from tests.factories import COMPANY_ID, OTHER_COMPANY_ID, make_audit_exception


def _seed_exceptions(api):
    api.add(make_audit_exception(severity="critical", category="revenue", status="open"))
    api.add(make_audit_exception(severity="high", category="revenue", status="open"))
    api.add(make_audit_exception(severity="low", category="payroll", status="resolved"))
    # belongs to a different company — must never appear
    api.add(make_audit_exception(company_id=OTHER_COMPANY_ID, severity="critical"))


def test_list_is_scoped_to_company(api):
    user = api.seed_user()
    _seed_exceptions(api)

    resp = api.auth_get(f"/api/v1/exceptions?company_id={COMPANY_ID}", user)

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3


def test_list_filters_by_severity(api):
    user = api.seed_user()
    _seed_exceptions(api)

    resp = api.auth_get(f"/api/v1/exceptions?company_id={COMPANY_ID}&severity=critical", user)

    assert resp.json()["total"] == 1


def test_list_paginates(api):
    user = api.seed_user()
    _seed_exceptions(api)

    resp = api.auth_get(f"/api/v1/exceptions?company_id={COMPANY_ID}&page=1&page_size=2", user)

    body = resp.json()
    assert body["total"] == 3        # total reflects the full match set
    assert len(body["items"]) == 2   # page is capped at page_size


def test_get_exception_404_when_missing(api):
    user = api.seed_user()

    resp = api.auth_get(f"/api/v1/exceptions/{uuid.uuid4()}", user)

    assert resp.status_code == 404


def test_status_transition_allowed(api):
    user = api.seed_user(role="auditor")
    exc = api.add(make_audit_exception(status="open"))

    resp = api.auth_patch(f"/api/v1/exceptions/{exc.id}/status", user,
                          json={"status": "in_review"})

    assert resp.status_code == 200
    assert resp.json()["status"] == "in_review"


def test_invalid_status_transition_is_rejected(api):
    user = api.seed_user(role="auditor")
    exc = api.add(make_audit_exception(status="open"))

    # 'open' may not jump straight to 'resolved'
    resp = api.auth_patch(f"/api/v1/exceptions/{exc.id}/status", user,
                          json={"status": "resolved"})

    assert resp.status_code == 400


def test_status_update_forbidden_for_client_user(api):
    user = api.seed_user(role="client_user")
    exc = api.add(make_audit_exception(status="open"))

    resp = api.auth_patch(f"/api/v1/exceptions/{exc.id}/status", user,
                          json={"status": "in_review"})

    assert resp.status_code == 403
