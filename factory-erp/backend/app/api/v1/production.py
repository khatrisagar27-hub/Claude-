from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.analytics.production import material_cost_per_unit, material_yield
from app.api.v1.deps import get_current_user
from app.database import get_db
from app.models.production import RejectionLog, WorkOrder
from app.schemas.production import (
    RejectionLogCreate,
    RejectionLogOut,
    WorkOrderCreate,
    WorkOrderOut,
    WorkOrderUpdate,
)

router = APIRouter(
    prefix="/production", tags=["production"], dependencies=[Depends(get_current_user)]
)


@router.post("/work-orders", response_model=WorkOrderOut, status_code=status.HTTP_201_CREATED)
def create_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db)) -> WorkOrder:
    if db.query(WorkOrder).filter(WorkOrder.order_number == payload.order_number).first():
        raise HTTPException(status_code=400, detail="Order number already exists")
    wo = WorkOrder(**payload.model_dump())
    db.add(wo)
    db.commit()
    db.refresh(wo)
    return wo


@router.get("/work-orders", response_model=list[WorkOrderOut])
def list_work_orders(
    plant_id: str | None = None,
    machine_id: str | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
) -> list[WorkOrder]:
    query = db.query(WorkOrder)
    if plant_id:
        query = query.filter(WorkOrder.plant_id == plant_id)
    if machine_id:
        query = query.filter(WorkOrder.machine_id == machine_id)
    if status_filter:
        query = query.filter(WorkOrder.status == status_filter)
    return query.all()


@router.get("/work-orders/{work_order_id}", response_model=WorkOrderOut)
def get_work_order(work_order_id: str, db: Session = Depends(get_db)) -> WorkOrder:
    wo = db.get(WorkOrder, work_order_id)
    if wo is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    return wo


@router.patch("/work-orders/{work_order_id}", response_model=WorkOrderOut)
def update_work_order(
    work_order_id: str, payload: WorkOrderUpdate, db: Session = Depends(get_db)
) -> WorkOrder:
    wo = db.get(WorkOrder, work_order_id)
    if wo is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(wo, field, value)
    db.commit()
    db.refresh(wo)
    return wo


@router.get("/work-orders/{work_order_id}/yield")
def get_material_yield(work_order_id: str, db: Session = Depends(get_db)) -> dict:
    if db.get(WorkOrder, work_order_id) is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    return {
        "work_order_id": work_order_id,
        "material_yield": material_yield(db, work_order_id),
        "material_cost_per_unit": material_cost_per_unit(db, work_order_id),
    }


@router.post("/rejections", response_model=RejectionLogOut, status_code=status.HTTP_201_CREATED)
def log_rejection(payload: RejectionLogCreate, db: Session = Depends(get_db)) -> RejectionLog:
    log = RejectionLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/work-orders/{work_order_id}/rejections", response_model=list[RejectionLogOut])
def list_rejections(work_order_id: str, db: Session = Depends(get_db)) -> list[RejectionLog]:
    return db.query(RejectionLog).filter(RejectionLog.work_order_id == work_order_id).all()
