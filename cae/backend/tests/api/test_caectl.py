"""Tests for scripts/caectl.py — the tool layer the audit-fieldwork agents use.

caectl computes every figure, band, due date and default route the agents act
on, and it enforces the autonomy boundary (what may reach the client without the
partner). Both are pinned here. Integration tests drive it through the real
FastAPI app via a TestClient-backed transport.
"""
import json
import sys
import uuid
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app.models.audit import AuditRule
from tests.factories import COMPANY_ID, OTHER_COMPANY_ID, make_audit_exception

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
import caectl  # noqa: E402

AS_OF = date(2026, 11, 18)
PASSWORD = "S3cret-pass"

ENG = {
    "company_id": str(COMPANY_ID), "client_name": "Acme Pvt Ltd", "period_label": "FY 2025-26",
    "overall_materiality": 5000000, "performance_materiality": 3750000, "clearly_trivial": 250000,
    "query_response_days": 7, "remediation_target_days": 30, "recurrence_threshold": 3,
    "remediation_owner": "Head of Accounts",
    "partner": {"name": "Partner", "email": "partner@firm.example"},
    "management_contacts": [{"name": "CFO", "email": "cfo@client.example"}],
}


# --------------------------------------------------------------------------- #
# Pure functions
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("value,expected", [
    (0, "₹0.00"), (999, "₹999.00"), (1000, "₹1,000.00"), (100000, "₹1,00,000.00"),
    ("1234567.891", "₹12,34,567.89"), (-150000, "-₹1,50,000.00"), (None, None),
])
def test_inr_uses_indian_grouping(value, expected):
    assert caectl.inr(value) == expected


@pytest.mark.parametrize("impact,band", [
    (None, "no_amount"),
    (Decimal("250000"), "clearly_trivial"),
    (Decimal("250000.01"), "above_clearly_trivial"),
    (Decimal("3750000"), "above_performance_materiality"),
    (Decimal("-5000000"), "above_overall_materiality"),
])
def test_band_boundaries(impact, band):
    assert caectl.band_for(impact, ENG) == band


def _q(status="open", days_overdue=0, reminder_due=True, reminders_sent=0):
    return {"status": status, "days_overdue": days_overdue, "reminder_due": reminder_due,
            "reminders_sent": reminders_sent, "max_reminders": 3}


def _route(**kw):
    base = dict(status="open", severity="high", band="above_clearly_trivial", fraud=False,
                queries=[], escalation=None, batch=None, resolution=None)
    base.update(kw)
    return caectl.ROUTES[caectl.route_for(**base)][0]


def test_route_table():
    assert _route() == "query"
    assert _route(status="false_positive") == "none"
    assert _route(fraud=True, band="clearly_trivial", severity="low") == "escalate"
    assert _route(severity="critical") == "escalate"
    assert _route(band="above_performance_materiality") == "escalate"
    assert _route(band="clearly_trivial", severity="medium") == "close_trivial"
    assert _route(band="clearly_trivial", severity="high") == "query"
    assert _route(fraud=True, escalation={"status": "pending"}) == "await_partner"
    assert _route(fraud=True, escalation={"status": "approved"}) == "query"
    assert _route(fraud=True, escalation={"status": "rejected"}) == "hold"
    assert _route(batch={"status": "pending"}) == "await_partner"
    assert _route(batch={"status": "approved"}) == "release"
    assert _route(queries=[_q("responded")]) == "review_response"
    assert _route(queries=[_q("responded")], resolution={"status": "pending"}) == "await_partner"
    assert _route(queries=[_q("responded")], resolution={"status": "approved"}) == "resolve"
    assert _route(queries=[_q(days_overdue=2)]) == "chase"
    assert _route(queries=[_q(days_overdue=2, reminder_due=False)]) == "wait"
    assert _route(queries=[_q(days_overdue=9, reminders_sent=3)]) == "report_nonresponse"
    assert _route(queries=[_q()]) == "wait"


def _write_eng(tmp_path, **overrides):
    path = tmp_path / "engagement.json"
    path.write_text(json.dumps({**ENG, **overrides}))
    return path


