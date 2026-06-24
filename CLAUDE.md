# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Last verified:** 2026-06-24

---

## 1. What This Repository Is

This repository holds the software and tooling of **Sagar Khatri & Associates,
Chartered Accountants** (Vadodara, India) — a practising CA firm. It is **not a
single application**: it is a collection of independent deliverables, each built
for a real client/practice need (audit, statutory compliance, advisory).

There is **no `main`/`master` branch**. Each project lives on its own
`claude/<topic>-<suffix>` branch and is developed in isolation. When you start a
session you are usually checked out on one such branch, so **orient yourself
first** (`git ls-files | head`) before assuming what project you are in.

### Projects in this repository

The current branch (a superset tree) contains the two code-heavy projects:

| Project | Location | Stack | Purpose |
|---------|----------|-------|---------|
| **Continuous Audit Engine (CAE)** | `cae/` | FastAPI + React/TS + Postgres + Redis/Celery + DuckDB | AI-powered continuous internal-audit platform for CAs/CFOs |
| **LexComply (Indian Law Compliance)** | repo root (`index.html`, `app.js`, `laws.js`, `lexcomply.html`, `build_excel.py`, `LexComply.bas`) | Static HTML/JS app + Python/Excel generator | Statutory compliance checklist tool for Indian businesses (60+ laws) |

Other sibling branches (not present on this branch) hold lighter, document- or
spreadsheet-style deliverables. Fetch and inspect them only if asked:

- `claude/10k-monetization-system-*` — practice growth/monetization playbook (Markdown)
- `claude/excel-debtors-creditors-sales-*` — receivables/payables Excel report
- `claude/india-equity-watchlist-*` — equity watchlist Excel + Python builders
- `claude/indian-law-compliance-tool-*` — standalone LexComply (subset of root files here)
- `claude/risk-control-matrix-manufacturing-*` — RCM Excel + builder
- `claude/website-purchase-build-*` — static marketing website

When the user asks for a **new** deliverable, the established convention is a
**new branch**, not a merge into an existing project.

---

## 2. Continuous Audit Engine (`cae/`)

The flagship application. A production-grade, multi-tenant continuous-audit
platform. Auditors connect a client's books (Tally / Excel), the engine runs a
rule library + ML/AI analysis over the transactions, raises **exceptions**,
scores **risk**, and drives a **remediation** workflow — all surfaced in a React
dashboard.

### 2.1 Layout

```
cae/
├── backend/                  FastAPI service
│   └── app/
│       ├── main.py           App entry; mounts /api/v1, /health, /api/docs
│       ├── config.py         Pydantic settings (env-driven)
│       ├── database.py       SQLAlchemy engine/session
│       ├── api/v1/           HTTP routers (one file per domain)
│       ├── models/           SQLAlchemy ORM models
│       ├── schemas/          Pydantic request/response schemas
│       ├── engines/          Core analysis logic (see below)
│       ├── rules/            Audit rule library (decorator-registered)
│       ├── connectors/       tally_connector, excel_importer (data ingestion)
│       ├── workers/          Celery app + background tasks
│       └── utils/            security (JWT/bcrypt), rbac, export (PDF/Excel)
│   ├── alembic/              DB migrations
│   └── requirements.txt
├── frontend/                 React 18 + TypeScript + Vite + Tailwind
│   └── src/{pages,components,api,store,types}
├── scripts/                  seed_data.py, run_first_audit.py
├── docker-compose.yml        Full stack: postgres, redis, backend, worker, frontend, nginx, prometheus, grafana
├── Makefile                  Operational shortcuts (see commands below)
└── docs/api.md               REST API reference
```

### 2.2 Engines (`cae/backend/app/engines/`)

Each engine is a class constructed with `(db: Session, company_id: str)` and is
orchestrated by the Celery `run_audit_cycle` task:

- `audit_engine.py` — loads enabled rules, materialises transactions into an
  **in-memory DuckDB**, runs each rule's SQL/Python, writes `AuditException` rows.
- `fraud_engine.py` — ML/statistical fraud indicators (e.g. Benford, anomalies).
- `risk_engine.py` — computes & stores per-area risk scores (heatmap source).
- `wc_engine.py` — working-capital metrics (DSO/DPO/DIO etc.).
- `gst_engine.py` — GST reconciliation/compliance checks.
- `ai_engine.py` — Anthropic (`anthropic` SDK) natural-language explanations,
  query answering, and remediation suggestions.

