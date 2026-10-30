"""
End-to-end on a throwaway embedded PostgreSQL (pgserver): migrate, seed, run the
first audit pass, then exercise the API. Skipped when pgserver is not installed.

Run on its own (it sets DATABASE_URL before the app is imported):
    python -m pytest tests/test_integration_pg.py -q
"""
import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

pgserver = pytest.importorskip("pgserver")

BACKEND = Path(__file__).resolve().parents[1]
SCRIPTS = BACKEND.parent / "scripts"


def _run(args, env):
    proc = subprocess.run([sys.executable, *args], cwd=BACKEND, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=900)
    assert proc.returncode == 0, f"{args} failed:\n{proc.stdout[-3000:]}\n{proc.stderr[-3000:]}"
    return proc.stdout


@pytest.fixture(scope="module")
def stack(tmp_path_factory):
    server = pgserver.get_server(str(tmp_path_factory.mktemp("pgdata")), cleanup_mode="stop")
    server.psql("CREATE DATABASE cae_it;")
    uri = server.get_uri("cae_it")
    env = {**os.environ, "DATABASE_URL": uri, "SECRET_KEY": "integration-test-secret-key-32chars!",
           "PYTHONIOENCODING": "utf-8", "ANTHROPIC_API_KEY": "", "ENVIRONMENT": "test"}
    os.environ.update({k: env[k] for k in ("DATABASE_URL", "SECRET_KEY", "ANTHROPIC_API_KEY", "ENVIRONMENT")})
    _run(["-m", "alembic", "upgrade", "head"], env)
    seed_out = _run([str(SCRIPTS / "seed_data.py")], env)
    audit_out = _run([str(SCRIPTS / "run_first_audit.py")], env)
    yield {"uri": uri, "seed": seed_out, "audit": audit_out}
    server.cleanup()


@pytest.fixture(scope="module")
def client(stack):
    from fastapi.testclient import TestClient
    from app.main import app

    c = TestClient(app)
    login = c.post("/api/v1/auth/login", json={"email": "sagar@ska.in", "password": "CAE@2024"})
    assert login.status_code == 200, login.text
    c.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    return c


@pytest.fixture(scope="module")
def company_id(stack):
    from app.database import SessionLocal
    from app.models.tenant import Company

    db = SessionLocal()
    try:
        return str(db.query(Company).filter(Company.name == "Bharat Steel & Alloys Pvt Ltd").one().id)
    finally:
        db.close()


def test_first_audit_runs_every_rule_without_errors(stack):
    out = "\n".join(line for line in stack["audit"].splitlines() if "sqlalchemy.engine" not in line)
    print(out.encode("ascii", "replace").decode())
    assert "Errors: 0" in out
    rules_run = int(out.split("Rules run:")[1].split()[0])
    from app.rules.catalogue import RULE_CATALOGUE
    assert rules_run == len(RULE_CATALOGUE)
    assert int(out.split("Exceptions raised:")[1].split()[0]) > 0


def test_exceptions_carry_statutory_references(stack, company_id):
    from app.database import SessionLocal
    from app.models.audit import AuditException, AuditRule

    db = SessionLocal()
    try:
        rows = (db.query(AuditRule.rule_code, AuditException.supporting_data, AuditException.category)
                .join(AuditException, AuditException.rule_id == AuditRule.id)
                .filter(AuditException.company_id == company_id).all())
    finally:
        db.close()
    by_code = {}
    for code, evidence, category in rows:
        by_code.setdefault(code, []).append((evidence or {}, category))
    print({k: len(v) for k, v in sorted(by_code.items())})
    # seed has cash debits of Rs.15k-50k to named parties in 2023-24 -> 1961 Act reference
    assert "TRE-001" in by_code
    assert all("40A(3)" in ev["statutory_ref"] for ev, _ in by_code["TRE-001"])
    assert {cat for _, cat in by_code["TRE-001"]} == {"statutory"}
    # journal rules moved out of bank_reconciliation
    assert all(cat == "financial_reporting" for code, v in by_code.items() if code.startswith("JE-") for _, cat in v)


def test_rules_api_and_catalogue_sync(client, company_id):
    rules = client.get(f"/api/v1/rules?company_id={company_id}")
    assert rules.status_code == 200 and len(rules.json()) >= 55
    sync = client.post(f"/api/v1/rules/sync?company_id={company_id}")
    assert sync.status_code == 200 and sync.json()["created"] == 0


