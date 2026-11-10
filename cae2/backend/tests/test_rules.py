"""Figures the rules compute, checked against values worked by hand."""
from datetime import date

import pytest
from sqlalchemy import select

from app.analytics.gst_reco import reconcile, summarise
from app.analytics.working_capital import working_capital
from app.audit.dataset import load_data, make_ctx
from app.audit.engine import run_audit
from app.demo import gstin
from app.models import Engagement, Finding

D = date(2025, 5, 1)
GST_A, GST_B = gstin("27", "AAACA1234A"), gstin("27", "AAACB1234B")


def run(db, eng, code):
    summary = run_audit(db, eng).summary
    result = next(r for r in summary["rules"] if r["code"] == code)
    assert result["status"] == "ok", result
    return db.scalars(select(Finding).where(Finding.engagement_id == eng.id, Finding.rule_code == code)).all()


def test_no_rule_fails_on_sparse_data(make_engagement, db):
    """One bare-minimum row per dataset: optional columns absent everywhere."""
    eng = make_engagement(
        purchases=[{"invoice_no": "A-1", "invoice_date": D, "vendor_name": "Apex", "taxable_value": 1000}],
        sales=[{"invoice_no": "S1", "invoice_date": D, "customer_name": "C", "taxable_value": 10}],
        ledger=[{"voucher_no": "1", "voucher_date": D, "voucher_type": "journal", "ledger": "A", "debit": 5},
                {"voucher_no": "1", "voucher_date": D, "voucher_type": "journal", "ledger": "B", "credit": 5}],
        bank=[{"txn_date": D, "withdrawal": 5}], stock=[{"move_date": D, "item_code": "I", "movement_type": "receipt", "quantity": 1}],
        employees=[{"emp_code": "E1", "name": "n"}], payroll=[{"emp_code": "E1", "pay_month": "Apr-2025", "gross": 10, "net_pay": 10}],
        parties=[{"code": "P", "name": "Apex"}], gstr2b=[{"supplier_gstin": GST_A, "invoice_no": "A-1", "taxable_value": 1000}])
    summary = run_audit(db, eng).summary
    assert [(r["code"], r["error"]) for r in summary["rules"] if r["status"] == "error"] == []
    assert sum(1 for r in summary["rules"] if r["status"] == "ok") >= 40


# ── TDS ──

def purchase(no, when, vendor, taxable, nature, tds=0, **extra):
    return {"invoice_no": no, "invoice_date": when, "vendor_name": vendor, "vendor_code": vendor, "taxable_value": taxable,
            "nature": nature, "tds_deducted": tds, **extra}


COMPANY, INDIVIDUAL = {"code": "CO", "name": "CO", "pan": "AAACC1234C"}, {"code": "IND", "name": "IND", "pan": "ABCPK1234L"}


def test_194c_single_and_aggregate_thresholds(make_engagement, db):
    eng = make_engagement(parties=[COMPANY, INDIVIDUAL, {"code": "SMALL", "name": "SMALL", "pan": "AAACS1234S"}], purchases=[
        purchase("1", D, "CO", 25000, "contract"), purchase("2", D, "CO", 40000, "contract"),          # only the 40,000 bill is liable
        purchase("3", D, "IND", 60000, "contract"), purchase("4", D, "IND", 50000, "contract"),        # aggregate 1,10,000 > 1,00,000
        purchase("5", D, "SMALL", 30000, "contract"), purchase("6", D, "SMALL", 30000, "contract")])   # neither test met
    found = {f.title.split(":")[0]: float(f.impact) for f in run(db, eng, "TDS-001")}
    assert found == {"CO": 800.0, "IND": 1100.0}     # 40,000 x 2%; 1,10,000 x 1% (individual)


def test_194j_threshold_changed_on_1_april_2025(make_engagement, db):
    old = make_engagement(period=(date(2024, 4, 1), date(2025, 3, 31)), parties=[COMPANY],
                          purchases=[purchase("1", date(2024, 6, 1), "CO", 40000, "professional")])
    new = make_engagement(parties=[COMPANY], purchases=[purchase("1", D, "CO", 40000, "professional")])
    assert [float(f.impact) for f in run(db, old, "TDS-001")] == [4000.0]     # limit 30,000 in FY 2024-25
    assert run(db, new, "TDS-001") == []                                      # limit 50,000 from FY 2025-26


def test_194i_is_tested_month_by_month_from_fy_2025_26(make_engagement, db):
    eng = make_engagement(parties=[COMPANY], purchases=[
        purchase("1", date(2025, 5, 1), "CO", 45000, "rent"), purchase("2", date(2025, 6, 1), "CO", 60000, "rent")])
    assert [float(f.impact) for f in run(db, eng, "TDS-001")] == [6000.0]     # only June exceeds 50,000 a month


