"""Exception schemas — aligned with AuditException model fields."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ExceptionOut(BaseModel):
    id: UUID
    company_id: UUID
    rule_id: UUID | None
    detected_on: date
    category: str
    title: str
    description: str | None
    severity: str
    risk_impact: str | None
    financial_impact: Decimal | None
    supporting_data: Any | None
    ai_analysis: str | None
    status: str

    model_config = {"from_attributes": True}


class ExceptionListOut(BaseModel):
    items: list[ExceptionOut]
    total: int
    page: int
    page_size: int


class ExceptionStatusUpdate(BaseModel):
    status: str
    comment: str | None = None


class AiExplainOut(BaseModel):
    exception_id: UUID
    explanation: str
    business_impact: str
    fraud_risk: str
    recommended_query: str
    suggested_remediation: str
