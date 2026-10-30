"""
AuditEngine: Loads enabled rules, runs them against transaction data using DuckDB for
SQL-based rules and Python callables for complex logic, writes exceptions to DB.
"""
import uuid
import duckdb
import pandas as pd
from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session

from app.models.audit import AuditRule, RuleExecution, AuditException


class AuditEngine:
    def __init__(self, db: Session, company_id: str):
        self.db = db
        self.company_id = company_id
        self.conn = duckdb.connect(":memory:")
        self._data_loaded = False

    def run_all_rules(self, frequency: str = "daily") -> dict:
        """Run all enabled rules for given frequency. Returns summary."""
        rules = self.db.query(AuditRule).filter(
            AuditRule.is_active == True,
            AuditRule.run_frequency == frequency,
            AuditRule.company_id == uuid.UUID(self.company_id),
        ).all()

        # Load data into DuckDB once
        self._load_data_to_duckdb()

        results = {"rules_run": 0, "exceptions_raised": 0, "errors": 0, "rule_details": [],
                   "load_errors": self.load_errors}
        for rule in rules:
            try:
                execution = self._run_rule(rule)
                results["rules_run"] += 1
                results["exceptions_raised"] += execution.exceptions_found or 0
                results["rule_details"].append({
                    "rule_code": rule.rule_code,
                    "status": execution.status,
                    "exceptions": execution.exceptions_found or 0,
                })
            except Exception as e:
                results["errors"] += 1
                results["rule_details"].append({
                    "rule_code": rule.rule_code,
                    "status": "error",
                    "error": str(e),
                })

        return results

    def run_single_rule(self, rule_code: str) -> dict:
        """Run a single rule by code. Useful for on-demand execution."""
        rule = self.db.query(AuditRule).filter(
            AuditRule.rule_code == rule_code,
            AuditRule.is_active == True,
            AuditRule.company_id == uuid.UUID(self.company_id),
        ).first()

        if not rule:
            return {"error": f"Rule {rule_code} not found or disabled"}

        self._load_data_to_duckdb()

        try:
            execution = self._run_rule(rule)
            return {
                "rule_code": rule_code,
                "status": execution.status,
                "exceptions_found": execution.exceptions_found or 0,
            }
        except Exception as e:
            return {"error": str(e), "rule_code": rule_code}

    # table -> SQL selecting this company's rows (bound parameter :cid)
    _TABLES = {
        "sales_invoices": "SELECT * FROM sales_invoices WHERE company_id = :cid",
        "purchase_invoices": "SELECT * FROM purchase_invoices WHERE company_id = :cid",
        "journal_entries": "SELECT * FROM journal_entries WHERE company_id = :cid",
        "journal_entry_lines": """SELECT jel.* FROM journal_entry_lines jel
                                   JOIN journal_entries je ON jel.journal_entry_id = je.id
                                   WHERE je.company_id = :cid""",
        "bank_transactions": "SELECT * FROM bank_transactions WHERE company_id = :cid",
        "inventory_movements": "SELECT * FROM inventory_movements WHERE company_id = :cid",
        "payroll_records": "SELECT * FROM payroll_records WHERE company_id = :cid",
        "employees": "SELECT * FROM employees WHERE company_id = :cid",
        "customers": "SELECT * FROM customers WHERE company_id = :cid",
        "vendors": "SELECT * FROM vendors WHERE company_id = :cid",
        "gl_accounts": "SELECT * FROM gl_accounts WHERE company_id = :cid",
    }

    def _load_data_to_duckdb(self):
        """Load this company's data from PostgreSQL into DuckDB.

        Each DuckDB table is created from the ORM schema, so an empty table or an all-NULL
        column still has the right type (pandas alone would make it INTEGER). UUIDs become
        strings and JSON columns become JSON text, so rules can compare ids with the bound
        company_id and use json_extract_string() on raw_data. A table that fails to load is
        left empty and recorded in self.load_errors."""
        if self._data_loaded:
            return
        from sqlalchemy import text
        from app.database import Base
        import app.models  # noqa: F401 — registers every table on Base.metadata

        self.load_errors: dict[str, str] = {}
        engine = self.db.get_bind()
        for table, sql in self._TABLES.items():
            columns = [(c.name, self._duck_type(c.type)) for c in Base.metadata.tables[table].columns]
            ddl = ", ".join('"%s" %s' % (n, t) for n, t in columns)
            self.conn.execute(f"CREATE OR REPLACE TABLE {table} ({ddl})")
            try:
                df = self._normalise_frame(pd.read_sql(text(sql), engine, params={"cid": self.company_id}))
                if df.empty:
                    continue
                self.conn.register("_load_df", df)
                select = ", ".join('CAST("%s" AS %s)' % (n, t) if n in df.columns else "CAST(NULL AS %s)" % t for n, t in columns)
                self.conn.execute(f"INSERT INTO {table} SELECT {select} FROM _load_df")
                self.conn.unregister("_load_df")
            except Exception as e:
                self.load_errors[table] = str(e)[:200]
        self._data_loaded = True

    @staticmethod
    def _duck_type(sa_type) -> str:
        import sqlalchemy as sa

        if isinstance(sa_type, sa.Boolean):
            return "BOOLEAN"
        if isinstance(sa_type, sa.DateTime):
            return "TIMESTAMP"
        if isinstance(sa_type, sa.Date):
            return "DATE"
        if isinstance(sa_type, sa.Integer):
            return "BIGINT"
        if isinstance(sa_type, (sa.Numeric, sa.Float)):
            return "DOUBLE"
        return "VARCHAR"   # strings, UUIDs, JSON/JSONB, enums

    @staticmethod
    def _normalise_frame(df: pd.DataFrame) -> pd.DataFrame:
        import json
        from decimal import Decimal

        for col in df.columns:
            if df[col].dtype != object:
                continue
            sample = df[col].dropna()
            if sample.empty:
                continue
            first = sample.iloc[0]
            if isinstance(first, uuid.UUID):
                df[col] = df[col].map(lambda v: str(v) if v is not None else None)
            elif isinstance(first, (dict, list)):
                df[col] = df[col].map(lambda v: json.dumps(v, default=str) if v is not None else None)
            elif isinstance(first, Decimal):
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def _run_rule(self, rule: AuditRule) -> RuleExecution:
        """Run a single rule and write exceptions."""
        execution = RuleExecution(
            id=uuid.uuid4(),
            rule_id=rule.id,
            company_id=uuid.UUID(self.company_id),
            started_at=datetime.utcnow(),
            status="running",
            exceptions_found=0,
            exceptions_raised=0,
            triggered_by="api",
        )
        self.db.add(execution)
        self.db.commit()

        try:
            from app.rules import get_rule_fn
            rule_fn = get_rule_fn(rule.rule_code)

            if not rule_fn:
                raise ValueError(f"No implementation registered for rule {rule.rule_code}")
            exceptions_data = rule_fn(self.conn, self.company_id, rule)

            # Write exceptions that don't already exist
            new_count = 0
            for exc_data in exceptions_data:
                title = exc_data.get("title", rule.rule_name)

                # Dedup: same rule + same title + still open
                existing = self.db.query(AuditException).filter(
                    AuditException.company_id == uuid.UUID(self.company_id),
                    AuditException.rule_id == rule.id,
                    AuditException.status.in_(["open", "in_review", "management_query_sent"]),
                    AuditException.title == title
                ).first()

                if not existing:
                    exc = AuditException(
                        id=uuid.uuid4(),
                        company_id=uuid.UUID(self.company_id),
                        rule_id=rule.id,
                        execution_id=execution.id,
                        title=title,
                        description=exc_data.get("description", ""),
                        severity=exc_data.get("severity", rule.severity),
                        category=rule.category,
                        risk_impact=rule.risk_area,
                        financial_impact=exc_data.get("financial_impact"),
                        supporting_data=exc_data.get("evidence", {}),
                        status="open",
                        detected_on=date.today(),
                    )
                    self.db.add(exc)
                    new_count += 1

            self.db.commit()

            execution.status = "completed"
            execution.exceptions_found = new_count
            execution.completed_at = datetime.utcnow()
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            execution.status = "failed"
            execution.error_message = str(e)[:500]
            execution.completed_at = datetime.utcnow()
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
            raise

        return execution

    def test_rule(self, rule: "AuditRule") -> list[dict]:
        """Run a single rule and return matched exceptions without writing to DB."""
        self._load_data_to_duckdb()
        from app.rules import get_rule_fn
        rule_fn = get_rule_fn(rule.rule_code)
        if not rule_fn:
            return []
        try:
            return rule_fn(self.conn, self.company_id, rule)
        except Exception as e:
            return [{"error": str(e)}]

    def close(self):
        """Clean up DuckDB connection."""
        try:
            self.conn.close()
        except Exception:
            pass
