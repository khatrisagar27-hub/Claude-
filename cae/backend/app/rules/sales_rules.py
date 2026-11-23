"""Sales audit rules SAL-001 to SAL-034."""
from app.rules import register, param, fy_sql, as_date, bulk_load_days_sql
from app.statutory import gst, income_tax


def _turnover_by_fy(conn, company_id) -> dict[int, float]:
    """Taxable sales per financial year (start year) from the books."""
    rows = conn.execute(f"""
        SELECT {fy_sql('invoice_date')} AS fy, SUM(taxable_amount)
        FROM sales_invoices_all
        WHERE company_id = ? AND status != 'cancelled'
        GROUP BY 1
    """, [company_id]).fetchall()
    return {int(r[0]): float(r[1] or 0) for r in rows}


@register("SAL-001")
def sal_001(conn, company_id, rule):
    """Duplicate Invoice Number within a financial year (Rule 46(b) CGST Rules)."""
    rows = conn.execute(f"""
        SELECT invoice_number, {fy_sql('invoice_date')} AS fy, COUNT(*) AS cnt, SUM(total_amount) AS total,
               STRING_AGG(CAST(invoice_date AS VARCHAR) || ' ₹' || CAST(ROUND(total_amount, 2) AS VARCHAR), '; ') AS lines
        FROM sales_invoices_all
        WHERE company_id = ? AND status != 'cancelled'
        GROUP BY invoice_number, fy
        HAVING COUNT(*) > 1 AND COUNT(*) FILTER (WHERE id IN (SELECT id FROM sales_invoices)) > 0
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Duplicate Invoice No: {r[0]} (FY {r[1]}-{str(r[1] + 1)[-2:]})",
            "description": f"Invoice number {r[0]} appears {r[2]} times in FY {r[1]}-{str(r[1] + 1)[-2:]}. "
                           f"Rule 46(b) requires a serial number unique for a financial year. Total value: ₹{float(r[3]):,.2f}",
            "severity": "critical",
            "financial_impact": float(r[3]),
            "evidence": {"invoice_number": r[0], "financial_year": f"{r[1]}-{str(r[1] + 1)[-2:]}", "count": r[2],
                         "total": float(r[3]), "invoices": r[4], "statutory_ref": "Rule 46(b), CGST Rules 2017"},
        }
        for r in rows
    ]


@register("SAL-002")
def sal_002(conn, company_id, rule):
    """Round Amount Invoice (at or above a value, exact multiple of a round figure)."""
    min_amount = float(param(rule, "min_amount", 100_000))
    multiple = int(param(rule, "multiple", 1000))
    rows = conn.execute("""
        SELECT id, invoice_number, total_amount
        FROM sales_invoices
        WHERE company_id = ? AND total_amount >= ?
          AND CAST(total_amount AS DECIMAL(18, 2)) % ? = 0
          AND status != 'cancelled'
        ORDER BY total_amount DESC
    """, [company_id, min_amount, multiple]).fetchall()
    return [
        {
            "title": f"Round Amount Invoice: {r[1]} (₹{float(r[2]):,.0f})",
            "description": f"Invoice {r[1]} is an exact multiple of ₹{multiple:,} (₹{float(r[2]):,.0f}). Tax-inclusive invoice values rarely land on round figures.",
            "severity": "medium",
            "financial_impact": float(r[2]),
            "evidence": {"invoice_id": str(r[0]), "invoice_number": r[1], "amount": float(r[2])},
        }
        for r in rows
    ]


@register("SAL-003")
def sal_003(conn, company_id, rule):
    """Monthly Sales Spike (more than N standard deviations above the mean)."""
    import numpy as np
    sigma = float(param(rule, "sigma", 3))
    min_months = int(param(rule, "min_months", 6))
    rows = conn.execute("""
        SELECT DATE_TRUNC('month', invoice_date) AS month, SUM(total_amount) AS monthly_total
        FROM sales_invoices_all
        WHERE company_id = ? AND status != 'cancelled'
        GROUP BY 1
        HAVING SUM(total_amount) > 0
        ORDER BY month
    """, [company_id]).fetchall()
    if len(rows) < min_months:
        return []
    totals = np.array([float(r[1]) for r in rows])
    mean, std = float(totals.mean()), float(totals.std())
    if std == 0:
        return []
    first = conn.execute("SELECT DATE_TRUNC('month', MIN(invoice_date)) FROM sales_invoices").fetchone()[0]
    out = []
    for (month, value) in rows:
        value = float(value)
        if first is not None and month < first:
            continue
        if value > mean + sigma * std:
            out.append({
                "title": f"Monthly Sales Spike: {str(month)[:7]}",
                "description": f"Sales in {str(month)[:7]} were ₹{value:,.0f} — more than {sigma:g}σ above the mean of ₹{mean:,.0f} (months with no sales excluded).",
                "severity": "high",
                "financial_impact": value - mean,
                "evidence": {"month": str(month)[:7], "amount": value, "mean": mean, "std": std},
            })
    return out


@register("SAL-004")
def sal_004(conn, company_id, rule):
    """Revenue Cut-Off — invoice entered well after the month it is dated in.
    Days that look like a bulk import are skipped (created_at is then the import date)."""
    grace_days = int(param(rule, "grace_days", 5))
    min_amount = float(param(rule, "min_amount", 100_000))
    bulk_months = int(param(rule, "bulk_load_months", 2))
    rows = conn.execute(f"""
        SELECT id, invoice_number, invoice_date, created_at, total_amount
        FROM sales_invoices
        WHERE company_id = ?
          AND CAST(created_at AS DATE) > LAST_DAY(invoice_date) + TO_DAYS(CAST(? AS INTEGER))
          AND CAST(created_at AS DATE) NOT IN {bulk_load_days_sql('sales_invoices_all', 'invoice_date')}
          AND status != 'cancelled'
          AND total_amount > ?
        ORDER BY total_amount DESC
    """, [company_id, grace_days, company_id, bulk_months, min_amount]).fetchall()
    return [
        {
            "title": f"Cut-Off Violation: Invoice {r[1]}",
            "description": f"Invoice {r[1]} dated {r[2]} was entered on {as_date(r[3])}, more than {grace_days} days after that month closed. Possible back-dating into an earlier period.",
            "severity": "critical",
            "financial_impact": float(r[4]),
            "evidence": {"invoice_number": r[1], "invoice_date": str(r[2]), "created_at": str(r[3]), "amount": float(r[4])},
        }
        for r in rows
    ]


@register("SAL-005")
def sal_005(conn, company_id, rule):
    """Excessive Discount (discount / gross above the policy limit)."""
    max_pct = float(param(rule, "max_discount_pct", 15))
    rows = conn.execute("""
        SELECT id, invoice_number, discount_amount,
               discount_amount / NULLIF(gross_amount, 0) * 100 AS discount_pct
        FROM sales_invoices
        WHERE company_id = ? AND status != 'cancelled'
          AND gross_amount > 0
          AND discount_amount / gross_amount * 100 > ?
        ORDER BY discount_amount DESC
    """, [company_id, max_pct]).fetchall()
    return [
        {
            "title": f"Excessive Discount: Invoice {r[1]} ({float(r[3]):.1f}%)",
            "description": f"Invoice {r[1]} carries a {float(r[3]):.1f}% discount (₹{float(r[2]):,.0f}) — above the {max_pct:g}% policy limit.",
            "severity": "high",
            "financial_impact": float(r[2]),
            "evidence": {"invoice_number": r[1], "discount_pct": float(r[3]), "discount_amount": float(r[2])},
        }
        for r in rows
    ]


@register("SAL-007")
def sal_007(conn, company_id, rule):
    """Missing E-Way Bill (consignment value above Rule 138 limit)."""
    threshold = float(param(rule, "threshold", gst.EWAY_BILL_THRESHOLD))
    rows = conn.execute("""
        SELECT id, invoice_number, total_amount
        FROM sales_invoices
        WHERE company_id = ? AND total_amount > ?
          AND (e_way_bill_number IS NULL OR e_way_bill_number = '')
          AND status != 'cancelled'
          -- Tally imports record whether the invoice moved stock; a services-only invoice needs no e-way bill
          AND COALESCE(json_extract_string(CAST(raw_data AS VARCHAR), '$.has_inventory'), 'true') != 'false'
        ORDER BY total_amount DESC
    """, [company_id, threshold]).fetchall()
    return [
        {
            "title": f"Missing E-Way Bill: Invoice {r[1]}",
            "description": f"Invoice {r[1]} (₹{float(r[2]):,.0f}) exceeds the ₹{threshold:,.0f} Rule 138 limit but has no e-way bill. "
                           "Confirm whether it is a supply of goods moved by road (services and exempt goods are outside Rule 138).",
            "severity": "high",
            "financial_impact": float(r[2]),
            "evidence": {"invoice_number": r[1], "amount": float(r[2]), "statutory_ref": "Rule 138, CGST Rules 2017"},
        }
        for r in rows
    ]


@register("SAL-009")
def sal_009(conn, company_id, rule):
    """Manual Invoice — entered outside the ERP."""
    min_amount = float(param(rule, "min_amount", 100_000))
    null_is_manual = bool(param(rule, "treat_null_source_as_manual", False))
    source_test = "(erp_source = 'manual' OR erp_source IS NULL)" if null_is_manual else "erp_source = 'manual'"
    rows = conn.execute(f"""
        SELECT id, invoice_number, total_amount, erp_source
        FROM sales_invoices
        WHERE company_id = ? AND {source_test}
          AND total_amount > ? AND status != 'cancelled'
        ORDER BY total_amount DESC
    """, [company_id, min_amount]).fetchall()
    return [
        {
            "title": f"Manual Invoice: {r[1]}",
            "description": f"Invoice {r[1]} (₹{float(r[2]):,.0f}) was entered manually, outside ERP controls.",
            "severity": "critical",
            "financial_impact": float(r[2]),
            "evidence": {"invoice_number": r[1], "amount": float(r[2]), "source": str(r[3])},
        }
        for r in rows
    ]


@register("SAL-010")
def sal_010(conn, company_id, rule):
    """Credit Limit Breach — customer outstanding above the approved limit."""
    rows = conn.execute("""
        SELECT c.id, c.name, c.credit_limit, SUM(s.outstanding_amount) AS outstanding
        FROM sales_invoices_all s
        JOIN customers c ON c.id = s.customer_id
        WHERE s.company_id = ? AND s.status != 'cancelled'
          AND c.credit_limit IS NOT NULL AND c.credit_limit > 0
        GROUP BY c.id, c.name, c.credit_limit
        HAVING SUM(s.outstanding_amount) > c.credit_limit
        ORDER BY SUM(s.outstanding_amount) - c.credit_limit DESC
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Credit Limit Breach: {r[1]}",
            "description": f"{r[1]} owes ₹{float(r[3]):,.0f} against an approved limit of ₹{float(r[2]):,.0f} (excess ₹{float(r[3]) - float(r[2]):,.0f}).",
            "severity": "high",
            "financial_impact": float(r[3]) - float(r[2]),
            "evidence": {"customer_id": str(r[0]), "customer": r[1], "credit_limit": float(r[2]), "outstanding": float(r[3])},
        }
        for r in rows
    ]


