from datetime import datetime

from app.schemas.common import ORMModel


class WorkOrderCreate(ORMModel):
    plant_id: str
    order_number: str
    product_id: str
    machine_id: str
    shift_id: str | None = None
    planned_qty: float = 0
    produced_qty: float = 0
    rejected_qty: float = 0
    planned_start: datetime | None = None
    planned_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    status: str = "planned"


class WorkOrderUpdate(ORMModel):
    produced_qty: float | None = None
    rejected_qty: float | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    status: str | None = None


class WorkOrderOut(WorkOrderCreate):
    id: str


class RejectionLogCreate(ORMModel):
    work_order_id: str
    defect_type: str
    quantity: float
    remarks: str | None = None


class RejectionLogOut(RejectionLogCreate):
    id: str
