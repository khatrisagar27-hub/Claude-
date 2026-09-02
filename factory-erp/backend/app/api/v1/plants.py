from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.database import get_db
from app.models.plant import Plant, Shift, Warehouse
from app.schemas.plant import (
    PlantCreate,
    PlantOut,
    ShiftCreate,
    ShiftOut,
    WarehouseCreate,
    WarehouseOut,
)

router = APIRouter(prefix="/plants", tags=["plants"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=PlantOut, status_code=status.HTTP_201_CREATED)
def create_plant(payload: PlantCreate, db: Session = Depends(get_db)) -> Plant:
    plant = Plant(**payload.model_dump())
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant


@router.get("", response_model=list[PlantOut])
def list_plants(db: Session = Depends(get_db)) -> list[Plant]:
    return db.query(Plant).all()


@router.get("/{plant_id}", response_model=PlantOut)
def get_plant(plant_id: str, db: Session = Depends(get_db)) -> Plant:
    plant = db.get(Plant, plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.post("/warehouses", response_model=WarehouseOut, status_code=status.HTTP_201_CREATED)
def create_warehouse(payload: WarehouseCreate, db: Session = Depends(get_db)) -> Warehouse:
    warehouse = Warehouse(**payload.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.get("/{plant_id}/warehouses", response_model=list[WarehouseOut])
def list_warehouses(plant_id: str, db: Session = Depends(get_db)) -> list[Warehouse]:
    return db.query(Warehouse).filter(Warehouse.plant_id == plant_id).all()


@router.post("/shifts", response_model=ShiftOut, status_code=status.HTTP_201_CREATED)
def create_shift(payload: ShiftCreate, db: Session = Depends(get_db)) -> Shift:
    shift = Shift(**payload.model_dump())
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


@router.get("/{plant_id}/shifts", response_model=list[ShiftOut])
def list_shifts(plant_id: str, db: Session = Depends(get_db)) -> list[Shift]:
    return db.query(Shift).filter(Shift.plant_id == plant_id).all()
