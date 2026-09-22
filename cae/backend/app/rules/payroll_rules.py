"""Payroll audit rules PAY-001 to PAY-009."""
from app.rules import register


@register("PAY-001")
def pay_001(conn, company_id, rule):
    """Ghost Employee — salary paid but employee is inactive in HR."""
    rows = conn.execute("""
        SELECT pr.employee_id, SUM(pr.net_pay) as total_paid, COUNT(*) as months
        FROM payroll_records pr
        JOIN employees e ON e.id = pr.employee_id
        WHERE pr.company_id = ? AND e.is_active = false
          AND pr.net_pay > 0
          AND pr.status = 'paid'
        GROUP BY pr.employee_id
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Ghost Employee: {r[0]}",
            "description": f"Employee ID {r[0]} received ₹{float(r[1]):,.0f} over {r[2]} months but is marked inactive in HR.",
            "severity": "critical",
            "financial_impact": float(r[1]),
            "evidence": {"employee_id": str(r[0]), "total_paid": float(r[1]), "months": r[2]},
            "key": f"employee_id={r[0]}",
        }
        for r in rows
    ]


@register("PAY-002")
def pay_002(conn, company_id, rule):
    """Salary Increase >50% Month-on-Month."""
    rows = conn.execute("""
        SELECT curr.employee_id,
               prev.net_pay as prev_salary, curr.net_pay as curr_salary,
               (curr.net_pay - prev.net_pay) / NULLIF(prev.net_pay, 0) * 100 as increase_pct,
               curr.pay_period_year, curr.pay_period_month
        FROM payroll_records curr
        JOIN payroll_records prev ON prev.employee_id = curr.employee_id
          AND prev.pay_period_year * 12 + prev.pay_period_month
              = curr.pay_period_year * 12 + curr.pay_period_month - 1
        WHERE curr.company_id = ? AND prev.company_id = ?
          AND (curr.net_pay - prev.net_pay) / NULLIF(prev.net_pay, 0) > 0.50
    """, [company_id, company_id]).fetchall()
    return [
        {
            "title": f"Salary Spike >50%: Employee {r[0]} ({r[4]}-{r[5]:02d})",
            "description": f"Employee {r[0]} salary increased {float(r[3]):.1f}% from ₹{float(r[1]):,.0f} to ₹{float(r[2]):,.0f} without documented approval.",
            "severity": "high",
            "financial_impact": float(r[2]) - float(r[1]),
            "evidence": {"employee_id": str(r[0]), "period": f"{r[4]}-{r[5]:02d}", "prev": float(r[1]), "curr": float(r[2]), "pct": float(r[3])},
            "key": f"employee_id={r[0]}|period={r[4]}-{r[5]:02d}",
        }
        for r in rows
    ]


@register("PAY-003")
def pay_003(conn, company_id, rule):
    """Duplicate Bank Account Across Employees."""
    rows = conn.execute("""
        SELECT e.bank_account_number, COUNT(DISTINCT pr.employee_id) as emp_count,
               SUM(pr.net_pay) as total_paid
        FROM payroll_records pr
        JOIN employees e ON e.id = pr.employee_id
        WHERE pr.company_id = ? AND e.bank_account_number IS NOT NULL
        GROUP BY e.bank_account_number
        HAVING COUNT(DISTINCT pr.employee_id) > 1
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Shared Bank Account: {r[0]}",
            "description": f"Bank account {r[0]} receives salary for {r[1]} different employees. Total paid: ₹{float(r[2]):,.0f}. Ghost employee indicator.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"bank_account": r[0], "employee_count": r[1], "total_paid": float(r[2])},
            "key": f"bank_account={r[0]}",
        }
        for r in rows
    ]


