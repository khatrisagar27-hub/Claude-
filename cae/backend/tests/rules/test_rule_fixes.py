"""Regression tests for rule defects found by the volume test (planted anomalies).

Each test pins one fixed defect: weekday numbering, warehouse netting, conditions
that could never fire, cross-year joins, per-day aggregation under s.40A(3) /
s.269ST, MSMED s.15 due dates, and the AATO basis for e-invoicing.
"""
from datetime import date, timedelta

import pytest

from app.rules import get_rule_fn
from tests.rules.schema import RULES_COMPANY, insert

TODAY = date.today()
SATURDAY = date(2025, 9, 20)
SUNDAY = date(2025, 9, 21)
MONDAY = date(2025, 9, 22)

_n = {"i": 0}


def _id():
    _n["i"] += 1
    return f"fx-{_n['i']}"


def run(duck, code, rule=None):
    return get_rule_fn(code)(duck, RULES_COMPANY, rule)


def keys(results):
    return {r["key"] for r in results}


# ---------------------------------------------------------------------------
# Sales
# ---------------------------------------------------------------------------
def test_sal_019_flags_saturday_and_sunday_not_monday(duck):
    for n, d in (("SAT", SATURDAY), ("SUN", SUNDAY), ("MON", MONDAY)):
        insert(duck, "sales_invoices", id=n, company_id=RULES_COMPANY, invoice_number=n,
               invoice_date=d, total_amount=600000, status="confirmed")

    assert sorted(r["evidence"]["invoice_number"] for r in run(duck, "SAL-019")) == ["SAT", "SUN"]


def test_sal_010_flags_outstanding_above_credit_limit(duck):
    insert(duck, "customers", id="c1", company_id=RULES_COMPANY, name="Over", credit_limit=100000)
    insert(duck, "customers", id="c2", company_id=RULES_COMPANY, name="Within", credit_limit=100000)
    for cust, amt in (("c1", 70000), ("c1", 50000), ("c2", 90000)):
        insert(duck, "sales_invoices", id=_id(), company_id=RULES_COMPANY, customer_id=cust,
               outstanding_amount=amt, status="confirmed")

    results = run(duck, "SAL-010")

    assert [r["evidence"]["customer"] for r in results] == ["Over"]
    assert results[0]["financial_impact"] == 20000


def _sale(duck, number, d, taxable, customer="b2b", irn=None, tax=18000):
    insert(duck, "sales_invoices", id=number, company_id=RULES_COMPANY, customer_id=customer,
           invoice_number=number, invoice_date=d, taxable_amount=taxable,
           total_amount=taxable + tax, igst_amount=tax, e_invoice_irn=irn, status="confirmed")


def test_sal_021_applies_by_prior_year_aato_not_invoice_value(duck):
    insert(duck, "customers", id="b2b", company_id=RULES_COMPANY, gstin="27AAACX0000X1Z1")
    insert(duck, "customers", id="b2c", company_id=RULES_COMPANY, gstin=None)
    _sale(duck, "FY23-BIG", date(2023, 6, 1), 6_00_00_000, irn="IRN")   # FY 2023-24 AATO ₹6 Cr
    _sale(duck, "SMALL", date(2024, 6, 1), 20000, tax=3600)            # B2B, tiny, no IRN
    _sale(duck, "B2C", date(2024, 6, 1), 20000, customer="b2c")        # B2C: out of scope

    results = run(duck, "SAL-021")

    assert [r["evidence"]["invoice_number"] for r in results] == ["SMALL"]
    assert results[0]["financial_impact"] == 10000     # s.122: higher of ₹10,000 or tax


def test_sal_021_silent_below_threshold(duck):
    insert(duck, "customers", id="b2b", company_id=RULES_COMPANY, gstin="27AAACX0000X1Z1")
    _sale(duck, "FY23", date(2023, 6, 1), 4_00_00_000, irn="IRN")      # ₹4 Cr < ₹5 Cr
    _sale(duck, "NOIRN", date(2024, 6, 1), 9_00_000)

    assert run(duck, "SAL-021") == []


