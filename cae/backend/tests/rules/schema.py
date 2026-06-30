"""
In-memory DuckDB schema for exercising the SQL audit rules.

The production ``AuditEngine`` loads PostgreSQL data into DuckDB and the rule
callables run raw DuckDB SQL against it.  These tests skip the Postgres hop and
register the same table shapes directly in DuckDB.  Columns are intentionally a
superset covering every column referenced by any rule in ``app.rules`` so that
the "every rule runs" smoke test can execute all of them.  All columns are
nullable so individual tests can insert only the fields they care about.
"""
from __future__ import annotations

import duckdb

RULES_COMPANY = "co-1"
OTHER_COMPANY = "co-2"


_TABLES: dict[str, str] = {
    "sales_invoices": """
        id VARCHAR, company_id VARCHAR, customer_id VARCHAR,
        invoice_number VARCHAR, invoice_date DATE, created_at TIMESTAMP,
        gross_amount DOUBLE, discount_amount DOUBLE, total_amount DOUBLE,
        status VARCHAR, e_way_bill_number VARCHAR, e_invoice_irn VARCHAR,
        erp_source VARCHAR
    """,
    "purchase_invoices": """
        id VARCHAR, company_id VARCHAR, vendor_id VARCHAR,
        invoice_number VARCHAR, our_po_number VARCHAR,
        invoice_date DATE, receipt_date DATE,
        total_amount DOUBLE, paid_amount DOUBLE, status VARCHAR,
        approved_by_user_id VARCHAR, raw_data JSON
    """,
    "journal_entries": """
        id VARCHAR, company_id VARCHAR, voucher_number VARCHAR,
        voucher_type VARCHAR, narration VARCHAR,
        total_debit DOUBLE, total_credit DOUBLE,
        entry_date DATE, posted_at TIMESTAMP,
        is_posted BOOLEAN, is_reversed BOOLEAN,
        reversal_of_id VARCHAR, posted_by_user_id VARCHAR
    """,
    "journal_entry_lines": """
        id VARCHAR, journal_entry_id VARCHAR,
        debit_amount DOUBLE, credit_amount DOUBLE,
        account_code VARCHAR, account_name VARCHAR
    """,
    "bank_transactions": """
        id VARCHAR, company_id VARCHAR, transaction_date TIMESTAMP,
        transaction_type VARCHAR, transaction_mode VARCHAR,
        amount DOUBLE, counterparty_name VARCHAR, description VARCHAR,
        reference_number VARCHAR
    """,
    "inventory_movements": """
        id VARCHAR, company_id VARCHAR, item_code VARCHAR,
        warehouse_from VARCHAR, movement_type VARCHAR, movement_date DATE,
        quantity DOUBLE, total_value DOUBLE, reference_document_number VARCHAR
    """,
    "vendors": """
        id VARCHAR, company_id VARCHAR, name VARCHAR,
        address_line1 VARCHAR, msme_status VARCHAR
    """,
    "employees": """
        id VARCHAR, company_id VARCHAR, full_name VARCHAR,
        is_active BOOLEAN, bank_account_number VARCHAR, date_of_leaving DATE
    """,
    "payroll_records": """
        id VARCHAR, company_id VARCHAR, employee_id VARCHAR,
        net_pay DOUBLE, gross_earnings DOUBLE, status VARCHAR,
        pay_period_year INTEGER, pay_period_month INTEGER,
        pf_employer DOUBLE, pf_employee DOUBLE, esic_employer DOUBLE
    """,
}


def new_connection() -> duckdb.DuckDBPyConnection:
    """Return a fresh in-memory DuckDB connection with all rule tables created."""
    conn = duckdb.connect(":memory:")
    for table, columns in _TABLES.items():
        conn.execute(f"CREATE TABLE {table} ({columns})")
    return conn


def insert(conn: duckdb.DuckDBPyConnection, table: str, **values) -> None:
    """Insert a single row, supplying only the columns given (rest stay NULL)."""
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    conn.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        list(values.values()),
    )