def test_gst_invoice_level_recon_from_csv(client, company_id):
    from app.database import SessionLocal
    from app.models.master import Vendor
    from app.models.transaction import PurchaseInvoice

    db = SessionLocal()
    try:
        inv, vendor = (db.query(PurchaseInvoice, Vendor).join(Vendor, Vendor.id == PurchaseInvoice.vendor_id)
                       .filter(PurchaseInvoice.company_id == company_id, PurchaseInvoice.itc_eligible.is_(True),
                               PurchaseInvoice.status != "cancelled", (PurchaseInvoice.igst_amount + PurchaseInvoice.cgst_amount) > 0)
                       .order_by(PurchaseInvoice.invoice_date).first())
        period = inv.invoice_date.strftime("%Y-%m")
        gstin = inv.vendor_gstin or vendor.gstin
        tax = float(inv.cgst_amount) + float(inv.sgst_amount) + float(inv.igst_amount) + float(inv.cess_amount)
    finally:
        db.close()
    csv = ("GSTIN of supplier,Trade/Legal name,Invoice number,Invoice Date,Taxable Value,Integrated Tax,Central Tax,State/UT Tax,Cess\n"
           f"{gstin},{vendor.name},{inv.invoice_number},{inv.invoice_date:%d-%m-%Y},{float(inv.taxable_amount)},{tax},0,0,0\n"
           f"{gstin},{vendor.name},NOT-IN-BOOKS-1,{inv.invoice_date:%d-%m-%Y},1000,180,0,0,0\n")
    resp = client.post("/api/v1/gst/upload-gstr2b",
                       data={"company_id": company_id, "period": period},
                       files={"file": ("gstr2b.csv", io.BytesIO(csv.encode()), "text/csv")})
    assert resp.status_code == 202, resp.text
    result = resp.json()["result"]
    assert result["mode"] == "invoice"
    assert result["summary"]["matched_count"] >= 1 and result["summary"]["missing_in_books_count"] == 1
    details = client.get(f"/api/v1/gst/reconciliation/{period}/details?company_id={company_id}").json()
    assert details["details"]["summary"]["itc_at_risk"] == result["summary"]["itc_at_risk"]
    bad = client.post("/api/v1/gst/upload-gstr2b", data={"company_id": company_id, "period": period},
                      files={"file": ("x.txt", io.BytesIO(b"not json"), "text/plain")})
    assert bad.status_code == 422


def test_statutory_endpoints(client, company_id):
    assert client.get("/api/v1/statutory/section-map").json()["income_tax_act_2025_effective"] == "2026-04-01"
    app_resp = client.post("/api/v1/statutory/applicability", json={
        "company_id": company_id, "balance_sheet_date": "2025-03-31", "paid_up_capital": 50_000_000})
    assert app_resp.status_code == 200, app_resp.text
    body = app_resp.json()
    assert {"small_company", "caro_2020", "ifc_reporting_143_3_i", "e_invoicing"} <= set(body)
    msme = client.get(f"/api/v1/statutory/msme-interest?company_id={company_id}")
    assert msme.status_code == 200, msme.text
    assert all(b["msme_status"].lower() in ("micro", "small") for b in msme.json()["bills"])
    s1 = client.post("/api/v1/statutory/sample", json={"company_id": company_id, "population": "purchase_invoices",
                                                       "seed": 42, "n": 10, "high_value_threshold": 2_000_000})
    s2 = client.post("/api/v1/statutory/sample", json={"company_id": company_id, "population": "purchase_invoices",
                                                       "seed": 42, "n": 10, "high_value_threshold": 2_000_000})
    assert s1.status_code == 200 and s1.json()["sample"] == s2.json()["sample"]
    c44 = client.get(f"/api/v1/statutory/clause44?company_id={company_id}&fy=2024")
    assert c44.status_code == 200, c44.text
    assert c44.json()["tie_out_difference"] == 0


def test_risk_and_working_capital_still_work(client, company_id):
    assert client.get(f"/api/v1/working-capital/metrics?company_id={company_id}").status_code == 200
    from app.database import SessionLocal
    from app.models.risk import RiskScore
    db = SessionLocal()
    try:
        areas = {r.entity_name for r in db.query(RiskScore).filter(RiskScore.company_id == company_id).all()}
    finally:
        db.close()
    assert "financial_reporting" in areas
