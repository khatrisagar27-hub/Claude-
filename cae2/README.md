# Continuous Audit Engine (CAE) — version 2

A self-hosted audit analytics tool for a CA practice. Upload a client's registers,
run a catalogue of statutory and control tests over them, review each exception
through to a conclusion, and take out an Excel working paper.

This is a ground-up rebuild. The earlier version in [`../cae`](../cae) is
untouched and is not used by this one.

> **Status: pre-release, not yet used on a live engagement.** Every figure and
> finding is for review by the engagement team. Statutory limits and rates are
> in [`backend/app/statute.py`](backend/app/statute.py) with their provisions —
> verify them against the current law before relying on a finding.

## How it works

**1. Engagement.** One client, one period (normally a financial year), one set
of thresholds. Everything else belongs to an engagement.

**2. Data.** Nine datasets, each an Excel/CSV upload (the day book also accepts
Tally Prime XML):

| Dataset | What it is |
|---|---|
| Party master | Customers and vendors: GSTIN, PAN, bank account, MSME category, related party, credit days |
| Day book / ledger | One row per voucher line, with ledger group |
| Sales register | Invoices with GST break-up, IRN, e-way bill, receipts |
| Purchase register | Invoices with GST, ITC claimed, TDS, PO, GRN, payment |
| Bank statement | Withdrawals and deposits |
| Stock movements | Opening, receipts, issues, adjustments |
| Employee master, Payroll register | For payroll tests |
| GSTR-2B | For ITC reconciliation |

Column headings are matched automatically (templates are downloadable). A row
that fails validation is rejected with its row number and the reason — nothing
is guessed. Where a value is derived (for example invoice total = taxable +
tax when no total column exists) the upload records that as a note.

**3. Rules.** 67 tests across Sales, Purchases, GST, TDS, Books, Treasury,
Payroll and Inventory — full list in [`docs/rules.md`](docs/rules.md). Each rule
states what it tests, the provision behind it, the data it needs and its
thresholds. Thresholds and on/off can be changed per engagement. A rule whose
data has not been uploaded is reported as **not run**, never as passed.

**4. Findings.** Each exception is a finding with the amount involved, the
provision, and the rows that prove it. Re-running the audit after new data:

| Situation | What happens |
|---|---|
| Same exception still there | The same finding is refreshed. Status and notes are kept. No duplicate. |
| Exception no longer in the data | An open or queried finding becomes **cleared**. |
| A cleared exception returns | It is reopened. |
| Finding already concluded | Never changed by a run. |

Review statuses: **open → queried → confirmed / dismissed → resolved**. Staff
can comment and raise queries. Confirming, dismissing or resolving needs a
manager or partner and a written basis. Remediation actions with owner and due
date hang off each finding.

**5. Outputs.** Dashboard, GSTR-2B reconciliation with ITC at risk, working
capital (DSO, DPO, DIO, ageing), and an Excel working paper (summary, findings
register, evidence, 2B reconciliation, rules run, review trail).

### How severity is set

Each rule has an inherent level (low, medium, high, critical). The amount then adjusts it:

- amount ≥ engagement **materiality** → critical
- amount > 0 and below the **clearly trivial** threshold → one level down
- otherwise the rule's own level

### How the risk score is computed

Per area: critical × 25 + high × 10 + medium × 4 + low × 1 over findings that
are open, queried or confirmed, capped at 100. Overall = the highest area score.
With many findings the cap is reached quickly; read the per-area counts and
amounts alongside it.

### Design rule

**Code computes every number.** Every figure comes from a rule a reviewer can
read. There is no AI in this version: nothing estimates, infers or adjusts a figure.

## Run it

### On your machine, without Docker

Needs Python 3.11+ and Node 20+. Uses a local SQLite file under `backend/data/`.

```bash
cd backend && pip install -r requirements-dev.txt
python -m app.demo            # optional: loads a demo engagement with planted exceptions
cd .. && make dev-api         # terminal 1
make dev-web                  # terminal 2  → http://localhost:5173
```

The first visit asks you to create the partner account. There is no default login.

### With Docker (app + Postgres)

```bash
make up        # creates .env with random secrets on first run → http://localhost:8080
make demo      # optional
make logs | make down | make psql
```

Postgres is not exposed on the host and the app listens on 127.0.0.1 only.
To serve a team, put it behind a TLS reverse proxy and back up the `db` volume.

### Tests

```bash
make test      # SQLite, a few seconds
CAE_TEST_DATABASE_URL=postgresql+psycopg://user@host/emptydb make test   # same suite on Postgres (wipes that database)
```

## Layout

```
backend/app/
  statute.py        every limit and rate, with its provision; GSTIN/PAN validation
  models.py         all tables: practice, client data, audit
  ingest/           schema.py (datasets and accepted headings), tabular.py, tally.py, loader.py
  audit/
    registry.py     @rule decorator and the catalogue
    dataset.py      loads an engagement into pandas once per run
    engine.py       runs rules; fingerprints, clears and reopens findings
    rules/          sales, purchases, gst, tds, books, treasury, payroll, inventory
  analytics/        gst_reco.py, working_capital.py, risk.py
  workpaper.py      Excel working paper
  api/              auth, engagements, data, audit, insights
  demo.py           demo engagement (one planted exception per rule)
backend/tests/      statute, ingest, engine, rules (hand-worked figures), api
frontend/src/       React + TypeScript + Tailwind; one file per page
docs/rules.md       generated rule catalogue
```

## Adding a rule

Write one function in the right file under `backend/app/audit/rules/`:

```python
@rule("PUR-012", "Purchases", "Short name", "medium", needs=["purchases"],
      law="Act, section", params={"min_amount": (50000, "Minimum invoice total (₹)")})
def my_rule(data, p, ctx):
    """One or two sentences a reviewer will read on the Rules page."""
    bad = data.purchases[data.purchases["total"] >= p["min_amount"]]
    return [Hit(key=f"{r.vendor_key}|{r.doc}", title="...", detail="...", impact=r.total,
                evidence=rows(bad[bad["doc"] == r.doc], COLS)) for r in bad.itertuples()]
```

`key` must be the same on every run for the same item — it is what prevents
duplicates. Plant an example in `demo.py` (a test checks every rule finds one),
then regenerate the catalogue: `python -m app.catalogue > ../docs/rules.md`.

## Known limitations

- **Income-tax Act, 2025.** Citations are to the 1961 Act. For periods starting
  on or after 1 April 2026 the new section is added from an **unverified**
  mapping in `statute.py` and marked "(verify)".
- **TDS** is tested from the purchase register only: thresholds, rates, missing
  PAN. Not tested: late deposit, lower-deduction certificates, s.194C(6)
  declarations, salary TDS, payments to non-residents.
- **MSME interest** is computed only when the RBI bank rate is entered on the
  engagement. Whether a supplier is a trader must be checked on review.
- **Database upgrades.** Tables are created on first start. There is no
  migration tool yet, so a future change to the tables needs one before it is
  applied to a database holding client work.
- **Access** is by role across the whole installation; there is no per-client
  restriction between staff.
- **Not built:** bank reconciliation, AI narrative, PDF reports, live Tally connection.
- The Docker image and compose file have not been built or run in the
  environment this was developed in (no Docker daemon); the app itself was run
  and tested directly, including against Postgres 16.
