# Audit-fieldwork agents

A four-agent Claude Code system that runs CAE fieldwork every day without the
partner checking in. On each run it ingests the client's data, runs the rules,
researches every flagged item, decides what to do with each one, does it,
and sends the partner a one-page digest. The digest lists only the decisions
that are the partner's to make.

```
 cron ─► fieldwork_cycle.sh ─► claude -p "/fieldwork run <client>"
                                   │  (lead: .claude/skills/fieldwork)
   caectl ingest · sync · brief ◄──┤
                                   ├─► fw-researcher  brief.json      ─► research.json
                                   ├─► fw-decider     + research      ─► decisions.json
                                   ├─► fw-executor    decisions ─► caectl writes ─► execution.json
                                   └─► fw-reporter    all of it        ─► digest.md ─► partner
 partner ─► /fieldwork approve|reject <client> A-000n  ─► caectl release / resolve
```

## Who does what

| Part | Kind | Job | Can touch CAE? |
|---|---|---|---|
| `cae/scripts/caectl.py` | Code | Computes every figure, band, due date, statutory reference and default route; enforces the approval gates; sends email | Yes, the only path |
| `/fieldwork` skill | Lead | Runs the cycle in order; records partner approvals and acts on them immediately | Through caectl |
| `fw-researcher` | Agent | Per exception: what the evidence shows, the innocent explanations, the exact documents that would settle it; whether a management response answers the query | No (read-only on files) |
| `fw-decider` | Agent | One final decision per exception per run; drafts query wording, escalation summaries, resolution comments and remediation plans | No (writes `decisions.json` only) |
| `fw-executor` | Agent | Applies decisions in a fixed order; records refusals without working around them | Through caectl |
| `fw-reporter` | Agent | Partner digest; checks every ₹ figure against the brief; emails the partner | Through caectl |

## What runs without you, and what waits

These are enforced in `caectl`, not left to the prompts:

| Goes ahead on its own | Waits for the partner |
|---|---|
| Rules run, research, decisions, working paper download | **Every query email to the client** (it carries figures): drafted, previewed, released only after approval |
| Reminders for overdue queries (rendered by code, no figures, max 3, every 3 days) | **Any client contact on fraud-category, critical or ≥ performance-materiality items** (escalation) |
| Accepting a management response on a routine item | **Accepting a response or marking false positive** on those same serious items |
| Closing clearly-trivial items (≤ clearly-trivial threshold, not fraud/critical; SA 450 para A2) | Materiality itself: set by the partner in `engagement.json` (SA 320); agents never change it |
| Recording remediation for recurring-rule control deficiencies (IFC, s.143(3)(i)) | — |
| The daily digest to the partner (internal) | — |

Nothing is ever filed on a government portal.

### Figure control

Agents never compute amounts. `caectl brief` puts every number the agents may
use into `brief.json`, including the evidence values. `draft-queries` rejects
any ₹/Rs/INR amount (and any "lakh"/"crore" wording) in model-written text that
isn't already in the brief. The reporter must pass `verify-figures` before the
digest goes out. The email's "Amount involved" line is filled in by code.

### Routes

`caectl brief` assigns each exception a default route. The decider may raise
scrutiny (query → escalate, close_trivial → query) but never lower it.

| Route | Meaning | Who acts |
|---|---|---|
| `escalate` | Fraud rule, critical, or ≥ performance materiality | Partner approves before any client contact |
| `query` | Above clearly trivial | Decider drafts, partner approves the batch |
| `close_trivial` | Clearly trivial, not fraud/critical | Executor closes |
| `review_response` | Management replied | Decider: accept / follow up / escalate |
| `chase` | Query overdue, reminder due | `caectl remind` |
| `report_nonresponse` | No reply after max reminders | Digest flags it (possible SA 705 scope limitation) |
| `release` / `resolve` | Partner approved | Executor applies |
| `await_partner` / `wait` / `hold` / `none` | Nothing to do now | — |

## Set up

1. **CAE user for the agents**: create a user with the `manager` role in CAE.
   Don't reuse the seed login.
2. **Credentials**: create `cae/fieldwork/.env` (git-ignored):
   ```
   CAE_EMAIL=agents@yourfirm.in
   CAE_PASSWORD=...
   # optional: without SMTP, emails are staged in outbox/ready/ for you to send
   CAE_SMTP_HOST=smtp.yourmail.com
   CAE_SMTP_PORT=587
   CAE_SMTP_USER=...
   CAE_SMTP_PASSWORD=...
   CAE_MAIL_FROM=audit@yourfirm.in
   ```
3. **Each client**: in Claude Code, run `/fieldwork setup <client>`. It finds
   the company in CAE, asks you for the materiality figures and contacts, and
   writes `cae/fieldwork/<client>/engagement.json` (template:
   [`../fieldwork/engagement.example.json`](../fieldwork/engagement.example.json)).
4. **Schedule**: on the machine that runs the CAE stack, add to `crontab -e`:
   ```
   40 6 * * 1-6  /path/to/repo/cae/scripts/fieldwork_cycle.sh >> /path/to/repo/cae/fieldwork/cron.log 2>&1
   ```
   The runner gives each unattended run only these tools: `caectl`, reading
   files, writing inside `cae/fieldwork/`, and the four subagents.
5. **Data**: drop Tally/Excel exports into `cae/fieldwork/<client>/inbox/`,
   named `<type>_anything.xlsx|.csv`, where type is one of `sales_invoices`,
   `purchase_invoices`, `journal_entries`, `bank_transactions`, `inventory` or
   `payroll`. The next run uploads them and moves them to `inbox/loaded/<date>/`.

## Your daily loop

Read the digest (email, or `cae/fieldwork/<client>/digest-latest.md`), then
clear the queue:

```
/fieldwork approve acme A-0007
/fieldwork reject acme A-0008 "Drop item 3; ask for the GRN instead of the PO"
/fieldwork status acme
```

An approved query batch goes out immediately. A rejection note is what the
decider follows when redrafting on the next run. Without Claude Code, the
same works directly:
`python3 cae/scripts/caectl.py -e cae/fieldwork/acme/engagement.json approval-decide A-0007 approve`.

## Files per client

```
cae/fieldwork/<client>/          (git-ignored: client data)
  engagement.json                materiality, contacts, day counts
  state.json                     approval queue + reminder log (caectl only)
  brief.json  digest-latest.md   latest
  inbox/  inbox/loaded/<date>/   data drop
  outbox/drafts/ ready/ sent/    query previews, emails to send by hand, sent mail
  runs/<date>/                   brief, research, decisions, queries, execution,
                                 working-paper.xlsx, digest — the SA 230 trail
```

## Known limits

- **CAE must be reachable** from wherever the runner runs. The stack is local
  (localhost:8080), so schedule on that machine, not in a cloud session.
- **Ingested files import asynchronously.** `sync` can start before the worker
  finishes a large import. If so, the new data is audited on the next run.
- **Management responses** are read from CAE (`POST /queries/{id}/respond`).
  Replies that arrive only by email must be entered into CAE before the
  agents can review them.
- **Statutory references** in the brief are candidates for your consideration
  (`STATUTORY_REFS` in `caectl.py`), not a reporting conclusion. Extend that
  map when you add rules.
