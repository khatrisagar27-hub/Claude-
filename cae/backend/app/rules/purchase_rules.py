"""Purchase audit rules PUR-001 to PUR-031."""
from app.rules import register


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
            "title": f"Duplicate Vendor Invoice: {r[1]}",
            "description": f"Vendor invoice {r[1]} appears {r[2]} times. Risk of duplicate payment: ₹{float(r[3]):,.0f}.",
            "severity": "critical",
            "financial_impact": float(r[3]),
            "evidence": {"vendor_id": str(r[0]), "invoice_number": r[1], "count": r[2], "total": float(r[3])},
        }
        for r in rows
    ]


@register("PUR-002")
def pur_002(conn, company_id, rule):
    """PO vs Invoice Amount Mismatch >5%."""
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, total_amount,
               CAST(raw_data->>'po_value' AS DOUBLE) as po_value
        FROM purchase_invoices
        WHERE company_id = ?
          AND raw_data->>'po_value' IS NOT NULL
          AND CAST(raw_data->>'po_value' AS DOUBLE) > 0
          AND ABS(total_amount - CAST(raw_data->>'po_value' AS DOUBLE))
              / CAST(raw_data->>'po_value' AS DOUBLE) > 0.05
        LIMIT 30
    """, [company_id]).fetchall()
    return [
        {
            "title": f"PO-Invoice Mismatch: {r[2]}",
            "description": f"Invoice {r[2]} (₹{float(r[3]):,.0f}) deviates more than 5% from PO value ₹{float(r[4]):,.0f}.",
            "severity": "high",
            "financial_impact": abs(float(r[3]) - float(r[4])),
            "evidence": {"invoice_number": r[2], "invoice_value": float(r[3]), "po_value": float(r[4])},
        }
        for r in rows
    ]


@register("PUR-004")
def pur_004(conn, company_id, rule):
    """Invoice Without PO above ₹1L."""
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, total_amount
        FROM purchase_invoices
        WHERE company_id = ? AND total_amount > 100000
          AND (our_po_number IS NULL OR our_po_number = '')
          AND status NOT IN ('cancelled', 'disputed')
        LIMIT 30
    """, [company_id]).fetchall()
    return [
        {
            "title": f"No PO for Invoice: {r[2]}",
            "description": f"Purchase invoice {r[2]} (₹{float(r[3]):,.0f}) has no PO reference. Authorization bypass risk.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"vendor_id": str(r[1]), "invoice_number": r[2], "amount": float(r[3])},
        }
        for r in rows
    ]


@register("PUR-006")
def pur_006(conn, company_id, rule):
    """Split POs below approval threshold."""
    rows = conn.execute("""
        SELECT vendor_id, DATE_TRUNC('month', invoice_date) as month,
               COUNT(*) as cnt, SUM(total_amount) as total
        FROM purchase_invoices
        WHERE company_id = ? AND total_amount < 100000
          AND status NOT IN ('cancelled')
        GROUP BY vendor_id, DATE_TRUNC('month', invoice_date)
        HAVING COUNT(*) >= 5 AND SUM(total_amount) > 300000
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Split POs: Vendor {r[0]} in {r[1]}",
            "description": f"Vendor {r[0]} has {r[2]} small invoices totaling ₹{float(r[3]):,.0f} in {r[1]}. Possible threshold splitting.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"vendor_id": str(r[0]), "month": str(r[1]), "count": r[2], "total": float(r[3])},
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
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Unapproved Large Invoice: {r[2]}",
            "description": f"Invoice {r[2]} of ₹{float(r[3]):,.0f} has no approval. Advance payment risk.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"vendor_id": str(r[1]), "invoice_number": r[2], "amount": float(r[3])},
        }
        for r in rows
    ]


@register("PUR-016")
def pur_016(conn, company_id, rule):
    """Duplicate Payment — invoices with same vendor, same amount, both paid."""
    rows = conn.execute("""
        SELECT vendor_id, total_amount, COUNT(*) as cnt, SUM(paid_amount) as total_paid
        FROM purchase_invoices
        WHERE company_id = ? AND status = 'paid'
        GROUP BY vendor_id, total_amount
        HAVING COUNT(*) > 1 AND SUM(paid_amount) > total_amount * COUNT(*)
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Possible Duplicate Payment: Vendor {r[0]} ₹{float(r[1]):,.0f}",
            "description": f"Vendor {r[0]} has {r[2]} paid invoices with identical amount ₹{float(r[1]):,.0f}. Review for duplicate payment.",
            "severity": "critical",
            "financial_impact": float(r[1]) * (r[2] - 1),
            "evidence": {"vendor_id": str(r[0]), "amount": float(r[1]), "count": r[2], "total_paid": float(r[3])},
        }
        for r in rows
    ]


