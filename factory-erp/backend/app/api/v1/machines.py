from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.database import get_db
from app.models.machine import MachineDowntime, MaintenanceLog
from app.models.machine import Machine
from app.schemas.machine import (
    DowntimeCreate,
    DowntimeOut,
    MachineCreate,
    MachineOut,
    MaintenanceLogCreate,
    MaintenanceLogOut,
)

router = APIRouter(prefix="/machines", tags=["machines"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=MachineOut, status_code=status.HTTP_201_CREATED)
def create_machine(payload: MachineCreate, db: Session = Depends(get_db)) -> Machine:
    machine = Machine(**payload.model_dump())
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.get("", response_model=list[MachineOut])
def list_machines(plant_id: str | None = None, db: Session = Depends(get_db)) -> list[Machine]:
    query = db.query(Machine)
    if plant_id:
        query = query.filter(Machine.plant_id == plant_id)
    return query.all()


@router.get("/{machine_id}", response_model=MachineOut)
def get_machine(machine_id: str, db: Session = Depends(get_db)) -> Machine:
    machine = db.get(Machine, machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


@router.patch("/{machine_id}/status", response_model=MachineOut)
def set_machine_status(machine_id: str, status_value: str, db: Session = Depends(get_db)) -> Machine:
    machine = db.get(Machine, machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    if status_value not in ("running", "idle", "breakdown", "maintenance"):
        raise HTTPException(status_code=422, detail="Invalid status")
    machine.status = status_value
    db.commit()
    db.refresh(machine)
    return machine


@router.post("/downtimes", response_model=DowntimeOut, status_code=status.HTTP_201_CREATED)
def log_downtime(payload: DowntimeCreate, db: Session = Depends(get_db)) -> MachineDowntime:
    downtime = MachineDowntime(**payload.model_dump())
    db.add(downtime)
    db.commit()
    db.refresh(downtime)
    return downtime


@router.get("/{machine_id}/downtimes", response_model=list[DowntimeOut])
def list_downtimes(machine_id: str, db: Session = Depends(get_db)) -> list[MachineDowntime]:
    return db.query(MachineDowntime).filter(MachineDowntime.machine_id == machine_id).all()


@router.post(
    "/maintenance-logs", response_model=MaintenanceLogOut, status_code=status.HTTP_201_CREATED
)
def log_maintenance(payload: MaintenanceLogCreate, db: Session = Depends(get_db)) -> MaintenanceLog:
    log = MaintenanceLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/{machine_id}/maintenance-logs", response_model=list[MaintenanceLogOut])
def list_maintenance(machine_id: str, db: Session = Depends(get_db)) -> list[MaintenanceLog]:
    return db.query(MaintenanceLog).filter(MaintenanceLog.machine_id == machine_id).all()