def test_sal_022_aggregates_cash_receipts_per_person_per_day(duck):
    for amt in (120000, 90000):
        insert(duck, "bank_transactions", id=_id(), company_id=RULES_COMPANY, transaction_type="credit",
               transaction_mode="cash", amount=amt, counterparty_name="Buyer", transaction_date=TODAY)
    insert(duck, "bank_transactions", id=_id(), company_id=RULES_COMPANY, transaction_type="credit",
           transaction_mode="cash", amount=150000, counterparty_name="Other", transaction_date=TODAY)

    results = run(duck, "SAL-022")

    assert [r["evidence"]["party"] for r in results] == ["Buyer"]
    assert results[0]["financial_impact"] == 210000    # s.271DA: penalty equals amount


def test_sal_034_distinct_amounts_same_day_get_distinct_keys(duck):
    for amt in (1000, 1000, 2000, 2000):
        insert(duck, "sales_invoices", id=_id(), company_id=RULES_COMPANY, customer_id="c",
               invoice_date=TODAY, total_amount=amt, status="confirmed")

    assert len(keys(run(duck, "SAL-034"))) == 2


def test_rules_do_not_truncate_results(duck):
    for i in range(120):
        insert(duck, "sales_invoices", id=_id(), company_id=RULES_COMPANY, invoice_number=f"R{i}",
               total_amount=200000, status="confirmed")

    assert len(run(duck, "SAL-002")) == 120


# ---------------------------------------------------------------------------
# Purchase
# ---------------------------------------------------------------------------
def test_pur_001_same_number_at_two_vendors_is_two_findings(duck):
    for vendor in ("v1", "v1", "v2", "v2"):
        insert(duck, "purchase_invoices", id=_id(), company_id=RULES_COMPANY, vendor_id=vendor,
               invoice_number="1", total_amount=1000, status="approved")

    assert len(keys(run(duck, "PUR-001"))) == 2


def test_pur_006_flags_same_day_split_not_regular_supplier(duck):
    for amt in (60000, 70000):                      # two just-below-limit bills, same day
        insert(duck, "purchase_invoices", id=_id(), company_id=RULES_COMPANY, vendor_id="split",
               invoice_number=_id(), invoice_date=TODAY, total_amount=amt, status="approved")
    for d in range(10):                             # regular supplier, one bill a day
        insert(duck, "purchase_invoices", id=_id(), company_id=RULES_COMPANY, vendor_id="regular",
               invoice_number=_id(), invoice_date=TODAY - timedelta(days=d), total_amount=80000,
               status="approved")

    results = run(duck, "PUR-006")

    assert [r["evidence"]["vendor_id"] for r in results] == ["split"]


def test_pur_016_flags_duplicate_paid_invoices(duck):
    for n in ("A", "B"):
        insert(duck, "purchase_invoices", id=_id(), company_id=RULES_COMPANY, vendor_id="v1",
               invoice_number=n, total_amount=55555.55, paid_amount=55555.55, status="paid")

    results = run(duck, "PUR-016")

    assert len(results) == 1
    assert results[0]["financial_impact"] == pytest.approx(55555.55)


def test_pur_022_matches_vendor_and_employee_bank_account(duck):
    insert(duck, "vendors", id="v1", company_id=RULES_COMPANY, name="Shell Co", bank_account_number=" 123456 ")
    insert(duck, "vendors", id="v2", company_id=RULES_COMPANY, name="Real Co", bank_account_number="999")
    insert(duck, "employees", id="e1", company_id=RULES_COMPANY, full_name="Insider", bank_account_number="123456")

    results = run(duck, "PUR-022")

    assert [(r["evidence"]["vendor_name"], r["evidence"]["employee_name"]) for r in results] == [("Shell Co", "Insider")]


