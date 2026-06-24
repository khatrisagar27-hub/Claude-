"""Dashboard KPI schemas."""
from pydantic import BaseModel


class KPIOut(BaseModel):
    total_exceptions: int
    critical: int
    high: int
    medium: int
    low: int
    open_queries: int
    overdue_queries: int
    resolved_this_month: int
    composite_risk_score: float
    risk_band: str
    fraud_indicators: int
    gst_risk_amount: float


class TopExceptionOut(BaseModel):
    id: str
    title: str
    severity: str
    financial_impact: float | None
    business_area: str
    detected_at: str
    status: str


class TrendPoint(BaseModel):
    period: str
    critical: int
    high: int
    medium: int
    low: int


class DashboardOut(BaseModel):
    kpis: KPIOut
    top_exceptions: list[TopExceptionOut]
    trend: list[TrendPoint]
