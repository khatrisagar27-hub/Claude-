"""Rules, audit runs, and the findings review workflow."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.engagements import get_engagement, open_engagement
from app.audit.engine import run_audit
from app.audit.registry import load_rules
from app.db import get_db
from app.models import Action, AuditRun, Engagement, Finding, FindingNote, RuleSetting, User, now
from app.security import current_user, reviewer

router = APIRouter(tags=["audit"])

# from-status -> statuses a user may move it to. "cleared" is set only by the engine.
TRANSITIONS = {
    "open": {"queried", "confirmed", "dismissed"},
    "queried": {"open", "confirmed", "dismissed"},
    "confirmed": {"resolved", "open"},
    "dismissed": {"open"},
    "resolved": {"open"},
    "cleared": set(),
}
STAFF_MAY = {("open", "queried"), ("queried", "open")}  # everything else needs a manager or partner
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class RulePatch(BaseModel):
    enabled: bool | None = None
    params: dict[str, float] | None = None


class StatusChange(BaseModel):
    status: str
    note: str = ""


class NoteIn(BaseModel):
    kind: str = "comment"
    body: str = Field(min_length=1, max_length=5000)


class ActionIn(BaseModel):
    description: str = Field(min_length=1, max_length=2000)
    owner: str = ""
    due_date: date | None = None


class ActionPatch(BaseModel):
    is_done: bool


# ── rules ──

@router.get("/engagements/{engagement_id}/rules")
def list_rules(eng: Engagement = Depends(get_engagement), db: Session = Depends(get_db)):
    overrides = {s.rule_code: s for s in db.scalars(select(RuleSetting).where(RuleSetting.engagement_id == eng.id))}
    hits = dict(db.execute(select(Finding.rule_code, func.count()).where(
        Finding.engagement_id == eng.id, Finding.status.in_(("open", "queried", "confirmed"))).group_by(Finding.rule_code)).all())
    out = []
    for code, r in sorted(load_rules().items()):
        s = overrides.get(code)
        values = {**r.defaults(), **(s.params if s else {})}
        out.append({"code": code, "area": r.area, "name": r.name, "description": r.description, "law": r.law,
                    "severity": r.severity, "fraud": r.fraud, "needs": list(r.needs), "enabled": s.enabled if s else True,
                    "active_findings": hits.get(code, 0),
                    "params": [{"name": k, "label": label, "default": default, "value": values[k]}
                               for k, (default, label) in r.params.items()]})
    return out


@router.patch("/engagements/{engagement_id}/rules/{code}")
def edit_rule(code: str, body: RulePatch, eng: Engagement = Depends(open_engagement), db: Session = Depends(get_db),
              _: User = Depends(reviewer)):
    rule = load_rules().get(code)
    if not rule:
        raise HTTPException(404, "Unknown rule")
    setting = db.scalar(select(RuleSetting).where(RuleSetting.engagement_id == eng.id, RuleSetting.rule_code == code))
    if not setting:
        setting = RuleSetting(engagement_id=eng.id, rule_code=code, enabled=True, params={})
        db.add(setting)
    if body.enabled is not None:
        setting.enabled = body.enabled
    if body.params is not None:
        unknown = set(body.params) - set(rule.params)
        if unknown:
            raise HTTPException(422, f"Unknown parameter(s): {', '.join(sorted(unknown))}")
        if any(v < 0 for v in body.params.values()):
            raise HTTPException(422, "Parameters cannot be negative")
        setting.params = {**(setting.params or {}), **body.params}
    db.commit()
    return {"code": code, "enabled": setting.enabled, "params": {**rule.defaults(), **setting.params}}


# ── runs ──

def run_out(r: AuditRun, full: bool = False) -> dict:
    s = r.summary or {}
    out = {"id": r.id, "started_at": r.started_at, "finished_at": r.finished_at, "run_by": r.run_by,
           "as_at": s.get("as_at"), "new": s.get("new", 0), "updated": s.get("updated", 0), "cleared": s.get("cleared", 0),
           "reopened": s.get("reopened", 0), "risk": (s.get("risk") or {}).get("overall", 0),
           "errors": sum(1 for x in s.get("rules", []) if x["status"] == "error")}
    if full:
        out["rules"] = s.get("rules", [])
    return out


@router.post("/engagements/{engagement_id}/runs")
def start_run(eng: Engagement = Depends(open_engagement), db: Session = Depends(get_db), user: User = Depends(current_user)):
    return run_out(run_audit(db, eng, user.name), full=True)


@router.get("/engagements/{engagement_id}/runs")
def list_runs(eng: Engagement = Depends(get_engagement), db: Session = Depends(get_db)):
    runs = db.scalars(select(AuditRun).where(AuditRun.engagement_id == eng.id).order_by(AuditRun.id.desc()).limit(30)).all()
    return [run_out(r, full=(i == 0)) for i, r in enumerate(runs)]


# ── findings ──

def finding_out(f: Finding, full: bool = False) -> dict:
    out = {"id": f.id, "rule_code": f.rule_code, "area": f.area, "title": f.title, "severity": f.severity,
           "impact": float(f.impact), "status": f.status, "fraud": f.is_fraud_indicator, "updated_at": f.updated_at}
    if full:
        out.update(detail=f.detail, law=f.law, evidence=f.evidence, first_run_id=f.first_run_id, last_run_id=f.last_run_id,
                   allowed=sorted(TRANSITIONS[f.status]),
                   notes=[{"id": n.id, "kind": n.kind, "body": n.body, "author": n.author, "created_at": n.created_at} for n in f.notes],
                   actions=[{"id": a.id, "description": a.description, "owner": a.owner, "due_date": a.due_date,
                             "is_done": a.is_done, "done_at": a.done_at} for a in f.actions])
    return out


def get_finding(finding_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)) -> Finding:
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")
    return finding


def editable(finding: Finding = Depends(get_finding), db: Session = Depends(get_db)) -> Finding:
    if db.get(Engagement, finding.engagement_id).is_closed:
        raise HTTPException(409, "This engagement is closed. Reopen it to make changes.")
    return finding


@router.get("/engagements/{engagement_id}/findings")
def list_findings(eng: Engagement = Depends(get_engagement), db: Session = Depends(get_db),
                  status: str | None = None, severity: str | None = None, area: str | None = None,
                  rule: str | None = None, fraud: bool | None = None, q: str | None = None,
                  page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500)):
    query = select(Finding).where(Finding.engagement_id == eng.id)
    if status == "active":
        query = query.where(Finding.status.in_(("open", "queried", "confirmed")))
    elif status:
        query = query.where(Finding.status == status)
    for column, value in ((Finding.severity, severity), (Finding.area, area), (Finding.rule_code, rule)):
        if value:
            query = query.where(column == value)
    if fraud is not None:
        query = query.where(Finding.is_fraud_indicator == fraud)
    if q:
        query = query.where(Finding.title.ilike(f"%{q}%"))
    items = sorted(db.scalars(query).all(), key=lambda f: (SEVERITY_RANK[f.severity], -float(f.impact), f.id))
    start = (page - 1) * page_size
    return {"total": len(items), "impact": round(sum(float(f.impact) for f in items), 2),
            "items": [finding_out(f) for f in items[start:start + page_size]]}


@router.get("/findings/{finding_id}")
def read_finding(finding: Finding = Depends(get_finding)):
    return finding_out(finding, full=True)


@router.post("/findings/{finding_id}/status")
def change_status(body: StatusChange, finding: Finding = Depends(editable), db: Session = Depends(get_db),
                  user: User = Depends(current_user)):
    if body.status not in TRANSITIONS[finding.status]:
        raise HTTPException(409, f"A finding that is {finding.status} cannot be moved to {body.status}")
    if user.role == "staff" and (finding.status, body.status) not in STAFF_MAY:
        raise HTTPException(403, "Concluding on a finding requires a manager or partner")
    if body.status in ("confirmed", "dismissed", "resolved") and not body.note.strip():
        raise HTTPException(422, "Record the basis for this conclusion in the note")
    label = f"{finding.status} → {body.status}"
    finding.notes.append(FindingNote(kind="status", author=user.name, body=f"{label}: {body.note.strip()}" if body.note.strip() else label))
    finding.status = body.status
    db.commit()
    return finding_out(finding, full=True)


@router.post("/findings/{finding_id}/notes")
def add_note(body: NoteIn, finding: Finding = Depends(editable), db: Session = Depends(get_db), user: User = Depends(current_user)):
    if body.kind not in ("comment", "query", "response"):
        raise HTTPException(422, "kind must be comment, query or response")
    finding.notes.append(FindingNote(kind=body.kind, author=user.name, body=body.body.strip()))
    if body.kind == "query" and finding.status == "open":
        finding.status = "queried"
    db.commit()
    return finding_out(finding, full=True)


@router.post("/findings/{finding_id}/actions")
def add_action(body: ActionIn, finding: Finding = Depends(editable), db: Session = Depends(get_db), _: User = Depends(current_user)):
    finding.actions.append(Action(**body.model_dump()))
    db.commit()
    return finding_out(finding, full=True)


@router.patch("/actions/{action_id}")
def edit_action(action_id: int, body: ActionPatch, db: Session = Depends(get_db), _: User = Depends(current_user)):
    action = db.get(Action, action_id)
    if not action:
        raise HTTPException(404, "Action not found")
    finding = editable(db.get(Finding, action.finding_id), db)
    action.is_done, action.done_at = body.is_done, now() if body.is_done else None
    db.commit()
    return finding_out(finding, full=True)


@router.get("/engagements/{engagement_id}/actions")
def list_actions(eng: Engagement = Depends(get_engagement), db: Session = Depends(get_db)):
    pairs = db.execute(select(Action, Finding).join(Finding, Finding.id == Action.finding_id)
                       .where(Finding.engagement_id == eng.id).order_by(Action.is_done, Action.due_date)).all()
    today = date.today()
    return [{"id": a.id, "finding_id": f.id, "finding": f.title, "rule_code": f.rule_code, "description": a.description,
             "owner": a.owner, "due_date": a.due_date, "is_done": a.is_done,
             "overdue": bool(a.due_date and not a.is_done and a.due_date < today)} for a, f in pairs]
