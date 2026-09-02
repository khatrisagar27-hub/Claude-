"""Overall Equipment Effectiveness.

OEE = Availability x Performance x Quality — the standard manufacturing
definition (see SEMI E10 / TPM literature). Every input here comes from the
work_orders and machine_downtimes ledger tables; nothing is estimated.

  Availability = Run time / Planned production time
  Performance  = Actual output rate / Ideal (rated) output rate
  Quality      = Good output / Total output

All three factors are clamped to [0, 1] before multiplying: a data-entry
error (e.g. downtime logged longer than the work order itself) should not
be allowed to produce a nonsensical OEE > 100% or a negative one — the
clamp makes bad input visible as a suspicious 100%/0% rather than a
number nobody would think to distrust.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.machine import Machine, MachineDowntime
from app.models.production import WorkOrder


@dataclass
class OEEResult:
    machine_id: str
    machine_name: str
    planned_minutes: float
    downtime_minutes: float
    run_minutes: float
    total_output: float
    good_output: float
    availability: float
    performance: float
    quality: float
    oee: float


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _wo_span_minutes(wo: WorkOrder) -> float:
    start = wo.actual_start or wo.planned_start
    end = wo.actual_end or wo.planned_end
    if not start or not end or end <= start:
        return 0.0
    return (end - start).total_seconds() / 60.0


def compute_oee(
    db: Session, machine_id: str, period_start: datetime, period_end: datetime
) -> OEEResult | None:
    machine = db.get(Machine, machine_id)
    if machine is None:
        return None

    work_orders = db.scalars(
        select(WorkOrder).where(
            WorkOrder.machine_id == machine_id,
            WorkOrder.status.in_(("in_progress", "completed")),
        )
    ).all()
    work_orders = [
        wo
        for wo in work_orders
        if (wo.actual_start or wo.planned_start)
        and period_start <= (wo.actual_start or wo.planned_start) <= period_end
    ]

    planned_minutes = sum(_wo_span_minutes(wo) for wo in work_orders)
    total_output = float(sum(wo.produced_qty or 0 for wo in work_orders))
    rejected = float(sum(wo.rejected_qty or 0 for wo in work_orders))
    good_output = max(0.0, total_output - rejected)

    downtimes = db.scalars(
        select(MachineDowntime).where(
            MachineDowntime.machine_id == machine_id,
            MachineDowntime.start_time >= period_start,
            MachineDowntime.start_time <= period_end,
        )
    ).all()
    downtime_minutes = 0.0
    for dt in downtimes:
        end = dt.end_time or period_end
        downtime_minutes += max(0.0, (end - dt.start_time).total_seconds() / 60.0)

    run_minutes = max(0.0, planned_minutes - downtime_minutes)

    availability = _clamp01(run_minutes / planned_minutes) if planned_minutes > 0 else 0.0

    rated_per_hour = float(machine.rated_capacity_per_hour or 0)
    if run_minutes > 0 and rated_per_hour > 0:
        ideal_output_for_run_time = (run_minutes / 60.0) * rated_per_hour
        performance = _clamp01(total_output / ideal_output_for_run_time) if ideal_output_for_run_time > 0 else 0.0
    else:
        performance = 0.0

    quality = _clamp01(good_output / total_output) if total_output > 0 else 0.0

    oee = availability * performance * quality

    return OEEResult(
        machine_id=machine.id,
        machine_name=machine.name,
        planned_minutes=round(planned_minutes, 2),
        downtime_minutes=round(downtime_minutes, 2),
        run_minutes=round(run_minutes, 2),
        total_output=total_output,
        good_output=good_output,
        availability=round(availability, 4),
        performance=round(performance, 4),
        quality=round(quality, 4),
        oee=round(oee, 4),
    )


def compute_oee_for_plant(
    db: Session, plant_id: str, period_start: datetime, period_end: datetime
) -> list[OEEResult]:
    machine_ids = db.scalars(select(Machine.id).where(Machine.plant_id == plant_id)).all()
    results = []
    for mid in machine_ids:
        r = compute_oee(db, mid, period_start, period_end)
        if r is not None:
            results.append(r)
    return results
