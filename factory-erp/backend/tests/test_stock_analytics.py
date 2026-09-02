from datetime import datetime, timedelta

from app.analytics.stock import on_hand_qty, reorder_alerts, stock_ageing, stock_valuation
from tests.factories import make_movement, make_plant, make_product, make_warehouse


def test_on_hand_qty_nets_inward_and_outward(db_session):
    plant = make_plant(db_session)
    wh = make_warehouse(db_session, plant.id)
    product = make_product(db_session, plant.id)
    now = datetime.utcnow()

    make_movement(db_session, product.id, wh.id, movement_type="receipt", quantity=100, movement_date=now)
    make_movement(db_session, product.id, wh.id, movement_type="issue", quantity=30, movement_date=now)
    make_movement(
        db_session, product.id, wh.id, movement_type="production_out", quantity=20, movement_date=now
    )

    assert on_hand_qty(db_session, product.id) == 50


def test_reorder_alert_fires_below_level(db_session):
    plant = make_plant(db_session)
    wh = make_warehouse(db_session, plant.id)
    low = make_product(db_session, plant.id, sku="LOW", reorder_level=50)
    ok = make_product(db_session, plant.id, sku="OK", reorder_level=5)
    now = datetime.utcnow()
    make_movement(db_session, low.id, wh.id, movement_type="receipt", quantity=10, movement_date=now)
    make_movement(db_session, ok.id, wh.id, movement_type="receipt", quantity=10, movement_date=now)

    alerts = reorder_alerts(db_session, plant.id)

    skus = {a.sku for a in alerts}
    assert "LOW" in skus
    assert "OK" not in skus


def test_stock_ageing_buckets_by_days_since_last_movement(db_session):
    plant = make_plant(db_session)
    wh = make_warehouse(db_session, plant.id)
    product = make_product(db_session, plant.id)
    as_of = datetime(2026, 9, 1)
    make_movement(
        db_session,
        product.id,
        wh.id,
        movement_type="receipt",
        quantity=10,
        movement_date=as_of - timedelta(days=95),
    )

    ageing = stock_ageing(db_session, plant.id, as_of=as_of)

    assert ageing[0].bucket == "90+"
    assert ageing[0].days_since_last_movement == 95


def test_stock_ageing_never_moved_when_no_movements(db_session):
    plant = make_plant(db_session)
    make_product(db_session, plant.id)

    ageing = stock_ageing(db_session, plant.id)

    assert ageing[0].bucket == "never moved"
    assert ageing[0].on_hand == 0


def test_stock_valuation_uses_standard_cost_by_category(db_session):
    plant = make_plant(db_session)
    wh = make_warehouse(db_session, plant.id)
    raw = make_product(db_session, plant.id, sku="RAW", category="raw_material", standard_cost=5)
    fg = make_product(db_session, plant.id, sku="FG", category="finished_good", standard_cost=50)
    now = datetime.utcnow()
    make_movement(db_session, raw.id, wh.id, movement_type="receipt", quantity=100, movement_date=now)
    make_movement(db_session, fg.id, wh.id, movement_type="production_in", quantity=10, movement_date=now)

    valuation = stock_valuation(db_session, plant.id)

    assert valuation["raw_material"] == 500
    assert valuation["finished_good"] == 500