@register("PUR-021")
def pur_021(conn, company_id, rule):
    """Invoice Date Before Receipt Date (goods received before invoice)."""
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, total_amount, invoice_date, receipt_date
        FROM purchase_invoices
        WHERE company_id = ?
          AND receipt_date IS NOT NULL
          AND invoice_date > receipt_date
          AND total_amount > 100000
        LIMIT 20
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Invoice Before Receipt: {r[2]}",
            "description": f"Invoice {r[2]} (₹{float(r[3]):,.0f}) dated {r[4]} but goods received {r[5]}. Backdated receipt risk.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"invoice_number": r[2], "invoice_date": str(r[4]), "receipt_date": str(r[5]), "amount": float(r[3])},
        }
        for r in rows
    ]


@register("PUR-022")
def pur_022(conn, company_id, rule):
    """Vendor Address Matches Employee Address."""
    rows = conn.execute("""
        SELECT v.id, v.name, e.id as emp_id, e.full_name as emp_name
        FROM vendors v
        JOIN employees e ON LOWER(TRIM(COALESCE(v.address_line1, ''))) = LOWER(TRIM(COALESCE(e.bank_account_number, 'X')))
        WHERE v.company_id = ? AND e.company_id = ?
          AND v.address_line1 IS NOT NULL AND v.address_line1 != ''
          AND LENGTH(v.address_line1) > 10
        LIMIT 10
    """, [company_id, company_id]).fetchall()
    return [
        {
            "title": f"Vendor-Employee Address Match: {r[1]}",
            "description": f"Vendor {r[1]} shares address with employee {r[3]}. Possible ghost vendor / insider fraud.",
            "severity": "critical",
            "financial_impact": 0,
            "evidence": {"vendor_id": str(r[0]), "vendor_name": r[1], "employee_id": str(r[2]), "employee_name": r[3]},
        }
        for r in rows
    ]


@register("PUR-031")
def pur_031(conn, company_id, rule):
    """MSME Payment Delayed Beyond 45 Days."""
    rows = conn.execute("""
        SELECT pi.id, pi.vendor_id, v.name, pi.invoice_number, pi.total_amount,
               DATEDIFF('day', pi.invoice_date, CURRENT_DATE) as days_outstanding
        FROM purchase_invoices pi
        JOIN vendors v ON v.id = pi.vendor_id
        WHERE pi.company_id = ?
          AND pi.status NOT IN ('paid', 'cancelled')
          AND v.msme_status IN ('Micro', 'Small', 'Medium')
          AND DATEDIFF('day', pi.invoice_date, CURRENT_DATE) > 45
        LIMIT 30
    """, [company_id]).fetchall()
    return [
        {
            "title": f"MSME Payment Delayed: {r[2]} — {r[5]} days",
            "description": f"MSME vendor {r[2]} invoice {r[3]} (₹{float(r[4]):,.0f}) outstanding {r[5]} days. Violates MSMED Act.",
            "severity": "high",
            "financial_impact": float(r[4]) * 0.18 * r[5] / 365,
            "evidence": {"vendor_name": r[2], "invoice_number": r[3], "amount": float(r[4]), "days": r[5]},
        }
        for r in rows
    ]