@register("PAY-004")
def pay_004(conn, company_id, rule):
    """Salary Paid to Terminated Employee."""
    rows = conn.execute("""
        SELECT pr.employee_id, e.full_name, SUM(pr.net_pay) as paid_after_leaving
        FROM payroll_records pr
        JOIN employees e ON e.id = pr.employee_id
        WHERE pr.company_id = ?
          AND e.is_active = false
          AND e.date_of_leaving IS NOT NULL
          AND MAKE_DATE(pr.pay_period_year, pr.pay_period_month, 1) > e.date_of_leaving
          AND pr.net_pay > 0
        GROUP BY pr.employee_id, e.full_name
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Post-Termination Pay: {r[1]}",
            "description": f"Employee {r[1]} ({r[0]}) received ₹{float(r[2]):,.0f} after leaving date. Immediate recovery required.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"employee_id": str(r[0]), "name": r[1], "overpaid": float(r[2])},
            "key": f"employee_id={r[0]}",
        }
        for r in rows
    ]


# EPF: 12% of basic wages from employee and employer; mandatory up to the ₹15,000
# wage ceiling (EPF Scheme para 26/29). ESI: 0.75% employee + 3.25% employer where
# gross wages are ≤ ₹21,000 (ESI Act s.39, rates w.e.f. 1 Jul 2019).
EPF_RATE, EPF_WAGE_CEILING = 0.12, 15000
ESI_EE_RATE, ESI_ER_RATE, ESI_WAGE_CEILING = 0.0075, 0.0325, 21000


@register("PAY-005")
def pay_005(conn, company_id, rule):
    """PF/ESI Short Deduction — contributions below the statutory rate, per pay period.

    PF is checked where the employee is a member (any PF deducted) or basic is within
    the wage ceiling. ESI coverage continuing through a contribution period after
    wages cross ₹21,000 is not modelled — verify flagged cases against ESI records.
    """
    rows = conn.execute("""
        WITH req AS (
            SELECT pay_period_year, pay_period_month, employee_id,
                   CASE WHEN COALESCE(pf_employee, 0) > 0 OR basic_salary <= ?
                        THEN ROUND(LEAST(basic_salary, ?) * ?, 2) ELSE 0 END as pf_due,
                   COALESCE(pf_employee, 0) as pf_ee, COALESCE(pf_employer, 0) as pf_er,
                   CASE WHEN gross_earnings <= ? THEN ROUND(gross_earnings * ?, 2) ELSE 0 END as esi_ee_due,
                   CASE WHEN gross_earnings <= ? THEN ROUND(gross_earnings * ?, 2) ELSE 0 END as esi_er_due,
                   COALESCE(esic_employee, 0) as esi_ee, COALESCE(esic_employer, 0) as esi_er
            FROM payroll_records
            WHERE company_id = ? AND basic_salary > 0
        ), short AS (
            SELECT *, GREATEST(pf_due - pf_ee, 0) + GREATEST(pf_due - pf_er, 0) as pf_short,
                      GREATEST(esi_ee_due - esi_ee, 0) + GREATEST(esi_er_due - esi_er, 0) as esi_short
            FROM req
        )
        SELECT pay_period_year, pay_period_month, COUNT(*) as employees,
               SUM(pf_short) as pf_short, SUM(esi_short) as esi_short
        FROM short
        WHERE pf_short > 1 OR esi_short > 1
        GROUP BY pay_period_year, pay_period_month
        ORDER BY pay_period_year, pay_period_month
    """, [EPF_WAGE_CEILING, EPF_WAGE_CEILING, EPF_RATE,
          ESI_WAGE_CEILING, ESI_EE_RATE, ESI_WAGE_CEILING, ESI_ER_RATE, company_id]).fetchall()
    return [
        {
            "title": f"PF/ESI Short Deduction: {r[0]}-{r[1]:02d}",
            "description": f"{r[2]} employee(s) in {r[0]}-{r[1]:02d} have contributions below the statutory rate: PF short ₹{float(r[3]):,.2f}, ESI short ₹{float(r[4]):,.2f} (employee + employer).",
            "severity": "high",
            "financial_impact": float(r[3]) + float(r[4]),
            "evidence": {"period": f"{r[0]}-{r[1]:02d}", "employees": r[2], "pf_short": float(r[3]), "esi_short": float(r[4])},
            "key": f"period={r[0]}-{r[1]:02d}",
        }
        for r in rows
    ]


@register("PAY-009")
def pay_009(conn, company_id, rule):
    """Excessive Payroll Deductions — over a third of gross deducted on a gross above ₹1L."""
    rows = conn.execute("""
        SELECT curr.employee_id, curr.pay_period_year, curr.pay_period_month,
               curr.net_pay, curr.gross_earnings
        FROM payroll_records curr
        WHERE curr.company_id = ?
          AND curr.gross_earnings > curr.net_pay * 1.5
          AND curr.gross_earnings > 100000
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Large Payroll Deduction: Employee {r[0]} ({r[1]}-{r[2]:02d})",
            "description": f"Employee {r[0]} gross ₹{float(r[4]):,.0f} vs net ₹{float(r[3]):,.0f} — more than a third of gross deducted. Verify correctness.",
            "severity": "critical",
            "financial_impact": float(r[4]) - float(r[3]),
            "evidence": {"employee_id": str(r[0]), "period": f"{r[1]}-{r[2]:02d}", "gross": float(r[4]), "net": float(r[3])},
            "key": f"employee_id={r[0]}|period={r[1]}-{r[2]:02d}",
        }
        for r in rows
    ]