def _msme(duck, number, accepted, due=None, status="approved", msme="Micro"):
    insert(duck, "vendors", id=f"v-{number}", company_id=RULES_COMPANY, name=number, msme_status=msme)
    insert(duck, "purchase_invoices", id=number, company_id=RULES_COMPANY, vendor_id=f"v-{number}",
           invoice_number=number, invoice_date=accepted, receipt_date=accepted, due_date=due,
           total_amount=100000, paid_amount=0, status=status)


def test_pur_031_uses_s15_due_date(duck):
    _msme(duck, "NO-TERMS-LATE", TODAY - timedelta(days=20))                         # 15-day default
    _msme(duck, "CAPPED-AT-45", TODAY - timedelta(days=50), due=TODAY + timedelta(days=40))
    _msme(duck, "WITHIN-TERMS", TODAY - timedelta(days=20), due=TODAY + timedelta(days=10))
    _msme(duck, "MEDIUM", TODAY - timedelta(days=100), msme="Medium")                 # not covered
    _msme(duck, "PAID", TODAY - timedelta(days=100), status="paid")

    results = run(duck, "PUR-031")

    assert sorted(r["evidence"]["invoice_number"] for r in results) == ["CAPPED-AT-45", "NO-TERMS-LATE"]
    capped = next(r for r in results if r["evidence"]["invoice_number"] == "CAPPED-AT-45")
    assert capped["evidence"]["days_late"] == 5
    assert capped["financial_impact"] == 100000
    assert capped["evidence"]["s16_interest"] is None       # bank rate not configured


def test_pur_031_s16_interest_compounds_monthly(duck, monkeypatch):
    import app.rules.purchase_rules as pr

    class FixedDate(date):
        @classmethod
        def today(cls):
            return date(2026, 9, 22)
    monkeypatch.setattr(pr, "date", FixedDate)

    class Rule:
        parameters = {"rbi_bank_rate": 0.06}      # 3x = 18% p.a. = 1.5% a month

    _msme(duck, "LATE", date(2026, 1, 7))          # no terms: due 22 Jan 2026 (15 days)

    [result] = run(duck, "PUR-031", Rule())

    # 22 Jan -> 22 Sep = 8 completed months: 1,00,000 x (1.015^8 - 1)
    assert result["evidence"]["statutory_due"] == "2026-01-22"
    assert result["evidence"]["s16_interest"] == 12649.26


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------
def _mv(duck, item, mtype, qty, value, d=TODAY, wh_from=None, wh_to=None):
    insert(duck, "inventory_movements", id=_id(), company_id=RULES_COMPANY, item_code=item,
           movement_type=mtype, quantity=qty, total_value=value, movement_date=d,
           warehouse_from=wh_from, warehouse_to=wh_to)


def test_inv_001_nets_receipts_into_warehouse_to_against_issues(duck):
    _mv(duck, "OK", "goods_receipt", 100, 1000, wh_to="WH1")
    _mv(duck, "OK", "goods_issue", 80, 800, wh_from="WH1")
    _mv(duck, "NEG", "goods_receipt", 10, 100, wh_to="WH1")
    _mv(duck, "NEG", "goods_issue", 30, 300, wh_from="WH1")

    results = run(duck, "INV-001")

    assert [(r["evidence"]["item_code"], r["evidence"]["balance"]) for r in results] == [("NEG", -20)]


def test_inv_001_transfer_moves_stock_between_warehouses(duck):
    _mv(duck, "T", "goods_receipt", 50, 500, wh_to="WH1")
    _mv(duck, "T", "transfer", 50, 500, wh_from="WH1", wh_to="WH2")
    _mv(duck, "T", "goods_issue", 40, 400, wh_from="WH2")

    assert run(duck, "INV-001") == []


def test_inv_005_ignores_items_fully_issued(duck):
    old = TODAY - timedelta(days=300)
    _mv(duck, "GONE", "goods_receipt", 10, 1000, d=old, wh_to="WH1")
    _mv(duck, "GONE", "goods_issue", 10, 1000, d=old, wh_from="WH1")
    _mv(duck, "STUCK", "goods_receipt", 10, 1000, d=old, wh_to="WH1")

    assert [r["evidence"]["item_code"] for r in run(duck, "INV-005")] == ["STUCK"]


