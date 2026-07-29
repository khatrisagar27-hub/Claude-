# Open-source audit & compliance tooling for Indian practice

Two tools for Indian chartered accountants and finance teams, built and used in
live practice:

| Project | What it is |
|---|---|
| **[Continuous Audit Engine (CAE)](#continuous-audit-engine-cae)** (`cae/`) | Self-hosted continuous-auditing platform: ingest accounting data, run exception rules, score risk and fraud indicators, reconcile GSTR-2B, generate ICAI-format working papers |
| **[LexComply India](#lexcomply-india)** (repo root) | Applicability engine for 69 Indian statutes — answers "which laws apply to this company, and what must it file when" |

> **Status: pre-release.** Both tools are in active development and have not had
> a tagged release. Interfaces will change. Neither tool is a substitute for
> professional judgment — every figure, exception and due date it produces is
> intended for review and sign-off by a qualified professional. See
> [Design principle](#design-principle) below.

---

## Continuous Audit Engine (CAE)

Most audit analytics for the Indian market is closed, per-seat, enterprise
software. CAE is an attempt at a self-hostable alternative that works on the
data small and mid-size practices actually have: Tally Prime companies and Excel
exports.

### What it does

- **Ingestion** — Tally Prime connector and Excel/CSV importer, with job tracking
  (`app/connectors/`)
- **Exception rule engine** — configurable rule packs across sales, purchase,
  journal, payroll, treasury and inventory (`app/rules/`); rules can be toggled
  and test-run individually
- **Risk & fraud scoring** — risk scores, heatmap, trend, and fraud indicators
  (`app/engines/risk_engine.py`, `fraud_engine.py`)
- **GST** — GSTR-2B upload, reconciliation against the purchase register, and an
  **input-tax-credit-at-risk** figure (`app/engines/gst_engine.py`)
- **Working capital** — working-capital analysis engine (`app/engines/wc_engine.py`)
- **Audit workflow** — exceptions → client queries → remediation tracking, each
  with status transitions
- **Reports** — working papers, exception summaries and audit decks (PDF via
  reportlab)
- **AI explanations** — optional; explains an exception in narrative form
  (`app/engines/ai_engine.py`). Off unless an API key is set, and it never
  computes a number — see [Design principle](#design-principle).

Multi-tenant by company, JWT auth, ~40 REST endpoints. Full endpoint reference:
[`cae/docs/api.md`](cae/docs/api.md). End-user walkthrough:
`CAE_User_Guide.html`.

### Stack

FastAPI · SQLAlchemy 2 + Alembic · PostgreSQL 15 · Redis + Celery worker ·
pandas / DuckDB / scikit-learn · React + TypeScript + Vite + Tailwind ·
nginx · Prometheus + Grafana · Docker Compose

### Quickstart

Requires Docker and Docker Compose.

```bash
cd cae
make build && make up
make seed          # loads demo companies and transactions
make audit         # runs the first audit pass over the seed data
```

| Service | URL |
|---|---|
| App (via nginx) | http://localhost:8080 |
| Frontend (direct) | http://localhost:3000 |
| API + interactive docs | http://localhost:8000/api/docs |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |

Other targets: `make migrate`, `make logs`, `make shell-backend`,
`make shell-db`, `make down`, `make clean` (drops volumes).

### Configuration

Compose ships working defaults for local use. Override via environment or a
`cae/backend/.env` (see `cae/backend/app/config.py` for the full list):

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | JWT signing key — **must** be replaced outside local use |
| `DATABASE_URL` | Postgres DSN |
| `REDIS_URL` | Celery broker / result backend |
| `ANTHROPIC_API_KEY` | Enables AI exception explanations; optional, blank disables the feature |
| `CORS_ORIGINS` | JSON array of allowed origins |
| `UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB` | File ingestion |

> **Not yet hardened for production.** The bundled compose file uses default
> database credentials, a default `SECRET_KEY`, publishes Postgres and Redis on
> host ports, and the seed script creates a demo login with a known password
> (see `cae/scripts/seed_data.py`). Treat the current stack as a local /
> evaluation deployment: rotate every credential, drop the published ports and
> put it behind TLS before it sees real client data.

---

## LexComply India

Answers a question that costs Indian practices real time: *given this company's
profile, which statutes apply to it, and what does it have to do under each one?*

- **69 statutes** across 15 categories — Social Security, Labour, Tax,
  Corporate, Securities, Environment, MSME & Trade, Technology & Data,
  Intellectual Property, Consumer, Food & Health, Infrastructure, Transport,
  Financial, Sector-Specific
- Each statute carries an **applicability rule** evaluated against a company
  profile (headcount, factory workers, turnover, sector, and so on) — so the
  output is a filtered, reasoned list, not a generic checklist. The reason is
  shown ("Mandatory: company has 24 employees, threshold: 20").
- Each statute expands into **action items** with frequency, statutory deadline,
  authority, penalty for default, and a plain-language description.
- Excel export of the resulting compliance calendar.

### Run it

**Web app** — static, no build step, no server dependency:

```bash
open index.html
```

(`laws.js` = statute database · `app.js` = applicability + UI ·
`excel-export.js` = export · `lexcomply.html` = single-file variant)

**Excel workbook** — regenerate the styled workbook, then import the VBA module:

```bash
python build_excel.py
```

Produces `LexComply_India.xlsm`. Import `LexComply.bas` via the VBA editor
(Alt+F11 → File → Import File).

> Statutory deadlines, rates and thresholds change with every Finance Act and
> notification. The database reflects the author's understanding at the time of
> writing and must be verified against the current bare Act, rules and
> notifications before being relied on.

---

## Design principle

**Deterministic code computes; the model explains.**

Every statutory or financial number — ITC at risk, exception thresholds,
applicability, due dates, interest — is produced by explicit Python or
JavaScript rule code that can be read, tested and argued with in front of a
reviewer. A language model is used only to draft narrative: explaining why an
exception was raised, summarising a working paper.

This is not a stylistic preference. A wrong due date or a wrong ITC figure is a
penalty on a real taxpayer, so the number has to come from a rule someone can
point at, and a chartered accountant reviews and signs the output.

---

## Repository layout

```
cae/                        Continuous Audit Engine
  backend/app/
    api/v1/                 REST endpoints (auth, ingestion, rules, exceptions,
                            queries, remediation, risk, gst, reports, dashboard,
                            working_capital)
    connectors/             Tally Prime connector, Excel importer
    engines/                audit, risk, fraud, gst, working-capital, ai
    rules/                  sales, purchase, journal, payroll, treasury, inventory
    models/ schemas/        SQLAlchemy models, pydantic schemas
    workers/                Celery tasks
  frontend/src/pages/       React pages (Dashboard, Exceptions, GST, Rules,
                            RiskHeatmap, FraudAnalytics, Reports, ...)
  scripts/                  seed_data.py, run_first_audit.py
  docs/api.md               API reference
  nginx/ monitoring/        reverse proxy, Prometheus config
  docker-compose.yml Makefile

index.html app.js laws.js excel-export.js    LexComply web app
lexcomply.html                               LexComply, single file
build_excel.py LexComply.bas                 LexComply Excel workbook + VBA
CAE_User_Guide.html                          CAE end-user guide
```

## Roadmap

- CAE 1.0: test coverage, auth hardening, migration correctness, production
  compose profile
- Live Tally Prime reads via MCP instead of static exports
- Broader GST coverage beyond GSTR-2B reconciliation
- CARO 2020 and Form 3CD working-paper generation
- Wider statutory due-date rule coverage in LexComply

Issues and pull requests are welcome.

## License

[MIT](LICENSE) © 2026 Sagar Khatri

Built by **CA Sagar Khatri** — Sagar Khatri & Associates, Chartered Accountants
(FRN 157238W). Developed with [Claude Code](https://claude.com/claude-code).