### 2.3 Rule library (`cae/backend/app/rules/`)

Rules are the heart of the audit. Pattern:

```python
from app.rules import register

@register("SAL-001")                       # rule_code, must be unique
def sal_001(conn, company_id, rule):
    """Duplicate Invoice Number."""        # docstring = human description
    rows = conn.execute("SELECT ... WHERE company_id = ?", [company_id]).fetchall()
    return [
        {
            "title": ...,                  # short headline
            "description": ...,            # ₹-formatted human explanation
            "severity": "critical",        # critical | high | medium | low
            "financial_impact": float(...),
            "evidence": {...},             # JSON proof, persisted with the exception
        }
        for r in rows
    ]
```

- `conn` is the DuckDB connection (transactions pre-loaded as tables:
  `sales_invoices`, `purchase_invoices`, `journal_entries`, …).
- Rules are grouped by domain: `sales_rules.py` (SAL-*), `purchase_rules.py`
  (PUR-*), `inventory_rules.py`, `journal_rules.py`, `payroll_rules.py`,
  `treasury_rules.py`.
- `rules/__init__.py` holds the `register`/`get_rule_fn` registry and imports
  every rule module to trigger registration. **A new rule module must be added
  to that import line**, or its rules won't load.

**To add a rule:** add a `@register("XXX-NNN")` function to the right domain
module, return the exception-dict list above, and ensure a corresponding
`AuditRule` row exists (created via seed/migration) so the engine picks it up
(`is_active`, `run_frequency`, `company_id`).

### 2.4 API surface (`cae/backend/app/api/v1/`)

Mounted under `/api/v1`. Routers: `auth`, `companies`, `ingestion`, `rules`,
`exceptions`, `queries`, `remediation`, `risk`, `gst`, `dashboard`, `reports`.
All endpoints except `/auth/login` require a Bearer JWT. Roles are enforced via
`utils/rbac.py` (e.g. `super_admin`, `partner`). Full reference: `cae/docs/api.md`.
Interactive docs at runtime: `http://localhost:8000/api/docs`.

### 2.5 Frontend (`cae/frontend/`)

React 18 + TypeScript + Vite, styled with Tailwind, charts via `@tremor/react`
and `recharts`, state via `zustand` (`src/store/authStore.ts`), HTTP via `axios`
(`src/api/client.ts`). One page per backend domain in `src/pages/`
(`Dashboard`, `Exceptions`, `RiskHeatmap`, `FraudAnalytics`, `Remediation`,
`GST`, `WorkingCapital`, `Reports`, `Queries`, `Rules`, `DataIngestion`,
`Login`, `Profile`). Shared chrome in `components/layout/` and reusable atoms in
`components/common/` (`SeverityBadge`, `StatusBadge`, `AmountDisplay`).

### 2.6 Data flow (one audit cycle)

```
Tally/Excel ──connectors──▶ transaction tables ──▶ Celery run_audit_cycle
   └▶ AuditEngine (DuckDB + rules) ─▶ AuditException rows
   └▶ FraudEngine ─▶ fraud indicators
   └▶ RiskEngine  ─▶ risk scores (heatmap)
   └▶ WorkingCapitalEngine ─▶ WC metrics
        ▼
   React dashboard  ◀── /api/v1 ──  SyncJob status, exceptions, risk, reports
```

---

## 3. Build, Run & Test Commands

### CAE — full stack (preferred: Docker, from `cae/`)

| Task | Command |
|------|---------|
| Build images | `make build` |
| Start everything | `make up` |
| Run DB migrations | `make migrate` (`alembic upgrade head`) |
| Seed demo data | `make seed` |
| Run first audit cycle | `make audit` |
| Tail backend+worker logs | `make logs` |
| Backend shell | `make shell-backend` |
| Postgres shell | `make shell-db` |
| Stop | `make down` |
| Stop + wipe volumes | `make clean` |

Default ports: backend `8000`, frontend `3000`, nginx `8080`, Postgres `5432`,
Redis `6379`, Prometheus `9090`, Grafana `3001`.

