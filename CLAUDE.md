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

CAE: all commands run from `cae/` via the Makefile — read `cae/Makefile` for the
target list. Two things it doesn't tell you: the backend also runs
`alembic upgrade head` on boot, and **port 8080 (nginx) is the one to use** —
3000 and 8000 are the frontend and API sitting behind it.

Backend tests (from `cae/backend/`, no Docker needed): `pytest` — details in
[`cae/backend/CLAUDE.md`](cae/backend/CLAUDE.md). CI runs the same suite with
coverage on every push and PR.

Frontend (from `cae/frontend/`): npm scripts as declared in `package.json`;
type-check via `npx tsc --noEmit`. **Frontend has no tests** — lint and
type-check are the only checks there, so verify UI work against the running
stack.

LexComply: open `index.html` directly in a browser; `python build_excel.py` to
regenerate the workbook.

## Architecture

### Request path

`nginx` (8080) → React SPA (`frontend`) and `/api/*` → FastAPI (`backend`).
`app/main.py` mounts `app/api/v1/router.py` under `/api/v1`; that router
aggregates one module per domain. Adding a domain means: new module in
`app/api/v1/`, then register it in `router.py`.

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

### Auth & shared utils

`app/utils/rbac.py` — access tokens and refresh tokens are distinct types, and a
refresh token must not be accepted as an access token. `app/utils/security.py`,
`app/utils/rbac.py`, `app/utils/export.py` and `app/database.py` are all covered
by tests; change them with the suite running.

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
`.env.example` at the repo root is the template for a real deployment — keep it
in sync when you add a setting to `config.py`. `ANTHROPIC_API_KEY` is optional;
blank must keep the AI features cleanly disabled rather than erroring.

`AuditEngine` validates `company_id` as a UUID specifically as a SQL-injection
guard — rule SQL is string-built for DuckDB, so that check is load-bearing. There
is a test asserting it; don't loosen it.

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
- Run `pytest` for backend changes, and verify UI changes against the running
  stack. Say plainly what you verified and what you didn't.
- Feature branches: `<type>/<short-description>`. No direct pushes to `main`
  without a PR unless told otherwise. Don't amend pushed commits.
- Confirm before destructive actions — `make clean` drops volumes, and force
  pushes, dropped tables and deleted branches all need a check first.
- Keep this file current after structural changes.
