"""Purchase audit rules PUR-001 to PUR-031."""
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from app.rules import register

# Purchase approval limit used by the PO / split-PO rules (₹).
APPROVAL_LIMIT = 100000


@register("PUR-001")
def pur_001(conn, company_id, rule):
    """Duplicate Vendor Invoice."""
    rows = conn.execute("""
        SELECT vendor_id, invoice_number, COUNT(*) as cnt, SUM(total_amount) as total
        FROM purchase_invoices
        WHERE company_id = ?
        GROUP BY vendor_id, invoice_number
        HAVING COUNT(*) > 1
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Duplicate Vendor Invoice: {r[1]} (Vendor {r[0]})",
            "description": f"Vendor invoice {r[1]} appears {r[2]} times. Risk of duplicate payment: ₹{float(r[3]):,.0f}.",
            "severity": "critical",
            "financial_impact": float(r[3]),
            "evidence": {"vendor_id": str(r[0]), "invoice_number": r[1], "count": r[2], "total": float(r[3])},
            "key": f"vendor_id={r[0]}|invoice_number={r[1]}",
        }
        for r in rows
    ]


@register("PUR-002")
def pur_002(conn, company_id, rule):
    """PO vs Invoice Amount Mismatch >5%."""
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, total_amount, po_value
        FROM (
            SELECT id, vendor_id, invoice_number, total_amount,
                   TRY_CAST(json_extract_string(raw_data, '$.po_value') AS DOUBLE) as po_value
            FROM purchase_invoices
            WHERE company_id = ? AND raw_data IS NOT NULL
        ) t
        WHERE po_value > 0
          AND ABS(total_amount - po_value) / po_value > 0.05
    """, [company_id]).fetchall()
    return [
        {
            "title": f"PO-Invoice Mismatch: {r[2]}",
            "description": f"Invoice {r[2]} (₹{float(r[3]):,.0f}) deviates more than 5% from PO value ₹{float(r[4]):,.0f}.",
            "severity": "high",
            "financial_impact": abs(float(r[3]) - float(r[4])),
            "evidence": {"invoice_number": r[2], "invoice_value": float(r[3]), "po_value": float(r[4])},
            "key": f"invoice_id={r[0]}",
        }
        for r in rows
    ]


