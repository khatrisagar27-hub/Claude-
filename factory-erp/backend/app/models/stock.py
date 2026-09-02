from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin

# raw_material / wip / finished_good / consumable / spare_part
PRODUCT_CATEGORIES = ("raw_material", "wip", "finished_good", "consumable", "spare_part")

# receipt / issue / production_in / production_out / transfer / adjustment / scrap
MOVEMENT_TYPES = (
    "receipt",
    "issue",
    "production_in",
    "production_out",
    "transfer",
    "adjustment",
    "scrap",
)
# movement types that increase on-hand qty; everything else decreases it
INWARD_TYPES = {"receipt", "production_in", "adjustment"}


class Product(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "products"

    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"))
    sku: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(30), default="raw_material")
    uom: Mapped[str] = mapped_column(String(20), default="unit")
    standard_cost: Mapped[float] = mapped_column(Numeric(14, 4), default=0)
    reorder_level: Mapped[float] = mapped_column(Numeric(14, 3), default=0)
    reorder_qty: Mapped[float] = mapped_column(Numeric(14, 3), default=0)

    bom_lines: Mapped[list["BOMItem"]] = relationship(
        back_populates="parent_product", foreign_keys="BOMItem.parent_product_id"
    )


class BOMItem(UUIDPKMixin, TimestampMixin, Base):
    """One component row of a finished/WIP product's bill of materials."""

    __tablename__ = "bom_items"

    parent_product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    component_product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    qty_per_unit: Mapped[float] = mapped_column(Numeric(14, 4), default=1)

    parent_product: Mapped["Product"] = relationship(
        back_populates="bom_lines", foreign_keys=[parent_product_id]
    )
    component_product: Mapped["Product"] = relationship(foreign_keys=[component_product_id])


class StockMovement(UUIDPKMixin, TimestampMixin, Base):
    """The stock ledger. On-hand quantity is never stored directly — it is
    always SUM(inward) - SUM(outward) over this table, computed in
    app/analytics/stock.py. Same discipline as an accounting ledger: a
    mutable balance field invites drift between what's recorded and what's
    true."""

    __tablename__ = "stock_movements"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    warehouse_id: Mapped[str] = mapped_column(ForeignKey("warehouses.id"))
    movement_type: Mapped[str] = mapped_column(String(20))
    quantity: Mapped[float] = mapped_column(Numeric(14, 3))
    unit_cost: Mapped[float] = mapped_column(Numeric(14, 4), default=0)
    reference: Mapped[str | None] = mapped_column(String(100), default=None)
    work_order_id: Mapped[str | None] = mapped_column(ForeignKey("work_orders.id"), default=None)
    movement_date: Mapped[datetime] = mapped_column(DateTime)

    product: Mapped["Product"] = relationship()
