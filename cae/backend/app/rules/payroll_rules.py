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
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Ghost Employee: {r[0]}",
            "description": f"Employee ID {r[0]} received ₹{float(r[1]):,.0f} over {r[2]} months but is marked inactive in HR.",
            "severity": "critical",
            "financial_impact": float(r[1]),
            "evidence": {"employee_id": str(r[0]), "total_paid": float(r[1]), "months": r[2]},
        }
        for r in rows
    ]


@register("PAY-002")
def pay_002(conn, company_id, rule):
    """Salary Increase >50% Month-on-Month."""
    rows = conn.execute("""
        SELECT curr.employee_id,
               prev.net_pay as prev_salary, curr.net_pay as curr_salary,
               (curr.net_pay - prev.net_pay) / NULLIF(prev.net_pay, 0) * 100 as increase_pct
        FROM payroll_records curr
        JOIN payroll_records prev ON prev.employee_id = curr.employee_id
          AND prev.pay_period_year = curr.pay_period_year
          AND prev.pay_period_month = curr.pay_period_month - 1
        WHERE curr.company_id = ? AND prev.company_id = ?
          AND (curr.net_pay - prev.net_pay) / NULLIF(prev.net_pay, 0) > 0.50
        LIMIT 20
    """, [company_id, company_id]).fetchall()
    return [
        {
            "title": f"Salary Spike >50%: Employee {r[0]}",
            "description": f"Employee {r[0]} salary increased {float(r[3]):.1f}% from ₹{float(r[1]):,.0f} to ₹{float(r[2]):,.0f} without documented approval.",
            "severity": "high",
            "financial_impact": float(r[2]) - float(r[1]),
            "evidence": {"employee_id": str(r[0]), "prev": float(r[1]), "curr": float(r[2]), "pct": float(r[3])},
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
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Shared Bank Account: {r[0]}",
            "description": f"Bank account {r[0]} receives salary for {r[1]} different employees. Total paid: ₹{float(r[2]):,.0f}. Ghost employee indicator.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"bank_account": r[0], "employee_count": r[1], "total_paid": float(r[2])},
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
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Post-Termination Pay: {r[1]}",
            "description": f"Employee {r[1]} ({r[0]}) received ₹{float(r[2]):,.0f} after leaving date. Immediate recovery required.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"employee_id": str(r[0]), "name": r[1], "overpaid": float(r[2])},
        }
        for r in rows
    ]


@register("PAY-005")
def pay_005(conn, company_id, rule):
    """PF/ESI Statutory Deduction Summary (compliance check)."""
    rows = conn.execute("""
        SELECT pay_period_year, pay_period_month,
               SUM(pf_employer + pf_employee) as total_pf,
               SUM(esic_employer) as total_esi
        FROM payroll_records
        WHERE company_id = ?
          AND status = 'paid'
          AND MAKE_DATE(pay_period_year, pay_period_month, 15) < CURRENT_DATE - INTERVAL '1' MONTH
          AND (pf_employer + pf_employee) > 0
        GROUP BY pay_period_year, pay_period_month
        ORDER BY pay_period_year DESC, pay_period_month DESC
        LIMIT 6
    """, [company_id]).fetchall()
    return [
        {
            "title": f"PF/ESI Compliance Check: {r[0]}-{r[1]:02d}",
            "description": f"Review statutory deposit for PF (₹{float(r[2]):,.0f}) and ESI (₹{float(r[3]):,.0f}) for {r[0]}-{r[1]:02d}.",
            "severity": "high",
            "financial_impact": float(r[2]) + float(r[3]),
            "evidence": {"year": r[0], "month": r[1], "pf": float(r[2]), "esi": float(r[3])},
        }
        for r in rows
    ]


@register("PAY-009")
def pay_009(conn, company_id, rule):
    """High Net Pay Variance — sudden spike in individual salary."""
    rows = conn.execute("""
        SELECT curr.employee_id, curr.pay_period_year, curr.pay_period_month,
               curr.net_pay, curr.gross_earnings
        FROM payroll_records curr
        WHERE curr.company_id = ?
          AND curr.gross_earnings > curr.net_pay * 1.5
          AND curr.gross_earnings > 100000
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Large Payroll Deduction: Employee {r[0]} ({r[1]}-{r[2]:02d})",
            "description": f"Employee {r[0]} gross ₹{float(r[4]):,.0f} vs net ₹{float(r[3]):,.0f} — over 50% deducted. Verify correctness.",
            "severity": "critical",
            "financial_impact": float(r[4]) - float(r[3]),
            "evidence": {"employee_id": str(r[0]), "period": f"{r[1]}-{r[2]:02d}", "gross": float(r[4]), "net": float(r[3])},
        }
        for r in rows
    ]
