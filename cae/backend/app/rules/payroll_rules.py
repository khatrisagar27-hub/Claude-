"""Payroll audit rules PAY-001 to PAY-009."""
import re
from calendar import monthrange
from datetime import date

from app.rules import register, param, as_date, as_on_date
from app.statutory import income_tax, labour


@register("PAY-001")
def pay_001(conn, company_id, rule):
    """Salary paid to an employee marked inactive with no leaving date recorded."""
    rows = conn.execute("""
        SELECT pr.employee_id, e.full_name, SUM(pr.net_pay) AS total_paid, COUNT(*) AS months
        FROM payroll_records pr
        JOIN employees e ON e.id = pr.employee_id
        WHERE pr.company_id = ? AND e.is_active = false AND e.date_of_leaving IS NULL
          AND pr.net_pay > 0 AND pr.status = 'paid'
        GROUP BY pr.employee_id, e.full_name
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Ghost Employee: {r[1]}",
            "description": f"{r[1]} ({r[0]}) is inactive in HR with no exit date, yet received ₹{float(r[2]):,.0f} over {r[3]} pay months.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"employee_id": str(r[0]), "name": r[1], "total_paid": float(r[2]), "months": r[3]},
        }
        for r in rows
    ]


@register("PAY-002")
def pay_002(conn, company_id, rule):
    """Gross salary up more than N% on the previous month (year boundary handled)."""
    pct = float(param(rule, "max_increase_pct", 50))
    rows = conn.execute("""
        SELECT curr.employee_id, curr.pay_period_year, curr.pay_period_month,
               prev.gross_earnings, curr.gross_earnings,
               (curr.gross_earnings - prev.gross_earnings) / NULLIF(prev.gross_earnings, 0) * 100 AS increase_pct
        FROM payroll_records curr
        JOIN payroll_records prev
          ON prev.employee_id = curr.employee_id AND prev.company_id = curr.company_id
         AND prev.pay_period_year * 12 + prev.pay_period_month = curr.pay_period_year * 12 + curr.pay_period_month - 1
        WHERE curr.company_id = ? AND prev.gross_earnings > 0
          AND (curr.gross_earnings - prev.gross_earnings) / prev.gross_earnings * 100 > ?
        ORDER BY increase_pct DESC
        LIMIT 20
    """, [company_id, pct]).fetchall()
    return [
        {
            "title": f"Salary Spike >{pct:g}%: Employee {r[0]} ({r[1]}-{r[2]:02d})",
            "description": f"Employee {r[0]} gross pay rose {float(r[5]):.1f}% from ₹{float(r[3]):,.0f} to ₹{float(r[4]):,.0f} in {r[1]}-{r[2]:02d}. "
                           "Check the increment letter or arrears working.",
            "severity": "high",
            "financial_impact": float(r[4]) - float(r[3]),
            "evidence": {"employee_id": str(r[0]), "period": f"{r[1]}-{r[2]:02d}", "prev": float(r[3]), "curr": float(r[4]), "pct": float(r[5])},
        }
        for r in rows
    ]


@register("PAY-003")
def pay_003(conn, company_id, rule):
    """Same bank account receiving salary for more than one employee."""
    rows = conn.execute("""
        SELECT e.bank_account_number, COUNT(DISTINCT pr.employee_id) AS emp_count, SUM(pr.net_pay) AS total_paid
        FROM payroll_records pr
        JOIN employees e ON e.id = pr.employee_id
        WHERE pr.company_id = ? AND e.bank_account_number IS NOT NULL AND TRIM(e.bank_account_number) != ''
        GROUP BY e.bank_account_number
        HAVING COUNT(DISTINCT pr.employee_id) > 1
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Shared Bank Account: {r[0]}",
            "description": f"Bank account {r[0]} receives salary for {r[1]} employees (₹{float(r[2]):,.0f} in total). Ghost-employee indicator.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"bank_account": r[0], "employee_count": r[1], "total_paid": float(r[2])},
        }
        for r in rows
    ]


