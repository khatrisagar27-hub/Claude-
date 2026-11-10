import io
from datetime import date

import pandas as pd
import pytest
from sqlalchemy import func, select

from app.ingest.loader import import_file, template_xlsx
from app.ingest.schema import DATASETS
from app.ingest.tabular import parse_file, to_date, to_month, to_number
from app.ingest.tally import parse_tally_xml
from app.models import LedgerEntry, PurchaseInvoice


def csv(text):
    return text.strip().encode()


def test_value_parsing():
    assert to_date("31-03-2026") == to_date("31/03/2026") == to_date("2026-03-31") == to_date("20260331") == date(2026, 3, 31)
    assert to_date("05-04-2025") == date(2025, 4, 5)                      # day first, never month first
    assert to_month("Apr-2025") == to_month("2025-04") == to_month("15-04-2025") == date(2025, 4, 1)
    assert to_number("1,23,456.50") == 123456.5
    assert to_number("₹ 2,500 Dr") == 2500
    assert to_number("(750.25)") == -750.25
    with pytest.raises(ValueError):
        to_date("31-13-2026")
    with pytest.raises(ValueError):
        to_number("twelve")


def test_header_found_below_title_rows_and_aliases_mapped():
    parsed = parse_file("purchases", "p.csv", csv("""
ABC Traders,,,,
Purchase Register 1-Apr-2025 to 31-Mar-2026,,,,
Bill No,Bill Date,Supplier,Taxable Amount,CGST Amount,Remarks
A-1,05-04-2025,Apex,"1,000.00",90,first
A-2,06-04-2025,Apex,2000,180,second
"""))
    assert parsed["rows_read"] == 2 and not parsed["errors"]
    assert parsed["rows"][0] == {"invoice_no": "A-1", "invoice_date": date(2025, 4, 5), "vendor_name": "Apex",
                                 "taxable_value": 1000.0, "cgst": 90.0, "source_row": 4}
    assert parsed["unmapped"] == ["Remarks"]


def test_bad_rows_are_rejected_with_reasons_not_guessed():
    parsed = parse_file("purchases", "p.csv", csv("""
invoice_no,invoice_date,vendor_name,taxable_value,nature
A-1,05-04-2025,Apex,1000,goods
A-2,not a date,Apex,2000,goods
,07-04-2025,Apex,abc,legal
"""))
    assert len(parsed["rows"]) == 1
    assert parsed["errors"][0]["row"] == 3 and "invoice_date" in parsed["errors"][0]["problems"][0]
    problems = " | ".join(parsed["errors"][1]["problems"])
    assert "invoice_no is blank" in problems and "taxable_value 'abc' is not a number" in problems and "nature 'legal' must be one of" in problems


def test_missing_required_column_names_it():
    with pytest.raises(ValueError, match="invoice_date"):
        parse_file("purchases", "p.csv", csv("invoice_no,vendor_name,taxable_value\nA-1,Apex,1000"))


def test_derived_values_are_recorded_as_notes(make_engagement, db):
    eng = make_engagement()
    frame = pd.DataFrame([{"invoice_no": "A-1", "invoice_date": date(2025, 5, 1), "vendor_name": "Apex", "taxable_value": 1000, "cgst": 90, "sgst": 90}])
    out = io.BytesIO()
    frame.to_excel(out, index=False)
    batch = import_file(db, eng, "purchases", "p.xlsx", out.getvalue())
    row = db.scalar(select(PurchaseInvoice).where(PurchaseInvoice.engagement_id == eng.id))
    assert float(row.total) == 1180 and float(row.itc_claimed) == 180
    assert len(batch.notes) == 3 and "ITC claimed assumed" in batch.notes[1]


def test_replace_and_append(make_engagement, db):
    eng = make_engagement()
    data = csv("invoice_no,invoice_date,vendor_name,taxable_value\nA-1,05-04-2025,Apex,1000")
    count = lambda: db.scalar(select(func.count()).select_from(PurchaseInvoice).where(PurchaseInvoice.engagement_id == eng.id))
    import_file(db, eng, "purchases", "p.csv", data)
    import_file(db, eng, "purchases", "p.csv", data, mode="append")
    assert count() == 2
    import_file(db, eng, "purchases", "p.csv", data, mode="replace")
    assert count() == 1


TALLY = b"""<ENVELOPE><BODY><IMPORTDATA><REQUESTDATA><TALLYMESSAGE>
<VOUCHER VCHTYPE="Payment"><DATE>20250512</DATE><VOUCHERNUMBER>17</VOUCHERNUMBER><NARRATION>Paid &#4;cash</NARRATION>
 <ALLLEDGERENTRIES.LIST><LEDGERNAME>Repairs</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>-15000.00</AMOUNT></ALLLEDGERENTRIES.LIST>
 <ALLLEDGERENTRIES.LIST><LEDGERNAME>Cash</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>15000.00</AMOUNT></ALLLEDGERENTRIES.LIST>
</VOUCHER></TALLYMESSAGE></REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""


def test_tally_xml_negative_amount_is_a_debit(make_engagement, db):
    records = parse_tally_xml(TALLY)
    assert [(r["ledger"], r["debit"], r["credit"]) for r in records] == [("Repairs", 15000.0, 0.0), ("Cash", 0.0, 15000.0)]
    eng = make_engagement()
    batch = import_file(db, eng, "ledger", "daybook.xml", TALLY)
    assert batch.rows_loaded == 2 and batch.rows_rejected == 0
    row = db.scalars(select(LedgerEntry).where(LedgerEntry.engagement_id == eng.id)).first()
    assert row.voucher_type == "payment" and row.voucher_date == date(2025, 5, 12) and row.narration == "Paid cash"


def test_tally_xml_rejects_entity_declarations():
    with pytest.raises(ValueError, match="DOCTYPE"):
        parse_tally_xml(b'<!DOCTYPE x [<!ENTITY a "b">]><ENVELOPE/>')
    with pytest.raises(ValueError, match="No vouchers"):
        parse_tally_xml(b"<ENVELOPE></ENVELOPE>")


@pytest.mark.parametrize("dataset", list(DATASETS))
def test_template_round_trips_through_the_parser(dataset):
    """The blank template we hand out must be accepted by our own importer."""
    parsed = parse_file(dataset, "t.xlsx", template_xlsx(dataset))
    assert parsed["rows"] == [] and parsed["unmapped"] == []
    assert set(parsed["mapped"]) == {c.name for c in DATASETS[dataset].cols}
