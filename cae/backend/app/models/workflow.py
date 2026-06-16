"""Management Query, Response, and Remediation Action models."""
import uuid
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import String, Boolean, Text, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Company
    from app.models.audit import AuditException


class ManagementQuery(Base):
    __tablename__ = "management_queries"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exception_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("audit_exceptions.id"), nullable=False, index=True)
    company_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False, index=True)
    query_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    process_area: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_question: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True)
    assigned_to_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="open")
    auditor_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raised_by_user_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False)
    raised_by_name: Mapped[str] = mapped_column(String(200), nullable=False)
    raised_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())

    company: Mapped["Company"] = relationship("Company", back_populates="management_queries", lazy="select")
    exception: Mapped["AuditException"] = relationship("AuditException", back_populates="management_queries", lazy="select")
    responses: Mapped[List["QueryResponse"]] = relationship("QueryResponse", back_populates="query", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ManagementQuery {self.query_no} status={self.status}>"


class QueryResponse(Base):
    __tablename__ = "query_responses"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("management_queries.id"), nullable=False, index=True)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    responded_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True)
    responded_by_name: Mapped[str] = mapped_column(String(200), nullable=False)
    responded_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    attachment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    auditor_review_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    auditor_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    query: Mapped["ManagementQuery"] = relationship("ManagementQuery", back_populates="responses")


class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False, index=True)
    exception_id: Mapped[Optional[uuid.UUID]] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("audit_exceptions.id"), nullable=True)
    control_gap_description: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_plan: Mapped[str] = mapped_column(Text, nullable=False)
    responsible_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True)
    responsible_name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_closure_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    evidence_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    retest_outcome: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    residual_risk_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="open")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True, onupdate=func.now())

    exception: Mapped[Optional["AuditException"]] = relationship("AuditException", back_populates="remediation_actions", lazy="select")

    def __repr__(self) -> str:
        return f"<RemediationAction {self.id} status={self.status}>"
