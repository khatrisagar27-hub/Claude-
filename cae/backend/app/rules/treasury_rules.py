"""Treasury/Cash audit rules TRE-001 to TRE-010."""
from app.rules import register


@register("TRE-001")
def tre_001(conn, company_id, rule):
    """Cash Payment >₹10,000 — Income Tax limit."""
    rows = conn.execute("""
        SELECT id, transaction_date, amount, counterparty_name, description
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'debit'
          AND transaction_mode = 'cash' AND amount > 10000
        ORDER BY amount DESC
        LIMIT 30
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Cash Payment >₹10K: ₹{float(r[2]):,.0f} to {r[3]}",
            "description": f"Cash payment of ₹{float(r[2]):,.0f} to {r[3]} on {r[1]} violates Section 40A(3) — cash payments >₹10,000 disallowed as deduction.",
            "severity": "high",
            "financial_impact": float(r[2]) * 0.30,
            "evidence": {"txn_id": str(r[0]), "date": str(r[1]), "amount": float(r[2]), "party": r[3]},
        }
        for r in rows
    ]


@register("TRE-002")
def tre_002(conn, company_id, rule):
    """Circular Bank Transfer — payment out and back within 48 hours."""
    rows = conn.execute("""
        SELECT t1.id, t1.counterparty_name as party,
               t1.amount, t1.transaction_date as dt1, t2.transaction_date as dt2
        FROM bank_transactions t1
        JOIN bank_transactions t2
          ON t1.company_id = t2.company_id
          AND t1.counterparty_name = t2.counterparty_name
          AND t1.transaction_type = 'debit' AND t2.transaction_type = 'credit'
          AND ABS(t1.amount - t2.amount) / NULLIF(t1.amount, 0) < 0.05
          AND DATEDIFF('hour', CAST(t1.transaction_date AS TIMESTAMP), CAST(t2.transaction_date AS TIMESTAMP)) BETWEEN 1 AND 48
        WHERE t1.company_id = ? AND t1.amount > 500000
        LIMIT 10
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Circular Transfer: ₹{float(r[2]):,.0f} with {r[1]}",
            "description": f"₹{float(r[2]):,.0f} transferred to {r[1]} on {r[3]} and returned within 48 hours on {r[4]}. Possible fund rotation.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"party": r[1], "amount": float(r[2]), "out_date": str(r[3]), "in_date": str(r[4])},
        }
        for r in rows
    ]


@register("TRE-004")
def tre_004(conn, company_id, rule):
    """Large Bank Transfer Without Reference (possible unauthorized)."""
    rows = conn.execute("""
        SELECT id, transaction_date, amount, counterparty_name, reference_number
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'debit'
          AND amount > 500000
          AND transaction_mode IN ('RTGS', 'NEFT')
          AND (reference_number IS NULL OR reference_number = '')
        ORDER BY amount DESC
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Unreferenced Transfer: ₹{float(r[2]):,.0f} to {r[3]}",
            "description": f"Bank transfer of ₹{float(r[2]):,.0f} to {r[3]} on {r[1]} has no reference number. Cannot verify authorization.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"txn_id": str(r[0]), "date": str(r[1]), "amount": float(r[2]), "party": r[3]},
        }
        for r in rows
    ]


@register("TRE-005")
def tre_005(conn, company_id, rule):
    """Multiple Payments to Same Party Same Day."""
    rows = conn.execute("""
        SELECT counterparty_name, transaction_date,
               COUNT(*) as cnt, SUM(amount) as total
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'debit'
        GROUP BY counterparty_name, transaction_date
        HAVING COUNT(*) > 2 AND SUM(amount) > 500000
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Multiple Payments to {r[0]} on {r[1]}",
            "description": f"{r[2]} payments totaling ₹{float(r[3]):,.0f} to {r[0]} on {r[1]}. Possible duplicate payment or structuring.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"party": r[0], "date": str(r[1]), "count": r[2], "total": float(r[3])},
        }
        for r in rows
    ]


@register("TRE-006")
def tre_006(conn, company_id, rule):
    """Large Payments with Unusual Description (keywords for director payments)."""
    rows = conn.execute("""
        SELECT id, transaction_date, amount, counterparty_name, description
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'debit'
          AND amount > 100000
          AND (LOWER(description) LIKE '%director%'
               OR LOWER(description) LIKE '%loan%'
               OR LOWER(counterparty_name) LIKE '%director%')
        ORDER BY amount DESC
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Director/Loan Payment: ₹{float(r[2]):,.0f}",
            "description": f"₹{float(r[2]):,.0f} to {r[3]} on {r[1]} — description mentions director or loan. Verify board approval.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"txn_id": str(r[0]), "date": str(r[1]), "amount": float(r[2]), "party": r[3], "narration": r[4]},
        }
        for r in rows
    ]


@register("TRE-010")
def tre_010(conn, company_id, rule):
    """Cash Withdrawal Pattern — structured withdrawals just below ₹10L."""
    rows = conn.execute("""
        SELECT transaction_date, SUM(amount) as daily_cash, COUNT(*) as withdrawals
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'debit' AND transaction_mode = 'cash'
          AND amount BETWEEN 800000 AND 990000
        GROUP BY transaction_date
        HAVING COUNT(*) >= 2
        LIMIT 10
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Structured Cash Withdrawal: {r[0]}",
            "description": f"{r[2]} cash withdrawals totaling ₹{float(r[1]):,.0f} on {r[0]}, each just below ₹10L reporting threshold. Possible structuring.",
            "severity": "critical",
            "financial_impact": float(r[1]),
            "evidence": {"date": str(r[0]), "total": float(r[1]), "transactions": r[2]},
        }
        for r in rows
    ]
