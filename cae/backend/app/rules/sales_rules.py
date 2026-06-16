"""Sales audit rules SAL-001 to SAL-034."""
from app.rules import register


@register("SAL-001")
def sal_001(conn, company_id, rule):
    """Duplicate Invoice Number."""
    rows = conn.execute("""
        SELECT invoice_number, COUNT(*) as cnt, SUM(total_amount) as total
        FROM sales_invoices
        WHERE company_id = ? AND status != 'cancelled'
        GROUP BY invoice_number
        HAVING COUNT(*) > 1
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Duplicate Invoice No: {r[0]}",
            "description": f"Invoice number {r[0]} appears {r[1]} times. Total value: ₹{float(r[2]):,.2f}",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"invoice_number": r[0], "count": r[1], "total": float(r[2])},
        }
        for r in rows
    ]


@register("SAL-002")
def sal_002(conn, company_id, rule):
    """Round Amount Invoice (>₹1L, ends in 000)."""
    rows = conn.execute("""
        SELECT id, invoice_number, total_amount
        FROM sales_invoices
        WHERE company_id = ? AND total_amount >= 100000
          AND CAST(total_amount AS BIGINT) % 1000 = 0
          AND status != 'cancelled'
        LIMIT 50
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Round Amount Invoice: {r[1]} (₹{float(r[2]):,.0f})",
            "description": f"Invoice {r[1]} has a suspiciously round value of ₹{float(r[2]):,.0f}. Round amounts >₹1L may indicate fabricated invoices.",
            "severity": "medium",
            "financial_impact": float(r[2]),
            "evidence": {"invoice_id": str(r[0]), "invoice_number": r[1], "amount": float(r[2])},
        }
        for r in rows
    ]


@register("SAL-003")
def sal_003(conn, company_id, rule):
    """Month-End Sales Spike (>3σ above mean)."""
    try:
        import numpy as np
        rows = conn.execute("""
            SELECT DATE_TRUNC('month', invoice_date) as month, SUM(total_amount) as monthly_total
            FROM sales_invoices
            WHERE company_id = ? AND status != 'cancelled'
            GROUP BY DATE_TRUNC('month', invoice_date)
            ORDER BY month
        """, [company_id]).fetchall()
        if len(rows) < 4:
            return []
        totals = [float(r[1]) for r in rows]
        mean, std = float(np.mean(totals)), float(np.std(totals))
        if std == 0:
            return []
        spikes = [(rows[i][0], totals[i]) for i in range(len(totals)) if totals[i] > mean + 3 * std]
        return [
            {
                "title": f"Month-End Sales Spike: {m}",
                "description": f"Sales in {m} were ₹{v:,.0f} — more than 3σ above the mean of ₹{mean:,.0f}.",
                "severity": "high",
                "financial_impact": v - mean,
                "evidence": {"month": str(m), "amount": v, "mean": mean, "std": std},
            }
            for m, v in spikes
        ]
    except Exception:
        return []


@register("SAL-004")
def sal_004(conn, company_id, rule):
    """Revenue Cut-Off Manipulation — invoice created long after period end."""
    rows = conn.execute("""
        SELECT id, invoice_number, invoice_date, created_at, total_amount
        FROM sales_invoices
        WHERE company_id = ?
          AND created_at > DATE_TRUNC('month', invoice_date) + INTERVAL '35' DAY
          AND status != 'cancelled'
          AND total_amount > 100000
        LIMIT 30
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Cut-Off Violation: Invoice {r[1]}",
            "description": f"Invoice {r[1]} dated {r[2]} was entered {r[3].date() if hasattr(r[3], 'date') else r[3]}. Possible revenue cut-off manipulation.",
            "severity": "critical",
            "financial_impact": float(r[4]),
            "evidence": {"invoice_number": r[1], "invoice_date": str(r[2]), "created_at": str(r[3]), "amount": float(r[4])},
        }
        for r in rows
    ]


@register("SAL-005")
def sal_005(conn, company_id, rule):
    """Excessive Discount (>15% — gross vs taxable)."""
    rows = conn.execute("""
        SELECT id, invoice_number, total_amount,
               discount_amount / NULLIF(gross_amount, 0) * 100 as discount_pct
        FROM sales_invoices
        WHERE company_id = ? AND status != 'cancelled'
          AND gross_amount > 0
          AND discount_amount / gross_amount > 0.15
        LIMIT 30
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Excessive Discount: Invoice {r[1]} ({float(r[3]):.1f}%)",
            "description": f"Invoice {r[1]} has {float(r[3]):.1f}% discount — exceeds 15% policy threshold.",
            "severity": "high",
            "financial_impact": float(r[2]) * float(r[3]) / 100,
            "evidence": {"invoice_number": r[1], "discount_pct": float(r[3]), "amount": float(r[2])},
        }
        for r in rows
    ]


