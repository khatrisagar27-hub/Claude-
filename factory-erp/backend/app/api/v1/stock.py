from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.analytics.stock import on_hand_qty
from app.api.v1.deps import get_current_user
from app.database import get_db
from app.models.stock import BOMItem, Product, StockMovement
from app.schemas.stock import (
    BOMItemCreate,
    BOMItemOut,
    ProductCreate,
    ProductOut,
    StockMovementCreate,
    StockMovementOut,
)

router = APIRouter(prefix="/stock", tags=["stock"], dependencies=[Depends(get_current_user)])


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    if db.query(Product).filter(Product.sku == payload.sku).first():
        raise HTTPException(status_code=400, detail="SKU already exists")
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/products", response_model=list[ProductOut])
def list_products(plant_id: str | None = None, db: Session = Depends(get_db)) -> list[Product]:
    query = db.query(Product)
    if plant_id:
        query = query.filter(Product.plant_id == plant_id)
    return query.all()


@router.get("/products/{product_id}/on-hand")
def get_on_hand(product_id: str, db: Session = Depends(get_db)) -> dict:
    if db.get(Product, product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"product_id": product_id, "on_hand_qty": on_hand_qty(db, product_id)}


@router.post("/bom", response_model=BOMItemOut, status_code=status.HTTP_201_CREATED)
def add_bom_item(payload: BOMItemCreate, db: Session = Depends(get_db)) -> BOMItem:
    item = BOMItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/bom/{parent_product_id}", response_model=list[BOMItemOut])
def get_bom(parent_product_id: str, db: Session = Depends(get_db)) -> list[BOMItem]:
    return db.query(BOMItem).filter(BOMItem.parent_product_id == parent_product_id).all()


@router.post("/movements", response_model=StockMovementOut, status_code=status.HTTP_201_CREATED)
def record_movement(payload: StockMovementCreate, db: Session = Depends(get_db)) -> StockMovement:
    if payload.movement_type not in (
        "receipt",
        "issue",
        "production_in",
        "production_out",
        "transfer",
        "adjustment",
        "scrap",
    ):
        raise HTTPException(status_code=422, detail="Invalid movement_type")
    movement = StockMovement(**payload.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


@router.get("/movements", response_model=list[StockMovementOut])
def list_movements(product_id: str | None = None, db: Session = Depends(get_db)) -> list[StockMovement]:
    query = db.query(StockMovement)
    if product_id:
        query = query.filter(StockMovement.product_id == product_id)
    return query.order_by(StockMovement.movement_date.desc()).all()
