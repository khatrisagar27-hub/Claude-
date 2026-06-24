"""
Tenant and Company models — top of the multi-tenant hierarchy.

Tenant  →  (many) Company  →  all transactional data
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy import Numeric, String, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Tenant(Base):
    """
    Root entity that owns one or more Companies.
    Represents a CA/audit firm or an enterprise group.
    """
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="starter",
        comment="starter / professional / enterprise",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
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
    companies: Mapped[List["Company"]] = relationship(
        "Company",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} slug={self.slug!r} plan={self.plan!r}>"


class Company(Base):
    """
    An audited legal entity — subsidiary, branch, or standalone company.
    All transactional and audit data is scoped to a Company.
    """
    __tablename__ = "companies"

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
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(
        String(15), nullable=True, comment="GST Identification Number"
    )
    pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    cin: Mapped[Optional[str]] = mapped_column(
        String(21), nullable=True, comment="Corporate Identity Number (ROC)"
    )
    entity_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Private / Public / LLP / Partnership / Proprietorship",
    )
    industry_sector: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Manufacturing / Trading / Services / NBFC / etc.",
    )
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    annual_turnover: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
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
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="companies")
    users: Mapped[List["User"]] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="company",
        lazy="select",
    )
    audit_exceptions: Mapped[List["AuditException"]] = relationship(  # type: ignore[name-defined]
        "AuditException",
        back_populates="company",
        lazy="select",
    )
    management_queries: Mapped[List["ManagementQuery"]] = relationship(  # type: ignore[name-defined]
        "ManagementQuery",
        back_populates="company",
        lazy="select",
    )
    sync_jobs: Mapped[List["SyncJob"]] = relationship(  # type: ignore[name-defined]
        "SyncJob",
        back_populates="company",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Company id={self.id} name={self.name!r} "
            f"gstin={self.gstin!r} tenant_id={self.tenant_id}>"
        )
