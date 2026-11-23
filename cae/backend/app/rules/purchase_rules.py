"""Purchase audit rules PUR-001 to PUR-031."""
from app.rules import register, param, fy_sql, as_date, as_on_date, capped
from app.statutory import income_tax, msme


@register("PUR-001")
def pur_001(conn, company_id, rule):
    """Duplicate Vendor Invoice (same vendor, same invoice number, same financial year)."""
    rows = conn.execute(f"""
        SELECT vendor_id, UPPER(REGEXP_REPLACE(invoice_number, '[^0-9A-Za-z]', '', 'g')) AS inv_key,
               {fy_sql('invoice_date')} AS fy, COUNT(*) AS cnt, SUM(total_amount) AS total,
               STRING_AGG(invoice_number, ', ') AS numbers
        FROM purchase_invoices_all
        WHERE company_id = ? AND status != 'cancelled'
        GROUP BY vendor_id, inv_key, fy
        HAVING COUNT(*) > 1 AND COUNT(*) FILTER (WHERE id IN (SELECT id FROM purchase_invoices)) > 0
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Duplicate Vendor Invoice: {r[5].split(', ')[0]} (FY {r[2]}-{str(r[2] + 1)[-2:]})",
            "description": f"Vendor {r[0]} invoice {r[5]} is booked {r[3]} times in FY {r[2]}-{str(r[2] + 1)[-2:]}. "
                           f"Risk of duplicate payment and double ITC: ₹{float(r[4]):,.0f}.",
            "severity": "critical",
            "financial_impact": float(r[4]) * (r[3] - 1) / r[3],
            "evidence": {"vendor_id": str(r[0]), "invoice_numbers": r[5], "financial_year": f"{r[2]}-{str(r[2] + 1)[-2:]}",
                         "count": r[3], "total": float(r[4])},
        }
        for r in rows
    ]


@register("PUR-002")
def pur_002(conn, company_id, rule):
    """PO vs Invoice Amount Mismatch above tolerance."""
    tolerance = float(param(rule, "tolerance_pct", 5)) / 100
    rows = conn.execute("""
        WITH po AS (
            SELECT id, vendor_id, invoice_number, total_amount,
                   TRY_CAST(json_extract_string(CAST(raw_data AS VARCHAR), '$.po_value') AS DOUBLE) AS po_value
            FROM purchase_invoices
            WHERE company_id = ? AND raw_data IS NOT NULL
        )
        SELECT id, vendor_id, invoice_number, total_amount, po_value
        FROM po
        WHERE po_value > 0 AND ABS(total_amount - po_value) / po_value > ?
        ORDER BY ABS(total_amount - po_value) DESC
    """, [company_id, tolerance]).fetchall()
    return [
        {
            "title": f"PO-Invoice Mismatch: {r[2]}",
            "description": f"Invoice {r[2]} (₹{float(r[3]):,.0f}) differs from PO value ₹{float(r[4]):,.0f} by more than {tolerance * 100:g}%.",
            "severity": "high",
            "financial_impact": abs(float(r[3]) - float(r[4])),
            "evidence": {"invoice_number": r[2], "invoice_value": float(r[3]), "po_value": float(r[4])},
        }
        for r in rows
    ]


@register("PUR-004")
def pur_004(conn, company_id, rule):
    """Invoice Without PO above a value."""
    min_amount = float(param(rule, "min_amount", 100_000))
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, total_amount
        FROM purchase_invoices
        WHERE company_id = ? AND total_amount > ?
          AND (our_po_number IS NULL OR our_po_number = '')
          AND status NOT IN ('cancelled', 'disputed')
        ORDER BY total_amount DESC
    """, [company_id, min_amount]).fetchall()
    return [
        {
            "title": f"No PO for Invoice: {r[2]}",
            "description": f"Purchase invoice {r[2]} (₹{float(r[3]):,.0f}) has no PO reference. Authorisation bypass risk.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"vendor_id": str(r[1]), "invoice_number": r[2], "amount": float(r[3])},
        }
        for r in rows
    ]


@register("PUR-006")
def pur_006(conn, company_id, rule):
    """Split purchases — several invoices each below the approval limit that together exceed it."""
    limit = float(param(rule, "approval_limit", 100_000))
    window_days = int(param(rule, "window_days", 7))
    min_count = int(param(rule, "min_count", 3))
    rows = conn.execute("""
        WITH small AS (
            SELECT vendor_id, invoice_date, total_amount
            FROM purchase_invoices
            WHERE company_id = ? AND total_amount < ? AND status != 'cancelled'
        ),
        windows AS (
            SELECT a.vendor_id, a.invoice_date AS window_start,
                   COUNT(*) AS cnt, SUM(b.total_amount) AS total
            FROM small a
            JOIN small b ON b.vendor_id = a.vendor_id
             AND b.invoice_date BETWEEN a.invoice_date AND a.invoice_date + CAST(? AS INTEGER)
            GROUP BY a.vendor_id, a.invoice_date
            HAVING COUNT(*) >= ? AND SUM(b.total_amount) > ?
        )
        SELECT vendor_id, MIN(window_start), MAX(cnt), MAX(total)
        FROM windows
        GROUP BY vendor_id
        ORDER BY MAX(total) DESC
    """, [company_id, limit, window_days, min_count, limit]).fetchall()
    return [
        {
            "title": f"Split Purchases: Vendor {r[0]} from {r[1]}",
            "description": f"Vendor {r[0]} has {r[2]} invoices each below the ₹{limit:,.0f} approval limit within {window_days} days, "
                           f"totalling ₹{float(r[3]):,.0f}. Possible splitting to avoid approval.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"vendor_id": str(r[0]), "first_window": str(r[1]), "count": r[2], "total": float(r[3])},
        }
        for r in rows
    ]


