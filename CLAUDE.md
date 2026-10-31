# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.
User-facing docs live in [README.md](README.md); this file covers what you need
to *change* the code.

## What's in here

Two unrelated projects share this repo:

1. **`cae/` — Continuous Audit Engine.** FastAPI + Postgres + Redis/Celery +
   React, Docker Compose. The substantial project; assume a task is about this
   one unless LexComply is named.
2. **Repo root — LexComply India.** Dependency-free static web app
   (`index.html` + `laws.js` + `app.js` + `excel-export.js`) plus an Excel
   workbook generator (`build_excel.py` → `LexComply_India.xlsm`, with
   `LexComply.bas` imported by hand). No build step, no package manager, no
   framework. Don't introduce one.

## Build & run commands

All CAE commands run from `cae/` via the Makefile:

| Task | Command |
|---|---|
| Build images | `make build` |
| Start stack | `make up` |
| Apply migrations | `make migrate` (the backend also runs `alembic upgrade head` on boot) |
| Load demo data | `make seed` |
| Run first audit pass | `make audit` |
| Tail backend + worker logs | `make logs` |
| Shell into backend / psql | `make shell-backend` / `make shell-db` |
| Stop / wipe volumes | `make down` / `make clean` |

Frontend (from `cae/frontend/`): `npm run dev`, `npm run build`,
`npm run lint` (eslint over `src`). Type-check via `npx tsc --noEmit`.

Ports: nginx 8080 (use this) · frontend 3000 · API 8000 (`/api/docs`) ·
Grafana 3001 · Prometheus 9090 · Postgres 5432 · Redis 6379.

LexComply: open `index.html` directly in a browser; `python build_excel.py` to
regenerate the workbook.

## Tests

Backend tests live in `cae/backend/tests/` (pytest; `pip install -r
requirements-dev.txt`). Run from `cae/backend/`:

| Suite | Command | Needs |
|---|---|---|
| Rules + statutory + engagement units | `python -m pytest tests/test_rules.py tests/test_statutory.py tests/test_engagement.py -q` | nothing — in-memory DuckDB |
| End to end | `python -m pytest tests/test_integration_pg.py -q` | `pgserver` (embedded Postgres) — no Docker |

The end-to-end suite migrates a throwaway Postgres, runs `scripts/seed_data.py`
and `scripts/run_first_audit.py`, asserts all catalogue rules run with zero
errors, then drives the API through `TestClient`. Run it on its own process (it
sets `DATABASE_URL` before the app is imported). Every new rule needs a
fire / don't-fire pair in `test_rules.py`. No frontend tests and no CI yet.

## Architecture

### Request path

`nginx` (8080) → React SPA (`frontend`) and `/api/*` → FastAPI (`backend`).
`app/main.py` mounts `app/api/v1/router.py` under `/api/v1`; that router
aggregates one module per domain (`auth`, `companies`, `ingestion`, `rules`,
`exceptions`, `queries`, `remediation`, `risk`, `gst`, `dashboard`, `reports`,
`working_capital`, `statutory`, `engagements`, `tally`). Adding a domain means:
new module in `app/api/v1/`, then register it in `router.py`.

### Engagements — Statutory vs Internal audit

`app/models/engagement.py` (`audit_engagements`): one audit of one company — a
**Statutory** audit of a financial year (period forced to 1 Apr–31 Mar, CARO /
IFC / tax-audit flags, SA 320 materiality) or an **Internal** audit of any
period. `audit_exceptions.engagement_id` and `sync_jobs.engagement_id` scope
everything: NULL = continuous monitoring outside any engagement. Every screen
and report takes `engagement_id`; without it they show continuous monitoring
only (`app/utils/engagement.py: exception_scope`), so audits never mix.