def test_inv_010_flags_weekend_not_monday(duck):
    for d in (SATURDAY, SUNDAY, MONDAY):
        _mv(duck, str(d), "goods_receipt", 1, 300000, d=d, wh_to="WH1")

    assert sorted(r["evidence"]["movement_date"] for r in run(duck, "INV-010")) == [str(SATURDAY), str(SUNDAY)]


# ---------------------------------------------------------------------------
# Payroll / treasury
# ---------------------------------------------------------------------------
def test_pay_002_compares_december_to_january(duck):
    insert(duck, "payroll_records", id=_id(), company_id=RULES_COMPANY, employee_id="e1",
           pay_period_year=2025, pay_period_month=12, net_pay=50000)
    insert(duck, "payroll_records", id=_id(), company_id=RULES_COMPANY, employee_id="e1",
           pay_period_year=2026, pay_period_month=1, net_pay=100000)

    results = run(duck, "PAY-002")

    assert [r["evidence"]["period"] for r in results] == ["2026-01"]


def test_pay_005_flags_pf_and_esi_short_deduction(duck):
    rows = [
        # basic 12,000 -> PF due 1,440 each side; only 1,000 deducted by each.
        dict(basic_salary=12000, gross_earnings=30000, pf_employee=1000, pf_employer=1000),
        # gross 20,000 -> ESI due 150 + 650; none deducted. PF correct.
        dict(basic_salary=10000, gross_earnings=20000, pf_employee=1200, pf_employer=1200),
        # basic 40,000, PF on the 15,000 ceiling = 1,800 each: compliant.
        dict(basic_salary=40000, gross_earnings=80000, pf_employee=1800, pf_employer=1800),
    ]
    for r in rows:
        insert(duck, "payroll_records", id=_id(), company_id=RULES_COMPANY, employee_id=_id(),
               pay_period_year=2026, pay_period_month=4, esic_employee=0, esic_employer=0, **r)

    [result] = run(duck, "PAY-005")

    assert result["evidence"]["employees"] == 2
    assert result["evidence"]["pf_short"] == pytest.approx(880)
    assert result["evidence"]["esi_short"] == pytest.approx(800)


def test_tre_001_sums_split_cash_payments_per_party_day(duck):
    for _ in range(3):
        insert(duck, "bank_transactions", id=_id(), company_id=RULES_COMPANY, transaction_type="debit",
               transaction_mode="cash", amount=9000, counterparty_name="Split", transaction_date=TODAY)

    results = run(duck, "TRE-001")

    assert len(results) == 1
    assert results[0]["financial_impact"] == 27000


def test_je_015_uses_indian_financial_year(duck):
    from datetime import datetime
    cases = [
        ("MAR-APR", date(2025, 3, 29), datetime(2025, 4, 2)),   # FY 24-25 -> 25-26: prior period
        ("DEC-JAN", date(2024, 12, 31), datetime(2025, 1, 2)),  # same FY: not prior period
    ]
    for num, entry, posted in cases:
        insert(duck, "journal_entries", id=num, company_id=RULES_COMPANY, voucher_number=num,
               entry_date=entry, posted_at=posted, is_posted=True, total_debit=200000)

    assert [r["evidence"]["voucher_number"] for r in run(duck, "JE-015")] == ["MAR-APR"]


def test_sal_002_does_not_round_paise_into_a_round_amount(duck):
    for n, amt in (("ROUND", 124000.00), ("PAISE", 123999.60)):
        insert(duck, "sales_invoices", id=n, company_id=RULES_COMPANY, invoice_number=n,
               total_amount=amt, status="confirmed")

    assert [r["evidence"]["invoice_number"] for r in run(duck, "SAL-002")] == ["ROUND"]
