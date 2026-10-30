"""
Income-tax: the 1961 Act -> 2025 Act switch, section concordance and thresholds.

The Income-tax Act, 2025 applies from 01-04-2026 (tax year 2026-27 onwards). A
transaction dated before that keeps its 1961 Act reference; one dated on or after it
gets the 2025 Act section, with the 1961 equivalent shown alongside.

Verified 30-10-2026 against "Income-tax Act 2025 (amended to 25-08-2026)" as printed
from incometaxindia.gov.in:
  s.36(4)/(6)  cash expenditure > Rs.10,000 a day to a person (Rs.35,000 for plying,
               hiring or leasing goods carriages)           [1961: s.40A(3)]
  s.36(2)      excessive payments to specified persons      [1961: s.40A(2)]
  s.37(2)(g)   MSME dues beyond MSMED s.15 time limit       [1961: s.43B(h)]
  s.37(2)(b)   employer contribution to PF/other funds      [1961: s.43B(b)]
  s.29(1)(e)   employee contribution — allowed if credited by the s.263(1) return due
               date (substituted by Act 4 of 2026 w.e.f. 01-04-2026) [1961: s.36(1)(va)]
  s.185        cash loans/deposits Rs.20,000 or more        [1961: s.269SS]
  s.186        cash receipts Rs.2,00,000 or more            [1961: s.269ST]
  s.188        cash repayment of loans Rs.20,000 or more    [1961: s.269T]
  s.393(1) Table — TDS on resident payments:
      Sl.1(ii) commission/brokerage, 2%, Rs.20,000          [194H]
      Sl.2(ii) rent by specified person, 2%/10%, Rs.50,000 a month [194-I]
      Sl.6(i)  contractors, 1%/2%, Rs.30,000 single / Rs.1,00,000 aggregate [194C]
      Sl.6(iii) professional 10% / technical 2%, Rs.50,000  [194J]
      Sl.8(ii) purchase of goods > Rs.50 lakh, 0.1% on the excess [194Q]
"""
from __future__ import annotations

from datetime import date

ITA_2025_EFFECTIVE = date(2026, 4, 1)

# key -> (1961 Act reference, 2025 Act reference, short description)
CONCORDANCE: dict[str, tuple[str, str, str]] = {
    "cash_expenditure":      ("s.40A(3)",    "s.36(4)",               "Cash expenditure above the daily limit"),
    "cash_expenditure_transport": ("s.40A(3) proviso", "s.36(6)",     "Rs.35,000 limit for goods-carriage hire"),
    "related_party_excess":  ("s.40A(2)",    "s.36(2)",               "Excessive payment to specified person"),
    "msme_disallowance":     ("s.43B(h)",    "s.37(2)(g)",            "MSME dues paid beyond MSMED s.15 limit"),
    "employer_contribution": ("s.43B(b)",    "s.37(2)(b)",            "Employer PF/ESI contribution"),
    "employee_contribution": ("s.36(1)(va)", "s.29(1)(e)",            "Employee PF/ESI contribution"),
    "cash_loan_accept":      ("s.269SS",     "s.185",                 "Cash loan/deposit accepted"),
    "cash_receipt":          ("s.269ST",     "s.186",                 "Cash receipt Rs.2 lakh or more"),
    "cash_loan_repay":       ("s.269T",      "s.188",                 "Cash repayment of loan/deposit"),
    "tds_commission":        ("s.194H",      "s.393(1) Table Sl.1(ii)",  "TDS — commission/brokerage"),
    "tds_rent":              ("s.194-I",     "s.393(1) Table Sl.2(ii)",  "TDS — rent"),
    "tds_contract":          ("s.194C",      "s.393(1) Table Sl.6(i)",   "TDS — contractors"),
    "tds_professional":      ("s.194J",      "s.393(1) Table Sl.6(iii)", "TDS — professional/technical fees"),
    "tds_goods":             ("s.194Q",      "s.393(1) Table Sl.8(ii)",  "TDS — purchase of goods"),
}

# Old TDS section labels (as stored in purchase_invoices.tds_section) -> concordance key
TDS_SECTION_KEYS = {
    "194H": "tds_commission",
    "194I": "tds_rent", "194-I": "tds_rent",
    "194C": "tds_contract",
    "194J": "tds_professional",
    "194Q": "tds_goods",
}

# Minimum rate in each TDS entry (the lower of the alternatives) — used only to flag
# short deduction; a payee-specific higher rate can still be short and is not caught.
TDS_MIN_RATE = {
    "tds_commission": 0.02,
    "tds_rent": 0.02,
    "tds_contract": 0.01,
    "tds_professional": 0.02,
    "tds_goods": 0.001,
}

CASH_EXPENDITURE_LIMIT = 10_000          # s.36(4) / 40A(3), per person per day
CASH_EXPENDITURE_LIMIT_TRANSPORT = 35_000  # s.36(6) / 40A(3) proviso
CASH_RECEIPT_LIMIT = 200_000             # s.186 / 269ST — "Rs. 200000 or more"
CASH_LOAN_LIMIT = 20_000                 # s.185 / 269SS and s.188 / 269T — "Rs. 20000 or more"
TDS_GOODS_THRESHOLD = 5_000_000          # s.393(1) Sl.8(ii) / 194Q — on the excess over Rs.50 lakh
ELECTRONIC_PAYMENT_FACILITY_TURNOVER = 500_000_000  # s.187 / 269SU — preceding-year turnover > Rs.50 cr


def under_2025_act(on: date) -> bool:
    return on >= ITA_2025_EFFECTIVE


def section_ref(key: str, on: date) -> str:
    """Section reference correct for the transaction date, e.g.
    's.36(4) of the Income-tax Act, 2025 (earlier s.40A(3) of the 1961 Act)'."""
    old, new, _ = CONCORDANCE[key]
    if under_2025_act(on):
        return f"{new} of the Income-tax Act, 2025 (earlier {old} of the 1961 Act)"
    return f"{old} of the Income-tax Act, 1961"


def tax_year(on: date) -> str:
    """Indian financial / tax year label, e.g. date(2026, 5, 1) -> '2026-27'."""
    start = on.year if on.month >= 4 else on.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def fy_start(on: date) -> date:
    return date(on.year if on.month >= 4 else on.year - 1, 4, 1)