@register("PUR-010")
def pur_010(conn, company_id, rule):
    """Vendor payment to a bank account that is not the one in the vendor master."""
    rows = conn.execute("""
        SELECT v.id, v.name, v.bank_account_number, t.counterparty_account, t.transaction_date, t.amount
        FROM bank_transactions t
        JOIN vendors v ON LOWER(TRIM(v.name)) = LOWER(TRIM(t.counterparty_name))
        WHERE t.company_id = ? AND v.company_id = ? AND t.transaction_type = 'debit'
          AND t.counterparty_account IS NOT NULL AND TRIM(t.counterparty_account) != ''
          AND v.bank_account_number IS NOT NULL AND TRIM(v.bank_account_number) != ''
          AND REGEXP_REPLACE(t.counterparty_account, '\\s', '', 'g') != REGEXP_REPLACE(v.bank_account_number, '\\s', '', 'g')
        ORDER BY t.amount DESC
    """, [company_id, company_id]).fetchall()
    return [
        {
            "title": f"Payment to Unregistered Account: {r[1]} on {r[4]}",
            "description": f"₹{float(r[5]):,.0f} paid to {r[1]} on {r[4]} went to account {r[3]}, not the master account {r[2]}. "
                           "Confirm the bank-detail change was authorised before the payment.",
            "severity": "critical",
            "financial_impact": float(r[5]),
            "evidence": {"vendor_id": str(r[0]), "vendor": r[1], "master_account": r[2], "paid_to_account": r[3],
                         "date": str(r[4]), "amount": float(r[5])},
        }
        for r in rows
    ]


@register("PUR-013")
def pur_013(conn, company_id, rule):
    """Large invoice with no approver and no PO."""
    min_amount = float(param(rule, "min_amount", 500_000))
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, total_amount
        FROM purchase_invoices
        WHERE company_id = ? AND total_amount > ?
          AND approved_by_user_id IS NULL
          AND status IN ('pending', 'approved', 'part_paid', 'paid')
          AND (our_po_number IS NULL OR our_po_number = '')
        ORDER BY total_amount DESC
    """, [company_id, min_amount]).fetchall()
    return [
        {
            "title": f"Unapproved Large Invoice: {r[2]}",
            "description": f"Invoice {r[2]} of ₹{float(r[3]):,.0f} has neither an approver nor a PO.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"vendor_id": str(r[1]), "invoice_number": r[2], "amount": float(r[3])},
        }
        for r in rows
    ]


@register("PUR-016")
def pur_016(conn, company_id, rule):
    """Possible duplicate payment — same vendor, same amount, different invoice numbers, close dates, both paid."""
    window_days = int(param(rule, "window_days", 30))
    rows = conn.execute("""
        SELECT a.vendor_id, a.total_amount, a.invoice_number, b.invoice_number, a.invoice_date, b.invoice_date
        FROM purchase_invoices a
        JOIN purchase_invoices b
          ON b.company_id = a.company_id AND b.vendor_id = a.vendor_id
         AND b.total_amount = a.total_amount AND b.id > a.id
         AND b.invoice_number != a.invoice_number
         AND ABS(DATEDIFF('day', a.invoice_date, b.invoice_date)) <= ?
        WHERE a.company_id = ? AND a.status = 'paid' AND b.status = 'paid' AND a.total_amount > 0
        ORDER BY a.total_amount DESC
    """, [window_days, company_id]).fetchall()
    return [
        {
            "title": f"Possible Duplicate Payment: {r[2]} / {r[3]}",
            "description": f"Vendor {r[0]} was paid ₹{float(r[1]):,.0f} twice, on invoices {r[2]} ({r[4]}) and {r[3]} ({r[5]}), "
                           f"within {window_days} days. Check they are separate supplies.",
            "severity": "critical",
            "financial_impact": float(r[1]),
            "evidence": {"vendor_id": str(r[0]), "amount": float(r[1]), "invoices": [r[2], r[3]],
                         "dates": [str(r[4]), str(r[5])]},
        }
        for r in rows
    ]


@register("PUR-021")
def pur_021(conn, company_id, rule):
    """GRN dated before the supplier's invoice (goods recorded as received before they were billed)."""
    min_amount = float(param(rule, "min_amount", 100_000))
    min_gap = int(param(rule, "min_gap_days", 1))
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, total_amount, invoice_date, receipt_date
        FROM purchase_invoices
        WHERE company_id = ? AND receipt_date IS NOT NULL
          AND DATEDIFF('day', receipt_date, invoice_date) >= ?
          AND total_amount > ? AND status != 'cancelled'
        ORDER BY DATEDIFF('day', receipt_date, invoice_date) DESC
    """, [company_id, min_gap, min_amount]).fetchall()
    return [
        {
            "title": f"GRN Before Invoice: {r[2]}",
            "description": f"Invoice {r[2]} (₹{float(r[3]):,.0f}) is dated {r[4]} but the goods receipt is dated {r[5]}. "
                           "A back-dated GRN can shift cost or ITC between periods.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"invoice_number": r[2], "invoice_date": str(r[4]), "receipt_date": str(r[5]), "amount": float(r[3])},
        }
        for r in rows
    ]


@register("PUR-022")
def pur_022(conn, company_id, rule):
    """Vendor shares a bank account or PAN with an employee."""
    rows = conn.execute("""
        SELECT v.id, v.name, e.id, e.full_name,
               CASE WHEN v.bank_account_number = e.bank_account_number THEN 'bank account' ELSE 'PAN' END AS link
        FROM vendors v
        JOIN employees e ON e.company_id = v.company_id
         AND ((v.bank_account_number IS NOT NULL AND LENGTH(TRIM(v.bank_account_number)) >= 6
               AND REGEXP_REPLACE(v.bank_account_number, '\\s', '', 'g') = REGEXP_REPLACE(e.bank_account_number, '\\s', '', 'g'))
           OR (v.pan IS NOT NULL AND LENGTH(TRIM(v.pan)) = 10 AND UPPER(TRIM(v.pan)) = UPPER(TRIM(e.pan))))
        WHERE v.company_id = ?
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Vendor-Employee Link: {r[1]}",
            "description": f"Vendor {r[1]} shares a {r[4]} with employee {r[3]}. Possible ghost vendor or undisclosed related party.",
            "severity": "critical",
            "financial_impact": 0,
            "evidence": {"vendor_id": str(r[0]), "vendor_name": r[1], "employee_id": str(r[2]),
                         "employee_name": r[3], "matched_on": r[4]},
        }
        for r in rows
    ]


