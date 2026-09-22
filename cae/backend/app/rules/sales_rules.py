"""Sales audit rules SAL-001 to SAL-034."""
from datetime import date

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
            "key": f"invoice_number={r[0]}",
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
          -- Exact test: a BIGINT cast rounds, so ₹1,23,999.60 would pass as 1,24,000.
          AND total_amount % 1000 = 0
          AND status != 'cancelled'
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Round Amount Invoice: {r[1]} (₹{float(r[2]):,.0f})",
            "description": f"Invoice {r[1]} has a suspiciously round value of ₹{float(r[2]):,.0f}. Round amounts >₹1L may indicate fabricated invoices.",
            "severity": "medium",
            "financial_impact": float(r[2]),
            "evidence": {"invoice_id": str(r[0]), "invoice_number": r[1], "amount": float(r[2])},
            "key": f"invoice_id={r[0]}",
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
                "key": f"month={m}",
            }
            for m, v in spikes
        ]
    except Exception:
        return []


@register("SAL-004")
def sal_004(conn, company_id, rule):
    """Revenue Cut-Off Manipulation — invoice created long after period end."""
    # created_at is TIMESTAMPTZ in Postgres; cast so DuckDB can compare it with the
    # plain TIMESTAMP produced by DATE_TRUNC.
    rows = conn.execute("""
        SELECT id, invoice_number, invoice_date, created_at, total_amount
        FROM sales_invoices
        WHERE company_id = ?
          AND CAST(created_at AS TIMESTAMP) > DATE_TRUNC('month', invoice_date) + INTERVAL '35' DAY
          AND status != 'cancelled'
          AND total_amount > 100000
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Cut-Off Violation: Invoice {r[1]}",
            "description": f"Invoice {r[1]} dated {r[2]} was entered {r[3].date() if hasattr(r[3], 'date') else r[3]}. Possible revenue cut-off manipulation.",
            "severity": "critical",
            "financial_impact": float(r[4]),
            "evidence": {"invoice_number": r[1], "invoice_date": str(r[2]), "created_at": str(r[3]), "amount": float(r[4])},
            "key": f"invoice_id={r[0]}",
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
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Excessive Discount: Invoice {r[1]} ({float(r[3]):.1f}%)",
            "description": f"Invoice {r[1]} has {float(r[3]):.1f}% discount — exceeds 15% policy threshold.",
            "severity": "high",
            "financial_impact": float(r[2]) * float(r[3]) / 100,
            "evidence": {"invoice_number": r[1], "discount_pct": float(r[3]), "amount": float(r[2])},
            "key": f"invoice_id={r[0]}",
        }
        for r in rows
    ]


@register("SAL-007")
def sal_007(conn, company_id, rule):
    """Missing E-Way Bill (consignment >₹50,000, Rule 138 CGST Rules)."""
    rows = conn.execute("""
        SELECT id, invoice_number, total_amount
        FROM sales_invoices
        WHERE company_id = ? AND total_amount > 50000
          AND (e_way_bill_number IS NULL OR e_way_bill_number = '')
          AND status != 'cancelled'
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Missing E-Way Bill: Invoice {r[1]}",
            "description": f"Invoice {r[1]} (₹{float(r[2]):,.0f}) exceeds ₹50,000 threshold but has no E-Way Bill.",
            "severity": "high",
            "financial_impact": float(r[2]) * 0.02,
            "evidence": {"invoice_number": r[1], "amount": float(r[2])},
            "key": f"invoice_id={r[0]}",
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
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Manual Invoice: {r[1]}",
            "description": f"Invoice {r[1]} (₹{float(r[2]):,.0f}) was created manually without ERP system controls.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"invoice_number": r[1], "amount": float(r[2]), "source": str(r[3])},
            "key": f"invoice_id={r[0]}",
        }
        for r in rows
    ]


@register("SAL-010")
def sal_010(conn, company_id, rule):
    """Credit Limit Breach — open receivables exceed the customer's credit limit."""
    rows = conn.execute("""
        SELECT c.id, c.name, c.credit_limit, SUM(si.outstanding_amount) as outstanding
        FROM sales_invoices si
        JOIN customers c ON c.id = si.customer_id
        WHERE si.company_id = ?
          AND si.status NOT IN ('cancelled', 'paid')
          AND c.credit_limit > 0
        GROUP BY c.id, c.name, c.credit_limit
        HAVING SUM(si.outstanding_amount) > c.credit_limit
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Credit Limit Breach: {r[1]}",
            "description": f"Customer {r[1]} has ₹{float(r[3]):,.2f} outstanding against a credit limit of ₹{float(r[2]):,.2f} — exceeded by ₹{float(r[3]) - float(r[2]):,.2f}.",
            "severity": "high",
            "financial_impact": float(r[3]) - float(r[2]),
            "evidence": {"customer_id": str(r[0]), "customer": r[1], "credit_limit": float(r[2]), "outstanding": float(r[3])},
            "key": f"customer_id={r[0]}",
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
            "key": f"customer_id={r[0]}|month={r[1]}",
        }
        for r in rows
    ]


@register("SAL-019")
def sal_019(conn, company_id, rule):
    """Weekend/Holiday Invoicing (high-value invoices on weekends)."""
    # ISODOW: Monday=1 … Saturday=6, Sunday=7. (DuckDB's DAYOFWEEK is Sunday=0.)
    rows = conn.execute("""
        SELECT id, invoice_number, invoice_date, total_amount
        FROM sales_invoices
        WHERE company_id = ? AND status != 'cancelled'
          AND ISODOW(invoice_date) IN (6, 7)
          AND total_amount > 500000
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Weekend Invoicing: {r[1]}",
            "description": f"Invoice {r[1]} (₹{float(r[3]):,.0f}) was created on {r[2]} — a weekend day.",
            "severity": "medium",
            "financial_impact": 0,
            "evidence": {"invoice_number": r[1], "date": str(r[2]), "amount": float(r[3])},
            "key": f"invoice_id={r[0]}",
        }
        for r in rows
    ]


