"""Treasury/Cash audit rules TRE-001 to TRE-010."""
import re

from app.rules import register, param, as_date, capped
from app.statutory import income_tax

_SELF_PARTIES = ("self", "cash", "cash withdrawal", "atm", "petty cash")
_TRANSPORT = re.compile(r"transport|truck|lorry|goods carriage|freight|tempo|logistics", re.I)


@register("TRE-001")
def tre_001(conn, company_id, rule):
    """Cash expenditure to one person in a day above Rs.10,000 (Rs.35,000 for goods-carriage hire)
    — s.36(4)/(6) of the 2025 Act / s.40A(3) of the 1961 Act."""
    tax_rate = float(param(rule, "tax_rate", 0.25168))
    limit = float(param(rule, "limit", income_tax.CASH_EXPENDITURE_LIMIT))
    transport_limit = float(param(rule, "transport_limit", income_tax.CASH_EXPENDITURE_LIMIT_TRANSPORT))
    rows = conn.execute("""
        SELECT counterparty_name, transaction_date, COUNT(*) AS cnt, SUM(amount) AS total,
               STRING_AGG(COALESCE(description, ''), ' | ') AS descr
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'debit' AND LOWER(transaction_mode) = 'cash'
          AND counterparty_name IS NOT NULL AND TRIM(counterparty_name) != ''
          AND LOWER(TRIM(counterparty_name)) NOT IN (SELECT UNNEST(?::VARCHAR[]))
        GROUP BY counterparty_name, transaction_date
        HAVING SUM(amount) > ?
        ORDER BY total DESC
    """, [company_id, list(_SELF_PARTIES), limit]).fetchall()
    out = []
    for party, on, cnt, total, descr in rows:
        on = as_date(on)
        transport = bool(_TRANSPORT.search(f"{party} {descr}"))
        applicable = transport_limit if transport else limit
        if float(total) <= applicable:
            continue
        key = "cash_expenditure_transport" if transport else "cash_expenditure"
        ref = income_tax.section_ref(key, on)
        out.append({
            "title": f"Cash Payment > ₹{applicable:,.0f}: {party} on {on}",
            "description": f"₹{float(total):,.0f} paid in cash to {party} on {on} ({cnt} payment{'s' if cnt > 1 else ''}). "
                           f"Cash payments to a person in a day above ₹{applicable:,.0f} are disallowed under {ref}, "
                           "unless an exception in the Rules applies.",
            "severity": "high",
            "financial_impact": round(float(total) * tax_rate, 2),
            "evidence": {"party": party, "date": str(on), "count": cnt, "amount": float(total),
                         "limit_applied": applicable, "tax_rate_used": tax_rate, "statutory_ref": ref},
        })
    return capped(out, rule)


@register("TRE-002")
def tre_002(conn, company_id, rule):
    """Circular Bank Transfer — money out to a party and back within a short window."""
    min_amount = float(param(rule, "min_amount", 500_000))
    window_days = int(param(rule, "window_days", 2))
    rows = conn.execute("""
        SELECT t1.counterparty_name, t1.amount, t1.transaction_date, t2.transaction_date, t2.amount
        FROM bank_transactions t1
        JOIN bank_transactions t2
          ON t1.company_id = t2.company_id AND t1.id != t2.id
         AND LOWER(TRIM(t1.counterparty_name)) = LOWER(TRIM(t2.counterparty_name))
         AND t1.transaction_type = 'debit' AND t2.transaction_type = 'credit'
         AND ABS(t1.amount - t2.amount) / NULLIF(t1.amount, 0) < 0.05
         AND DATEDIFF('day', t1.transaction_date, t2.transaction_date) BETWEEN 0 AND ?
        WHERE t1.company_id = ? AND t1.amount > ?
        ORDER BY t1.amount DESC
    """, [window_days, company_id, min_amount]).fetchall()
    return [
        {
            "title": f"Circular Transfer: ₹{float(r[1]):,.0f} with {r[0]} on {r[2]}",
            "description": f"₹{float(r[1]):,.0f} went to {r[0]} on {r[2]} and ₹{float(r[4]):,.0f} came back on {r[3]}. Possible fund rotation or window dressing.",
            "severity": "critical",
            "financial_impact": float(r[1]),
            "evidence": {"party": r[0], "amount_out": float(r[1]), "amount_in": float(r[4]), "out_date": str(r[2]), "in_date": str(r[3])},
        }
        for r in rows
    ]