def test_engagement_validation(tmp_path):
    with pytest.raises(caectl.CaeError, match="thresholds"):
        caectl.load_engagement(_write_eng(tmp_path, clearly_trivial=4000000))
    with pytest.raises(caectl.CaeError, match="performance_materiality"):
        caectl.load_engagement(_write_eng(tmp_path, performance_materiality=None))
    with pytest.raises(caectl.CaeError, match="email"):
        caectl.load_engagement(_write_eng(tmp_path, management_contacts=[{"name": "x"}]))
    eng = caectl.load_engagement(_write_eng(tmp_path))
    assert eng["max_reminders"] == 3 and eng["auto_send_reminders"] is True


def test_figure_check():
    allowed = caectl.figures_in({"a": "₹1,18,000.00", "evidence": {"amount": 59000.5}, "n": 7})
    assert caectl.unverified_figures("Invoice of Rs. 118000 and ₹59,000.50", allowed) == []
    assert caectl.unverified_figures("about ₹1,20,000", allowed) == ["₹1,20,000"]
    assert caectl.unverified_figures("roughly 1.2 lakh", allowed) == ["1.2 lakh"]
    # Bare numbers (dates, invoice numbers) are not amounts.
    assert caectl.unverified_figures("INV-4417 dated 15-03-2024", allowed) == []


# --------------------------------------------------------------------------- #
# Through the real API
# --------------------------------------------------------------------------- #

def _transport(client):
    def transport(method, url, headers, body):
        resp = client.request(method, url, headers=headers, content=body)
        return resp.status_code, resp.content
    return transport


@pytest.fixture
def cae(api):
    user = api.seed_user(role="manager", email="agent@example.com")
    client = caectl.Cae("http://testserver/api/v1", transport=_transport(api.client))
    client.login(user.email, PASSWORD)
    return client


@pytest.fixture
def eng(tmp_path):
    return caectl.load_engagement(_write_eng(tmp_path))


class Outbox:
    def __init__(self):
        self.sent = []

    def __call__(self, msg):
        self.sent.append(msg)


def _rule(api, code, risk_area, severity="high"):
    return api.add(AuditRule(
        id=uuid.uuid4(), company_id=COMPANY_ID, rule_code=code, rule_name=f"Rule {code}",
        category="revenue", severity=severity, risk_area=risk_area, rule_type="sql",
        run_frequency="daily", is_active=True, auto_raise_exception=True, requires_approval=False,
    ))


def _brief(cae, eng, as_of=AS_OF):
    return caectl.fetch_brief(cae, eng, as_of, with_risk=False)


def _route_of(cae, eng, exc, as_of=AS_OF):
    return caectl._item(_brief(cae, eng, as_of), str(exc.id))["route"]


def _queries_file(tmp_path, *excs, **overrides):
    q = [{"exception_id": str(e.id), "observation": "Invoice INV-1 is recorded twice.",
          "question": "Please explain why INV-1 appears twice.", "documents": ["Copy of INV-1"], **overrides}
         for e in excs]
    path = tmp_path / "queries.json"
    path.write_text(json.dumps({"queries": q}))
    return path


def _released_query(api, cae, eng, tmp_path, exc, as_of=AS_OF):
    """Draft, approve and release one query; return the raised query no."""
    draft = caectl.draft_queries(cae, eng, _queries_file(tmp_path, exc), as_of)
    caectl.decide_approval(eng, draft["approval_id"], "approve", None, as_of)
    return caectl.release_batch(cae, eng, draft["approval_id"], as_of, Outbox())


def test_login_failure_is_reported(api):
    client = caectl.Cae("http://testserver/api/v1", transport=_transport(api.client))
    with pytest.raises(caectl.CaeError) as err:
        client.login("nobody@example.com", "wrong")
    assert err.value.status == 401


