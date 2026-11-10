"""API behaviour: who may do what, and that the workflow rules hold."""
import io
from datetime import date

import pandas as pd
import pytest
from openpyxl import load_workbook
from sqlalchemy import delete

from app.db import SessionLocal
from app.demo import gstin, to_xlsx
from app.models import User

CSV = b"invoice_no,invoice_date,vendor_name,taxable_value\nA-1,05-04-2025,Apex,1000\nA-1,05-04-2025,Apex,1000\n"


@pytest.fixture
def engagement(api, manager):
    client = api.post("/api/clients", json={"name": "API Co", "gstin": gstin("27", "AAACP1234P")}, headers=manager).json()
    body = {"client_id": client["id"], "name": "FY 2025-26", "period_start": "2025-04-01", "period_end": "2026-03-31",
            "settings": {"data_as_at": "2026-03-31"}}
    return api.post("/api/engagements", json=body, headers=manager).json()


@pytest.fixture
def finding(api, engagement, staff):
    eid = engagement["id"]
    assert api.post(f"/api/engagements/{eid}/data/purchases", files={"file": ("p.csv", CSV)}, headers=staff).status_code == 200
    assert api.post(f"/api/engagements/{eid}/runs", headers=staff).json()["new"] == 1
    return api.get(f"/api/engagements/{eid}/findings", headers=staff).json()["items"][0]


def test_first_run_setup_then_locked(api):
    with SessionLocal() as db:               # start from an empty user table
        db.execute(delete(User))
        db.commit()
    assert api.get("/api/setup").json() == {"needed": True}
    weak = api.post("/api/setup", json={"email": "p@firm.in", "name": "P", "password": "short"})
    assert weak.status_code == 422
    made = api.post("/api/setup", json={"email": "P@Firm.in", "name": "P", "password": "a-long-passphrase"})
    assert made.status_code == 200 and made.json()["user"]["role"] == "partner" and made.json()["user"]["email"] == "p@firm.in"
    assert api.get("/api/setup").json() == {"needed": False}
    assert api.post("/api/setup", json={"email": "x@firm.in", "name": "X", "password": "a-long-passphrase"}).status_code == 409
    assert api.post("/api/login", json={"email": "p@firm.in", "password": "wrong-password"}).status_code == 401
    token = api.post("/api/login", json={"email": "p@firm.in", "password": "a-long-passphrase"}).json()["token"]
    assert api.get("/api/me", headers={"Authorization": f"Bearer {token}"}).json()["name"] == "P"


def test_everything_except_setup_login_health_needs_a_token(api):
    open_paths = {"/api/setup", "/api/login", "/api/health"}
    for route in api.app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/") or path in open_paths or "openapi" in path or "docs" in path:
            continue
        url = path.replace("{engagement_id}", "1").replace("{finding_id}", "1").replace("{action_id}", "1") \
                  .replace("{user_id}", "1").replace("{dataset}", "sales").replace("{code}", "SAL-001")
        for method in route.methods - {"HEAD", "OPTIONS"}:
            assert api.request(method, url).status_code == 401, f"{method} {path} is reachable without signing in"
    assert api.get("/api/me", headers={"Authorization": "Bearer not-a-token"}).status_code == 401


def test_disabled_user_token_stops_working(api, partner):
    made = api.post("/api/users", json={"email": "temp@test.in", "name": "Temp", "password": "a-long-passphrase", "role": "staff"}, headers=partner).json()
    token = {"Authorization": "Bearer " + api.post("/api/login", json={"email": "temp@test.in", "password": "a-long-passphrase"}).json()["token"]}
    assert api.get("/api/me", headers=token).status_code == 200
    api.patch(f"/api/users/{made['id']}", json={"is_active": False}, headers=partner)
    assert api.get("/api/me", headers=token).status_code == 401
    assert api.post("/api/login", json={"email": "temp@test.in", "password": "a-long-passphrase"}).status_code == 401


