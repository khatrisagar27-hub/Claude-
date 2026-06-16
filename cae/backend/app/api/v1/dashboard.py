"""Executive dashboard endpoints."""
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import AuditException
from app.models.workflow import ManagementQuery
from app.models.risk import RiskScore, FraudIndicator, GSTReconciliation
from app.schemas.dashboard import KPIOut, TopExceptionOut, TrendPoint, DashboardOut
from app.utils.rbac import get_current_user
from app.models.user import User

router = APIRouter()

_OPEN_STATUSES = ["open", "in_review", "management_query_sent", "remediation_in_progress"]


@router.get("/kpis", response_model=KPIOut)
def get_kpis(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base = db.query(AuditException).filter(AuditException.company_id == company_id)
    total = base.count()
    critical = base.filter(AuditException.severity == "critical").count()
    high = base.filter(AuditException.severity == "high").count()
    medium = base.filter(AuditException.severity == "medium").count()
    low = base.filter(AuditException.severity == "low").count()

    queries = db.query(ManagementQuery).filter(ManagementQuery.company_id == company_id)
    open_queries = queries.filter(ManagementQuery.status.in_(["open", "pending"])).count()
    overdue_queries = queries.filter(
        ManagementQuery.status.in_(["open", "pending"]),
        ManagementQuery.due_date < date.today(),
    ).count()

    first_of_month = date.today().replace(day=1)
    resolved_this_month = base.filter(
        AuditException.status == "resolved",
        AuditException.detected_on >= first_of_month,
    ).count()

    latest_score = (
        db.query(RiskScore)
        .filter(RiskScore.company_id == company_id)
        .order_by(RiskScore.score_date.desc(), RiskScore.composite_score.desc())
        .first()
    )
    composite_score = float(latest_score.composite_score) if latest_score else 0.0
    risk_band = latest_score.risk_band if latest_score else "low"

    fraud_count = db.query(FraudIndicator).filter(FraudIndicator.company_id == company_id).count()
    gst_risk = db.query(func.sum(GSTReconciliation.risk_amount)).filter(
        GSTReconciliation.company_id == company_id
    ).scalar() or 0.0

    return KPIOut(
        total_exceptions=total, critical=critical, high=high, medium=medium, low=low,
        open_queries=open_queries, overdue_queries=overdue_queries,
        resolved_this_month=resolved_this_month,
        composite_risk_score=composite_score, risk_band=risk_band,
        fraud_indicators=fraud_count, gst_risk_amount=float(gst_risk),
    )


@router.get("/top-exceptions", response_model=list[TopExceptionOut])
def get_top_exceptions(
    company_id: uuid.UUID,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    excs = (
        db.query(AuditException)
        .filter(AuditException.company_id == company_id, AuditException.status.in_(_OPEN_STATUSES))
        .order_by(AuditException.financial_impact.desc().nullslast(), AuditException.detected_on.desc())
        .limit(limit)
        .all()
    )
    return [
        TopExceptionOut(
            id=str(e.id), title=e.title, severity=e.severity,
            financial_impact=float(e.financial_impact) if e.financial_impact else None,
            business_area=e.category,
            detected_at=e.detected_on.isoformat(),
            status=e.status,
        )
        for e in excs
    ]


@router.get("/trend", response_model=list[TrendPoint])
def get_exception_trend(
    company_id: uuid.UUID,
    months: int = 6,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_date = date.today() - timedelta(days=months * 30)
    excs = (
        db.query(AuditException)
        .filter(AuditException.company_id == company_id, AuditException.detected_on >= from_date)
        .all()
    )
    by_period: dict = {}
    for e in excs:
        period = e.detected_on.strftime("%Y-%m")
        if period not in by_period:
            by_period[period] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_period[period][e.severity] = by_period[period].get(e.severity, 0) + 1
    return [TrendPoint(period=k, **v) for k, v in sorted(by_period.items())]


@router.get("/fraud-indicators")
def dashboard_fraud_indicators(
    company_id: uuid.UUID,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return [
        {"id": str(i.id), "type": i.indicator_type, "description": i.description,
         "score": float(i.score), "analysis_date": i.analysis_date.isoformat()}
        for i in db.query(FraudIndicator).filter(FraudIndicator.company_id == company_id)
        .order_by(FraudIndicator.analysis_date.desc()).limit(limit).all()
    ]
