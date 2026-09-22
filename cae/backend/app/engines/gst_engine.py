"""GST reconciliation engine — GSTR-1/3B/2B vs books."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def parse_gstr2b(data: dict) -> dict:
    """Extract ITC available (and optional return figures) from an uploaded GSTR-2B.

    Accepts either the portal's GSTR-2B JSON (``data.docdata`` with ``b2b`` invoices,
    ``cdnr`` notes and ``impg`` imports; entries with ``itcavl = "N"`` excluded, credit
    notes deducted) or a summary ``{"itc_available": ..., "turnover": ..., "itc_claimed": ...}``.
    Raises ValueError when neither shape is present, so a wrong file can never be
    read as "zero ITC available". Amendment sections (b2ba, cdnra) are not applied.
    """
    if not isinstance(data, dict):
        raise ValueError("GSTR-2B upload must be a JSON object")
    inner = data["data"] if isinstance(data.get("data"), dict) else data
    doc = inner.get("docdata")
    out = {"turnover": data.get("turnover"), "itc_claimed": data.get("itc_claimed")}

    if doc is not None:
        def tax(x):
            return sum(float(x.get(k) or 0) for k in ("igst", "cgst", "sgst", "cess"))
        itc = 0.0
        for sup in doc.get("b2b", []):
            itc += sum(tax(inv) for inv in sup.get("inv", []) if inv.get("itcavl", "Y") != "N")
        for sup in doc.get("cdnr", []):
            for nt in sup.get("nt", []):
                if nt.get("itcavl", "Y") != "N":
                    itc += -tax(nt) if nt.get("typ") == "C" else tax(nt)
        itc += sum(tax(b) for b in doc.get("impg", []))
        out["itc_available"] = round(itc, 2)
        return out
    if "itc_available" in data:
        out["itc_available"] = float(data["itc_available"])
        return out
    raise ValueError("Unrecognised GSTR-2B file: expected portal JSON (data.docdata) or an itc_available figure")


class GSTEngine:
    def __init__(self, db: "Session", company_id: str):
        self.db = db
        self.company_id = uuid.UUID(company_id)

    def reconcile(self, period: str, gstr2b_data: dict) -> dict:
        from app.models.risk import GSTReconciliation
        from app.models.transaction import SalesInvoice, PurchaseInvoice

        year, month = int(period[:4]), int(period[5:7])

        sales = (
            self.db.query(SalesInvoice)
            .filter(
                SalesInvoice.company_id == self.company_id,
                SalesInvoice.invoice_date >= datetime(year, month, 1),
                SalesInvoice.invoice_date < self._next_month(year, month),
                SalesInvoice.status != "cancelled",
            )
            .all()
        )

        books_turnover = sum(float(s.taxable_amount or 0) for s in sales)
        books_output_cgst = sum(float(s.cgst_amount or 0) for s in sales)

        purchases = (
            self.db.query(PurchaseInvoice)
            .filter(
                PurchaseInvoice.company_id == self.company_id,
                PurchaseInvoice.invoice_date >= datetime(year, month, 1),
                PurchaseInvoice.invoice_date < self._next_month(year, month),
                PurchaseInvoice.itc_eligible == True,
            )
            .all()
        )
        books_itc = sum(
            float(p.cgst_amount or 0) + float(p.sgst_amount or 0) + float(p.igst_amount or 0)
            for p in purchases
        )

        parsed = parse_gstr2b(gstr2b_data)
        gstr2b_itc = parsed["itc_available"]
        # Return figures not supplied stay unknown rather than defaulting to books,
        # which would report a false "no variance".
        gstr1_turnover = float(parsed["turnover"]) if parsed["turnover"] is not None else None
        gstr3b_itc = float(parsed["itc_claimed"]) if parsed["itc_claimed"] is not None else None

        variance_turnover = abs(gstr1_turnover - books_turnover) if gstr1_turnover is not None else None
        variance_itc = abs(books_itc - gstr2b_itc)

        # ITC at risk = ITC in books not reflected in GSTR-2B (s.16(2)(aa) CGST Act).
        # A turnover gap is reported as a variance only: the tax on it depends on the
        # rates of the supplies involved, which this reconciliation does not know.
        risk_amount = round(max(books_itc - gstr2b_itc, 0.0), 2)

        existing = (
            self.db.query(GSTReconciliation)
            .filter(GSTReconciliation.company_id == self.company_id, GSTReconciliation.period == period)
            .first()
        )

        if existing:
            existing.gstr1_turnover = gstr1_turnover
            existing.books_turnover = books_turnover
            existing.gstr3b_itc = gstr3b_itc
            existing.books_itc = books_itc
            existing.gstr2b_itc = gstr2b_itc
            existing.variance_turnover = variance_turnover
            existing.variance_itc = variance_itc
            existing.risk_amount = risk_amount
            existing.status = "reconciled"
        else:
            recon = GSTReconciliation(
                id=uuid.uuid4(),
                company_id=self.company_id,
                period=period,
                gstr1_turnover=gstr1_turnover,
                books_turnover=books_turnover,
                gstr3b_itc=gstr3b_itc,
                books_itc=books_itc,
                gstr2b_itc=gstr2b_itc,
                variance_turnover=variance_turnover,
                variance_itc=variance_itc,
                risk_amount=risk_amount,
                status="reconciled",
            )
            self.db.add(recon)

        self.db.commit()
        return {
            "period": period,
            "books_turnover": books_turnover,
            "gstr1_turnover": gstr1_turnover,
            "variance_turnover": variance_turnover,
            "books_itc": books_itc,
            "gstr2b_itc": gstr2b_itc,
            "variance_itc": variance_itc,
            "risk_amount": risk_amount,
        }

    @staticmethod
    def _next_month(year: int, month: int) -> datetime:
        if month == 12:
            return datetime(year + 1, 1, 1)
        return datetime(year, month + 1, 1)
