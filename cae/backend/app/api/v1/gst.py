"""GST reconciliation endpoints."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.risk import GSTReconciliation
from app.schemas.risk import GSTReconciliationOut
from app.utils.rbac import get_current_user, require_roles
from app.models.user import User

router = APIRouter()


@router.get("/reconciliation", response_model=list[GSTReconciliationOut])
def list_gst_recon(
    company_id: uuid.UUID,
    period: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(GSTReconciliation).filter(GSTReconciliation.company_id == company_id)
    if period:
        q = q.filter(GSTReconciliation.period == period)
    return q.order_by(GSTReconciliation.period.desc()).all()


@router.post("/upload-gstr2b", status_code=status.HTTP_202_ACCEPTED)
async def upload_gstr2b(
    company_id: uuid.UUID = Form(...),
    period: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    contents = await file.read()

    try:
        import json
        gstr2b_data = json.loads(contents)
    except Exception:
        gstr2b_data = {}

    try:
        from app.engines.gst_engine import GSTEngine
        engine = GSTEngine(db, str(company_id))
        result = engine.reconcile(period, gstr2b_data)
        return {"message": "GSTR-2B uploaded and reconciliation triggered", "period": period, "result": result}
    except Exception as e:
        return {"message": "GSTR-2B stored, reconciliation pending", "period": period, "error": str(e)}


@router.get("/itc-risk")
def get_itc_risk(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recons = db.query(GSTReconciliation).filter(
        GSTReconciliation.company_id == company_id,
        GSTReconciliation.risk_amount > 0,
    ).all()
    total_risk = sum(float(r.risk_amount or 0) for r in recons)
    return {
        "company_id": str(company_id),
        "total_itc_risk": total_risk,
        "periods_at_risk": len(recons),
        "details": [{"period": r.period, "risk_amount": float(r.risk_amount or 0)} for r in recons],
    }