def test_194q_only_on_excess_and_only_when_applicable(make_engagement, db):
    rows = [purchase(str(i), date(2025, 4 + i, 1), "CO", 2000000, "goods") for i in range(3)]      # 60 lakh in the year
    off = make_engagement(parties=[COMPANY], purchases=rows)
    on = make_engagement(parties=[COMPANY], purchases=rows, settings={"tds_194q_applicable": True})
    assert run(db, off, "TDS-001") == []
    assert [float(f.impact) for f in run(db, on, "TDS-001")] == [1000.0]      # 0.1% of the 10 lakh above 50 lakh


def test_short_deduction_missing_pan_and_pan_from_gstin(make_engagement, db):
    eng = make_engagement(parties=[COMPANY], purchases=[
        purchase("1", D, "CO", 100000, "professional", tds=5000),                                   # 10% due, 5% deducted
        purchase("2", D, "NOPAN", 100000, "professional", tds=10000),                               # no PAN: 20% due
        purchase("3", D, "GSTONLY", 100000, "professional", tds=10000, vendor_gstin=GST_A)])        # PAN read from GSTIN: fine
    assert {f.title.split(":")[0]: float(f.impact) for f in run(db, eng, "TDS-002")} == {"CO": 5000.0, "NOPAN": 10000.0}
    assert [f.title.split(":")[0] for f in run(db, eng, "TDS-003")] == ["NOPAN"]


def test_correctly_deducted_vendors_in_demo_are_not_flagged(demo_findings):
    flagged = " ".join(f.title for code in ("TDS-001", "TDS-002") for f in demo_findings(code))
    for vendor in ("Jai Contractors", "Kapoor & Co", "Laxmi Estates"):
        assert vendor not in flagged
    assert {f.title.split(":")[0]: float(f.impact) for f in demo_findings("TDS-001")} == {"Om Fabricators": 4800.0, "Ratna Alloys": 2200.0}


# ── MSME ──

def test_msme_due_date_interest_and_43bh(make_engagement, db):
    parties = [{"code": "MIC", "name": "MIC", "msme_category": "micro", "credit_days": 60},     # agreed 60 is capped at 45
               {"code": "MED", "name": "MED", "msme_category": "medium"}]                         # medium: outside s.15 test
    rows = [dict(purchase("1", date(2025, 6, 1), "MIC", 100000, "goods"), grn_date=date(2025, 6, 2), paid_date=date(2025, 8, 30), amount_paid=100000),
            dict(purchase("2", date(2026, 1, 5), "MIC", 50000, "goods")),
            dict(purchase("3", date(2025, 6, 1), "MED", 100000, "goods"))]
    eng = make_engagement(parties=parties, purchases=rows, settings={"rbi_bank_rate_pct": 6})
    found = {f.title: f for f in run(db, eng, "PUR-006")}
    assert len(found) == 2
    late = next(f for t, f in found.items() if "invoice 1 paid 44 days" in t)
    # accepted 02-06, due 17-07 (45 days), paid 30-08 = 44 days. Monthly rate 3 x 6% / 12 = 1.5%.
    # 1 full month compounded + 14 days: 1,00,000 x (1.015 x 1.007 - 1) = 2,210.50
    assert "payable by 17-07-2025 (45 days)" in late.detail and "₹2,210.50" in late.detail
    unpaid = next(f for t, f in found.items() if "invoice 2 unpaid" in t)
    assert "s.43B(h)" in unpaid.detail and "s.43B(h)" not in late.detail      # the late one was paid within the year

    no_agreement = make_engagement(parties=parties, purchases=rows[:1], settings={"msme_written_agreement": False})
    assert "(15 days)" in run(db, no_agreement, "PUR-006")[0].detail


# ── GST ──