`app/statutory/reporting.py` is the single source of truth for *where a rule's
findings land*: per rule a `process` (internal audit), a `scope`
(`statutory` / `ifc` = statutory only when IFC applies / `internal` only) and
reporting `refs` (CARO 2020 clause, Form 3CD clause, IFC, SA / law). A test
fails if a catalogue rule is missing there. Reports: `app/utils/engagement_export.py`
(statutory working paper with CARO / tax-audit matrices + IFC sheet; internal
audit report with process summary, observations, management response, action
plan; PDF for both).

### The audit engine — Postgres for state, DuckDB for analysis

This is the central design fact. `app/engines/audit_engine.py` opens an
**in-memory DuckDB** connection, and `_load_data_to_duckdb()` pulls each
relevant table out of Postgres via `pandas.read_sql` and registers it as a
DuckDB table. Rules then run as plain analytical SQL against DuckDB.

Consequences to respect:

- Rule SQL is **DuckDB dialect** with `?` positional params — not SQLAlchemy,
  not Postgres. DuckDB day codes differ: use `ISODOW()` (Mon=1..Sun=7), never
  `DAYOFWEEK()` (Sun=0).
- A rule can only query tables listed in `AuditEngine._TABLES`. Needing a new
  table means adding it there first.
- Each DuckDB table is created from the ORM schema (`_duck_type`), then filled.
  Don't go back to `CREATE TABLE AS SELECT * FROM df`: an all-NULL column then
  becomes INTEGER and `TRIM()` / `DATEDIFF()` on it fails — that broke 8 rules
  on real data. UUIDs arrive as VARCHAR, JSON as text (`json_extract_string`).
- Every rule run reloads the company's data. Keep that in mind before adding
  per-rule loads.
- **Period scoping.** Transaction tables (`PERIOD_TABLES` in `app/rules/__init__.py`)
  load as `<table>_all` — every row up to the engagement's period end — and
  `<table>` is a **view** of the period itself (`apply_period`). Transaction
  tests read `<table>`; balance / cumulative tests (stock on hand, MSME dues,
  credit exposure, FY-to-date TDS threshold, duplicates within a FY, suspense
  balance) read `<table>_all`. Without an engagement the two are identical.
  Inside an engagement the engine injects `as_on` = period end (and
  `period_from` / `period_to`) into a runtime copy of the rule — never saved.
- **Never truncate a population.** No `LIMIT` in rule SQL and no `out[:50]`;
  `capped(out, rule)` trims only when a rule sets `max_results`. Capped lists
  understated exposure, risk scores and reports (fixed 31-10-2026).
- `AuditEngine.run_all_rules()` with no frequency runs **every** active rule;
  the UI / worker path used to run only the daily ones.

### Rule registry

`app/rules/__init__.py` is a decorator registry: `@register("SAL-001")` maps a
rule code to a callable, and the module's tail imports every rule module to
trigger registration. Rule packs are `sales_rules`, `purchase_rules`,
`inventory_rules`, `journal_rules`, `payroll_rules`, `treasury_rules`,
`gst_rules`, `tds_rules`.

A rule is `fn(conn, company_id, rule)` returning a **list of exception dicts**
with keys `title`, `description`, `severity`, `financial_impact`, `evidence`
(statutory rules put the section in `evidence["statutory_ref"]`). Thresholds
come from `param(rule, key, default)` — `rule.parameters`, then
`threshold_config` — never hard-coded. Ageing rules take `as_on` via
`as_on_date()`, which defaults to the latest date in the data, not today.
Financial years are Apr–Mar: group with `fy_sql()`.

**`app/rules/catalogue.py` is the single source of truth** for which rules exist
(name, category, severity, frequency, default parameters). `sync_rules()` (also
`POST /rules/sync`) creates and refreshes a company's `AuditRule` rows from it;
`seed_data.py` uses it too. To add a rule: function + `@register`, a catalogue
row, a fire / don't-fire test, then `python scripts/gen_rule_docs.py` to
refresh `docs/rules.md`. A test fails if the catalogue and registry disagree,
and the engine marks an unregistered code as failed instead of returning [].

