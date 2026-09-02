"""Row builders for tests — construct-and-flush helpers so each test can set
up only the fields it cares about."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.machine import Machine, MachineDowntime
from app.models.plant import Plant, Warehouse
from app.models.production import WorkOrder
from app.models.stock import BOMItem, Product, StockMovement


def make_plant(db: Session, **kwargs) -> Plant:
    defaults = {"code": "P1", "name": "Test Plant"}
    defaults.update(kwargs)
    plant = Plant(**defaults)
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant


def make_warehouse(db: Session, plant_id: str, **kwargs) -> Warehouse:
    defaults = {"plant_id": plant_id, "code": "WH1", "name": "Main Store"}
    defaults.update(kwargs)
    wh = Warehouse(**defaults)
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return wh


def make_machine(db: Session, plant_id: str, **kwargs) -> Machine:
    defaults = {
        "plant_id": plant_id,
        "code": "M1",
        "name": "Test Machine",
        "rated_capacity_per_hour": 100,
    }
    defaults.update(kwargs)
    machine = Machine(**defaults)
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


def make_downtime(db: Session, machine_id: str, **kwargs) -> MachineDowntime:
    defaults = {
        "machine_id": machine_id,
        "start_time": datetime.utcnow(),
        "reason_category": "breakdown",
    }
    defaults.update(kwargs)
    dt = MachineDowntime(**defaults)
    db.add(dt)
    db.commit()
    db.refresh(dt)
    return dt


def make_product(db: Session, plant_id: str, **kwargs) -> Product:
    defaults = {
        "plant_id": plant_id,
        "sku": "SKU1",
        "name": "Test Product",
        "category": "raw_material",
        "standard_cost": 10,
    }
    defaults.update(kwargs)
    product = Product(**defaults)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def make_bom_item(db: Session, parent_product_id: str, component_product_id: str, **kwargs) -> BOMItem:
    defaults = {
        "parent_product_id": parent_product_id,
        "component_product_id": component_product_id,
        "qty_per_unit": 1,
    }
    defaults.update(kwargs)
    item = BOMItem(**defaults)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def make_movement(db: Session, product_id: str, warehouse_id: str, **kwargs) -> StockMovement:
    defaults = {
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "movement_type": "receipt",
        "quantity": 10,
        "unit_cost": 10,
        "movement_date": datetime.utcnow(),
    }
    defaults.update(kwargs)
    movement = StockMovement(**defaults)
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


def make_work_order(db: Session, plant_id: str, product_id: str, machine_id: str, **kwargs) -> WorkOrder:
    defaults = {
        "plant_id": plant_id,
        "order_number": f"WO-{datetime.utcnow().timestamp()}",
        "product_id": product_id,
        "machine_id": machine_id,
        "planned_qty": 100,
        "produced_qty": 0,
        "rejected_qty": 0,
        "status": "planned",
    }
    defaults.update(kwargs)
    wo = WorkOrder(**defaults)
    db.add(wo)
    db.commit()
    db.refresh(wo)
    return wo
