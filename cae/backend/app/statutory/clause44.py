"""
Form 3CD clause 44 — break-up of expenditure by GST registration status, per the ICAI
Guidance Note on Tax Audit (Revised 2025), para 79.

Column 2 = total P&L expenditure (incl. purchases and non-cash charges) + capital
expenditure (79.1, 79.2, 79.18). Columns 3-7 cover only expenditure that is a "supply"
under s.7 CGST (79.3). The 79.4 working removes, from column 2:
  - non-cash charges (depreciation, provisions, write-offs),
  - transactions in money and securities,
  - Schedule III items (employee remuneration, Sch III para 1).
Column 3 (exempt) includes non-taxable supplies such as petrol, HSD and alcohol (79.11).
An exempt supply from an unregistered person goes to column 7. Composition status (col 4)
cannot be seen from books; it is reported with a 3CB remark (79.13), so it stays 0 here
unless the vendor master says otherwise.

Classification of expense heads is keyword-based on the account/ledger name and is a
STARTING POINT for the auditor — the 79.20 vendor-wise table is the evidence.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")

# head -> treatment; first matching pattern wins (order matters)
HEAD_RULES: list[tuple[str, str]] = [
    (r"depreciation|amorti[sz]ation|provision|written off|write.?off|impairment", "non_cash"),
    (r"salary|salaries|wages|bonus|gratuity|leave encashment|staff welfare|director.?s? remuneration|employee", "schedule_iii"),
    (r"income.?tax|gst paid|stamp duty|property tax|municipal|rates and taxes|\bcess\b|penalty|interest on (tds|gst|tax)", "statutory_levy"),
    (r"loss on (sale|redemption) of (shares|securities|investments)|forex|exchange (loss|difference)", "money_or_securities"),
    (r"petrol|diesel|\bhsd\b|motor spirit|natural gas|aviation turbine|alcohol|liquor", "exempt_non_taxable"),
    (r"interest|bank guarantee commission", "exempt"),
]


def classify_head(account_name: str) -> str:
    name = (account_name or "").lower()
    for pattern, treatment in HEAD_RULES:
        if re.search(pattern, name):
            return treatment
    return "supply"


@dataclass
class ExpenseLine:
    account_name: str
    amount: float
    vendor_gstin: str | None = None
    vendor_name: str | None = None
    composition: bool = False
    capital: bool = False


def compute(lines: list[ExpenseLine]) -> dict:
    working = defaultdict(float)
    cols = {"col3_exempt": 0.0, "col4_composition": 0.0, "col5_other_registered": 0.0,
            "col7_unregistered": 0.0}
    vendor_table: dict[tuple, dict] = {}

    for ln in lines:
        amt = float(ln.amount or 0)
        working["capital_expenditure" if ln.capital else "pl_expenditure"] += amt
        treatment = classify_head(ln.account_name)
        if treatment in ("non_cash", "schedule_iii", "statutory_levy", "money_or_securities"):
            working[f"less_{treatment}"] += amt
            continue

        gstin = (ln.vendor_gstin or "").strip().upper()
        registered = bool(GSTIN_RE.match(gstin))
        exempt = treatment in ("exempt", "exempt_non_taxable")
        if not registered:
            col = "col7_unregistered"
        elif exempt:
            col = "col3_exempt"
        elif ln.composition:
            col = "col4_composition"
        else:
            col = "col5_other_registered"
        cols[col] += amt

        key = (gstin or "UNREGISTERED", ln.vendor_name or "")
        row = vendor_table.setdefault(key, {"gstin": key[0], "vendor": key[1], "amount": 0.0, "column": col})
        row["amount"] += amt

    col2 = working["pl_expenditure"] + working["capital_expenditure"]
    excluded = sum(v for k, v in working.items() if k.startswith("less_"))
    cols = {k: round(v, 2) for k, v in cols.items()}
    cols["col6_total_registered"] = round(cols["col3_exempt"] + cols["col4_composition"] + cols["col5_other_registered"], 2)
    in_scope = round(col2 - excluded, 2)
    return {
        "col2_total_expenditure": round(col2, 2),
        **cols,
        "working_79_4": {k: round(v, 2) for k, v in working.items()},
        "balance_for_clause_44": in_scope,
        "tie_out_difference": round(in_scope - cols["col6_total_registered"] - cols["col7_unregistered"], 2),
        "vendor_table_79_20": sorted(vendor_table.values(), key=lambda r: -r["amount"]),
        "remarks": [
            "Composition dealers cannot be identified from books — report per GN 79.13 with a 3CB remark.",
            "Expense-head classification is keyword-based; review the 79.4 working before signing.",
        ],
    }
