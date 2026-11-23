"""Report generation endpoints.

With ``engagement_id`` the report follows the audit type: a Statutory audit gets the statutory
working paper (CARO 2020 / tax audit / IFC matrices) and findings PDF; an Internal audit gets the
Internal Audit Report (process-wise observations and action plan). Without it, the reports cover
continuous monitoring outside any engagement.
"""
import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.engagement import get_engagement
from app.utils.rbac import get_current_user, require_roles
from app.models.user import User

router = APIRouter()

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _stream(buffer, media_type: str, filename: str) -> StreamingResponse:
    return StreamingResponse(buffer, media_type=media_type,
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def _slug(engagement) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", engagement.label).strip("_")


@router.post("/working-paper")
def generate_working_paper(
    company_id: uuid.UUID,
    period: Optional[str] = None,
    engagement_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    engagement = get_engagement(db, engagement_id, company_id)
    if engagement is not None:
        from app.utils.engagement_export import internal_audit_report, statutory_working_paper
        if engagement.audit_type == "statutory":
            return _stream(statutory_working_paper(db, engagement), _XLSX, f"Statutory_Audit_WP_{_slug(engagement)}.xlsx")
        return _stream(internal_audit_report(db, engagement), _XLSX, f"Internal_Audit_Report_{_slug(engagement)}.xlsx")
    from app.utils.export import generate_working_paper_excel
    buffer = generate_working_paper_excel(db, str(company_id), period)
    return _stream(buffer, _XLSX, f"continuous_monitoring_wp_{company_id}.xlsx")


@router.post("/exception-summary")
def generate_exception_summary(
    company_id: uuid.UUID,
    engagement_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    engagement = get_engagement(db, engagement_id, company_id)
    if engagement is not None:   # the engagement workbook already carries the summary sheets
        from app.utils.engagement_export import internal_audit_report, statutory_working_paper
        build = statutory_working_paper if engagement.audit_type == "statutory" else internal_audit_report
        return _stream(build(db, engagement), _XLSX, f"Exception_Summary_{_slug(engagement)}.xlsx")
    from app.utils.export import generate_exception_summary_excel
    buffer = generate_exception_summary_excel(db, str(company_id))
    return _stream(buffer, _XLSX, f"exception_summary_{company_id}.xlsx")


@router.post("/audit-deck")
def generate_audit_deck(
    company_id: uuid.UUID,
    engagement_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner")),
):
    engagement = get_engagement(db, engagement_id, company_id)
    if engagement is not None:
        from app.utils.engagement_export import engagement_pdf
        kind = "Statutory_Audit_Findings" if engagement.audit_type == "statutory" else "Internal_Audit_Report"
        return _stream(engagement_pdf(db, engagement), "application/pdf", f"{kind}_{_slug(engagement)}.pdf")
    from app.utils.export import generate_audit_deck_pdf
    buffer = generate_audit_deck_pdf(db, str(company_id))
    return _stream(buffer, "application/pdf", f"continuous_monitoring_deck_{company_id}.pdf")
