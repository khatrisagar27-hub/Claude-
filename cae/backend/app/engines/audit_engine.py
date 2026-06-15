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
from app.models.transaction import SalesInvoice, PurchaseInvoice, JournalEntry
from app.database import SessionLocal


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

        results = {"rules_run": 0, "exceptions_raised": 0, "errors": 0, "rule_details": []}
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

    def _load_data_to_duckdb(self):
        """Load transaction data from PostgreSQL into DuckDB for fast analytics."""
        if self._data_loaded:
            return

        try:
            engine = self.db.get_bind()

            # Load sales invoices
            try:
                sales_df = pd.read_sql(
                    f"SELECT * FROM sales_invoices WHERE company_id = '{self.company_id}'",
                    engine
                )
                if not sales_df.empty:
                    self.conn.register("sales_invoices", sales_df)
                else:
                    self.conn.execute(
                        "CREATE TABLE IF NOT EXISTS sales_invoices (id VARCHAR, company_id VARCHAR)"
                    )
            except Exception:
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS sales_invoices (id VARCHAR, company_id VARCHAR)"
                )

            # Load purchase invoices
            try:
                purchase_df = pd.read_sql(
                    f"SELECT * FROM purchase_invoices WHERE company_id = '{self.company_id}'",
                    engine
                )
                if not purchase_df.empty:
                    self.conn.register("purchase_invoices", purchase_df)
                else:
                    self.conn.execute(
                        "CREATE TABLE IF NOT EXISTS purchase_invoices (id VARCHAR, company_id VARCHAR)"
                    )
            except Exception:
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS purchase_invoices (id VARCHAR, company_id VARCHAR)"
                )

            # Load journal entries
            try:
                je_df = pd.read_sql(
                    f"SELECT * FROM journal_entries WHERE company_id = '{self.company_id}'",
                    engine
                )
                if not je_df.empty:
                    self.conn.register("journal_entries", je_df)
                else:
                    self.conn.execute(
                        "CREATE TABLE IF NOT EXISTS journal_entries (id VARCHAR, company_id VARCHAR)"
                    )
            except Exception:
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS journal_entries (id VARCHAR, company_id VARCHAR)"
                )

            # Load journal entry lines
            try:
                jel_df = pd.read_sql(
                    f"""SELECT jel.* FROM journal_entry_lines jel
                        JOIN journal_entries je ON jel.journal_entry_id = je.id
                        WHERE je.company_id = '{self.company_id}'""",
                    engine
                )
                if not jel_df.empty:
                    self.conn.register("journal_entry_lines", jel_df)
                else:
                    self.conn.execute(
                        "CREATE TABLE IF NOT EXISTS journal_entry_lines (id VARCHAR, journal_entry_id VARCHAR)"
                    )
            except Exception:
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS journal_entry_lines (id VARCHAR, journal_entry_id VARCHAR)"
                )

            # Load bank transactions
            try:
                bank_df = pd.read_sql(
                    f"SELECT * FROM bank_transactions WHERE company_id = '{self.company_id}'",
                    engine
                )
                if not bank_df.empty:
                    self.conn.register("bank_transactions", bank_df)
                else:
                    self.conn.execute(
                        "CREATE TABLE IF NOT EXISTS bank_transactions (id VARCHAR, company_id VARCHAR)"
                    )
            except Exception:
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS bank_transactions (id VARCHAR, company_id VARCHAR)"
                )

            # Load inventory movements
            try:
                inv_df = pd.read_sql(
                    f"SELECT * FROM inventory_movements WHERE company_id = '{self.company_id}'",
                    engine
                )
                if not inv_df.empty:
                    self.conn.register("inventory_movements", inv_df)
                else:
                    self.conn.execute(
                        "CREATE TABLE IF NOT EXISTS inventory_movements (id VARCHAR, company_id VARCHAR)"
                    )
            except Exception:
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS inventory_movements (id VARCHAR, company_id VARCHAR)"
                )

            # Load payroll records
            try:
                payroll_df = pd.read_sql(
                    f"SELECT * FROM payroll_records WHERE company_id = '{self.company_id}'",
                    engine
                )
                if not payroll_df.empty:
                    self.conn.register("payroll_records", payroll_df)
                else:
                    self.conn.execute(
                        "CREATE TABLE IF NOT EXISTS payroll_records (id VARCHAR, company_id VARCHAR)"
                    )
            except Exception:
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS payroll_records (id VARCHAR, company_id VARCHAR)"
                )

            # Load employees
            try:
                emp_df = pd.read_sql(
                    f"SELECT * FROM employees WHERE company_id = '{self.company_id}'",
                    engine
                )
                if not emp_df.empty:
                    self.conn.register("employees", emp_df)
                else:
                    self.conn.execute(
                        "CREATE TABLE IF NOT EXISTS employees (id VARCHAR, company_id VARCHAR)"
                    )
            except Exception:
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS employees (id VARCHAR, company_id VARCHAR)"
                )

            # Load customers
            try:
                cust_df = pd.read_sql(
                    f"SELECT * FROM customers WHERE company_id = '{self.company_id}'",
                    engine
                )
                if not cust_df.empty:
                    self.conn.register("customers", cust_df)
                else:
                    self.conn.execute(
                        "CREATE TABLE IF NOT EXISTS customers (id VARCHAR, company_id VARCHAR)"
                    )
            except Exception:
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS customers (id VARCHAR, company_id VARCHAR)"
                )

            # Load vendors
            try:
                vendor_df = pd.read_sql(
                    f"SELECT * FROM vendors WHERE company_id = '{self.company_id}'",
                    engine
                )
                if not vendor_df.empty:
                    self.conn.register("vendors", vendor_df)
                else:
                    self.conn.execute(
                        "CREATE TABLE IF NOT EXISTS vendors (id VARCHAR, company_id VARCHAR)"
                    )
            except Exception:
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS vendors (id VARCHAR, company_id VARCHAR)"
                )

            # Load GL accounts
            try:
                gl_df = pd.read_sql(
                    f"SELECT * FROM gl_accounts WHERE company_id = '{self.company_id}'",
                    engine
                )
                if not gl_df.empty:
                    self.conn.register("gl_accounts", gl_df)
                else:
                    self.conn.execute(
                        "CREATE TABLE IF NOT EXISTS gl_accounts (id VARCHAR, company_id VARCHAR)"
                    )
            except Exception:
                self.conn.execute(
                    "CREATE TABLE IF NOT EXISTS gl_accounts (id VARCHAR, company_id VARCHAR)"
                )

            self._data_loaded = True

        except Exception as e:
            # Ensure basic tables exist even on complete failure
            for table in ["sales_invoices", "purchase_invoices", "journal_entries",
                          "journal_entry_lines", "bank_transactions", "inventory_movements",
                          "payroll_records", "employees", "customers", "vendors", "gl_accounts"]:
                try:
                    self.conn.execute(
                        f"CREATE TABLE IF NOT EXISTS {table} (id VARCHAR, company_id VARCHAR)"
                    )
                except Exception:
                    pass
            self._data_loaded = True

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

            if rule_fn:
                exceptions_data = rule_fn(self.conn, self.company_id, rule)
            else:
                exceptions_data = []

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
