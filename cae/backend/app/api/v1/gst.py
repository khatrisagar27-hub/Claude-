"""GST reconciliation endpoints."""
import json
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


@router.get("/reconciliation/{period}/details")
def get_gst_recon_details(
    period: str,
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invoice-level buckets (mismatch / missing_in_2b / missing_in_books / review_probable)."""
    recon = db.query(GSTReconciliation).filter(
        GSTReconciliation.company_id == company_id, GSTReconciliation.period == period
    ).first()
    if not recon:
        raise HTTPException(status_code=404, detail=f"No reconciliation for {period}")
    return {"period": period, "risk_amount": float(recon.risk_amount or 0), "details": recon.details_json or {}}


@router.post("/upload-gstr2b", status_code=status.HTTP_202_ACCEPTED)
async def upload_gstr2b(
    company_id: uuid.UUID = Form(...),
    period: str = Form(..., pattern=r"^\d{4}-\d{2}$"),
    file: UploadFile = File(...),
    tolerance: float = Form(1.0),
    gstr1_turnover: Optional[float] = Form(None),
    gstr1_tax: Optional[float] = Form(None),
    itc_claimed: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    """Accepts the portal GSTR-2B Excel/CSV (invoice-level match) or JSON — either
    {"itc_available": ...} for a summary recon or {"invoices": [...]} for invoice level."""
    from app.engines import gst_match
    from app.engines.gst_engine import GSTEngine

    contents = await file.read()
    name = (file.filename or "").lower()
    summary: dict = {}
    rows = None
    stats = None
    if name.endswith((".xlsx", ".xlsm", ".csv")):
        try:
            rows, stats = gst_match.parse_2b_file(contents, name)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Could not read the GSTR-2B file: {e}")
        if not rows:
            raise HTTPException(status_code=422, detail=f"No invoice rows with a valid supplier GSTIN found ({stats}).")
    else:
        try:
            summary = json.loads(contents)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=422, detail=f"Upload is neither GSTR-2B Excel/CSV nor JSON: {e}")
    for key, value in (("gstr1_turnover", gstr1_turnover), ("gstr1_tax", gstr1_tax), ("itc_claimed", itc_claimed)):
        if value is not None:
            summary[key] = value

    result = GSTEngine(db, str(company_id)).reconcile(period, summary, rows, tolerance)
    return {"message": "GSTR-2B reconciled", "period": period, "parse_stats": stats, "result": result}


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
        "details": [{"period": r.period, "risk_amount": float(r.risk_amount or 0), "risk_category": r.risk_category}
                    for r in recons],
    }