`created_at` on imported rows is the CAE import date, not the books entry date.
Entry-timing rules (SAL-004, GST-003) skip bulk-load days via
`bulk_load_days_sql()`.

### Statutory layer

`app/statutory/` holds every legal threshold, rate and section number, each with
its effective date and source: `income_tax` (1961→2025 Act concordance; the
2025 Act applies from 01-04-2026 and `section_ref()` picks the right citation by
transaction date), `gst`, `msme`, `companies` (small company / CARO / IFC),
`labour`, `sampling` (SA 530), `clause44` (Form 3CD cl.44, GN para 79). Rules,
engines and `/statutory` endpoints import from here. A change in law is a dated
edit in one file plus a test — don't put a statutory figure anywhere else.

### Engines

`app/engines/` — `audit_engine` (orchestrates rules), `risk_engine` (scores,
heatmap, trend; live per engagement), `fraud_engine` (fraud indicators — these
use **`score`**, not `severity`; `score` is NUMERIC(5,2), so cap it; a re-run
replaces the day's rows), `gst_engine` + `gst_match` (deterministic GSTR-2B ↔
books match on GSTIN + normalised invoice number, buckets in
`gst_reconciliation.details_json`), `wc_engine` (working capital — DIO on cost
of goods issued, stress score = weighted overdue / DSO / CCC signals, balances
as of the reference date),
`ai_engine` (narrative explanations only; `claude-sonnet-5-5`, reads text
blocks by type because replies can open with a thinking block).

### Connectors

`app/connectors/` — `tally_live.py` (**live Tally Prime** over the XML gateway,
read-only: masters, vouchers month by month, bill-wise outstanding and
settlement dates → CAE tables; idempotent per period; `TALLY_URL`, from Docker
`http://host.docker.internal:9000`), `tally_connector.py` (legacy XML-file
parser, unused), `excel_importer.py` (Excel/CSV upload with auto-detect; the
Analyse step's column mapping is applied on import, Indian day-first dates,
party names resolved to masters).

Background work goes through `app/workers/dispatch.enqueue()`: Celery when a
broker answers, otherwise the same function runs in-process (FastAPI
`BackgroundTasks`) — never "queued" work that silently never runs. Task bodies
are plain `execute_*` functions in `app/workers/tasks.py`. The `beat` service
in docker-compose fires the daily continuous-monitoring run.

### Frontend

React 18 + Vite + TypeScript + Tailwind, `@tremor/react` and `recharts` for
charts, `zustand` for auth state (`src/store/authStore.ts`), axios wrapper in
`src/api/client.ts`. One page per route in `src/pages/`.

## Non-negotiable design rule

**Deterministic code computes every number; the model only explains.**

Statutory and financial figures — ITC at risk, exception thresholds, financial
impact, applicability, due dates, interest — must be produced by explicit rule
code that a reviewer can read and challenge. `ai_engine` may draft narrative
prose about an exception; it must never produce, adjust or infer a figure that
reaches a report.

Do not route a calculation through the model to avoid writing the rule. A wrong
due date or ITC figure is a real penalty for a real taxpayer.

## Gotchas earned the hard way

These are all fixes already in the git history. Re-breaking them is the most
likely way to waste an hour:

- **nginx caches the upstream IP.** After rebuilding `backend` or `frontend`,
  restart `nginx` too, or you'll get 502s pointing at a dead container IP.
- **nginx must proxy frontend requests to the frontend container**, not serve
  from a local filesystem path.
- **Auth uses `bcrypt` directly**, not `passlib` — passlib breaks on
  Python 3.11 + bcrypt 4.x. Don't reintroduce it.
- **The Alembic migration builds schema from `Base.metadata`.** Adding a model
  means the model must be imported where metadata sees it.
- **`invoice_number` deliberately has no unique constraint** — duplicate
  detection (SAL-001) depends on duplicates being insertable.
