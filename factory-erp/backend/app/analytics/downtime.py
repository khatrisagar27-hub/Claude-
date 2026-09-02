"""Downtime Pareto — where machine time is actually being lost, ranked."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.machine import MachineDowntime


@dataclass
class DowntimeReasonTotal:
    reason_category: str
    total_minutes: float
    occurrences: int


def downtime_pareto(
    db: Session,
    period_start: datetime,
    period_end: datetime,
    machine_id: str | None = None,
) -> list[DowntimeReasonTotal]:
    query = select(MachineDowntime).where(
        MachineDowntime.start_time >= period_start,
        MachineDowntime.start_time <= period_end,
    )
    if machine_id:
        query = query.where(MachineDowntime.machine_id == machine_id)

    totals: dict[str, list[float]] = {}
    for dt in db.scalars(query).all():
        end = dt.end_time or period_end
        minutes = max(0.0, (end - dt.start_time).total_seconds() / 60.0)
        bucket = totals.setdefault(dt.reason_category, [0.0, 0])
        bucket[0] += minutes
        bucket[1] += 1

    results = [
        DowntimeReasonTotal(reason_category=reason, total_minutes=round(mins, 2), occurrences=int(count))
        for reason, (mins, count) in totals.items()
    ]
    results.sort(key=lambda r: r.total_minutes, reverse=True)
    return results
