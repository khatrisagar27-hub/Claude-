from datetime import datetime, timedelta

from app.analytics.downtime import downtime_pareto
from tests.factories import make_downtime, make_machine, make_plant


def test_downtime_pareto_ranks_by_total_minutes(db_session):
    plant = make_plant(db_session)
    machine = make_machine(db_session, plant.id)
    start = datetime(2026, 1, 1)

    make_downtime(
        db_session,
        machine.id,
        start_time=start,
        end_time=start + timedelta(minutes=10),
        reason_category="changeover",
    )
    make_downtime(
        db_session,
        machine.id,
        start_time=start + timedelta(hours=1),
        end_time=start + timedelta(hours=1, minutes=90),
        reason_category="breakdown",
    )
    make_downtime(
        db_session,
        machine.id,
        start_time=start + timedelta(hours=3),
        end_time=start + timedelta(hours=3, minutes=5),
        reason_category="changeover",
    )

    results = downtime_pareto(db_session, start - timedelta(hours=1), start + timedelta(hours=5))

    assert results[0].reason_category == "breakdown"
    assert results[0].total_minutes == 90
    changeover = next(r for r in results if r.reason_category == "changeover")
    assert changeover.total_minutes == 15
    assert changeover.occurrences == 2


def test_downtime_pareto_filters_by_machine(db_session):
    plant = make_plant(db_session)
    m1 = make_machine(db_session, plant.id, code="M1")
    m2 = make_machine(db_session, plant.id, code="M2")
    start = datetime(2026, 1, 1)
    make_downtime(db_session, m1.id, start_time=start, end_time=start + timedelta(minutes=10))
    make_downtime(db_session, m2.id, start_time=start, end_time=start + timedelta(minutes=20))

    results = downtime_pareto(
        db_session, start - timedelta(hours=1), start + timedelta(hours=1), machine_id=m1.id
    )
    assert len(results) == 1
    assert results[0].total_minutes == 10
