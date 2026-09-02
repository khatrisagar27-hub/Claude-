from sqlalchemy import ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Plant(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "plants"

    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(200), default=None)

    warehouses: Mapped[list["Warehouse"]] = relationship(back_populates="plant")
    shifts: Mapped[list["Shift"]] = relationship(back_populates="plant")


class Warehouse(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "warehouses"

    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"))
    code: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(200))
    # raw_material / wip / finished_good / scrap
    category: Mapped[str] = mapped_column(String(30), default="raw_material")

    plant: Mapped["Plant"] = relationship(back_populates="warehouses")


class Shift(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "shifts"

    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"))
    name: Mapped[str] = mapped_column(String(50))
    start_time: Mapped[str] = mapped_column(Time)
    end_time: Mapped[str] = mapped_column(Time)

    plant: Mapped["Plant"] = relationship(back_populates="shifts")
