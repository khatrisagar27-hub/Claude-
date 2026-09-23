"""Working capital engine — aging, stress score, DSO/DPO/DIO/CCC.

Notes on methodology:
  * Metrics are computed "as of" a *reference date* = the latest invoice date
    that carries an actual amount. This is how auditors age receivables
    (against the last data / period-end date) rather than the wall-clock
    date, and it keeps the view meaningful when the books are not perfectly
    current.
  * When an invoice has no explicit due date, a standard Net-30 credit
    period is assumed (invoice_date + 30 days).
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DEFAULT_CREDIT_DAYS = 30


class WorkingCapitalEngine:
    def __init__(self, db: "Session", company_id: str):
        self.db = db
        self.company_id = uuid.UUID(company_id)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def compute_and_store(self) -> dict:
        """Compute metrics and upsert today's WorkingCapitalMetric row."""
        from app.models.risk import WorkingCapitalMetric
        metrics = self._compute_metrics()

        today = date.today()
        existing = (
            self.db.query(WorkingCapitalMetric)
            .filter(
                WorkingCapitalMetric.company_id == self.company_id,
                WorkingCapitalMetric.metric_date == today,
            )
            .first()
        )
        aging = metrics["receivables_aging"]
        model_data = {
            "receivables_total": metrics["receivables_total"],
            "receivables_overdue": metrics["receivables_overdue"],
            "receivables_0_30": aging["d0_30"],
            "receivables_31_60": aging["d31_60"],
            "receivables_61_90": aging["d61_90"],
            "receivables_above_90": aging["d90_plus"],
            "payables_total": metrics["payables_total"],
            "payables_overdue": metrics["payables_overdue"],
            "inventory_value": metrics["inventory_value"],
            "wc_stress_score": metrics["wc_stress_score"],
            "dso": metrics["dso"],
            "dpo": metrics["dpo"],
            "dio": metrics["dio"],
        }
        if existing:
            for k, v in model_data.items():
                setattr(existing, k, v)
        else:
            wc = WorkingCapitalMetric(
                id=uuid.uuid4(),
                company_id=self.company_id,
                metric_date=today,
                **model_data,
            )
            self.db.add(wc)
        self.db.commit()
        return metrics

    def compute_full(self) -> dict:
        """Live computation with aging breakdown and top overdue receivables."""
        metrics = self._compute_metrics()
        metrics["company_id"] = str(self.company_id)
        return metrics

    # ------------------------------------------------------------------ #
    # Core computation
    # ------------------------------------------------------------------ #
    def _compute_metrics(self) -> dict:
        from app.models.transaction import SalesInvoice, PurchaseInvoice
        from sqlalchemy import func

        ref_date = self._reference_date()
        window_start = ref_date - timedelta(days=365)

        # --- Sales velocity (trailing 12 months) ---
        annual_sales = self.db.query(func.sum(SalesInvoice.total_amount)).filter(
            SalesInvoice.company_id == self.company_id,
            SalesInvoice.invoice_date >= window_start,
            SalesInvoice.invoice_date <= ref_date,
            SalesInvoice.status != "cancelled",
        ).scalar() or 0
        avg_daily_sales = float(annual_sales) / 365

        # --- Receivables: aging, totals, overdue, top overdue ---
        ar = self._receivables_breakdown(ref_date)

        dso = ar["total"] / avg_daily_sales if avg_daily_sales > 0 else 0

        # --- Purchase velocity (trailing 12 months) ---
        annual_purchases = self.db.query(func.sum(PurchaseInvoice.total_amount)).filter(
            PurchaseInvoice.company_id == self.company_id,
            PurchaseInvoice.invoice_date >= window_start,
            PurchaseInvoice.invoice_date <= ref_date,
            PurchaseInvoice.status != "cancelled",
        ).scalar() or 0
        avg_daily_purchases = float(annual_purchases) / 365

        ap = self._payables_breakdown(ref_date)
        dpo = ap["total"] / avg_daily_purchases if avg_daily_purchases > 0 else 0

        # --- Inventory on-hand ---
        inventory_value = self._inventory_value(ref_date)
        dio = inventory_value / avg_daily_sales if avg_daily_sales > 0 else 0

        # --- Cash conversion cycle + stress score ---
        ccc = dso + dio - dpo
        stress_score = min(100.0, max(0.0, (ccc / 180) * 100))

        return {
            "as_of": ref_date.isoformat(),
            "dso": round(dso, 1),
            "dpo": round(dpo, 1),
            "dio": round(dio, 1),
            "ccc": round(ccc, 1),
            "stress_score": round(stress_score, 1),
            "wc_stress_score": round(stress_score, 1),  # alias for stored model
            "receivables_total": round(ar["total"], 2),
            "receivables_overdue": round(ar["overdue"], 2),
            "payables_total": round(ap["total"], 2),
            "payables_overdue": round(ap["overdue"], 2),
            "inventory_value": round(inventory_value, 2),
            "avg_daily_sales": round(avg_daily_sales, 2),
            "receivables_aging": {k: round(v, 2) for k, v in ar["aging"].items()},
            "top_overdue_receivables": ar["top_overdue"],
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _reference_date(self) -> date:
        """Latest invoice date carrying an actual amount (the 'as of' date)."""
        from app.models.transaction import SalesInvoice
        from sqlalchemy import func

        ref = (
            self.db.query(func.max(SalesInvoice.invoice_date))
            .filter(
                SalesInvoice.company_id == self.company_id,
                SalesInvoice.total_amount > 0,
                SalesInvoice.status != "cancelled",
            )
            .scalar()
        )
        return ref or date.today()

    @staticmethod
    def _effective_due(invoice) -> date:
        return invoice.due_date or (invoice.invoice_date + timedelta(days=DEFAULT_CREDIT_DAYS))

    def _inventory_value(self, ref_date: date) -> float:
        """Closing inventory on-hand value derived from the movement ledger.

        Stock-on-hand is not stored directly, so we net signed movements per
        item (receipts/opening/adjustments add, issues subtract; internal
        transfers are excluded) and floor each item at zero. This avoids the
        nonsensical figure produced by summing gross movement value.
        """
        from app.models.transaction import InventoryMovement
        from sqlalchemy import func, case

        signed = case(
            (InventoryMovement.movement_type == "goods_issue", -InventoryMovement.total_value),
            (InventoryMovement.movement_type == "transfer", 0),
            else_=InventoryMovement.total_value,
        )
        per_item = (
            self.db.query(func.sum(signed).label("net"))
            .filter(
                InventoryMovement.company_id == self.company_id,
                InventoryMovement.movement_date <= ref_date,
            )
            .group_by(InventoryMovement.item_code)
            .subquery()
        )
        value = self.db.query(func.sum(func.greatest(per_item.c.net, 0))).scalar() or 0
        return float(value)

    def _receivables_breakdown(self, ref_date: date) -> dict:
        """Aging buckets, totals, overdue and top overdue from outstanding AR."""
        from app.models.transaction import SalesInvoice
        from app.models.master import Customer

        rows = (
            self.db.query(SalesInvoice, Customer.name)
            .outerjoin(Customer, SalesInvoice.customer_id == Customer.id)
            .filter(
                SalesInvoice.company_id == self.company_id,
                SalesInvoice.outstanding_amount > 0,
                SalesInvoice.status != "cancelled",
            )
            .all()
        )

        aging = {"current": 0.0, "d0_30": 0.0, "d31_60": 0.0, "d61_90": 0.0, "d90_plus": 0.0}
        total = 0.0
        overdue = 0.0
        overdue_rows = []

        for inv, customer_name in rows:
            amt = float(inv.outstanding_amount or 0)
            total += amt
            due = self._effective_due(inv)
            days_overdue = (ref_date - due).days

            if days_overdue <= 0:
                aging["current"] += amt
            elif days_overdue <= 30:
                aging["d0_30"] += amt
            elif days_overdue <= 60:
                aging["d31_60"] += amt
            elif days_overdue <= 90:
                aging["d61_90"] += amt
            else:
                aging["d90_plus"] += amt

            if days_overdue > 0:
                overdue += amt
                overdue_rows.append({
                    "invoice_number": inv.invoice_number,
                    "customer": customer_name or "—",
                    "due_date": due.isoformat(),
                    "days_overdue": days_overdue,
                    "outstanding": amt,
                })

        overdue_rows.sort(key=lambda r: r["outstanding"], reverse=True)
        return {
            "total": total,
            "overdue": overdue,
            "aging": aging,
            "top_overdue": overdue_rows[:10],
        }

    def _payables_breakdown(self, ref_date: date) -> dict:
        """Total outstanding and overdue payables."""
        from app.models.transaction import PurchaseInvoice

        rows = (
            self.db.query(PurchaseInvoice)
            .filter(
                PurchaseInvoice.company_id == self.company_id,
                PurchaseInvoice.outstanding_amount > 0,
                PurchaseInvoice.status != "cancelled",
            )
            .all()
        )
        total = 0.0
        overdue = 0.0
        for inv in rows:
            amt = float(inv.outstanding_amount or 0)
            total += amt
            due = self._effective_due(inv)
            if (ref_date - due).days > 0:
                overdue += amt
        return {"total": total, "overdue": overdue}
