#!/usr/bin/env python3
"""caectl — the deterministic tool layer the audit-fieldwork agents drive CAE with.

The agents (.claude/agents/fw-*.md) never call the CAE API directly and never
compute a figure themselves. Every amount, materiality band, age, due date,
statutory reference and default route they act on is produced here, in code a
reviewer can read and challenge (CLAUDE.md: deterministic code computes every
number; the model only explains).

The autonomy boundary is enforced here too, not in a prompt:
  * query emails to the client carry figures, so they are drafted, queued for
    the partner, and only released after `approval-decide ... approve`;
  * reminders carry no figures and are rendered entirely by code;
  * fraud / critical / at-or-above-performance-materiality exceptions cannot be
    queried, resolved or marked false positive without the partner's approval;
  * every ₹ amount in model-written text must already exist in the brief.

Stdlib only, so it runs on any machine with Python 3.10+.

Environment:
  CAE_URL            API base, default http://localhost:8080/api/v1 (nginx)
  CAE_EMAIL          login of the CAE user the agents act as (manager role)
  CAE_PASSWORD       its password
  CAE_SMTP_HOST      optional; without it emails are rendered to outbox/ready/
  CAE_SMTP_PORT      default 587 (STARTTLS); 465 uses SSL
  CAE_SMTP_USER, CAE_SMTP_PASSWORD, CAE_MAIL_FROM

Every command prints JSON on stdout. On failure it prints {"error": ...} on
stderr and exits 1. Engagement-scoped commands take -e pointing at
fieldwork/<client>/engagement.json; approval state, outbox and inbox live
beside it.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import smtplib
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path

DEFAULT_URL = "http://localhost:8080/api/v1"

TERMINAL_STATUSES = {"resolved", "closed", "false_positive"}
TRIVIAL_ELIGIBLE_SEVERITIES = {"low", "medium", "info"}
REPORT_KINDS = {"working-paper", "exception-summary", "audit-deck"}
INGEST_TYPES = ("sales_invoices", "purchase_invoices", "journal_entries",
                "bank_transactions", "inventory", "payroll")
INGEST_EXTENSIONS = {".xlsx", ".xls", ".csv"}

ENGAGEMENT_DEFAULTS = {
    "reminder_interval_days": 3,
    "max_reminders": 3,
    "auto_send_reminders": True,
    "firm_name": None,
}

# Applicability is a statutory call, so it lives in code (CLAUDE.md), not in a
# prompt. These are *candidate* references for the partner's consideration; they
# never decide reporting on their own.
FRAUD_REF = (
    "SA 240; CARO 2020 para 3(xi)(a) fraud by/on the company; "
    "Companies Act s.143(12) / Form ADT-4 if it meets the reporting threshold"
)
IFC_REF = "IFC over financial reporting — Companies Act s.143(3)(i)"
STATUTORY_REFS: dict[str, list[str]] = {
    "PAY-005": ["CARO 2020 para 3(vii)(a): undisputed statutory dues (PF/ESI) not deposited regularly"],
    "PUR-031": [
        "MSMED Act 2006 s.15/s.16: payment beyond 45 days attracts compound interest",
        "Schedule III MSME dues disclosure; Income-tax Act s.43B(h)",
    ],
    "TRE-001": ["Income-tax Act s.40A(3): cash payment above ₹10,000 to a person in a day is disallowed"],
    "SAL-021": ["CGST Rules r.48(4)/(5): invoice without IRN is not a valid tax invoice"],
    "SAL-007": ["CGST Rules r.138: e-way bill required above ₹50,000 consignment value"],
    "TRE-006": [
        "CARO 2020 para 3(iv): loans/advances to directors — Companies Act s.185/s.186",
        "CARO 2020 para 3(xiii): related party transactions — Companies Act s.177/s.188",
    ],
    "PUR-022": ["CARO 2020 para 3(xiii): possible undisclosed related party — Companies Act s.188"],
    "INV-001": ["CARO 2020 para 3(ii)(a): inventory discrepancies of 10% or more in aggregate per class"],
    "INV-002": ["CARO 2020 para 3(ii)(a): inventory discrepancies of 10% or more in aggregate per class"],
    "INV-007": ["CARO 2020 para 3(ii)(a): inventory discrepancies of 10% or more in aggregate per class"],
}
IFC_CATEGORIES = {"Authorization", "Financial Reporting"}

# route rule -> (action, reason). route_for() checks them in this order.
ROUTES = {
    "R0": ("none", "Exception already resolved/closed."),
    "R1": ("await_partner", "Escalation is waiting for the partner."),
    "R2": ("hold", "Partner rejected the escalation — partner handles it personally."),
    "R3": ("resolve", "Partner approved the resolution — apply it."),
    "R4": ("await_partner", "Resolution is waiting for the partner."),
    "R5": ("review_response", "Management has responded — review the response."),
    "R6": ("report_nonresponse", "No response after the maximum reminders — report to partner (SA 500/SA 705)."),
    "R7": ("chase", "Query overdue and a reminder is due — `caectl remind` sends it."),
    "R8": ("wait", "Query open — not yet due, or reminded recently."),
    "R9": ("release", "Partner approved the query batch — release it."),
    "R10": ("await_partner", "Query batch is waiting for the partner."),
    "R11": ("escalate", "Fraud-category rule (SA 240) — partner decides before any client contact."),
    "R12": ("escalate", "Critical severity — partner decides before any client contact."),
    "R13": ("escalate", "Impact at or above performance materiality — partner decides."),
    "R14": ("close_trivial", "Clearly trivial and not fraud/critical — close; not accumulated (SA 450 para A2)."),
    "R15": ("query", "Partner approved the escalation — draft the management query."),
    "R16": ("query", "Above clearly trivial — draft a management query."),
}


class CaeError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


# --------------------------------------------------------------------------- #
# Figures — the only place amounts are produced or checked
# --------------------------------------------------------------------------- #

def money(value) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def inr(value) -> str | None:
    """Format as ₹1,23,456.78 (Indian digit grouping)."""
    amount = money(value)
    if amount is None:
        return None
    sign = "-" if amount < 0 else ""
    whole, frac = f"{abs(amount):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    return f"{sign}₹{whole}.{frac}"


_AMOUNT_RE = re.compile(r"(?:₹|\bRs\.?|\bINR)\s*([0-9](?:[0-9,]*[0-9])?(?:\.[0-9]+)?)", re.IGNORECASE)
_WORD_AMOUNT_RE = re.compile(r"\b[0-9]+(?:\.[0-9]+)?\s*(?:lakhs?|lacs?|crores?|cr)\b", re.IGNORECASE)


def figures_in(obj) -> set[Decimal]:
    """Every number in a brief (values, numeric strings and ₹ strings), to 2dp."""
    found: set[Decimal] = set()

    def add(raw):
        try:
            found.add(abs(Decimal(str(raw).replace(",", "")).quantize(Decimal("0.01"))))
        except (InvalidOperation, ValueError):
            pass

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, (list, tuple)):
            for v in node:
                walk(v)
        elif isinstance(node, bool) or node is None:
            return
        elif isinstance(node, (int, float, Decimal)):
            add(node)
        elif isinstance(node, str):
            add(node)
            for m in _AMOUNT_RE.finditer(node):
                add(m.group(1))

    walk(obj)
    return found


def unverified_figures(text: str, allowed: set[Decimal]) -> list[str]:
    """Amounts in model-written text that do not appear in the brief."""
    bad = [m.group(0) for m in _WORD_AMOUNT_RE.finditer(text)]
    for m in _AMOUNT_RE.finditer(text):
        try:
            value = abs(Decimal(m.group(1).replace(",", "")).quantize(Decimal("0.01")))
        except InvalidOperation:
            bad.append(m.group(0))
            continue
        if value not in allowed:
            bad.append(m.group(0))
    return bad


def band_for(impact: Decimal | None, eng: dict) -> str:
    if impact is None:
        return "no_amount"
    impact = abs(impact)
    if impact >= money(eng["overall_materiality"]):
        return "above_overall_materiality"
    if impact >= money(eng["performance_materiality"]):
        return "above_performance_materiality"
    if impact > money(eng["clearly_trivial"]):
        return "above_clearly_trivial"
    return "clearly_trivial"


def needs_partner(*, severity: str, band: str, fraud: bool) -> bool:
    return fraud or severity == "critical" or band in ("above_overall_materiality", "above_performance_materiality")


def statutory_refs_for(rule_code: str | None, risk_category: str | None) -> list[str]:
    refs = list(STATUTORY_REFS.get(rule_code or "", []))
    if risk_category == "Fraud":
        refs.append(FRAUD_REF)
    if risk_category in IFC_CATEGORIES:
        refs.append(IFC_REF)
    return refs


def route_for(*, status: str, severity: str, band: str, fraud: bool, queries: list[dict],
              escalation: dict | None, batch: dict | None, resolution: dict | None) -> str:
    """Default action for one exception. Order matters; see ROUTES."""
    if status in TERMINAL_STATUSES:
        return "R0"
    if escalation and escalation["status"] == "pending":
        return "R1"
    if escalation and escalation["status"] == "rejected":
        return "R2"
    if resolution and resolution["status"] == "approved":
        return "R3"
    if resolution and resolution["status"] == "pending":
        return "R4"
    if any(q["status"] == "responded" for q in queries):
        return "R5"
    open_queries = [q for q in queries if q["status"] == "open"]
    if open_queries:
        if any(q["days_overdue"] > 0 and q["reminder_due"] and q["reminders_sent"] >= q["max_reminders"]
               for q in open_queries):
            return "R6"
        if any(q["days_overdue"] > 0 and q["reminder_due"] for q in open_queries):
            return "R7"
        return "R8"
    if batch and batch["status"] == "approved":
        return "R9"
    if batch and batch["status"] == "pending":
        return "R10"
    approved = bool(escalation and escalation["status"] in ("approved", "done"))
    if not approved:
        if fraud:
            return "R11"
        if severity == "critical":
            return "R12"
        if band in ("above_overall_materiality", "above_performance_materiality"):
            return "R13"
    if band == "clearly_trivial" and severity in TRIVIAL_ELIGIBLE_SEVERITIES and not fraud:
        return "R14"
    return "R15" if approved else "R16"


# --------------------------------------------------------------------------- #
# Engagement file and approval state
# --------------------------------------------------------------------------- #

def load_engagement(path: str | Path) -> dict:
    path = Path(path)
    try:
        eng = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise CaeError(f"engagement file not found: {path}")
    except json.JSONDecodeError as exc:
        raise CaeError(f"engagement file is not valid JSON: {exc}")

    required = ["company_id", "client_name", "period_label", "overall_materiality",
                "performance_materiality", "clearly_trivial", "query_response_days",
                "remediation_target_days", "recurrence_threshold", "remediation_owner",
                "partner", "management_contacts"]
    missing = [k for k in required if eng.get(k) in (None, "", [])]
    if missing:
        raise CaeError(f"engagement file missing: {', '.join(missing)}")
    try:
        uuid.UUID(str(eng["company_id"]))
    except ValueError:
        raise CaeError("engagement company_id is not a UUID")
    om, pm, ct = (money(eng[k]) for k in ("overall_materiality", "performance_materiality", "clearly_trivial"))
    if not (Decimal("0") < ct < pm <= om):
        raise CaeError("thresholds must satisfy 0 < clearly_trivial < performance_materiality <= overall_materiality")
    for k, v in ENGAGEMENT_DEFAULTS.items():
        eng.setdefault(k, v)
    for k in ("query_response_days", "remediation_target_days", "recurrence_threshold",
              "reminder_interval_days", "max_reminders"):
        if not isinstance(eng[k], int) or isinstance(eng[k], bool) or eng[k] < 1:
            raise CaeError(f"{k} must be a positive whole number")
    if not eng["partner"].get("email") or not all(c.get("email") for c in eng["management_contacts"]):
        raise CaeError("partner and every management contact need an email")
    eng["_dir"] = str(path.resolve().parent)
    return eng


def _engdir(eng: dict, *parts: str) -> Path:
    p = Path(eng["_dir"]).joinpath(*parts)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_state(eng: dict) -> dict:
    p = Path(eng["_dir"]) / "state.json"
    state = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    state.setdefault("approvals", {})
    state.setdefault("reminders", {})
    return state


def save_state(eng: dict, state: dict) -> None:
    p = Path(eng["_dir"]) / "state.json"
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def _new_approval(state: dict, today: date, **fields) -> str:
    aid = f"A-{len(state['approvals']) + 1:04d}"
    state["approvals"][aid] = {
        "status": "pending", "created_on": today.isoformat(), "decided_on": None, "note": None, **fields,
    }
    return aid


def latest_approval(state: dict, kind: str, exception_id: str, statuses: tuple[str, ...]) -> dict | None:
    latest = None
    for aid, a in state["approvals"].items():
        if a["kind"] == kind and exception_id in a.get("exception_ids", []) and a["status"] in statuses:
            latest = {"id": aid, **a}
    return latest


def decide_approval(eng: dict, approval_id: str, decision: str, note: str | None, today: date) -> dict:
    state = load_state(eng)
    a = state["approvals"].get(approval_id)
    if a is None:
        raise CaeError(f"no approval {approval_id}")
    if a["status"] != "pending":
        raise CaeError(f"{approval_id} is already {a['status']}")
    a["status"] = "approved" if decision == "approve" else "rejected"
    a["decided_on"] = today.isoformat()
    a["note"] = note
    save_state(eng, state)
    return {"id": approval_id, **a}


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

def urllib_transport(method: str, url: str, headers: dict, body: bytes | None):
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except urllib.error.URLError as exc:
        raise CaeError(f"cannot reach CAE at {url}: {exc.reason}")


def _multipart(fields: dict, filename: str, content: bytes) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    out += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n").encode() + content + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return out, f"multipart/form-data; boundary={boundary}"


class Cae:
    def __init__(self, base_url: str, transport=urllib_transport):
        self.base_url = base_url.rstrip("/")
        self.transport = transport
        self.token: str | None = None

    def login(self, email: str, password: str) -> None:
        body = self._call("POST", "/auth/login", json_body={"email": email, "password": password}, auth=False)
        self.token = body["access_token"]

    def _call(self, method, path, *, params=None, json_body=None, data=None, content_type=None,
              auth=True, raw=False):
        url = self.base_url + path
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        headers = {"Accept": "application/json"}
        body = data
        if json_body is not None:
            body = json.dumps(json_body).encode()
            headers["Content-Type"] = "application/json"
        elif content_type:
            headers["Content-Type"] = content_type
        if auth:
            if not self.token:
                raise CaeError("not logged in")
            headers["Authorization"] = f"Bearer {self.token}"
        status, content = self.transport(method, url, headers, body)
        if status >= 400:
            try:
                detail = json.loads(content).get("detail", content.decode(errors="replace"))
            except (ValueError, AttributeError):
                detail = content.decode(errors="replace")[:500]
            raise CaeError(f"{method} {path} -> {status}: {detail}", status)
        if raw:
            return content
        return json.loads(content) if content else None

    # reads
    def companies(self):
        return self._call("GET", "/companies")

    def rules(self):
        return self._call("GET", "/rules")

    def exceptions(self, company_id):
        items, page = [], 1
        while True:
            body = self._call("GET", "/exceptions", params={"company_id": company_id, "page": page, "page_size": 200})
            items.extend(body["items"])
            if len(items) >= body["total"] or not body["items"]:
                return items
            page += 1

    def exception(self, exception_id):
        return self._call("GET", f"/exceptions/{exception_id}")

    def queries(self, company_id):
        return self._call("GET", "/queries", params={"company_id": company_id})

    def query(self, query_id):
        return self._call("GET", f"/queries/{query_id}")

    def remediations(self, company_id):
        return self._call("GET", "/remediation", params={"company_id": company_id})

    def fraud_indicators(self, company_id):
        return self._call("GET", "/risk/fraud-indicators", params={"company_id": company_id})

    def itc_risk(self, company_id):
        return self._call("GET", "/gst/itc-risk", params={"company_id": company_id})

    def jobs(self, company_id, limit=5):
        return self._call("GET", "/ingestion/jobs", params={"company_id": company_id, "limit": limit})

    # writes
    def sync(self, company_id):
        return self._call("POST", "/ingestion/sync", params={"company_id": company_id, "job_type": "full_audit"})

    def upload(self, company_id, file_type, path: Path):
        body, ctype = _multipart({"company_id": company_id, "file_type": file_type}, path.name, path.read_bytes())
        return self._call("POST", "/ingestion/upload", data=body, content_type=ctype)

    def set_status(self, exception_id, status, comment):
        return self._call("PATCH", f"/exceptions/{exception_id}/status",
                          json_body={"status": status, "comment": comment})

    def create_query(self, payload):
        return self._call("POST", "/queries", json_body=payload)

    def update_query_status(self, query_id, status, comment):
        return self._call("PATCH", f"/queries/{query_id}/status",
                          json_body={"status": status, "auditor_comment": comment})

    def create_remediation(self, payload):
        return self._call("POST", "/remediation", json_body=payload)

    def report(self, kind, company_id, period=None):
        return self._call("POST", f"/reports/{kind}", params={"company_id": company_id, "period": period}, raw=True)


# --------------------------------------------------------------------------- #
# The brief — every number the agents may quote, and the default route
# --------------------------------------------------------------------------- #

def _parse_date(value) -> date | None:
    return date.fromisoformat(str(value)[:10]) if value else None


def build_brief(*, eng: dict, as_of: date, exceptions: list[dict], rules: list[dict],
                queries: list[dict], remediations: list[dict], state: dict,
                itc_risk: dict | None = None, fraud_indicators: list | None = None) -> dict:
    rule_by_id = {str(r["id"]): r for r in rules}

    queries_by_exc: dict[str, list[dict]] = defaultdict(list)
    for q in queries:
        due = _parse_date(q.get("due_date"))
        days_overdue = (as_of - due).days if (due and q["status"] == "open" and as_of > due) else 0
        sent = state["reminders"].get(str(q["id"]), [])
        last = _parse_date(sent[-1]) if sent else None
        queries_by_exc[str(q["exception_id"])].append({
            "query_id": str(q["id"]), "query_no": q["query_no"], "status": q["status"],
            "raised_on": str(q.get("raised_at", ""))[:10] or None,
            "due_date": q.get("due_date"), "days_overdue": days_overdue,
            "reminders_sent": len(sent), "max_reminders": eng["max_reminders"],
            "reminder_due": last is None or (as_of - last).days >= eng["reminder_interval_days"],
            "responses": [{"responded_at": r.get("responded_at"), "text": r.get("response_text"),
                           "attachment_url": r.get("attachment_url")} for r in q.get("responses", [])],
        })

    remediated_exc = {str(r["exception_id"]) for r in remediations if r.get("exception_id")}

    items = []
    for e in exceptions:
        rule = rule_by_id.get(str(e.get("rule_id")), {})
        code, risk_category = rule.get("rule_code"), rule.get("risk_category")
        impact = money(e.get("financial_impact"))
        band = band_for(impact, eng)
        fraud = risk_category == "Fraud"
        exc_id = str(e["id"])
        qs = queries_by_exc.get(exc_id, [])
        escalation = latest_approval(state, "escalation", exc_id, ("pending", "approved", "rejected", "done"))
        batch = latest_approval(state, "queries", exc_id, ("pending", "approved"))
        resolution = latest_approval(state, "resolution", exc_id, ("pending", "approved"))
        rejected_batch = latest_approval(state, "queries", exc_id, ("rejected",))
        route = route_for(status=e["status"], severity=e["severity"], band=band, fraud=fraud, queries=qs,
                          escalation=escalation, batch=batch, resolution=resolution)
        detected = _parse_date(e.get("detected_on"))
        items.append({
            "exception_id": exc_id,
            "rule_code": code,
            "rule_name": rule.get("name"),
            "risk_category": risk_category,
            "title": e.get("title"),
            "description": e.get("description"),
            "category": e.get("category"),
            "severity": e["severity"],
            "status": e["status"],
            "detected_on": e.get("detected_on"),
            "age_days": (as_of - detected).days if detected else None,
            "financial_impact": str(impact) if impact is not None else None,
            "financial_impact_inr": inr(impact),
            "band": band,
            "fraud_flag": fraud,
            "partner_sign_off_required": needs_partner(severity=e["severity"], band=band, fraud=fraud),
            "statutory_refs": statutory_refs_for(code, risk_category),
            "queries": qs,
            "escalation": escalation,
            "pending_or_approved_batch": batch and batch["id"],
            "last_rejected_batch_note": rejected_batch and rejected_batch.get("note"),
            "resolution": resolution,
            "remediation_exists": exc_id in remediated_exc,
            "route": ROUTES[route][0],
            "route_rule": route,
            "route_reason": ROUTES[route][1],
            "evidence": e.get("supporting_data"),
        })

    # Recurrence of the same rule signals a control (IFC) deficiency, not a one-off.
    by_code: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        if it["rule_code"]:
            by_code[it["rule_code"]].append(it)
    deficiencies = []
    for code, group in sorted(by_code.items()):
        if len(group) < eng["recurrence_threshold"] or any(it["remediation_exists"] for it in group):
            continue
        anchor = max(group, key=lambda it: Decimal(it["financial_impact"] or "0"))
        total = sum((Decimal(it["financial_impact"] or "0") for it in group), Decimal("0"))
        deficiencies.append({
            "rule_code": code, "rule_name": group[0]["rule_name"], "occurrences": len(group),
            "total_impact_inr": inr(total), "anchor_exception_id": anchor["exception_id"],
            "statutory_refs": group[0]["statutory_refs"],
        })

    open_items = [it for it in items if it["status"] not in TERMINAL_STATUSES]
    open_impact = sum((Decimal(it["financial_impact"]) for it in open_items if it["financial_impact"]), Decimal("0"))
    pm = money(eng["performance_materiality"])
    pending = [{"id": k, **v} for k, v in state["approvals"].items() if v["status"] == "pending"]

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "as_of": as_of.isoformat(),
        "client_name": eng["client_name"],
        "company_id": str(eng["company_id"]),
        "period_label": eng["period_label"],
        "thresholds": {
            "overall_materiality_inr": inr(eng["overall_materiality"]),
            "performance_materiality_inr": inr(pm),
            "clearly_trivial_inr": inr(eng["clearly_trivial"]),
            "query_response_days": eng["query_response_days"],
            "query_due_date_if_released_today": (as_of + timedelta(days=eng["query_response_days"])).isoformat(),
            "remediation_target_date_if_raised_today": (as_of + timedelta(days=eng["remediation_target_days"])).isoformat(),
        },
        "summary": {
            "total_exceptions": len(items),
            "open_exceptions": len(open_items),
            "open_impact_inr": inr(open_impact),
            # SA 450: uncorrected items are judged in aggregate, not one by one.
            "open_impact_at_or_above_performance_materiality": open_impact >= pm,
            "by_status": dict(Counter(it["status"] for it in items)),
            "by_severity_open": dict(Counter(it["severity"] for it in open_items)),
            "by_route": dict(Counter(it["route"] for it in items)),
            "pending_approvals": len(pending),
        },
        "control_deficiency_candidates": deficiencies,
        "pending_approvals": pending,
        "approved_batches": [k for k, v in state["approvals"].items()
                             if v["kind"] == "queries" and v["status"] == "approved"],
        "itc_at_risk": None if itc_risk is None else {
            "total_inr": inr(itc_risk.get("total_itc_risk")),
            "periods_at_risk": itc_risk.get("periods_at_risk"),
            "details": [{"period": d["period"], "risk_inr": inr(d["risk_amount"])} for d in itc_risk.get("details", [])],
        },
        "fraud_indicator_count": None if fraud_indicators is None else len(fraud_indicators),
        "exceptions": items,
    }


def fetch_brief(cae: Cae, eng: dict, today: date, *, with_risk: bool = True) -> dict:
    company = str(eng["company_id"])
    return build_brief(
        eng=eng, as_of=today, exceptions=cae.exceptions(company), rules=cae.rules(),
        queries=cae.queries(company), remediations=cae.remediations(company), state=load_state(eng),
        itc_risk=cae.itc_risk(company) if with_risk else None,
        fraud_indicators=cae.fraud_indicators(company) if with_risk else None,
    )


def _item(brief: dict, exception_id: str) -> dict:
    for it in brief["exceptions"]:
        if it["exception_id"] == exception_id:
            return it
    raise CaeError(f"exception {exception_id} is not in this engagement's company")


# --------------------------------------------------------------------------- #
# Email
# --------------------------------------------------------------------------- #

def smtp_mailer_from_env():
    host = os.environ.get("CAE_SMTP_HOST")
    if not host:
        return None
    port = int(os.environ.get("CAE_SMTP_PORT", "587"))
    user, password = os.environ.get("CAE_SMTP_USER"), os.environ.get("CAE_SMTP_PASSWORD")

    def send(msg: EmailMessage) -> None:
        ctx = ssl.create_default_context()
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, context=ctx, timeout=60)
        else:
            server = smtplib.SMTP(host, port, timeout=60)
            server.starttls(context=ctx)
        with server:
            if user:
                server.login(user, password or "")
            server.send_message(msg)
    return send


def _message(eng: dict, subject: str, body: str, kind: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = os.environ.get("CAE_MAIL_FROM") or eng["partner"]["email"]
    msg["To"] = ", ".join(formataddr((c.get("name", ""), c["email"])) for c in eng["management_contacts"])
    msg["Cc"] = formataddr((eng["partner"].get("name", ""), eng["partner"]["email"]))
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg["X-CAE-Kind"] = kind
    msg.set_content(body)
    return msg


def _signoff(eng: dict) -> str:
    lines = ["Regards,", eng["partner"].get("name") or ""]
    if eng.get("firm_name"):
        lines.append(eng["firm_name"])
    return "\n".join(l for l in lines if l)


def render_query_email(eng: dict, brief: dict, queries: list[dict], due: date,
                       query_nos: dict[str, str] | None = None) -> tuple[str, str]:
    names = ", ".join(c.get("name") or c["email"] for c in eng["management_contacts"])
    out = [
        f"Dear {names},",
        "",
        f"As part of our audit of {eng['client_name']} for {eng['period_label']}, we request your "
        f"response to the {len(queries)} matter(s) below by {due.strftime('%d %b %Y')}. Please reply "
        "to this email with the documents asked for against each item.",
    ]
    for n, q in enumerate(queries, 1):
        it = _item(brief, q["exception_id"])
        ref = (query_nos or {}).get(q["exception_id"]) or f"Item {n}"
        out += ["", f"{n}. {ref} — {it['title']}",
                f"   Amount involved: {it['financial_impact_inr'] or 'Not quantified'}",
                f"   Observation: {q['observation']}",
                f"   Our query: {q['question']}"]
        if q.get("documents"):
            out.append("   Please provide:")
            out += [f"     - {d}" for d in q["documents"]]
    out += ["", _signoff(eng)]
    subject = f"Audit queries — {eng['client_name']} — {eng['period_label']}"
    return subject, "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# Guarded workflow commands
# --------------------------------------------------------------------------- #

def draft_queries(cae: Cae, eng: dict, queries_file: Path, today: date) -> dict:
    """Validate the decider's queries, render a preview, queue it for the partner."""
    try:
        payload = json.loads(Path(queries_file).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaeError(f"cannot read queries file: {exc}")
    queries = payload.get("queries") if isinstance(payload, dict) else None
    if not queries:
        raise CaeError('queries file must be {"queries": [{exception_id, observation, question, documents}]}')

    brief = fetch_brief(cae, eng, today, with_risk=False)
    allowed = figures_in(brief)
    problems, seen = [], set()
    for q in queries:
        exc_id = str(q.get("exception_id", ""))
        if exc_id in seen:
            problems.append(f"{exc_id}: listed twice")
        seen.add(exc_id)
        try:
            it = _item(brief, exc_id)
        except CaeError as exc:
            problems.append(str(exc))
            continue
        # The decider may raise scrutiny (close_trivial -> query) but never lower it.
        if it["route"] not in ("query", "close_trivial"):
            problems.append(f"{exc_id}: route is {it['route']} ({it['route_reason']}) — cannot be queried")
        for field in ("observation", "question"):
            if not str(q.get(field, "")).strip():
                problems.append(f"{exc_id}: {field} is empty")
        text = " ".join([str(q.get("observation", "")), str(q.get("question", ""))] +
                        [str(d) for d in q.get("documents", [])])
        bad = unverified_figures(text, allowed)
        if bad:
            problems.append(f"{exc_id}: amounts not in the brief: {', '.join(bad)} — copy figures from the brief or drop them")
    if problems:
        raise CaeError("draft rejected: " + "; ".join(problems))

    state = load_state(eng)
    exc_ids = [str(q["exception_id"]) for q in queries]
    total = sum((Decimal(_item(brief, e)["financial_impact"] or "0") for e in exc_ids), Decimal("0"))
    aid = _new_approval(
        state, today, kind="queries", exception_ids=exc_ids,
        summary=f"{len(queries)} management {'query' if len(queries) == 1 else 'queries'} to "
                f"{', '.join(c['email'] for c in eng['management_contacts'])}; amount involved {inr(total)}",
    )
    drafts = _engdir(eng, "outbox", "drafts")
    (drafts / f"{aid}-queries.json").write_text(json.dumps({"queries": queries}, indent=2, ensure_ascii=False),
                                                encoding="utf-8")
    due = today + timedelta(days=eng["query_response_days"])
    subject, body = render_query_email(eng, brief, queries, due)
    preview = drafts / f"{aid}-queries.eml"
    preview.write_bytes(_message(eng, subject, body, "queries").as_bytes())
    state["approvals"][aid]["file"] = str(preview)
    save_state(eng, state)
    return {"approval_id": aid, "preview": str(preview), "summary": state["approvals"][aid]["summary"]}


def release_batch(cae: Cae, eng: dict, approval_id: str, today: date, mailer) -> dict:
    """Partner approved: raise the queries in CAE, then send (or stage) the email."""
    state = load_state(eng)
    a = state["approvals"].get(approval_id)
    if a is None or a["kind"] != "queries":
        raise CaeError(f"{approval_id} is not a query batch")
    if a["status"] != "approved":
        raise CaeError(f"{approval_id} is {a['status']} — only an approved batch can be released")
    queries = json.loads((_engdir(eng, "outbox", "drafts") / f"{approval_id}-queries.json").read_text(encoding="utf-8"))["queries"]

    brief = fetch_brief(cae, eng, today, with_risk=False)
    due = today + timedelta(days=eng["query_response_days"])
    query_nos, raised = {}, []
    for q in queries:
        it = _item(brief, q["exception_id"])
        if any(x["status"] in ("open", "responded") for x in it["queries"]):
            raise CaeError(f"{q['exception_id']} already has a live query — refusing to raise a duplicate")
        created = cae.create_query({
            "exception_id": q["exception_id"], "process_area": it["category"], "severity": it["severity"],
            "description": q["observation"],
            "evidence_summary": "; ".join(q.get("documents", [])) or "See query",
            "suggested_question": q["question"], "due_date": due.isoformat(),
        })
        query_nos[q["exception_id"]] = created["query_no"]
        raised.append(created["query_no"])

    subject, body = render_query_email(eng, brief, queries, due, query_nos)
    msg = _message(eng, subject, body, "queries")
    sent = False
    if mailer is not None:
        mailer(msg)
        sent = True
    folder = _engdir(eng, "outbox", "sent" if sent else "ready")
    path = folder / f"{approval_id}-queries.eml"
    path.write_bytes(msg.as_bytes())

    a["status"] = "done"
    a["done_on"] = today.isoformat()
    a["released_file"] = str(path)
    save_state(eng, state)
    return {"approval_id": approval_id, "queries_raised": raised, "due_date": due.isoformat(),
            "sent": sent, "file": str(path),
            "action_for_partner": None if sent else f"SMTP not configured — send {path} yourself today"}


def remind(cae: Cae, eng: dict, today: date, mailer) -> dict:
    """Chase overdue queries. Rendered by code only; carries no figures."""
    brief = fetch_brief(cae, eng, today, with_risk=False)
    due = [(it, q) for it in brief["exceptions"] if it["route"] == "chase"
           for q in it["queries"] if q["status"] == "open" and q["days_overdue"] > 0 and q["reminder_due"]
           and q["reminders_sent"] < q["max_reminders"]]
    if not due:
        return {"reminders": 0}
    names = ", ".join(c.get("name") or c["email"] for c in eng["management_contacts"])
    lines = [f"Dear {names},", "",
             f"The following audit queries for {eng['client_name']} ({eng['period_label']}) are past their "
             "response date. Please send your responses and supporting documents at the earliest.", ""]
    for it, q in due:
        lines.append(f"  - {q['query_no']} ({it['category']}): raised {q['raised_on']}, due {q['due_date']}, "
                     f"{q['days_overdue']} day(s) overdue — reminder {q['reminders_sent'] + 1} of {q['max_reminders']}")
    lines += ["", _signoff(eng)]
    msg = _message(eng, f"Reminder: pending audit queries — {eng['client_name']}", "\n".join(lines) + "\n", "reminder")
    if _AMOUNT_RE.search(msg.get_content()) or _WORD_AMOUNT_RE.search(msg.get_content()):
        raise CaeError("reminder text contains an amount — reminders must carry no figures")

    sent = False
    if mailer is not None and eng["auto_send_reminders"]:
        mailer(msg)
        sent = True
    folder = _engdir(eng, "outbox", "sent" if sent else "ready")
    path = folder / f"{today.isoformat()}-reminder.eml"
    path.write_bytes(msg.as_bytes())

    state = load_state(eng)
    for _, q in due:
        state["reminders"].setdefault(q["query_id"], []).append(today.isoformat())
    save_state(eng, state)
    return {"reminders": len(due), "queries": [q["query_no"] for _, q in due], "sent": sent, "file": str(path)}


def send_digest(eng: dict, path: Path, today: date, mailer) -> dict:
    """Email the run digest to the partner only — internal, so no approval gate."""
    msg = EmailMessage()
    msg["From"] = os.environ.get("CAE_MAIL_FROM") or eng["partner"]["email"]
    msg["To"] = formataddr((eng["partner"].get("name", ""), eng["partner"]["email"]))
    msg["Subject"] = f"Fieldwork digest — {eng['client_name']} — {today.isoformat()}"
    msg["Date"] = formatdate(localtime=True)
    msg["X-CAE-Kind"] = "digest"
    msg.set_content(Path(path).read_text(encoding="utf-8"))
    if mailer is None:
        return {"sent": False, "reason": "SMTP not configured — digest is on disk only", "file": str(path)}
    mailer(msg)
    return {"sent": True, "to": eng["partner"]["email"]}


def escalate(cae: Cae, eng: dict, exception_id: str, summary: str, today: date) -> dict:
    brief = fetch_brief(cae, eng, today, with_risk=False)
    it = _item(brief, exception_id)
    if it["route"] == "none":
        raise CaeError("exception is already resolved/closed")
    if it["route"] == "await_partner":
        return {"already_pending": True, "exception_id": exception_id}
    state = load_state(eng)
    aid = _new_approval(state, today, kind="escalation", exception_ids=[exception_id],
                        summary=f"{it['title']} — {it['financial_impact_inr'] or 'not quantified'} — {summary}")
    save_state(eng, state)
    return {"approval_id": aid, **state["approvals"][aid]}


def _resolve(cae: Cae, eng: dict, exception_id: str, target: str, comment: str | None,
             query_id: str | None, today: date) -> dict:
    """Resolve / mark false positive. Serious items need the partner's approval first."""
    brief = fetch_brief(cae, eng, today, with_risk=False)
    it = _item(brief, exception_id)
    state = load_state(eng)
    res = latest_approval(state, "resolution", exception_id, ("pending", "approved"))

    if it["partner_sign_off_required"]:
        if res is None:
            if not comment:
                raise CaeError("--comment is required")
            aid = _new_approval(state, today, kind="resolution", exception_ids=[exception_id],
                                query_id=query_id, target_status=target, comment=comment,
                                summary=f"Mark {target}: {it['title']} — {it['financial_impact_inr'] or 'not quantified'}"
                                        f" — {comment}")
            save_state(eng, state)
            return {"queued_for_partner": aid, "reason": "fraud/critical/at-or-above performance materiality"}
        if res["status"] == "pending":
            raise CaeError(f"awaiting partner on {res['id']}")
        comment, query_id, target = res["comment"], res.get("query_id"), res["target_status"]
    elif not comment:
        raise CaeError("--comment is required")

    if query_id:
        cae.update_query_status(query_id, "resolved", comment)
    result = cae.set_status(exception_id, target, comment)
    if res is not None and res["status"] == "approved":
        state = load_state(eng)
        state["approvals"][res["id"]]["status"] = "done"
        state["approvals"][res["id"]]["done_on"] = today.isoformat()
        save_state(eng, state)
    return {"applied": result, "comment": comment}


def resolve_query(cae: Cae, eng: dict, query_id: str, comment: str | None, today: date) -> dict:
    q = cae.query(query_id)
    if str(q["company_id"]) != str(eng["company_id"]):
        raise CaeError(f"query {query_id} belongs to another company — refusing")
    if q["status"] != "responded":
        raise CaeError(f"query {q['query_no']} is {q['status']}; only a responded query can be resolved")
    return _resolve(cae, eng, str(q["exception_id"]), "resolved", comment, query_id, today)


def false_positive(cae: Cae, eng: dict, exception_id: str, comment: str | None, today: date) -> dict:
    return _resolve(cae, eng, exception_id, "false_positive", comment, None, today)


def close_query_for_followup(cae: Cae, eng: dict, query_id: str, comment: str) -> dict:
    """Response not acceptable: close this query so a sharper follow-up can be drafted."""
    q = cae.query(query_id)
    if str(q["company_id"]) != str(eng["company_id"]):
        raise CaeError(f"query {query_id} belongs to another company — refusing")
    if q["status"] not in ("open", "responded"):
        raise CaeError(f"query {q['query_no']} is already {q['status']}")
    return cae.update_query_status(query_id, "closed", comment)


def close_trivial(cae: Cae, eng: dict, exception_id: str, today: date) -> dict:
    """Close an exception only if the code agrees it is clearly trivial."""
    it = _item(fetch_brief(cae, eng, today, with_risk=False), exception_id)
    if it["route"] != "close_trivial":
        raise CaeError(f"route is {it['route']} ({it['route_reason']}) — refusing to close as trivial")
    comment = (f"Closed as clearly trivial: impact {it['financial_impact_inr']} is at or below the clearly-trivial "
               f"threshold of {inr(eng['clearly_trivial'])}; not accumulated (SA 450 para A2).")
    return cae.set_status(exception_id, "closed", comment)


def remediate(cae: Cae, eng: dict, exception_id: str, *, gap: str, plan: str,
              root_cause: str | None, today: date) -> dict:
    _item(fetch_brief(cae, eng, today, with_risk=False), exception_id)
    return cae.create_remediation({
        "company_id": str(eng["company_id"]), "exception_id": exception_id,
        "control_gap_description": gap, "root_cause": root_cause, "action_plan": plan,
        "responsible_name": eng["remediation_owner"],
        "target_date": (today + timedelta(days=eng["remediation_target_days"])).isoformat(),
    })


def ingest(cae: Cae, eng: dict, today: date) -> dict:
    """Upload every recognised file dropped in <engagement>/inbox/."""
    inbox = _engdir(eng, "inbox")
    uploaded, skipped = [], []
    for path in sorted(p for p in inbox.iterdir() if p.is_file()):
        file_type = next((t for t in INGEST_TYPES if path.name.lower().startswith(t)), None)
        if file_type is None or path.suffix.lower() not in INGEST_EXTENSIONS:
            skipped.append(path.name)
            continue
        result = cae.upload(str(eng["company_id"]), file_type, path)
        dest = _engdir(eng, "inbox", "loaded", today.isoformat())
        shutil.move(str(path), dest / path.name)
        uploaded.append({"file": path.name, "file_type": file_type, "status": result.get("status")})
    return {"uploaded": uploaded,
            "skipped": skipped,
            "naming": f"name files <type>_*.xlsx|.csv, type one of {', '.join(INGEST_TYPES)}" if skipped else None}


def sync_and_wait(cae: Cae, company: str, timeout: int) -> dict:
    job = cae.sync(company)
    deadline = time.monotonic() + timeout
    while job["status"] in ("queued", "running") and time.monotonic() < deadline:
        time.sleep(10)
        job = next((j for j in cae.jobs(company, limit=20) if j["id"] == job["id"]), job)
    if job["status"] in ("queued", "running"):
        job["warning"] = f"still {job['status']} after {timeout}s — is the Celery worker running?"
    return job


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _client(args) -> Cae:
    email, password = os.environ.get("CAE_EMAIL"), os.environ.get("CAE_PASSWORD")
    if not email or not password:
        raise CaeError("set CAE_EMAIL and CAE_PASSWORD")
    cae = Cae(os.environ.get("CAE_URL", DEFAULT_URL))
    cae.login(email, password)
    return cae


def run(args, cae_factory=_client, mailer_factory=smtp_mailer_from_env) -> object:
    eng = load_engagement(args.engagement) if args.engagement else None
    today = date.fromisoformat(args.as_of) if args.as_of else date.today()
    cmd = args.cmd

    if cmd in ("approvals", "approval-decide", "verify-figures", "send-digest"):
        if not eng:
            raise CaeError(f"{cmd} needs -e engagement.json")
        if cmd == "send-digest":
            return send_digest(eng, Path(args.file), today, mailer_factory())
        if cmd == "approvals":
            items = [{"id": k, **v} for k, v in load_state(eng)["approvals"].items()]
            return [a for a in items if not args.status or a["status"] == args.status]
        if cmd == "approval-decide":
            return decide_approval(eng, args.approval_id, args.decision, args.note, today)
        brief_path = Path(eng["_dir"]) / "brief.json"
        if not brief_path.exists():
            raise CaeError("no brief.json yet — run `caectl brief` first")
        allowed = figures_in(json.loads(brief_path.read_text(encoding="utf-8")))
        bad = unverified_figures(Path(args.file).read_text(encoding="utf-8"), allowed)
        return {"file": args.file, "ok": not bad, "unverified": bad}

    cae = cae_factory(args)
    if cmd == "companies":
        return cae.companies()
    if cmd == "rules":
        return cae.rules()
    if not eng:
        raise CaeError(f"{cmd} needs -e engagement.json")
    company = str(eng["company_id"])

    if cmd == "exception":
        exc = cae.exception(args.exception_id)
        if str(exc["company_id"]) != company:
            raise CaeError("exception belongs to another company")
        return exc
    if cmd == "sync":
        return sync_and_wait(cae, company, args.wait)
    if cmd == "ingest":
        return ingest(cae, eng, today)
    if cmd == "brief":
        brief = fetch_brief(cae, eng, today)
        text = json.dumps(brief, indent=2, ensure_ascii=False)
        (Path(eng["_dir"]) / "brief.json").write_text(text, encoding="utf-8")
        run_dir = _engdir(eng, "runs", today.isoformat())
        (run_dir / "brief.json").write_text(text, encoding="utf-8")
        return {"written": str(Path(eng["_dir"]) / "brief.json"), "run_dir": str(run_dir),
                "summary": brief["summary"], "control_deficiency_candidates": len(brief["control_deficiency_candidates"])}
    if cmd == "draft-queries":
        return draft_queries(cae, eng, Path(args.file), today)
    if cmd == "release":
        return release_batch(cae, eng, args.approval_id, today, mailer_factory())
    if cmd == "remind":
        return remind(cae, eng, today, mailer_factory())
    if cmd == "escalate":
        return escalate(cae, eng, args.exception_id, args.summary, today)
    if cmd == "resolve-query":
        return resolve_query(cae, eng, args.query_id, args.comment, today)
    if cmd == "false-positive":
        return false_positive(cae, eng, args.exception_id, args.comment, today)
    if cmd == "close-query":
        return close_query_for_followup(cae, eng, args.query_id, args.comment)
    if cmd == "close-trivial":
        return close_trivial(cae, eng, args.exception_id, today)
    if cmd == "remediate":
        return remediate(cae, eng, args.exception_id, gap=args.gap, plan=args.plan,
                         root_cause=args.root_cause, today=today)
    if cmd == "report":
        if args.kind not in REPORT_KINDS:
            raise CaeError(f"kind must be one of {sorted(REPORT_KINDS)}")
        content = cae.report(args.kind, company, args.period)
        out = _engdir(eng, "runs", today.isoformat()) / f"{args.kind}.{'pdf' if args.kind == 'audit-deck' else 'xlsx'}"
        out.write_bytes(content)
        return {"written": str(out), "bytes": len(content)}
    raise CaeError(f"unknown command {cmd}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="caectl", description=__doc__.splitlines()[0])
    p.add_argument("-e", "--engagement", help="path to fieldwork/<client>/engagement.json")
    p.add_argument("--as-of", help="treat this ISO date as today (re-runs and tests)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("companies", help="list companies (to find company_id)")
    sub.add_parser("rules", help="list audit rules")
    s = sub.add_parser("exception", help="one exception with full evidence")
    s.add_argument("exception_id")
    s = sub.add_parser("sync", help="run the CAE audit cycle and wait for it")
    s.add_argument("--wait", type=int, default=900, help="seconds to wait (default 900)")
    sub.add_parser("ingest", help="upload files dropped in <engagement>/inbox/")
    sub.add_parser("brief", help="write brief.json: figures, bands, routes")

    s = sub.add_parser("draft-queries", help="validate + queue a query batch for the partner")
    s.add_argument("file")
    s = sub.add_parser("release", help="raise + send an approved query batch")
    s.add_argument("approval_id")
    sub.add_parser("remind", help="send code-rendered reminders for overdue queries")
    s = sub.add_parser("escalate", help="queue an exception for the partner")
    s.add_argument("exception_id")
    s.add_argument("--summary", required=True)
    s = sub.add_parser("resolve-query", help="accept a response (partner-gated if serious)")
    s.add_argument("query_id")
    s.add_argument("--comment")
    s = sub.add_parser("false-positive", help="mark false positive (partner-gated if serious)")
    s.add_argument("exception_id")
    s.add_argument("--comment")
    s = sub.add_parser("close-query", help="reject a response so a follow-up can be drafted")
    s.add_argument("query_id")
    s.add_argument("--comment", required=True)
    s = sub.add_parser("close-trivial", help="close a clearly trivial exception")
    s.add_argument("exception_id")
    s = sub.add_parser("remediate", help="record a control-deficiency remediation action")
    s.add_argument("exception_id")
    s.add_argument("--gap", required=True)
    s.add_argument("--plan", required=True)
    s.add_argument("--root-cause")
    s = sub.add_parser("report", help="download a CAE report into runs/<date>/")
    s.add_argument("kind")
    s.add_argument("--period")

    s = sub.add_parser("approvals")
    s.add_argument("--status", choices=["pending", "approved", "rejected", "done"])
    s = sub.add_parser("approval-decide", help="partner: approve or reject")
    s.add_argument("approval_id")
    s.add_argument("decision", choices=["approve", "reject"])
    s.add_argument("--note")
    s = sub.add_parser("verify-figures", help="check every ₹ amount in a file exists in brief.json")
    s.add_argument("file")
    s = sub.add_parser("send-digest", help="email a digest file to the partner only")
    s.add_argument("file")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run(args)
    except CaeError as exc:
        print(json.dumps({"error": str(exc), "status": exc.status}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
