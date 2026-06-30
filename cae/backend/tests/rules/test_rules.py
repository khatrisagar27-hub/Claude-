"""Behavioural tests for representative rules across all six rule modules."""
from datetime import date, timedelta

import pytest

from app.rules import get_rule_fn
from tests.rules.schema import OTHER_COMPANY, RULES_COMPANY, insert

TODAY = date.today()


def run(duck, code):
    return get_rule_fn(code)(duck, RULES_COMPANY, None)


# ---------------------------------------------------------------------------
# Sales
# ---------------------------------------------------------------------------
def test_sal_001_flags_duplicate_invoice_number(duck):
    for _ in range(2):
        insert(duck, "sales_invoices", id=_id(), company_id=RULES_COMPANY,
               invoice_number="INV-1", total_amount=5000, status="confirmed")
    insert(duck, "sales_invoices", id=_id(), company_id=RULES_COMPANY,
           invoice_number="INV-2", total_amount=5000, status="confirmed")

    results = run(duck, "SAL-001")

    assert len(results) == 1
    assert results[0]["severity"] == "critical"
    assert results[0]["evidence"]["invoice_number"] == "INV-1"


def test_sal_001_ignores_cancelled_and_other_company(duck):
    insert(duck, "sales_invoices", id=_id(), company_id=RULES_COMPANY,
           invoice_number="INV-1", total_amount=5000, status="cancelled")
    insert(duck, "sales_invoices", id=_id(), company_id=RULES_COMPANY,
           invoice_number="INV-1", total_amount=5000, status="cancelled")
    insert(duck, "sales_invoices", id=_id(), company_id=OTHER_COMPANY,
           invoice_number="INV-9", total_amount=5000, status="confirmed")
    insert(duck, "sales_invoices", id=_id(), company_id=OTHER_COMPANY,
           invoice_number="INV-9", total_amount=5000, status="confirmed")

    assert run(duck, "SAL-001") == []


def test_sal_002_flags_large_round_amount_only(duck):
    insert(duck, "sales_invoices", id=_id(), company_id=RULES_COMPANY,
           invoice_number="R1", total_amount=500000, status="confirmed")   # round, >1L
    insert(duck, "sales_invoices", id=_id(), company_id=RULES_COMPANY,
           invoice_number="R2", total_amount=123456, status="confirmed")   # not round
    insert(duck, "sales_invoices", id=_id(), company_id=RULES_COMPANY,
           invoice_number="R3", total_amount=50000, status="confirmed")    # round but <1L

    results = run(duck, "SAL-002")

    assert [r["evidence"]["invoice_number"] for r in results] == ["R1"]


def test_sal_034_flags_same_customer_day_amount(duck):
    for _ in range(2):
        insert(duck, "sales_invoices", id=_id(), company_id=RULES_COMPANY,
               customer_id="cust-1", invoice_date=TODAY, total_amount=9000, status="confirmed")

    results = run(duck, "SAL-034")

    assert len(results) == 1
    assert results[0]["evidence"]["count"] == 2


# ---------------------------------------------------------------------------
# Purchase
# ---------------------------------------------------------------------------
def test_pur_001_flags_duplicate_vendor_invoice(duck):
    for _ in range(2):
        insert(duck, "purchase_invoices", id=_id(), company_id=RULES_COMPANY,
               vendor_id="v-1", invoice_number="B-1", total_amount=20000, status="approved")

    results = run(duck, "PUR-001")

    assert len(results) == 1
    assert results[0]["financial_impact"] == 40000  # SUM(total_amount)


def test_pur_004_flags_high_value_invoice_without_po(duck):
    insert(duck, "purchase_invoices", id=_id(), company_id=RULES_COMPANY,
           vendor_id="v-1", invoice_number="NOPO", total_amount=150000,
           our_po_number=None, status="approved")
    insert(duck, "purchase_invoices", id=_id(), company_id=RULES_COMPANY,
           vendor_id="v-1", invoice_number="HASPO", total_amount=150000,
           our_po_number="PO-123", status="approved")
    insert(duck, "purchase_invoices", id=_id(), company_id=RULES_COMPANY,
           vendor_id="v-1", invoice_number="SMALL", total_amount=5000,
           our_po_number=None, status="approved")

    results = run(duck, "PUR-004")

    assert [r["evidence"]["invoice_number"] for r in results] == ["NOPO"]


# ---------------------------------------------------------------------------
# Journal
# ---------------------------------------------------------------------------
def test_je_001_flags_manual_je_without_narration(duck):
    insert(duck, "journal_entries", id=_id(), company_id=RULES_COMPANY,
           voucher_number="JV-1", voucher_type="journal", narration=None,
           total_debit=200000)
    insert(duck, "journal_entries", id=_id(), company_id=RULES_COMPANY,
           voucher_number="JV-2", voucher_type="journal", narration="Accrual",
           total_debit=200000)

    results = run(duck, "JE-001")

    assert [r["evidence"]["voucher_number"] for r in results] == ["JV-1"]