@register("SAL-016")
def sal_016(conn, company_id, rule):
    """Invoice Cancellation Abuse — too many cancellations per customer per month."""
    max_cancels = int(param(rule, "max_cancellations_per_month", 5))
    rows = conn.execute("""
        SELECT customer_id, DATE_TRUNC('month', invoice_date) AS month, COUNT(*) AS cnt, SUM(total_amount)
        FROM sales_invoices
        WHERE company_id = ? AND status = 'cancelled'
        GROUP BY customer_id, month
        HAVING COUNT(*) > ?
    """, [company_id, max_cancels]).fetchall()
    return [
        {
            "title": f"Cancellation Abuse: Customer {r[0]} in {str(r[1])[:7]}",
            "description": f"Customer {r[0]} had {r[2]} invoice cancellations (₹{float(r[3] or 0):,.0f}) in {str(r[1])[:7]}.",
            "severity": "high",
            "financial_impact": float(r[3] or 0),
            "evidence": {"customer_id": str(r[0]), "month": str(r[1])[:7], "cancellations": r[2]},
        }
        for r in rows
    ]


@register("SAL-019")
def sal_019(conn, company_id, rule):
    """Weekend Invoicing (high-value invoices dated Saturday or Sunday)."""
    min_amount = float(param(rule, "min_amount", 500_000))
    rows = conn.execute("""
        SELECT id, invoice_number, invoice_date, total_amount, DAYNAME(invoice_date)
        FROM sales_invoices
        WHERE company_id = ? AND status != 'cancelled'
          AND ISODOW(invoice_date) IN (6, 7)
          AND total_amount > ?
        ORDER BY total_amount DESC
    """, [company_id, min_amount]).fetchall()
    return [
        {
            "title": f"Weekend Invoicing: {r[1]}",
            "description": f"Invoice {r[1]} (₹{float(r[3]):,.0f}) is dated {r[2]}, a {r[4]}.",
            "severity": "medium",
            "financial_impact": float(r[3]),
            "evidence": {"invoice_number": r[1], "date": str(r[2]), "weekday": r[4], "amount": float(r[3])},
        }
        for r in rows
    ]


