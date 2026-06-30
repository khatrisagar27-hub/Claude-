"""GST reconciliation engine — GSTR-1/3B/2B vs books."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


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

        gstr1_turnover = float(gstr2b_data.get("turnover", books_turnover))
        gstr2b_itc = float(gstr2b_data.get("itc_available", 0))
        gstr3b_itc = float(gstr2b_data.get("itc_claimed", books_itc))

        variance_turnover = abs(gstr1_turnover - books_turnover)
        variance_itc = abs(books_itc - gstr2b_itc)

        risk_amount = variance_turnover * 0.18 + variance_itc

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
