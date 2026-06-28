"""Tests for TallyConnector — parsing Tally XML voucher exports into journal entries.

Regression note: the connector previously constructed JournalEntry with field
names that do not exist on the model (je_no/je_date/period/je_type/source_system)
and omitted the required total_credit, so every voucher raised and nothing was
imported. It now maps to the real columns (voucher_number/entry_date/
voucher_type/erp_source) and computes total_credit.
"""
from datetime import date

import pytest

from app.connectors.tally_connector import TallyConnector
from app.models.transaction import JournalEntry
from tests.factories import COMPANY_ID

ONE_VOUCHER = b"""<ENVELOPE>
  <BODY><DATA>
    <VOUCHER>
      <DATE>20240315</DATE>
      <VOUCHERNUMBER>JV-100</VOUCHERNUMBER>
      <VOUCHERTYPE>Payment</VOUCHERTYPE>
      <NARRATION>Vendor payment</NARRATION>
      <ALLLEDGERENTRIES.LIST><AMOUNT>1000.00</AMOUNT></ALLLEDGERENTRIES.LIST>
      <ALLLEDGERENTRIES.LIST><AMOUNT>-1000.00</AMOUNT></ALLLEDGERENTRIES.LIST>
    </VOUCHER>
  </DATA></BODY>
</ENVELOPE>"""


def _connector(db):
    return TallyConnector(db, str(COMPANY_ID))


def test_import_xml_creates_journal_entry_with_mapped_fields(db):
    result = _connector(db).import_xml(ONE_VOUCHER)

    assert result["journal_entries"] == 1
    assert result["errors"] == []

    je = db.query(JournalEntry).one()
    assert je.voucher_number == "JV-100"
    assert je.entry_date == date(2024, 3, 15)
    assert je.voucher_type == "payment"          # lower-cased
    assert je.narration == "Vendor payment"
    assert je.erp_source == "tally"
    assert je.company_id == COMPANY_ID


def test_total_debit_and_credit_are_split_by_sign(db):
    _connector(db).import_xml(ONE_VOUCHER)

    je = db.query(JournalEntry).one()
    assert float(je.total_debit) == 1000.0
    assert float(je.total_credit) == 1000.0


def test_amounts_with_thousands_separators_are_parsed(db):
    xml = b"""<ENVELOPE><VOUCHER>
      <DATE>20240401</DATE><VOUCHERNUMBER>JV-2</VOUCHERNUMBER>
      <VOUCHERTYPE>Journal</VOUCHERTYPE>
      <ALLLEDGERENTRIES.LIST><AMOUNT>1,50,000.00</AMOUNT></ALLLEDGERENTRIES.LIST>
    </VOUCHER></ENVELOPE>"""

    _connector(db).import_xml(xml)

    je = db.query(JournalEntry).one()
    assert float(je.total_debit) == 150000.0


def test_multiple_vouchers_are_counted(db):
    xml = b"""<ENVELOPE>
      <VOUCHER><DATE>20240101</DATE><VOUCHERNUMBER>A</VOUCHERNUMBER>
        <VOUCHERTYPE>Journal</VOUCHERTYPE>
        <ALLLEDGERENTRIES.LIST><AMOUNT>100</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER>
      <VOUCHER><DATE>20240102</DATE><VOUCHERNUMBER>B</VOUCHERNUMBER>
        <VOUCHERTYPE>Journal</VOUCHERTYPE>
        <ALLLEDGERENTRIES.LIST><AMOUNT>200</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER>
    </ENVELOPE>"""

    result = _connector(db).import_xml(xml)

    assert result["journal_entries"] == 2
    assert db.query(JournalEntry).count() == 2


def test_missing_date_defaults_to_today(db):
    xml = b"""<ENVELOPE><VOUCHER>
      <VOUCHERNUMBER>JV-NODATE</VOUCHERNUMBER><VOUCHERTYPE>Journal</VOUCHERTYPE>
      <ALLLEDGERENTRIES.LIST><AMOUNT>100</AMOUNT></ALLLEDGERENTRIES.LIST>
    </VOUCHER></ENVELOPE>"""

    _connector(db).import_xml(xml)

    je = db.query(JournalEntry).one()
    assert je.entry_date == date.today()
