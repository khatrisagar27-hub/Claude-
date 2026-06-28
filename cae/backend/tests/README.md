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
| `conftest.py` | Shared `db` fixture (in-memory SQLite) + Postgres→SQLite shims (JSONB→JSON, strips `gen_random_uuid()` defaults). |
| `factories.py` | Builders for transaction / exception rows with sane NOT-NULL defaults. |
| `engines/test_wc_engine.py` | Working-capital metrics: DSO/DPO/DIO, CCC, stress-score clamping, divide-by-zero guards. |
| `engines/test_risk_engine.py` | Composite risk scoring, band boundaries, 100-cap, tenant isolation. |
| `engines/test_fraud_engine.py` | Benford deviation, duplicate invoices, round-amount concentration, ML anomaly, persistence. |
| `engines/test_gst_engine.py` | GST reconciliation: books turnover/ITC, variances, risk amount, period upsert. |

## Notes

* These are the "Priority 1" pure-logic engine tests. API/route, rules-engine,
  auth/RBAC, and ingestion tests are intended follow-ups.
* `test_gst_engine.py` is a regression guard: the engine previously queried
  non-existent ORM columns (`taxable_value`, `cgst`, `is_cancelled`) and raised
  `AttributeError` at runtime. It now uses the real columns (`taxable_amount`,
  `cgst_amount`, `status`).
* Test company ids deliberately contain hex letters — SQLite would coerce an
  all-digit UUID string to a float (see `factories.py`).
