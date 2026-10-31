"""Live Tally Prime data — gateway status, company list and import into CAE (read-only on Tally)."""
import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tenant import Company
from app.models.user import User
from app.utils.rbac import get_current_user, require_roles

router = APIRouter()


@router.get("/status")
def tally_status(current_user: User = Depends(get_current_user)):
    """Is the Tally XML gateway reachable, and which companies are open in Tally?"""
    from app.connectors.tally_live import Gateway, TallyError

    gw = Gateway()
    try:
        banner = gw.ping()
        companies = gw.companies()
        return {"url": gw.url, "running": True, "message": banner, "companies": companies}
    except TallyError as e:
        return {"url": gw.url, "running": False, "message": str(e), "companies": []}


class TallyImportIn(BaseModel):
    tally_company: str
    from_date: date
    to_date: date
    company_id: Optional[uuid.UUID] = None     # CAE company to load into; blank = create one named after Tally's
    extended_ledger_details: bool = False       # GSTIN / MSME sub-lists — slow on some Tally files

    @model_validator(mode="after")
    def _window(self):
        if self.from_date > self.to_date:
            raise ValueError("'from' is after 'to'")
        if (self.to_date - self.from_date).days > 400:
            raise ValueError("Import at most one financial year at a time")
        return self


@router.post("/import")
def import_from_tally(payload: TallyImportIn, background: BackgroundTasks, db: Session = Depends(get_db),
                      current_user: User = Depends(require_roles("super_admin", "partner", "manager"))):
    from app.api.v1.ingestion import job_out
    from app.models.ingestion import SyncJob
    from app.rules.catalogue import sync_rules
    from app.workers.dispatch import enqueue
    from app.workers.tasks import execute_tally_import, import_from_tally as task

    if payload.company_id:
        company = db.query(Company).filter(Company.id == payload.company_id,
                                           Company.tenant_id == current_user.tenant_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
    else:
        company = (db.query(Company).filter(Company.tenant_id == current_user.tenant_id,
                                            Company.name == payload.tally_company[:300]).first())
        if company is None:
            company = Company(id=uuid.uuid4(), tenant_id=current_user.tenant_id, name=payload.tally_company[:300])
            db.add(company)
            db.commit()
        sync_rules(db, company.id)   # the rule catalogue for a new company
    job = SyncJob(id=uuid.uuid4(), company_id=company.id, job_type="tally_import", status="queued",
                  triggered_by=current_user.full_name)
    db.add(job)
    db.commit()
    db.refresh(job)
    mode = enqueue(task, execute_tally_import, str(job.id), str(company.id), payload.tally_company,
                   payload.from_date.isoformat(), payload.to_date.isoformat(), payload.extended_ledger_details,
                   background=background)
    return {"company_id": str(company.id), "company_name": company.name, "job": job_out(job, mode)}
