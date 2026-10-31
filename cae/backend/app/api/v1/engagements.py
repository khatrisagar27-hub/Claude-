"""Audit engagements — a Statutory audit of a financial year or an Internal audit of a period."""
import uuid
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, model_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import AuditException
from app.models.engagement import AuditEngagement
from app.models.tenant import Company
from app.models.user import User
from app.utils.rbac import get_current_user, require_roles

router = APIRouter()


class EngagementIn(BaseModel):
    company_id: uuid.UUID
    audit_type: Literal["statutory", "internal"]
    financial_year: Optional[int] = None       # statutory: FY start year (2024 = FY 2024-25)
    period_from: Optional[date] = None         # internal: any period
    period_to: Optional[date] = None
    name: Optional[str] = None
    caro_applicable: bool = False
    ifc_applicable: bool = False
    tax_audit_applicable: bool = False
    materiality: Optional[float] = None
    scope_notes: Optional[str] = None

    @model_validator(mode="after")
    def _period(self):
        if self.audit_type == "statutory":
            if not self.financial_year:
                raise ValueError("A statutory audit needs a financial year")
            self.period_from, self.period_to = date(self.financial_year, 4, 1), date(self.financial_year + 1, 3, 31)
        else:
            if not (self.period_from and self.period_to):
                raise ValueError("An internal audit needs a period (from and to dates)")
            if self.period_from > self.period_to:
                raise ValueError("Period 'from' is after 'to'")
            self.caro_applicable = self.ifc_applicable = self.tax_audit_applicable = False
        return self


class EngagementUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[Literal["planning", "fieldwork", "reporting", "closed"]] = None
    caro_applicable: Optional[bool] = None
    ifc_applicable: Optional[bool] = None
    tax_audit_applicable: Optional[bool] = None
    materiality: Optional[float] = None
    scope_notes: Optional[str] = None


class EngagementOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    label: str
    audit_type: str
    financial_year: Optional[int]
    period_from: date
    period_to: date
    status: str
    caro_applicable: bool
    ifc_applicable: bool
    tax_audit_applicable: bool
    materiality: Optional[float]
    scope_notes: Optional[str]
    exception_count: int = 0
    rules_in_scope: int = 0
    last_run_at: Optional[str] = None

    model_config = {"from_attributes": True}


def _out(db: Session, e: AuditEngagement) -> EngagementOut:
    from app.models.audit import AuditRule
    from app.models.ingestion import SyncJob
    from app.statutory.reporting import in_scope

    n = db.query(func.count(AuditException.id)).filter(AuditException.engagement_id == e.id).scalar() or 0
    codes = [c for (c,) in db.query(AuditRule.rule_code).filter(AuditRule.company_id == e.company_id,
                                                                  AuditRule.is_active == True).all()]  # noqa: E712
    last = (db.query(func.max(SyncJob.completed_at)).filter(SyncJob.engagement_id == e.id,
                                                            SyncJob.status == "completed").scalar())
    return EngagementOut(
        id=e.id, company_id=e.company_id, name=e.name, label=e.label, audit_type=e.audit_type,
        financial_year=e.financial_year, period_from=e.period_from, period_to=e.period_to, status=e.status,
        caro_applicable=e.caro_applicable, ifc_applicable=e.ifc_applicable,
        tax_audit_applicable=e.tax_audit_applicable,
        materiality=float(e.materiality) if e.materiality is not None else None, scope_notes=e.scope_notes,
        exception_count=n, rules_in_scope=sum(1 for c in codes if in_scope(c, e)),
        last_run_at=last.isoformat() if last else None,
    )


def _get(db: Session, engagement_id: uuid.UUID, user: User) -> AuditEngagement:
    e = (db.query(AuditEngagement).join(Company, Company.id == AuditEngagement.company_id)
         .filter(AuditEngagement.id == engagement_id, Company.tenant_id == user.tenant_id).first())
    if not e:
        raise HTTPException(status_code=404, detail="Engagement not found")
    return e


@router.get("", response_model=list[EngagementOut])
def list_engagements(company_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (db.query(AuditEngagement).filter(AuditEngagement.company_id == company_id)
            .order_by(AuditEngagement.period_to.desc(), AuditEngagement.created_at.desc()).all())
    return [_out(db, e) for e in rows]


@router.post("", response_model=EngagementOut, status_code=status.HTTP_201_CREATED)
def create_engagement(payload: EngagementIn, db: Session = Depends(get_db),
                      current_user: User = Depends(require_roles("super_admin", "partner", "manager"))):
    company = db.query(Company).filter(Company.id == payload.company_id, Company.tenant_id == current_user.tenant_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    e = AuditEngagement(id=uuid.uuid4(), created_by_user_id=current_user.id,
                        **payload.model_dump(exclude={"name"}),
                        name=payload.name or "")
    e.name = payload.name or e.label
    db.add(e)
    db.commit()
    db.refresh(e)
    return _out(db, e)


@router.get("/{engagement_id}", response_model=EngagementOut)
def get_engagement_detail(engagement_id: uuid.UUID, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    return _out(db, _get(db, engagement_id, current_user))


@router.put("/{engagement_id}", response_model=EngagementOut)
def update_engagement(engagement_id: uuid.UUID, payload: EngagementUpdate, db: Session = Depends(get_db),
                      current_user: User = Depends(require_roles("super_admin", "partner", "manager"))):
    e = _get(db, engagement_id, current_user)
    for k, v in payload.model_dump(exclude_none=True).items():
        if e.audit_type == "internal" and k in ("caro_applicable", "ifc_applicable", "tax_audit_applicable"):
            continue
        setattr(e, k, v)
    db.commit()
    db.refresh(e)
    return _out(db, e)


@router.post("/{engagement_id}/run")
def run_engagement(engagement_id: uuid.UUID, background: BackgroundTasks, db: Session = Depends(get_db),
                   current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor"))):
    """Run every in-scope rule over the engagement period, then fraud, risk and WC analytics."""
    from app.api.v1.ingestion import job_out
    from app.models.ingestion import SyncJob
    from app.workers.dispatch import enqueue
    from app.workers.tasks import execute_audit_cycle, run_audit_cycle

    e = _get(db, engagement_id, current_user)
    job = SyncJob(id=uuid.uuid4(), company_id=e.company_id, job_type=f"{e.audit_type}_audit", status="queued",
                  triggered_by=current_user.full_name, engagement_id=e.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    mode = enqueue(run_audit_cycle, execute_audit_cycle, str(e.company_id), str(job.id), str(e.id), background=background)
    return job_out(job, mode)


@router.get("/{engagement_id}/summary")
def engagement_summary(engagement_id: uuid.UUID, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    """Findings rolled up the way the audit type reports them: by CARO / tax-audit / IFC clause for a
    statutory audit, by process for an internal audit."""
    from app.utils.engagement_export import build_summary

    return build_summary(db, _get(db, engagement_id, current_user))
