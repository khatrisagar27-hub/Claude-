"""Statutory constants and validators — the single place a threshold or rate lives.

Every figure here carries the provision it comes from. Rates and limits change
with each Finance Act and notification: VERIFY against the current law before
relying on a finding, and change the number here (or the rule parameter on the
engagement), never inside a rule.

Income-tax references are to the Income-tax Act, 1961. Tax years beginning on or
after 1 April 2026 fall under the Income-tax Act, 2025, which re-numbers these
provisions; ITA_2025 below maps them and is UNVERIFIED — confirm each reference
against the bare Act before it goes into a report.
"""
import re
from datetime import date

# ── Income-tax: cash and loan limits ──
CASH_PAYMENT_LIMIT = 10_000          # s.40A(3): per person per day; disallowed in full above this
CASH_PAYMENT_LIMIT_TRANSPORT = 35_000  # s.40A(3A) second proviso: plying/hiring goods carriages
CASH_RECEIPT_LIMIT = 200_000         # s.269ST: Rs 2 lakh or more; penalty s.271DA = amount received
CASH_LOAN_LIMIT = 20_000             # s.269SS / s.269T: loan or deposit taken/repaid otherwise than by banking channel
CASH_WITHDRAWAL_TDS_LIMIT = 10_000_000  # s.194N: aggregate cash withdrawal above Rs 1 crore in a year, TDS 2%

ITA_2025 = {  # UNVERIFIED mapping, shown as "verify" wherever it is displayed
    "s.40A(3)": "s.36", "s.43B(h)": "s.37", "s.269SS": "s.185", "s.269ST": "s.186",
    "s.269T": "s.188", "s.194C": "s.393", "s.194J": "s.393", "s.194I": "s.393",
    "s.194H": "s.393", "s.194A": "s.393", "s.194Q": "s.393", "s.194N": "s.393", "s.206AA": "s.397",
}
ITA_2025_START = date(2026, 4, 1)

# ── GST ──
EWAY_BILL_LIMIT = 50_000             # CGST Rule 138(1): consignment value exceeding Rs 50,000
ITC_PAYMENT_DAYS = 180               # s.16(2) second proviso r/w Rule 37: pay supplier within 180 days of invoice
# s.17(5) blocked credits, matched against purchase "nature".
BLOCKED_CREDIT_NATURES = {"motor_vehicle", "food_beverage", "club_membership", "health_insurance",
                          "personal", "works_contract_immovable", "gift"}

# ── MSMED Act, 2006 ──
MSME_DAYS_WITH_AGREEMENT = 45        # s.15: agreed period, never beyond 45 days from acceptance
MSME_DAYS_NO_AGREEMENT = 15          # s.15: 15 days where there is no written agreement
MSME_CATEGORIES_43BH = {"micro", "small"}  # s.43B(h) ITA 1961 covers micro and small enterprises only

# ── Payroll ──
PF_RATE = 0.12                       # EPF Scheme para 29: employee contribution 12% of basic + DA
PF_WAGE_CEILING = 15_000             # EPF Scheme para 2(f): employees up to Rs 15,000 must be covered
ESI_WAGE_CEILING = 21_000            # ESI (Central) Rules, rule 50: wages up to Rs 21,000 per month
ESI_EMPLOYEE_RATE = 0.0075           # ESI rule 51 (w.e.f. 1 July 2019): employee 0.75%

