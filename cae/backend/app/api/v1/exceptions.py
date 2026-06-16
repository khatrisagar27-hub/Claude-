"""Exception management endpoints."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import AuditException
from app.schemas.exceptions import ExceptionOut, ExceptionListOut, ExceptionStatusUpdate, AiExplainOut
from app.utils.rbac import get_current_user, require_roles
from app.models.user import User

router = APIRouter()

_VALID_TRANSITIONS = {
    "open": ["in_review", "management_query_sent", "remediation_in_progress", "closed", "false_positive"],
    "in_review": ["management_query_sent", "remediation_in_progress", "resolved", "closed", "false_positive"],
    "management_query_sent": ["remediation_in_progress", "resolved", "closed"],
    "remediation_in_progress": ["resolved", "closed"],
    "resolved": ["closed"],
}


@router.get("", response_model=ExceptionListOut)
def list_exceptions(
    company_id: uuid.UUID,
    page: int = 1,
    page_size: int = 50,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AuditException).filter(AuditException.company_id == company_id)
    if severity:
        q = q.filter(AuditException.severity == severity)
    if status:
        q = q.filter(AuditException.status == status)
    if category:
        q = q.filter(AuditException.category == category)

    total = q.count()
    items = q.order_by(AuditException.detected_on.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ExceptionListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{exception_id}", response_model=ExceptionOut)
def get_exception(
    exception_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exc = db.query(AuditException).filter(AuditException.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")
    return exc


@router.patch("/{exception_id}/status")
def update_status(
    exception_id: uuid.UUID,
    payload: ExceptionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    exc = db.query(AuditException).filter(AuditException.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    allowed = _VALID_TRANSITIONS.get(exc.status, [])
    if payload.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Cannot transition from {exc.status} to {payload.status}")

    exc.status = payload.status
    if payload.comment:
        exc.resolution_notes = payload.comment
    db.commit()
    return {"exception_id": str(exc.id), "status": exc.status}


@router.post("/{exception_id}/ai-explain", response_model=AiExplainOut)
async def ai_explain(
    exception_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exc = db.query(AuditException).filter(AuditException.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    from app.engines.ai_engine import AIEngine
    engine = AIEngine()
    result = await engine.explain_exception(exc)

    exc.ai_analysis = result.get("explanation", "")
    exc.ai_recommendation = result.get("suggested_remediation", "")
    db.commit()

    return AiExplainOut(
        exception_id=exc.id,
        explanation=result.get("explanation", ""),
        business_impact=result.get("business_impact", ""),
        fraud_risk=result.get("fraud_risk", ""),
        recommended_query=result.get("recommended_query", ""),
        suggested_remediation=result.get("suggested_remediation", ""),
    )
