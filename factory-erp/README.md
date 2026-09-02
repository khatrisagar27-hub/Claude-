# Factory ERP — Stock, Machines & Production

A standalone ERP for small/mid manufacturers, scoped to three things a plant
manager actually needs day to day: **stock** (raw material, WIP, finished
goods), **machines** (uptime, downtime, maintenance), and **production**
(work orders, output, rejection) — feeding a **management analytics**
dashboard, not just a set of data-entry screens.

This is unrelated to `cae/` (Continuous Audit Engine) and to LexComply at the
repo root. It does not share their database, code, or containers. It's a
separate product for a client's ops/production team; a CA practice would use
it (or its data exports) as a source system, not as an audit tool itself.

## Why these three modules together

Stock, machines, and production are one feedback loop in any factory:
a machine's downtime blocks a work order, a work order consumes stock and
produces stock, and stock shortages stall machines. Splitting these into
three separate tools (as most small manufacturers end up doing — a stock
register in Excel, a maintenance diary, a production log) loses exactly the
cross-cutting numbers management actually wants: OEE, true cost per unit,
what's actually consuming the machine's idle time. One schema, one set of
foreign keys between work orders / machines / stock movements, makes those
numbers a query instead of a manual reconciliation.

## Modules

### 1. Master data
- **Plant** — a client can run more than one factory location.
- **Warehouse/Location** — store within a plant (raw material store, WIP
  floor, finished goods store, scrap yard).
- **Machine** — work center: code, category, rated capacity/hour, install
  date, status.
- **Product/SKU** — raw material, component, WIP, or finished good; UOM,
  category, standard cost.
- **BOM (Bill of Materials)** — product → component list with qty-per-unit,
  used to compute expected material consumption and yield.
- **Shift** — for shift-wise OEE and manning.

### 2. Stock
- **Stock ledger** (`StockMovement`) — every receipt, issue, production
  consumption, production output, transfer, and adjustment is a row; on-hand
  qty is always a derived sum, never a mutable field. This is the same
  discipline as a proper accounting ledger — necessary if this data is ever
  going to reconcile against purchase/sales records.
- Reorder level / reorder qty per item → low-stock alerts.
- Standard costing for valuation (weighted-average/FIFO is a v2 concern, not
  v1 — see Non-goals).

### 3. Machines
- Machine master + status (running/idle/breakdown/maintenance).
- **Downtime log** — every stoppage, tagged with a reason category
  (breakdown, changeover, no material, power outage, planned maintenance,
  other) and linked to the work order in progress, if any.
- **Maintenance log** — preventive/breakdown/predictive, cost, next-due date.

### 4. Production
- **Work Order (Production Order)** — product, machine, shift, planned vs.
  actual qty, planned vs. actual start/end, status.
- **Rejection/quality log** — defect type + qty against a work order, so
  yield and quality-rate analytics have a source.
- Consuming a work order's BOM against stock, and posting its output back to
  stock, are both stock movements — see Stock ledger above.

### 5. Management analytics
Every figure below is computed by deterministic backend code from the
ledger/log tables — never estimated or eyeballed. That's a hard rule
carried over from this repo's audit-engine sibling project and it applies
here for the same reason: a wrong OEE or reorder number costs a real
production decision.

| Metric | Formula | Feeds |
|---|---|---|
| Availability | Run time ÷ Planned production time (planned − downtime) | OEE |
| Performance | (Total output ÷ Run time) ÷ Ideal run rate | OEE |
| Quality | Good output ÷ Total output | OEE |
| **OEE** | Availability × Performance × Quality | machine/line/plant, trended |
| Machine utilization | Run time ÷ Available time | machine ranking |
| Downtime Pareto | Total downtime minutes by reason category | top-loss chart |
| Production yield | Good output ÷ (BOM-expected input consumed) | material efficiency |
| Rejection rate | Rejected qty ÷ Total output | quality trend |
| Stock ageing | Days since last outward movement, bucketed 0–30/31–60/61–90/90+ | dead-stock flag |
| Stock valuation | On-hand qty × standard cost, by category | balance-sheet-adjacent view |
| Reorder alerts | On-hand qty < reorder level | procurement action list |
| Stock turnover | Value consumed (period) ÷ average on-hand value | working-capital signal |
| Cost per unit | (Material consumed value + machine hours × rate) ÷ good output | product costing |

## Explicit non-goals (v1)

- No FIFO/weighted-average costing layer — standard cost only.
- No multi-currency, no GST/e-way-bill fields (that's LexComply/CAE territory,
  not this product).
- No barcode/RFID scanning integration — data entry is form-based.
- No scheduling/APS (advanced planning & scheduling) — work orders are
  planned by the user, not auto-sequenced.
- No mobile app — responsive web only.

## Stack

Deliberately mirrors `cae/`'s stack (same team will maintain both) but is a
fully separate deployment:

- **Backend:** FastAPI + SQLAlchemy + Alembic, Postgres in prod / SQLite
  in-memory for tests (same shim pattern as `cae/backend/tests/conftest.py`).
- **Frontend:** React + Vite + TypeScript + Tailwind, `recharts` for charts,
  axios client.
- **Docker Compose:** own `docker-compose.yml`, own Postgres container, own
  ports (nginx 8081, backend 8001, frontend 5173, Postgres 5433 — all offset
  from `cae/`'s so both stacks can run at once) — does not touch `cae/`'s
  containers.

## Layout

```
factory-erp/
  backend/
    app/
      models/        # SQLAlchemy models: plant, machine, stock, production, downtime, maintenance, user
      schemas/        # Pydantic request/response schemas
      api/v1/         # one router module per domain
      analytics/       # OEE, stock, production, downtime calculations — plain Python, unit-tested
      database.py, config.py, main.py
    alembic/
    tests/
    requirements.txt
  frontend/
    src/
      pages/          # Dashboard, Machines, Stock, Production
      components/
      api/
  docker-compose.yml
```

## Running it

```bash
cd factory-erp
docker compose up --build
# nginx  -> http://localhost:8081  (use this)
# backend  direct -> http://localhost:8001/api/docs
# frontend direct -> http://localhost:5173
# Postgres         -> localhost:5433
```

Apply migrations and load demo data (backend container, or locally against
`DATABASE_URL`):
```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed_data.py
# login: admin@factory.local / changeme123
```

Backend tests (no Docker needed):
```bash
cd factory-erp/backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

Frontend (from `factory-erp/frontend`): `npm install`, `npm run dev`,
`npm run build`, `npm run lint`. Type-check via `npx tsc --noEmit`.

## Status

Built and verified: full schema + Alembic migration, CRUD + auth APIs, the
analytics module (OEE, downtime Pareto, stock ageing/reorder/valuation/
turnover, production yield/rejection) with 21 passing pytest tests run
against in-memory SQLite, a seed script exercised end-to-end against every
analytics function, and a frontend (Login, Dashboard with OEE/downtime
charts and reorder-alert table, plus read-only Machines/Stock/Production
list pages) that type-checks, lints, and builds clean. Not run: the actual
Docker Compose stack (no Postgres available in this environment) and the
frontend against a live backend — both are standard FastAPI/Vite setups, but
say so rather than claim otherwise. Not yet built: RBAC enforcement beyond
login (roles exist on `User` but no endpoint restricts by role yet),
BOM-driven auto stock posting on work-order completion, and create/edit UI
for stock movements, work orders, downtime and maintenance logs — those are
currently API-only (see `/api/docs`).
