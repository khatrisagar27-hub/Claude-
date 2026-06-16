"""Management query schemas."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class QueryCreate(BaseModel):
    exception_id: UUID
    process_area: str
    severity: str
    description: str
    evidence_summary: str
    suggested_question: str
    assigned_to_user_id: UUID | None = None
    due_date: date | None = None


class QueryOut(BaseModel):
    id: UUID
    exception_id: UUID
    company_id: UUID
    query_no: str
    process_area: str
    severity: str
    description: str
    evidence_summary: str
    suggested_question: str
    assigned_to_user_id: UUID | None
    due_date: date | None
    status: str
    raised_at: datetime

    model_config = {"from_attributes": True}


class QueryResponseCreate(BaseModel):
    response_text: str
    attachment_url: str | None = None


class QueryResponseOut(BaseModel):
    id: UUID
    query_id: UUID
    response_text: str
    responded_at: datetime
    attachment_url: str | None
    auditor_review_status: str | None
    auditor_comment: str | None

    model_config = {"from_attributes": True}


class QueryStatusUpdate(BaseModel):
    status: str
    auditor_comment: str | None = None
