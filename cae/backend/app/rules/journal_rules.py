"""Journal entry audit rules JE-001 to JE-015."""
from app.rules import register


@register("JE-001")
def je_001(conn, company_id, rule):
    """Manual JE Without Narration."""
    rows = conn.execute("""
        SELECT id, voucher_number, total_debit, entry_date
        FROM journal_entries
        WHERE company_id = ? AND voucher_type = 'journal'
          AND (narration IS NULL OR narration = '')
          AND total_debit > 100000
        LIMIT 30
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Manual JE Without Narration: {r[1]}",
            "description": f"Journal entry {r[1]} (₹{float(r[2]):,.0f}) dated {r[3]} has no narration. Cannot determine business purpose.",
            "severity": "high",
            "financial_impact": float(r[2]),
            "evidence": {"voucher_number": r[1], "amount": float(r[2]), "date": str(r[3])},
        }
        for r in rows
    ]


@register("JE-002")
def je_002(conn, company_id, rule):
    """JE Posted Well After Entry Date (late posting)."""
    rows = conn.execute("""
        SELECT id, voucher_number, entry_date, posted_at, total_debit
        FROM journal_entries
        WHERE company_id = ? AND is_posted = true
          AND posted_at IS NOT NULL
          AND DATEDIFF('day', entry_date, CAST(posted_at AS DATE)) > 10
          AND total_debit > 100000
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Late-Posted JE: {r[1]}",
            "description": f"JE {r[1]} was posted on {r[3]}, more than 10 days after entry date {r[2]}.",
            "severity": "critical",
            "financial_impact": float(r[4]),
            "evidence": {"voucher_number": r[1], "entry_date": str(r[2]), "posted_at": str(r[3]), "amount": float(r[4])},
        }
        for r in rows
    ]


@register("JE-003")
def je_003(conn, company_id, rule):
    """Large Value Manual JE >₹10L."""
    rows = conn.execute("""
        SELECT id, voucher_number, total_debit, entry_date, posted_by_user_id
        FROM journal_entries
        WHERE company_id = ? AND voucher_type = 'journal'
          AND total_debit > 1000000
        ORDER BY total_debit DESC
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Large Manual JE: {r[1]} (₹{float(r[2])/100000:.1f}L)",
            "description": f"Journal entry {r[1]} of ₹{float(r[2]):,.0f} dated {r[3]}. High-value manual JEs require special scrutiny.",
            "severity": "high",
            "financial_impact": float(r[2]),
            "evidence": {"voucher_number": r[1], "amount": float(r[2]), "date": str(r[3]), "posted_by": str(r[4])},
        }
        for r in rows
    ]


@register("JE-005")
def je_005(conn, company_id, rule):
    """JE to Suspense Account Not Cleared (>30 days)."""
    rows = conn.execute("""
        SELECT jel.id, je.voucher_number, je.entry_date,
               jel.debit_amount + jel.credit_amount as line_amount,
               DATEDIFF('day', je.entry_date, CURRENT_DATE) as days_open
        FROM journal_entry_lines jel
        JOIN journal_entries je ON jel.journal_entry_id = je.id
        WHERE je.company_id = ?
          AND (jel.account_code LIKE 'SUSP%' OR jel.account_name LIKE '%Suspense%')
          AND DATEDIFF('day', je.entry_date, CURRENT_DATE) > 30
          AND (jel.debit_amount + jel.credit_amount) > 50000
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Uncleared Suspense: JE {r[1]} ({r[4]} days)",
            "description": f"JE {r[1]} has ₹{float(r[3]):,.0f} in suspense account for {r[4]} days since {r[2]}.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"voucher_number": r[1], "date": str(r[2]), "amount": float(r[3]), "days_open": r[4]},
        }
        for r in rows
    ]


@register("JE-006")
def je_006(conn, company_id, rule):
    """Reversal Without Original JE Reference."""
    rows = conn.execute("""
        SELECT id, voucher_number, total_debit, entry_date
        FROM journal_entries
        WHERE company_id = ? AND is_reversed = true
          AND reversal_of_id IS NULL
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Orphan Reversal JE: {r[1]}",
            "description": f"Reversal JE {r[1]} (₹{float(r[2]):,.0f}) has no original JE reference. Possible fraudulent reversal.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"voucher_number": r[1], "amount": float(r[2]), "date": str(r[3])},
        }
        for r in rows
    ]


@register("JE-009")
def je_009(conn, company_id, rule):
    """Unbalanced JE (debit ≠ credit in lines)."""
    rows = conn.execute("""
        SELECT je.id, je.voucher_number, je.total_debit,
               SUM(jel.debit_amount) as line_debits,
               SUM(jel.credit_amount) as line_credits
        FROM journal_entries je
        JOIN journal_entry_lines jel ON jel.journal_entry_id = je.id
        WHERE je.company_id = ?
        GROUP BY je.id, je.voucher_number, je.total_debit
        HAVING ABS(SUM(jel.debit_amount) - SUM(jel.credit_amount)) > 1
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Unbalanced JE: {r[1]}",
            "description": f"JE {r[1]} is unbalanced — Debits: ₹{float(r[3]):,.0f}, Credits: ₹{float(r[4]):,.0f}. Difference: ₹{abs(float(r[3])-float(r[4])):,.0f}.",
            "severity": "critical",
            "financial_impact": abs(float(r[3]) - float(r[4])),
            "evidence": {"voucher_number": r[1], "debits": float(r[3]), "credits": float(r[4])},
        }
        for r in rows
    ]


@register("JE-011")
def je_011(conn, company_id, rule):
    """JE Posted by Same User Repeatedly (SoD proxy — single approver)."""
    rows = conn.execute("""
        SELECT posted_by_user_id, COUNT(*) as cnt, SUM(total_debit) as total_value
        FROM journal_entries
        WHERE company_id = ?
          AND posted_by_user_id IS NOT NULL
          AND is_posted = true
          AND total_debit > 500000
        GROUP BY posted_by_user_id
        HAVING COUNT(*) > 10
        LIMIT 10
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Single-User High-Volume JE Posting: {r[0]}",
            "description": f"User {r[0]} posted {r[1]} large JEs totaling ₹{float(r[2]):,.0f}. Review for SoD compliance.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"user_id": str(r[0]), "count": r[1], "total": float(r[2])},
        }
        for r in rows
    ]


@register("JE-015")
def je_015(conn, company_id, rule):
    """Prior Period JE — entry_date in previous year but posted now."""
    rows = conn.execute("""
        SELECT id, voucher_number, entry_date, posted_at, total_debit
        FROM journal_entries
        WHERE company_id = ?
          AND is_posted = true
          AND posted_at IS NOT NULL
          AND YEAR(entry_date) < YEAR(CAST(posted_at AS DATE))
          AND total_debit > 100000
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Prior Period JE: {r[1]}",
            "description": f"JE {r[1]} (₹{float(r[4]):,.0f}) dated {r[2]} was posted in a later year ({r[3]}). Prior period entry may distort current financials.",
            "severity": "high",
            "financial_impact": float(r[4]),
            "evidence": {"voucher_number": r[1], "entry_date": str(r[2]), "posted_at": str(r[3]), "amount": float(r[4])},
        }
        for r in rows
    ]
