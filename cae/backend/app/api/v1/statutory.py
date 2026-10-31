"""Statutory applicability, MSME interest, SA 530 sampling and Form 3CD clause 44.

All figures come from the deterministic functions in app.statutory; nothing here is
estimated by a model. Each response names the provisions and inputs it relied on.
"""
import uuid
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.statutory import clause44, companies, gst, income_tax, msme, sampling
from app.utils.rbac import get_current_user

router = APIRouter()


def _fy_turnover(db: Session, company_id: uuid.UUID) -> dict[int, float]:
    from app.models.transaction import SalesInvoice

    rows = (
        db.query(SalesInvoice.invoice_date, SalesInvoice.taxable_amount)
        .filter(SalesInvoice.company_id == company_id, SalesInvoice.status != "cancelled")
        .all()
    )
    out: dict[int, float] = {}
    for d, amt in rows:
        fy = d.year if d.month >= 4 else d.year - 1
        out[fy] = out.get(fy, 0.0) + float(amt or 0)
    return out


@router.get("/section-map")
def section_map(current_user: User = Depends(get_current_user)):
    """1961 Act -> 2025 Act concordance used in exception text."""
    return {
        "income_tax_act_2025_effective": income_tax.ITA_2025_EFFECTIVE.isoformat(),
        "sections": [{"key": k, "act_1961": old, "act_2025": new, "subject": subject}
                     for k, (old, new, subject) in income_tax.CONCORDANCE.items()],
    }


class ApplicabilityIn(BaseModel):
    company_id: uuid.UUID
    balance_sheet_date: date
    paid_up_capital: float
    company_type: Literal["private", "public", "opc", "section8", "banking", "insurance"] = "private"
    reserves_and_surplus: float = 0.0
    is_holding: bool = False
    is_subsidiary: bool = False
    governed_by_special_act: bool = False
    is_subsidiary_or_holding_of_public: bool = False
    peak_bank_borrowings: float = 0.0
    peak_total_borrowings: float = 0.0
    filing_default: bool = False
    preceding_year_turnover: Optional[float] = Field(None, description="Default: books, FY before the BS date")
    total_revenue: Optional[float] = Field(None, description="Revenue from operations + other income. Default: books turnover")
    latest_audited_turnover: Optional[float] = None


