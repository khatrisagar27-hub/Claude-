"""TDS rules TDS-001 to TDS-002 (s.393 of the 2025 Act / Chapter XVII-B of the 1961 Act)."""
from collections import defaultdict

from app.rules import register, param, fy_sql, as_date, capped
from app.statutory import income_tax


@register("TDS-001")
def tds_001(conn, company_id, rule):
    """TDS on purchase of goods not deducted after a vendor crosses Rs.50 lakh in the year
    (s.393(1) Table Sl.8(ii) / s.194Q). Applies only if the buyer's turnover in the
    preceding year exceeded Rs.10 crore."""
    buyer_limit = float(param(rule, "buyer_turnover_limit", 100_000_000))
    threshold = float(param(rule, "threshold", income_tax.TDS_GOODS_THRESHOLD))
    turnover = dict(conn.execute(f"""
        SELECT {fy_sql('invoice_date')}, SUM(taxable_amount) FROM sales_invoices_all
        WHERE company_id = ? AND status != 'cancelled' GROUP BY 1
    """, [company_id]).fetchall())
    override = param(rule, "buyer_turnover_override", None)
    rows = conn.execute(f"""
        SELECT vendor_id, {fy_sql('invoice_date')} AS fy, invoice_number, invoice_date, taxable_amount,
               tds_amount, tds_section, id IN (SELECT id FROM purchase_invoices) AS in_period
        FROM purchase_invoices_all
        WHERE company_id = ? AND status != 'cancelled' AND taxable_amount > 0
        ORDER BY vendor_id, invoice_date, invoice_number
    """, [company_id]).fetchall()

    running = defaultdict(float)
    misses: dict[tuple, dict] = {}
    for vendor, fy, inv_no, inv_date, taxable, tds, section, in_period in rows:
        fy = int(fy)
        prior_turnover = float(override) if override is not None else float(turnover.get(fy - 1) or 0)
        if prior_turnover <= buyer_limit:
            continue
        before = running[(vendor, fy)]
        running[(vendor, fy)] += float(taxable)
        excess = running[(vendor, fy)] - max(before, threshold)
        if excess <= 0 or float(tds or 0) > 0 or not in_period:   # FY-to-date threshold, in-period misses
            continue
        m = misses.setdefault((vendor, fy), {"invoices": [], "excess": 0.0, "first_date": as_date(inv_date)})
        m["invoices"].append(inv_no)
        m["excess"] += excess

    out = []
    for (vendor, fy), m in misses.items():
        ref = income_tax.section_ref("tds_goods", m["first_date"])
        due = m["excess"] * income_tax.TDS_MIN_RATE["tds_goods"]
        out.append({
            "title": f"TDS on Goods Not Deducted: Vendor {vendor} (FY {fy}-{str(fy + 1)[-2:]})",
            "description": f"Purchases from vendor {vendor} crossed ₹{threshold:,.0f} in FY {fy}-{str(fy + 1)[-2:]}, but "
                           f"{len(m['invoices'])} later invoice(s) worth ₹{m['excess']:,.0f} above the threshold show no TDS. "
                           f"TDS of ₹{due:,.0f} (0.1%) on the excess is due under {ref}.",
            "severity": "high",
            "financial_impact": round(due, 2),
            "evidence": {"vendor_id": str(vendor), "financial_year": fy, "invoices": m["invoices"][:20],
                         "excess_over_threshold": round(m["excess"], 2), "tds_due": round(due, 2), "statutory_ref": ref},
        })
    return out


@register("TDS-002")
def tds_002(conn, company_id, rule):
    """TDS deducted below the minimum rate for the section recorded on the bill."""
    tolerance = float(param(rule, "tolerance", 1.0))
    rows = conn.execute("""
        SELECT id, vendor_id, invoice_number, invoice_date, taxable_amount, tds_amount,
               UPPER(REPLACE(TRIM(tds_section), ' ', '')) AS section
        FROM purchase_invoices
        WHERE company_id = ? AND status != 'cancelled'
          AND tds_section IS NOT NULL AND TRIM(tds_section) != '' AND taxable_amount > 0
    """, [company_id]).fetchall()
    out = []
    for r in rows:
        key = income_tax.TDS_SECTION_KEYS.get(str(r[6]).replace("S.", ""))
        if not key or key == "tds_goods":
            continue
        expected = float(r[4]) * income_tax.TDS_MIN_RATE[key]
        actual = float(r[5] or 0)
        if actual + tolerance >= expected:
            continue
        on = as_date(r[3])
        ref = income_tax.section_ref(key, on)
        out.append({
            "title": f"TDS Short-Deducted: {r[2]} ({r[6]})",
            "description": f"Invoice {r[2]} dated {on} (taxable ₹{float(r[4]):,.0f}) shows TDS of ₹{actual:,.0f} under {r[6]}; "
                           f"the minimum rate under {ref} gives ₹{expected:,.0f}. Short deduction ₹{expected - actual:,.0f}.",
            "severity": "medium",
            "financial_impact": round(expected - actual, 2),
            "evidence": {"vendor_id": str(r[1]), "invoice_number": r[2], "invoice_date": str(on),
                         "taxable": float(r[4]), "tds_actual": actual, "tds_minimum": round(expected, 2),
                         "section_recorded": r[6], "statutory_ref": ref},
        })
    out.sort(key=lambda e: -e["financial_impact"])
    return capped(out, rule)
