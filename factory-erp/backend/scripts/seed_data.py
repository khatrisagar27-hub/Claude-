"""Demo data for a plausible small-factory setup: one plant, two machines,
a raw-material -> finished-good BOM, some stock movements, and a couple of
work orders with downtime — enough for every analytics endpoint to return a
non-empty answer.

Run: python scripts/seed_data.py
"""

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base, SessionLocal, engine
from app.models.machine import Machine, MachineDowntime
from app.models.plant import Plant, Warehouse
from app.models.production import WorkOrder
from app.models.stock import BOMItem, Product, StockMovement
from app.models.user import User
from app.utils.security import hash_password
from app.utils.time import utcnow

# import every model so metadata is complete before create_all
from app import models  # noqa: F401


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Plant).first():
            print("Seed data already present — skipping.")
            return

        plant = Plant(code="PL-01", name="Ranchi Sheet Metal Works", location="Ranchi, JH")
        db.add(plant)
        db.flush()

        rm_store = Warehouse(plant_id=plant.id, code="WH-RM", name="Raw Material Store", category="raw_material")
        fg_store = Warehouse(plant_id=plant.id, code="WH-FG", name="Finished Goods Store", category="finished_good")
        db.add_all([rm_store, fg_store])

        admin = User(
            plant_id=plant.id,
            name="Plant Admin",
            email="admin@factory.local",
            hashed_password=hash_password("changeme123"),
            role="admin",
        )
        db.add(admin)

        steel_coil = Product(
            plant_id=plant.id, sku="RM-STEEL-COIL", name="Steel Coil 2mm", category="raw_material",
            uom="kg", standard_cost=65, reorder_level=500, reorder_qty=2000,
        )
        bracket = Product(
            plant_id=plant.id, sku="FG-BRACKET-A", name="Mounting Bracket A", category="finished_good",
            uom="pcs", standard_cost=180, reorder_level=200, reorder_qty=500,
        )
        db.add_all([steel_coil, bracket])
        db.flush()

        db.add(BOMItem(parent_product_id=bracket.id, component_product_id=steel_coil.id, qty_per_unit=1.8))

        press1 = Machine(
            plant_id=plant.id, code="PRESS-01", name="Hydraulic Press 1",
            category="press", rated_capacity_per_hour=120, status="idle",
        )
        press2 = Machine(
            plant_id=plant.id, code="PRESS-02", name="Hydraulic Press 2",
            category="press", rated_capacity_per_hour=100, status="idle",
        )
        db.add_all([press1, press2])
        db.flush()

        now = utcnow()

        db.add(
            StockMovement(
                product_id=steel_coil.id, warehouse_id=rm_store.id, movement_type="receipt",
                quantity=3000, unit_cost=65, reference="PO-1001", movement_date=now - timedelta(days=10),
            )
        )

        wo_start = now - timedelta(days=1, hours=4)
        wo_end = now - timedelta(days=1)
        wo1 = WorkOrder(
            plant_id=plant.id, order_number="WO-2026-0001", product_id=bracket.id, machine_id=press1.id,
            planned_qty=500, produced_qty=470, rejected_qty=12,
            planned_start=wo_start, planned_end=wo_start + timedelta(hours=4),
            actual_start=wo_start, actual_end=wo_end, status="completed",
        )
        db.add(wo1)
        db.flush()

        db.add(
            StockMovement(
                product_id=steel_coil.id, warehouse_id=rm_store.id, movement_type="issue",
                quantity=900, unit_cost=65, work_order_id=wo1.id, reference="WO-2026-0001",
                movement_date=wo_start,
            )
        )
        db.add(
            StockMovement(
                product_id=bracket.id, warehouse_id=fg_store.id, movement_type="production_in",
                quantity=470, unit_cost=180, work_order_id=wo1.id, reference="WO-2026-0001",
                movement_date=wo_end,
            )
        )

        db.add(
            MachineDowntime(
                machine_id=press1.id, work_order_id=wo1.id,
                start_time=wo_start + timedelta(hours=1),
                end_time=wo_start + timedelta(hours=1, minutes=25),
                reason_category="breakdown", remarks="Hydraulic seal leak",
            )
        )
        db.add(
            MachineDowntime(
                machine_id=press1.id, work_order_id=wo1.id,
                start_time=wo_start + timedelta(hours=2, minutes=30),
                end_time=wo_start + timedelta(hours=2, minutes=45),
                reason_category="changeover", remarks="Die change",
            )
        )

        db.commit()
        print(f"Seeded plant {plant.code}. Login: admin@factory.local / changeme123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
