"""Journal entry audit rules JE-001 to JE-015."""
from app.rules import register, param, fy_sql, as_on_date


@register("JE-001")
def je_001(conn, company_id, rule):
    """Manual JE Without Narration."""
    min_amount = float(param(rule, "min_amount", 100_000))
    rows = conn.execute("""
        SELECT id, voucher_number, total_debit, entry_date
        FROM journal_entries
        WHERE company_id = ? AND voucher_type = 'journal'
          AND (narration IS NULL OR TRIM(narration) = '')
          AND total_debit > ?
        ORDER BY total_debit DESC
    """, [company_id, min_amount]).fetchall()
    return [
        {
            "title": f"Manual JE Without Narration: {r[1]}",
            "description": f"Journal entry {r[1]} (₹{float(r[2]):,.0f}) dated {r[3]} has no narration. Business purpose cannot be established.",
            "severity": "high",
            "financial_impact": float(r[2]),
            "evidence": {"voucher_number": r[1], "amount": float(r[2]), "date": str(r[3])},
        }
        for r in rows
    ]


@register("JE-002")
def je_002(conn, company_id, rule):
    """JE posted well after its entry date (late posting)."""
    max_days = int(param(rule, "max_days", 10))
    min_amount = float(param(rule, "min_amount", 100_000))
    rows = conn.execute("""
        SELECT id, voucher_number, entry_date, posted_at, total_debit,
               DATEDIFF('day', entry_date, CAST(posted_at AS DATE)) AS lag
        FROM journal_entries
        WHERE company_id = ? AND is_posted = true AND posted_at IS NOT NULL
          AND DATEDIFF('day', entry_date, CAST(posted_at AS DATE)) > ?
          AND total_debit > ?
        ORDER BY lag DESC
    """, [company_id, max_days, min_amount]).fetchall()
    return [
        {
            "title": f"Late-Posted JE: {r[1]}",
            "description": f"JE {r[1]} dated {r[2]} was posted {r[5]} days later, on {str(r[3])[:10]}.",
            "severity": "critical",
            "financial_impact": float(r[4]),
            "evidence": {"voucher_number": r[1], "entry_date": str(r[2]), "posted_at": str(r[3]), "lag_days": r[5], "amount": float(r[4])},
        }
        for r in rows
    ]


@register("JE-003")
def je_003(conn, company_id, rule):
    """Large Value Manual JE."""
    min_amount = float(param(rule, "min_amount", 1_000_000))
    rows = conn.execute("""
        SELECT id, voucher_number, total_debit, entry_date, posted_by_user_id
        FROM journal_entries
        WHERE company_id = ? AND voucher_type = 'journal' AND total_debit > ?
        ORDER BY total_debit DESC
    """, [company_id, min_amount]).fetchall()
    return [
        {
            "title": f"Large Manual JE: {r[1]} (₹{float(r[2]) / 100000:.1f}L)",
            "description": f"Journal entry {r[1]} of ₹{float(r[2]):,.0f} dated {r[3]}. High-value manual JEs need supporting documents and approval (SA 240 para 32).",
            "severity": "high",
            "financial_impact": float(r[2]),
            "evidence": {"voucher_number": r[1], "amount": float(r[2]), "date": str(r[3]), "posted_by": str(r[4])},
        }
        for r in rows
    ]


@register("JE-005")
def je_005(conn, company_id, rule):
    """Suspense account carrying a balance older than N days."""
    max_days = int(param(rule, "max_days", 30))
    min_amount = float(param(rule, "min_amount", 50_000))
    as_on = as_on_date(conn, rule, "journal_entries", "entry_date")
    rows = conn.execute("""
        SELECT COALESCE(jel.account_code, jel.account_name) AS acct, MAX(jel.account_name),
               SUM(jel.debit_amount - jel.credit_amount) AS net, MIN(je.entry_date) AS oldest, COUNT(*) AS lines
        FROM journal_entry_lines_all jel
        JOIN journal_entries_all je ON jel.journal_entry_id = je.id
        WHERE je.company_id = ? AND je.entry_date <= ?
          AND (UPPER(jel.account_code) LIKE 'SUSP%' OR LOWER(jel.account_name) LIKE '%suspense%')
        GROUP BY acct
        HAVING ABS(SUM(jel.debit_amount - jel.credit_amount)) > ?
           AND DATEDIFF('day', MIN(je.entry_date), CAST(? AS DATE)) > ?
    """, [company_id, as_on, min_amount, as_on, max_days]).fetchall()
    return [
        {
            "title": f"Uncleared Suspense: {r[1] or r[0]}",
            "description": f"Suspense account {r[1] or r[0]} carries a net {'debit' if float(r[2]) > 0 else 'credit'} of ₹{abs(float(r[2])):,.0f} "
                           f"as on {as_on}; the oldest entry is from {r[3]} ({r[4]} lines).",
            "severity": "high",
            "financial_impact": abs(float(r[2])),
            "evidence": {"account": r[1] or r[0], "net_balance": float(r[2]), "oldest_entry": str(r[3]), "lines": r[4], "as_on": str(as_on)},
        }
        for r in rows
    ]


