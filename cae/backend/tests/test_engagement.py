"""Statutory / Internal engagements, period scoping, full populations, importer and Tally parsing."""
from datetime import date
from types import SimpleNamespace

import pytest

from app.rules import get_rule_fn
from app.rules.catalogue import RULE_CATALOGUE
from app.statutory import reporting
from tests.conftest import CID, build_conn, rule


def _eng(audit_type="statutory", caro=True, ifc=False, tax=True, fy=2024):
    return SimpleNamespace(audit_type=audit_type, caro_applicable=caro, ifc_applicable=ifc,
                           tax_audit_applicable=tax, financial_year=fy)


def run(code, conn, **params):
    return get_rule_fn(code)(conn, CID, rule(**params))


# ---------------------------------------------------------------- reporting map
def test_every_catalogue_rule_is_mapped_for_both_audit_types():
    codes = {row[0] for row in RULE_CATALOGUE}
    assert codes == set(reporting.RULE_MAP)
    for code, m in reporting.RULE_MAP.items():
        assert m["process"] in reporting.PROCESSES, code
        assert m["scope"] in ("statutory", "ifc", "internal"), code
        for frame, ref, _ in m["refs"]:
            assert frame in ("CARO", "3CD", "IFC", "SA"), code
            if frame == "CARO":
                assert ref in reporting.CARO_2020, (code, ref)
            if frame == "3CD":
                assert ref in reporting.FORM_3CD, (code, ref)
        if m["scope"] == "ifc":
            assert any(f == "IFC" for f, *_ in m["refs"]), code


def test_statutory_scope_follows_ifc_applicability_internal_takes_all():
    assert reporting.in_scope("TRE-001", _eng())              # tax audit cl.21(d)
    assert not reporting.in_scope("SAL-019", _eng())          # weekend invoicing: internal only
    assert not reporting.in_scope("PUR-004", _eng(ifc=False))  # control test without IFC reporting
    assert reporting.in_scope("PUR-004", _eng(ifc=True))
    assert all(reporting.in_scope(c, _eng("internal")) for c in reporting.RULE_MAP)
    assert all(reporting.in_scope(c, None) for c in reporting.RULE_MAP)


def test_refs_only_for_frames_that_apply():
    refs = reporting.refs_for("PAY-005", _eng(caro=False, tax=True))
    assert [r["frame"] for r in refs] == ["Form 3CD (Income-tax Act, 1961)"] and refs[0]["ref"] == "cl. 20(b)"
    refs = reporting.refs_for("PAY-005", _eng(caro=True, tax=False))
    assert [(r["frame"], r["ref"]) for r in refs] == [("CARO 2020", "3(vii)(a)")]
    assert reporting.refs_for("TRE-001", _eng(fy=2026))[0]["frame"].startswith("Tax audit report (Income-tax Act, 2025)")
    assert reporting.refs_for("SAL-019", _eng("internal")) == [{"frame": "Process", "ref": "Order to Cash", "note": ""}]


# ---------------------------------------------------------------- period scoping
def test_transaction_rules_see_only_the_period():
    conn = build_conn(period_from=date(2024, 4, 1), period_to=date(2025, 3, 31), sales_invoices=[
        {"invoice_number": "A", "invoice_date": date(2024, 3, 15), "total_amount": 200000.0},   # before the period
        {"invoice_number": "B", "invoice_date": date(2024, 6, 15), "total_amount": 300000.0},
    ])
    assert [e["evidence"]["invoice_number"] for e in run("SAL-002", conn)] == ["B"]


def test_duplicate_number_across_period_start_is_reported_once_from_inside():
    rows = [{"invoice_number": "X1", "invoice_date": date(2024, 4, 10), "total_amount": 100.0},
            {"invoice_number": "X1", "invoice_date": date(2024, 9, 10), "total_amount": 100.0},
            {"invoice_number": "Y1", "invoice_date": date(2024, 4, 5), "total_amount": 100.0},
            {"invoice_number": "Y1", "invoice_date": date(2024, 5, 5), "total_amount": 100.0}]
    conn = build_conn(period_from=date(2024, 7, 1), period_to=date(2024, 9, 30), sales_invoices=rows)
    out = run("SAL-001", conn)
    assert [e["evidence"]["invoice_number"] for e in out] == ["X1"]      # Y1 lies wholly before Q2
    assert out[0]["evidence"]["financial_year"] == "2024-25" and out[0]["evidence"]["count"] == 2


def test_msme_dues_at_period_end_include_older_unpaid_bills():
    conn = build_conn(period_from=date(2024, 10, 1), period_to=date(2024, 12, 31),
                      vendors=[{"id": "V1", "name": "Small Co", "msme_status": "Small"}],
                      purchase_invoices=[{"vendor_id": "V1", "invoice_number": "OLD", "invoice_date": date(2024, 5, 1),
                                          "total_amount": 100000.0, "outstanding_amount": 100000.0}])
    out = run("PUR-031", conn, as_on="2024-12-31")
    assert [e["evidence"]["invoice_number"] for e in out] == ["OLD"]


