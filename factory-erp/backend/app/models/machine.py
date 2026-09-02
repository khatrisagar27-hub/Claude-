from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin

# running / idle / breakdown / maintenance
MACHINE_STATUSES = ("running", "idle", "breakdown", "maintenance")

# breakdown / changeover / no_material / power / planned_maintenance / other
DOWNTIME_CATEGORIES = (
    "breakdown",
    "changeover",
    "no_material",
    "power",
    "planned_maintenance",
    "other",
)

MAINTENANCE_TYPES = ("preventive", "breakdown", "predictive")


class Machine(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "machines"

    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"))
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(100), default=None)
    # units produced per hour at ideal (unhindered) rate — the OEE "ideal run rate"
    rated_capacity_per_hour: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    install_date: Mapped[date | None] = mapped_column(Date, default=None)
    status: Mapped[str] = mapped_column(String(20), default="idle")

    downtimes: Mapped[list["MachineDowntime"]] = relationship(back_populates="machine")
    maintenance_logs: Mapped[list["MaintenanceLog"]] = relationship(back_populates="machine")


class MachineDowntime(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "machine_downtimes"

    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.id"))
    work_order_id: Mapped[str | None] = mapped_column(ForeignKey("work_orders.id"), default=None)
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    reason_category: Mapped[str] = mapped_column(String(30), default="other")
    remarks: Mapped[str | None] = mapped_column(String(500), default=None)

    machine: Mapped["Machine"] = relationship(back_populates="downtimes")


class MaintenanceLog(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_logs"

    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.id"))
    maintenance_type: Mapped[str] = mapped_column(String(20), default="preventive")
    scheduled_date: Mapped[date | None] = mapped_column(Date, default=None)
    performed_date: Mapped[date | None] = mapped_column(Date, default=None)
    cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    next_due_date: Mapped[date | None] = mapped_column(Date, default=None)
    remarks: Mapped[str | None] = mapped_column(String(500), default=None)

    machine: Mapped["Machine"] = relationship(back_populates="maintenance_logs")
