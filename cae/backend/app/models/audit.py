"""
Audit models — rules engine, execution results, and exceptions.

Models:
  AuditRule      — configurable audit test definitions
  RuleExecution  — record of each time a rule was run with results
  AuditException — individual exception / finding raised by a rule execution
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

import sqlalchemy as sa
from sqlalchemy import (
    String, Boolean, Numeric, Date, DateTime, Text, Integer,
    UniqueConstraint, ForeignKey, text, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class AuditRule(Base):
    """
    Configurable audit test — defines WHAT to check, HOW to check it,
    and how to classify findings.
    """
    __tablename__ = "audit_rules"
    __table_args__ = (
        UniqueConstraint("company_id", "rule_code", name="uq_auditrule_company_code"),
        Index("ix_auditrule_company_category", "company_id", "category"),
        Index("ix_auditrule_is_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="NULL = global rule available to all companies",
    )
    rule_code: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment=(
            "revenue / expenditure / payroll / gst / inventory / "
            "bank_reconciliation / related_party / statutory"
        )
    )
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="medium",
        comment="critical / high / medium / low / info"
    )
    risk_area: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Rule logic — supports SQL, Python expression, or AI prompt
    rule_type: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="sql",
        comment="sql / python / ai_prompt / threshold"
    )
    rule_definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="SQL query or Python expression")
    ai_prompt_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    threshold_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, comment="Numeric threshold parameters")
    parameters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, comment="Configurable runtime parameters")

    # Scheduling
    run_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="daily",
        comment="realtime / hourly / daily / weekly / monthly / on_demand"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
    auto_raise_exception: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sa.true(),
        comment="If true, automatically create AuditException on positive detection"
    )
    requires_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sa.false(),
        comment="Exception requires management approval to close"
    )

    # Metadata
    regulatory_reference: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Applicable law / standard / CARO clause"
    )
    remediation_guidance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relationships
    executions: Mapped[List["RuleExecution"]] = relationship(
        "RuleExecution", back_populates="rule",
        cascade="all, delete-orphan", lazy="select"
    )
    exceptions: Mapped[List["AuditException"]] = relationship(
        "AuditException", back_populates="rule", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<AuditRule id={self.id} code={self.rule_code!r} "
            f"category={self.category!r} severity={self.severity!r}>"
        )


class RuleExecution(Base):
    """
    Log of a single run of an AuditRule — captures timing, status,
    count of exceptions found, and execution diagnostics.
    """
    __tablename__ = "rule_executions"
    __table_args__ = (
        Index("ix_ruleexec_company_rule", "company_id", "rule_id"),
        Index("ix_ruleexec_started_at", "started_at"),
        Index("ix_ruleexec_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("audit_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    triggered_by: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="scheduler",
        comment="scheduler / manual / api / ingestion_hook"
    )
    triggered_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True), nullable=True
    )
    period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="running",
        comment="running / completed / failed / cancelled"
    )
    records_scanned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exceptions_found: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    exceptions_raised: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_log: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    rule: Mapped["AuditRule"] = relationship("AuditRule", back_populates="executions", lazy="select")
    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]
    exceptions: Mapped[List["AuditException"]] = relationship(
        "AuditException", back_populates="execution", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<RuleExecution id={self.id} rule_id={self.rule_id} "
            f"status={self.status!r} found={self.exceptions_found}>"
        )


class AuditException(Base):
    """
    An individual audit finding / exception raised by a rule execution.
    Tracks lifecycle from detection through remediation and closure.
    """
    __tablename__ = "audit_exceptions"
    __table_args__ = (
        Index("ix_auditexc_company_severity", "company_id", "severity"),
        Index("ix_auditexc_status", "status"),
        Index("ix_auditexc_rule", "rule_id"),
        Index("ix_auditexc_detected_on", "detected_on"),
        Index("ix_auditexc_due_date", "due_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("audit_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    execution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("rule_executions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Exception identity
    exception_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="critical / high / medium / low / info"
    )
    risk_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Source record reference
    source_document_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(sa.UUID(as_uuid=True), nullable=True)
    source_document_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    financial_impact: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")

    # AI-generated analysis
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supporting_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Status lifecycle
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="open",
        comment="open / in_review / management_query_sent / remediation_in_progress / resolved / closed / false_positive"
    )
    detected_on: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    resolved_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    closed_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Assignment
    assigned_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True), nullable=True
    )
    raised_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True), nullable=True
    )
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True), nullable=True
    )
    closed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True), nullable=True
    )

    # Resolution details
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preventive_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship(  # type: ignore[name-defined]
        "Company", back_populates="audit_exceptions", lazy="select"
    )
    rule: Mapped[Optional["AuditRule"]] = relationship(
        "AuditRule", back_populates="exceptions", lazy="select"
    )
    execution: Mapped[Optional["RuleExecution"]] = relationship(
        "RuleExecution", back_populates="exceptions", lazy="select"
    )
    management_queries: Mapped[List["ManagementQuery"]] = relationship(  # type: ignore[name-defined]
        "ManagementQuery", back_populates="exception", lazy="select"
    )
    remediation_actions: Mapped[List["RemediationAction"]] = relationship(  # type: ignore[name-defined]
        "RemediationAction", back_populates="exception", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<AuditException id={self.id} number={self.exception_number!r} "
            f"severity={self.severity!r} status={self.status!r}>"
        )
