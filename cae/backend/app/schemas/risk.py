"""Risk and fraud schemas."""
from datetime import date
from uuid import UUID

from pydantic import BaseModel


class RiskScoreOut(BaseModel):
    id: UUID
    company_id: UUID
    score_date: date
    entity_level: str
    entity_name: str
    likelihood: float
    impact: float
    materiality: float
    frequency: float
    control_weakness: float
    composite_score: float
    risk_band: str

    model_config = {"from_attributes": True}


class HeatmapCell(BaseModel):
    process: str
    entity: str
    score: float
    band: str
    exception_count: int


class HeatmapOut(BaseModel):
    company_id: UUID
    score_date: date
    cells: list[HeatmapCell]


class FraudIndicatorOut(BaseModel):
    id: UUID
    company_id: UUID
    indicator_type: str
    analysis_date: date
    description: str
    score: float
    affected_transactions: int
    financial_exposure: float | None = None

    model_config = {"from_attributes": True}


class GSTReconciliationOut(BaseModel):
    id: UUID
    company_id: UUID
    period: str
    gstr1_turnover: float | None
    books_turnover: float | None
    gstr3b_itc: float | None
    books_itc: float | None
    gstr2b_itc: float | None
    variance_turnover: float | None
    variance_itc: float | None
    risk_amount: float | None
    status: str

    model_config = {"from_attributes": True}
