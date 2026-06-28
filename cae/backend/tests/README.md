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
| `engines/test_wc_engine.py` | Working-capital metrics: DSO/DPO/DIO, CCC, stress-score clamping, divide-by-zero guards. |
| `engines/test_risk_engine.py` | Composite risk scoring, band boundaries, 100-cap, tenant isolation. |
| `engines/test_fraud_engine.py` | Benford deviation, duplicate invoices, round-amount concentration, ML anomaly, persistence. |
| `engines/test_gst_engine.py` | GST reconciliation: books turnover/ITC, variances, risk amount, period upsert. |

## Notes

* Covered so far: the pure-logic engines (Priority 1) and auth/RBAC (Priority 3).
  The rules engine (DuckDB SQL rules), data ingestion, and API/route tests are
  intended follow-ups.
* `test_gst_engine.py` is a regression guard: the engine previously queried
  non-existent ORM columns (`taxable_value`, `cgst`, `is_cancelled`) and raised
  `AttributeError` at runtime. It now uses the real columns (`taxable_amount`,
  `cgst_amount`, `status`).
* Test company ids deliberately contain hex letters — SQLite would coerce an
  all-digit UUID string to a float (see `factories.py`).