@register("TRE-003")
def tre_003(conn, company_id, rule):
    """Cash loan/deposit taken or repaid of Rs.20,000 or more (s.185 / s.188; 1961: s.269SS / s.269T)."""
    limit = float(param(rule, "limit", income_tax.CASH_LOAN_LIMIT))
    rows = conn.execute("""
        SELECT counterparty_name, transaction_date, transaction_type, SUM(amount) AS total,
               STRING_AGG(COALESCE(description, ''), ' | ') AS descr
        FROM bank_transactions
        WHERE company_id = ? AND LOWER(transaction_mode) = 'cash'
          AND REGEXP_MATCHES(LOWER(COALESCE(description, '')), 'loan|deposit|advance|unsecured|repay')
          AND counterparty_name IS NOT NULL AND TRIM(counterparty_name) != ''
          AND LOWER(TRIM(counterparty_name)) NOT IN (SELECT UNNEST(?::VARCHAR[]))
        GROUP BY counterparty_name, transaction_date, transaction_type
        HAVING SUM(amount) >= ?
        ORDER BY total DESC
    """, [company_id, list(_SELF_PARTIES), limit]).fetchall()
    out = []
    for party, on, ttype, total, descr in rows:
        on = as_date(on)
        key = "cash_loan_accept" if ttype == "credit" else "cash_loan_repay"
        ref = income_tax.section_ref(key, on)
        verb = "taken from" if ttype == "credit" else "repaid to"
        out.append({
            "title": f"Cash Loan {('Taken' if ttype == 'credit' else 'Repaid')}: {party} on {on}",
            "description": f"₹{float(total):,.0f} {verb} {party} in cash on {on} ('{descr[:80]}'). Loans/deposits of "
                           f"₹{limit:,.0f} or more must move through banking channels — {ref}. Penalty equals the amount.",
            "severity": "critical",
            "financial_impact": float(total),
            "evidence": {"party": party, "date": str(on), "direction": ttype, "amount": float(total), "statutory_ref": ref},
        })
    return out


@register("TRE-004")
def tre_004(conn, company_id, rule):
    """Large electronic transfer with no reference or UTR."""
    min_amount = float(param(rule, "min_amount", 500_000))
    rows = conn.execute("""
        SELECT id, transaction_date, amount, counterparty_name
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'debit' AND amount > ?
          AND UPPER(transaction_mode) IN ('RTGS', 'NEFT', 'IMPS')
          AND (reference_number IS NULL OR TRIM(reference_number) = '')
          AND (utr_number IS NULL OR TRIM(utr_number) = '')
        ORDER BY amount DESC
    """, [company_id, min_amount]).fetchall()
    return [
        {
            "title": f"Unreferenced Transfer: ₹{float(r[2]):,.0f} to {r[3]}",
            "description": f"Transfer of ₹{float(r[2]):,.0f} to {r[3]} on {r[1]} has no reference or UTR. Cannot trace authorisation.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"txn_id": str(r[0]), "date": str(r[1]), "amount": float(r[2]), "party": r[3]},
        }
        for r in rows
    ]


@register("TRE-005")
def tre_005(conn, company_id, rule):
    """Multiple payments to the same party on the same day."""
    min_count = int(param(rule, "min_count", 3))
    min_total = float(param(rule, "min_total", 500_000))
    rows = conn.execute("""
        SELECT counterparty_name, transaction_date, COUNT(*) AS cnt, SUM(amount) AS total
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'debit'
          AND counterparty_name IS NOT NULL AND TRIM(counterparty_name) != ''
        GROUP BY counterparty_name, transaction_date
        HAVING COUNT(*) >= ? AND SUM(amount) > ?
        ORDER BY total DESC
    """, [company_id, min_count, min_total]).fetchall()
    return [
        {
            "title": f"Multiple Payments to {r[0]} on {r[1]}",
            "description": f"{r[2]} payments totalling ₹{float(r[3]):,.0f} to {r[0]} on {r[1]}. Possible duplicate payment or structuring.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"party": r[0], "date": str(r[1]), "count": r[2], "total": float(r[3])},
        }
        for r in rows
    ]


@register("TRE-006")
def tre_006(conn, company_id, rule):
    """Large payments described as director/loan payments (s.185/s.186/s.188 Companies Act review)."""
    min_amount = float(param(rule, "min_amount", 100_000))
    rows = conn.execute("""
        SELECT id, transaction_date, amount, counterparty_name, description
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'debit' AND amount > ?
          AND (REGEXP_MATCHES(LOWER(COALESCE(description, '')), 'director|loan|advance to')
               OR LOWER(COALESCE(counterparty_name, '')) LIKE '%director%')
        ORDER BY amount DESC
    """, [company_id, min_amount]).fetchall()
    return [
        {
            "title": f"Director/Loan Payment: ₹{float(r[2]):,.0f} to {r[3]}",
            "description": f"₹{float(r[2]):,.0f} to {r[3]} on {r[1]} — narration mentions a director or loan. Check s.185 / s.186 / "
                           "s.188 Companies Act approvals and the related-party register.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"txn_id": str(r[0]), "date": str(r[1]), "amount": float(r[2]), "party": r[3], "narration": r[4]},
        }
        for r in rows
    ]


@register("TRE-010")
def tre_010(conn, company_id, rule):
    """Structured cash withdrawals just below the Rs.10 lakh cash-transaction-report level."""
    low = float(param(rule, "band_low", 800_000))
    high = float(param(rule, "band_high", 999_999.99))
    min_count = int(param(rule, "min_count", 2))
    rows = conn.execute("""
        SELECT transaction_date, SUM(amount) AS daily_cash, COUNT(*) AS withdrawals
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'debit' AND LOWER(transaction_mode) = 'cash'
          AND amount BETWEEN ? AND ?
        GROUP BY transaction_date
        HAVING COUNT(*) >= ?
        ORDER BY daily_cash DESC
    """, [company_id, low, high, min_count]).fetchall()
    return [
        {
            "title": f"Structured Cash Withdrawal: {r[0]}",
            "description": f"{r[2]} cash withdrawals totalling ₹{float(r[1]):,.0f} on {r[0]}, each just below ₹10 lakh. Possible structuring.",
            "severity": "critical",
            "financial_impact": float(r[1]),
            "evidence": {"date": str(r[0]), "total": float(r[1]), "transactions": r[2]},
        }
        for r in rows
    ]
