"""Stores a parsed file as an import batch."""
import io

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from sqlalchemy import delete, insert
from sqlalchemy.orm import Session

from app.ingest.schema import DATASETS
from app.ingest.tabular import parse_file, validate_rows
from app.ingest.tally import parse_tally_xml
from app.models import Engagement, ImportBatch

MAX_ERRORS_KEPT = 200


def _derive(dataset: str, rows: list[dict], mapped: list[str]) -> list[str]:
    """Fill values that are definitions, not estimates, and say so."""
    notes = []
    if dataset in ("sales", "purchases") and "total" not in mapped:
        for r in rows:
            r["total"] = round(r.get("taxable_value", 0) + r.get("cgst", 0) + r.get("sgst", 0) + r.get("igst", 0), 2)
        notes.append("No invoice total column: total taken as taxable value + CGST + SGST + IGST.")
    if dataset == "purchases" and "itc_claimed" not in mapped:
        for r in rows:
            r["itc_claimed"] = round(r.get("cgst", 0) + r.get("sgst", 0) + r.get("igst", 0), 2)
        notes.append("No ITC column: ITC claimed assumed equal to GST charged on every invoice. "
                     "Upload an itc_claimed column if credit was not taken in full.")
    if dataset == "purchases" and "booking_date" not in mapped:
        notes.append("No booking date column: time-limit checks use the invoice date.")
    return notes


def import_file(db: Session, engagement: Engagement, dataset: str, filename: str, content: bytes,
                mode: str = "replace", user: str = "") -> ImportBatch:
    ds = DATASETS[dataset]
    if filename.lower().endswith(".xml"):
        if dataset != "ledger":
            raise ValueError("Tally XML is accepted only for the day book / ledger dataset")
        records = parse_tally_xml(content)
        rows, errors = validate_rows(ds, records, first_row=1)
        parsed = {"rows": rows, "errors": errors, "unmapped": [], "rows_read": len(records),
                  "mapped": sorted({k for r in records for k in r})}
    else:
        parsed = parse_file(dataset, filename, content)
    notes = _derive(dataset, parsed["rows"], parsed["mapped"])

    if mode == "replace":
        db.execute(delete(ds.model).where(ds.model.engagement_id == engagement.id))
    batch = ImportBatch(
        engagement_id=engagement.id, dataset=dataset, filename=filename, mode=mode, uploaded_by=user,
        rows_read=parsed["rows_read"], rows_loaded=len(parsed["rows"]), rows_rejected=len(parsed["errors"]),
        errors=parsed["errors"][:MAX_ERRORS_KEPT], unmapped_columns=parsed["unmapped"], notes=notes)
    db.add(batch)
    db.flush()
    if parsed["rows"]:
        columns = {c.name for c in ds.model.__table__.columns}
        payload = [{**{k: v for k, v in r.items() if k in columns}, "engagement_id": engagement.id, "batch_id": batch.id}
                   for r in parsed["rows"]]
        # Rows in one executemany must share keys, so pad the optional ones.
        keys = set().union(*payload)
        db.execute(insert(ds.model), [{k: r.get(k) for k in keys} for r in payload])
    db.commit()
    return batch


def template_xlsx(dataset: str) -> bytes:
    """Blank upload template: headings on row 1, guidance on a second sheet."""
    ds = DATASETS[dataset]
    wb = Workbook()
    ws = wb.active
    ws.title = "Data"
    for i, col in enumerate(ds.cols, start=1):
        cell = ws.cell(row=1, column=i, value=col.name)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="B91C1C" if col.required else "475569")
        ws.column_dimensions[cell.column_letter].width = max(14, len(col.name) + 4)
    guide = wb.create_sheet("Guide")
    guide.append(["Column", "Mandatory", "Type", "Notes"])
    for col in ds.cols:
        choices = " / ".join(sorted(set(col.choices.values()))) if col.choices else ""
        guide.append([col.name, "Yes" if col.required else "", col.kind, col.help or choices])
    for width, letter in zip((22, 11, 9, 90), "ABCD"):
        guide.column_dimensions[letter].width = width
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()