@register("JE-006")
def je_006(conn, company_id, rule):
    """Reversal JE without a reference to the original entry."""
    rows = conn.execute("""
        SELECT id, voucher_number, total_debit, entry_date
        FROM journal_entries
        WHERE company_id = ? AND is_reversed = true AND reversal_of_id IS NULL
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Orphan Reversal JE: {r[1]}",
            "description": f"Reversal JE {r[1]} (₹{float(r[2]):,.0f}) has no link to the entry it reverses.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"voucher_number": r[1], "amount": float(r[2]), "date": str(r[3])},
        }
        for r in rows
    ]


@register("JE-009")
def je_009(conn, company_id, rule):
    """Unbalanced JE (line debits not equal to line credits)."""
    tolerance = float(param(rule, "tolerance", 1))
    rows = conn.execute("""
        SELECT je.id, je.voucher_number, SUM(jel.debit_amount) AS d, SUM(jel.credit_amount) AS c
        FROM journal_entries je
        JOIN journal_entry_lines jel ON jel.journal_entry_id = je.id
        WHERE je.company_id = ?
        GROUP BY je.id, je.voucher_number
        HAVING ABS(SUM(jel.debit_amount) - SUM(jel.credit_amount)) > ?
    """, [company_id, tolerance]).fetchall()
    return [
        {
            "title": f"Unbalanced JE: {r[1]}",
            "description": f"JE {r[1]} is unbalanced — debits ₹{float(r[2]):,.2f}, credits ₹{float(r[3]):,.2f}, difference ₹{abs(float(r[2]) - float(r[3])):,.2f}.",
            "severity": "critical",
            "financial_impact": abs(float(r[2]) - float(r[3])),
            "evidence": {"voucher_number": r[1], "debits": float(r[2]), "credits": float(r[3])},
        }
        for r in rows
    ]


@register("JE-011")
def je_011(conn, company_id, rule):
    """One user posting a high volume of large JEs (segregation-of-duties indicator)."""
    min_amount = float(param(rule, "min_amount", 500_000))
    min_count = int(param(rule, "min_count", 10))
    rows = conn.execute("""
        WITH je AS (
            SELECT j.*, COALESCE(u.full_name, json_extract_string(CAST(j.raw_data AS VARCHAR), '$.entered_by'),
                                 j.posted_by_user_id) AS poster
            FROM journal_entries j LEFT JOIN users u ON u.id = j.posted_by_user_id
        )
        SELECT poster, COUNT(*) AS cnt, SUM(total_debit) AS total_value, MAX(posted_by_user_id)
        FROM je
        WHERE company_id = ? AND poster IS NOT NULL AND is_posted = true
          AND total_debit > ?
        GROUP BY poster
        HAVING COUNT(*) > ?
    """, [company_id, min_amount, min_count]).fetchall()
    return [
        {
            "title": f"Single-User High-Volume JE Posting: {r[0]}",
            "description": f"User {r[0]} posted {r[1]} JEs above ₹{min_amount:,.0f}, totalling ₹{float(r[2]):,.0f}. Check maker-checker separation.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"posted_by": str(r[0]), "user_id": str(r[3]) if r[3] else None, "count": r[1], "total": float(r[2])},
        }
        for r in rows
    ]


@register("JE-015")
def je_015(conn, company_id, rule):
    """Prior-period JE — dated in one financial year (Apr-Mar) but posted in a later one."""
    min_amount = float(param(rule, "min_amount", 100_000))
    rows = conn.execute(f"""
        SELECT id, voucher_number, entry_date, posted_at, total_debit
        FROM journal_entries
        WHERE company_id = ? AND is_posted = true AND posted_at IS NOT NULL
          AND {fy_sql('entry_date')} < {fy_sql('CAST(posted_at AS DATE)')}
          AND total_debit > ?
        ORDER BY total_debit DESC
    """, [company_id, min_amount]).fetchall()
    return [
        {
            "title": f"Prior Period JE: {r[1]}",
            "description": f"JE {r[1]} (₹{float(r[4]):,.0f}) dated {r[2]} was posted on {str(r[3])[:10]}, in a later financial year. "
                           "Check whether the earlier year's books were already closed or audited (AS 5 / Ind AS 8).",
            "severity": "high",
            "financial_impact": float(r[4]),
            "evidence": {"voucher_number": r[1], "entry_date": str(r[2]), "posted_at": str(r[3]), "amount": float(r[4])},
        }
        for r in rows
    ]
