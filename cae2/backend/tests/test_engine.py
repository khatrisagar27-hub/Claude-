"""The engine's contract: every rule runs, re-runs never duplicate, and a
reviewer's conclusions survive new data."""
from datetime import date

import pytest
from sqlalchemy import select

from app.audit import registry
from app.audit.engine import fingerprint, grade, run_audit
from app.audit.registry import Hit, load_rules
from app.demo import to_xlsx
from app.ingest.loader import import_file
from app.models import Finding, RuleSetting

import pandas as pd

RULES = sorted(load_rules())
DUP = [{"invoice_no": "A-1", "invoice_date": date(2025, 5, 1), "vendor_name": "Apex", "taxable_value": 1000},
       {"invoice_no": "A-1", "invoice_date": date(2025, 5, 1), "vendor_name": "Apex", "taxable_value": 1000}]


def findings(db, eng, code=None):
    query = select(Finding).where(Finding.engagement_id == eng.id)
    return db.scalars(query.where(Finding.rule_code == code) if code else query).all()


@pytest.mark.parametrize("code", RULES)
def test_every_rule_runs_and_finds_its_planted_exception(demo, code):
    result = next(r for r in demo[1]["rules"] if r["code"] == code)
    assert result["status"] == "ok", result["error"]
    assert result["hits"] >= 1


def test_rule_catalogue_is_complete():
    for code, rule in load_rules().items():
        assert rule.description, f"{code} has no description"
        assert rule.needs, f"{code} declares no data needs"
        assert code.split("-")[0] in ("SAL", "PUR", "GST", "TDS", "JE", "TRE", "PAY", "INV")


def test_rerun_updates_instead_of_duplicating(make_engagement, db):
    eng = make_engagement(purchases=DUP)
    first = run_audit(db, eng).summary
    second = run_audit(db, eng).summary
    assert first["new"] == 1 and second["new"] == 0 and second["updated"] == 1
    assert len(findings(db, eng, "PUR-001")) == 1


def test_finding_clears_when_data_is_fixed_and_reopens_if_it_returns(make_engagement, db):
    eng = make_engagement(purchases=DUP)
    run_audit(db, eng)
    import_file(db, eng, "purchases", "p.xlsx", to_xlsx(pd.DataFrame(DUP[:1])))
    assert run_audit(db, eng).summary["cleared"] == 1
    finding = findings(db, eng, "PUR-001")[0]
    assert finding.status == "cleared" and "Cleared" in finding.notes[-1].body
    import_file(db, eng, "purchases", "p.xlsx", to_xlsx(pd.DataFrame(DUP)))
    assert run_audit(db, eng).summary["reopened"] == 1
    db.refresh(finding)
    assert finding.status == "open" and len(findings(db, eng, "PUR-001")) == 1


@pytest.mark.parametrize("status", ["confirmed", "dismissed", "resolved"])
def test_concluded_findings_are_never_changed_by_a_run(make_engagement, db, status):
    eng = make_engagement(purchases=DUP)
    run_audit(db, eng)
    finding = findings(db, eng, "PUR-001")[0]
    finding.status = status
    db.commit()
    import_file(db, eng, "purchases", "p.xlsx", to_xlsx(pd.DataFrame(DUP[:1])))
    run_audit(db, eng)
    db.refresh(finding)
    assert finding.status == status


def test_disabled_rule_does_not_run_or_clear(make_engagement, db):
    eng = make_engagement(purchases=DUP)
    run_audit(db, eng)
    db.add(RuleSetting(engagement_id=eng.id, rule_code="PUR-001", enabled=False, params={}))
    db.commit()
    import_file(db, eng, "purchases", "p.xlsx", to_xlsx(pd.DataFrame(DUP[:1])))
    summary = run_audit(db, eng).summary
    assert next(r for r in summary["rules"] if r["code"] == "PUR-001")["status"] == "disabled"
    assert findings(db, eng, "PUR-001")[0].status == "open"      # not cleared: the rule did not look


def test_rules_without_data_are_reported_not_passed(make_engagement, db):
    eng = make_engagement(purchases=DUP)
    by_code = {r["code"]: r for r in run_audit(db, eng).summary["rules"]}
    assert by_code["PAY-001"]["status"] == "no_data" and "payroll" in by_code["PAY-001"]["error"]
    assert by_code["PUR-003"]["status"] == "no_data"              # purchases loaded, but no PO column at all
    assert by_code["PUR-001"]["status"] == "ok"


def test_a_failing_rule_is_reported_and_the_rest_still_run(make_engagement, db, monkeypatch):
    eng = make_engagement(purchases=DUP)
    run_audit(db, eng)
    rule = load_rules()["PUR-001"]
    monkeypatch.setattr(rule, "fn", lambda data, p, ctx: 1 / 0)
    summary = run_audit(db, eng).summary
    by_code = {r["code"]: r for r in summary["rules"]}
    assert by_code["PUR-001"]["status"] == "error" and "ZeroDivisionError" in by_code["PUR-001"]["error"]
    assert by_code["PUR-011"]["status"] == "ok"
    assert findings(db, eng, "PUR-001")[0].status == "open"      # a failed rule clears nothing


def test_rule_parameters_can_be_overridden_per_engagement(make_engagement, db):
    rows = [{"invoice_no": f"A-{i}", "invoice_date": date(2025, 5, i), "vendor_name": "Apex", "taxable_value": 60000, "po_no": "P1" if i == 1 else ""}
            for i in (1, 2)]
    eng = make_engagement(purchases=rows)
    run_audit(db, eng)
    assert findings(db, eng, "PUR-003") == []                    # 60,000 is below the default 1,00,000
    db.add(RuleSetting(engagement_id=eng.id, rule_code="PUR-003", enabled=True, params={"min_amount": 50000}))
    db.commit()
    run_audit(db, eng)
    assert len(findings(db, eng, "PUR-003")) == 1


def test_severity_grading():
    assert grade("medium", 500, materiality=1000, trivial=100) == "medium"
    assert grade("low", 1000, materiality=1000, trivial=100) == "critical"   # at or above materiality
    assert grade("high", 50, materiality=1000, trivial=100) == "medium"      # below trivial: one step down
    assert grade("low", 50, materiality=1000, trivial=100) == "low"
    assert grade("high", 0, materiality=1000, trivial=100) == "high"         # no amount: inherent level stands
    assert grade("high", 5_000_000, materiality=0, trivial=0) == "high"      # thresholds not set


def test_materiality_drives_severity_end_to_end(make_engagement, db):
    eng = make_engagement(purchases=DUP, materiality=1000, trivial=100)
    run_audit(db, eng)
    assert findings(db, eng, "PUR-001")[0].severity == "critical"
    assert fingerprint("a") != fingerprint("b") and fingerprint("a") == fingerprint("a")


def test_duplicate_keys_from_one_rule_make_one_finding(make_engagement, db, monkeypatch):
    eng = make_engagement(purchases=DUP)
    monkeypatch.setattr(load_rules()["PUR-001"], "fn", lambda data, p, ctx: [Hit("k", "t", "d"), Hit("k", "t", "d")])
    assert run_audit(db, eng).summary["new"] == 1
    assert registry.RULES["PUR-001"].code == "PUR-001"
