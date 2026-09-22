"""Working capital engine — aging, stress score, DSO/DPO/DIO."""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class WorkingCapitalEngine:
    def __init__(self, db: "Session", company_id: str):
        self.db = db
        self.company_id = uuid.UUID(company_id)

    def compute_and_store(self) -> dict:
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
        # Map internal keys to model field names
        model_data = {
            "receivables_total": metrics["receivables_total"],
            "receivables_overdue": metrics["receivables_overdue"],
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

    def _compute_metrics(self) -> dict:
        from app.models.transaction import SalesInvoice, PurchaseInvoice, InventoryMovement
        from sqlalchemy import case, func

        today = date.today()
        ninety_days_ago = today - timedelta(days=90)

        sales = self.db.query(func.sum(SalesInvoice.total_amount)).filter(
            SalesInvoice.company_id == self.company_id,
            SalesInvoice.invoice_date >= ninety_days_ago,
            SalesInvoice.status != "cancelled",
        ).scalar() or 0
        avg_daily_sales = float(sales) / 90

        # DSO / DPO use all open balances; the overdue part is reported separately.
        open_sales = [
            SalesInvoice.company_id == self.company_id,
            SalesInvoice.status.notin_(["paid", "cancelled"]),
        ]
        receivables = self.db.query(func.sum(SalesInvoice.outstanding_amount)).filter(*open_sales).scalar() or 0
        receivables_overdue = self.db.query(func.sum(SalesInvoice.outstanding_amount)).filter(
            *open_sales, SalesInvoice.due_date < today,
        ).scalar() or 0
        dso = float(receivables) / avg_daily_sales if avg_daily_sales > 0 else 0

        purchases = self.db.query(func.sum(PurchaseInvoice.total_amount)).filter(
            PurchaseInvoice.company_id == self.company_id,
            PurchaseInvoice.invoice_date >= ninety_days_ago,
            PurchaseInvoice.status != "cancelled",
        ).scalar() or 0
        avg_daily_purchases = float(purchases) / 90

        open_purchases = [
            PurchaseInvoice.company_id == self.company_id,
            PurchaseInvoice.status.notin_(["paid", "cancelled"]),
        ]
        payables = self.db.query(func.sum(PurchaseInvoice.outstanding_amount)).filter(*open_purchases).scalar() or 0
        payables_overdue = self.db.query(func.sum(PurchaseInvoice.outstanding_amount)).filter(
            *open_purchases, PurchaseInvoice.due_date < today,
        ).scalar() or 0
        dpo = float(payables) / avg_daily_purchases if avg_daily_purchases > 0 else 0

        # Movements are gross, so closing stock is receipts less issues. Transfers
        # move stock between warehouses and net to nil for the company.
        signed_value = case(
            (InventoryMovement.movement_type.in_(["goods_receipt", "opening", "adjustment"]), InventoryMovement.total_value),
            (InventoryMovement.movement_type == "transfer", 0),
            else_=-InventoryMovement.total_value,
        )
        inventory_value = self.db.query(func.sum(signed_value)).filter(
            InventoryMovement.company_id == self.company_id,
        ).scalar() or 0
        # DIO is inventory at cost over cost of goods issued, not over sales value.
        issues = self.db.query(func.sum(InventoryMovement.total_value)).filter(
            InventoryMovement.company_id == self.company_id,
            InventoryMovement.movement_type == "goods_issue",
            InventoryMovement.movement_date >= ninety_days_ago,
        ).scalar() or 0
        avg_daily_issues = float(issues) / 90
        dio = float(inventory_value) / avg_daily_issues if avg_daily_issues > 0 else 0

        ccc = dso + dio - dpo
        stress_score = min(100.0, max(0.0, (ccc / 180) * 100))

        return {
            "dso": round(dso, 1),
            "dpo": round(dpo, 1),
            "dio": round(dio, 1),
            "ccc": round(ccc, 1),
            "wc_stress_score": round(stress_score, 1),
            "receivables_total": float(receivables),
            "receivables_overdue": float(receivables_overdue),
            "payables_total": float(payables),
            "payables_overdue": float(payables_overdue),
            "inventory_value": float(inventory_value),
        }
