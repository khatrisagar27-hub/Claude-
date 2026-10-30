"""
MSMED Act 2006 — classification, s.15 time limit and s.16 interest.

Ported from the tally-audit skill's msme_interest.py (deterministic; the LLM never
computes this figure).

- s.15: pay by the agreed date, which cannot exceed 45 days from the day of acceptance
  (or deemed acceptance); with no agreement, within 15 days.
- s.16: on default, compound interest with monthly rests at three times the bank rate
  notified by the RBI, from the appointed day to the date of payment.
- s.15-16 protect micro and small enterprises only ("supplier", s.2(n)). Medium
  enterprises are outside s.15-16 and outside s.37(2)(g) / 43B(h).
- Classification (S.O. 2119(E) of 26-06-2020 as amended by S.O. 1364(E), w.e.f.
  01-04-2025): micro <= Rs.2.5 cr investment and <= Rs.10 cr turnover; small <= Rs.25 cr
  and <= Rs.100 cr; medium <= Rs.125 cr and <= Rs.500 cr.

Bank rate table: RBI Bank Rate (= repo + 25 bps). The latest entry comes from secondary
reports of the 07-10-2026 MPC statement — confirm against the RBI before signing.
"""
from __future__ import annotations

from datetime import date, timedelta

MAX_CREDIT_DAYS = 45
DEFAULT_CREDIT_DAYS = 15
PROTECTED_CLASSES = {"micro", "small"}

# (effective from, investment cap, turnover cap) per class
CLASSIFICATION_LIMITS = {
    "micro":  [(date(2020, 7, 1), 10_000_000, 50_000_000), (date(2025, 4, 1), 25_000_000, 100_000_000)],
    "small":  [(date(2020, 7, 1), 100_000_000, 500_000_000), (date(2025, 4, 1), 250_000_000, 1_000_000_000)],
    "medium": [(date(2020, 7, 1), 500_000_000, 2_500_000_000), (date(2025, 4, 1), 1_250_000_000, 5_000_000_000)],
}

# (effective from, RBI Bank Rate % p.a.)
BANK_RATE_HISTORY = [
    (date(2023, 2, 8), 6.75),
    (date(2025, 2, 7), 6.50),
    (date(2025, 4, 9), 6.25),
    (date(2025, 6, 6), 5.75),
    (date(2025, 12, 5), 5.50),
    (date(2026, 10, 7), 5.75),
]


def bank_rate_on(on: date) -> float:
    rate = BANK_RATE_HISTORY[0][1]
    for start, value in BANK_RATE_HISTORY:
        if on >= start:
            rate = value
    return rate


def classify(investment: float, turnover: float, on: date) -> str | None:
    """Return 'micro' / 'small' / 'medium' or None (not an MSME) under the limits in force."""
    for cls in ("micro", "small", "medium"):
        caps = [c for c in CLASSIFICATION_LIMITS[cls] if on >= c[0]]
        if not caps:
            continue
        _, inv_cap, to_cap = caps[-1]
        if investment <= inv_cap and turnover <= to_cap:
            return cls
    return None


def is_protected(msme_status: str | None) -> bool:
    return (msme_status or "").strip().lower() in PROTECTED_CLASSES


def appointed_day(acceptance: date, agreed_credit_days: int | None) -> tuple[date, int]:
    """Last day for payment under s.15 and the credit period actually applied."""
    if agreed_credit_days is None:
        credit = DEFAULT_CREDIT_DAYS
    else:
        credit = min(int(agreed_credit_days), MAX_CREDIT_DAYS)
    return acceptance + timedelta(days=credit), credit


def _add_one_month(d: date) -> date:
    y, m = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    for day in (d.day, 30, 29, 28):
        try:
            return date(y, m, day)
        except ValueError:
            continue
    return date(y, m, 28)


def compound_interest(principal: float, start: date, end: date, rate_pa: float) -> tuple[float, list[dict]]:
    """Compound interest with monthly rests, actual/365. Returns (interest, segments)."""
    if end <= start or principal <= 0:
        return 0.0, []
    balance, total, segments = principal, 0.0, []
    seg_start = start
    while seg_start < end:
        seg_end = min(_add_one_month(seg_start), end)
        days = (seg_end - seg_start).days
        interest = balance * rate_pa / 100.0 * days / 365.0
        segments.append({
            "from": seg_start.isoformat(), "to": seg_end.isoformat(), "days": days,
            "opening_balance": round(balance, 2), "interest": round(interest, 2),
        })
        total += interest
        balance += interest
        seg_start = seg_end
    return total, segments


def bill_interest(amount: float, acceptance: date, paid_on: date | None, as_on: date,
                  agreed_credit_days: int | None = None, bank_rate: float | None = None) -> dict:
    """s.16 interest on one bill. Rate = 3x the bank rate in force on the appointed day
    unless an explicit bank_rate is passed."""
    due, credit = appointed_day(acceptance, agreed_credit_days)
    end = paid_on or as_on
    rate = bank_rate if bank_rate is not None else bank_rate_on(due)
    interest, segments = compound_interest(amount, due, end, 3.0 * rate)
    return {
        "appointed_day": due.isoformat(),
        "credit_days_applied": credit,
        "end_date": end.isoformat(),
        "delay_days": max((end - due).days, 0),
        "bank_rate": rate,
        "rate_pa": 3.0 * rate,
        "interest": round(interest, 2),
        "segments": segments,
    }
