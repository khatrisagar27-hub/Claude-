# CAE backend tests

Unit tests for the business-logic engines. They run against an in-memory SQLite
database (no Postgres/Redis required), so the suite is fast and self-contained.

## Running

```bash
cd cae/backend
pip install -r requirements-dev.txt
pytest
```

## Layout

| Path | What it covers |
| --- | --- |
| `conftest.py` | Shared `db` fixture (in-memory SQLite) + Postgres→SQLite shims (JSONB→JSON, strips `gen_random_uuid()` defaults, string-tolerant UUID binds). |
| `factories.py` | Builders for transaction / exception / user rows with sane NOT-NULL defaults. |
| `test_security.py` | Password hashing (salt, round-trip, rejection) and JWT create/verify (type, expiry, bad signature). |
| `test_rbac.py` | `get_current_user` (valid/expired/garbage/no-sub/unknown/inactive, refresh-as-access rejection) and role enforcement. |
| `rules/` | SQL audit rules run against in-memory DuckDB. `schema.py` builds the table shapes; `test_registry.py` checks the registry and **executes every registered rule against an empty schema** (SQL-validity net); `test_rules.py` asserts representative rules across all six modules (sales/purchase/journal/inventory/treasury/payroll). |
| `test_excel_importer.py` | ExcelImporter: column mapping + aliases, CSV/XLSX dispatch, unknown-type rejection, batch resilience to bad rows, per-type mappers. |
| `test_tally_connector.py` | TallyConnector: XML voucher parsing, debit/credit split, thousands separators, multi-voucher counting, date fallback. |
| `engines/test_audit_engine.py` | AuditEngine constructor: company_id UUID validation / SQL-injection guard. |
| `api/` | HTTP integration over the real FastAPI app via `TestClient` with real JWTs (`conftest.py` provides the `api` harness): health, login/refresh/me + auth-stack rejection, `/companies` (tenant scoping + role gates), `/exceptions` (listing/filtering/pagination/status transitions), `/dashboard` KPIs. |
| `engines/test_wc_engine.py` | Working-capital metrics: DSO/DPO/DIO, CCC, stress-score clamping, divide-by-zero guards. |
| `engines/test_risk_engine.py` | Composite risk scoring, band boundaries, 100-cap, tenant isolation. |
| `engines/test_fraud_engine.py` | Benford deviation, duplicate invoices, round-amount concentration, ML anomaly, persistence. |
| `engines/test_gst_engine.py` | GST reconciliation: books turnover/ITC, variances, risk amount, period upsert. |

## Notes

* Covered so far: the pure-logic engines (Priority 1), the DuckDB rules engine
  (Priority 2), auth/RBAC (Priority 3), data ingestion (Priority 4), and HTTP/API
  integration (Priority 5). Remaining route modules (gst/queries/remediation/
  reports/ingestion/rules/risk) and the AuditEngine data-load path are follow-ups
  (the latter needs a Postgres-backed fixture — see below).
* `CompanyOut` declared `id`/`tenant_id` as `str` but the ORM yields `uuid.UUID`,
  so `/companies` endpoints raised `ResponseValidationError` (HTTP 500). Retyped
  to `UUID`; `tests/api/test_companies.py` guards it.
* `AuditEngine._load_data_to_duckdb` interpolates `company_id` into SQL via an
  f-string. The constructor now validates it is a UUID (injection guard). The
  full data-load/tenant-isolation path is intentionally not tested on SQLite: the
  emulated UUID type stores values without hyphens, so the hyphenated f-string
  filter would never match — a SQLite artifact, not production behaviour.
* The rules smoke test is a regression net: `INV-005` previously raised a DuckDB
  `BinderException` (`CURRENT_DATE` in a grouped query) and failed on every run;
  it was rewritten to group in a subquery and now has a behavioural guard.
* `TallyConnector` previously built `JournalEntry` with non-existent fields
  (`je_no`/`je_date`/`period`/`je_type`/`source_system`) and omitted the required
  `total_credit`, so every voucher raised and nothing imported. Fixed to the real
  columns; `test_tally_connector.py` guards it.
* `test_gst_engine.py` is a regression guard: the engine previously queried
  non-existent ORM columns (`taxable_value`, `cgst`, `is_cancelled`) and raised
  `AttributeError` at runtime. It now uses the real columns (`taxable_amount`,
  `cgst_amount`, `status`).
* Test company ids deliberately contain hex letters — SQLite would coerce an
  all-digit UUID string to a float (see `factories.py`).
