"""Runs the rule catalogue for an engagement and keeps findings in step with the data.

Re-running is safe by design:
  • an exception seen before  → same finding row is refreshed; status and notes are kept
  • an exception no longer in the data → an open/queried finding becomes "cleared"
  • a cleared exception that comes back → reopened
Findings a reviewer has concluded on (confirmed / dismissed / resolved) are never
changed by a run.
"""
import hashlib
import time
import traceback

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.risk import score
from app.audit.dataset import load_data, make_ctx
from app.audit.registry import SEVERITIES, load_rules
from app.models import AuditRun, Engagement, Finding, FindingNote, RuleSetting, now


def grade(base: str, impact: float, materiality: float, trivial: float) -> str:
    """Severity from the rule's inherent level and the amount involved."""
    if materiality > 0 and impact >= materiality:
        return "critical"
    if trivial > 0 and 0 < impact < trivial:
        return SEVERITIES[max(0, SEVERITIES.index(base) - 1)]
    return base


def fingerprint(key: str) -> str:
    return hashlib.sha1(key.encode()).hexdigest()


def run_audit(db: Session, eng: Engagement, user: str = "", today=None) -> AuditRun:
    rules = load_rules()
    run = AuditRun(engagement_id=eng.id, run_by=user)
    db.add(run)
    db.flush()

    data, ctx = load_data(db, eng.id), make_ctx(db, eng, today)
    overrides = {s.rule_code: s for s in db.scalars(select(RuleSetting).where(RuleSetting.engagement_id == eng.id))}
    existing = {(f.rule_code, f.fingerprint): f
                for f in db.scalars(select(Finding).where(Finding.engagement_id == eng.id))}
    counts, results, seen, ran_ok = {"new": 0, "updated": 0, "cleared": 0, "reopened": 0}, [], set(), set()

    for code in sorted(rules):
        rule, setting = rules[code], overrides.get(code)
        result = {"code": code, "name": rule.name, "area": rule.area, "hits": 0, "ms": 0, "error": ""}
        results.append(result)
        if setting and not setting.enabled:
            result["status"] = "disabled"
            continue
        missing = [n for n in rule.needs if not data.has(n)]
        if missing:
            result["status"], result["error"] = "no_data", "Needs: " + ", ".join(missing)
            continue
        params = {**rule.defaults(), **(setting.params if setting else {})}
        started = time.perf_counter()
        try:
            hits = rule.fn(data, params, ctx) or []
        except Exception:  # one faulty rule must not stop the audit; it is reported as failed
            result["status"], result["error"] = "error", traceback.format_exc(limit=3)
            continue
        finally:
            result["ms"] = round((time.perf_counter() - started) * 1000)
        result["status"], result["hits"] = "ok", len(hits)
        ran_ok.add(code)

        for hit in hits:
            fp = fingerprint(hit.key)
            if (code, fp) in seen:
                continue
            seen.add((code, fp))
            impact = round(float(hit.impact or 0), 2)
            values = dict(title=hit.title[:300], detail=hit.detail, impact=impact, evidence=hit.evidence,
                          severity=grade(hit.severity or rule.severity, impact, ctx.materiality, ctx.trivial),
                          law=rule.law, area=rule.area, is_fraud_indicator=rule.fraud, last_run_id=run.id)
            finding = existing.get((code, fp))
            if finding is None:
                db.add(Finding(engagement_id=eng.id, rule_code=code, fingerprint=fp, first_run_id=run.id, **values))
                counts["new"] += 1
                continue
            for name, value in values.items():
                setattr(finding, name, value)
            if finding.status == "cleared":
                finding.status = "open"
                finding.notes.append(FindingNote(kind="status", author="system",
                                                 body=f"Reopened: exception reappeared in run #{run.id}."))
                counts["reopened"] += 1
            else:
                counts["updated"] += 1

    for (code, fp), finding in existing.items():
        if code in ran_ok and (code, fp) not in seen and finding.status in ("open", "queried"):
            finding.status = "cleared"
            finding.notes.append(FindingNote(kind="status", author="system",
                                             body=f"Cleared: no longer present in the data as of run #{run.id}."))
            counts["cleared"] += 1

    db.flush()
    findings = db.scalars(select(Finding).where(Finding.engagement_id == eng.id)).all()
    run.summary = {**counts, "rules": results, "risk": score(findings),
                   "as_at": ctx.as_at.strftime("%d-%m-%Y")}
    run.finished_at = now()
    db.commit()
    return run