@register("PUR-004")
def pur_004(conn, company_id, rule):
    """Invoice Without PO above ₹1L."""
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, total_amount
        FROM purchase_invoices
        WHERE company_id = ? AND total_amount > ?
          AND (our_po_number IS NULL OR our_po_number = '')
          AND status NOT IN ('cancelled', 'disputed')
    """, [company_id, APPROVAL_LIMIT]).fetchall()
    return [
        {
            "title": f"No PO for Invoice: {r[2]}",
            "description": f"Purchase invoice {r[2]} (₹{float(r[3]):,.0f}) has no PO reference. Authorization bypass risk.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"vendor_id": str(r[1]), "invoice_number": r[2], "amount": float(r[3])},
            "key": f"invoice_id={r[0]}",
        }
        for r in rows
    ]


@register("PUR-006")
def pur_006(conn, company_id, rule):
    """Split invoices — same vendor, same day, each just below the approval limit.

    Every invoice in the group is between 50% and 100% of the limit, so any two of
    them together cross it. A regular supplier billing many small amounts across a
    month is not flagged.
    """
    rows = conn.execute("""
        SELECT vendor_id, invoice_date, COUNT(*) as cnt, SUM(total_amount) as total,
               STRING_AGG(invoice_number, ', ' ORDER BY invoice_number) as invoices
        FROM purchase_invoices
        WHERE company_id = ?
          AND total_amount >= ? * 0.5 AND total_amount < ?
          AND status != 'cancelled'
        GROUP BY vendor_id, invoice_date
        HAVING COUNT(*) >= 2
    """, [company_id, APPROVAL_LIMIT, APPROVAL_LIMIT]).fetchall()
    return [
        {
            "title": f"Split Invoices: Vendor {r[0]} on {r[1]}",
            "description": f"Vendor {r[0]} raised {r[2]} invoices on {r[1]} (₹{float(r[3]):,.2f} in total), each just below the ₹{APPROVAL_LIMIT:,} approval limit: {r[4]}. Possible splitting to avoid approval.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"vendor_id": str(r[0]), "date": str(r[1]), "count": r[2], "total": float(r[3]), "invoices": r[4]},
            "key": f"vendor_id={r[0]}|date={r[1]}",
        }
        for r in rows
    ]


@register("PUR-013")
def pur_013(conn, company_id, rule):
    """Advance Payment Without Approval."""
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, total_amount
        FROM purchase_invoices
        WHERE company_id = ?
          AND total_amount > 500000
          AND approved_by_user_id IS NULL
          AND status IN ('pending', 'approved')
          AND our_po_number IS NULL
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Unapproved Large Invoice: {r[2]}",
            "description": f"Invoice {r[2]} of ₹{float(r[3]):,.0f} has no approval. Advance payment risk.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"vendor_id": str(r[1]), "invoice_number": r[2], "amount": float(r[3])},
            "key": f"invoice_id={r[0]}",
        }
        for r in rows
    ]


@register("PUR-016")
def pur_016(conn, company_id, rule):
    """Duplicate Payment — same vendor, same amount, more than one invoice paid."""
    rows = conn.execute("""
        SELECT vendor_id, total_amount, COUNT(*) as cnt, SUM(paid_amount) as total_paid,
               STRING_AGG(invoice_number, ', ' ORDER BY invoice_number) as invoices
        FROM purchase_invoices
        WHERE company_id = ? AND status = 'paid' AND total_amount > 0
        GROUP BY vendor_id, total_amount
        HAVING COUNT(*) > 1
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Possible Duplicate Payment: Vendor {r[0]} ₹{float(r[1]):,.2f}",
            "description": f"Vendor {r[0]} has {r[2]} paid invoices with identical amount ₹{float(r[1]):,.2f} ({r[4]}). Review for duplicate payment.",
            "severity": "critical",
            "financial_impact": float(r[1]) * (r[2] - 1),
            "evidence": {"vendor_id": str(r[0]), "amount": float(r[1]), "count": r[2], "total_paid": float(r[3]), "invoices": r[4]},
            "key": f"vendor_id={r[0]}|amount={float(r[1]):.2f}",
        }
        for r in rows
    ]


@register("PUR-021")
def pur_021(conn, company_id, rule):
    """Goods Receipt Dated Before Invoice."""
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, total_amount, invoice_date, receipt_date
        FROM purchase_invoices
        WHERE company_id = ?
          AND receipt_date IS NOT NULL
          AND invoice_date > receipt_date
          AND total_amount > 100000
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Receipt Dated Before Invoice: {r[2]}",
            "description": f"Invoice {r[2]} (₹{float(r[3]):,.0f}) dated {r[4]} but goods received {r[5]}. Backdated receipt risk.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"invoice_number": r[2], "invoice_date": str(r[4]), "receipt_date": str(r[5]), "amount": float(r[3])},
            "key": f"invoice_id={r[0]}",
        }
        for r in rows
    ]


@register("PUR-022")
def pur_022(conn, company_id, rule):
    """Vendor Bank Account Matches an Employee's Bank Account."""
    rows = conn.execute("""
        SELECT v.id, v.name, e.id as emp_id, e.full_name as emp_name, v.bank_account_number
        FROM vendors v
        JOIN employees e
          ON UPPER(TRIM(v.bank_account_number)) = UPPER(TRIM(e.bank_account_number))
        WHERE v.company_id = ? AND e.company_id = ?
          AND v.bank_account_number IS NOT NULL AND TRIM(v.bank_account_number) != ''
    """, [company_id, company_id]).fetchall()
    return [
        {
            "title": f"Vendor-Employee Bank Account Match: {r[1]} / {r[3]}",
            "description": f"Vendor {r[1]} is paid into bank account {r[4]}, which is also the salary account of employee {r[3]}. Possible ghost vendor / insider fraud.",
            "severity": "critical",
            "financial_impact": 0,
            "evidence": {"vendor_id": str(r[0]), "vendor_name": r[1], "employee_id": str(r[2]), "employee_name": r[3], "bank_account": r[4]},
            "key": f"vendor_id={r[0]}|employee_id={r[2]}",
        }
        for r in rows
    ]


