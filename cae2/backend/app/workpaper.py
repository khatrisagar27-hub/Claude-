"""Excel working paper for an engagement: summary, findings register, evidence,
GSTR-2B reconciliation, rules run and review trail."""
import io
from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.gst_reco import COLUMNS as RECO_COLUMNS, reconcile, summarise
from app.analytics.risk import ACTIVE, score
from app.audit.dataset import load_data
from app.models import AuditRun, Client, Engagement, Finding

HEAD = PatternFill("solid", fgColor="1E293B")
INR = '[>=10000000]##\\,##\\,##\\,##0.00;[>=100000]##\\,##\\,##0.00;##,##0.00'
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _table(ws, headers, records, widths=None, money=()):
    ws.append(headers)
    for cell in ws[ws.max_row]:
        cell.font, cell.fill = Font(bold=True, color="FFFFFF"), HEAD
        cell.alignment = Alignment(vertical="top", wrap_text=True)
    for record in records:
        ws.append(record)
        for i in money:
            ws.cell(row=ws.max_row, column=i + 1).number_format = INR
    for i, width in enumerate(widths or [], start=1):
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.freeze_panes = "A2" if ws.max_row == len(records) + 1 else None


def build_workpaper(db: Session, eng: Engagement, prepared_by: str, include_closed: bool = False) -> bytes:
    client = db.get(Client, eng.client_id)
    findings = db.scalars(select(Finding).where(Finding.engagement_id == eng.id)).all()
    listed = sorted((f for f in findings if include_closed or f.status in ACTIVE),
                    key=lambda f: (SEVERITY_ORDER[f.severity], -float(f.impact)))
    last_run = db.scalars(select(AuditRun).where(AuditRun.engagement_id == eng.id).order_by(AuditRun.id.desc())).first()
    risk = score(findings)
    ref = lambda f: f"{f.rule_code}/{f.id}"

    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 30, 50
    for label, value in [
        ("Client", client.name), ("PAN", client.pan or ""), ("GSTIN", client.gstin or ""),
        ("Engagement", eng.name), ("Period", f"{eng.period_start:%d-%m-%Y} to {eng.period_end:%d-%m-%Y}"),
        ("Data as at", (last_run.summary or {}).get("as_at", "") if last_run else "Audit not yet run"),
        ("Materiality (Rs)", float(eng.materiality or 0)), ("Clearly trivial threshold (Rs)", float(eng.trivial_threshold or 0)),
        ("Prepared by", prepared_by), ("Prepared on", f"{date.today():%d-%m-%Y}"), ("Reviewed by", ""), ("Reviewed on", ""),
        ("Scope of this paper", "All findings" if include_closed else "Findings open, queried or confirmed"),
    ]:
        ws.append([label, value])
        ws.cell(row=ws.max_row, column=1).font = Font(bold=True)
        if isinstance(value, float):
            ws.cell(row=ws.max_row, column=2).number_format = INR
    ws.append([])
    _table(ws, ["Area", "Risk score (0-100)", "Band", "Critical", "High", "Medium", "Low", "Impact (Rs)"],
           [[a, v["score"], v["band"], v["critical"], v["high"], v["medium"], v["low"], v["impact"]]
            for a, v in sorted(risk["areas"].items())], money=(7,))
    ws.append(["Overall", risk["overall"], risk["band"]])
    ws.append([])
    ws.append(["Risk score = sum of weights of open, queried and confirmed findings per area "
               "(critical 25, high 10, medium 4, low 1), capped at 100. Overall = highest area score."])
    ws.append(["Figures are computed by rule from the data supplied and are for review by the engagement team "
               "before being relied on or reported."])

    ws = wb.create_sheet("Findings")
    _table(ws, ["Ref", "Area", "Rule", "Severity", "Finding", "Detail", "Provision", "Impact (Rs)", "Status", "Fraud indicator",
                "Auditor's conclusion", "Management response"],
           [[ref(f), f.area, f.rule_code, f.severity, f.title, f.detail, f.law, float(f.impact), f.status,
             "Yes" if f.is_fraud_indicator else "",
             "\n".join(n.body for n in f.notes if n.kind == "status" and n.author != "system"),
             "\n".join(n.body for n in f.notes if n.kind == "response")] for f in listed],
           widths=[14, 12, 10, 10, 45, 70, 40, 16, 11, 9, 40, 40], money=(7,))
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    ws = wb.create_sheet("Evidence")
    ws.column_dimensions["A"].width = 16
    for f in listed:
        ws.append([ref(f), f.title])
        ws.cell(row=ws.max_row, column=1).font = ws.cell(row=ws.max_row, column=2).font = Font(bold=True)
        if f.evidence:
            keys = list(f.evidence[0].keys())
            ws.append([""] + keys)
            for cell in ws[ws.max_row][1:]:
                cell.font, cell.fill = Font(bold=True, color="FFFFFF"), HEAD
            for row in f.evidence:
                ws.append([""] + [row.get(k) for k in keys])
        ws.append([])

    data = load_data(db, eng.id)
    if not data.gstr2b.empty:
        reco = reconcile(data.purchases, data.gstr2b)
        ws = wb.create_sheet("GSTR-2B reconciliation")
        summary = summarise(reco)
        for label, key in (("ITC claimed in books", "itc_claimed"), ("Tax as per GSTR-2B", "itc_in_2b"), ("ITC at risk", "itc_at_risk")):
            ws.append([label, summary[key]])
            ws.cell(row=ws.max_row, column=2).number_format = INR
        ws.append([])
        records = [[(v.strftime("%d-%m-%Y") if hasattr(v, "strftime") and v == v else ("" if v != v else v)) for v in row]
                   for row in reco[RECO_COLUMNS].itertuples(index=False)]
        _table(ws, [c.replace("_", " ").title() for c in RECO_COLUMNS], records,
               widths=[18, 30, 18, 18, 12, 14, 14, 14, 14, 14, 10, 16, 14], money=(5, 6, 7, 8, 9, 12))

    ws = wb.create_sheet("Rules run")
    results = (last_run.summary or {}).get("rules", []) if last_run else []
    _table(ws, ["Rule", "Area", "Test", "Result", "Exceptions", "Note"],
           [[r["code"], r["area"], r["name"], {"ok": "Run", "no_data": "Not run - no data", "disabled": "Switched off",
                                               "error": "FAILED"}[r["status"]], r["hits"], r["error"]] for r in results],
           widths=[10, 12, 55, 20, 11, 60])

    ws = wb.create_sheet("Review trail")
    _table(ws, ["Ref", "When", "By", "Type", "Note"],
           [[ref(f), f"{n.created_at:%d-%m-%Y %H:%M}", n.author, n.kind, n.body] for f in listed for n in f.notes],
           widths=[14, 17, 25, 10, 100])

    # Client text beginning with "=" (a narration, a party name) must stay text:
    # this workbook contains no formulas, so any formula cell is neutralised.
    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.data_type == "f":
                    cell.data_type = "s"

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()
