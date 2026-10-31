"""
Audit engagement — one audit of one company: a Statutory audit of a financial year or an
Internal audit of any period. Audit runs, exceptions and reports are scoped to it.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Boolean, Date, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

AUDIT_TYPES = ("statutory", "internal")


class AuditEngagement(Base):
    __tablename__ = "audit_engagements"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    audit_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="statutory / internal")
    financial_year: Mapped[Optional[int]] = mapped_column(
        sa.Integer, nullable=True, comment="FY start year (2024 = FY 2024-25); set for statutory audits"
    )
    period_from: Mapped[date] = mapped_column(Date, nullable=False)
    period_to: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="planning", comment="planning / fieldwork / reporting / closed"
    )
    # Statutory reporting frame (from the Statutory > Applicability screen)
    caro_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    ifc_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    tax_audit_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    materiality: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True, comment="Overall materiality (SA 320); findings at or above it are flagged"
    )
    scope_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(sa.UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True, onupdate=func.now())

    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]

    @property
    def label(self) -> str:
        kind = "Statutory Audit" if self.audit_type == "statutory" else "Internal Audit"
        if self.audit_type == "statutory" and self.financial_year:
            return f"{kind} · FY {self.financial_year}-{str(self.financial_year + 1)[-2:]}"
        return f"{kind} · {self.period_from:%d-%m-%Y} to {self.period_to:%d-%m-%Y}"

    def __repr__(self) -> str:
        return f"<AuditEngagement {self.audit_type} {self.period_from}..{self.period_to} company={self.company_id}>"
