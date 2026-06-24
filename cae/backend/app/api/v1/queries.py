"""Management query lifecycle endpoints."""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.workflow import ManagementQuery, QueryResponse
from app.models.audit import AuditException
from app.schemas.queries import QueryCreate, QueryOut, QueryResponseCreate, QueryResponseOut, QueryStatusUpdate
from app.utils.rbac import get_current_user, require_roles
from app.models.user import User

router = APIRouter()

_QUERY_COUNTER = 0


def _next_query_no(db: Session) -> str:
    count = db.query(ManagementQuery).count()
    return f"MQ-{count + 1:04d}"


@router.post("", response_model=QueryOut, status_code=status.HTTP_201_CREATED)
def create_query(
    payload: QueryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    exc = db.query(AuditException).filter(AuditException.id == payload.exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    query = ManagementQuery(
        id=uuid.uuid4(),
        exception_id=payload.exception_id,
        company_id=exc.company_id,
        query_no=_next_query_no(db),
        process_area=payload.process_area,
        severity=payload.severity,
        description=payload.description,
        evidence_summary=payload.evidence_summary,
        suggested_question=payload.suggested_question,
        assigned_to_user_id=payload.assigned_to_user_id,
        due_date=payload.due_date,
        status="open",
        raised_by_user_id=current_user.id,
        raised_at=datetime.utcnow(),
    )
    db.add(query)

    exc.status = "query_raised"
    db.commit()
    db.refresh(query)
    return query


@router.get("", response_model=list[QueryOut])
def list_queries(
    company_id: uuid.UUID,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(ManagementQuery).filter(ManagementQuery.company_id == company_id)
    if status:
        q = q.filter(ManagementQuery.status == status)
    if severity:
        q = q.filter(ManagementQuery.severity == severity)
    return q.order_by(ManagementQuery.raised_at.desc()).all()


@router.get("/{query_id}", response_model=QueryOut)
def get_query(
    query_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ManagementQuery).filter(ManagementQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    return query


@router.post("/{query_id}/respond", response_model=QueryResponseOut, status_code=status.HTTP_201_CREATED)
def respond_to_query(
    query_id: uuid.UUID,
    payload: QueryResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ManagementQuery).filter(ManagementQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    response = QueryResponse(
        id=uuid.uuid4(),
        query_id=query_id,
        response_text=payload.response_text,
        responded_by_user_id=current_user.id,
        responded_at=datetime.utcnow(),
        attachment_url=payload.attachment_url,
    )
    db.add(response)
    query.status = "responded"
    db.commit()
    db.refresh(response)
    return response


@router.patch("/{query_id}/status")
def update_query_status(
    query_id: uuid.UUID,
    payload: QueryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    query = db.query(ManagementQuery).filter(ManagementQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    query.status = payload.status
    if payload.auditor_comment:
        query.auditor_comment = payload.auditor_comment
    db.commit()
    return {"query_id": str(query.id), "status": query.status}
