from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin

# planned / in_progress / completed / cancelled
WORK_ORDER_STATUSES = ("planned", "in_progress", "completed", "cancelled")


class WorkOrder(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "work_orders"

    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"))
    order_number: Mapped[str] = mapped_column(String(50), unique=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.id"))
    shift_id: Mapped[str | None] = mapped_column(ForeignKey("shifts.id"), default=None)

    planned_qty: Mapped[float] = mapped_column(Numeric(14, 3), default=0)
    produced_qty: Mapped[float] = mapped_column(Numeric(14, 3), default=0)
    rejected_qty: Mapped[float] = mapped_column(Numeric(14, 3), default=0)

    planned_start: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    planned_end: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    actual_end: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    status: Mapped[str] = mapped_column(String(20), default="planned")

    product: Mapped["Product"] = relationship()
    machine: Mapped["Machine"] = relationship()
    rejections: Mapped[list["RejectionLog"]] = relationship(back_populates="work_order")


class RejectionLog(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "rejection_logs"

    work_order_id: Mapped[str] = mapped_column(ForeignKey("work_orders.id"))
    defect_type: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[float] = mapped_column(Numeric(14, 3))
    remarks: Mapped[str | None] = mapped_column(String(500), default=None)

    work_order: Mapped["WorkOrder"] = relationship(back_populates="rejections")
