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
from app.utils.engagement import exception_scope, get_engagement
from app.models.user import User

router = APIRouter()


_OPEN = ["open", "in_review", "management_query_sent", "remediation_in_progress"]


def _live_scores(db, company_id, engagement_id) -> list[RiskScoreOut]:
    """Scores computed now from one engagement's open exceptions (not stored)."""
    from app.engines.risk_engine import RiskEngine

    out = []
    for area, d in RiskEngine(db, str(company_id), str(engagement_id))._compute_scores().items():
        out.append(RiskScoreOut(id=uuid.uuid5(uuid.NAMESPACE_OID, f"{engagement_id}:{area}"), company_id=company_id,
                                score_date=date.today(), entity_level="process", entity_name=area,
                                likelihood=d["likelihood"], impact=d["impact"], materiality=d["materiality"],
                                frequency=d["frequency"], control_weakness=d["control_weakness"],
                                composite_score=d["composite_score"], risk_band=d["risk_band"]))
    return out


def _stored_scores(db, company_id, score_date):
    from sqlalchemy import func

    if score_date is None:   # latest scored day, not just today (a run yesterday left today empty)
        score_date = db.query(func.max(RiskScore.score_date)).filter(RiskScore.company_id == company_id).scalar()
    if score_date is None:
        return date.today(), []
    return score_date, db.query(RiskScore).filter(RiskScore.company_id == company_id,
                                                  RiskScore.score_date == score_date).all()


@router.get("/scores", response_model=list[RiskScoreOut])
def get_risk_scores(
    company_id: uuid.UUID,
    score_date: Optional[date] = None,
    entity_level: Optional[str] = None,
    engagement_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if engagement_id:
        get_engagement(db, engagement_id, company_id)
        return _live_scores(db, company_id, engagement_id)
    _, scores = _stored_scores(db, company_id, score_date)
    return [s for s in scores if not entity_level or s.entity_level == entity_level]


@router.get("/heatmap", response_model=HeatmapOut)
def get_heatmap(
    company_id: uuid.UUID,
    score_date: Optional[date] = None,
    engagement_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.audit import AuditException

    if engagement_id:
        get_engagement(db, engagement_id, company_id)
        score_date, scores = date.today(), _live_scores(db, company_id, engagement_id)
    else:
        score_date, scores = _stored_scores(db, company_id, score_date)
    cells = []
    for s in scores:
        exc_count = db.query(AuditException).filter(
            AuditException.company_id == company_id,
            AuditException.category == s.entity_name,
            AuditException.status.in_(_OPEN),
            exception_scope(engagement_id),
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
    from sqlalchemy import func

    last_run = db.query(func.max(FraudIndicator.analysis_date)).filter(FraudIndicator.company_id == company_id).scalar()
    if last_run is None:
        return []
    return (
        db.query(FraudIndicator)
        .filter(FraudIndicator.company_id == company_id, FraudIndicator.analysis_date == last_run)
        .order_by(FraudIndicator.score.desc())
        .all()
    )
