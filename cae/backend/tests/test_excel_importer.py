"""Tests for ExcelImporter — parsing uploaded files into transaction rows."""
from datetime import date

import pandas as pd
import pytest

from app.connectors.excel_importer import ExcelImporter
from app.models.transaction import (
    BankTransaction,
    InventoryMovement,
    JournalEntry,
    PayrollRecord,
    PurchaseInvoice,
    SalesInvoice,
)
from tests.factories import COMPANY_ID


def _importer(db):
    return ExcelImporter(db, str(COMPANY_ID))


# ---------------------------------------------------------------------------
# Sales mapping
# ---------------------------------------------------------------------------
def test_import_sales_maps_canonical_columns(db):
    df = pd.DataFrame([{
        "invoice_number": "INV-1",
        "invoice_date": "2024-03-15",
        "gross_amount": 1180,
        "taxable_amount": 1000,
        "cgst_amount": 90,
        "sgst_amount": 90,
        "total_amount": 1180,
        "outstanding_amount": 1180,
        "status": "confirmed",
    }])

    result = _importer(db)._import_sales(df)

    assert result["rows_imported"] == 1
    inv = db.query(SalesInvoice).one()
    assert inv.invoice_number == "INV-1"
    assert inv.invoice_date == date(2024, 3, 15)
    assert float(inv.taxable_amount) == 1000
    assert float(inv.cgst_amount) == 90
    assert inv.company_id == COMPANY_ID


def test_import_sales_accepts_alternate_column_names(db):
    """invoice_no / taxable_value / cgst aliases and defaulted fields."""
    df = pd.DataFrame([{
        "invoice_no": "INV-2",
        "invoice_date": "2024-03-15",
        "total_value": 500,        # -> total_amount
        "taxable_value": 450,      # -> taxable_amount
        "cgst": 25,                # -> cgst_amount
    }])

    _importer(db)._import_sales(df)

    inv = db.query(SalesInvoice).one()
    assert inv.invoice_number == "INV-2"
    assert float(inv.total_amount) == 500
    assert float(inv.taxable_amount) == 450
    assert float(inv.cgst_amount) == 25
    # outstanding defaults to total; erp_source defaults to excel_import
    assert float(inv.outstanding_amount) == 500
    assert inv.erp_source == "excel_import"


def test_import_sales_continues_after_bad_rows(db):
    """A row that triggers an error must not abort the rest of the batch."""
    df = pd.DataFrame([
        {"invoice_number": "GOOD-1", "invoice_date": "2024-03-15", "total_amount": 100},
        {"invoice_number": "BAD", "invoice_date": "2024-03-15",
         "customer_id": "not-a-uuid", "total_amount": "abc"},  # unparseable amount -> 0, bad uuid -> None
        {"invoice_number": "GOOD-2", "invoice_date": "2024-03-15", "total_amount": 200},
    ])

    result = _importer(db)._import_sales(df)

    # All three are resilient (helpers swallow bad values), so all import.
    assert result["rows_imported"] == 3
    assert db.query(SalesInvoice).count() == 3


# ---------------------------------------------------------------------------
# Dispatch via import_file
# ---------------------------------------------------------------------------
def test_import_file_dispatches_csv_by_type(db, tmp_path):
    csv = tmp_path / "purchases.csv"
    csv.write_text("invoice_number,invoice_date,total_amount\nB-1,2024-03-15,1000\n")

    result = _importer(db).import_file(str(csv), "purchase_invoices")

    assert result["rows_imported"] == 1
    assert db.query(PurchaseInvoice).one().invoice_number == "B-1"


def test_import_file_reads_xlsx(db, tmp_path):
    xlsx = tmp_path / "sales.xlsx"
    pd.DataFrame([{"invoice_number": "X-1", "invoice_date": "2024-03-15",
                   "total_amount": 750}]).to_excel(xlsx, index=False)

    result = _importer(db).import_file(str(xlsx), "sales_invoices")

    assert result["rows_imported"] == 1
    assert float(db.query(SalesInvoice).one().total_amount) == 750


def test_import_file_rejects_unknown_type(db, tmp_path):
    csv = tmp_path / "x.csv"
    csv.write_text("a,b\n1,2\n")

    result = _importer(db).import_file(str(csv), "not_a_real_type")

    assert result["rows_imported"] == 0
    assert "Unknown file type" in result["error"]


# ---------------------------------------------------------------------------
# Journal entries default total_credit to total_debit
# ---------------------------------------------------------------------------
def test_import_journal_defaults_credit_to_debit(db):
    df = pd.DataFrame([{
        "voucher_number": "JV-1", "entry_date": "2024-03-15",
        "voucher_type": "journal", "total_debit": 5000,
    }])

    _importer(db)._import_journal_entries(df)

    je = db.query(JournalEntry).one()
    assert float(je.total_debit) == 5000
    assert float(je.total_credit) == 5000


# ---------------------------------------------------------------------------
# Bank & inventory mapping (alternate column names)
# ---------------------------------------------------------------------------
def test_import_bank_maps_alternate_columns(db):
    df = pd.DataFrame([{
        "txn_date": "2024-03-15", "amount": 9000, "txn_type": "debit",
        "party_name": "ACME", "channel": "NEFT", "narration": "settlement",
    }])

    result = _importer(db)._import_bank(df)

    assert result["rows_imported"] == 1
    bt = db.query(BankTransaction).one()
    assert bt.transaction_type == "debit"
    assert bt.counterparty_name == "ACME"
    assert bt.transaction_mode == "NEFT"
    assert bt.description == "settlement"


def test_import_inventory_maps_alternate_columns(db):
    df = pd.DataFrame([{
        "material_code": "WIDGET", "movement_date": "2024-03-15",
        "movement_type": "goods_receipt", "quantity": 10, "unit": "KG",
        "value": 5000,
    }])

    result = _importer(db)._import_inventory(df)

    assert result["rows_imported"] == 1
    mv = db.query(InventoryMovement).one()
    assert mv.item_code == "WIDGET"
    assert mv.unit_of_measure == "KG"
    assert float(mv.total_value) == 5000


# ---------------------------------------------------------------------------
# Payroll: rows missing employee_id are skipped, others import
# ---------------------------------------------------------------------------
def test_import_payroll_skips_rows_missing_employee_id(db):
    import uuid
    good_emp = str(uuid.uuid4())
    df = pd.DataFrame([
        {"employee_id": good_emp, "pay_period_year": 2024, "pay_period_month": 3,
         "gross_earnings": 50000, "total_deductions": 5000, "net_pay": 45000},
        {"pay_period_year": 2024, "pay_period_month": 3,  # no employee_id -> KeyError -> skipped
         "gross_earnings": 50000, "total_deductions": 5000, "net_pay": 45000},
    ])

    result = _importer(db)._import_payroll(df)

    assert result["rows_imported"] == 1
    assert len(result["errors"]) == 1
    assert db.query(PayrollRecord).count() == 1


# ---------------------------------------------------------------------------
# Helper behaviour
# ---------------------------------------------------------------------------
def test_get_str_treats_nan_as_none():
    assert ExcelImporter._get_str(pd.Series({"k": float("nan")}), "k") is None
    assert ExcelImporter._get_str(pd.Series({"k": "v"}), "k") == "v"


def test_parse_date_falls_back_to_today_on_garbage():
    assert ExcelImporter._parse_date("not-a-date") == date.today()


def test_decimal_falls_back_to_zero_on_garbage():
    from decimal import Decimal
    assert ExcelImporter._decimal("abc") == Decimal("0")
    assert ExcelImporter._decimal("12.5") == Decimal("12.5")
