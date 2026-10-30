"""GST reconciliation engine — books vs GSTR-2B (ITC) and GSTR-1 (outward supplies).

Invoice-level when the GSTR-2B rows are supplied (portal Excel/CSV, or JSON with an
"invoices" list): matching is deterministic, see gst_match. Summary-level otherwise.

Risk = ITC at risk (booked but not in 2B, or booked above the 2B figure) plus, when
GSTR-1 figures are supplied, the gap between output tax in the books and in GSTR-1.
No tax rate is assumed — the old 18%-of-turnover-variance shortcut is gone.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from app.engines import gst_match

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DETAIL_ROW_CAP = 500


class GSTEngine:
    def __init__(self, db: "Session", company_id: str):
        self.db = db
        self.company_id = uuid.UUID(company_id)

    def _period_bounds(self, period: str) -> tuple[date, date]:
        year, month = int(period[:4]), int(period[5:7])
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        return start, end

    def books_purchases(self, period: str) -> list[dict]:
        from app.models.master import Vendor
        from app.models.transaction import PurchaseInvoice

        start, end = self._period_bounds(period)
        rows = (
            self.db.query(PurchaseInvoice, Vendor.gstin, Vendor.name)
            .outerjoin(Vendor, Vendor.id == PurchaseInvoice.vendor_id)
            .filter(
                PurchaseInvoice.company_id == self.company_id,
                PurchaseInvoice.invoice_date >= start,
                PurchaseInvoice.invoice_date < end,
                PurchaseInvoice.itc_eligible.is_(True),
                PurchaseInvoice.status != "cancelled",
            )
            .all()
        )
        return [
            gst_match.record(
                p.vendor_gstin or vgstin, p.invoice_number, p.invoice_date, p.taxable_amount,
                float(p.cgst_amount or 0) + float(p.sgst_amount or 0) + float(p.igst_amount or 0) + float(p.cess_amount or 0),
                vname, ref=str(p.id),
            )
            for p, vgstin, vname in rows
        ]

    def books_sales(self, period: str) -> dict:
        from app.models.transaction import SalesInvoice

        start, end = self._period_bounds(period)
        sales = (
            self.db.query(SalesInvoice)
            .filter(
                SalesInvoice.company_id == self.company_id,
                SalesInvoice.invoice_date >= start,
                SalesInvoice.invoice_date < end,
                SalesInvoice.status != "cancelled",
            )
            .all()
        )
        return {
            "turnover": round(sum(float(s.taxable_amount or 0) for s in sales), 2),
            "output_tax": round(sum(float(s.cgst_amount or 0) + float(s.sgst_amount or 0) + float(s.igst_amount or 0)
                                    for s in sales), 2),
        }

    def reconcile(self, period: str, gstr2b_data: dict | None = None, gstr2b_rows: list[dict] | None = None,
                  tolerance: float = 1.0) -> dict:
        from app.models.risk import GSTReconciliation

        gstr2b_data = gstr2b_data or {}
        if gstr2b_rows is None and isinstance(gstr2b_data.get("invoices"), list):
            gstr2b_rows = [
                gst_match.record(r.get("gstin"), r.get("invoice_number"), r.get("invoice_date"),
                                 r.get("taxable_value"), r.get("tax", sum(float(r.get(k) or 0) for k in ("igst", "cgst", "sgst", "cess"))),
                                 r.get("supplier"))
                for r in gstr2b_data["invoices"]
            ]

        books = self.books_purchases(period)
        sales = self.books_sales(period)
        books_itc = round(sum(r["tax"] for r in books), 2)

        details: dict = {"mode": "summary"}
        if gstr2b_rows is not None:
            match = gst_match.reconcile(gstr2b_rows, books, tolerance)
            details = {"mode": "invoice", **{k: [self._jsonable(r) for r in v[:DETAIL_ROW_CAP]]
                                              for k, v in match.items() if isinstance(v, list) and k != "matched"},
                       "summary": match["summary"]}
            gstr2b_itc = match["summary"]["gstr2b_itc"]
            itc_at_risk = match["summary"]["itc_at_risk"]
        else:
            gstr2b_itc = float(gstr2b_data.get("itc_available", 0) or 0)
            itc_at_risk = round(max(books_itc - gstr2b_itc, 0), 2) if "itc_available" in gstr2b_data else 0.0

        gstr1_turnover = gstr2b_data.get("gstr1_turnover", gstr2b_data.get("turnover"))
        gstr1_tax = gstr2b_data.get("gstr1_tax")
        variance_turnover = abs(float(gstr1_turnover) - sales["turnover"]) if gstr1_turnover is not None else None
        output_tax_gap = abs(float(gstr1_tax) - sales["output_tax"]) if gstr1_tax is not None else 0.0
        gstr3b_itc = gstr2b_data.get("itc_claimed")
        risk_amount = round(itc_at_risk + output_tax_gap, 2)
        details.update({"books_output_tax": sales["output_tax"], "gstr1_tax": gstr1_tax, "output_tax_gap": output_tax_gap,
                        "itc_at_risk": itc_at_risk})

        values = dict(
            gstr1_turnover=gstr1_turnover, books_turnover=sales["turnover"], gstr3b_itc=gstr3b_itc,
            books_itc=books_itc, gstr2b_itc=gstr2b_itc, variance_turnover=variance_turnover,
            variance_itc=round(books_itc - gstr2b_itc, 2), risk_amount=risk_amount,
            risk_category="itc_at_risk" if itc_at_risk else ("output_tax_gap" if output_tax_gap else None),
            status="reconciled", details_json=details,
        )
        existing = (
            self.db.query(GSTReconciliation)
            .filter(GSTReconciliation.company_id == self.company_id, GSTReconciliation.period == period)
            .first()
        )
        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
        else:
            self.db.add(GSTReconciliation(id=uuid.uuid4(), company_id=self.company_id, period=period, **values))
        self.db.commit()
        return {"period": period, **{k: v for k, v in values.items() if k != "details_json"},
                "summary": details.get("summary"), "mode": details["mode"]}

    @staticmethod
    def _jsonable(r: dict) -> dict:
        return {k: (v.isoformat() if isinstance(v, date) else v) for k, v in r.items()}
