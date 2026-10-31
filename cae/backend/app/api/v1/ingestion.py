"""Data ingestion endpoints — file upload and ERP sync trigger."""
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
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
    engagement_id: Optional[str] = None
    run_mode: Optional[str] = None
    result: Optional[dict] = None
    completed_at: Optional[str] = None

    model_config = {"from_attributes": True}


def job_out(j: SyncJob, run_mode: Optional[str] = None) -> "SyncJobOut":
    return SyncJobOut(
        id=str(j.id), company_id=str(j.company_id), job_type=j.job_type, status=j.status,
        records_processed=j.records_processed or 0, exceptions_raised=j.exceptions_raised or 0,
        error_message=j.error_message, created_at=j.created_at.isoformat(),
        engagement_id=str(j.engagement_id) if j.engagement_id else None, run_mode=run_mode,
        result=j.result_json, completed_at=j.completed_at.isoformat() if j.completed_at else None,
    )


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
    parse_errors: Optional[list] = None
    run_mode: Optional[str] = None

    model_config = {"from_attributes": True}


def upload_out(u: UploadedFile, run_mode: Optional[str] = None) -> UploadedFileOut:
    return UploadedFileOut(
        id=str(u.id), company_id=str(u.company_id), filename=u.filename, file_type=u.file_type,
        file_size=u.file_size, rows_parsed=u.rows_parsed, rows_imported=u.rows_imported, status=u.status,
        created_at=u.created_at.isoformat(), parse_errors=u.parse_errors, run_mode=run_mode,
    )


@router.post("/analyze")
async def analyze_file(
    company_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    """Detect data type and column mapping from any uploaded file — no DB writes."""
    import tempfile, os

    ext = os.path.splitext(file.filename or "upload")[1] or ".xlsx"
    contents = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        from app.connectors.excel_importer import ExcelImporter
        result = ExcelImporter.detect_schema(tmp_path)
    finally:
        os.unlink(tmp_path)

    return result


@router.post("/upload", response_model=UploadedFileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    background: BackgroundTasks,
    company_id: uuid.UUID = Form(...),
    file_type: str = Form(...),
    file: UploadFile = File(...),
    detected_type: Optional[str] = Form(None),
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

    from app.workers.dispatch import enqueue
    from app.workers.tasks import process_uploaded_file, execute_file_import
    mode = enqueue(process_uploaded_file, execute_file_import, str(file_id), detected_type, background=background)
    return upload_out(uploaded, mode)


@router.get("/uploads", response_model=list[UploadedFileOut])
def list_uploads(
    company_id: uuid.UUID,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (db.query(UploadedFile).filter(UploadedFile.company_id == company_id)
            .order_by(UploadedFile.created_at.desc()).limit(limit).all())
    return [upload_out(u) for u in rows]


@router.post("/sync", response_model=SyncJobOut, status_code=status.HTTP_201_CREATED)
def trigger_sync(
    company_id: uuid.UUID,
    background: BackgroundTasks,
    job_type: str = "full_audit",
    engagement_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager")),
):
    job = SyncJob(
        id=uuid.uuid4(),
        company_id=company_id,
        job_type=job_type,
        status="queued",
        triggered_by=current_user.full_name or str(current_user.id),
        engagement_id=engagement_id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    from app.workers.dispatch import enqueue
    from app.workers.tasks import run_audit_cycle, execute_audit_cycle
    eid = str(engagement_id) if engagement_id else None
    mode = enqueue(run_audit_cycle, execute_audit_cycle, str(company_id), str(job.id), eid, background=background)
    return job_out(job, mode)


@router.get("/jobs/{job_id}", response_model=SyncJobOut)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_out(job)


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
    return [job_out(j) for j in jobs]
