"""Risk scoring, fraud indicators, GST reconciliation, and working capital models."""
import uuid
from datetime import datetime, date
from typing import Optional
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import String, Numeric, Date, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False, index=True)
    score_date: Mapped[date] = mapped_column(Date, nullable=False)
    entity_level: Mapped[str] = mapped_column(String(30), nullable=False)  # company/department/branch/process
    entity_name: Mapped[str] = mapped_column(String(200), nullable=False)
    likelihood: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    impact: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    materiality: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    frequency: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    control_weakness: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    composite_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    risk_band: Mapped[str] = mapped_column(String(20), nullable=False)  # critical/high/moderate/low
    exception_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        sa.Index("idx_risk_scores_company_date", "company_id", "score_date"),
    )


class FraudIndicator(Base):
    __tablename__ = "fraud_indicators"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False, index=True)
    analysis_date: Mapped[date] = mapped_column(Date, nullable=False)
    indicator_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    affected_transactions: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    financial_exposure: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    details_json: Mapped[Optional[dict]] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())


class GSTReconciliation(Base):
    __tablename__ = "gst_reconciliation"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(7), nullable=False)  # "2024-03"
    gstr1_turnover: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    books_turnover: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    gstr3b_itc: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    books_itc: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    gstr2b_itc: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    variance_turnover: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    variance_itc: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    risk_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    risk_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        sa.UniqueConstraint("company_id", "period", name="uq_gst_recon_company_period"),
    )


class WorkingCapitalMetric(Base):
    __tablename__ = "working_capital_metrics"

    id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False, index=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    receivables_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    receivables_overdue: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    receivables_0_30: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    receivables_31_60: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    receivables_61_90: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    receivables_above_90: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    payables_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    payables_overdue: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    inventory_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    slow_moving_inventory: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    wc_stress_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    dso: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    dpo: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    dio: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