def test_brief_routes_and_figures(api, cae, eng):
    fraud_rule = _rule(api, "SAL-001", "Fraud", "critical")
    plain_rule = _rule(api, "SAL-005", "Revenue Leakage")
    fraud = api.add(make_audit_exception(rule_id=fraud_rule.id, severity="critical", financial_impact=125000))
    trivial = api.add(make_audit_exception(rule_id=plain_rule.id, severity="medium", financial_impact=1000))
    normal = api.add(make_audit_exception(rule_id=plain_rule.id, severity="high", financial_impact=1234567.89))
    api.add(make_audit_exception(company_id=OTHER_COMPANY_ID, rule_id=plain_rule.id))

    brief = _brief(cae, eng)

    by_id = {it["exception_id"]: it for it in brief["exceptions"]}
    assert len(by_id) == 3
    assert by_id[str(fraud.id)]["route"] == "escalate"
    assert by_id[str(fraud.id)]["partner_sign_off_required"] is True
    assert any("SA 240" in ref for ref in by_id[str(fraud.id)]["statutory_refs"])
    assert by_id[str(trivial.id)]["route"] == "close_trivial"
    assert by_id[str(normal.id)]["route"] == "query"
    assert by_id[str(normal.id)]["financial_impact_inr"] == "₹12,34,567.89"
    assert brief["summary"]["open_impact_inr"] == "₹13,60,567.89"
    assert brief["summary"]["open_impact_at_or_above_performance_materiality"] is False
    assert brief["thresholds"]["query_due_date_if_released_today"] == "2026-11-25"
    assert brief["control_deficiency_candidates"] == []


def test_draft_queries_rejects_invented_figures_and_wrong_route(api, cae, eng, tmp_path):
    normal = api.add(make_audit_exception(financial_impact=118000))
    critical = api.add(make_audit_exception(severity="critical"))

    with pytest.raises(caectl.CaeError, match="amounts not in the brief"):
        caectl.draft_queries(cae, eng, _queries_file(tmp_path, normal, observation="Short by ₹5,000."), AS_OF)
    with pytest.raises(caectl.CaeError, match="route is escalate.*cannot be queried"):
        caectl.draft_queries(cae, eng, _queries_file(tmp_path, critical), AS_OF)
    foreign = api.add(make_audit_exception(company_id=OTHER_COMPANY_ID))
    with pytest.raises(caectl.CaeError, match="not in this engagement"):
        caectl.draft_queries(cae, eng, _queries_file(tmp_path, foreign), AS_OF)

    trivial = api.add(make_audit_exception(severity="low", financial_impact=500))
    raised = caectl.draft_queries(cae, eng, _queries_file(tmp_path, trivial), AS_OF)  # upward override allowed
    assert raised["approval_id"]

    ok = caectl.draft_queries(cae, eng, _queries_file(tmp_path, normal, observation="Booked at ₹1,18,000."), AS_OF)

    assert Path(ok["preview"]).exists()
    assert "₹1,18,000.00" in ok["summary"]
    assert _route_of(cae, eng, normal) == "await_partner"


def test_release_needs_approval_then_raises_and_sends(api, cae, eng, tmp_path):
    exc = api.add(make_audit_exception(financial_impact=118000))
    draft = caectl.draft_queries(cae, eng, _queries_file(tmp_path, exc), AS_OF)

    with pytest.raises(caectl.CaeError, match="pending"):
        caectl.release_batch(cae, eng, draft["approval_id"], AS_OF, Outbox())

    caectl.decide_approval(eng, draft["approval_id"], "approve", None, AS_OF)
    assert _route_of(cae, eng, exc) == "release"
    outbox = Outbox()
    result = caectl.release_batch(cae, eng, draft["approval_id"], AS_OF, outbox)

    assert result["sent"] is True and result["queries_raised"] == ["MQ-0001"]
    body = outbox.sent[0].get_content()
    assert "MQ-0001" in body and "₹1,18,000.00" in body and "25 Nov 2026" in body
    assert outbox.sent[0]["To"] == "CFO <cfo@client.example>"
    assert _route_of(cae, eng, exc) == "wait"
    with pytest.raises(caectl.CaeError, match="done"):
        caectl.release_batch(cae, eng, draft["approval_id"], AS_OF, Outbox())


