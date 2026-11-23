"""Rule registry — maps rule_code strings to Python callables, plus shared helpers."""
from datetime import date, datetime
from typing import Any, Callable, Optional


_REGISTRY: dict[str, Callable] = {}


def register(rule_code: str):
    def decorator(fn: Callable) -> Callable:
        _REGISTRY[rule_code] = fn
        return fn
    return decorator


def get_rule_fn(rule_code: str) -> Optional[Callable]:
    return _REGISTRY.get(rule_code)


def registered_codes() -> set[str]:
    return set(_REGISTRY)


def param(rule, key: str, default: Any) -> Any:
    """Read a tunable from rule.parameters, then rule.threshold_config, else the default."""
    for attr in ("parameters", "threshold_config"):
        cfg = getattr(rule, attr, None) or {}
        if isinstance(cfg, dict) and cfg.get(key) is not None:
            return cfg[key]
    return default


def capped(out: list, rule) -> list:
    """Audit populations are reported in full. Only an explicit max_results parameter trims
    the list — never a silent default (a capped list understated exposure and risk)."""
    n = param(rule, "max_results", None)
    return out[: int(n)] if n else out


# Transaction tables and the date that places a row in a period. The engine loads each as
# <table>_all (every row up to the period end) and exposes <table> as a view of the rows
# inside the period. Transaction tests read <table>; balance and cumulative tests (stock on
# hand, MSME dues, FY-to-date thresholds, duplicates within a FY) read <table>_all.
PERIOD_TABLES = {
    "sales_invoices": "invoice_date",
    "purchase_invoices": "invoice_date",
    "journal_entries": "entry_date",
    "bank_transactions": "transaction_date",
    "inventory_movements": "movement_date",
    "payroll_records": "MAKE_DATE(CAST(pay_period_year AS INTEGER), CAST(pay_period_month AS INTEGER), 1)",
}


def apply_period(conn, period_from=None, period_to=None) -> None:
    """(Re)create the in-period views over the loaded <table>_all tables."""
    lo = f"DATE '{as_date(period_from)}'" if period_from else "DATE '1900-01-01'"
    hi = f"DATE '{as_date(period_to)}'" if period_to else "DATE '9999-12-31'"
    for table, col in PERIOD_TABLES.items():
        conn.execute(f"CREATE OR REPLACE VIEW {table} AS SELECT * FROM {table}_all WHERE {col} BETWEEN {lo} AND {hi}")
    conn.execute("""CREATE OR REPLACE VIEW journal_entry_lines AS
                    SELECT l.* FROM journal_entry_lines_all l JOIN journal_entries je ON je.id = l.journal_entry_id""")


def fy_sql(col: str) -> str:
    """DuckDB expression for the Indian financial year (Apr-Mar) start year of a date column."""
    return f"(CASE WHEN MONTH({col}) >= 4 THEN YEAR({col}) ELSE YEAR({col}) - 1 END)"


def bulk_load_days_sql(table: str, date_col: str) -> str:
    """Subquery of created_at dates that look like a bulk import rather than day-to-day entry:
    rows created that day span more than :months invoice months. created_at on an imported
    row is the import date, not the books entry date, so entry-timing rules skip those days.
    Binds two parameters: company_id, months."""
    return f"""(SELECT CAST(created_at AS DATE) FROM {table}
               WHERE company_id = ? AND created_at IS NOT NULL
               GROUP BY 1 HAVING COUNT(DISTINCT DATE_TRUNC('month', {date_col})) > ?)"""


def as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def as_on_date(conn, rule, table: str, col: str) -> date:
    """Reference date for ageing tests: rule parameter 'as_on', else the latest date in the
    data (so a historical data set is not aged against today), else today."""
    explicit = param(rule, "as_on", None)
    if explicit:
        return as_date(explicit)
    try:
        row = conn.execute(f"SELECT MAX(CAST({col} AS DATE)) FROM {table}").fetchone()
        if row and row[0]:
            return as_date(row[0])
    except Exception:
        pass
    return date.today()


# Import all rule modules to trigger registration
from app.rules import (  # noqa: F401, E402
    sales_rules, purchase_rules, inventory_rules, journal_rules, payroll_rules,
    treasury_rules, gst_rules, tds_rules,
)
