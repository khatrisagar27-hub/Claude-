"""Integration tests for the write paths of /queries and /remediation.

Both creates used to 500 on a NOT NULL column the handler never set
(raised_by_name / responsible_name), and raising a query parked the exception
in a status with no outgoing transitions. These pin the fixed behaviour.
"""
from tests.factories import COMPANY_ID, make_audit_exception


def _query_payload(exc, **overrides):
    payload = {
        "exception_id": str(exc.id),
        "process_area": "Sales",
        "severity": "high",
        "description": "Duplicate invoice INV-1 detected",
        "evidence_summary": "INV-1 appears twice",
        "suggested_question": "Please explain the duplicate INV-1.",
        "due_date": "2026-12-01",
    }
    payload.update(overrides)
    return payload


def test_create_query_records_raiser_and_advances_exception(api):
    user = api.seed_user(role="auditor", full_name="Asha Auditor")
    exc = api.add(make_audit_exception(status="open"))

    resp = api.auth_post("/api/v1/queries", user, json=_query_payload(exc))

    assert resp.status_code == 201
    body = resp.json()
    assert body["query_no"] == "MQ-0001"
    assert body["status"] == "open"
    api.db.refresh(exc)
    assert exc.status == "management_query_sent"


def test_exception_can_move_on_after_query_raised(api):
    user = api.seed_user(role="auditor")
    exc = api.add(make_audit_exception(status="open"))
    api.auth_post("/api/v1/queries", user, json=_query_payload(exc))

    resp = api.auth_patch(f"/api/v1/exceptions/{exc.id}/status", user,
                          json={"status": "resolved", "comment": "Credit note verified"})

    assert resp.status_code == 200


def test_create_query_does_not_reopen_resolved_exception(api):
    user = api.seed_user(role="auditor")
    exc = api.add(make_audit_exception(status="resolved"))

    resp = api.auth_post("/api/v1/queries", user, json=_query_payload(exc))

    assert resp.status_code == 201
    api.db.refresh(exc)
    assert exc.status == "resolved"


def test_create_query_requires_due_date(api):
    user = api.seed_user(role="auditor")
    exc = api.add(make_audit_exception(status="open"))
    payload = _query_payload(exc)
    del payload["due_date"]

    resp = api.auth_post("/api/v1/queries", user, json=payload)

    assert resp.status_code == 422


def test_create_query_forbidden_for_cfo(api):
    user = api.seed_user(role="cfo")
    exc = api.add(make_audit_exception(status="open"))

    resp = api.auth_post("/api/v1/queries", user, json=_query_payload(exc))

    assert resp.status_code == 403


def test_respond_to_query_records_responder(api):
    auditor = api.seed_user(role="auditor")
    exc = api.add(make_audit_exception(status="open"))
    query_id = api.auth_post("/api/v1/queries", auditor, json=_query_payload(exc)).json()["id"]
    mgmt = api.seed_user(role="management", full_name="Client CFO")

    resp = api.auth_post(f"/api/v1/queries/{query_id}/respond", mgmt,
                         json={"response_text": "INV-1 duplicate was cancelled by CN-4."})

    assert resp.status_code == 201
    listed = api.auth_get(f"/api/v1/queries?company_id={COMPANY_ID}", auditor).json()
    assert listed[0]["status"] == "responded"
    detail = api.auth_get(f"/api/v1/queries/{query_id}", auditor).json()
    assert detail["responses"][0]["response_text"] == "INV-1 duplicate was cancelled by CN-4."


def test_create_remediation(api):
    user = api.seed_user(role="manager")
    exc = api.add(make_audit_exception(status="open"))

    resp = api.auth_post("/api/v1/remediation", user, json={
        "company_id": str(COMPANY_ID),
        "exception_id": str(exc.id),
        "control_gap_description": "No system block on duplicate invoice numbers",
        "action_plan": "Enable unique voucher numbering in Tally",
        "responsible_name": "Client Accounts Head",
        "target_date": "2026-12-31",
    })

    assert resp.status_code == 201
    assert resp.json()["action_plan"] == "Enable unique voucher numbering in Tally"


def test_create_remediation_requires_owner_and_target_date(api):
    user = api.seed_user(role="manager")
    exc = api.add(make_audit_exception(status="open"))

    resp = api.auth_post("/api/v1/remediation", user, json={
        "company_id": str(COMPANY_ID),
        "exception_id": str(exc.id),
        "control_gap_description": "gap",
        "action_plan": "plan",
    })

    assert resp.status_code == 422


def test_list_remediation_serialises_rows(api):
    user = api.seed_user(role="manager")
    exc = api.add(make_audit_exception(status="open"))
    api.auth_post("/api/v1/remediation", user, json={
        "company_id": str(COMPANY_ID), "exception_id": str(exc.id),
        "control_gap_description": "gap", "action_plan": "plan",
        "responsible_name": "Owner", "target_date": "2026-12-31",
    })

    resp = api.auth_get(f"/api/v1/remediation?company_id={COMPANY_ID}", user)

    assert resp.status_code == 200
    assert resp.json()[0]["exception_id"] == str(exc.id)