@register("SAL-007")
def sal_007(conn, company_id, rule):
    """Missing E-Way Bill (consignment >₹50,000)."""
    rows = conn.execute("""
        SELECT id, invoice_number, total_amount
        FROM sales_invoices
        WHERE company_id = ? AND total_amount > 50000
          AND (e_way_bill_number IS NULL OR e_way_bill_number = '')
          AND status != 'cancelled'
        LIMIT 50
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Missing E-Way Bill: Invoice {r[1]}",
            "description": f"Invoice {r[1]} (₹{float(r[2]):,.0f}) exceeds ₹50,000 threshold but has no E-Way Bill.",
            "severity": "high",
            "financial_impact": float(r[2]) * 0.02,
            "evidence": {"invoice_number": r[1], "amount": float(r[2])},
        }
        for r in rows
    ]


@register("SAL-009")
def sal_009(conn, company_id, rule):
    """Manual Invoice Override — entered via non-ERP source."""
    rows = conn.execute("""
        SELECT id, invoice_number, total_amount, erp_source
        FROM sales_invoices
        WHERE company_id = ?
          AND (erp_source = 'manual' OR erp_source IS NULL)
          AND total_amount > 100000
          AND status != 'cancelled'
        LIMIT 30
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Manual Invoice: {r[1]}",
            "description": f"Invoice {r[1]} (₹{float(r[2]):,.0f}) was created manually without ERP system controls.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"invoice_number": r[1], "amount": float(r[2]), "source": str(r[3])},
        }
        for r in rows
    ]


@register("SAL-016")
def sal_016(conn, company_id, rule):
    """Invoice Cancellation Abuse — >5 cancels/month per customer."""
    rows = conn.execute("""
        SELECT customer_id, DATE_TRUNC('month', invoice_date) as month, COUNT(*) as cnt
        FROM sales_invoices
        WHERE company_id = ? AND status = 'cancelled'
        GROUP BY customer_id, DATE_TRUNC('month', invoice_date)
        HAVING COUNT(*) > 5
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Cancellation Abuse: Customer {r[0]} in {r[1]}",
            "description": f"Customer {r[0]} had {r[2]} invoice cancellations in {r[1]}.",
            "severity": "high",
            "financial_impact": 0,
            "evidence": {"customer_id": str(r[0]), "month": str(r[1]), "cancellations": r[2]},
        }
        for r in rows
    ]


@register("SAL-019")
def sal_019(conn, company_id, rule):
    """Weekend/Holiday Invoicing (high-value invoices on weekends)."""
    rows = conn.execute("""
        SELECT id, invoice_number, invoice_date, total_amount
        FROM sales_invoices
        WHERE company_id = ? AND status != 'cancelled'
          AND DAYOFWEEK(invoice_date) IN (1, 7)
          AND total_amount > 500000
        LIMIT 30
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Weekend Invoicing: {r[1]}",
            "description": f"Invoice {r[1]} (₹{float(r[3]):,.0f}) was created on {r[2]} — a weekend day.",
            "severity": "medium",
            "financial_impact": 0,
            "evidence": {"invoice_number": r[1], "date": str(r[2]), "amount": float(r[3])},
        }
        for r in rows
    ]


@register("SAL-021")
def sal_021(conn, company_id, rule):
    """E-Invoice IRN Missing (invoice above GST e-invoice threshold)."""
    rows = conn.execute("""
        SELECT id, invoice_number, total_amount
        FROM sales_invoices
        WHERE company_id = ? AND status != 'cancelled'
          AND total_amount > 500000
          AND (e_invoice_irn IS NULL OR e_invoice_irn = '')
        LIMIT 30
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Missing E-Invoice IRN: {r[1]}",
            "description": f"Invoice {r[1]} (₹{float(r[2]):,.0f}) is above e-invoice threshold but has no IRN. GST compliance risk.",
            "severity": "high",
            "financial_impact": float(r[2]) * 0.10,
            "evidence": {"invoice_number": r[1], "amount": float(r[2])},
        }
        for r in rows
    ]


@register("SAL-034")
def sal_034(conn, company_id, rule):
    """Multiple Invoices — Same Customer, Same Day, Same Amount."""
    rows = conn.execute("""
        SELECT customer_id, invoice_date, total_amount, COUNT(*) as cnt
        FROM sales_invoices
        WHERE company_id = ? AND status != 'cancelled'
        GROUP BY customer_id, invoice_date, total_amount
        HAVING COUNT(*) > 1
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Duplicate Sale: Customer {r[0]} on {r[1]}",
            "description": f"{r[3]} invoices to same customer on same day for same amount ₹{float(r[2]):,.0f}.",
            "severity": "critical",
            "financial_impact": float(r[2]) * (r[3] - 1),
            "evidence": {"customer_id": str(r[0]), "date": str(r[1]), "amount": float(r[2]), "count": r[3]},
        }
        for r in rows
    ]
