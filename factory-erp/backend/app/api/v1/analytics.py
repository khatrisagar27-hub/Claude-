from dataclasses import asdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics.downtime import downtime_pareto
from app.analytics.oee import compute_oee, compute_oee_for_plant
from app.analytics.production import production_summary
from app.analytics.stock import reorder_alerts, stock_ageing, stock_turnover, stock_valuation
from app.api.v1.deps import get_current_user
from app.database import get_db
from app.utils.time import utcnow

router = APIRouter(
    prefix="/analytics", tags=["analytics"], dependencies=[Depends(get_current_user)]
)


def _default_period(period_start: datetime | None, period_end: datetime | None) -> tuple[datetime, datetime]:
    end = period_end or utcnow()
    start = period_start or (end - timedelta(days=30))
    return start, end


@router.get("/oee/machine/{machine_id}")
def oee_machine(
    machine_id: str,
    period_start: datetime | None = Query(None),
    period_end: datetime | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    start, end = _default_period(period_start, period_end)
    result = compute_oee(db, machine_id, start, end)
    return asdict(result) if result else {}


@router.get("/oee/plant/{plant_id}")
def oee_plant(
    plant_id: str,
    period_start: datetime | None = Query(None),
    period_end: datetime | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict]:
    start, end = _default_period(period_start, period_end)
    return [asdict(r) for r in compute_oee_for_plant(db, plant_id, start, end)]


@router.get("/downtime-pareto")
def downtime_pareto_view(
    period_start: datetime | None = Query(None),
    period_end: datetime | None = Query(None),
    machine_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict]:
    start, end = _default_period(period_start, period_end)
    return [asdict(r) for r in downtime_pareto(db, start, end, machine_id)]


@router.get("/production-summary/{plant_id}")
def production_summary_view(
    plant_id: str,
    period_start: datetime | None = Query(None),
    period_end: datetime | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    start, end = _default_period(period_start, period_end)
    return asdict(production_summary(db, plant_id, start, end))


@router.get("/stock/ageing/{plant_id}")
def stock_ageing_view(plant_id: str, db: Session = Depends(get_db)) -> list[dict]:
    return [asdict(r) for r in stock_ageing(db, plant_id)]


@router.get("/stock/reorder-alerts/{plant_id}")
def reorder_alerts_view(plant_id: str, db: Session = Depends(get_db)) -> list[dict]:
    return [asdict(r) for r in reorder_alerts(db, plant_id)]


@router.get("/stock/valuation/{plant_id}")
def stock_valuation_view(plant_id: str, db: Session = Depends(get_db)) -> dict:
    return stock_valuation(db, plant_id)


@router.get("/stock/turnover/{plant_id}")
def stock_turnover_view(
    plant_id: str,
    period_start: datetime | None = Query(None),
    period_end: datetime | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    start, end = _default_period(period_start, period_end)
    return {"plant_id": plant_id, "turnover_ratio": stock_turnover(db, plant_id, start, end)}
