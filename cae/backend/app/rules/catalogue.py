"""
Rule catalogue — the single source of truth for which rules exist, their names,
categories and default parameters. The seed script and sync_rules() both read this,
and a test asserts every catalogue entry has a registered function (and vice versa).

Categories map to the risk engine's business areas.
"""
from __future__ import annotations

import uuid

# code, name, category, risk_area, severity, frequency, default parameters
RULE_CATALOGUE: list[tuple[str, str, str, str, str, str, dict]] = [
    ("SAL-001", "Duplicate Invoice Number in a Financial Year", "revenue", "Fraud", "critical", "daily", {}),
    ("SAL-002", "Round Amount Invoice", "revenue", "Fraud", "medium", "daily", {"min_amount": 100000, "multiple": 1000}),
    ("SAL-003", "Monthly Sales Spike", "revenue", "Financial Reporting", "high", "monthly", {"sigma": 3, "min_months": 6}),
    ("SAL-004", "Revenue Cut-Off Manipulation", "revenue", "Financial Reporting", "critical", "monthly", {"grace_days": 5, "min_amount": 100000}),
    ("SAL-005", "Excessive Discount", "revenue", "Revenue Leakage", "high", "daily", {"max_discount_pct": 15}),
    ("SAL-007", "Missing E-Way Bill", "gst", "GST", "high", "daily", {"threshold": 50000}),
    ("SAL-009", "Manual Invoice Override", "revenue", "Authorization", "critical", "daily", {"min_amount": 100000}),
    ("SAL-010", "Credit Limit Breach", "revenue", "Financial", "high", "daily", {}),
    ("SAL-016", "Invoice Cancellation Abuse", "revenue", "Fraud", "high", "monthly", {"max_cancellations_per_month": 5}),
    ("SAL-019", "Weekend Invoicing", "revenue", "Fraud", "medium", "daily", {"min_amount": 500000}),
    ("SAL-021", "E-Invoice IRN Missing", "gst", "GST", "high", "daily", {}),
    ("SAL-022", "Cash Receipt of Rs.2 Lakh or More", "statutory", "Compliance", "critical", "daily", {"threshold": 200000}),
    ("SAL-034", "Duplicate Sale Same Customer-Day-Amount", "revenue", "Fraud", "critical", "daily", {}),
    ("PUR-001", "Duplicate Vendor Invoice", "expenditure", "Fraud", "critical", "daily", {}),
    ("PUR-002", "PO-Invoice Amount Mismatch", "expenditure", "Authorization", "high", "daily", {"tolerance_pct": 5}),
    ("PUR-004", "Invoice Without PO", "expenditure", "Authorization", "high", "daily", {"min_amount": 100000}),
    ("PUR-006", "Split Purchases Below Approval Limit", "expenditure", "Authorization", "high", "monthly",
     {"approval_limit": 100000, "window_days": 7, "min_count": 3}),
    ("PUR-010", "Payment to Account Not in Vendor Master", "expenditure", "Fraud", "critical", "daily", {}),
    ("PUR-013", "Large Invoice Without Approval or PO", "expenditure", "Authorization", "high", "daily", {"min_amount": 500000}),
    ("PUR-016", "Possible Duplicate Payment", "expenditure", "Fraud", "critical", "daily", {"window_days": 30}),
    ("PUR-021", "GRN Dated Before Supplier Invoice", "expenditure", "Financial Reporting", "high", "daily", {"min_amount": 100000}),
    ("PUR-022", "Vendor Shares Bank Account or PAN with Employee", "related_party", "Fraud", "critical", "daily", {}),
    ("PUR-031", "MSME Payment Beyond s.15 Limit", "statutory", "Compliance", "high", "weekly", {}),
    ("GST-001", "Removed GST Slab After 22-09-2025", "gst", "GST", "high", "daily", {"rate_tolerance": 0.05}),
    ("GST-002", "Rule 37 ITC Reversal — Supplier Unpaid 180 Days", "gst", "GST", "high", "weekly", {}),
    ("GST-003", "ITC Booked After s.16(4) Time Limit", "gst", "GST", "high", "monthly", {}),
    ("TDS-001", "TDS on Purchase of Goods Not Deducted", "statutory", "Compliance", "high", "monthly", {}),
    ("TDS-002", "TDS Short-Deducted", "statutory", "Compliance", "medium", "monthly", {"tolerance": 1}),
    ("INV-001", "Negative Stock Balance", "inventory", "Operational", "critical", "daily", {}),
    ("INV-002", "Inventory Shrinkage Above Limit", "inventory", "Fraud", "high", "monthly", {"max_shrinkage_pct": 2}),
    ("INV-005", "Slow Moving Stock", "inventory", "Working Capital", "medium", "monthly", {"max_idle_days": 180}),
    ("INV-007", "Ghost Inventory", "inventory", "Fraud", "critical", "monthly", {"min_value": 500000, "max_movements": 2}),
    ("INV-010", "Weekend Inventory Movement", "inventory", "Fraud", "high", "daily", {"min_value": 200000}),
    ("INV-015", "Multiple GRNs on One Reference", "inventory", "Fraud", "high", "daily", {"max_grns": 2}),
    ("JE-001", "Manual JE Without Narration", "financial_reporting", "Financial Reporting", "high", "daily", {"min_amount": 100000}),
    ("JE-002", "Late-Posted JE", "financial_reporting", "Financial Reporting", "critical", "monthly", {"max_days": 10}),
    ("JE-003", "Large Manual JE", "financial_reporting", "Authorization", "high", "daily", {"min_amount": 1000000}),
    ("JE-005", "Uncleared Suspense Account", "financial_reporting", "Financial Reporting", "high", "weekly", {"max_days": 30}),
    ("JE-006", "Orphan Reversal", "financial_reporting", "Fraud", "critical", "daily", {}),
    ("JE-009", "Unbalanced Journal Entry", "financial_reporting", "Financial Reporting", "critical", "daily", {}),
    ("JE-011", "Single-User High-Volume JE Posting", "financial_reporting", "Authorization", "critical", "daily", {"min_count": 10}),
    ("JE-015", "Prior Period JE", "financial_reporting", "Financial Reporting", "high", "monthly", {}),
    ("PAY-001", "Ghost Employee", "payroll", "Fraud", "critical", "monthly", {}),
    ("PAY-002", "Salary Spike Month-on-Month", "payroll", "Authorization", "high", "monthly", {"max_increase_pct": 50}),
    ("PAY-003", "Duplicate Bank Account in Payroll", "payroll", "Fraud", "critical", "monthly", {}),
    ("PAY-004", "Post-Termination Pay", "payroll", "Fraud", "critical", "monthly", {}),
    ("PAY-005", "PF/ESI Not Deposited by Due Date", "statutory", "Compliance", "high", "monthly", {"amount_tolerance_pct": 5}),
    ("PAY-009", "High Payroll Deductions", "payroll", "Fraud", "medium", "monthly", {"max_deduction_share": 0.33}),
    ("TRE-001", "Cash Payment Above Daily Limit", "statutory", "Compliance", "high", "daily", {"tax_rate": 0.25168}),
    ("TRE-002", "Circular Bank Transfer", "bank_reconciliation", "Fraud", "critical", "daily", {"window_days": 2}),
    ("TRE-003", "Cash Loan Taken or Repaid", "statutory", "Compliance", "critical", "daily", {}),
    ("TRE-004", "Unreferenced Transfer Above Limit", "bank_reconciliation", "Authorization", "critical", "daily", {"min_amount": 500000}),
    ("TRE-005", "Multiple Payments Same Party Day", "bank_reconciliation", "Fraud", "high", "daily", {"min_count": 3}),
    ("TRE-006", "Director/Loan Payment", "related_party", "Fraud", "critical", "daily", {"min_amount": 100000}),
    ("TRE-010", "Structured Cash Withdrawal", "bank_reconciliation", "Fraud", "critical", "daily", {}),
]