- **Column widths are enforced**, e.g. `e_way_bill_number` is `String(12)`. Seed
  and test data must fit.
- **`back_populates` pairs in `app/models/` must match on both sides**, or
  SQLAlchemy fails at mapper configuration.
- **Fraud indicators are scored, not severity-graded** — read `score`.
- **Frontend must set `companyId` after login**, or the dashboard hangs on
  loading forever.
- **The backend image is Python 3.11.** Local venvs are often 3.12, which
  accepts f-strings that reuse the outer quote inside `{}` — 3.11 rejects them
  as a syntax error.
- **Migration 001 only creates `pgcrypto` on PostgreSQL < 13** — `gen_random_uuid()`
  is core from 13, and embedded test Postgres ships no contrib extensions.
- **Pydantic `*Out` models must type ids as `uuid.UUID`**, not `str` — the ORM
  hands back UUID objects and a `str` field 500s the whole endpoint
  (`/companies` and `/remediation` did, 31-10-2026).
- **Workflow tables have NOT NULL name/date columns** (`raised_by_name`,
  `responded_by_name`, `responsible_name`, `due_date`, `target_date`). The API
  fills them from the current user / sensible defaults; keep it that way.
- **The integration test must not see the Docker stack's Redis** (localhost:6379)
  — it sets `REDIS_URL` to a dead port so background work runs in-process.
- **Tally gateway traps** are documented at the top of `app/connectors/tally_live.py`;
  never fetch the bare `Voucher` collection or `CLOSINGBALANCE` on ledgers.

### Seed data quirks (`scripts/seed_data.py`)

Deliberate, so don't "fix" them — and don't read them as bugs when a report
looks odd:

- some `due_date` values are NULL
- some 2026 invoices are zero-value
- inventory is recorded as **gross movements**, not net positions
- no PF/ESI challan payments are seeded, so PAY-005 flags every wage month
- GSTINs are valid-format (15 chars) but fictitious — needed for SAL-021 and the
  2B matcher, which reject malformed GSTINs

## Security posture

The committed compose stack is local/evaluation only: default DB credentials, a
default `SECRET_KEY`, Postgres and Redis published on host ports, and a seed
login with a known password documented in `docs/api.md`. That is a known,
accepted state for local dev — but **never add a new hardcoded secret**, and if
a task touches deployment, raise hardening rather than copying the pattern.
`ANTHROPIC_API_KEY` is optional; blank must keep the AI features cleanly
disabled rather than erroring.

## Conventions

- Rule codes: `<PACK>-<NNN>`, sequential within a pack. Existing prefixes are
  `SAL-` (sales), `PUR-` (purchase), `INV-` (inventory), `JE-` (journal),
  `PAY-` (payroll), `TRE-` (treasury), `GST-` (GST), `TDS-` (TDS).
- API modules are one-per-domain, plural, snake_case, mirrored by the router
  prefix.
- Backend: pydantic schemas in `app/schemas/`, SQLAlchemy models in
  `app/models/`. Don't return ORM objects straight from an endpoint.
- Money in narratives is formatted `₹1,23,456.78`-style with thousands
  separators; keep that consistent.
- Comments only where the reasoning is non-obvious — much of this codebase is
  statutory logic, and *that* is exactly where a comment citing the section or
  threshold earns its place.
- Match surrounding style rather than importing a new idiom.

## Working agreements

- Read this file and the relevant module before assuming structure.
- Don't add features, refactors or error handling beyond the task.
- Prefer editing existing files over creating new ones.
- Verify UI/API changes against the running stack before reporting done; say
  plainly what you verified and what you didn't.
- Feature branches: `<type>/<short-description>`. No direct pushes to `main`
  without a PR unless told otherwise. Don't amend pushed commits.
- Confirm before destructive actions — `make clean` drops volumes, and force
  pushes, dropped tables and deleted branches all need a check first.
- Keep this file current after structural changes.
