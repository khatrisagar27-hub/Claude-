from datetime import datetime, timedelta

from app.analytics.production import material_cost_per_unit, material_yield, production_summary
from tests.factories import (
    make_bom_item,
    make_movement,
    make_plant,
    make_product,
    make_warehouse,
    make_work_order,
)


def test_material_yield_at_standard_consumption_is_100_percent(db_session):
    plant = make_plant(db_session)
    wh = make_warehouse(db_session, plant.id)
    component = make_product(db_session, plant.id, sku="COMP", standard_cost=2)
    finished = make_product(db_session, plant.id, sku="FIN", standard_cost=20)
    make_bom_item(db_session, finished.id, component.id, qty_per_unit=2)  # 2 units component -> 1 finished

    wo = make_work_order(
        db_session,
        plant.id,
        product_id=finished.id,
        machine_id="m1",
        planned_qty=50,
        produced_qty=50,
        rejected_qty=0,
    )
    # Standard: 50 finished units need 100 component units at cost 2 = 200 value.
    # Issue exactly that -> standard_output = 200 / (2*2=4 standard unit cost) = 50 -> yield 50/50=100%
    make_movement(
        db_session,
        component.id,
        wh.id,
        movement_type="issue",
        quantity=100,
        unit_cost=2,
        work_order_id=wo.id,
        movement_date=datetime.utcnow(),
    )

    result = material_yield(db_session, wo.id)
    assert result == 1.0


def test_material_yield_below_100_when_more_material_issued_than_standard(db_session):
    plant = make_plant(db_session)
    wh = make_warehouse(db_session, plant.id)
    component = make_product(db_session, plant.id, sku="COMP", standard_cost=2)
    finished = make_product(db_session, plant.id, sku="FIN", standard_cost=20)
    make_bom_item(db_session, finished.id, component.id, qty_per_unit=2)

    wo = make_work_order(
        db_session,
        plant.id,
        product_id=finished.id,
        machine_id="m1",
        planned_qty=50,
        produced_qty=50,
        rejected_qty=0,
    )
    # Issue 150 units (more than the 100 standard) -> yield should drop below 1.0
    make_movement(
        db_session,
        component.id,
        wh.id,
        movement_type="issue",
        quantity=150,
        unit_cost=2,
        work_order_id=wo.id,
        movement_date=datetime.utcnow(),
    )

    result = material_yield(db_session, wo.id)
    assert result < 1.0


def test_material_yield_none_without_bom(db_session):
    plant = make_plant(db_session)
    product = make_product(db_session, plant.id)
    wo = make_work_order(db_session, plant.id, product_id=product.id, machine_id="m1")
    assert material_yield(db_session, wo.id) is None


def test_material_cost_per_unit(db_session):
    plant = make_plant(db_session)
    component = make_product(db_session, plant.id, sku="COMP", standard_cost=3)
    finished = make_product(db_session, plant.id, sku="FIN")
    make_bom_item(db_session, finished.id, component.id, qty_per_unit=4)  # 4 * 3 = 12/unit

    wo = make_work_order(
        db_session,
        plant.id,
        product_id=finished.id,
        machine_id="m1",
        produced_qty=10,
        rejected_qty=2,
    )
    # total material cost = 12 * 10 = 120, good qty = 8 -> 15/unit
    result = material_cost_per_unit(db_session, wo.id)
    assert result == 15.0


def test_production_summary_aggregates_and_computes_rejection_rate(db_session):
    plant = make_plant(db_session)
    product = make_product(db_session, plant.id)
    period_start = datetime(2026, 1, 1)
    make_work_order(
        db_session,
        plant.id,
        product_id=product.id,
        machine_id="m1",
        planned_qty=100,
        produced_qty=90,
        rejected_qty=9,
        planned_start=period_start + timedelta(days=1),
        planned_end=period_start + timedelta(days=1, hours=2),
        actual_end=period_start + timedelta(days=1, hours=1),
        status="completed",
    )

    summary = production_summary(
        db_session, plant.id, period_start, period_start + timedelta(days=30)
    )

    assert summary.total_produced_qty == 90
    assert summary.rejection_rate == round(9 / 90, 4)
    assert summary.good_qty == 81
    assert summary.schedule_adherence == 1.0  # finished before planned_end
