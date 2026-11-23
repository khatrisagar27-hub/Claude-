"""Working capital intelligence endpoints — DSO/DPO/DIO/CCC, aging, stress."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.rbac import get_current_user, require_roles
from app.models.user import User
from app.utils.engagement import get_engagement

router = APIRouter()


@router.get("/metrics")
def get_working_capital(
    company_id: uuid.UUID,
    engagement_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Live working capital metrics, aging, top overdue AR and Schedule III ageing / ratios.
    With an engagement: measured as at its period end, over its period."""
    from app.engines.wc_engine import WorkingCapitalEngine
    engine = WorkingCapitalEngine(db, str(company_id), get_engagement(db, engagement_id, company_id))
    return engine.compute_full()


@router.post("/recompute")
def recompute_working_capital(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    """Recompute and persist today's working capital snapshot."""
    from app.engines.wc_engine import WorkingCapitalEngine
    engine = WorkingCapitalEngine(db, str(company_id))
    metrics = engine.compute_and_store()
    return {"message": "Working capital metrics recomputed and stored", "metrics": metrics}