CATALOGUE_BY_CODE = {row[0]: row for row in RULE_CATALOGUE}


def sync_rules(db, company_id) -> dict:
    """Create missing catalogue rules for a company and refresh names/categories of existing
    ones. User-set parameters and is_active flags are kept; only missing parameter keys are
    filled with catalogue defaults."""
    from app.models.audit import AuditRule

    company_uuid = uuid.UUID(str(company_id))
    existing = {r.rule_code: r for r in db.query(AuditRule).filter(AuditRule.company_id == company_uuid).all()}
    created, updated = 0, 0
    for code, name, category, risk_area, severity, frequency, defaults in RULE_CATALOGUE:
        rule = existing.get(code)
        if rule is None:
            db.add(AuditRule(
                id=uuid.uuid4(), company_id=company_uuid, rule_code=code, rule_name=name,
                category=category, risk_area=risk_area, severity=severity, run_frequency=frequency,
                rule_type="python", is_active=True, auto_raise_exception=True,
                parameters=dict(defaults) or None,
                description=f"Detects {name.lower()} in {category.replace('_', ' ')} data.",
                remediation_guidance=f"Review and obtain documentation for {name}. Escalate if unresolved within 7 days.",
            ))
            created += 1
            continue
        merged = {**defaults, **(rule.parameters or {})}
        if (rule.rule_name, rule.category, rule.risk_area, rule.parameters or {}) != (name, category, risk_area, merged):
            rule.rule_name, rule.category, rule.risk_area = name, category, risk_area
            rule.parameters = merged or None
            updated += 1
    db.commit()
    return {"created": created, "updated": updated, "catalogue_size": len(RULE_CATALOGUE)}
