"""Risk analytics endpoints."""
import uuid
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.risk import RiskScore, FraudIndicator
from app.schemas.risk import RiskScoreOut, HeatmapOut, HeatmapCell, FraudIndicatorOut
from app.utils.rbac import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/scores", response_model=list[RiskScoreOut])
def get_risk_scores(
    company_id: uuid.UUID,
    score_date: Optional[date] = None,
    entity_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if score_date is None:
        score_date = date.today()
    q = db.query(RiskScore).filter(
        RiskScore.company_id == company_id,
        RiskScore.score_date == score_date,
    )
    if entity_level:
        q = q.filter(RiskScore.entity_level == entity_level)
    return q.all()


@router.get("/heatmap", response_model=HeatmapOut)
def get_heatmap(
    company_id: uuid.UUID,
    score_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if score_date is None:
        score_date = date.today()

    scores = db.query(RiskScore).filter(
        RiskScore.company_id == company_id,
        RiskScore.score_date == score_date,
    ).all()

    from app.models.audit import AuditException
    cells = []
    for s in scores:
        exc_count = db.query(AuditException).filter(
            AuditException.company_id == company_id,
            AuditException.category == s.entity_name,
        ).count()
        cells.append(HeatmapCell(
            process=s.entity_level,
            entity=s.entity_name,
            score=float(s.composite_score),
            band=s.risk_band,
            exception_count=exc_count,
        ))

    return HeatmapOut(company_id=company_id, score_date=score_date, cells=cells)


@router.get("/trend")
def get_risk_trend(
    company_id: uuid.UUID,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_date = date.today() - timedelta(days=days)
    scores = (
        db.query(RiskScore)
        .filter(RiskScore.company_id == company_id, RiskScore.score_date >= from_date)
        .order_by(RiskScore.score_date)
        .all()
    )
    by_date: dict = {}
    for s in scores:
        key = s.score_date.isoformat()
        if key not in by_date:
            by_date[key] = []
        by_date[key].append(s.composite_score)

    trend = [{"date": k, "avg_score": sum(v) / len(v)} for k, v in sorted(by_date.items())]
    return trend


@router.get("/fraud-indicators", response_model=list[FraudIndicatorOut])
def get_fraud_indicators(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(FraudIndicator)
        .filter(FraudIndicator.company_id == company_id)
        .order_by(FraudIndicator.analysis_date.desc())
        .limit(100)
        .all()
    )