@register("PAY-004")
def pay_004(conn, company_id, rule):
    """Salary paid for a period that starts after the employee's leaving date."""
    rows = conn.execute("""
        SELECT pr.employee_id, e.full_name, SUM(pr.net_pay) AS paid_after_leaving, MAX(e.date_of_leaving)
        FROM payroll_records pr
        JOIN employees e ON e.id = pr.employee_id
        WHERE pr.company_id = ? AND e.date_of_leaving IS NOT NULL
          AND MAKE_DATE(pr.pay_period_year, pr.pay_period_month, 1) > e.date_of_leaving
          AND pr.net_pay > 0
        GROUP BY pr.employee_id, e.full_name
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Post-Termination Pay: {r[1]}",
            "description": f"{r[1]} ({r[0]}) left on {r[3]} but was paid ₹{float(r[2]):,.0f} for later periods. "
                           "Full-and-final settlements are usually one payment — check anything recurring.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"employee_id": str(r[0]), "name": r[1], "date_of_leaving": str(r[3]), "overpaid": float(r[2])},
        }
        for r in rows
    ]


@register("PAY-005")
def pay_005(conn, company_id, rule):
    """PF/ESI contributions not deposited by the 15th of the following month. PF and ESI are
    matched to bank debits separately, by narration and amount (tolerance covers EPF admin charges)."""
    patterns = {
        "PF": re.compile(param(rule, "pf_pattern", r"epfo|\bepf\b|provident"), re.I),
        "ESI": re.compile(param(rule, "esi_pattern", r"\besic?\b|state insurance"), re.I),
    }
    tolerance = float(param(rule, "amount_tolerance_pct", 5)) / 100
    as_on = as_on_date(conn, rule, "bank_transactions", "transaction_date")
    months = conn.execute("""
        SELECT pay_period_year, pay_period_month,
               SUM(pf_employee) AS pf_ee, SUM(pf_employer) AS pf_er,
               SUM(esic_employee) AS esi_ee, SUM(esic_employer) AS esi_er
        FROM payroll_records
        WHERE company_id = ? AND status = 'paid'
        GROUP BY 1, 2
        HAVING SUM(pf_employee + pf_employer + esic_employee + esic_employer) > 0
        ORDER BY 1, 2
    """, [company_id]).fetchall()
    payments = conn.execute("""
        SELECT transaction_date, amount, COALESCE(description, '') || ' ' || COALESCE(counterparty_name, '')
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'debit'
        ORDER BY transaction_date
    """, [company_id]).fetchall()
    challans = {
        scheme: [(as_date(d), float(a)) for d, a, text in payments if rx.search(text)]
        for scheme, rx in patterns.items()
    }

    out = []
    used: dict[str, set[int]] = {"PF": set(), "ESI": set()}
    for year, month, pf_ee, pf_er, esi_ee, esi_er in months:
        year, month = int(year), int(month)
        due = labour.contribution_due_date(year, month)
        if due > as_on:
            continue
        month_end = date(year, month, monthrange(year, month)[1])
        for scheme, ee, er in (("PF", float(pf_ee or 0), float(pf_er or 0)), ("ESI", float(esi_ee or 0), float(esi_er or 0))):
            liability = ee + er
            if liability <= 0:
                continue
            paid_on = None
            for i, (d, amt) in enumerate(challans[scheme]):
                if i not in used[scheme] and d > month_end and liability * (1 - tolerance) <= amt <= liability * (1 + tolerance) + 1:
                    used[scheme].add(i)
                    paid_on = d
                    break
            if paid_on and paid_on <= due:
                continue
            test = labour.employee_contribution_tax_test(month_end)
            ref = income_tax.section_ref("employee_contribution", month_end)
            if test == "labour_due_date":
                tax_note = f"The employee share (₹{ee:,.0f}) is disallowed under {ref} as it was not credited by the due date."
            else:
                tax_note = f"The employee share (₹{ee:,.0f}) stays deductible under {ref} only if credited by the return due date."
            status = f"deposited late on {paid_on}" if paid_on else "and no matching challan payment is in the bank data"
            out.append({
                "title": f"{scheme} Late or Not Deposited: {year}-{month:02d}",
                "description": f"{scheme} of ₹{liability:,.0f} for {year}-{month:02d} was due by {due}, {status}. "
                               f"Interest and damages apply under the {'EPF' if scheme == 'PF' else 'ESI'} Act. {tax_note}",
                "severity": "high" if paid_on else "critical",
                "financial_impact": ee if test == "labour_due_date" else 0.0,
                "evidence": {"scheme": scheme, "period": f"{year}-{month:02d}", "due_date": str(due),
                             "paid_on": str(paid_on) if paid_on else None, "employee_share": ee, "employer_share": er,
                             "tax_test": test, "statutory_ref": f"{'EPF Scheme para 38' if scheme == 'PF' else 'ESI (Central) Regulations'}; {ref}"},
            })
    return out


@register("PAY-009")
def pay_009(conn, company_id, rule):
    """Deductions above a share of gross pay (recoveries, advances or payroll errors)."""
    max_share = float(param(rule, "max_deduction_share", 0.33))
    min_gross = float(param(rule, "min_gross", 100_000))
    rows = conn.execute("""
        SELECT employee_id, pay_period_year, pay_period_month, net_pay, gross_earnings
        FROM payroll_records
        WHERE company_id = ? AND gross_earnings > ?
          AND (gross_earnings - net_pay) > gross_earnings * ?
        ORDER BY gross_earnings - net_pay DESC
        LIMIT 20
    """, [company_id, min_gross, max_share]).fetchall()
    return [
        {
            "title": f"High Payroll Deductions: Employee {r[0]} ({r[1]}-{r[2]:02d})",
            "description": f"Employee {r[0]}: gross ₹{float(r[4]):,.0f}, net ₹{float(r[3]):,.0f} — {(1 - float(r[3]) / float(r[4])) * 100:.0f}% deducted. "
                           "Check advance recoveries and TDS working.",
            "severity": "medium",
            "financial_impact": float(r[4]) - float(r[3]),
            "evidence": {"employee_id": str(r[0]), "period": f"{r[1]}-{r[2]:02d}", "gross": float(r[4]), "net": float(r[3])},
        }
        for r in rows
    ]