@router.post("/applicability")
def applicability(body: ApplicabilityIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    turnover = _fy_turnover(db, body.company_id)
    bs_fy = body.balance_sheet_date.year if body.balance_sheet_date.month >= 4 else body.balance_sheet_date.year - 1
    sources = {}

    def pick(name, supplied, books_value):
        sources[name] = "supplied" if supplied is not None else "books (sales register, taxable value)"
        return float(supplied) if supplied is not None else float(books_value)

    preceding = pick("preceding_year_turnover", body.preceding_year_turnover, turnover.get(bs_fy - 1, 0.0))
    revenue = pick("total_revenue", body.total_revenue, turnover.get(bs_fy, 0.0))
    audited = pick("latest_audited_turnover", body.latest_audited_turnover, turnover.get(bs_fy - 1, 0.0))
    facts = companies.CompanyFacts(
        balance_sheet_date=body.balance_sheet_date, paid_up_capital=body.paid_up_capital,
        preceding_year_turnover=preceding, company_type=body.company_type, is_holding=body.is_holding,
        is_subsidiary=body.is_subsidiary, governed_by_special_act=body.governed_by_special_act,
        reserves_and_surplus=body.reserves_and_surplus, peak_bank_borrowings=body.peak_bank_borrowings,
        peak_total_borrowings=body.peak_total_borrowings, total_revenue=revenue,
        latest_audited_turnover=audited, is_subsidiary_or_holding_of_public=body.is_subsidiary_or_holding_of_public,
        filing_default=body.filing_default,
    )
    max_prior = max([v for y, v in turnover.items() if 2017 <= y < bs_fy], default=0.0)

    def as_dict(a: companies.Applicability):
        return {"applies": a.applies, "reasons": a.reasons}

    return {
        "balance_sheet_date": body.balance_sheet_date.isoformat(),
        "inputs": {"preceding_year_turnover": preceding, "total_revenue": revenue,
                   "latest_audited_turnover": audited, "sources": sources},
        "small_company": as_dict(companies.small_company(facts)),
        "caro_2020": as_dict(companies.caro_2020(facts)),
        "ifc_reporting_143_3_i": as_dict(companies.ifc_reporting(facts)),
        "e_invoicing": {
            "applies": gst.e_invoice_applicable(max_prior, body.balance_sheet_date),
            "reasons": [f"Highest preceding-year turnover in books Rs.{max_prior:,.0f} vs threshold "
                        f"Rs.{gst.e_invoice_threshold(body.balance_sheet_date):,} (Rule 48(4))"],
        },
        "irp_30_day_reporting_limit": {
            "applies": gst.irp_30_day_limit_applies(preceding, body.balance_sheet_date),
            "reasons": ["GSTN advisory 05-11-2024: AATO Rs.10 cr or more, from 01-04-2025"],
        },
        "electronic_payment_facility": {
            "applies": preceding > income_tax.ELECTRONIC_PAYMENT_FACILITY_TURNOVER,
            "reasons": [f"{income_tax.section_ref('electronic_payment_facility', body.balance_sheet_date)}: "
                        f"preceding-year turnover Rs.{preceding:,.0f} vs Rs.50 crore"],
        },
        "note": "Applicability is staged for the auditor's review — confirm thresholds against the notification in force for the year.",
    }


@router.get("/msme-interest")
def msme_interest(
    company_id: uuid.UUID,
    as_on: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bill-wise MSMED s.16 interest and the s.37(2)(g) / 43B(h) amount unpaid beyond the s.15 limit."""
    from app.models.master import Vendor
    from app.models.transaction import PurchaseInvoice

    rows = (
        db.query(PurchaseInvoice, Vendor)
        .join(Vendor, Vendor.id == PurchaseInvoice.vendor_id)
        .filter(PurchaseInvoice.company_id == company_id, PurchaseInvoice.status != "cancelled",
                func.lower(Vendor.msme_status).in_(["micro", "small"]))
        .all()
    )
    if as_on is None:
        as_on = max((p.invoice_date for p, _ in rows), default=date.today())
    fy = as_on.year if as_on.month >= 4 else as_on.year - 1
    fy_start = date(fy, 4, 1)
    bills, total_interest, unpaid_beyond_limit = [], 0.0, 0.0
    # s.43B(h) / s.37(2)(g): an MSE sum is deductible only when paid, unless paid within the s.15
    # limit. For the year ending on as_on that means bills OF THIS YEAR unpaid at year-end with the
    # limit already passed; earlier years' bills were disallowed in their own year (deductible when
    # paid); bills before 01-04-2023 predate the provision. Expense value = taxable value where ITC
    # is taken (GST is not expensed).
    s43 = {"this_year": 0.0, "this_year_bills": 0, "within_limit_at_year_end": 0.0, "within_limit_bills": 0,
           "earlier_years_unpaid": 0.0, "before_provision_unpaid": 0.0}
    for p, v in rows:
        if p.invoice_date > as_on:
            continue
        paid_on = p.payment_date if p.status == "paid" else None
        if paid_on and paid_on > as_on:            # settled after as_on: still due on as_on
            paid_on = None
        outstanding = float(p.total_amount) if (p.status == "paid" and not paid_on) else float(p.outstanding_amount or 0)
        principal = float(p.total_amount) if paid_on else outstanding
        if principal <= 0:
            continue
        acceptance = p.receipt_date or p.invoice_date
        calc = msme.bill_interest(principal, acceptance, paid_on, as_on, v.payment_terms_days)
        if not paid_on:
            share = principal / float(p.total_amount) if float(p.total_amount or 0) else 1.0
            expense = (float(p.taxable_amount) if p.itc_eligible else float(p.total_amount)) * share
            if p.invoice_date < msme.S43BH_FROM:
                s43["before_provision_unpaid"] += expense
            elif p.invoice_date < fy_start:
                s43["earlier_years_unpaid"] += expense
            elif calc["delay_days"] > 0:
                s43["this_year"] += expense
                s43["this_year_bills"] += 1
            else:
                s43["within_limit_at_year_end"] += expense
                s43["within_limit_bills"] += 1
        if calc["delay_days"] <= 0:
            continue
        total_interest += calc["interest"]
        if not paid_on:
            unpaid_beyond_limit += principal
        bills.append({"vendor": v.name, "msme_status": v.msme_status, "invoice_number": p.invoice_number,
                      "invoice_date": p.invoice_date.isoformat(), "principal": principal, "paid_on": paid_on.isoformat() if paid_on else None,
                      **{k: val for k, val in calc.items() if k != "segments"}})
    bills.sort(key=lambda b: -b["interest"])
    return {
        "as_on": as_on.isoformat(),
        "bills": bills,
        "total_interest_s16": round(total_interest, 2),
        "unpaid_beyond_s15_limit": round(unpaid_beyond_limit, 2),
        "s43bh": {"financial_year": f"{fy}-{str(fy + 1)[-2:]}", **{k: round(val, 2) if isinstance(val, float) else val
                                                                   for k, val in s43.items()}},
        "disallowance_ref": income_tax.section_ref("msme_disallowance", as_on),
        "notes": ["Interest u/s 16 is not deductible (s.23 MSMED) and is disclosed under s.22 MSMED / Form 3CD.",
                  "Disallowance = this year's bills unpaid at year-end beyond the s.15 limit, at expense value (taxable value "
                  "where ITC is taken). Bills still within the limit at year-end are allowed only if paid by their due date.",
                  "Bank rate table in app/statutory/msme.py — confirm the latest RBI rate before signing."],
    }


class SampleIn(BaseModel):
    company_id: uuid.UUID
    population: Literal["sales_invoices", "purchase_invoices", "journal_entries", "exceptions"]
    seed: int
    n: int = Field(25, ge=0, le=1000)
    high_value_threshold: float = 0.0
    date_from: Optional[date] = None
    date_to: Optional[date] = None


@router.post("/sample")
def sample(body: SampleIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Deterministic SA 530 sample — record the seed in the working paper."""
    from app.models.audit import AuditException
    from app.models.transaction import JournalEntry, PurchaseInvoice, SalesInvoice

    model, amount_col, date_col, ref_col = {
        "sales_invoices": (SalesInvoice, SalesInvoice.total_amount, SalesInvoice.invoice_date, SalesInvoice.invoice_number),
        "purchase_invoices": (PurchaseInvoice, PurchaseInvoice.total_amount, PurchaseInvoice.invoice_date, PurchaseInvoice.invoice_number),
        "journal_entries": (JournalEntry, JournalEntry.total_debit, JournalEntry.entry_date, JournalEntry.voucher_number),
        "exceptions": (AuditException, AuditException.financial_impact, AuditException.detected_on, AuditException.title),
    }[body.population]
    q = db.query(model.id, ref_col, date_col, amount_col).filter(model.company_id == body.company_id)
    if body.date_from:
        q = q.filter(date_col >= body.date_from)
    if body.date_to:
        q = q.filter(date_col <= body.date_to)
    population = [{"id": str(i), "reference": ref, "date": d.isoformat() if d else None, "amount": float(a or 0)}
                  for i, ref, d, a in q.all()]
    if not population:
        raise HTTPException(status_code=404, detail="Population is empty for the filters given")
    return {"population_source": body.population, "filters": {"from": body.date_from, "to": body.date_to},
            **sampling.select(population, body.seed, body.n, body.high_value_threshold)}


@router.get("/clause44")
def clause_44(
    company_id: uuid.UUID,
    fy: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Form 3CD clause 44 draft for FY fy-(fy+1), per ICAI GN para 79. Purchases carry their
    vendor's GSTIN; payroll is Schedule III; journal debits to expense accounts have no party
    and are shown as 'unattributed' until allocated."""
    from app.models.master import GLAccount, Vendor
    from app.models.transaction import JournalEntry, JournalEntryLine, PayrollRecord, PurchaseInvoice

    start, end = date(fy, 4, 1), date(fy + 1, 3, 31)
    lines: list[clause44.ExpenseLine] = []
    purchases = (
        db.query(PurchaseInvoice, Vendor)
        .outerjoin(Vendor, Vendor.id == PurchaseInvoice.vendor_id)
        .filter(PurchaseInvoice.company_id == company_id, PurchaseInvoice.status != "cancelled",
                PurchaseInvoice.invoice_date.between(start, end))
        .all()
    )
    for p, v in purchases:
        lines.append(clause44.ExpenseLine("Purchases", float(p.taxable_amount or 0),
                                          p.vendor_gstin or (v.gstin if v else None), v.name if v else None,
                                          composition=bool(v is not None and getattr(v, "is_composition", False))))
    payroll_total = (
        db.query(func.coalesce(func.sum(PayrollRecord.gross_earnings), 0))
        .filter(PayrollRecord.company_id == company_id,
                (PayrollRecord.pay_period_year * 100 + PayrollRecord.pay_period_month).between(fy * 100 + 4, (fy + 1) * 100 + 3))
        .scalar()
    )
    if payroll_total:
        lines.append(clause44.ExpenseLine("Salaries and wages", float(payroll_total)))
    expenses = (
        db.query(JournalEntryLine.account_name, func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount))
        .join(JournalEntry, JournalEntry.id == JournalEntryLine.journal_entry_id)
        .join(GLAccount, GLAccount.id == JournalEntryLine.account_id)
        .filter(JournalEntry.company_id == company_id, JournalEntry.entry_date.between(start, end),
                func.lower(GLAccount.account_type) == "expense")
        .group_by(JournalEntryLine.account_name)
        .all()
    )
    for name, amount in expenses:
        if amount and float(amount) > 0:
            lines.append(clause44.ExpenseLine(name, float(amount)))
    return {"financial_year": f"{fy}-{str(fy + 1)[-2:]}", "basis": "ICAI GN on Tax Audit (Revised 2025), para 79",
            **clause44.compute(lines)}
