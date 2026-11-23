"""
GST thresholds and rates.

Verified 30-10-2026 against the CGST Act/Rules as on the CBIC portal (14-10-2026), the
Central Tax (Rate) notifications file, and the GSTN advisories noted below.

- s.16(4) CGST Act: ITC cannot be taken after 30 November following the end of the
  financial year of the invoice, or the annual-return date if earlier.
- Rule 37: ITC on a supply not paid for within 180 days of the invoice date must be
  reversed (proportionately) with interest in the next GSTR-3B.
- Rule 46(b): invoice serial number must be unique for a financial year.
- Rule 138: e-way bill where consignment value exceeds Rs.50,000.
- Rule 48(4) + Notf 13/2020-CT as amended (10/2023-CT): e-invoicing where aggregate
  turnover in ANY preceding financial year from 2017-18 exceeds Rs.5 crore (01-08-2023).
- GSTN advisory 05-11-2024: invoices may not be reported to the IRP more than 30 days
  after the invoice date where AATO >= Rs.10 crore, from 01-04-2025 (>= Rs.100 crore
  since 01-11-2023).
- Notf 9/2025-CT(Rate), w.e.f. 22-09-2025 ("GST 2.0"): standard slabs are 5% and 18%
  with a 40% slab for specified goods; the 12% and 28% slabs were removed (tobacco and
  pan masala stayed on the old rates plus cess for a transition period).
"""
from __future__ import annotations

from datetime import date

GST_2_EFFECTIVE = date(2025, 9, 22)

# Total GST rates (CGST+SGST or IGST) in force — merchant-export 0.1% included
RATES_BEFORE_GST2 = {0.0, 0.1, 0.25, 1.5, 3.0, 5.0, 6.0, 12.0, 18.0, 28.0}
RATES_FROM_GST2 = {0.0, 0.1, 0.25, 1.5, 3.0, 5.0, 18.0, 40.0}
LEGACY_SLABS = {12.0, 28.0}

EWAY_BILL_THRESHOLD = 50_000
RULE_37_DAYS = 180

# (effective from, AATO threshold in rupees) — e-invoice applicability history
E_INVOICE_THRESHOLDS = [
    (date(2020, 10, 1), 5_000_000_000),
    (date(2021, 1, 1), 1_000_000_000),
    (date(2021, 4, 1), 500_000_000),
    (date(2022, 4, 1), 200_000_000),
    (date(2022, 10, 1), 100_000_000),
    (date(2023, 8, 1), 50_000_000),
]

# (effective from, AATO at or above which the 30-day IRP reporting limit applies)
IRP_30_DAY_THRESHOLDS = [
    (date(2023, 11, 1), 1_000_000_000),
    (date(2025, 4, 1), 100_000_000),
]
IRP_REPORTING_DAYS = 30


def _threshold_on(table: list[tuple[date, int]], on: date) -> int | None:
    current = None
    for start, value in table:
        if on >= start:
            current = value
    return current


def e_invoice_threshold(on: date) -> int | None:
    """AATO above which e-invoicing applies on the given date (None before the scheme)."""
    return _threshold_on(E_INVOICE_THRESHOLDS, on)


def e_invoice_applicable(max_preceding_aato: float, on: date) -> bool:
    """Rule 48(4): turnover in any preceding FY (from 2017-18) above the threshold."""
    limit = e_invoice_threshold(on)
    return limit is not None and max_preceding_aato > limit


def irp_30_day_limit_applies(aato: float, on: date) -> bool:
    limit = _threshold_on(IRP_30_DAY_THRESHOLDS, on)
    return limit is not None and aato >= limit


def valid_rates(on: date) -> set[float]:
    return RATES_FROM_GST2 if on >= GST_2_EFFECTIVE else RATES_BEFORE_GST2


def itc_time_limit(invoice_date: date) -> date:
    """s.16(4): 30 November following the end of the invoice's financial year
    (the annual-return date, if earlier, is not known here)."""
    fy_end_year = invoice_date.year + 1 if invoice_date.month >= 4 else invoice_date.year
    return date(fy_end_year, 11, 30)