def test_role_limits(api, staff, manager, partner):
    assert api.post("/api/clients", json={"name": "X"}, headers=staff).status_code == 403
    assert api.get("/api/users", headers=manager).status_code == 403
    assert api.get("/api/users", headers=partner).status_code == 200
    assert api.post("/api/users", json={"email": "a@b.in", "name": "A", "password": "a-long-passphrase", "role": "owner"}, headers=partner).status_code == 422
    me = api.get("/api/me", headers=partner).json()
    assert api.patch(f"/api/users/{me['id']}", json={"role": "staff"}, headers=partner).status_code == 409


def test_client_identifiers_are_validated(api, manager):
    assert api.post("/api/clients", json={"name": "X", "gstin": "27AAPFU0939F1ZX"}, headers=manager).status_code == 422
    assert api.post("/api/clients", json={"name": "X", "pan": "12345"}, headers=manager).status_code == 422
    bad = {"client_id": 999999, "name": "E", "period_start": "2025-04-01", "period_end": "2026-03-31"}
    assert api.post("/api/engagements", json=bad, headers=manager).status_code == 404


def test_engagement_settings_validated(api, engagement, manager):
    url = f"/api/engagements/{engagement['id']}"
    assert api.patch(url, json={"settings": {"made_up": True}}, headers=manager).status_code == 422
    assert api.patch(url, json={"settings": {"data_as_at": "31/03/2026"}}, headers=manager).status_code == 422
    out = api.patch(url, json={"materiality": 500000, "settings": {"einvoice_applicable": True}}, headers=manager).json()
    assert out["materiality"] == 500000 and out["settings"]["einvoice_applicable"] is True
    assert out["settings"]["data_as_at"] == "2026-03-31"            # other settings are kept


def test_upload_reports_rejections(api, engagement, staff):
    url = f"/api/engagements/{engagement['id']}/data"
    bad = b"invoice_no,invoice_date,vendor_name,taxable_value\nA-1,05-04-2025,Apex,1000\nA-2,bad,Apex,5\n"
    out = api.post(f"{url}/purchases", files={"file": ("p.csv", bad)}, headers=staff).json()
    assert (out["rows_read"], out["rows_loaded"], out["rows_rejected"]) == (2, 1, 1) and out["errors"][0]["row"] == 3
    assert api.post(f"{url}/purchases", files={"file": ("p.exe", b"x")}, headers=staff).status_code == 422
    assert api.post(f"{url}/purchases", files={"file": ("p.xlsx", b"not a workbook")}, headers=staff).status_code == 422
    assert api.post(f"{url}/nonsense", files={"file": ("p.csv", bad)}, headers=staff).status_code == 404
    missing = api.post(f"{url}/sales", files={"file": ("s.csv", b"a,b\n1,2\n")}, headers=staff)
    assert missing.status_code == 422 and "No column headings recognised" in missing.json()["detail"]
    assert api.get(url, headers=staff).json()["counts"]["purchases"] == 1
    template = api.get("/api/datasets/purchases/template", headers=staff)
    assert template.status_code == 200 and load_workbook(io.BytesIO(template.content))["Data"]["A1"].value == "invoice_no"


