"""Working capital engine — aging, stress score, DSO/DPO/DIO/CCC.

Formulas (D = days in the trailing window, 365 unless the books hold less history):
  DSO = closing trade receivables / (sales incl. GST in the window / D)
  DPO = closing trade payables    / (purchases incl. GST in the window / D)
  DIO = closing inventory at cost / (cost of goods issued in the window / D)
  CCC = DSO + DIO - DPO

Where this departs from the textbook / ICAI Guidance Note on Schedule III ratios:
  * Closing, not average, balances. An opening balance needs the settlement
    date of every invoice paid in the year, which imported books often lack.
    Closing balances are the period-end ("countback") reading.
  * Total sales, not credit sales. There is no reliable cash-sale marker.
    Cash sales in the denominator understate DSO slightly.
  * Purchases, not COGS, for DPO. This follows the ICAI trade-payables
    turnover ratio. Payables and purchases both include GST, so they match.
  * Receivables and sales both include GST; inventory and COGS are both at cost.

Data handling:
  * Metrics are computed "as of" a *reference date* = the latest invoice date
    that carries an actual amount. This is how auditors age receivables
    (against the last data / period-end date) rather than the wall-clock
    date, and it keeps the view meaningful when the books are not perfectly
    current. Zero-value invoices are ignored for this date.
  * A bill marked `paid` is settled even if its outstanding_amount was never
    cleared (as in GST-002). Counting such bills put DPO at 629 days on the seed
    data instead of 263.
  * When an invoice has no due date, the party's credit days apply
    (Customer.credit_days / Vendor.payment_terms_days), else Net-30.
  * Inventory is held as gross movements. Stock on hand is the signed net per
    item (receipts / adjustments add, issues subtract, transfers ignored),
    floored at zero. A negative net means opening stock is missing from the
    ledger.
  * `data_quality` in the output counts every one of these fallbacks.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DEFAULT_CREDIT_DAYS = 30
WINDOW_DAYS = 365
SETTLED = ("cancelled", "paid")


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
        window_start = ref_date - timedelta(days=WINDOW_DAYS - 1)   # 365 days including ref_date
        days = self._days_in_window(self._first_invoice_date(), window_start, ref_date)

        # --- Sales velocity (trailing 12 months) ---
        annual_sales = self.db.query(func.sum(SalesInvoice.total_amount)).filter(
            SalesInvoice.company_id == self.company_id,
            SalesInvoice.invoice_date >= window_start,
            SalesInvoice.invoice_date <= ref_date,
            SalesInvoice.status != "cancelled",
        ).scalar() or 0
        avg_daily_sales = float(annual_sales) / days

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
        avg_daily_purchases = float(annual_purchases) / days

        ap = self._payables_breakdown(ref_date)
        dpo = ap["total"] / avg_daily_purchases if avg_daily_purchases > 0 else 0

        # --- Inventory on-hand, turned over at cost (goods issued), not at selling price ---
        inventory_value, items_below_zero = self._inventory_value(ref_date)
        cogs, dio_basis = self._annual_cost_of_goods(window_start, ref_date)
        if cogs <= 0:
            cogs, dio_basis = float(annual_sales), "sales (no cost data)"
        dio = inventory_value / (cogs / days) if cogs > 0 else 0

        # --- Cash conversion cycle + stress score ---
        ccc = dso + dio - dpo
        stress_score, stress_components = self._stress_score(ar, ap, dso, ccc)

        return {
            "as_of": ref_date.isoformat(),
            "dso": round(dso, 1),
            "dpo": round(dpo, 1),
            "dio": round(dio, 1),
            "ccc": round(ccc, 1),
            "stress_score": round(stress_score, 1),
            "wc_stress_score": round(stress_score, 1),  # alias for stored model
            "stress_components": stress_components,
            "dio_basis": dio_basis,
            "days_in_period": days,
            "data_quality": {
                "receivables_due_date_assumed": ar["due_assumed"],
                "payables_due_date_assumed": ap["due_assumed"],
                "payables_paid_with_outstanding_ignored": ap["paid_with_outstanding"],
                "receivables_paid_with_outstanding_ignored": ar["paid_with_outstanding"],
                "zero_value_sales_invoices": self._zero_value_sales(),
                "inventory_items_below_zero": items_below_zero,
            },
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

    def _first_invoice_date(self) -> date | None:
        from app.models.transaction import SalesInvoice, PurchaseInvoice
        from sqlalchemy import func

        firsts = [
            self.db.query(func.min(m.invoice_date)).filter(m.company_id == self.company_id).scalar()
            for m in (SalesInvoice, PurchaseInvoice)
        ]
        firsts = [d for d in firsts if d]
        return min(firsts) if firsts else None

    @staticmethod
    def _days_in_window(first: date | None, window_start: date, ref_date: date) -> int:
        """Days of books inside the window: a 5-month history annualised over 365 days
        would understate daily sales and inflate DSO / DPO / DIO 2.4 times."""
        if first is None or first <= window_start:
            return WINDOW_DAYS
        return max(1, (ref_date - first).days + 1)

    def _zero_value_sales(self) -> int:
        from app.models.transaction import SalesInvoice

        return self.db.query(SalesInvoice).filter(
            SalesInvoice.company_id == self.company_id,
            SalesInvoice.total_amount == 0,
            SalesInvoice.status != "cancelled",
        ).count()

    # Stress = weighted share of warning signs, 0 (healthy) to 100 (critical). A CCC-only score
    # read 0 / "healthy" with 92% of receivables overdue, because a long DPO netted it away.
    STRESS_WEIGHTS = {"receivables_90_plus": 0.30, "receivables_overdue": 0.20, "dso_vs_180": 0.20,
                      "payables_overdue": 0.15, "ccc_vs_180": 0.15}

    @classmethod
    def _stress_score(cls, ar: dict, ap: dict, dso: float, ccc: float) -> tuple[float, dict]:
        share = lambda part, whole: (part / whole) if whole else 0.0  # noqa: E731
        signals = {
            "receivables_90_plus": share(ar["aging"]["d90_plus"], ar["total"]),
            "receivables_overdue": share(ar["overdue"], ar["total"]),
            "dso_vs_180": min(max(dso, 0) / 180, 1.0),
            "payables_overdue": share(ap["overdue"], ap["total"]),
            "ccc_vs_180": min(max(ccc, 0) / 180, 1.0),
        }
        score = 100 * sum(cls.STRESS_WEIGHTS[k] * v for k, v in signals.items())
        return min(100.0, score), {k: round(v * 100, 1) for k, v in signals.items()}

    def _annual_cost_of_goods(self, start: date, end: date) -> tuple[float, str]:
        """Cost of goods issued in the window (inventory ledger), else taxable purchases."""
        from app.models.transaction import InventoryMovement, PurchaseInvoice
        from sqlalchemy import func

        issued = self.db.query(func.sum(InventoryMovement.total_value)).filter(
            InventoryMovement.company_id == self.company_id,
            InventoryMovement.movement_type == "goods_issue",
            InventoryMovement.movement_date >= start,
            InventoryMovement.movement_date <= end,
        ).scalar() or 0
        if float(issued) > 0:
            return float(issued), "cost of goods issued"
        bought = self.db.query(func.sum(PurchaseInvoice.taxable_amount)).filter(
            PurchaseInvoice.company_id == self.company_id,
            PurchaseInvoice.invoice_date >= start,
            PurchaseInvoice.invoice_date <= end,
            PurchaseInvoice.status != "cancelled",
        ).scalar() or 0
        return float(bought), "taxable purchases"

    @staticmethod
    def _effective_due(invoice, party_credit_days: int | None = None) -> tuple[date, bool]:
        """Due date, and whether it was assumed (no due date on the bill)."""
        if invoice.due_date:
            return invoice.due_date, False
        return invoice.invoice_date + timedelta(days=party_credit_days or DEFAULT_CREDIT_DAYS), True

    def _inventory_value(self, ref_date: date) -> tuple[float, int]:
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
        value, below = self.db.query(
            func.sum(func.greatest(per_item.c.net, 0)),
            func.count().filter(per_item.c.net < 0),
        ).one()
        return float(value or 0), int(below or 0)

    def _receivables_breakdown(self, ref_date: date) -> dict:
        """Aging buckets, totals, overdue and top overdue from outstanding AR."""
        from app.models.transaction import SalesInvoice
        from app.models.master import Customer

        rows = (
            self.db.query(SalesInvoice, Customer.name, Customer.credit_days)
            .outerjoin(Customer, SalesInvoice.customer_id == Customer.id)
            .filter(
                SalesInvoice.company_id == self.company_id,
                SalesInvoice.outstanding_amount > 0,
                SalesInvoice.status != "cancelled",
                SalesInvoice.invoice_date <= ref_date,
            )
            .all()
        )
        paid_with_outstanding = sum(1 for inv, _, _ in rows if inv.status == "paid")
        rows = [r for r in rows if r[0].status not in SETTLED]

        aging = {"current": 0.0, "d0_30": 0.0, "d31_60": 0.0, "d61_90": 0.0, "d90_plus": 0.0}
        total = 0.0
        overdue = 0.0
        overdue_rows = []
        due_assumed = 0

        for inv, customer_name, credit_days in rows:
            amt = float(inv.outstanding_amount or 0)
            total += amt
            due, assumed = self._effective_due(inv, credit_days)
            due_assumed += assumed
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
            "due_assumed": due_assumed,
            "paid_with_outstanding": paid_with_outstanding,
        }

    def _payables_breakdown(self, ref_date: date) -> dict:
        """Total outstanding and overdue payables."""
        from app.models.transaction import PurchaseInvoice
        from app.models.master import Vendor

        rows = (
            self.db.query(PurchaseInvoice, Vendor.payment_terms_days)
            .outerjoin(Vendor, PurchaseInvoice.vendor_id == Vendor.id)
            .filter(
                PurchaseInvoice.company_id == self.company_id,
                PurchaseInvoice.outstanding_amount > 0,
                PurchaseInvoice.status != "cancelled",
                PurchaseInvoice.invoice_date <= ref_date,   # a bill dated after the as-of date is not yet payable
            )
            .all()
        )
        paid_with_outstanding = sum(1 for inv, _ in rows if inv.status == "paid")
        total = 0.0
        overdue = 0.0
        due_assumed = 0
        for inv, terms in rows:
            if inv.status in SETTLED:
                continue
            amt = float(inv.outstanding_amount or 0)
            total += amt
            due, assumed = self._effective_due(inv, terms)
            due_assumed += assumed
            if (ref_date - due).days > 0:
                overdue += amt
        return {"total": total, "overdue": overdue, "due_assumed": due_assumed,
                "paid_with_outstanding": paid_with_outstanding}
