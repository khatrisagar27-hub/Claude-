"""Uploading client data and seeing what has been loaded."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.engagements import get_engagement, open_engagement
from app.config import settings
from app.db import get_db
from app.ingest.loader import import_file, template_xlsx
from app.ingest.schema import DATASETS
from app.models import Engagement, ImportBatch, User
from app.security import current_user

router = APIRouter(tags=["data"])
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
ALLOWED = (".xlsx", ".xlsm", ".xls", ".csv", ".xml")


def batch_out(b: ImportBatch) -> dict:
    return {"id": b.id, "dataset": b.dataset, "filename": b.filename, "mode": b.mode, "rows_read": b.rows_read,
            "rows_loaded": b.rows_loaded, "rows_rejected": b.rows_rejected, "errors": b.errors,
            "unmapped_columns": b.unmapped_columns, "notes": b.notes, "uploaded_by": b.uploaded_by, "created_at": b.created_at}


@router.get("/datasets")
def datasets(_: User = Depends(current_user)):
    return [{"key": d.key, "label": d.label, "help": d.help,
             "columns": [{"name": c.name, "kind": c.kind, "required": c.required,
                          "help": c.help or " / ".join(sorted(set(c.choices.values())))} for c in d.cols]}
            for d in DATASETS.values()]


@router.get("/datasets/{dataset}/template")
def template(dataset: str, _: User = Depends(current_user)):
    if dataset not in DATASETS:
        raise HTTPException(404, "Unknown dataset")
    return Response(template_xlsx(dataset), media_type=XLSX,
                    headers={"Content-Disposition": f'attachment; filename="{dataset}_template.xlsx"'})


@router.get("/engagements/{engagement_id}/data")
def loaded(eng: Engagement = Depends(get_engagement), db: Session = Depends(get_db)):
    """Row counts per dataset and the import history."""
    counts = {key: db.scalar(select(func.count()).select_from(ds.model).where(ds.model.engagement_id == eng.id))
              for key, ds in DATASETS.items()}
    batches = db.scalars(select(ImportBatch).where(ImportBatch.engagement_id == eng.id).order_by(ImportBatch.id.desc()).limit(50))
    return {"counts": counts, "batches": [batch_out(b) for b in batches]}


@router.post("/engagements/{engagement_id}/data/{dataset}")
async def upload(dataset: str, file: UploadFile = File(...), mode: str = Form("replace"),
                 eng: Engagement = Depends(open_engagement), db: Session = Depends(get_db), user: User = Depends(current_user)):
    if dataset not in DATASETS:
        raise HTTPException(404, "Unknown dataset")
    if mode not in ("replace", "append"):
        raise HTTPException(422, "mode must be replace or append")
    name = (file.filename or "upload").replace("\\", "/").split("/")[-1]
    if not name.lower().endswith(ALLOWED):
        raise HTTPException(422, f"File type not accepted. Use one of: {', '.join(ALLOWED)}")
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File is larger than {settings.max_upload_mb} MB")
    try:
        batch = import_file(db, eng, dataset, name, content, mode, user.name)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc))
    except Exception as exc:  # unreadable workbook, wrong extension, corrupt file
        db.rollback()
        raise HTTPException(422, f"Could not read the file: {type(exc).__name__}")
    return batch_out(batch)