@register("SAL-021")
def sal_021(conn, company_id, rule):
    """E-Invoice IRN Missing on a B2B invoice where e-invoicing applies (Rule 48(4))."""
    override = param(rule, "aato_override", None)
    turnover = _turnover_by_fy(conn, company_id)
    rows = conn.execute(f"""
        SELECT s.id, s.invoice_number, s.invoice_date, s.total_amount, c.name, c.gstin,
               {fy_sql('s.invoice_date')} AS fy
        FROM sales_invoices s
        JOIN customers c ON c.id = s.customer_id
        WHERE s.company_id = ? AND s.status != 'cancelled'
          AND c.gstin IS NOT NULL AND LENGTH(TRIM(c.gstin)) = 15
          AND (s.e_invoice_irn IS NULL OR s.e_invoice_irn = '')
          AND s.total_amount > 0
        ORDER BY s.invoice_date
    """, [company_id]).fetchall()
    out = []
    for r in rows:
        inv_date, fy = as_date(r[2]), int(r[6])
        preceding = [v for y, v in turnover.items() if y < fy and y >= 2017]
        aato = float(override) if override is not None else max(preceding, default=0.0)
        if not gst.e_invoice_applicable(aato, inv_date):
            continue
        out.append({
            "title": f"Missing E-Invoice IRN: {r[1]}",
            "description": f"B2B invoice {r[1]} dated {inv_date} to {r[4]} ({r[5]}) has no IRN. Turnover in a preceding year "
                           f"(₹{aato:,.0f}) exceeds the ₹{gst.e_invoice_threshold(inv_date):,} e-invoice threshold — "
                           "an invoice without an IRN is not a valid tax invoice and the buyer's ITC is exposed.",
            "severity": "high",
            "financial_impact": float(r[3]),
            "evidence": {"invoice_number": r[1], "invoice_date": str(inv_date), "customer_gstin": r[5],
                         "amount": float(r[3]), "aato_used": aato,
                         "statutory_ref": "Rule 48(4), CGST Rules 2017; Notf 13/2020-CT as amended"},
        })
    return out


