from datetime import date, datetime

from app.schemas.common import ORMModel


class MachineCreate(ORMModel):
    plant_id: str
    code: str
    name: str
    category: str | None = None
    rated_capacity_per_hour: float = 0
    install_date: date | None = None
    status: str = "idle"


class MachineOut(MachineCreate):
    id: str


class DowntimeCreate(ORMModel):
    machine_id: str
    work_order_id: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    reason_category: str = "other"
    remarks: str | None = None


class DowntimeOut(DowntimeCreate):
    id: str


class MaintenanceLogCreate(ORMModel):
    machine_id: str
    maintenance_type: str = "preventive"
    scheduled_date: date | None = None
    performed_date: date | None = None
    cost: float = 0
    next_due_date: date | None = None
    remarks: str | None = None


class MaintenanceLogOut(MaintenanceLogCreate):
    id: str