def test_review_workflow(api, engagement, finding, staff, manager):
    url = f"/api/findings/{finding['id']}"
    assert finding["rule_code"] == "PUR-001" and finding["status"] == "open"
    # staff may raise a query, which moves the finding to queried
    assert api.post(f"{url}/notes", json={"kind": "query", "body": "Please explain."}, headers=staff).json()["status"] == "queried"
    assert api.post(f"{url}/notes", json={"kind": "response", "body": "Booked twice in error."}, headers=staff).json()["status"] == "queried"
    # staff may not conclude
    assert api.post(f"{url}/status", json={"status": "confirmed", "note": "x"}, headers=staff).status_code == 403
    # a conclusion needs its basis recorded
    assert api.post(f"{url}/status", json={"status": "confirmed"}, headers=manager).status_code == 422
    confirmed = api.post(f"{url}/status", json={"status": "confirmed", "note": "Duplicate booking confirmed."}, headers=manager).json()
    assert confirmed["status"] == "confirmed" and confirmed["allowed"] == ["open", "resolved"]
    # not every move is allowed
    assert api.post(f"{url}/status", json={"status": "dismissed", "note": "x"}, headers=manager).status_code == 409
    assert api.post(f"{url}/status", json={"status": "cleared", "note": "x"}, headers=manager).status_code == 409
    # remediation action, then resolve
    with_action = api.post(f"{url}/actions", json={"description": "Reverse the second booking", "owner": "Accounts", "due_date": "2020-01-31"}, headers=staff).json()
    action = with_action["actions"][0]
    listed = api.get(f"/api/engagements/{engagement['id']}/actions", headers=staff).json()
    assert len(listed) == 1 and listed[0]["overdue"] is True and listed[0]["rule_code"] == "PUR-001"
    assert api.patch(f"/api/actions/{action['id']}", json={"is_done": True}, headers=staff).json()["actions"][0]["is_done"] is True
    final = api.post(f"{url}/status", json={"status": "resolved", "note": "Reversed vide JV 12."}, headers=manager).json()
    kinds = [n["kind"] for n in final["notes"]]
    assert final["status"] == "resolved" and kinds == ["query", "response", "status", "status"]


def test_closed_engagement_is_read_only(api, engagement, finding, staff, manager):
    eid = engagement["id"]
    assert api.patch(f"/api/engagements/{eid}", json={"is_closed": True}, headers=manager).json()["is_closed"] is True
    assert api.post(f"/api/engagements/{eid}/data/purchases", files={"file": ("p.csv", CSV)}, headers=staff).status_code == 409
    assert api.post(f"/api/engagements/{eid}/runs", headers=staff).status_code == 409
    assert api.post(f"/api/findings/{finding['id']}/notes", json={"body": "late note"}, headers=staff).status_code == 409
    assert api.patch(f"/api/engagements/{eid}", json={"materiality": 1}, headers=manager).status_code == 409
    assert api.get(f"/api/engagements/{eid}/findings", headers=staff).status_code == 200
    assert api.patch(f"/api/engagements/{eid}", json={"is_closed": False}, headers=manager).json()["is_closed"] is False


def test_rule_settings(api, engagement, staff, manager):
    url = f"/api/engagements/{engagement['id']}/rules"
    rules = api.get(url, headers=staff).json()
    assert len(rules) >= 60 and all(r["enabled"] and r["description"] for r in rules)
    assert api.patch(f"{url}/PUR-003", json={"enabled": False}, headers=staff).status_code == 403
    assert api.patch(f"{url}/PUR-003", json={"params": {"nope": 1}}, headers=manager).status_code == 422
    assert api.patch(f"{url}/PUR-003", json={"params": {"min_amount": -5}}, headers=manager).status_code == 422
    assert api.patch(f"{url}/XXX-999", json={"enabled": False}, headers=manager).status_code == 404
    out = api.patch(f"{url}/PUR-003", json={"enabled": False, "params": {"min_amount": 250000}}, headers=manager).json()
    assert out == {"code": "PUR-003", "enabled": False, "params": {"min_amount": 250000}}
    saved = next(r for r in api.get(url, headers=staff).json() if r["code"] == "PUR-003")
    assert saved["enabled"] is False and saved["params"][0]["value"] == 250000 and saved["params"][0]["default"] == 100000


