"""Stock analytics — everything derived from the stock_movements ledger.
On-hand quantity is never read off a stored field; it is always
SUM(inward) - SUM(outward) computed here, per app/models/stock.py's ledger
discipline."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock import INWARD_TYPES, Product, StockMovement
from app.utils.time import utcnow


def _signed_qty(movement: StockMovement) -> float:
    qty = float(movement.quantity or 0)
    return qty if movement.movement_type in INWARD_TYPES else -qty


def on_hand_qty(db: Session, product_id: str, as_of: datetime | None = None) -> float:
    query = select(StockMovement).where(StockMovement.product_id == product_id)
    if as_of is not None:
        query = query.where(StockMovement.movement_date <= as_of)
    return round(sum(_signed_qty(m) for m in db.scalars(query).all()), 3)


def last_movement_date(db: Session, product_id: str) -> datetime | None:
    latest = db.scalars(
        select(StockMovement.movement_date)
        .where(StockMovement.product_id == product_id)
        .order_by(StockMovement.movement_date.desc())
        .limit(1)
    ).first()
    return latest


@dataclass
class StockAgeing:
    product_id: str
    sku: str
    name: str
    on_hand: float
    days_since_last_movement: int | None
    bucket: str  # "0-30" / "31-60" / "61-90" / "90+" / "never moved"


def _age_bucket(days: int | None) -> str:
    if days is None:
        return "never moved"
    if days <= 30:
        return "0-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"


def stock_ageing(db: Session, plant_id: str, as_of: datetime | None = None) -> list[StockAgeing]:
    as_of = as_of or utcnow()
    products = db.scalars(select(Product).where(Product.plant_id == plant_id)).all()
    results = []
    for p in products:
        qty = on_hand_qty(db, p.id, as_of)
        last = last_movement_date(db, p.id)
        days = (as_of - last).days if last else None
        results.append(
            StockAgeing(
                product_id=p.id,
                sku=p.sku,
                name=p.name,
                on_hand=qty,
                days_since_last_movement=days,
                bucket=_age_bucket(days),
            )
        )
    return results


@dataclass
class ReorderAlert:
    product_id: str
    sku: str
    name: str
    on_hand: float
    reorder_level: float
    reorder_qty: float
    shortfall: float


def reorder_alerts(db: Session, plant_id: str) -> list[ReorderAlert]:
    products = db.scalars(select(Product).where(Product.plant_id == plant_id)).all()
    alerts = []
    for p in products:
        qty = on_hand_qty(db, p.id)
        level = float(p.reorder_level or 0)
        if qty < level:
            alerts.append(
                ReorderAlert(
                    product_id=p.id,
                    sku=p.sku,
                    name=p.name,
                    on_hand=qty,
                    reorder_level=level,
                    reorder_qty=float(p.reorder_qty or 0),
                    shortfall=round(level - qty, 3),
                )
            )
    alerts.sort(key=lambda a: a.shortfall, reverse=True)
    return alerts


def stock_valuation(db: Session, plant_id: str) -> dict[str, float]:
    """Standard-cost valuation of on-hand stock, grouped by product category.
    Not FIFO/weighted-average — see README non-goals."""
    products = db.scalars(select(Product).where(Product.plant_id == plant_id)).all()
    by_category: dict[str, float] = {}
    for p in products:
        qty = on_hand_qty(db, p.id)
        value = qty * float(p.standard_cost or 0)
        by_category[p.category] = round(by_category.get(p.category, 0.0) + value, 2)
    return by_category


def stock_turnover(
    db: Session, plant_id: str, period_start: datetime, period_end: datetime
) -> float:
    """Value of stock consumed (issue + production_in... outward movements) in
    the period, divided by the average on-hand value across the period
    endpoints. A low ratio flags working-capital tied up in slow-moving
    stock."""
    products = db.scalars(select(Product).where(Product.plant_id == plant_id)).all()
    consumed_value = 0.0
    opening_value = 0.0
    closing_value = 0.0
    for p in products:
        cost = float(p.standard_cost or 0)
        movements = db.scalars(
            select(StockMovement).where(
                StockMovement.product_id == p.id,
                StockMovement.movement_date >= period_start,
                StockMovement.movement_date <= period_end,
            )
        ).all()
        for m in movements:
            if m.movement_type not in INWARD_TYPES:
                consumed_value += float(m.quantity or 0) * cost
        opening_value += on_hand_qty(db, p.id, period_start) * cost
        closing_value += on_hand_qty(db, p.id, period_end) * cost

    avg_value = (opening_value + closing_value) / 2
    if avg_value <= 0:
        return 0.0
    return round(consumed_value / avg_value, 3)