def _months_between(start: date, end: date) -> tuple[int, int]:
    """Completed calendar months from start to end, plus leftover days."""
    rd = relativedelta(end, start)
    months = rd.years * 12 + rd.months
    return months, (end - (start + relativedelta(months=months))).days


@register("PUR-031")
def pur_031(conn, company_id, rule):
    """MSME payment beyond the s.15 MSMED Act limit (micro & small suppliers only).

    Appointed day = agreed due date, capped at 45 days from acceptance; 15 days if
    nothing was agreed. Acceptance is taken as the goods receipt date, else the
    invoice date. The unpaid amount is the s.43B(h) disallowance exposure.
    s.16 interest (compound, monthly rests, at 3x the RBI Bank Rate) is computed only
    when the rule's parameters carry ``rbi_bank_rate`` (e.g. 0.055) — the rate
    changes with RBI policy and is not hard-coded.
    """
    params = (getattr(rule, "parameters", None) or {}) if rule is not None else {}
    bank_rate = params.get("rbi_bank_rate")
    rows = conn.execute("""
        SELECT pi.id, pi.vendor_id, v.name, pi.invoice_number,
               pi.total_amount - COALESCE(pi.paid_amount, 0) as unpaid,
               COALESCE(pi.receipt_date, pi.invoice_date) as accepted_on,
               pi.due_date
        FROM purchase_invoices pi
        JOIN vendors v ON v.id = pi.vendor_id
        WHERE pi.company_id = ?
          AND pi.status NOT IN ('paid', 'cancelled')
          AND LOWER(v.msme_status) IN ('micro', 'small')
          AND pi.total_amount - COALESCE(pi.paid_amount, 0) > 0
    """, [company_id]).fetchall()

    today = date.today()
    out = []
    for inv_id, vendor_id, vendor, number, unpaid, accepted_on, due_date in rows:
        unpaid = float(unpaid)
        allowed = min((due_date - accepted_on).days, 45) if due_date else 15
        statutory_due = accepted_on + timedelta(days=max(allowed, 0))
        days_late = (today - statutory_due).days
        if days_late <= 0:
            continue
        interest = None
        if bank_rate is not None:
            r_annual = 3 * float(bank_rate)
            months, rem_days = _months_between(statutory_due, today)
            compounded = unpaid * (1 + r_annual / 12) ** months
            interest = round(compounded * (1 + r_annual * rem_days / 365) - unpaid, 2)
        interest_txt = (f" s.16 interest at 3× Bank Rate ({float(bank_rate) * 100:.2f}%), compounded monthly: ₹{interest:,.2f}."
                        if interest is not None else " Set parameters.rbi_bank_rate on this rule to compute s.16 interest.")
        out.append({
            "title": f"MSME Payment Delayed: {vendor} — Invoice {number}",
            "description": (
                f"MSME vendor {vendor} invoice {number}: ₹{unpaid:,.2f} unpaid {days_late} days past the "
                f"s.15 due date {statutory_due} (accepted {accepted_on}). Unpaid amount is exposed to "
                f"disallowance u/s 43B(h) (not applicable to traders).{interest_txt}"
            ),
            "severity": "high",
            "financial_impact": unpaid,
            "evidence": {"vendor_name": vendor, "invoice_number": number, "unpaid": unpaid,
                         "accepted_on": str(accepted_on), "statutory_due": str(statutory_due),
                         "days_late": days_late, "s16_interest": interest},
            "key": f"invoice_id={inv_id}",
        })
    return out