### CAE backend — local (without Docker, from `cae/backend/`)

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload          # serves on :8000
celery -A app.workers.celery_app worker --loglevel=info   # background worker
```

### CAE frontend (from `cae/frontend/`)

```bash
npm install
npm run dev        # Vite dev server (:5173)
npm run build      # production build
npm run lint       # eslint src --ext ts,tsx
npm run preview
```

### LexComply (repo root)

- The web tool is **static** — open `index.html` / `lexcomply.html` directly in a
  browser (no build step). Logic lives in `app.js` (firm config, UI) and
  `laws.js` (the 60+ law dataset), with export helpers in `excel-export.js`.
- To regenerate the Excel workbook: `python3 build_excel.py` → produces
  `LexComply_India.xlsm`. The VBA module `LexComply.bas` is imported into the
  workbook manually via the Excel VBE (Alt+F11 → File → Import File).

> **No automated test suite exists** in this repository today. "Testing" means
> running the app and exercising the golden path (CAE: log in → ingest → run
> audit → view exceptions; LexComply: open the page, fill the questionnaire,
> verify the generated checklist/export). Do not claim tests pass — there are none.

---

## 4. Configuration & Secrets

- CAE backend is configured entirely via environment variables (see
  `cae/backend/app/config.py` and the root `.env.example`). Copy `.env.example`
  to `.env` for local runs.
- Key vars: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY` (min 32 chars),
  `ANTHROPIC_API_KEY` (required for the AI engine), `CORS_ORIGINS`,
  `ENVIRONMENT` (`development`/`production`), `UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB`.
- **Never commit real secrets.** The defaults in `config.py` and
  `docker-compose.yml` are dev placeholders and must be overridden in production.
- This is financial/audit software handling **real client data**. Treat ingested
  books, exceptions, and credentials as confidential. Do not exfiltrate sample
  data, do not log secrets, and keep `.env` out of git.

---

## 5. Conventions

- **Backend (Python):** FastAPI + SQLAlchemy 2.x + Pydantic v2. One router per
  domain in `api/v1/`, one ORM module per aggregate in `models/`, matching
  Pydantic schemas in `schemas/`. Business logic belongs in `engines/` or
  `rules/`, **not** in routers. Money is rendered with `₹` and thousands
  separators in user-facing strings.
- **Rule codes:** `DOMAIN-NNN` (`SAL-001`, `PUR-014`, …), unique across the
  library, registered via the `@register` decorator.
- **Frontend (TS):** functional React components, Tailwind utility classes,
  `zustand` for state, typed API client. Page filenames are `PascalCase.tsx`.
- **LexComply data:** each law in `laws.js` is an object with `id`, `name`,
  `category`, `priority`, a `reason(company)` predicate that decides
  applicability, and an `actions[]` list (each with `freq`, `deadline`,
  `authority`, `penalty`, `desc`). Add laws by extending this array — keep the
  shape consistent so the renderer and Excel export keep working.
- **Firm identity** (name, email, WhatsApp, tagline) is centralised in the
  `FIRM_CONFIG` object at the top of `app.js`; change it there, not inline.

---

## 6. Git Workflow

- **One project = one branch.** Branch names follow `claude/<short-topic>-<suffix>`.
  Do a new deliverable on a new branch; do not merge unrelated projects together.
- **There is no shared `main`** to integrate into — work is delivered on the
  feature branch and pushed there.
- Push with `git push -u origin <branch-name>`; retry transient network failures
  with exponential backoff (2s, 4s, 8s, 16s).
- Write commit messages about *why*. Do not amend commits already pushed.
- **Do not open a pull request unless explicitly asked.**
- Confirm before destructive actions (force-push, dropping volumes/data,
  deleting branches).

---

## 7. AI Assistant Guidelines

1. **Orient before acting** — confirm which branch/project you are in; this repo
   mixes several unrelated codebases.
2. **Keep changes scoped** to the requested task; don't refactor or add features
   beyond it, and prefer editing existing files over creating new ones.
3. **Respect the rule-registry contract** in the CAE — new rule modules must be
   imported in `rules/__init__.py`, and rules must return the exception-dict shape.
4. **No invented tests** — verify by running the golden path; never report that a
   non-existent test suite passed.
5. **Guard client/financial data and secrets** — never commit `.env`, never log
   credentials, treat ingested books as confidential.
6. **Default to no code comments** unless the reasoning is non-obvious.
7. **Keep this file current** — after any significant structural change (new
   engine, new project branch, new build step), update the relevant section and
   the "Last verified" date.
