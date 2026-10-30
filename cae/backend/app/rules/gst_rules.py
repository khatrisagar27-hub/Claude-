"""GST compliance rules GST-001 to GST-003."""
from datetime import timedelta

from app.rules import register, param, as_date, as_on_date
from app.statutory import gst


@register("GST-001")
def gst_001(conn, company_id, rule):
    """Removed GST slab (12% / 28%) on an invoice dated on or after 22-09-2025."""
    tol = float(param(rule, "rate_tolerance", 0.05))
    out = []
    for table, party in (("sales_invoices", "customer_id"), ("purchase_invoices", "vendor_id")):
        rows = conn.execute(f"""
            SELECT id, invoice_number, invoice_date, taxable_amount,
                   (cgst_amount + sgst_amount + igst_amount) / NULLIF(taxable_amount, 0) * 100 AS rate, {party}
            FROM {table}
            WHERE company_id = ? AND status != 'cancelled'
              AND invoice_date >= ? AND taxable_amount > 0
        """, [company_id, gst.GST_2_EFFECTIVE]).fetchall()
        for r in rows:
            rate = float(r[4] or 0)
            legacy = next((s for s in gst.LEGACY_SLABS if abs(rate - s) <= tol), None)
            if legacy is None:
                continue
            side = "Sales" if table == "sales_invoices" else "Purchase"
            out.append({
                "title": f"Old GST Rate {legacy:g}%: {side} {r[1]}",
                "description": f"{side} invoice {r[1]} dated {r[2]} carries GST at {rate:.2f}% of taxable value. The {legacy:g}% slab "
                               f"was removed from {gst.GST_2_EFFECTIVE} (Notf 9/2025-CT(Rate)). Check the HSN rate — only "
                               "tobacco/pan masala stayed on the old rates, and a multi-rate invoice can blend to this figure.",
                "severity": "high" if side == "Sales" else "medium",
                "financial_impact": float(r[3]) * abs(legacy - 18) / 100 if legacy == 12 else float(r[3]) * 0.10,
                "evidence": {"side": side.lower(), "invoice_number": r[1], "invoice_date": str(r[2]),
                             "taxable": float(r[3]), "effective_rate": round(rate, 2), "party_id": str(r[5]),
                             "statutory_ref": "Notf 9/2025-Central Tax (Rate), w.e.f. 22-09-2025"},
            })
    return out[: int(param(rule, "limit", 50))]


@register("GST-002")
def gst_002(conn, company_id, rule):
    """ITC on a supplier bill unpaid for more than 180 days (Rule 37 reversal)."""
    as_on = as_on_date(conn, rule, "purchase_invoices", "invoice_date")
    cutoff = as_on - timedelta(days=gst.RULE_37_DAYS)
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, invoice_date, total_amount, outstanding_amount,
               cgst_amount + sgst_amount + igst_amount AS tax
        FROM purchase_invoices
        WHERE company_id = ? AND itc_eligible = true AND reverse_charge = false
          AND status NOT IN ('cancelled', 'paid')
          AND outstanding_amount > 0 AND invoice_date < ?
          AND (cgst_amount + sgst_amount + igst_amount) > 0
        ORDER BY outstanding_amount DESC
    """, [company_id, cutoff]).fetchall()
    out = []
    for r in rows:
        total, outstanding, tax = float(r[4]), float(r[5]), float(r[6])
        reversal = tax * min(outstanding / total, 1.0) if total else tax
        days = (as_on - as_date(r[3])).days
        out.append({
            "title": f"Rule 37 ITC Reversal: {r[2]}",
            "description": f"Invoice {r[2]} dated {r[3]} is unpaid (₹{outstanding:,.0f} of ₹{total:,.0f}) after {days} days. "
                           f"ITC of ₹{reversal:,.0f} proportionate to the unpaid value must be reversed with s.50 interest "
                           "in the next GSTR-3B, and can be re-availed on payment.",
            "severity": "high",
            "financial_impact": round(reversal, 2),
            "evidence": {"vendor_id": str(r[1]), "invoice_number": r[2], "invoice_date": str(r[3]), "days_unpaid": days,
                         "outstanding": outstanding, "itc_to_reverse": round(reversal, 2), "as_on": str(as_on),
                         "statutory_ref": "s.16(2) second proviso CGST Act; Rule 37 CGST Rules"},
        })
    return out[: int(param(rule, "limit", 50))]


@register("GST-003")
def gst_003(conn, company_id, rule):
    """ITC-eligible bill booked after the s.16(4) time limit (30 November after the year end)."""
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, invoice_date, created_at,
               cgst_amount + sgst_amount + igst_amount AS tax
        FROM purchase_invoices
        WHERE company_id = ? AND itc_eligible = true AND status != 'cancelled'
          AND created_at IS NOT NULL AND (cgst_amount + sgst_amount + igst_amount) > 0
    """, [company_id]).fetchall()
    out = []
    for r in rows:
        inv_date, booked = as_date(r[3]), as_date(r[4])
        limit = gst.itc_time_limit(inv_date)
        if booked <= limit:
            continue
        out.append({
            "title": f"ITC Time-Barred: {r[2]}",
            "description": f"Invoice {r[2]} dated {inv_date} was booked on {booked}, after the s.16(4) limit of {limit}. "
                           f"ITC of ₹{float(r[5]):,.0f} cannot be taken if it was claimed after that date — check the GSTR-3B period.",
            "severity": "high",
            "financial_impact": float(r[5]),
            "evidence": {"vendor_id": str(r[1]), "invoice_number": r[2], "invoice_date": str(inv_date),
                         "booked_on": str(booked), "time_limit": str(limit), "tax": float(r[5]),
                         "statutory_ref": "s.16(4) CGST Act"},
        })
    return out[: int(param(rule, "limit", 50))]
