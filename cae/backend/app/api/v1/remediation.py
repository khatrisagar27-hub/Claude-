"""Remediation action tracker endpoints."""
import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.workflow import RemediationAction
from app.utils.rbac import get_current_user, require_roles
from app.models.user import User

router = APIRouter()


class RemediationCreate(BaseModel):
    company_id: uuid.UUID
    exception_id: uuid.UUID
    control_gap_description: str
    root_cause: Optional[str] = None
    action_plan: str
    responsible_user_id: Optional[uuid.UUID] = None
    responsible_name: Optional[str] = None
    target_date: Optional[date] = None


class RemediationUpdate(BaseModel):
    action_plan: Optional[str] = None
    target_date: Optional[date] = None
    actual_closure_date: Optional[date] = None
    evidence_url: Optional[str] = None
    retest_outcome: Optional[str] = None
    residual_risk_score: Optional[float] = None
    status: Optional[str] = None
    responsible_name: Optional[str] = None


class RemediationOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    exception_id: Optional[uuid.UUID]
    control_gap_description: str
    root_cause: Optional[str]
    action_plan: str
    target_date: Optional[date]
    actual_closure_date: Optional[date]
    evidence_url: Optional[str]
    retest_outcome: Optional[str]
    residual_risk_score: Optional[float]
    responsible_name: Optional[str] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[RemediationOut])
def list_remediations(
    company_id: uuid.UUID,
    retest_outcome: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(RemediationAction).filter(RemediationAction.company_id == company_id)
    if retest_outcome:
        q = q.filter(RemediationAction.retest_outcome == retest_outcome)
    return q.order_by(RemediationAction.target_date).all()


@router.post("", response_model=RemediationOut, status_code=status.HTTP_201_CREATED)
def create_remediation(
    payload: RemediationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    from datetime import timedelta
    from app.models.audit import AuditException

    data = payload.model_dump()
    data["responsible_name"] = data.get("responsible_name") or current_user.full_name
    data["target_date"] = data.get("target_date") or (date.today() + timedelta(days=30))
    action = RemediationAction(id=uuid.uuid4(), status="open", **data)
    db.add(action)
    exc = db.query(AuditException).filter(AuditException.id == payload.exception_id).first()
    if exc and exc.status in ("open", "in_review", "management_query_sent"):
        exc.status = "remediation_in_progress"
    db.commit()
    db.refresh(action)
    return action


@router.put("/{action_id}", response_model=RemediationOut)
def update_remediation(
    action_id: uuid.UUID,
    payload: RemediationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    action = db.query(RemediationAction).filter(RemediationAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Remediation action not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(action, k, v)
    if payload.actual_closure_date and not payload.status:
        action.status = "closed"
    if action.retest_outcome == "effective" and action.exception_id:
        # an effective re-test resolves the exception the action was raised for
        from app.models.audit import AuditException
        exc = db.query(AuditException).filter(AuditException.id == action.exception_id).first()
        if exc and exc.status in ("open", "in_review", "management_query_sent", "remediation_in_progress"):
            exc.status = "resolved"
            exc.resolved_on = action.actual_closure_date or date.today()
    db.commit()
    db.refresh(action)
    return action