def test_results_are_never_silently_capped():
    rows = [{"invoice_number": f"R{i}", "invoice_date": date(2024, 6, 1), "total_amount": 100000.0 + i * 1000}
            for i in range(80)]
    conn = build_conn(sales_invoices=rows)
    assert len(run("SAL-002", conn)) == 80
    assert len(get_rule_fn("SAL-002")(conn, CID, rule(max_results=10))) == 80   # SQL rules ignore it (no LIMIT)
    from app.rules import capped
    assert len(capped(list(range(80)), rule(max_results=10))) == 10 and len(capped(list(range(80)), rule())) == 80


def test_eway_bill_rule_skips_services_invoices_from_tally():
    conn = build_conn(sales_invoices=[
        {"invoice_number": "S1", "invoice_date": date(2024, 6, 1), "total_amount": 90000.0, "e_way_bill_number": None,
         "raw_data": '{"has_inventory": false}'},
        {"invoice_number": "G1", "invoice_date": date(2024, 6, 1), "total_amount": 90000.0, "e_way_bill_number": None,
         "raw_data": '{"has_inventory": true}'},
    ])
    assert [e["evidence"]["invoice_number"] for e in run("SAL-007", conn)] == ["G1"]


def test_weekend_invoice_and_negative_stock_carry_an_amount():
    conn = build_conn(sales_invoices=[{"invoice_number": "W", "invoice_date": date(2024, 6, 8), "total_amount": 600000.0}],
                      inventory_movements=[
                          {"item_code": "M1", "movement_date": date(2024, 6, 1), "movement_type": "goods_receipt",
                           "quantity": 5.0, "unit_cost": 100.0, "total_value": 500.0},
                          {"item_code": "M1", "movement_date": date(2024, 6, 2), "movement_type": "goods_issue",
                           "quantity": 8.0, "unit_cost": 100.0, "total_value": 800.0}])
    assert run("SAL-019", conn)[0]["financial_impact"] == 600000.0
    assert run("INV-001", conn)[0]["financial_impact"] == 300.0


def test_je_011_names_the_poster_not_a_uuid():
    jes = [{"voucher_number": f"J{i}", "entry_date": date(2024, 6, 1), "total_debit": 600000.0, "total_credit": 600000.0,
            "posted_by_user_id": "U1"} for i in range(11)]
    conn = build_conn(journal_entries=jes, users=[{"id": "U1", "full_name": "Asha Mehta"}])
    out = run("JE-011", conn)
    assert out and "Asha Mehta" in out[0]["title"]


# ---------------------------------------------------------------- statutory helpers
def test_msme_interest_stops_at_as_on_when_paid_later():
    from app.statutory import msme
    calc = msme.bill_interest(100000, date(2024, 1, 1), date(2025, 6, 30), date(2025, 3, 31))
    assert calc["end_date"] == "2025-03-31"


def test_wc_stress_reads_overdue_receivables_not_only_ccc():
    from app.engines.wc_engine import WorkingCapitalEngine
    ar = {"total": 100.0, "overdue": 92.0, "aging": {"d90_plus": 78.0}}
    ap = {"total": 100.0, "overdue": 93.0}
    score, parts = WorkingCapitalEngine._stress_score(ar, ap, dso=331, ccc=-1.4)
    assert 70 < score < 80 and parts["ccc_vs_180"] == 0.0


# ---------------------------------------------------------------- importer
def test_importer_maps_source_headers_and_reads_indian_dates():
    from app.connectors.excel_importer import ExcelImporter, map_columns
    cols = ["Invoice No", "Invoice Date", "Customer Name", "Taxable Value", "CGST", "SGST", "IGST", "Total Amount"]
    m = map_columns(cols, "sales_invoices")
    assert m["invoice_number"] == "Invoice No" and m["invoice_date"] == "Invoice Date" and m["customer_id"] == "Customer Name"
    assert ExcelImporter._parse_date("15-11-2024") == date(2024, 11, 15)
    assert ExcelImporter._parse_date("2024-11-05") == date(2024, 11, 5)
    assert ExcelImporter._parse_date(None) is None
    with pytest.raises(ValueError):
        ExcelImporter._parse_date("not a date", required=True)
    assert str(ExcelImporter._decimal(float("nan"))) == "0"


