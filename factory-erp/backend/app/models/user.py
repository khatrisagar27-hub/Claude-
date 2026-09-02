from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin

# operator / supervisor / plant_manager / admin
ROLES = ("operator", "supervisor", "plant_manager", "admin")


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    plant_id: Mapped[str | None] = mapped_column(ForeignKey("plants.id"), default=None)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="operator")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
