"""Working capital engine — aging, stress score, DSO/DPO/DIO/CCC, Schedule III ageing and ratios.

Formulas (D = days in the period, capped at the days of books actually held):
  DSO = closing trade receivables / (sales incl. GST in the period / D)
  DPO = closing trade payables    / (purchases incl. GST in the period / D)
  DIO = closing inventory at cost / (cost of goods issued in the period / D)
  CCC = DSO + DIO - DPO

Period: inside an engagement, its period_from .. period_to (a statutory audit is
measured as at 31 March). Outside one, the 365 days to the reference date.

Where DSO / DPO / DIO depart from the textbook / ICAI Guidance Note on Schedule III ratios:
  * Closing, not average, balances. The Schedule III turnover ratios in
    `schedule_iii.ratios` use average balances instead.
  * Total sales, not credit sales. There is no reliable cash-sale marker.
    Cash sales in the denominator understate DSO slightly.
  * Purchases, not COGS, for DPO. This follows the ICAI trade-payables
    turnover ratio. Payables and purchases both include GST, so they match.
  * Receivables and sales both include GST; inventory and COGS are both at cost.

Balance of a bill on a date (`_open_at`). outstanding_amount is today's snapshot, so for an
earlier date: a bill settled after that date (payment_date later) was open for its full
amount; a bill still unpaid is open for its current outstanding; a bill marked `paid` with no
payment date is taken as settled. That last case is counted in data_quality when the as-at
date is earlier than the latest data.

Data handling:
  * Outside an engagement the as-at date is the *reference date* = the latest invoice date
    that carries an actual amount, so a historical data set is not aged against today.
    Zero-value invoices are ignored for this date.
  * A bill marked `paid` is settled even if its outstanding_amount was never cleared
    (as in GST-002). Counting such bills put DPO at 629 days on the seed data instead of 263.
  * Stress-score ageing: when an invoice has no due date, the party's credit days apply
    (Customer.credit_days / Vendor.payment_terms_days), else Net-30.
  * Inventory is held as gross movements. Stock on hand is the signed net per item
    (receipts / adjustments add, issues subtract, transfers ignored), floored at zero.
    A negative net means opening stock is missing from the ledger.
  * `data_quality` in the output counts every one of these fallbacks.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING, Optional

from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DEFAULT_CREDIT_DAYS = 30
WINDOW_DAYS = 365
SETTLED = ("cancelled", "paid")

# Schedule III (Companies Act 2013), Division I & II, as amended by MCA notification
# G.S.R. 207(E) of 24-03-2021, from FY 2021-22: ageing of trade receivables and trade
# payables "from due date of payment", or from the date of the transaction where no due
# date is specified. "Not due" is the column the ICAI Guidance Note adds for bills
# not yet due.
SCH3_RECEIVABLE_COLUMNS = ["Not due", "Less than 6 months", "6 months - 1 year", "1-2 years", "2-3 years",
                           "More than 3 years"]
SCH3_PAYABLE_COLUMNS = ["Not due", "Less than 1 year", "1-2 years", "2-3 years", "More than 3 years"]
# Ratios the same amendment requires, with an explanation when one moves by more than 25%.
SCH3_VARIANCE_PCT = 25.0


@dataclass
class Bill:
    number: str
    party: Optional[str]
    invoice_date: date
    due_date: Optional[date]
    total: float
    outstanding: float
    status: str
    payment_date: Optional[date]
    terms: Optional[int]          # party credit days from the master
    msme: bool = False            # vendor is a micro or small enterprise (MSMED Act s.2)


class WorkingCapitalEngine:
    def __init__(self, db: "Session", company_id: str, engagement=None):
        self.db = db
        self.company_id = uuid.UUID(company_id)
        self.engagement = engagement

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
        """Live computation with aging breakdown, top overdue receivables and Schedule III."""
        metrics = self._compute_metrics()
        metrics["company_id"] = str(self.company_id)
        return metrics

    # ------------------------------------------------------------------ #
    # Core computation
    # ------------------------------------------------------------------ #
    def _period(self) -> tuple[date, date, date]:
        """(period start, as-at date, latest data date)."""
        latest = self._reference_date()
        if self.engagement is not None:
            return self.engagement.period_from, self.engagement.period_to, latest
        return latest - timedelta(days=WINDOW_DAYS - 1), latest, latest   # 365 days including as-at

    def _compute_metrics(self) -> dict:
        start, as_on, latest = self._period()
        first = self._first_invoice_date()
        days = self._days_in_window(first, start, as_on)
        sales_bills = self._sales_bills(as_on)
        purchase_bills = self._purchase_bills(as_on)

        period_sales = self._turnover(sales_bills, start, as_on)
        avg_daily_sales = period_sales / days
        ar = self._receivables_breakdown(sales_bills, as_on)
        dso = ar["total"] / avg_daily_sales if avg_daily_sales > 0 else 0

        period_purchases = self._turnover(purchase_bills, start, as_on)
        avg_daily_purchases = period_purchases / days
        ap = self._payables_breakdown(purchase_bills, as_on)
        dpo = ap["total"] / avg_daily_purchases if avg_daily_purchases > 0 else 0

        # --- Inventory on-hand, turned over at cost (goods issued), not at selling price ---
        inventory_value, items_below_zero = self._inventory_value(as_on)
        cogs, dio_basis = self._annual_cost_of_goods(start, as_on)
        if cogs <= 0:
            cogs, dio_basis = period_sales, "sales (no cost data)"
        dio = inventory_value / (cogs / days) if cogs > 0 else 0

        # --- Cash conversion cycle + stress score ---
        ccc = dso + dio - dpo
        stress_score, stress_components = self._stress_score(ar, ap, dso, ccc)

        assumed_settled = 0
        if as_on < latest:
            assumed_settled = sum(1 for b in sales_bills + purchase_bills
                                  if b.status == "paid" and b.payment_date is None)

        return {
            "as_of": as_on.isoformat(),
            "period_from": start.isoformat(),
            "engagement_id": str(self.engagement.id) if self.engagement is not None else None,
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
                "paid_bills_without_payment_date_assumed_settled": assumed_settled,
                "books_end_before_as_of": latest < as_on,
                "latest_invoice_date": latest.isoformat(),
            },
            "receivables_total": round(ar["total"], 2),
            "receivables_overdue": round(ar["overdue"], 2),
            "payables_total": round(ap["total"], 2),
            "payables_overdue": round(ap["overdue"], 2),
            "inventory_value": round(inventory_value, 2),
            "avg_daily_sales": round(avg_daily_sales, 2),
            "receivables_aging": {k: round(v, 2) for k, v in ar["aging"].items()},
            "top_overdue_receivables": ar["top_overdue"],
            "schedule_iii": self._schedule_iii(sales_bills, purchase_bills, start, as_on, first),
        }

    # ------------------------------------------------------------------ #
    # Bills and balances
    # ------------------------------------------------------------------ #
    def _sales_bills(self, as_on: date) -> list[Bill]:
        from app.models.transaction import SalesInvoice
        from app.models.master import Customer

        q = (
            self.db.query(SalesInvoice.invoice_number, Customer.name, SalesInvoice.invoice_date, SalesInvoice.due_date,
                          SalesInvoice.total_amount, SalesInvoice.outstanding_amount, SalesInvoice.status,
                          SalesInvoice.payment_date, Customer.credit_days)
            .outerjoin(Customer, SalesInvoice.customer_id == Customer.id)
            .filter(SalesInvoice.company_id == self.company_id, SalesInvoice.status != "cancelled",
                    SalesInvoice.invoice_date <= as_on)
        )
        return [Bill(n, p, d, due, float(t or 0), float(o or 0), s, pd, terms) for n, p, d, due, t, o, s, pd, terms in q]

    def _purchase_bills(self, as_on: date) -> list[Bill]:
        from app.models.transaction import PurchaseInvoice
        from app.models.master import Vendor
        from app.statutory import msme

        q = (
            self.db.query(PurchaseInvoice.invoice_number, Vendor.name, PurchaseInvoice.invoice_date,
                          PurchaseInvoice.due_date, PurchaseInvoice.total_amount, PurchaseInvoice.outstanding_amount,
                          PurchaseInvoice.status, PurchaseInvoice.payment_date, Vendor.payment_terms_days,
                          Vendor.msme_status)
            .outerjoin(Vendor, PurchaseInvoice.vendor_id == Vendor.id)
            .filter(PurchaseInvoice.company_id == self.company_id, PurchaseInvoice.status != "cancelled",
                    PurchaseInvoice.invoice_date <= as_on)   # a bill dated after the as-at date is not yet payable
        )
        return [Bill(n, p, d, due, float(t or 0), float(o or 0), s, pd, terms, msme.is_protected(ms))
                for n, p, d, due, t, o, s, pd, terms, ms in q]

    @staticmethod
    def _open_at(bill: Bill, on: date) -> float:
        """Amount of the bill still open on `on`, from today's outstanding and the settlement date."""
        if bill.invoice_date > on or bill.status == "cancelled":
            return 0.0
        if bill.payment_date and bill.payment_date > on:
            return bill.total
        if bill.status == "paid":
            return 0.0
        return max(bill.outstanding, 0.0)

    @classmethod
    def _balance(cls, bills: list[Bill], on: date) -> float:
        return sum(cls._open_at(b, on) for b in bills)

    @staticmethod
    def _turnover(bills: list[Bill], start: date, end: date) -> float:
        return sum(b.total for b in bills if start <= b.invoice_date <= end)

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
        """Days of books inside the period: a 5-month history annualised over 365 days
        would understate daily sales and inflate DSO / DPO / DIO 2.4 times."""
        begin = window_start if first is None or first <= window_start else first
        return max(1, (ref_date - begin).days + 1)

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

    def _receivables_breakdown(self, bills: list[Bill], as_on: date) -> dict:
        """Aging buckets, totals, overdue and top overdue from receivables open on the as-at date."""
        aging = {"current": 0.0, "d0_30": 0.0, "d31_60": 0.0, "d61_90": 0.0, "d90_plus": 0.0}
        total = 0.0
        overdue = 0.0
        overdue_rows = []
        due_assumed = 0
        paid_with_outstanding = sum(1 for b in bills if b.status == "paid" and b.outstanding > 0)

        for b in bills:
            amt = self._open_at(b, as_on)
            if amt <= 0:
                continue
            total += amt
            due, assumed = self._effective_due(b, b.terms)
            due_assumed += assumed
            days_overdue = (as_on - due).days

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
                    "invoice_number": b.number,
                    "customer": b.party or "—",
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

    def _payables_breakdown(self, bills: list[Bill], as_on: date) -> dict:
        """Total and overdue payables open on the as-at date."""
        paid_with_outstanding = sum(1 for b in bills if b.status == "paid" and b.outstanding > 0)
        total = 0.0
        overdue = 0.0
        due_assumed = 0
        for b in bills:
            amt = self._open_at(b, as_on)
            if amt <= 0:
                continue
            total += amt
            due, assumed = self._effective_due(b, b.terms)
            due_assumed += assumed
            if (as_on - due).days > 0:
                overdue += amt
        return {"total": total, "overdue": overdue, "due_assumed": due_assumed,
                "paid_with_outstanding": paid_with_outstanding}

    # ------------------------------------------------------------------ #
    # Schedule III
    # ------------------------------------------------------------------ #
    @staticmethod
    def _sch3_age_from(bill: Bill, payable: bool) -> tuple[date, str]:
        """Date ageing runs from under Schedule III, and the basis used."""
        if bill.due_date:
            return bill.due_date, "due date"
        if payable and bill.msme:
            from app.statutory import msme
            return msme.appointed_day(bill.invoice_date, bill.terms)[0], "MSMED s.15 appointed day"
        if bill.terms:
            return bill.invoice_date + timedelta(days=int(bill.terms)), "party credit terms"
        return bill.invoice_date, "transaction date"

    @staticmethod
    def _sch3_bucket(age_from: date, as_on: date, payable: bool) -> int:
        """Column index into SCH3_*_COLUMNS."""
        if age_from >= as_on:
            return 0
        steps = ([relativedelta(years=1), relativedelta(years=2), relativedelta(years=3)] if payable else
                 [relativedelta(months=6), relativedelta(years=1), relativedelta(years=2), relativedelta(years=3)])
        for i, step in enumerate(steps, 1):
            if age_from > as_on - step:
                return i
        return len(steps) + 1

    @classmethod
    def _sch3_ageing(cls, bills: list[Bill], as_on: date, payable: bool) -> dict:
        columns = SCH3_PAYABLE_COLUMNS if payable else SCH3_RECEIVABLE_COLUMNS
        labels = (["MSME", "Others", "Disputed dues - MSME", "Disputed dues - Others"] if payable
                  else ["Undisputed", "Disputed"])
        table = {label: [0.0] * len(columns) for label in labels}
        basis: dict[str, int] = {}
        for b in bills:
            amt = cls._open_at(b, as_on)
            if amt <= 0:
                continue
            disputed = b.status == "disputed"
            if payable:
                label = ("Disputed dues - " if disputed else "") + ("MSME" if b.msme else "Others")
            else:
                label = "Disputed" if disputed else "Undisputed"
            age_from, how = cls._sch3_age_from(b, payable)
            basis[how] = basis.get(how, 0) + 1
            table[label][cls._sch3_bucket(age_from, as_on, payable)] += amt
        rows = [{"label": label, "amounts": [round(v, 2) for v in vals], "total": round(sum(vals), 2)}
                for label, vals in table.items()]
        note = ("MSME = micro and small enterprises per the vendor master (MSMED Act s.2); dues of medium "
                "enterprises fall under Others." if payable else
                "Schedule III also splits each row into considered good / significant increase in credit risk / "
                "credit impaired. That classification is the auditor's judgement and is not made here.")
        return {"columns": columns, "rows": rows, "total": round(sum(r["total"] for r in rows), 2),
                "aged_from": basis, "note": note}

    def _sch3_ratios_for(self, sales: list[Bill], purchases: list[Bill], start: date, end: date) -> dict | None:
        opening = start - timedelta(days=1)
        turnover_s = self._turnover(sales, start, end)
        turnover_p = self._turnover(purchases, start, end)
        if turnover_s <= 0 and turnover_p <= 0:
            return None
        avg = lambda a, b: (a + b) / 2  # noqa: E731
        avg_ar = avg(self._balance(sales, opening), self._balance(sales, end))
        avg_ap = avg(self._balance(purchases, opening), self._balance(purchases, end))
        avg_inv = avg(self._inventory_value(opening)[0], self._inventory_value(end)[0])
        cogs, _ = self._annual_cost_of_goods(start, end)
        div = lambda a, b: round(a / b, 2) if b else None  # noqa: E731
        return {
            "trade_receivables_turnover": div(turnover_s, avg_ar),
            "trade_payables_turnover": div(turnover_p, avg_ap),
            "inventory_turnover": div(cogs, avg_inv),
            "inputs": {"sales": round(turnover_s, 2), "purchases": round(turnover_p, 2), "cogs": round(cogs, 2),
                       "average_trade_receivables": round(avg_ar, 2), "average_trade_payables": round(avg_ap, 2),
                       "average_inventory": round(avg_inv, 2)},
        }

    def _schedule_iii(self, sales: list[Bill], purchases: list[Bill], start: date, as_on: date,
                      first: date | None) -> dict:
        prior_start, prior_end = start - relativedelta(years=1), start - timedelta(days=1)
        current = self._sch3_ratios_for(sales, purchases, start, as_on)
        prior = (self._sch3_ratios_for(sales, purchases, prior_start, prior_end)
                 if first is not None and first <= prior_start else None)   # never compare against a part year
        names = {"trade_receivables_turnover": "Trade receivables turnover ratio (times)",
                 "trade_payables_turnover": "Trade payables turnover ratio (times)",
                 "inventory_turnover": "Inventory turnover ratio (times)"}
        formulas = {"trade_receivables_turnover": "Sales (incl. GST) / average trade receivables",
                    "trade_payables_turnover": "Purchases (incl. GST) / average trade payables",
                    "inventory_turnover": "Cost of goods issued / average inventory"}
        ratios = []
        for key, name in names.items():
            cur = current.get(key) if current else None
            prev = prior.get(key) if prior else None
            change = round((cur - prev) / prev * 100, 1) if cur is not None and prev else None
            ratios.append({"key": key, "ratio": name, "formula": formulas[key], "current": cur, "previous": prev,
                           "change_pct": change,
                           "explanation_required": change is not None and abs(change) > SCH3_VARIANCE_PCT})
        return {
            "as_of": as_on.isoformat(),
            "period": [start.isoformat(), as_on.isoformat()],
            "previous_period": [prior_start.isoformat(), prior_end.isoformat()],
            "trade_receivables": self._sch3_ageing(sales, as_on, payable=False),
            "trade_payables": self._sch3_ageing(purchases, as_on, payable=True),
            "ratios": ratios,
            "ratio_inputs": {"current": current["inputs"] if current else None,
                             "previous": prior["inputs"] if prior else None},
            "not_computed": ["Current ratio, debt-equity, DSCR, ROE, net capital turnover, net profit, ROCE and "
                             "return on investment need balance-sheet and P&L figures that invoice data lacks"],
        }
