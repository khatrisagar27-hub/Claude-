"""Read-only views built from findings and data: dashboard, GST, working capital, working paper."""
import re

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.gst_reco import COLUMNS, reconcile, summarise
from app.analytics.risk import ACTIVE, score
from app.analytics.working_capital import working_capital
from app.api.data import XLSX
from app.api.engagements import get_engagement
from app.audit.dataset import load_data, make_ctx
from app.audit.helpers import rows
from app.db import get_db
from app.models import AuditRun, Engagement, Finding, User
from app.security import current_user
from app.workpaper import build_workpaper

router = APIRouter(tags=["insights"])


@router.get("/engagements/{engagement_id}/dashboard")
def dashboard(eng: Engagement = Depends(get_engagement), db: Session = Depends(get_db)):
    findings = db.scalars(select(Finding).where(Finding.engagement_id == eng.id)).all()
    active = [f for f in findings if f.status in ACTIVE]
    by_status, by_severity = {}, {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        by_status[f.status] = by_status.get(f.status, 0) + 1
    for f in active:
        by_severity[f.severity] += 1
    runs = db.scalars(select(AuditRun).where(AuditRun.engagement_id == eng.id).order_by(AuditRun.id.desc()).limit(12)).all()
    top = sorted(active, key=lambda f: -float(f.impact))[:10]
    return {
        "risk": score(findings), "by_status": by_status, "by_severity": by_severity,
        "active": len(active), "impact": round(sum(float(f.impact) for f in active), 2),
        "fraud_indicators": sum(1 for f in active if f.is_fraud_indicator),
        "last_run": ({"id": runs[0].id, "finished_at": runs[0].finished_at, "as_at": runs[0].summary.get("as_at"),
                      "not_run": sum(1 for r in runs[0].summary.get("rules", []) if r["status"] == "no_data"),
                      "failed": sum(1 for r in runs[0].summary.get("rules", []) if r["status"] == "error")} if runs else None),
        "trend": [{"run": r.id, "date": r.started_at, "risk": (r.summary.get("risk") or {}).get("overall", 0),
                   "new": r.summary.get("new", 0), "cleared": r.summary.get("cleared", 0)} for r in reversed(runs)],
        "top": [{"id": f.id, "rule_code": f.rule_code, "title": f.title, "severity": f.severity, "impact": float(f.impact),
                 "status": f.status} for f in top],
    }


@router.get("/engagements/{engagement_id}/gst")
def gst(eng: Engagement = Depends(get_engagement), db: Session = Depends(get_db), status: str | None = None,
        limit: int = Query(500, ge=1, le=5000)):
    data = load_data(db, eng.id)
    if data.gstr2b.empty or data.purchases.empty:
        return {"ready": False, "missing": [n for n, f in (("purchases", data.purchases), ("gstr2b", data.gstr2b)) if f.empty]}
    reco = reconcile(data.purchases, data.gstr2b)
    summary = summarise(reco)
    lines = reco[reco["status"] == status] if status else reco[reco["status"] != "matched"]
    return {"ready": True, **summary, "total_lines": int(len(lines)), "lines": rows(lines, COLUMNS, limit)}


@router.get("/engagements/{engagement_id}/working-capital")
def wc(eng: Engagement = Depends(get_engagement), db: Session = Depends(get_db)):
    return working_capital(load_data(db, eng.id), make_ctx(db, eng))


@router.get("/engagements/{engagement_id}/workpaper")
def workpaper(eng: Engagement = Depends(get_engagement), db: Session = Depends(get_db), user: User = Depends(current_user),
              include_closed: bool = False):
    # Header value: keep to characters that cannot break out of the quoted filename.
    ascii_name = re.sub(r"[^A-Za-z0-9 ._()&-]", "", f"Working paper - {eng.client.name} - {eng.name}")[:150] + ".xlsx"
    return Response(build_workpaper(db, eng, user.name, include_closed), media_type=XLSX,
                    headers={"Content-Disposition": f'attachment; filename="{ascii_name}"'})
