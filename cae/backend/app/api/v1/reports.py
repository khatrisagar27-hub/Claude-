"""Report generation endpoints."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.rbac import get_current_user, require_roles
from app.models.user import User

router = APIRouter()


@router.post("/working-paper")
def generate_working_paper(
    company_id: uuid.UUID,
    period: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    from app.utils.export import generate_working_paper_excel
    buffer = generate_working_paper_excel(db, str(company_id), period)
    filename = f"working_paper_{company_id}_{period or 'all'}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/exception-summary")
def generate_exception_summary(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner", "manager", "auditor")),
):
    from app.utils.export import generate_exception_summary_excel
    buffer = generate_exception_summary_excel(db, str(company_id))
    filename = f"exception_summary_{company_id}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/audit-deck")
def generate_audit_deck(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "partner")),
):
    from app.utils.export import generate_audit_deck_pdf
    buffer = generate_audit_deck_pdf(db, str(company_id))
    filename = f"audit_deck_{company_id}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
