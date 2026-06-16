"""Data ingestion endpoints — file upload and ERP sync trigger."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ingestion import SyncJob, UploadedFile
from app.utils.rbac import get_current_user, require_roles
from app.models.user import User
from app.config import settings
import os

router = APIRouter()


class SyncJobOut(BaseModel):
    id: str
    company_id: str
    job_type: str
    status: str
    records_processed: int
    exceptions_raised: int
    error_message: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


class UploadedFileOut(BaseModel):
    id: str
    company_id: str
    filename: str
    file_type: str
    file_size: Optional[int]
    rows_parsed: Optional[int]
    rows_imported: Optional[int]
    status: str
    created_at: str

    model_config = {"from_attributes": True}


@router.post("/upload", response_model=UploadedFileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    company_id: uuid.UUID = Form(...),
    file_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(company_id))
    os.makedirs(upload_dir, exist_ok=True)

    file_id = uuid.uuid4()
    ext = os.path.splitext(file.filename or "upload")[1]
    dest_path = os.path.join(upload_dir, f"{file_id}{ext}")

    contents = await file.read()
    with open(dest_path, "wb") as f:
        f.write(contents)

    uploaded = UploadedFile(
        id=file_id,
        company_id=company_id,
        filename=file.filename or "upload",
        file_type=file_type,
        file_path=dest_path,
        file_size=len(contents),
        status="uploaded",
        uploaded_by=str(current_user.id),
    )
    db.add(uploaded)
    db.commit()
    db.refresh(uploaded)

    # Trigger async processing in background
    try:
        from app.workers.tasks import process_uploaded_file
        process_uploaded_file.delay(str(file_id))
    except Exception:
        pass  # worker may not be running; file is stored, can process manually

    return UploadedFileOut(
        id=str(uploaded.id),
        company_id=str(uploaded.company_id),
        filename=uploaded.filename,
        file_type=uploaded.file_type,
        file_size=uploaded.file_size,
        rows_parsed=uploaded.rows_parsed,
        rows_imported=uploaded.rows_imported,
        status=uploaded.status,
        created_at=uploaded.created_at.isoformat(),
    )


@router.post("/sync", response_model=SyncJobOut, status_code=status.HTTP_201_CREATED)
def trigger_sync(
    company_id: uuid.UUID,
    job_type: str = "full_audit",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager")),
):
    job = SyncJob(
        id=uuid.uuid4(),
        company_id=company_id,
        job_type=job_type,
        status="queued",
        triggered_by=str(current_user.id),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        from app.workers.tasks import run_audit_cycle
        run_audit_cycle.delay(str(company_id), str(job.id))
    except Exception:
        pass

    return SyncJobOut(
        id=str(job.id),
        company_id=str(job.company_id),
        job_type=job.job_type,
        status=job.status,
        records_processed=job.records_processed,
        exceptions_raised=job.exceptions_raised,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
    )


@router.get("/jobs", response_model=list[SyncJobOut])
def list_jobs(
    company_id: uuid.UUID,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    jobs = (
        db.query(SyncJob)
        .filter(SyncJob.company_id == company_id)
        .order_by(SyncJob.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        SyncJobOut(
            id=str(j.id),
            company_id=str(j.company_id),
            job_type=j.job_type,
            status=j.status,
            records_processed=j.records_processed,
            exceptions_raised=j.exceptions_raised,
            error_message=j.error_message,
            created_at=j.created_at.isoformat(),
        )
        for j in jobs
    ]
