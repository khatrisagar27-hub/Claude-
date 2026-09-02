"""Production analytics — yield, rejection rate, and unit cost, all derived
from work orders, their BOM, and the stock ledger. Machine-hour cost is not
modeled in v1 (no machine hourly-rate field yet); cost per unit here is
material cost only and is labelled as such rather than presented as a full
cost — see README non-goals."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.production import WorkOrder
from app.models.stock import BOMItem, Product, StockMovement


@dataclass
class ProductionSummary:
    plant_id: str
    period_start: datetime
    period_end: datetime
    total_planned_qty: float
    total_produced_qty: float
    total_rejected_qty: float
    good_qty: float
    rejection_rate: float  # rejected / produced
    schedule_adherence: float  # completed on/before planned_end / total completed


def production_summary(
    db: Session, plant_id: str, period_start: datetime, period_end: datetime
) -> ProductionSummary:
    work_orders = db.scalars(
        select(WorkOrder).where(
            WorkOrder.plant_id == plant_id,
            WorkOrder.planned_start >= period_start,
            WorkOrder.planned_start <= period_end,
        )
    ).all()

    planned = float(sum(wo.planned_qty or 0 for wo in work_orders))
    produced = float(sum(wo.produced_qty or 0 for wo in work_orders))
    rejected = float(sum(wo.rejected_qty or 0 for wo in work_orders))
    good = max(0.0, produced - rejected)
    rejection_rate = round(rejected / produced, 4) if produced > 0 else 0.0

    completed = [wo for wo in work_orders if wo.status == "completed" and wo.actual_end]
    on_time = [
        wo for wo in completed if wo.planned_end and wo.actual_end and wo.actual_end <= wo.planned_end
    ]
    adherence = round(len(on_time) / len(completed), 4) if completed else 0.0

    return ProductionSummary(
        plant_id=plant_id,
        period_start=period_start,
        period_end=period_end,
        total_planned_qty=planned,
        total_produced_qty=produced,
        total_rejected_qty=rejected,
        good_qty=good,
        rejection_rate=rejection_rate,
        schedule_adherence=adherence,
    )


def material_yield(db: Session, work_order_id: str) -> float | None:
    """Material efficiency: good output actually produced, divided by the
    output the BOM's standard cost implies the material *actually issued*
    to this work order should have yielded.

        standard_output = value of material issued / BOM standard unit cost
        yield %         = good output / standard_output

    100% means the work order converted issued material into good output
    exactly at the BOM standard; below 100% means more material went in
    than the BOM says a unit of good output should need (scrap, rework,
    over-issue). Returns None when there's no BOM or no material was
    recorded as issued against this work order — nothing to compare
    against."""
    wo = db.get(WorkOrder, work_order_id)
    if wo is None:
        return None
    bom_lines = db.scalars(select(BOMItem).where(BOMItem.parent_product_id == wo.product_id)).all()
    if not bom_lines:
        return None

    standard_unit_cost = 0.0
    for line in bom_lines:
        component = db.get(Product, line.component_product_id)
        if component is None:
            continue
        standard_unit_cost += float(line.qty_per_unit) * float(component.standard_cost or 0)
    if standard_unit_cost <= 0:
        return None

    issues = db.scalars(
        select(StockMovement).where(
            StockMovement.work_order_id == work_order_id,
            StockMovement.movement_type == "issue",
        )
    ).all()
    if not issues:
        return None
    actual_material_value = sum(float(m.quantity or 0) * float(m.unit_cost or 0) for m in issues)
    if actual_material_value <= 0:
        return None

    standard_output = actual_material_value / standard_unit_cost
    good_qty = max(0.0, float(wo.produced_qty or 0) - float(wo.rejected_qty or 0))
    return round(good_qty / standard_output, 4) if standard_output > 0 else None


def material_cost_per_unit(db: Session, work_order_id: str) -> float | None:
    """Material cost per good unit produced, from the BOM at standard cost.
    Excludes machine/labour overhead — see module docstring."""
    wo = db.get(WorkOrder, work_order_id)
    if wo is None:
        return None
    bom_lines = db.scalars(select(BOMItem).where(BOMItem.parent_product_id == wo.product_id)).all()
    if not bom_lines:
        return None
    good_qty = max(0.0, float(wo.produced_qty or 0) - float(wo.rejected_qty or 0))
    if good_qty <= 0:
        return None
    unit_material_cost = 0.0
    for line in bom_lines:
        component = db.get(Product, line.component_product_id)
        if component is None:
            continue
        unit_material_cost += float(line.qty_per_unit) * float(component.standard_cost or 0)
    total_material_cost = unit_material_cost * float(wo.produced_qty or 0)
    return round(total_material_cost / good_qty, 4)
