"""AI explanation engine using Claude API."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.audit import AuditException


class AIEngine:
    def __init__(self):
        from app.config import settings
        self.api_key = settings.ANTHROPIC_API_KEY

    async def explain_exception(self, exception: "AuditException") -> dict:
        if not self.api_key:
            return self._fallback_explanation(exception)

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)

            prompt = self._build_prompt(exception)
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            text = message.content[0].text
            return self._parse_response(text)
        except Exception:
            return self._fallback_explanation(exception)

    def _build_prompt(self, exc: "AuditException") -> str:
        return f"""You are an expert Chartered Accountant and Internal Auditor in India. Analyze this audit exception and provide a structured response.

Exception Details:
- Rule Code: {exc.rule_id}
- Title: {exc.title}
- Category: {exc.category}
- Severity: {exc.severity}
- Description: {exc.description}
- Financial Impact: ₹{float(exc.financial_impact or 0):,.2f}
- Risk Area: {exc.risk_impact}
- Evidence: {json.dumps(exc.supporting_data or {}, indent=2)}

Provide a JSON response with these exact keys:
{{
  "explanation": "Plain English explanation of what happened and why it's concerning (2-3 sentences)",
  "business_impact": "Specific business and financial impact (1-2 sentences)",
  "fraud_risk": "Assessment of fraud risk — Low/Medium/High/Critical with rationale",
  "recommended_query": "Exact question to ask management to get clarification",
  "suggested_remediation": "Specific control improvement to prevent recurrence"
}}

Respond with only valid JSON, no markdown."""

    def _parse_response(self, text: str) -> dict:
        try:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            return json.loads(cleaned)
        except Exception:
            return {
                "explanation": text[:500],
                "business_impact": "Assessment pending manual review.",
                "fraud_risk": "Medium — automated assessment not available",
                "recommended_query": "Please provide documentation supporting this transaction.",
                "suggested_remediation": "Review internal controls for this area.",
            }

    def _fallback_explanation(self, exc: "AuditException") -> dict:
        severity_risk = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low"}
        return {
            "explanation": f"The audit rule '{exc.title}' detected an anomaly in {exc.category}. {exc.description}",
            "business_impact": f"Financial exposure estimated at ₹{float(exc.financial_impact or 0):,.2f}. Risk area: {exc.risk_impact}.",
            "fraud_risk": f"{severity_risk.get(exc.severity, 'Medium')} — based on rule severity classification.",
            "recommended_query": f"Please provide documentary evidence and business justification for the transaction(s) identified under {exc.title}.",
            "suggested_remediation": f"Strengthen controls in {exc.category} process. Implement maker-checker approval for transactions triggering {exc.title}.",
        }
