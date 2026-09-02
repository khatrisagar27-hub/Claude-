from datetime import datetime

from app.schemas.common import ORMModel


class ProductCreate(ORMModel):
    plant_id: str
    sku: str
    name: str
    category: str = "raw_material"
    uom: str = "unit"
    standard_cost: float = 0
    reorder_level: float = 0
    reorder_qty: float = 0


class ProductOut(ProductCreate):
    id: str


class BOMItemCreate(ORMModel):
    parent_product_id: str
    component_product_id: str
    qty_per_unit: float = 1


class BOMItemOut(BOMItemCreate):
    id: str


class StockMovementCreate(ORMModel):
    product_id: str
    warehouse_id: str
    movement_type: str
    quantity: float
    unit_cost: float = 0
    reference: str | None = None
    work_order_id: str | None = None
    movement_date: datetime


class StockMovementOut(StockMovementCreate):
    id: str
