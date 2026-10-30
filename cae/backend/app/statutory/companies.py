"""
Companies Act 2013 applicability tests: small company, CARO 2020, IFC reporting.

- s.2(85) small company limits (Rule 2(1)(t), Specification of Definition Details
  Rules 2014): Rs.10 cr paid-up and Rs.100 cr preceding-year turnover from 01-12-2025
  (G.S.R. 880(E)); Rs.4 cr / Rs.40 cr from 15-09-2022; Rs.2 cr / Rs.20 cr from
  01-04-2021. A holding, subsidiary, s.8 or special-Act company is never small.
  Status is judged as at the balance sheet date (ICAI GN on CARO 2020, para 12).
- CARO 2020 para 1(2): excludes banking, insurance, s.8, OPC, small companies, and a
  private company (not a holding/subsidiary of a public company) that meets ALL of:
  paid-up capital + reserves <= Rs.1 cr at the BS date (securities premium counted,
  debit P&L netted — GN paras 18-19); bank/FI borrowings <= Rs.1 cr on every day of the
  year (GN 22-23, NBFCs count); total revenue incl. other income <= Rs.10 cr (GN 24).
  The small-company exemption wins even if the private-company test fails (GN 12).
- s.143(3)(i) IFC reporting — exempt (G.S.R. 583(E), 13-06-2017): OPC, small company,
  and a private company with turnover < Rs.50 cr per its latest audited FS or
  borrowings from banks, FIs or bodies corporate < Rs.25 cr at all times in the year,
  provided it has not defaulted in filing its FS/annual return.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

CRORE = 10_000_000

SMALL_COMPANY_LIMITS = [  # (effective from, paid-up cap, turnover cap)
    (date(2014, 4, 1), 50 * 100_000, 2 * CRORE),
    (date(2021, 4, 1), 2 * CRORE, 20 * CRORE),
    (date(2022, 9, 15), 4 * CRORE, 40 * CRORE),
    (date(2025, 12, 1), 10 * CRORE, 100 * CRORE),
]


@dataclass
class CompanyFacts:
    balance_sheet_date: date
    paid_up_capital: float
    preceding_year_turnover: float
    company_type: str = "private"          # private / public / opc / section8 / banking / insurance
    is_holding: bool = False
    is_subsidiary: bool = False
    governed_by_special_act: bool = False
    reserves_and_surplus: float = 0.0       # signed; debit P&L reduces it
    peak_bank_borrowings: float = 0.0       # highest bank/FI balance on any day in the year
    peak_total_borrowings: float = 0.0      # incl. bodies corporate (IFC test)
    total_revenue: float = 0.0              # revenue from operations + other income
    latest_audited_turnover: float = 0.0
    is_subsidiary_or_holding_of_public: bool = False
    filing_default: bool = False


@dataclass
class Applicability:
    applies: bool
    reasons: list[str] = field(default_factory=list)


def small_company_limits(on: date) -> tuple[int, int]:
    caps = [c for c in SMALL_COMPANY_LIMITS if on >= c[0]]
    _, paid_up, turnover = caps[-1]
    return paid_up, turnover


def small_company(f: CompanyFacts) -> Applicability:
    paid_cap, to_cap = small_company_limits(f.balance_sheet_date)
    reasons = [f"Limits on {f.balance_sheet_date}: paid-up <= Rs.{paid_cap:,}, turnover <= Rs.{to_cap:,}"]
    barred = []
    if f.company_type in ("public", "section8"):
        barred.append(f"{f.company_type} company")
    if f.is_holding:
        barred.append("holding company")
    if f.is_subsidiary:
        barred.append("subsidiary company")
    if f.governed_by_special_act:
        barred.append("governed by a special Act")
    if barred:
        return Applicability(False, reasons + [f"Excluded by s.2(85) proviso: {', '.join(barred)}"])
    ok_paid = f.paid_up_capital <= paid_cap
    ok_to = f.preceding_year_turnover <= to_cap
    reasons.append(f"Paid-up Rs.{f.paid_up_capital:,.0f} {'within' if ok_paid else 'exceeds'} limit")
    reasons.append(f"Preceding-year turnover Rs.{f.preceding_year_turnover:,.0f} {'within' if ok_to else 'exceeds'} limit")
    return Applicability(ok_paid and ok_to, reasons)


def caro_2020(f: CompanyFacts) -> Applicability:
    if f.company_type in ("banking", "insurance", "section8", "opc"):
        return Applicability(False, [f"CARO para 1(2): {f.company_type} company excluded"])
    small = small_company(f)
    if small.applies:
        return Applicability(False, ["Small company — excluded (GN para 12: wins over the private-company test)"] + small.reasons)
    if f.company_type != "private" or f.is_subsidiary_or_holding_of_public:
        return Applicability(True, ["Not small; public company or holding/subsidiary of a public company"])
    net_worth = f.paid_up_capital + f.reserves_and_surplus
    tests = [
        (net_worth <= CRORE, f"paid-up + reserves Rs.{net_worth:,.0f} (limit Rs.1 cr at BS date)"),
        (f.peak_bank_borrowings <= CRORE, f"peak bank/FI borrowings Rs.{f.peak_bank_borrowings:,.0f} (limit Rs.1 cr on any day)"),
        (f.total_revenue <= 10 * CRORE, f"total revenue incl. other income Rs.{f.total_revenue:,.0f} (limit Rs.10 cr)"),
    ]
    failed = [t for ok, t in tests if not ok]
    if failed:
        return Applicability(True, ["Private company fails para 1(2)(v): " + "; ".join(failed)])
    return Applicability(False, ["Private company meets all three para 1(2)(v) limits: " + "; ".join(t for _, t in tests)])


def ifc_reporting(f: CompanyFacts) -> Applicability:
    if f.company_type == "opc":
        return Applicability(False, ["OPC — exempt"])
    small = small_company(f)
    if small.applies:
        return Applicability(False, ["Small company — exempt"] + small.reasons)
    if f.company_type == "private" and not f.filing_default:
        if f.latest_audited_turnover < 50 * CRORE:
            return Applicability(False, [f"Private company, latest audited turnover Rs.{f.latest_audited_turnover:,.0f} < Rs.50 cr"])
        if f.peak_total_borrowings < 25 * CRORE:
            return Applicability(False, [f"Private company, peak borrowings Rs.{f.peak_total_borrowings:,.0f} < Rs.25 cr"])
    reason = "filing default removes the private-company exemption" if f.filing_default else "no exemption met"
    return Applicability(True, [f"s.143(3)(i) reporting required — {reason}"])