def test_demo_views(api, demo, staff):
    eid = demo[0]
    dash = api.get(f"/api/engagements/{eid}/dashboard", headers=staff).json()
    assert dash["active"] == sum(dash["by_severity"].values()) > 60 and dash["risk"]["overall"] == 100
    assert dash["last_run"]["failed"] == 0 and dash["last_run"]["as_at"] == "31-03-2026" and len(dash["top"]) == 10
    listing = api.get(f"/api/engagements/{eid}/findings", params={"area": "TDS", "status": "active"}, headers=staff).json()
    assert listing["total"] == 5 and {f["rule_code"] for f in listing["items"]} == {"TDS-001", "TDS-002", "TDS-003"}
    assert api.get(f"/api/engagements/{eid}/findings", params={"fraud": True, "page_size": 500}, headers=staff).json()["total"] > 5
    detail = api.get(f"/api/findings/{listing['items'][0]['id']}", headers=staff).json()
    assert detail["evidence"] and detail["law"].startswith("Income-tax Act")
    gst = api.get(f"/api/engagements/{eid}/gst", headers=staff).json()
    assert gst["ready"] and gst["itc_at_risk"] > 0 and set(gst["statuses"]) == {"matched", "value_mismatch", "probable_match", "not_in_2b", "not_in_books"}
    assert all(line["status"] != "matched" for line in gst["lines"])
    wc = api.get(f"/api/engagements/{eid}/working-capital", headers=staff).json()
    assert wc["dso"] > 0 and wc["dpo"] > 0 and wc["dio"] > 0 and len(wc["receivables"]["buckets"]) == 6
    runs = api.get(f"/api/engagements/{eid}/runs", headers=staff).json()
    assert runs[0]["errors"] == 0 and len(runs[0]["rules"]) >= 60


def test_working_paper_download(api, demo, staff):
    out = api.get(f"/api/engagements/{demo[0]}/workpaper", headers=staff)
    assert out.status_code == 200 and "Working paper" in out.headers["content-disposition"]
    wb = load_workbook(io.BytesIO(out.content))
    assert wb.sheetnames == ["Summary", "Findings", "Evidence", "GSTR-2B reconciliation", "Rules run", "Review trail"]
    assert wb["Summary"]["B1"].value == "Demo Traders Private Limited"
    header = [c.value for c in wb["Findings"][1]]
    assert header[:4] == ["Ref", "Area", "Rule", "Severity"] and wb["Findings"].max_row > 60
    assert wb["Rules run"].max_row >= 61


def test_working_paper_neutralises_formulas_and_odd_client_names(api, manager, staff):
    client = api.post("/api/clients", json={"name": 'Evil "Co"\r\nX-Header: 1 / Ltd'}, headers=manager).json()
    eng = api.post("/api/engagements", json={"client_id": client["id"], "name": "FY", "period_start": "2025-04-01",
                                             "period_end": "2026-03-31"}, headers=manager).json()
    rows = b"invoice_no,invoice_date,vendor_name,taxable_value\nA-1,05-04-2025,=HYPERLINK(\"http://x\"),1000\nA-1,05-04-2025,=HYPERLINK(\"http://x\"),1000\n"
    assert api.post(f"/api/engagements/{eng['id']}/data/purchases", files={"file": ("p.csv", rows)}, headers=staff).json()["rows_loaded"] == 2
    api.post(f"/api/engagements/{eng['id']}/runs", headers=staff)
    out = api.get(f"/api/engagements/{eng['id']}/workpaper", headers=staff)
    assert out.status_code == 200
    assert out.headers["content-disposition"] == 'attachment; filename="Working paper - Evil CoX-Header 1  Ltd - FY.xlsx"'
    wb = load_workbook(io.BytesIO(out.content))
    cells = [c for ws in wb.worksheets for row in ws.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("=")]
    assert cells and all(c.data_type == "s" for c in cells)


def test_gst_view_says_what_is_missing(api, engagement, staff):
    assert api.get(f"/api/engagements/{engagement['id']}/gst", headers=staff).json() == {"ready": False, "missing": ["purchases", "gstr2b"]}


def test_health(api):
    assert api.get("/api/health").json() == {"status": "ok"}