def test_release_without_smtp_stages_email_for_partner(api, cae, eng, tmp_path):
    exc = api.add(make_audit_exception())
    draft = caectl.draft_queries(cae, eng, _queries_file(tmp_path, exc), AS_OF)
    caectl.decide_approval(eng, draft["approval_id"], "approve", None, AS_OF)

    result = caectl.release_batch(cae, eng, draft["approval_id"], AS_OF, None)

    assert result["sent"] is False
    assert "/outbox/ready/" in result["file"] and result["action_for_partner"]


def test_reminders_are_figure_free_rate_limited_and_capped(api, cae, eng, tmp_path):
    exc = api.add(make_audit_exception(financial_impact=118000))
    _released_query(api, cae, eng, tmp_path, exc, as_of=date(2026, 11, 1))
    day = date(2026, 11, 9)  # due 8 Nov
    assert _route_of(cae, eng, exc, day) == "chase"

    outbox = Outbox()
    first = caectl.remind(cae, eng, day, outbox)
    assert first["reminders"] == 1 and first["sent"] is True
    body = outbox.sent[0].get_content()
    assert "MQ-0001" in body and "₹" not in body
    assert caectl.remind(cae, eng, day + timedelta(days=1), outbox)["reminders"] == 0

    caectl.remind(cae, eng, day + timedelta(days=3), outbox)
    caectl.remind(cae, eng, day + timedelta(days=6), outbox)
    assert len(outbox.sent) == 3
    assert _route_of(cae, eng, exc, day + timedelta(days=9)) == "report_nonresponse"
    assert caectl.remind(cae, eng, day + timedelta(days=9), outbox)["reminders"] == 0


def _respond(api, query_no):
    from app.models.workflow import ManagementQuery
    q = api.db.query(ManagementQuery).filter_by(query_no=query_no).one()
    mgmt = api.seed_user(role="management")
    api.auth_post(f"/api/v1/queries/{q.id}/respond", mgmt, json={"response_text": "Cancelled by CN-4"})
    return str(q.id)


def test_routine_response_is_resolved_directly(api, cae, eng, tmp_path):
    exc = api.add(make_audit_exception(financial_impact=118000))
    query_id = _respond(api, _released_query(api, cae, eng, tmp_path, exc)["queries_raised"][0])
    item = caectl._item(_brief(cae, eng), str(exc.id))
    assert item["route"] == "review_response"
    assert item["queries"][0]["responses"][0]["text"] == "Cancelled by CN-4"

    result = caectl.resolve_query(cae, eng, query_id, "CN-4 verified against ledger", AS_OF)

    assert result["applied"]["status"] == "resolved"
    assert _route_of(cae, eng, exc) == "none"


def test_serious_resolution_needs_partner(api, cae, eng, tmp_path):
    rule = _rule(api, "PUR-022", "Fraud", "critical")
    exc = api.add(make_audit_exception(rule_id=rule.id, severity="critical"))
    esc = caectl.escalate(cae, eng, str(exc.id), "Vendor address matches employee", AS_OF)
    assert _route_of(cae, eng, exc) == "await_partner"
    caectl.decide_approval(eng, esc["approval_id"], "approve", "Query management", AS_OF)
    assert _route_of(cae, eng, exc) == "query"
    query_id = _respond(api, _released_query(api, cae, eng, tmp_path, exc)["queries_raised"][0])

    queued = caectl.resolve_query(cae, eng, query_id, "Address is a shared co-working space", AS_OF)
    assert "queued_for_partner" in queued
    assert _route_of(cae, eng, exc) == "await_partner"
    with pytest.raises(caectl.CaeError, match="awaiting partner"):
        caectl.resolve_query(cae, eng, query_id, None, AS_OF)

    caectl.decide_approval(eng, queued["queued_for_partner"], "approve", None, AS_OF)
    assert _route_of(cae, eng, exc) == "resolve"
    applied = caectl.resolve_query(cae, eng, query_id, None, AS_OF)

    assert applied["comment"] == "Address is a shared co-working space"
    assert _route_of(cae, eng, exc) == "none"
    assert caectl.load_state(eng)["approvals"][queued["queued_for_partner"]]["status"] == "done"