@register("PUR-031")
def pur_031(conn, company_id, rule):
    """MSME dues beyond the MSMED s.15 time limit — s.16 interest and s.37(2)(g) / s.43B(h) exposure."""
    as_on = as_on_date(conn, rule, "purchase_invoices", "invoice_date")
    default_days = param(rule, "assume_agreed_days", None)
    rows = conn.execute("""
        SELECT pi.id, v.name, v.msme_status, pi.invoice_number, pi.invoice_date, pi.receipt_date,
               pi.total_amount, pi.outstanding_amount, pi.payment_date, pi.status, v.payment_terms_days
        FROM purchase_invoices_all pi
        JOIN vendors v ON v.id = pi.vendor_id
        WHERE pi.company_id = ? AND pi.status != 'cancelled'
          AND LOWER(TRIM(v.msme_status)) IN ('micro', 'small')
    """, [company_id]).fetchall()
    out = []
    for r in rows:
        acceptance = as_date(r[5]) if r[5] else as_date(r[4])
        agreed = r[10] if r[10] is not None else default_days
        outstanding = float(r[7] or 0)
        paid_on = as_date(r[8]) if (r[9] == "paid" and r[8]) else None
        if paid_on and paid_on > as_on:           # settled after the as-on date: still due on it
            paid_on, outstanding = None, float(r[6])
        if paid_on is None and outstanding <= 0:
            continue
        principal = outstanding if paid_on is None else float(r[6])
        calc = msme.bill_interest(principal, acceptance, paid_on, as_on, agreed)
        if calc["delay_days"] <= 0:
            continue
        ref = income_tax.section_ref("msme_disallowance", as_on)
        state = f"paid {calc['delay_days']} days late on {paid_on}" if paid_on else f"unpaid {calc['delay_days']} days past the due date"
        out.append({
            "title": f"MSME Payment Delayed: {r[1]} — {r[3]}",
            "description": f"{r[2]} enterprise {r[1]}: invoice {r[3]} (₹{principal:,.0f}) was due on {calc['appointed_day']} "
                           f"({calc['credit_days_applied']}-day limit) and is {state}. Interest u/s 16 MSMED at "
                           f"{calc['rate_pa']:g}% p.a. compounded monthly: ₹{calc['interest']:,.0f} (not deductible, s.23 MSMED). "
                           + (f"If still unpaid at year-end, the expense is deductible only in the year of payment ({ref})."
                              if paid_on is None else ""),
            "severity": "high" if paid_on is None else "medium",
            "financial_impact": calc["interest"],
            "evidence": {"vendor": r[1], "msme_status": r[2], "invoice_number": r[3], "principal": principal,
                         "as_on": str(as_on), **{k: v for k, v in calc.items() if k != "segments"},
                         "statutory_ref": f"MSMED Act ss.15-16; {ref}"},
        })
    out.sort(key=lambda e: -e["financial_impact"])
    return capped(out, rule)
