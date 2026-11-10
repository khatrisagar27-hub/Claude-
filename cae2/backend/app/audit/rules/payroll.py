"""Payroll rules."""
import math

import pandas as pd

from app.audit.helpers import d, month, rows
from app.audit.registry import Hit, rule
from app.money import inr
from app.statute import ESI_EMPLOYEE_RATE, ESI_WAGE_CEILING, PF_RATE, PF_WAGE_CEILING

COLS = ["emp_code", "pay_month", "basic", "gross", "pf_employee", "esi_employee", "other_deductions", "net_pay", "source_row"]


def names(data) -> dict:
    return dict(zip(data.employees["emp_code"], data.employees["name"]))


@rule("PAY-001", "Payroll", "Salary paid to a person not in the employee master", "critical", ["payroll", "employees"], fraud=True)
def not_in_master(data, p, ctx):
    """Payroll lines whose employee code does not exist in the employee master."""
    pay = data.payroll[~data.payroll["emp_code"].isin(data.employees["emp_code"])]
    return [Hit(f"ghost|{code}", f"Employee code {code} not in master — {inr(g['net_pay'].sum())} paid",
                f"{len(g)} month(s) of salary paid to a code with no employee record.", g["net_pay"].sum(), rows(g, COLS))
            for code, g in pay.groupby("emp_code")]


@rule("PAY-002", "Payroll", "Salary paid after the date of leaving", "critical", ["payroll", "employees.date_left"],
      params={"grace_months": (1, "Months allowed for full and final settlement")}, fraud=True)
def paid_after_leaving(data, p, ctx):
    """Salary for wage months after the month of leaving plus the grace period."""
    left = data.employees.dropna(subset=["date_left"])[["emp_code", "name", "date_left"]]
    pay = data.payroll.merge(left, on="emp_code")
    cutoff = (pay["date_left"].dt.to_period("M") + p["grace_months"]).dt.start_time
    pay = pay[pay["pay_month"] > cutoff]
    return [Hit(f"left|{code}", f"{g['name'].iloc[0]} ({code}) paid {inr(g['net_pay'].sum())} after leaving on {d(g['date_left'].iloc[0])}",
                f"{len(g)} salary month(s) after the leaving date.", g["net_pay"].sum(), rows(g, COLS + ["date_left"]))
            for code, g in pay.groupby("emp_code")]


def _shared(data, column, label):
    e = data.employees[data.employees[column] != ""]
    hits = []
    for value, g in e[e.duplicated(column, keep=False)].groupby(column):
        paid = data.payroll[data.payroll["emp_code"].isin(g["emp_code"])]["net_pay"].sum()
        hits.append(Hit(f"{column}|{value}", f"{len(g)} employees share {label} {value}",
                        f"Employees {', '.join(g['emp_code'] + ' ' + g['name'])} have the same {label}. "
                        f"Net pay to them in the period: {inr(paid)}.", paid, rows(g, ["emp_code", "name", column, "date_joined", "date_left"])))
    return hits


@rule("PAY-003", "Payroll", "Employees sharing a bank account", "high", ["employees.bank_account"], fraud=True)
def shared_bank(data, p, ctx):
    """Two or more employees with the same salary bank account."""
    return _shared(data, "bank_account", "bank account")


@rule("PAY-004", "Payroll", "Employees sharing a PAN", "high", ["employees.pan"], fraud=True)
def shared_pan(data, p, ctx):
    """Two or more employee records with the same PAN — a duplicate or fictitious record."""
    return _shared(data, "pan", "PAN")


@rule("PAY-005", "Payroll", "Sharp rise in gross pay", "medium", ["payroll"],
      params={"rise_pct": (50, "Month-on-month rise (%)"), "min_rise": (5000, "Minimum rise (₹)")})
def pay_jump(data, p, ctx):
    """Gross pay higher than the employee's previous month by more than the set percentage."""
    pay = data.payroll.groupby(["emp_code", "pay_month"], as_index=False)["gross"].sum().sort_values(["emp_code", "pay_month"])
    pay["previous"] = pay.groupby("emp_code")["gross"].shift()
    pay = pay[(pay["previous"] > 0) & (pay["gross"] - pay["previous"] >= p["min_rise"])
              & (pay["gross"] > pay["previous"] * (1 + p["rise_pct"] / 100))]
    name = names(data)
    return [Hit(f"jump|{r.emp_code}|{r.pay_month:%Y-%m}", f"{name.get(r.emp_code, r.emp_code)}: gross pay up "
                f"{(r.gross / r.previous - 1) * 100:.0f}% in {month(r.pay_month)}",
                f"Gross {inr(r.gross)} against {inr(r.previous)} the month before. Check the increment letter, arrears or bonus approval.",
                r.gross - r.previous, rows(data.payroll[data.payroll["emp_code"] == r.emp_code].sort_values("pay_month"), COLS))
            for r in pay.itertuples()]