def test_false_positive_routine_vs_serious(api, cae, eng):
    routine = api.add(make_audit_exception())
    serious = api.add(make_audit_exception(financial_impact=4000000))

    assert caectl.false_positive(cae, eng, str(routine.id), "Pair is invoice + credit note", AS_OF)["applied"]["status"] == "false_positive"
    assert "queued_for_partner" in caectl.false_positive(cae, eng, str(serious.id), "Reversal pair", AS_OF)


def test_close_trivial_is_guarded_by_code(api, cae, eng):
    big = api.add(make_audit_exception(severity="medium", financial_impact=300000))
    critical = api.add(make_audit_exception(severity="critical", financial_impact=10))
    small = api.add(make_audit_exception(severity="low", financial_impact=250000))

    with pytest.raises(caectl.CaeError, match="refusing"):
        caectl.close_trivial(cae, eng, str(big.id), AS_OF)
    with pytest.raises(caectl.CaeError, match="refusing"):
        caectl.close_trivial(cae, eng, str(critical.id), AS_OF)
    assert caectl.close_trivial(cae, eng, str(small.id), AS_OF)["status"] == "closed"

    api.db.refresh(small)
    assert "₹2,50,000.00" in small.resolution_notes and "SA 450" in small.resolution_notes


def test_recurring_rule_becomes_deficiency_until_remediated(api, cae, eng):
    rule = _rule(api, "JE-001", "Financial Reporting")
    excs = [api.add(make_audit_exception(rule_id=rule.id, financial_impact=amt)) for amt in (10, 500, 20)]

    cands = _brief(cae, eng)["control_deficiency_candidates"]
    assert len(cands) == 1
    assert cands[0]["occurrences"] == 3 and cands[0]["total_impact_inr"] == "₹530.00"
    assert cands[0]["anchor_exception_id"] == str(excs[1].id)
    assert any("143(3)(i)" in r for r in cands[0]["statutory_refs"])

    r = caectl.remediate(cae, eng, str(excs[1].id), gap="g", plan="p", root_cause=None, today=AS_OF)
    assert r["target_date"] == "2026-12-18"
    assert _brief(cae, eng)["control_deficiency_candidates"] == []


def test_ingest_uploads_recognised_files(api, cae, eng, monkeypatch, tmp_path):
    from app.config import settings
    import app.workers.tasks as tasks
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(tasks.process_uploaded_file, "delay", lambda *a, **k: None)
    inbox = Path(eng["_dir"]) / "inbox"
    inbox.mkdir()
    (inbox / "sales_invoices_oct.csv").write_text("invoice_number,amount\nINV-1,100\n")
    (inbox / "notes.txt").write_text("not data")

    result = caectl.ingest(cae, eng, AS_OF)

    assert [u["file_type"] for u in result["uploaded"]] == ["sales_invoices"]
    assert result["skipped"] == ["notes.txt"]
    assert (inbox / "loaded" / "2026-11-18" / "sales_invoices_oct.csv").exists()


def test_cli_wiring(api, cae, tmp_path, capsys):
    path = _write_eng(tmp_path)
    exc = api.add(make_audit_exception(financial_impact=118000))
    qfile = _queries_file(tmp_path, exc)

    def cli(*argv, mailer=None):
        args = caectl.build_parser().parse_args(["-e", str(path), "--as-of", "2026-11-18", *argv])
        return caectl.run(args, cae_factory=lambda a: cae, mailer_factory=lambda: mailer)

    assert cli("brief")["summary"]["open_exceptions"] == 1
    aid = cli("draft-queries", str(qfile))["approval_id"]
    assert [a["id"] for a in cli("approvals", "--status", "pending")] == [aid]
    cli("approval-decide", aid, "approve", "--note", "ok")
    assert cli("release", aid, mailer=Outbox())["sent"] is True

    digest = tmp_path / "digest.md"
    digest.write_text("Open impact ₹1,18,000.00; ITC at risk ₹9,99,999.00")
    assert cli("verify-figures", str(digest))["unverified"] == ["₹9,99,999.00"]
    outbox = Outbox()
    assert cli("send-digest", str(digest), mailer=outbox)["sent"] is True
    assert outbox.sent[0]["To"] == "Partner <partner@firm.example>"
    assert cli("send-digest", str(digest))["sent"] is False
