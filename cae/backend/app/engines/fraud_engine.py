"""Fraud analytics engine — Benford's Law, duplicates, round amounts, ML anomaly.

Benford uses Nigrini's first-digit mean absolute deviation (MAD) rather than a
chi-square p-value: with thousands of invoices chi-square rejects almost any real
data set, so it flagged everything. MAD conformity bands (Nigrini, 2012):
  <= 0.006 close, <= 0.012 acceptable, <= 0.015 marginal, > 0.015 nonconformity.
"""
from __future__ import annotations

import math
import uuid
from collections import Counter
from datetime import date
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

MIN_BENFORD_N = 300
MAD_BANDS = [(0.006, "close conformity"), (0.012, "acceptable conformity"), (0.015, "marginally acceptable")]
SCORE_CAP = 999.99   # FraudIndicator.score is NUMERIC(5,2)


def first_digit(amount: float) -> int | None:
    a = abs(float(amount))
    if a <= 0 or not math.isfinite(a):
        return None
    return int(f"{a:e}"[0])


def benford_first_digit(amounts: list[float]) -> dict:
    digits = [d for d in (first_digit(a) for a in amounts) if d]
    n = len(digits)
    counts = Counter(digits)
    observed = np.array([counts.get(d, 0) / n if n else 0 for d in range(1, 10)])
    expected = np.array([math.log10(1 + 1 / d) for d in range(1, 10)])
    mad = float(np.mean(np.abs(observed - expected))) if n else 0.0
    band = next((label for limit, label in MAD_BANDS if mad <= limit), "nonconformity")
    return {"n": n, "mad": mad, "conformity": band,
            "observed": [round(float(x), 4) for x in observed], "expected": [round(float(x), 4) for x in expected]}


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
        from app.models.transaction import PurchaseInvoice, SalesInvoice
        out = []
        for label, model in (("Sales", SalesInvoice), ("Purchase", PurchaseInvoice)):
            amounts = [float(r[0]) for r in self.db.query(model.total_amount)
                       .filter(model.company_id == self.company_id, model.total_amount > 0,
                               model.status != "cancelled").all()]
            if len(amounts) < MIN_BENFORD_N:
                continue
            result = benford_first_digit(amounts)
            if result["conformity"] in ("close conformity", "acceptable conformity"):
                continue
            out.append({
                "indicator_type": "benford_deviation",
                "description": f"{label} invoice amounts show {result['conformity']} with Benford's first-digit law "
                               f"(MAD {result['mad']:.4f}, n={result['n']}). Look at the digits that are over-represented.",
                "score": min(round(result["mad"] * 1000, 2), SCORE_CAP),
                "affected_transactions": result["n"],
                "financial_exposure": None,
                "details_json": {"population": label.lower(), **result},
            })
        return out

    def detect_duplicate_invoices(self) -> list[dict]:
        """Same vendor, same amount, same invoice date — an exact-duplicate indicator."""
        from app.models.transaction import PurchaseInvoice
        from sqlalchemy import func

        dupes = (
            self.db.query(
                PurchaseInvoice.vendor_id, PurchaseInvoice.total_amount, PurchaseInvoice.invoice_date,
                func.count(PurchaseInvoice.id).label("cnt"),
            )
            .filter(PurchaseInvoice.company_id == self.company_id, PurchaseInvoice.status != "cancelled",
                    PurchaseInvoice.total_amount > 0)
            .group_by(PurchaseInvoice.vendor_id, PurchaseInvoice.total_amount, PurchaseInvoice.invoice_date)
            .having(func.count(PurchaseInvoice.id) > 1)
            .all()
        )
        return [
            {
                "indicator_type": "duplicate_invoice",
                "description": f"Vendor {vendor_id}: {cnt} invoices of ₹{float(amount):,.2f} dated {inv_date}. Possible duplicate booking.",
                "score": min(float(cnt), SCORE_CAP),
                "affected_transactions": int(cnt),
                "financial_exposure": float(amount) * (cnt - 1),
                "details_json": {"vendor_id": str(vendor_id), "amount": float(amount), "date": str(inv_date), "count": int(cnt)},
            }
            for vendor_id, amount, inv_date, cnt in dupes
        ]

    def round_amount_analysis(self, threshold_pct: float = 20.0) -> list[dict]:
        from app.models.transaction import PurchaseInvoice
        invoices = (
            self.db.query(PurchaseInvoice.id, PurchaseInvoice.total_amount)
            .filter(PurchaseInvoice.company_id == self.company_id, PurchaseInvoice.total_amount >= 100000)
            .all()
        )
        round_invoices = [{"id": str(i), "amount": float(a)} for i, a in invoices if float(a) % 1000 == 0]
        if not invoices or not round_invoices:
            return []
        pct = len(round_invoices) / len(invoices) * 100
        if pct <= threshold_pct:
            return []
        return [{
            "indicator_type": "round_amount_concentration",
            "description": f"{pct:.1f}% of purchase invoices of ₹1L or more are exact multiples of ₹1,000. "
                           "Tax-inclusive values rarely land on round figures; look for estimates or fabricated bills.",
            "score": round(pct, 2),
            "affected_transactions": len(round_invoices),
            "financial_exposure": sum(r["amount"] for r in round_invoices),
            "details_json": {"pct": pct, "sample": round_invoices[:10]},
        }]

    def behavioral_anomaly(self) -> list[dict]:
        """Isolation Forest over amount, weekend posting, round value and posting lag."""
        from app.models.transaction import JournalEntry
        entries = (
            self.db.query(JournalEntry.id, JournalEntry.total_debit, JournalEntry.entry_date, JournalEntry.posted_at)
            .filter(JournalEntry.company_id == self.company_id)
            .all()
        )
        if len(entries) < 30:
            return []
        features = []
        for _, amount, entry_date, posted_at in entries:
            amt = float(amount or 0)
            lag = (posted_at.date() - entry_date).days if posted_at and entry_date else 0
            features.append([
                math.log10(amt + 1),
                1.0 if entry_date and entry_date.weekday() >= 5 else 0.0,
                1.0 if amt >= 1000 and amt % 1000 == 0 else 0.0,
                float(max(lag, 0)),
            ])
        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            return []
        preds = IsolationForest(contamination=0.02, random_state=42).fit_predict(np.array(features))
        anomalies = [str(entries[i][0]) for i, p in enumerate(preds) if p == -1]
        if not anomalies:
            return []
        return [{
            "indicator_type": "ml_anomaly",
            "description": f"Isolation Forest flagged {len(anomalies)} journal entries as unusual on amount, weekend posting, "
                           "round value and posting lag together.",
            "score": min(float(len(anomalies)), SCORE_CAP),
            "affected_transactions": len(anomalies),
            "financial_exposure": None,
            "details_json": {"anomalous_je_ids": anomalies[:25], "features": ["log_amount", "weekend", "round", "posting_lag_days"]},
        }]

    def write_indicators(self, indicators: list[dict]) -> int:
        from app.models.risk import FraudIndicator
        today = date.today()
        # one set per day — a re-run replaces today's indicators instead of stacking duplicates
        self.db.query(FraudIndicator).filter(FraudIndicator.company_id == self.company_id,
                                             FraudIndicator.analysis_date == today).delete(synchronize_session=False)
        written = 0
        for ind in indicators:
            fi = FraudIndicator(
                id=uuid.uuid4(),
                company_id=self.company_id,
                analysis_date=today,
                indicator_type=ind["indicator_type"],
                description=ind["description"][:500],
                score=ind.get("score", 0),
                affected_transactions=ind.get("affected_transactions", 0),
                financial_exposure=ind.get("financial_exposure"),
                details_json=ind.get("details_json"),
            )
            self.db.add(fi)
            written += 1
        self.db.commit()
        return written
