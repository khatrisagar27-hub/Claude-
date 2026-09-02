from datetime import datetime, timedelta

from app.analytics.oee import compute_oee
from tests.factories import make_downtime, make_machine, make_plant, make_work_order


def test_oee_perfect_run_no_downtime(db_session):
    plant = make_plant(db_session)
    machine = make_machine(db_session, plant.id, rated_capacity_per_hour=100)
    start = datetime(2026, 1, 1, 8, 0)
    end = start + timedelta(hours=1)
    make_work_order(
        db_session,
        plant.id,
        product_id="prod-1",
        machine_id=machine.id,
        planned_qty=100,
        produced_qty=100,
        rejected_qty=0,
        actual_start=start,
        actual_end=end,
        status="completed",
    )

    result = compute_oee(
        db_session, machine.id, start - timedelta(hours=1), end + timedelta(hours=1)
    )

    assert result is not None
    assert result.availability == 1.0
    assert result.performance == 1.0
    assert result.quality == 1.0
    assert result.oee == 1.0


def test_oee_reflects_downtime_and_rejection(db_session):
    plant = make_plant(db_session)
    machine = make_machine(db_session, plant.id, rated_capacity_per_hour=100)
    start = datetime(2026, 1, 1, 8, 0)
    end = start + timedelta(hours=2)  # 120 planned minutes
    make_work_order(
        db_session,
        plant.id,
        product_id="prod-1",
        machine_id=machine.id,
        planned_qty=200,
        produced_qty=90,  # under the ideal 100/hr * (run time) rate
        rejected_qty=10,
        actual_start=start,
        actual_end=end,
        status="completed",
    )
    # 30 minutes of breakdown inside the work order window
    make_downtime(
        db_session,
        machine.id,
        start_time=start + timedelta(minutes=30),
        end_time=start + timedelta(minutes=60),
        reason_category="breakdown",
    )

    result = compute_oee(db_session, machine.id, start - timedelta(hours=1), end + timedelta(hours=1))

    assert result.planned_minutes == 120
    assert result.downtime_minutes == 30
    assert result.run_minutes == 90
    # quality = good/total = 80/90
    assert result.quality == round(80 / 90, 4)
    # OEE must never exceed the least of its three factors
    assert result.oee <= result.availability
    assert result.oee <= result.performance
    assert result.oee <= result.quality
    assert 0 < result.oee < 1


def test_oee_unknown_machine_returns_none(db_session):
    now = datetime.utcnow()
    assert compute_oee(db_session, "does-not-exist", now - timedelta(days=1), now) is None


def test_oee_clamps_overlogged_downtime_to_zero_availability(db_session):
    """A downtime entry logged longer than the work order itself (bad data
    entry) must not push availability negative."""
    plant = make_plant(db_session)
    machine = make_machine(db_session, plant.id, rated_capacity_per_hour=100)
    start = datetime(2026, 1, 1, 8, 0)
    end = start + timedelta(hours=1)
    make_work_order(
        db_session,
        plant.id,
        product_id="prod-1",
        machine_id=machine.id,
        produced_qty=10,
        actual_start=start,
        actual_end=end,
        status="completed",
    )
    make_downtime(
        db_session,
        machine.id,
        start_time=start,
        end_time=end + timedelta(hours=5),
        reason_category="breakdown",
    )

    result = compute_oee(db_session, machine.id, start - timedelta(hours=1), end + timedelta(hours=6))
    assert result.availability == 0.0
    assert result.oee == 0.0