# E-invoicing AATO thresholds under Notification 13/2020-CT as amended
# (61/2020, 88/2020, 5/2021, 1/2022, 17/2022, 10/2023): effective date → threshold in ₹.
E_INVOICE_THRESHOLDS = [
    (date(2023, 8, 1), 5_00_00_000),
    (date(2022, 10, 1), 10_00_00_000),
    (date(2022, 4, 1), 20_00_00_000),
    (date(2021, 4, 1), 50_00_00_000),
    (date(2021, 1, 1), 100_00_00_000),
    (date(2020, 10, 1), 500_00_00_000),
]


def _fy_start(d: date) -> int:
    return d.year if d.month >= 4 else d.year - 1


@register("SAL-021")
def sal_021(conn, company_id, rule):
    """E-Invoice IRN Missing on a B2B invoice once AATO crossed the notified threshold.

    Applicability turns on aggregate turnover in any preceding FY from 2017-18, not
    on invoice value. AATO here is computed from the sales loaded for this company
    only (taxable value, non-cancelled); a PAN with other GSTINs must be checked
    manually, as must exempt classes (banks, insurers, GTA, SEZ units, etc.).
    """
    fy_turnover = {
        int(r[0]): float(r[1])
        for r in conn.execute("""
            SELECT CASE WHEN MONTH(invoice_date) >= 4 THEN YEAR(invoice_date) ELSE YEAR(invoice_date) - 1 END,
                   SUM(taxable_amount)
            FROM sales_invoices
            WHERE company_id = ? AND status != 'cancelled'
            GROUP BY 1
        """, [company_id]).fetchall()
    }
    if not fy_turnover:
        return []
    rows = conn.execute("""
        SELECT si.id, si.invoice_number, si.invoice_date, si.total_amount,
               COALESCE(si.cgst_amount, 0) + COALESCE(si.sgst_amount, 0) + COALESCE(si.igst_amount, 0) as tax
        FROM sales_invoices si
        JOIN customers c ON c.id = si.customer_id
        WHERE si.company_id = ? AND si.status != 'cancelled'
          AND c.gstin IS NOT NULL AND c.gstin != ''
          AND (si.e_invoice_irn IS NULL OR si.e_invoice_irn = '')
          AND si.invoice_date >= DATE '2020-10-01'
    """, [company_id]).fetchall()

    out = []
    for inv_id, number, inv_date, amount, tax in rows:
        threshold = next(t for eff, t in E_INVOICE_THRESHOLDS if inv_date >= eff)
        fy = _fy_start(inv_date)
        crossed = [(y, v) for y, v in fy_turnover.items() if 2017 <= y < fy and v > threshold]
        if not crossed:
            continue
        y, v = max(crossed)
        # Rule 48(5): an invoice without IRN is not a valid invoice; s.122(1) penalty
        # is the higher of ₹10,000 or the tax involved.
        penalty = max(10000.0, float(tax))
        out.append({
            "title": f"Missing E-Invoice IRN: {number}",
            "description": (
                f"B2B invoice {number} dated {inv_date} (₹{float(amount):,.2f}) has no IRN. "
                f"Books turnover for FY {y}-{str(y + 1)[2:]} was ₹{v:,.2f}, above the ₹{threshold:,.0f} "
                f"e-invoicing threshold applicable on that date. Invalid invoice under Rule 48(5); "
                f"penalty u/s 122(1) is the higher of ₹10,000 or tax (₹{float(tax):,.2f})."
            ),
            "severity": "high",
            "financial_impact": penalty,
            "evidence": {"invoice_number": number, "invoice_date": str(inv_date), "amount": float(amount),
                         "tax": float(tax), "aato_fy": f"{y}-{str(y + 1)[2:]}", "aato": v, "threshold": threshold},
            "key": f"invoice_id={inv_id}",
        })
    return out


@register("SAL-022")
def sal_022(conn, company_id, rule):
    """Cash receipt of ₹2 lakh or more from one person in a day (s.269ST)."""
    rows = conn.execute("""
        SELECT counterparty_name, CAST(transaction_date AS DATE) as d, COUNT(*) as cnt, SUM(amount) as total
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'credit' AND transaction_mode = 'cash'
        GROUP BY counterparty_name, CAST(transaction_date AS DATE)
        HAVING SUM(amount) >= 200000
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Cash Receipt ≥₹2L (s.269ST): {r[0]} on {r[1]}",
            "description": f"₹{float(r[3]):,.2f} received in cash from {r[0]} on {r[1]} across {r[2]} receipt(s). Section 269ST bars cash receipts of ₹2,00,000 or more from a person in a day; penalty u/s 271DA equals the amount received.",
            "severity": "critical",
            "financial_impact": float(r[3]),
            "evidence": {"party": r[0], "date": str(r[1]), "count": r[2], "total": float(r[3])},
            "key": f"party={r[0]}|date={r[1]}",
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
            "title": f"Duplicate Sale: Customer {r[0]} on {r[1]} (₹{float(r[2]):,.2f})",
            "description": f"{r[3]} invoices to same customer on same day for same amount ₹{float(r[2]):,.0f}.",
            "severity": "critical",
            "financial_impact": float(r[2]) * (r[3] - 1),
            "evidence": {"customer_id": str(r[0]), "date": str(r[1]), "amount": float(r[2]), "count": r[3]},
            "key": f"customer_id={r[0]}|date={r[1]}|amount={float(r[2]):.2f}",
        }
        for r in rows
    ]