@register("SAL-022")
def sal_022(conn, company_id, rule):
    """Cash Receipt of Rs.2 lakh or more from a person in a day (s.186 / s.269ST)."""
    limit = float(param(rule, "threshold", income_tax.CASH_RECEIPT_LIMIT))
    rows = conn.execute("""
        SELECT counterparty_name, transaction_date, COUNT(*) AS cnt, SUM(amount) AS total
        FROM bank_transactions
        WHERE company_id = ? AND transaction_type = 'credit'
          AND LOWER(transaction_mode) = 'cash'
          AND counterparty_name IS NOT NULL AND TRIM(counterparty_name) != ''
          AND LOWER(counterparty_name) NOT IN ('self', 'cash', 'cash deposit')
        GROUP BY counterparty_name, transaction_date
        HAVING SUM(amount) >= ?
        ORDER BY total DESC
    """, [company_id, limit]).fetchall()
    out = []
    for r in rows:
        on = as_date(r[1])
        ref = income_tax.section_ref("cash_receipt", on)
        out.append({
            "title": f"Cash Receipt ≥ ₹2L: {r[0]} on {on}",
            "description": f"₹{float(r[3]):,.0f} received in cash from {r[0]} on {on} ({r[2]} entr{'y' if r[2] == 1 else 'ies'}). "
                           f"Receipts of ₹{limit:,.0f} or more in a day from one person must come through banking channels — {ref}. "
                           "The penalty equals the amount received.",
            "severity": "critical",
            "financial_impact": float(r[3]),
            "evidence": {"party": r[0], "date": str(on), "count": r[2], "total": float(r[3]), "statutory_ref": ref},
        })
    return out


@register("SAL-034")
def sal_034(conn, company_id, rule):
    """Multiple Invoices — Same Customer, Same Day, Same Amount."""
    rows = conn.execute("""
        SELECT customer_id, invoice_date, total_amount, COUNT(*) AS cnt
        FROM sales_invoices
        WHERE company_id = ? AND status != 'cancelled' AND total_amount > 0
        GROUP BY customer_id, invoice_date, total_amount
        HAVING COUNT(*) > 1
    """, [company_id]).fetchall()
    return [
        {
            "title": f"Duplicate Sale: Customer {r[0]} on {r[1]}",
            "description": f"{r[3]} invoices to the same customer on the same day for the same amount ₹{float(r[2]):,.0f}.",
            "severity": "critical",
            "financial_impact": float(r[2]) * (r[3] - 1),
            "evidence": {"customer_id": str(r[0]), "date": str(r[1]), "amount": float(r[2]), "count": r[3]},
        }
        for r in rows
    ]