@rule("PAY-006", "Payroll", "Provident fund short deducted", "high", ["payroll.basic"],
      law=f"EPF Scheme, 1952 para 26 and 29: {PF_RATE:.0%} of basic + DA; compulsory up to Rs {PF_WAGE_CEILING:,}")
def pf_short(data, p, ctx):
    """Employees with basic + DA up to the wage ceiling whose PF deduction is below 12%.
    Employees above the ceiling may be excluded employees and are not tested."""
    if not ctx.flag("pf_applicable", True):
        return []
    pay = data.payroll[(data.payroll["basic"] > 0) & (data.payroll["basic"] <= PF_WAGE_CEILING)].copy()
    pay["pf_due"] = (pay["basic"] * PF_RATE).round()
    pay["shortfall"] = pay["pf_due"] - pay["pf_employee"]
    pay = pay[pay["shortfall"] > 1]
    name = names(data)
    return [Hit(f"pf|{code}", f"{name.get(code, code)}: PF short by {inr(g['shortfall'].sum())} over {len(g)} month(s)",
                f"Employee share short deducted {inr(g['shortfall'].sum())}. The employer's matching share, interest u/s 7Q "
                f"and damages u/s 14B follow.", g["shortfall"].sum(), rows(g, COLS + ["pf_due", "shortfall"]))
            for code, g in pay.groupby("emp_code")]


@rule("PAY-007", "Payroll", "ESI short deducted", "high", ["payroll"],
      law=f"ESI Act, 1948 s.39; ESI (Central) Rules r.50, r.51: employee {ESI_EMPLOYEE_RATE:.2%} on wages up to Rs {ESI_WAGE_CEILING:,}")
def esi_short(data, p, ctx):
    """Employees with gross wages up to the ceiling whose ESI deduction is below 0.75%
    (rounded up to the next rupee). An employee who crosses the ceiling mid contribution
    period stays covered until it ends — those months are not tested here."""
    if not ctx.flag("esi_applicable", True):
        return []
    pay = data.payroll[(data.payroll["gross"] > 0) & (data.payroll["gross"] <= ESI_WAGE_CEILING)].copy()
    pay["esi_due"] = pay["gross"].map(lambda g: math.ceil(round(g * ESI_EMPLOYEE_RATE, 4)))
    pay["shortfall"] = pay["esi_due"] - pay["esi_employee"]
    pay = pay[pay["shortfall"] > 1]
    name = names(data)
    return [Hit(f"esi|{code}", f"{name.get(code, code)}: ESI short by {inr(g['shortfall'].sum())} over {len(g)} month(s)",
                f"Employee share short deducted {inr(g['shortfall'].sum())}; the employer's 3.25% follows.",
                g["shortfall"].sum(), rows(g, COLS + ["esi_due", "shortfall"])) for code, g in pay.groupby("emp_code")]


@rule("PAY-008", "Payroll", "Net pay exceeds gross less deductions", "high", ["payroll"],
      params={"tolerance": (1.0, "Rounding tolerance (₹)")})
def net_pay_excess(data, p, ctx):
    """Net pay is more than gross minus PF, ESI and other deductions."""
    pay = data.payroll.copy()
    pay["excess"] = (pay["net_pay"] - (pay["gross"] - pay["pf_employee"] - pay["esi_employee"] - pay["other_deductions"])).round(2)
    pay = pay[pay["excess"] > p["tolerance"]]
    name = names(data)
    return [Hit(f"net|{r.emp_code}|{r.pay_month:%Y-%m}", f"{name.get(r.emp_code, r.emp_code)}: net pay {inr(r.excess)} more than computed in {month(r.pay_month)}",
                f"Gross {inr(r.gross)} less deductions gives {inr(r.net_pay - r.excess)}; paid {inr(r.net_pay)}.", r.excess,
                rows(pay[pay.index == r.Index], COLS + ["excess"])) for r in pay.itertuples()]


@rule("PAY-009", "Payroll", "Employee paid twice for a month", "critical", ["payroll"], fraud=True)
def paid_twice(data, p, ctx):
    """More than one payroll line for the same employee and wage month."""
    dup = data.payroll[data.payroll.duplicated(["emp_code", "pay_month"], keep=False)]
    name = names(data)
    return [Hit(f"twice|{code}|{m:%Y-%m}", f"{name.get(code, code)}: {len(g)} salary lines for {month(m)}",
                f"Net pay on the extra line(s): {inr(g['net_pay'].sum() - g['net_pay'].iloc[0])}.",
                g["net_pay"].sum() - g["net_pay"].iloc[0], rows(g, COLS)) for (code, m), g in dup.groupby(["emp_code", "pay_month"])]
