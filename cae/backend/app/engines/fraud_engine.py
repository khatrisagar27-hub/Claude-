"""Fraud analytics engine — Benford's Law, duplicates, round amounts, ML anomaly."""
from __future__ import annotations

import uuid
from collections import Counter
from datetime import date
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class FraudEngine:
    def __init__(self, db: "Session", company_id: str):
        self.db = db
        self.company_id = uuid.UUID(company_id)

    def run_all(self) -> list[dict]:
        indicators = []
        indicators.extend(self.benford_analysis())
        indicators.extend(self.detect_duplicate_invoices())
        indicators.extend(self.round_amount_analysis())
        indicators.extend(self.behavioral_anomaly())
        return indicators

    def benford_analysis(self) -> list[dict]:
        from app.models.transaction import SalesInvoice
        invoices = (
            self.db.query(SalesInvoice.total_amount)
            .filter(SalesInvoice.company_id == self.company_id, SalesInvoice.total_amount > 0)
            .all()
        )
        amounts = [float(r[0]) for r in invoices if r[0]]
        if len(amounts) < 50:
            return []

        leading_digits = [int(str(abs(a)).lstrip("0")[0]) for a in amounts if a > 0]
        observed = Counter(leading_digits)
        observed_freq = np.array([observed.get(d, 0) for d in range(1, 10)], dtype=float)
        observed_freq /= observed_freq.sum()

        benford_expected = np.array([np.log10(1 + 1 / d) for d in range(1, 10)])

        from scipy.stats import chisquare
        chi2, p_value = chisquare(observed_freq * len(amounts), f_exp=benford_expected * len(amounts))

        if p_value < 0.05:
            return [{
                "indicator_type": "benford_deviation",
                "description": f"Sales invoice amounts deviate from Benford's Law (p={p_value:.4f}, chi2={chi2:.2f}). Possible fabricated amounts.",
                "score": float(chi2),
                "affected_transactions": len(amounts),
                "financial_exposure": None,
                "details_json": {"sample_count": len(amounts), "p_value": float(p_value), "chi2": float(chi2)},
            }]
        return []

    def detect_duplicate_invoices(self) -> list[dict]:
        from app.models.transaction import PurchaseInvoice
        from sqlalchemy import func

        dupes = (
            self.db.query(
                PurchaseInvoice.vendor_id,
                PurchaseInvoice.total_amount,
                func.count(PurchaseInvoice.id).label("cnt"),
            )
            .filter(PurchaseInvoice.company_id == self.company_id)
            .group_by(PurchaseInvoice.vendor_id, PurchaseInvoice.total_amount)
            .having(func.count(PurchaseInvoice.id) > 1)
            .all()
        )

        return [
            {
                "indicator_type": "duplicate_invoice",
                "description": f"Vendor {vendor_id}: {cnt} invoices with identical amount ₹{float(amount):,.2f}. Possible duplicate payment.",
                "score": float(cnt),
                "affected_transactions": int(cnt),
                "financial_exposure": float(amount) * (cnt - 1),
                "details_json": {"vendor_id": str(vendor_id), "amount": float(amount), "count": int(cnt)},
            }
            for vendor_id, amount, cnt in dupes
        ]

    def round_amount_analysis(self) -> list[dict]:
        from app.models.transaction import PurchaseInvoice
        invoices = (
            self.db.query(PurchaseInvoice.id, PurchaseInvoice.total_amount)
            .filter(
                PurchaseInvoice.company_id == self.company_id,
                PurchaseInvoice.total_amount >= 100000,
            )
            .all()
        )

        thresholds = [1000, 5000, 10000, 100000]
        round_invoices = [
            {"id": str(inv_id), "amount": float(amt)}
            for inv_id, amt in invoices
            if any(float(amt) % t == 0 for t in thresholds)
        ]

        if not round_invoices:
            return []

        pct = len(round_invoices) / max(len(invoices), 1) * 100
        if pct > 20:
            return [{
                "indicator_type": "round_amount_concentration",
                "description": f"{pct:.1f}% of purchase invoices above ₹1L are round amounts. Normal is ~5-10%.",
                "score": round(pct, 2),
                "affected_transactions": len(round_invoices),
                "financial_exposure": sum(r["amount"] for r in round_invoices),
                "details_json": {"pct": pct, "sample": round_invoices[:10]},
            }]
        return []

    def behavioral_anomaly(self) -> list[dict]:
        from app.models.transaction import JournalEntry
        entries = (
            self.db.query(JournalEntry.id, JournalEntry.total_debit, JournalEntry.posted_by_user_id)
            .filter(JournalEntry.company_id == self.company_id)
            .all()
        )
        if len(entries) < 30:
            return []

        amounts = np.array([float(e[1] or 0) for e in entries]).reshape(-1, 1)
        try:
            from sklearn.ensemble import IsolationForest
            clf = IsolationForest(contamination=0.05, random_state=42)
            preds = clf.fit_predict(amounts)
            anomalies = [str(entries[i][0]) for i, p in enumerate(preds) if p == -1]
            if anomalies:
                return [{
                    "indicator_type": "ml_anomaly",
                    "description": f"Isolation Forest detected {len(anomalies)} anomalous journal entries by amount pattern.",
                    "score": float(len(anomalies)),
                    "affected_transactions": len(anomalies),
                    "financial_exposure": None,
                    "details_json": {"anomalous_je_ids": anomalies[:10]},
                }]
        except ImportError:
            pass
        return []

    def write_indicators(self, indicators: list[dict]) -> int:
        from app.models.risk import FraudIndicator
        today = date.today()
        written = 0
        for ind in indicators:
            fi = FraudIndicator(
                id=uuid.uuid4(),
                company_id=self.company_id,
                analysis_date=today,
                indicator_type=ind["indicator_type"],
                description=ind["description"],
                score=ind.get("score", 0),
                affected_transactions=ind.get("affected_transactions", 0),
                financial_exposure=ind.get("financial_exposure"),
                details_json=ind.get("details_json"),
            )
            self.db.add(fi)
            written += 1
        self.db.commit()
        return written
