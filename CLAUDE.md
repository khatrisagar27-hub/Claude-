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

**There are none.** No pytest, no vitest, no CI. Do not claim a change is
"tested" — verify by exercising the running stack (`make up`, then hit the
endpoint or the UI) and say that's what you did. If you add tests, put backend
tests under `cae/backend/tests/`, add pytest to `requirements.txt`, and record
the command in the table above.

## Architecture

### Request path

`nginx` (8080) → React SPA (`frontend`) and `/api/*` → FastAPI (`backend`).
`app/main.py` mounts `app/api/v1/router.py` under `/api/v1`; that router
aggregates one module per domain (`auth`, `companies`, `ingestion`, `rules`,
`exceptions`, `queries`, `remediation`, `risk`, `gst`, `dashboard`, `reports`,
`working_capital`). Adding a domain means: new module in `app/api/v1/`, then
register it in `router.py`.

### The audit engine — Postgres for state, DuckDB for analysis

This is the central design fact. `app/engines/audit_engine.py` opens an
**in-memory DuckDB** connection, and `_load_data_to_duckdb()` pulls each
relevant table out of Postgres via `pandas.read_sql` and registers it as a
DuckDB table. Rules then run as plain analytical SQL against DuckDB.

Consequences to respect:

- Rule SQL is **DuckDB dialect** with `?` positional params — not SQLAlchemy,
  not Postgres.
- A rule can only query tables `_load_data_to_duckdb()` actually loads. Needing
  a new table means loading it there first.
- Every rule run reloads the company's data. Keep that in mind before adding
  per-rule loads.

### Rule registry

`app/rules/__init__.py` is a decorator registry: `@register("SAL-001")` maps a
rule code to a callable, and the module's tail imports every rule module to
trigger registration. Rule packs are `sales_rules`, `purchase_rules`,
`inventory_rules`, `journal_rules`, `payroll_rules`, `treasury_rules`.

A rule is `fn(conn, company_id, rule)` returning a **list of exception dicts**
with keys `title`, `description`, `severity`, `financial_impact`, `evidence`.
To add one: write the function in the right pack with the next code in sequence,
decorate it, and ensure a corresponding `AuditRule` row exists (rules are
enabled/disabled from the DB, not from code).

### Engines

`app/engines/` — `audit_engine` (orchestrates rules), `risk_engine` (scores,
heatmap, trend), `fraud_engine` (fraud indicators — these use **`score`**, not
`severity`), `gst_engine` (GSTR-2B reconciliation, ITC at risk), `wc_engine`
(working capital), `ai_engine` (narrative explanations only).

### Connectors

`app/connectors/` — `tally_connector.py` (Tally Prime), `excel_importer.py`
(Excel/CSV upload with auto-detect ingestion).

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

### Seed data quirks (`scripts/seed_data.py`)

Deliberate, so don't "fix" them — and don't read them as bugs when a report
looks odd:

- some `due_date` values are NULL
- some 2026 invoices are zero-value
- inventory is recorded as **gross movements**, not net positions

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
  `PAY-` (payroll), `TRE-` (treasury).
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
