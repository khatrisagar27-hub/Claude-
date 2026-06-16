"""Audit rule management endpoints."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import AuditRule
from app.utils.rbac import get_current_user, require_roles
from app.models.user import User

router = APIRouter()


class RuleOut(BaseModel):
    id: str
    rule_code: str
    name: str
    description: str | None
    business_area: str
    severity: str
    risk_category: str | None
    frequency: str
    is_enabled: bool

    model_config = {"from_attributes": True}


def _rule_to_out(r: AuditRule) -> RuleOut:
    return RuleOut(
        id=str(r.id),
        rule_code=r.rule_code,
        name=r.rule_name,
        description=r.description,
        business_area=r.category,
        severity=r.severity,
        risk_category=r.risk_area,
        frequency=r.run_frequency,
        is_enabled=r.is_active,
    )


@router.get("", response_model=list[RuleOut])
def list_rules(
    company_id: Optional[uuid.UUID] = None,
    business_area: Optional[str] = None,
    severity: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AuditRule)
    if company_id:
        q = q.filter(AuditRule.company_id == company_id)
    if business_area:
        q = q.filter(AuditRule.category == business_area)
    if severity:
        q = q.filter(AuditRule.severity == severity)
    if is_enabled is not None:
        q = q.filter(AuditRule.is_active == is_enabled)
    return [_rule_to_out(r) for r in q.order_by(AuditRule.rule_code).all()]


@router.put("/{rule_id}/toggle")
def toggle_rule(
    rule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager")),
):
    rule = db.query(AuditRule).filter(AuditRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = not rule.is_active
    db.commit()
    return {"rule_id": str(rule.id), "is_enabled": rule.is_active}


@router.post("/{rule_id}/test")
def test_rule(
    rule_id: uuid.UUID,
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    rule = db.query(AuditRule).filter(AuditRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    try:
        from app.engines.audit_engine import AuditEngine
        engine = AuditEngine(db, str(company_id))
        result = engine.test_rule(rule)
        return {"rule_code": rule.rule_code, "matches": result}
    except Exception as e:
        return {"rule_code": rule.rule_code, "error": str(e)}