# ---------------------------------------------------------------- Tally parsing
_SALES_XML = """<ENVELOPE><BODY><DATA><COLLECTION>
<VOUCHER REMOTEID="g-1" VCHTYPE="GST Sales"><DATE>20240615</DATE><VOUCHERTYPENAME>GST Sales</VOUCHERTYPENAME>
<VOUCHERNUMBER>INV/1</VOUCHERNUMBER><PARTYLEDGERNAME>Acme Ltd</PARTYLEDGERNAME><ISCANCELLED>No</ISCANCELLED>
<IRNACKNO>112410001</IRNACKNO>
<ALLLEDGERENTRIES.LIST><LEDGERNAME>Acme Ltd</LEDGERNAME><ISPARTYLEDGER>Yes</ISPARTYLEDGER><AMOUNT>-118000.00</AMOUNT>
<BILLALLOCATIONS.LIST><NAME>INV/1</NAME><BILLTYPE>New Ref</BILLTYPE><AMOUNT>-118000.00</AMOUNT><BILLCREDITPERIOD>30 Days</BILLCREDITPERIOD></BILLALLOCATIONS.LIST>
</ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST><LEDGERNAME>Sales @18%</LEDGERNAME><AMOUNT>100000.00</AMOUNT></ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST><LEDGERNAME>Output CGST</LEDGERNAME><AMOUNT>9000.00</AMOUNT></ALLLEDGERENTRIES.LIST>
<ALLLEDGERENTRIES.LIST><LEDGERNAME>Output SGST</LEDGERNAME><AMOUNT>9000.00</AMOUNT></ALLLEDGERENTRIES.LIST>
<LEDGERENTRIES.LIST><LEDGERNAME>Acme Ltd</LEDGERNAME><AMOUNT>-118000.00</AMOUNT></LEDGERENTRIES.LIST>
<ALLINVENTORYENTRIES.LIST><STOCKITEMNAME>Pipe</STOCKITEMNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
<ACTUALQTY>10.000 Nos</ACTUALQTY><RATE>10000.00/Nos</RATE><AMOUNT>100000.00</AMOUNT></ALLINVENTORYENTRIES.LIST>
</VOUCHER><VOUCHER>0</VOUCHER></COLLECTION></DATA></BODY></ENVELOPE>"""


def test_tally_voucher_takes_one_ledger_list_and_reads_bills_stock_irn():
    import xml.etree.ElementTree as ET
    from app.connectors import tally_live as tl
    root = ET.fromstring(tl.clean(_SALES_XML))
    vouchers = [tl._parse_voucher(v, {"GST Sales": "Sales"}) for v in root.iter("VOUCHER") if len(v)]
    assert len(vouchers) == 1
    v = vouchers[0]
    assert v["parent"] == "Sales" and v["in_books"] and v["irn"] == "112410001"
    cancelled = tl._parse_voucher(ET.fromstring(tl.clean(_SALES_XML.replace("<ISCANCELLED>No", '<ISCANCELLED TYPE="Logical">Yes'))).find(".//VOUCHER"), {"GST Sales": "Sales"})
    assert not cancelled["in_books"] and cancelled["excluded"] == "cancelled"
    assert len(v["lines"]) == 4 and sum(ln["amount"] for ln in v["lines"]) == 0      # not doubled
    assert v["lines"][0]["bills"][0] == {"ref": "INV/1", "type": "New Ref", "amount": -118000.0, "credit_days": 30}
    assert v["stock"] == [{"item": "Pipe", "qty": 10.0, "unit": "Nos", "rate": 10000.0, "amount": 100000.0,
                           "inward": False, "godown": ""}]


def test_tally_group_class_and_months():
    from app.connectors import tally_live as tl
    groups = {"Debtors - Gujarat": ("", "Sundry Debtors"), "Sundry Debtors": ("Sundry Debtors", "Current Assets"),
              "Current Assets": ("Current Assets", "Primary"), "My Debtors": ("Sundry Debtors", "Current Assets")}
    assert tl._group_class("Debtors - Gujarat", groups) == "Sundry Debtors"
    assert tl._group_class("My Debtors", groups) == "Sundry Debtors"           # renamed predefined group
    assert list(tl.months(date(2024, 4, 15), date(2024, 6, 10))) == [
        (date(2024, 4, 15), date(2024, 4, 30)), (date(2024, 5, 1), date(2024, 5, 31)), (date(2024, 6, 1), date(2024, 6, 10))]
    assert "xmlns:UDF" in tl.clean("<ENVELOPE>&#4;<A/></ENVELOPE>") and "&#4;" not in tl.clean("<ENVELOPE>&#4;</ENVELOPE>")


def test_report_amounts_use_indian_grouping():
    from app.utils.engagement_export import inr
    assert inr(2500000, "Rs.") == "Rs.25,00,000" and inr(123456789, "Rs.") == "Rs.12,34,56,789"
    assert inr(999, "Rs.") == "Rs.999" and inr(-1234567, "Rs.") == "-Rs.12,34,567" and inr(None) == "\u2014"
