"""Excel and PDF export utilities."""
from __future__ import annotations

import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def generate_working_paper_excel(db: "Session", company_id: str, period: str | None = None) -> io.BytesIO:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from app.models.audit import AuditException
    from app.models.tenant import Company
    import uuid

    wb = openpyxl.Workbook()

    company = db.query(Company).filter(Company.id == uuid.UUID(company_id)).first()
    company_name = company.name if company else "Company"

    # Cover sheet
    ws_cover = wb.active
    ws_cover.title = "Cover"
    ws_cover["A1"] = "INTERNAL AUDIT WORKING PAPER"
    ws_cover["A1"].font = Font(bold=True, size=16, color="C8A951")
    ws_cover["A2"] = company_name
    ws_cover["A2"].font = Font(bold=True, size=14)
    ws_cover["A3"] = f"Period: {period or 'All Periods'}"
    ws_cover["A4"] = f"Generated: {__import__('datetime').datetime.now().strftime('%d %b %Y %H:%M')}"

    # Exceptions sheet
    ws = wb.create_sheet("Exceptions")
    headers = ["Exc #", "Rule Code", "Category", "Title", "Severity", "Risk Area", "Financial Impact (₹)", "Status", "Detected On"]
    header_fill = PatternFill(start_color="0D1117", end_color="0D1117", fill_type="solid")
    header_font = Font(bold=True, color="C8A951")

    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    q = db.query(AuditException).filter(AuditException.company_id == uuid.UUID(company_id))
    for i, exc in enumerate(q.order_by(AuditException.severity, AuditException.detected_at.desc()).all(), 2):
        ws.cell(row=i, column=1, value=i - 1)
        ws.cell(row=i, column=2, value=str(exc.rule_id)[:8])
        ws.cell(row=i, column=3, value=exc.business_area)
        ws.cell(row=i, column=4, value=exc.title)
        ws.cell(row=i, column=5, value=exc.severity.upper())
        ws.cell(row=i, column=6, value=exc.risk_category)
        ws.cell(row=i, column=7, value=float(exc.financial_impact or 0))
        ws.cell(row=i, column=8, value=exc.status)
        ws.cell(row=i, column=9, value=exc.detected_at.strftime("%d-%b-%Y"))

        severity_colors = {"CRITICAL": "FF0000", "HIGH": "FF6B00", "MEDIUM": "FFC107", "LOW": "28A745"}
        color = severity_colors.get(exc.severity.upper(), "FFFFFF")
        ws.cell(row=i, column=5).fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
        ws.cell(row=i, column=5).font = Font(bold=True, color="FFFFFF")

    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].auto_size = True

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def generate_exception_summary_excel(db: "Session", company_id: str) -> io.BytesIO:
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    from app.models.audit import AuditException
    from sqlalchemy import func
    import uuid

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Summary"

    ws["A1"] = "Exception Summary"
    ws["A1"].font = Font(bold=True, size=14)

    severities = ["critical", "high", "medium", "low"]
    for i, sev in enumerate(severities, 2):
        count = db.query(func.count(AuditException.id)).filter(
            AuditException.company_id == uuid.UUID(company_id),
            AuditException.severity == sev,
        ).scalar() or 0
        ws.cell(row=i, column=1, value=sev.upper())
        ws.cell(row=i, column=2, value=count)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def generate_audit_deck_pdf(db: "Session", company_id: str) -> io.BytesIO:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from app.models.audit import AuditException
    from app.models.tenant import Company
    import uuid

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    company = db.query(Company).filter(Company.id == uuid.UUID(company_id)).first()
    company_name = company.name if company else "Company"

    c.setFillColorRGB(0.05, 0.07, 0.09)
    c.rect(0, 0, w, h, fill=1)

    c.setFillColorRGB(0.78, 0.66, 0.32)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(w / 2, h - 100, "INTERNAL AUDIT REPORT")
    c.setFont("Helvetica", 16)
    c.drawCentredString(w / 2, h - 140, company_name)

    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, h - 200, "Exception Summary")

    from sqlalchemy import func
    y = h - 230
    for sev in ["critical", "high", "medium", "low"]:
        count = db.query(func.count(AuditException.id)).filter(
            AuditException.company_id == uuid.UUID(company_id),
            AuditException.severity == sev,
        ).scalar() or 0
        c.setFont("Helvetica", 11)
        c.drawString(60, y, f"{sev.upper()}: {count} exceptions")
        y -= 20

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
