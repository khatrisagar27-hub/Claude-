"""
User model — platform users with role-based access control.

Roles:
  super_admin    — Anthropic/platform-level admin
  partner        — CA partner owning client engagements
  manager        — CA manager overseeing audits
  auditor        — Field auditor raising exceptions
  cfo            — Client CFO with full financial view
  management     — Client management (MD / CEO)
  process_owner  — Client process owner responsible for remediation
  client_user    — General read-only client user
"""
import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import String, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # super_admin users may not be scoped to a company
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment=(
            "super_admin | partner | manager | auditor | "
            "cfo | management | process_owner | client_user"
        ),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sa.true()
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(  # type: ignore[name-defined]
        "Tenant", lazy="select"
    )
    company: Mapped[Optional["Company"]] = relationship(  # type: ignore[name-defined]
        "Company", back_populates="users", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<User id={self.id} email={self.email!r} role={self.role!r}>"
        )