def test_reconciliation_statuses_and_itc_at_risk(make_engagement, db):
    book = lambda no, gst_in, tax, **extra: {"invoice_no": no, "invoice_date": D, "vendor_name": "V", "vendor_gstin": gst_in,
                                             "taxable_value": tax * 10, "igst": tax, **extra}
    portal = lambda no, gst_in, tax, ok="Yes": {"supplier_gstin": gst_in, "invoice_no": no, "taxable_value": tax * 10, "igst": tax,
                                                "itc_available": ok}
    eng = make_engagement(
        purchases=[book("INV/001", GST_A, 100), book("INV-2", GST_A, 200), book("INV-3", GST_A, 300), book("INV-4", GST_A, 400),
                   book("INV-5", GST_A, 500)],
        gstr2b=[portal("inv 1", GST_A, 100), portal("INV-2", GST_A, 150), portal("X/3", GST_A, 300), portal("INV-5", GST_A, 500, "No"),
                portal("INV-9", GST_B, 900)])
    data = load_data(db, eng.id)
    reco = reconcile(data.purchases, data.gstr2b)
    status = dict(zip(reco["books_invoice_no"].where(reco["books_invoice_no"] != "", reco["portal_invoice_no"]), reco["status"]))
    assert status == {"INV/001": "matched",          # "INV/001" and "inv 1" are the same number
                      "INV-2": "value_mismatch", "INV-3": "probable_match", "INV-4": "not_in_2b", "INV-5": "matched",
                      "INV-9": "not_in_books"}
    # at risk: 50 excess on INV-2 + 400 not in 2B + 500 marked not available
    assert summarise(reco)["itc_at_risk"] == 950.0
    assert summarise(reco)["itc_claimed"] == 1500.0


def test_rule_37_reversal_is_proportionate(make_engagement, db):
    eng = make_engagement(purchases=[
        {"invoice_no": "1", "invoice_date": date(2025, 5, 1), "vendor_name": "V", "vendor_gstin": GST_A, "taxable_value": 100000,
         "igst": 18000, "amount_paid": 59000},                                              # half of 1,18,000 unpaid at 334 days
        {"invoice_no": "2", "invoice_date": date(2025, 12, 1), "vendor_name": "V", "vendor_gstin": GST_A, "taxable_value": 100000, "igst": 18000}])
    found = run(db, eng, "GST-004")
    assert [float(f.impact) for f in found] == [9000.0] and "invoice 1" in found[0].title


def test_section_16_4_last_date(make_engagement, db):
    row = lambda no, booked: {"invoice_no": no, "invoice_date": date(2025, 3, 20), "booking_date": booked, "vendor_name": "V",
                              "vendor_gstin": GST_A, "taxable_value": 1000, "igst": 180}
    eng = make_engagement(purchases=[row("on-time", date(2025, 11, 30)), row("late", date(2025, 12, 1))])
    found = run(db, eng, "GST-005")
    assert len(found) == 1 and "invoice late" in found[0].title and "30-11-2025" in found[0].detail


def test_wrong_tax_head_needs_client_state(make_engagement, db):
    rows = [{"invoice_no": "1", "invoice_date": D, "customer_name": "C", "place_of_supply": "29", "taxable_value": 1000, "cgst": 90, "sgst": 90, "total": 1180},
            {"invoice_no": "2", "invoice_date": D, "customer_name": "C", "place_of_supply": "27", "taxable_value": 1000, "igst": 180, "total": 1180},
            {"invoice_no": "3", "invoice_date": D, "customer_name": "C", "place_of_supply": "27", "taxable_value": 1000, "cgst": 90, "sgst": 90, "total": 1180}]
    eng = make_engagement(client_gstin=gstin("27", "AAACZ1234Z"), sales=rows)
    assert sorted(f.title[:9] for f in run(db, eng, "SAL-006")) == ["Invoice 1", "Invoice 2"]
    assert run(db, make_engagement(sales=rows), "SAL-006") == []       # no client GSTIN: cannot tell, so says nothing


# ── cash limits ──

def voucher(no, kind, when, *lines):
    return [{"voucher_no": no, "voucher_date": when, "voucher_type": kind, "ledger": name, "ledger_group": group, "debit": dr, "credit": cr}
            for name, group, dr, cr in lines]


