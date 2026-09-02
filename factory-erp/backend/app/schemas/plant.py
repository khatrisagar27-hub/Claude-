from datetime import time

from app.schemas.common import ORMModel


class PlantCreate(ORMModel):
    code: str
    name: str
    location: str | None = None


class PlantOut(PlantCreate):
    id: str


class WarehouseCreate(ORMModel):
    plant_id: str
    code: str
    name: str
    category: str = "raw_material"


class WarehouseOut(WarehouseCreate):
    id: str


class ShiftCreate(ORMModel):
    plant_id: str
    name: str
    start_time: time
    end_time: time


class ShiftOut(ShiftCreate):
    id: str