# ── TDS on payments to residents ──
# Each nature has dated versions; the one in force on the invoice date applies.
# rate_ind applies when the deductee PAN's 4th character is P (individual) or H (HUF).
# basis: "single_or_aggregate" (194C), "aggregate" (yearly), "monthly" (194I from 1 Apr 2025),
#        "excess" (194Q: only on purchases above the limit).
TDS_NATURES = {
    "contract": [dict(frm=date(2000, 1, 1), section="s.194C", basis="single_or_aggregate",
                      single=30_000, limit=100_000, rate=2.0, rate_ind=1.0)],
    "professional": [dict(frm=date(2000, 1, 1), section="s.194J", basis="aggregate", limit=30_000, rate=10.0),
                     dict(frm=date(2025, 4, 1), section="s.194J", basis="aggregate", limit=50_000, rate=10.0)],
    "technical": [dict(frm=date(2020, 4, 1), section="s.194J", basis="aggregate", limit=30_000, rate=2.0),
                  dict(frm=date(2025, 4, 1), section="s.194J", basis="aggregate", limit=50_000, rate=2.0)],
    "rent": [dict(frm=date(2019, 4, 1), section="s.194I", basis="aggregate", limit=240_000, rate=10.0),
             dict(frm=date(2025, 4, 1), section="s.194I", basis="monthly", limit=50_000, rate=10.0)],
    "rent_machinery": [dict(frm=date(2019, 4, 1), section="s.194I", basis="aggregate", limit=240_000, rate=2.0),
                       dict(frm=date(2025, 4, 1), section="s.194I", basis="monthly", limit=50_000, rate=2.0)],
    "commission": [dict(frm=date(2016, 6, 1), section="s.194H", basis="aggregate", limit=15_000, rate=5.0),
                   dict(frm=date(2024, 10, 1), section="s.194H", basis="aggregate", limit=15_000, rate=2.0),
                   dict(frm=date(2025, 4, 1), section="s.194H", basis="aggregate", limit=20_000, rate=2.0)],
    "interest": [dict(frm=date(2000, 1, 1), section="s.194A", basis="aggregate", limit=5_000, rate=10.0),
                 dict(frm=date(2025, 4, 1), section="s.194A", basis="aggregate", limit=10_000, rate=10.0)],
    # Applies only where the buyer's turnover exceeded Rs 10 crore in the preceding year
    # (engagement setting tds_194q_applicable).
    "goods": [dict(frm=date(2021, 7, 1), section="s.194Q", basis="excess", limit=5_000_000, rate=0.1)],
}
TDS_RATE_NO_PAN = 20.0               # s.206AA: higher of the section rate and 20%
TDS_RATE_NO_PAN_194Q = 5.0           # s.206AA proviso: 5% for s.194Q


def tds_version(nature: str, on: date) -> dict | None:
    versions = [v for v in TDS_NATURES.get(nature, []) if v["frm"] <= on]
    return versions[-1] if versions else None


def law_ref(section: str, period_start: date) -> str:
    """Citation text for an Income-tax section, adding the 2025 Act where it governs."""
    text = f"Income-tax Act, 1961 {section}"
    if period_start >= ITA_2025_START and section in ITA_2025:
        text += f" / Income-tax Act, 2025 {ITA_2025[section]} (verify)"
    return text


# ── Identifier validation ──
_PAN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
_GSTIN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
_B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def clean_id(value) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()


def pan_valid(pan) -> bool:
    return bool(_PAN.match(clean_id(pan)))


def pan_is_individual_or_huf(pan) -> bool:
    pan = clean_id(pan)
    return pan_valid(pan) and pan[3] in "PH"


def gstin_valid(gstin) -> bool:
    """Format plus the check digit (15th character, mod-36 weighted sum of the first 14)."""
    gstin = clean_id(gstin)
    if not _GSTIN.match(gstin):
        return False
    total = 0
    for i, ch in enumerate(gstin[:14]):
        product = _B36.index(ch) * (2 if i % 2 else 1)
        total += product // 36 + product % 36
    return _B36[(36 - total % 36) % 36] == gstin[14]


def gstin_check_digit(first14: str) -> str:
    total = 0
    for i, ch in enumerate(first14):
        product = _B36.index(ch) * (2 if i % 2 else 1)
        total += product // 36 + product % 36
    return _B36[(36 - total % 36) % 36]


def gstin_state(gstin) -> str:
    return clean_id(gstin)[:2]


def gstin_pan(gstin) -> str:
    return clean_id(gstin)[2:12]
