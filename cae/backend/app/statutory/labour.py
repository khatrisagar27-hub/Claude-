"""
PF / ESI deposit due dates and their income-tax effect.

- EPF Scheme para 38 and ESI (Central) Regulations: contributions for a wage month are
  due by the 15th of the following month. The four Labour Codes (in force 21-11-2025)
  carry the same monthly cycle for EPF/ESI; check the Social Security (Central) Rules
  2026 if a client's scheme says otherwise.
- Employee contribution, tax years to 2025-26 (1961 Act s.36(1)(va) with s.2(24)(x)):
  disallowed if credited after the labour-law due date (Checkmate Fortune, SC 2022).
- From tax year 2026-27 (2025 Act s.29(1)(e), substituted by Act 4 of 2026 w.e.f.
  01-04-2026): allowed if credited by the s.263(1) return due date. Late deposit still
  attracts labour-law interest/damages.
- Employer contribution (s.43B(b) / s.37(2)(b)): allowed if paid by the return due date.
"""
from __future__ import annotations

from datetime import date

from app.statutory.income_tax import ITA_2025_EFFECTIVE

CONTRIBUTION_DUE_DAY = 15


def contribution_due_date(year: int, month: int) -> date:
    y, m = (year + 1, 1) if month == 12 else (year, month + 1)
    return date(y, m, CONTRIBUTION_DUE_DAY)


def employee_contribution_tax_test(wage_month_end: date) -> str:
    """Which deadline governs the deduction of the employee share for this wage month."""
    if wage_month_end >= ITA_2025_EFFECTIVE:
        return "return_due_date"   # s.29(1)(e), 2025 Act
    return "labour_due_date"       # s.36(1)(va), 1961 Act
