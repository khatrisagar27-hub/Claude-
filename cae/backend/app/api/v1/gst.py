"""GST reconciliation endpoints."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
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

    import json
    from app.engines.gst_engine import GSTEngine, parse_gstr2b
    try:
        gstr2b_data = json.loads(contents)
        parse_gstr2b(gstr2b_data)
    except ValueError as e:  # JSONDecodeError is a ValueError
        raise HTTPException(status_code=400, detail=f"Could not read GSTR-2B file: {e}")

    result = GSTEngine(db, str(company_id)).reconcile(period, gstr2b_data)
    return {"message": "GSTR-2B uploaded and reconciliation completed", "period": period, "result": result}


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
