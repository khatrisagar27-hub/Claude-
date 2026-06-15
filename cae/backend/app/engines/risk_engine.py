"""Risk scoring engine.

Formula: risk_score = likelihood * impact * materiality_factor * frequency_factor * (1 + control_weakness)
Bands: 0-20=Low, 21-50=Moderate, 51-80=High, 81+=Critical
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


BUSINESS_AREAS = [
    "revenue", "expenditure", "inventory", "bank_reconciliation",
    "payroll", "gst", "related_party", "statutory",
]


def _risk_band(score: float) -> str:
    if score >= 81:
        return "critical"
    if score >= 51:
        return "high"
    if score >= 21:
        return "moderate"
    return "low"


class RiskEngine:
    def __init__(self, db: "Session", company_id: str):
        self.db = db
        self.company_id = uuid.UUID(company_id)

    def compute_and_store(self) -> int:
        from app.models.risk import RiskScore
        today = date.today()
        scores = self._compute_scores()
        written = 0
        for area, data in scores.items():
            rs = RiskScore(
                id=uuid.uuid4(),
                company_id=self.company_id,
                score_date=today,
                entity_level="process",
                entity_name=area,
                likelihood=data["likelihood"],
                impact=data["impact"],
                materiality=data["materiality"],
                frequency=data["frequency"],
                control_weakness=data["control_weakness"],
                composite_score=data["composite_score"],
                risk_band=data["risk_band"],
            )
            self.db.add(rs)
            written += 1
        self.db.commit()
        return written

    def _compute_scores(self) -> dict:
        from app.models.audit import AuditException
        from sqlalchemy import func

        thirty_days_ago = date.today() - timedelta(days=30)

        result = {}
        for area in BUSINESS_AREAS:
            excs = (
                self.db.query(AuditException)
                .filter(
                    AuditException.company_id == self.company_id,
                    AuditException.category == area,
                    AuditException.status.in_(["open", "in_review", "management_query_sent", "remediation_in_progress"]),
                )
                .all()
            )

            if not excs:
                result[area] = {
                    "likelihood": 1, "impact": 1, "materiality": 0.5,
                    "frequency": 1, "control_weakness": 0,
                    "composite_score": 1.0, "risk_band": "low",
                }
                continue

            severity_scores = {"critical": 5, "high": 4, "medium": 3, "low": 1}
            max_severity = max(severity_scores.get(e.severity, 1) for e in excs)
            avg_severity = sum(severity_scores.get(e.severity, 1) for e in excs) / len(excs)

            financial_impacts = [float(e.financial_impact or 0) for e in excs]
            total_impact = sum(financial_impacts)
            materiality = min(2.0, max(0.5, total_impact / 10_000_000))

            recent_count = sum(1 for e in excs if e.detected_on >= thirty_days_ago)
            frequency = min(3.0, 1.0 + recent_count / max(len(excs), 1) * 2)

            critical_count = sum(1 for e in excs if e.severity == "critical")
            control_weakness = min(1.0, critical_count / max(len(excs), 1))

            composite = avg_severity * max_severity * materiality * frequency * (1 + control_weakness)
            composite = min(100.0, composite)

            result[area] = {
                "likelihood": avg_severity,
                "impact": max_severity,
                "materiality": materiality,
                "frequency": frequency,
                "control_weakness": control_weakness,
                "composite_score": composite,
                "risk_band": _risk_band(composite),
            }
        return result
