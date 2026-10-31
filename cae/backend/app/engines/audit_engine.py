"""
AuditEngine: Loads enabled rules, runs them against transaction data using DuckDB for
SQL-based rules and Python callables for complex logic, writes exceptions to DB.

With an engagement (Statutory / Internal audit) the run is scoped: only rules in the
engagement's scope run, transaction tables hold rows up to the period end (<table>_all) with
<table> a view of the period itself, ageing tests are aged to the period end, and exceptions
are tagged with — and de-duplicated within — the engagement.
"""
import uuid
from datetime import datetime, date
from types import SimpleNamespace
from typing import Optional

import duckdb
import pandas as pd
from sqlalchemy.orm import Session

from app.models.audit import AuditRule, RuleExecution, AuditException

FREQUENCIES = ("daily", "weekly", "monthly")


class AuditEngine:
    def __init__(self, db: Session, company_id: str, engagement=None):
        self.db = db
        self.company_id = company_id
        self.engagement = engagement
        self.conn = duckdb.connect(":memory:")
        self._data_loaded = False
        self.load_errors: dict[str, str] = {}

    @property
    def engagement_id(self) -> Optional[uuid.UUID]:
        return self.engagement.id if self.engagement is not None else None

    def _rules(self, frequency: Optional[str] = None) -> list[AuditRule]:
        from app.statutory.reporting import in_scope

        q = self.db.query(AuditRule).filter(
            AuditRule.is_active == True,  # noqa: E712
            AuditRule.company_id == uuid.UUID(self.company_id),
        )
        if frequency:
            q = q.filter(AuditRule.run_frequency == frequency)
        return [r for r in q.order_by(AuditRule.rule_code).all() if in_scope(r.rule_code, self.engagement)]

    def run_all_rules(self, frequency: Optional[str] = None) -> dict:
        """Run every enabled, in-scope rule (or only one frequency). Returns a summary."""
        rules = self._rules(frequency)
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
            AuditRule.is_active == True,  # noqa: E712
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
        "users": "SELECT * FROM users WHERE tenant_id = (SELECT tenant_id FROM companies WHERE id = :cid)",
    }
    # Postgres condition keeping rows on or before the period end (``:to``)
    _PERIOD_END_SQL = {
        "sales_invoices": "invoice_date <= :to",
        "purchase_invoices": "invoice_date <= :to",
        "journal_entries": "entry_date <= :to",
        "journal_entry_lines": "je.entry_date <= :to",
        "bank_transactions": "transaction_date <= :to",
        "inventory_movements": "movement_date <= :to",
        "payroll_records": "make_date(pay_period_year, pay_period_month, 1) <= :to",
    }

    def _load_data_to_duckdb(self):
        """Load this company's data from PostgreSQL into DuckDB.

        Each DuckDB table is created from the ORM schema, so an empty table or an all-NULL
        column still has the right type (pandas alone would make it INTEGER). UUIDs become
        strings and JSON columns become JSON text, so rules can compare ids with the bound
        company_id and use json_extract_string() on raw_data. A table that fails to load is
        left empty and recorded in self.load_errors.

        Transaction tables land as <table>_all (rows up to the engagement's period end, or
        everything) and <table> becomes a view of the period — see app.rules.apply_period."""
        if self._data_loaded:
            return
        from sqlalchemy import text
        from app.database import Base
        from app.rules import PERIOD_TABLES, apply_period
        import app.models  # noqa: F401 — registers every table on Base.metadata

        self.load_errors = {}
        engine = self.db.get_bind()
        period_to = self.engagement.period_to if self.engagement is not None else None
        for table, sql in self._TABLES.items():
            stored = f"{table}_all" if table in PERIOD_TABLES or table == "journal_entry_lines" else table
            columns = [(c.name, self._duck_type(c.type)) for c in Base.metadata.tables[table].columns
                       if not (table == "users" and c.name == "password_hash")]
            ddl = ", ".join('"%s" %s' % (n, t) for n, t in columns)
            self.conn.execute(f"CREATE OR REPLACE TABLE {stored} ({ddl})")
            params = {"cid": self.company_id}
            if period_to is not None and table in self._PERIOD_END_SQL:
                sql = f"{sql} AND {self._PERIOD_END_SQL[table]}"
                params["to"] = period_to
            try:
                df = self._normalise_frame(pd.read_sql(text(sql), engine, params=params))
                if df.empty:
                    continue
                self.conn.register("_load_df", df)
                select = ", ".join('CAST("%s" AS %s)' % (n, t) if n in df.columns else "CAST(NULL AS %s)" % t for n, t in columns)
                self.conn.execute(f"INSERT INTO {stored} SELECT {select} FROM _load_df")
                self.conn.unregister("_load_df")
            except Exception as e:
                self.load_errors[table] = str(e)[:200]
        apply_period(self.conn,
                     self.engagement.period_from if self.engagement is not None else None,
                     period_to)
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

    def _runtime_rule(self, rule: AuditRule):
        """The rule as the rule function sees it: inside an engagement, ageing tests are aged to
        the period end unless the rule fixes its own as_on. Nothing here is written back."""
        params = dict(rule.parameters or {})
        if self.engagement is not None:
            params.setdefault("as_on", self.engagement.period_to.isoformat())
            params["period_from"] = self.engagement.period_from.isoformat()
            params["period_to"] = self.engagement.period_to.isoformat()
        return SimpleNamespace(parameters=params, threshold_config=rule.threshold_config, rule_code=rule.rule_code,
                               rule_name=rule.rule_name, severity=rule.severity, category=rule.category)

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
            triggered_by="engagement" if self.engagement is not None else "api",
            period_start=self.engagement.period_from if self.engagement is not None else None,
            period_end=self.engagement.period_to if self.engagement is not None else None,
        )
        self.db.add(execution)
        self.db.commit()

        try:
            from app.rules import get_rule_fn
            rule_fn = get_rule_fn(rule.rule_code)

            if not rule_fn:
                raise ValueError(f"No implementation registered for rule {rule.rule_code}")
            exceptions_data = rule_fn(self.conn, self.company_id, self._runtime_rule(rule))

            # Still-open exceptions of this rule in the same engagement (or outside any) — skip repeats
            scope = (AuditException.engagement_id.is_(None) if self.engagement is None
                     else AuditException.engagement_id == self.engagement_id)
            open_titles = {
                t for (t,) in self.db.query(AuditException.title).filter(
                    AuditException.company_id == uuid.UUID(self.company_id),
                    AuditException.rule_id == rule.id,
                    scope,
                    AuditException.status.in_(["open", "in_review", "management_query_sent", "remediation_in_progress"]),
                ).all()
            }
            new_count = 0
            for exc_data in exceptions_data:
                title = exc_data.get("title", rule.rule_name)[:300]
                if title in open_titles:
                    continue
                open_titles.add(title)
                self.db.add(AuditException(
                    id=uuid.uuid4(),
                    company_id=uuid.UUID(self.company_id),
                    rule_id=rule.id,
                    execution_id=execution.id,
                    engagement_id=self.engagement_id,
                    title=title,
                    description=exc_data.get("description", ""),
                    severity=exc_data.get("severity", rule.severity),
                    category=rule.category,
                    risk_impact=rule.risk_area,
                    financial_impact=exc_data.get("financial_impact"),
                    supporting_data=exc_data.get("evidence", {}),
                    status="open",
                    detected_on=date.today(),
                ))
                new_count += 1

            self.db.commit()

            execution.status = "completed"
            execution.exceptions_found = new_count
            execution.records_scanned = len(exceptions_data)
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
            return rule_fn(self.conn, self.company_id, self._runtime_rule(rule))
        except Exception as e:
            return [{"error": str(e)}]

    def close(self):
        """Clean up DuckDB connection."""
        try:
            self.conn.close()
        except Exception:
            pass
