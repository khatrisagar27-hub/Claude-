"""Tally XML export parser — imports ledger and voucher data."""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class TallyConnector:
    def __init__(self, db: "Session", company_id: str):
        self.db = db
        self.company_id = uuid.UUID(company_id)

    def import_xml(self, xml_content: bytes) -> dict:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_content)
        results = {"journal_entries": 0, "errors": []}
        for voucher in root.iter("VOUCHER"):
            try:
                self._import_voucher(voucher)
                results["journal_entries"] += 1
            except Exception as e:
                results["errors"].append(str(e))
        self.db.commit()
        return results

    def _import_voucher(self, v):
        import xml.etree.ElementTree as ET
        from datetime import datetime
        from app.models.transaction import JournalEntry

        date_str = v.findtext("DATE", "")
        je_date = datetime.strptime(date_str, "%Y%m%d") if date_str else datetime.utcnow()

        total_debit = Decimal("0")
        total_credit = Decimal("0")
        for line in v.findall(".//ALLLEDGERENTRIES.LIST"):
            amt_text = line.findtext("AMOUNT", "0").replace(",", "")
            amt = Decimal(amt_text) if amt_text else Decimal("0")
            if amt > 0:
                total_debit += amt
            elif amt < 0:
                total_credit += -amt

        je = JournalEntry(
            id=uuid.uuid4(),
            company_id=self.company_id,
            voucher_number=v.findtext("VOUCHERNUMBER", str(uuid.uuid4())[:8]),
            entry_date=je_date.date(),
            voucher_type=v.findtext("VOUCHERTYPE", "manual").lower(),
            narration=v.findtext("NARRATION"),
            total_debit=total_debit,
            total_credit=total_credit,
            erp_source="tally",
        )
        self.db.add(je)