def test_cash_limits(make_engagement, db):
    cash = lambda dr, cr: ("Cash", "Cash-in-Hand", dr, cr)
    eng = make_engagement(ledger=[
        *voucher("0", "opening", date(2025, 4, 1), cash(1000000, 0), ("Capital", "Capital Account", 0, 1000000)),
        *voucher("1", "payment", D, ("Repairs", "Indirect Expenses", 6000, 0), cash(0, 6000)),
        *voucher("2", "payment", D, ("Repairs", "Indirect Expenses", 5000, 0), cash(0, 5000)),          # 11,000 in a day: over
        *voucher("3", "payment", D, ("Stationery", "Indirect Expenses", 10000, 0), cash(0, 10000)),     # exactly 10,000: within
        *voucher("4", "payment", D, ("Freight Inward", "Direct Expenses", 30000, 0), cash(0, 30000)),   # goods carriage limit 35,000
        *voucher("5", "contra", D, ("HDFC", "Bank Accounts", 500000, 0), cash(0, 500000)),              # cash deposited in bank
        *voucher("6", "receipt", D, cash(200000, 0), ("Customer A", "Sundry Debtors", 0, 200000)),      # exactly 2,00,000: hit
        *voucher("7", "receipt", D, cash(199999, 0), ("Customer B", "Sundry Debtors", 0, 199999)),
        *voucher("8", "receipt", D, cash(20000, 0), ("Loan X", "Loans (Liability)", 0, 20000)),         # 269SS
        *voucher("9", "payment", D, ("Loan X", "Loans (Liability)", 19999, 0), cash(0, 19999))])        # below 269T limit
    assert [(f.title, float(f.impact)) for f in run(db, eng, "TRE-001")] == [("Cash ₹11,000.00 paid to Repairs on 01-05-2025", 11000.0)]
    assert [f.title for f in run(db, eng, "TRE-002")] == ["Cash ₹2,00,000.00 received from Customer A on 01-05-2025"]
    loans = run(db, eng, "TRE-003")
    assert len(loans) == 1 and "s.269SS" in loans[0].detail and float(loans[0].impact) == 20000.0
    assert run(db, eng, "JE-009") == []                                # opening balance covers every payment


# ── payroll ──

def test_pf_and_esi_shortfalls(make_engagement, db):
    line = lambda code, basic, gross, pf, esi: {"emp_code": code, "pay_month": "Apr-2025", "basic": basic, "gross": gross,
                                                "pf_employee": pf, "esi_employee": esi, "net_pay": gross - pf - esi}
    eng = make_engagement(employees=[{"emp_code": c, "name": c} for c in "ABCD"], payroll=[
        line("A", 12000, 18000, 1440, 135),     # correct: 12% of 12,000; 0.75% of 18,000
        line("B", 12000, 18000, 1000, 100),     # PF short 440, ESI short 35
        line("C", 20000, 30000, 0, 0),          # above both ceilings: not tested
        line("D", 15000, 21000, 1800, 157)])    # ESI due ceil(157.5) = 158, short by 1: within rounding
    assert [(f.title.split(":")[0], float(f.impact)) for f in run(db, eng, "PAY-006")] == [("B", 440.0)]
    assert [(f.title.split(":")[0], float(f.impact)) for f in run(db, eng, "PAY-007")] == [("B", 35.0)]
    off = make_engagement(settings={"pf_applicable": False}, employees=[{"emp_code": "B", "name": "B"}], payroll=[line("B", 12000, 18000, 0, 135)])
    assert run(db, off, "PAY-006") == []


# ── inventory and working capital ──

def test_negative_stock_orders_receipts_before_issues_on_a_day(make_engagement, db):
    move = lambda when, kind, qty: {"move_date": when, "item_code": "X", "movement_type": kind, "quantity": qty, "rate": 10, "reference": "r"}
    same_day = make_engagement(stock=[move(D, "issue", 5), move(D, "receipt", 5)])
    assert run(db, same_day, "INV-001") == []
    early = make_engagement(stock=[move(D, "issue", 5), move(date(2025, 5, 2), "receipt", 5)])
    assert len(run(db, early, "INV-001")) == 1


def test_working_capital_ratios(make_engagement, db):
    eng = make_engagement(period=(date(2025, 4, 1), date(2025, 6, 29)),   # 90 days
        sales=[{"invoice_no": "1", "invoice_date": date(2025, 4, 1), "customer_name": "C", "taxable_value": 900, "total": 900, "amount_received": 600}],
        purchases=[{"invoice_no": "1", "invoice_date": date(2025, 4, 1), "vendor_name": "V", "taxable_value": 450, "total": 450, "amount_paid": 0}])
    wc = working_capital(load_data(db, eng.id), make_ctx(db, db.get(Engagement, eng.id)))
    assert wc["days"] == 90 and wc["dso"] == 30.0 and wc["dpo"] == 90.0 and wc["dio"] is None and wc["ccc"] == -60.0
    assert wc["receivables"]["total"] == 300.0 and wc["receivables"]["buckets"][2] == {"bucket": "31-60", "amount": 300.0, "invoices": 1}


def test_demo_figures(demo_findings):
    assert float(demo_findings("GST-004")[0].impact) == 36000.0
    assert float(demo_findings("PAY-006")[0].impact) == 6960.0             # (1,380 - 800) x 12 months
    assert float(demo_findings("TRE-001")[0].impact) == 150000.0           # the 30,000 freight payment is within its limit
    assert len(demo_findings("TRE-001")) == 1

