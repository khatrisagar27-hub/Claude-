"""Shared fixtures: an in-memory DuckDB with the CAE table shapes, and a rule stub."""
import sys
from pathlib import Path
from types import SimpleNamespace

import duckdb
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CID = "00000000-0000-0000-0000-000000000001"

# Column types as loaded by AuditEngine (UUIDs as VARCHAR, JSON as text)
SCHEMAS = {
    "sales_invoices": {
        "id": "VARCHAR", "company_id": "VARCHAR", "customer_id": "VARCHAR", "invoice_number": "VARCHAR",
        "invoice_date": "DATE", "due_date": "DATE", "gross_amount": "DOUBLE", "discount_amount": "DOUBLE",
        "taxable_amount": "DOUBLE", "cgst_amount": "DOUBLE", "sgst_amount": "DOUBLE", "igst_amount": "DOUBLE",
        "total_amount": "DOUBLE", "paid_amount": "DOUBLE", "outstanding_amount": "DOUBLE",
        "e_invoice_irn": "VARCHAR", "e_way_bill_number": "VARCHAR", "status": "VARCHAR",
        "erp_source": "VARCHAR", "raw_data": "VARCHAR", "created_at": "TIMESTAMP",
    },
    "purchase_invoices": {
        "id": "VARCHAR", "company_id": "VARCHAR", "vendor_id": "VARCHAR", "invoice_number": "VARCHAR",
        "our_po_number": "VARCHAR", "invoice_date": "DATE", "receipt_date": "DATE", "gross_amount": "DOUBLE",
        "taxable_amount": "DOUBLE", "cgst_amount": "DOUBLE", "sgst_amount": "DOUBLE", "igst_amount": "DOUBLE",
        "tds_amount": "DOUBLE", "tds_section": "VARCHAR", "total_amount": "DOUBLE", "paid_amount": "DOUBLE",
        "outstanding_amount": "DOUBLE", "vendor_gstin": "VARCHAR", "reverse_charge": "BOOLEAN",
        "itc_eligible": "BOOLEAN", "status": "VARCHAR", "approved_by_user_id": "VARCHAR",
        "payment_date": "DATE", "raw_data": "VARCHAR", "created_at": "TIMESTAMP",
    },
    "journal_entries": {
        "id": "VARCHAR", "company_id": "VARCHAR", "voucher_number": "VARCHAR", "entry_date": "DATE",
        "voucher_type": "VARCHAR", "narration": "VARCHAR", "total_debit": "DOUBLE", "total_credit": "DOUBLE",
        "is_posted": "BOOLEAN", "is_reversed": "BOOLEAN", "reversal_of_id": "VARCHAR",
        "posted_by_user_id": "VARCHAR", "posted_at": "TIMESTAMP",
    },
    "journal_entry_lines": {
        "id": "VARCHAR", "journal_entry_id": "VARCHAR", "account_code": "VARCHAR", "account_name": "VARCHAR",
        "debit_amount": "DOUBLE", "credit_amount": "DOUBLE",
    },
    "bank_transactions": {
        "id": "VARCHAR", "company_id": "VARCHAR", "transaction_date": "DATE", "transaction_type": "VARCHAR",
        "amount": "DOUBLE", "description": "VARCHAR", "reference_number": "VARCHAR", "transaction_mode": "VARCHAR",
        "counterparty_name": "VARCHAR", "counterparty_account": "VARCHAR", "utr_number": "VARCHAR",
    },
    "inventory_movements": {
        "id": "VARCHAR", "company_id": "VARCHAR", "movement_date": "DATE", "movement_type": "VARCHAR",
        "item_code": "VARCHAR", "quantity": "DOUBLE", "unit_cost": "DOUBLE", "total_value": "DOUBLE",
        "warehouse_from": "VARCHAR", "warehouse_to": "VARCHAR", "reference_document_number": "VARCHAR",
    },
    "payroll_records": {
        "id": "VARCHAR", "company_id": "VARCHAR", "employee_id": "VARCHAR", "pay_period_year": "INTEGER",
        "pay_period_month": "INTEGER", "gross_earnings": "DOUBLE", "pf_employee": "DOUBLE", "pf_employer": "DOUBLE",
        "esic_employee": "DOUBLE", "esic_employer": "DOUBLE", "net_pay": "DOUBLE", "status": "VARCHAR",
    },
    "employees": {
        "id": "VARCHAR", "company_id": "VARCHAR", "full_name": "VARCHAR", "pan": "VARCHAR",
        "bank_account_number": "VARCHAR", "is_active": "BOOLEAN", "date_of_leaving": "DATE",
    },
    "customers": {
        "id": "VARCHAR", "company_id": "VARCHAR", "name": "VARCHAR", "gstin": "VARCHAR", "credit_limit": "DOUBLE",
    },
    "vendors": {
        "id": "VARCHAR", "company_id": "VARCHAR", "name": "VARCHAR", "gstin": "VARCHAR", "pan": "VARCHAR",
        "msme_status": "VARCHAR", "payment_terms_days": "INTEGER", "bank_account_number": "VARCHAR",
    },
}

DEFAULTS = {
    "sales_invoices": {"company_id": CID, "status": "confirmed", "discount_amount": 0.0, "cgst_amount": 0.0,
                       "sgst_amount": 0.0, "igst_amount": 0.0, "paid_amount": 0.0, "outstanding_amount": 0.0,
                       "erp_source": "erp", "e_way_bill_number": "EWB1", "e_invoice_irn": "IRN1"},
    "purchase_invoices": {"company_id": CID, "status": "pending", "cgst_amount": 0.0, "sgst_amount": 0.0,
                          "igst_amount": 0.0, "tds_amount": 0.0, "paid_amount": 0.0, "outstanding_amount": 0.0,
                          "reverse_charge": False, "itc_eligible": True, "our_po_number": "PO1"},
    "journal_entries": {"company_id": CID, "voucher_type": "journal", "is_posted": True, "is_reversed": False,
                        "narration": "ok"},
    "bank_transactions": {"company_id": CID, "transaction_mode": "NEFT", "reference_number": "R1"},
    "inventory_movements": {"company_id": CID, "warehouse_from": "WH1"},
    "payroll_records": {"company_id": CID, "status": "paid", "pf_employee": 0.0, "pf_employer": 0.0,
                        "esic_employee": 0.0, "esic_employer": 0.0},
    "employees": {"company_id": CID, "is_active": True},
    "customers": {"company_id": CID},
    "vendors": {"company_id": CID},
}


def build_conn(**tables):
    conn = duckdb.connect(":memory:")
    for name, cols in SCHEMAS.items():
        conn.execute(f"CREATE TABLE {name} ({', '.join(f'{c} {t}' for c, t in cols.items())})")
    for name, rows in tables.items():
        if not rows:
            continue
        cols = SCHEMAS[name]
        full = []
        for i, r in enumerate(rows):
            base = {c: None for c in cols}
            base.update(DEFAULTS.get(name, {}))
            base["id"] = f"{name[:3]}-{i:04d}"
            base.update(r)
            full.append(base)
        df = pd.DataFrame(full, columns=list(cols))
        conn.register("_df", df)
        conn.execute(f"INSERT INTO {name} SELECT {', '.join(f'CAST({c} AS {t})' for c, t in cols.items())} FROM _df")
        conn.unregister("_df")
    return conn


def rule(**params):
    return SimpleNamespace(parameters=params or None, threshold_config=None, rule_name="test", severity="medium")


@pytest.fixture
def conn_factory():
    return build_conn