def test_je_009_flags_unbalanced_entry(duck):
    insert(duck, "journal_entries", id="je-1", company_id=RULES_COMPANY,
           voucher_number="JV-1", total_debit=1000)
    insert(duck, "journal_entry_lines", id=_id(), journal_entry_id="je-1",
           debit_amount=1000, credit_amount=0)
    insert(duck, "journal_entry_lines", id=_id(), journal_entry_id="je-1",
           debit_amount=0, credit_amount=900)  # 100 out of balance

    results = run(duck, "JE-009")

    assert len(results) == 1
    assert results[0]["financial_impact"] == 100


def test_je_009_passes_balanced_entry(duck):
    insert(duck, "journal_entries", id="je-1", company_id=RULES_COMPANY,
           voucher_number="JV-1", total_debit=1000)
    insert(duck, "journal_entry_lines", id=_id(), journal_entry_id="je-1",
           debit_amount=1000, credit_amount=0)
    insert(duck, "journal_entry_lines", id=_id(), journal_entry_id="je-1",
           debit_amount=0, credit_amount=1000)

    assert run(duck, "JE-009") == []


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------
def test_inv_001_flags_negative_stock(duck):
    insert(duck, "inventory_movements", id=_id(), company_id=RULES_COMPANY,
           item_code="WIDGET", warehouse_from="WH1", movement_type="goods_receipt",
           quantity=10, movement_date=TODAY)
    insert(duck, "inventory_movements", id=_id(), company_id=RULES_COMPANY,
           item_code="WIDGET", warehouse_from="WH1", movement_type="goods_issue",
           quantity=15, movement_date=TODAY)  # issued more than received

    results = run(duck, "INV-001")

    assert len(results) == 1
    assert results[0]["evidence"]["balance"] == -5


def test_inv_005_flags_slow_moving_stock(duck):
    """Regression guard for the DuckDB CURRENT_DATE-in-GROUP-BY fix."""
    insert(duck, "inventory_movements", id=_id(), company_id=RULES_COMPANY,
           item_code="DUSTY", warehouse_from="WH1", movement_type="goods_receipt",
           quantity=5, total_value=100000, movement_date=TODAY - timedelta(days=200))
    insert(duck, "inventory_movements", id=_id(), company_id=RULES_COMPANY,
           item_code="FRESH", warehouse_from="WH1", movement_type="goods_receipt",
           quantity=5, total_value=100000, movement_date=TODAY - timedelta(days=10))

    results = run(duck, "INV-005")

    assert [r["evidence"]["item_code"] for r in results] == ["DUSTY"]
    assert results[0]["evidence"]["days_idle"] >= 180


# ---------------------------------------------------------------------------
# Treasury
# ---------------------------------------------------------------------------
def test_tre_001_flags_large_cash_payment(duck):
    insert(duck, "bank_transactions", id=_id(), company_id=RULES_COMPANY,
           transaction_type="debit", transaction_mode="cash", amount=25000,
           counterparty_name="Cash Vendor", transaction_date=TODAY)
    insert(duck, "bank_transactions", id=_id(), company_id=RULES_COMPANY,
           transaction_type="debit", transaction_mode="cash", amount=5000,
           counterparty_name="Small", transaction_date=TODAY)  # under 10k

    results = run(duck, "TRE-001")

    assert len(results) == 1
    assert results[0]["evidence"]["amount"] == 25000


def test_tre_005_flags_multiple_payments_same_party_same_day(duck):
    for _ in range(3):
        insert(duck, "bank_transactions", id=_id(), company_id=RULES_COMPANY,
               transaction_type="debit", amount=200000,
               counterparty_name="ACME", transaction_date=TODAY)

    results = run(duck, "TRE-005")

    assert len(results) == 1
    assert results[0]["evidence"]["count"] == 3
    assert results[0]["evidence"]["total"] == 600000


# ---------------------------------------------------------------------------
# Payroll
# ---------------------------------------------------------------------------
def test_pay_001_flags_ghost_employee(duck):
    insert(duck, "employees", id="emp-1", company_id=RULES_COMPANY,
           full_name="Ghost", is_active=False)
    insert(duck, "employees", id="emp-2", company_id=RULES_COMPANY,
           full_name="Active", is_active=True)
    insert(duck, "payroll_records", id=_id(), company_id=RULES_COMPANY,
           employee_id="emp-1", net_pay=50000, status="paid")
    insert(duck, "payroll_records", id=_id(), company_id=RULES_COMPANY,
           employee_id="emp-2", net_pay=50000, status="paid")

    results = run(duck, "PAY-001")

    assert len(results) == 1
    assert results[0]["evidence"]["employee_id"] == "emp-1"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
_counter = {"n": 0}


def _id() -> str:
    _counter["n"] += 1
    return f"row-{_counter['n']}"
