"""
In-memory DuckDB schema for exercising the SQL audit rules.

The production ``AuditEngine`` loads PostgreSQL data into DuckDB and the rule
callables run raw DuckDB SQL against it.  These tests skip the Postgres hop and
register the same table shapes directly in DuckDB, from ``tests/duckdb_harness.py``
(the shapes AuditEngine loads).  All columns are nullable so individual tests can
insert only the fields they care about.
"""
from __future__ import annotations

import duckdb

RULES_COMPANY = "co-1"
OTHER_COMPANY = "co-2"


def new_connection() -> duckdb.DuckDBPyConnection:
    """Return a fresh in-memory DuckDB connection with every rule table created.

    Built by the shared harness, so the table shapes and the period scoping
    (transaction tables stored as ``<table>_all`` with ``<table>`` an in-period view)
    are the ones AuditEngine creates.
    """
    from tests.duckdb_harness import build_conn

    return build_conn()


def insert(conn: duckdb.DuckDBPyConnection, table: str, **values) -> None:
    """Insert a single row, supplying only the columns given (rest stay NULL)."""
    from datetime import date

    from app.rules import PERIOD_TABLES
    from tests.duckdb_harness import _stored

    # Books dates are NOT NULL in the ORM, and the in-period views drop undated rows.
    if table == "payroll_records":
        values.setdefault("pay_period_year", date.today().year)
        values.setdefault("pay_period_month", date.today().month)
    elif table in PERIOD_TABLES:
        values.setdefault(PERIOD_TABLES[table], date.today())
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    conn.execute(
        f"INSERT INTO {_stored(table)} ({columns}) VALUES ({placeholders})",
        list(values.values()),
    )
