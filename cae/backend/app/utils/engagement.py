"""Engagement scoping shared by the API: which exceptions a screen shows, and how a finding is
labelled for a Statutory vs an Internal audit."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def get_engagement(db: Session, engagement_id: Optional[uuid.UUID], company_id: Optional[uuid.UUID] = None):
    if not engagement_id:
        return None
    from app.models.engagement import AuditEngagement

    eng = db.query(AuditEngagement).filter(AuditEngagement.id == engagement_id).first()
    if not eng or (company_id and eng.company_id != company_id):
        raise HTTPException(status_code=404, detail="Engagement not found for this company")
    return eng


def exception_scope(engagement_id: Optional[uuid.UUID]):
    """Exceptions of one engagement, or (no engagement) continuous-monitoring exceptions only."""
    from app.models.audit import AuditException

    return AuditException.engagement_id == engagement_id if engagement_id else AuditException.engagement_id.is_(None)


def severity_order():
    from sqlalchemy import case
    from app.models.audit import AuditException

    return case(SEVERITY_RANK, value=AuditException.severity, else_=9)


def enrich(exc, rule_code: Optional[str], engagement) -> dict:
    """Exception fields plus its audit-type view: reporting references (statutory) or process
    (internal), and whether it reaches the engagement's materiality."""
    from app.statutory.reporting import process_for, refs_for

    impact = float(exc.financial_impact) if exc.financial_impact is not None else None
    materiality = float(engagement.materiality) if engagement is not None and engagement.materiality else None
    return {
        "id": exc.id, "company_id": exc.company_id, "rule_id": exc.rule_id, "rule_code": rule_code,
        "engagement_id": exc.engagement_id, "detected_on": exc.detected_on, "category": exc.category,
        "title": exc.title, "description": exc.description, "severity": exc.severity,
        "risk_impact": exc.risk_impact, "financial_impact": exc.financial_impact,
        "supporting_data": exc.supporting_data, "ai_analysis": exc.ai_analysis, "status": exc.status,
        "process": process_for(rule_code) if rule_code else None,
        "audit_refs": refs_for(rule_code, engagement) if rule_code else [],
        "material": (impact is not None and impact >= materiality) if materiality else None,
    }
