"""GST rules: input tax credit eligibility and GSTR-2B reconciliation."""
import pandas as pd

from app.analytics.gst_reco import reconcile
from app.audit.dataset import fy_start_year
from app.audit.helpers import d, rows
from app.audit.registry import Hit, rule
from app.money import inr
from app.statute import BLOCKED_CREDIT_NATURES, ITC_PAYMENT_DAYS, gstin_valid

RECO = ["gstin", "party", "books_invoice_no", "portal_invoice_no", "invoice_date", "books_tax", "itc_claimed", "portal_tax", "at_risk"]
COLS = ["invoice_no", "invoice_date", "vendor_name", "vendor_gstin", "taxable_value", "gst", "itc_claimed", "source_row"]
TOL = {"tolerance": (1.0, "Matching tolerance (₹)")}


@rule("GST-001", "GST", "ITC claimed on invoices not in GSTR-2B", "high", ["purchases", "gstr2b"],
      law="CGST Act s.16(2)(aa); CGST Rules r.36(4)", params=TOL)
def itc_not_in_2b(data, p, ctx):
    """Credit taken on invoices the supplier has not reported. Grouped by supplier."""
    r = reconcile(data.purchases, data.gstr2b, p["tolerance"])
    r = r[(r["status"] == "not_in_2b") & (r["itc_claimed"] > 0)]
    return [Hit(f"n2b|{gstin}", f"{g['party'].iloc[0]}: ITC {inr(g['itc_claimed'].sum())} not reflected in GSTR-2B",
                f"{len(g)} invoice(s) from GSTIN {gstin} with ITC of {inr(g['itc_claimed'].sum())} do not appear in GSTR-2B. "
                f"Credit is not available until the supplier reports them; follow up or reverse.",
                g["itc_claimed"].sum(), rows(g, RECO)) for gstin, g in r.groupby("gstin")]


@rule("GST-002", "GST", "ITC claimed exceeds tax in GSTR-2B", "high", ["purchases", "gstr2b"],
      law="CGST Act s.16(2)(aa); CGST Rules r.36(4)", params=TOL)
def itc_excess(data, p, ctx):
    """Invoice is in GSTR-2B but for a lower tax amount than the credit taken."""
    r = reconcile(data.purchases, data.gstr2b, p["tolerance"])
    r = r[(r["status"] == "value_mismatch") & (r["at_risk"] > 0)]
    return [Hit(f"exc|{x.gstin}|{x.doc}", f"{x.party}: invoice {x.books_invoice_no} ITC exceeds GSTR-2B by {inr(x.at_risk)}",
                f"ITC claimed {inr(x.itc_claimed)}; GSTR-2B shows tax of {inr(x.portal_tax)}.", x.at_risk,
                rows(r[(r["gstin"] == x.gstin) & (r["doc"] == x.doc)], RECO)) for x in r.itertuples()]


@rule("GST-003", "GST", "Invoices in GSTR-2B not booked", "medium", ["purchases", "gstr2b"], params=TOL)
def in_2b_not_booked(data, p, ctx):
    """Supplier has reported invoices that are not in the purchase register: unrecorded
    purchases, credit not availed, or a supplier quoting the client's GSTIN in error."""
    r = reconcile(data.purchases, data.gstr2b, p["tolerance"])
    r = r[r["status"] == "not_in_books"]
    return [Hit(f"nib|{gstin}", f"{g['party'].iloc[0] or gstin}: {len(g)} invoice(s) in GSTR-2B not booked, tax {inr(g['portal_tax'].sum())}",
                f"GSTIN {gstin} reported {len(g)} invoice(s), taxable value {inr(g['portal_taxable'].sum())}, not found in the purchase register.",
                g["portal_tax"].sum(), rows(g, ["gstin", "party", "portal_invoice_no", "invoice_date", "portal_taxable", "portal_tax"]))
            for gstin, g in r.groupby("gstin")]


@rule("GST-004", "GST", f"Supplier not paid within {ITC_PAYMENT_DAYS} days — ITC reversal", "high", ["purchases"],
      law="CGST Act s.16(2) second proviso; CGST Rules r.37; interest s.50")
def rule_37(data, p, ctx):
    """ITC taken on invoices still unpaid, wholly or partly, beyond 180 days from the invoice date.
    Reversal is proportionate to the unpaid amount."""
    pu = data.purchases.copy()
    pu["unpaid"] = (pu["total"] - pu["amount_paid"]).round(2)
    pu["age_days"] = (ctx.as_at - pu["invoice_date"]).dt.days
    pu = pu[(pu["itc_claimed"] > 0) & (pu["unpaid"] > 1) & (pu["age_days"] > ITC_PAYMENT_DAYS) & (pu["total"] > 0)]
    pu["itc_to_reverse"] = (pu["itc_claimed"] * pu["unpaid"] / pu["total"]).round(2)
    return [Hit(f"r37|{r.vendor_key}|{r.doc}", f"{r.vendor_name}: invoice {r.invoice_no} unpaid {r.age_days} days — reverse ITC {inr(r.itc_to_reverse)}",
                f"Invoice dated {d(r.invoice_date)}, {inr(r.unpaid)} of {inr(r.total)} unpaid as at {d(ctx.as_at)}. "
                f"Proportionate ITC of {inr(r.itc_to_reverse)} is to be reversed with interest; it can be re-availed on payment.",
                r.itc_to_reverse, rows(pu[(pu["vendor_key"] == r.vendor_key) & (pu["doc"] == r.doc)],
                                       COLS + ["total", "amount_paid", "unpaid", "age_days", "itc_to_reverse"]))
            for r in pu.itertuples()]


@rule("GST-005", "GST", "ITC booked after the time limit", "critical", ["purchases"],
      law="CGST Act s.16(4): 30 November following the financial year of the invoice")
def time_barred(data, p, ctx):
    """Credit on an invoice booked after 30 November following the end of the financial year
    to which the invoice belongs. Uses booking date; where absent, the test cannot be made."""
    pu = data.purchases[data.purchases["booking_date"].notna() & (data.purchases["itc_claimed"] > 0)].copy()
    pu["last_date"] = pd.to_datetime((fy_start_year(pu["invoice_date"]) + 1).astype(str) + "-11-30")
    pu = pu[pu["booking_date"] > pu["last_date"]]
    return [Hit(f"164|{r.vendor_key}|{r.doc}", f"{r.vendor_name}: invoice {r.invoice_no} booked after s.16(4) time limit",
                f"Invoice dated {d(r.invoice_date)} was booked on {d(r.booking_date)}; the last date to take credit was "
                f"{d(r.last_date)}. ITC of {inr(r.itc_claimed)} is not admissible.", r.itc_claimed,
                rows(pu[(pu["vendor_key"] == r.vendor_key) & (pu["doc"] == r.doc)], COLS + ["booking_date", "last_date"]))
            for r in pu.itertuples()]


@rule("GST-006", "GST", "ITC claimed against a missing or invalid GSTIN", "high", ["purchases"],
      law="CGST Act s.16(2)(a); CGST Rules r.36(1), r.46")
def invalid_gstin(data, p, ctx):
    """Credit taken where the supplier GSTIN is blank or fails the check-digit test."""
    pu = data.purchases[data.purchases["itc_claimed"] > 0]
    pu = pu[~pu["vendor_gstin"].map(gstin_valid).astype(bool)]
    return [Hit(f"gstin|{key}", f"{g['vendor_name'].iloc[0]}: ITC {inr(g['itc_claimed'].sum())} with "
                + ("no GSTIN" if g["vendor_gstin"].iloc[0] == "" else f"invalid GSTIN {g['vendor_gstin'].iloc[0]}"),
                f"{len(g)} invoice(s). A tax invoice must carry the supplier's valid GSTIN for credit to be available.",
                g["itc_claimed"].sum(), rows(g, COLS)) for key, g in pu.groupby("vendor_key")]


@rule("GST-007", "GST", "ITC claimed where GSTR-2B shows credit not available", "high", ["purchases", "gstr2b"],
      law="CGST Act s.16(2)(aa), s.16(4), s.38", params=TOL)
def itc_marked_unavailable(data, p, ctx):
    """GSTR-2B flags the invoice as 'ITC not available' but credit has been taken."""
    r = reconcile(data.purchases, data.gstr2b, p["tolerance"])
    r = r[~r["itc_available"] & (r["itc_claimed"] > 0) & r["status"].isin(["matched", "value_mismatch", "probable_match"])]
    return [Hit(f"na|{x.gstin}|{x.doc}", f"{x.party}: invoice {x.books_invoice_no} — GSTR-2B shows ITC not available",
                f"ITC of {inr(x.itc_claimed)} claimed; GSTR-2B marks this invoice as not eligible.", x.itc_claimed,
                rows(r[(r["gstin"] == x.gstin) & (r["doc"] == x.doc)], RECO)) for x in r.itertuples()]


@rule("GST-008", "GST", "ITC claimed on blocked credits", "high", ["purchases"], law="CGST Act s.17(5)")
def blocked_credit(data, p, ctx):
    """Credit taken on purchases whose nature falls under s.17(5): motor vehicles, food and
    beverages, club membership, health insurance, works contract for immovable property, gifts, personal use.
    Exceptions within s.17(5) (e.g. vehicles for transport of goods) need review."""
    pu = data.purchases[data.purchases["nature"].isin(BLOCKED_CREDIT_NATURES) & (data.purchases["itc_claimed"] > 0)]
    return [Hit(f"175|{r.vendor_key}|{r.doc}", f"{r.vendor_name}: ITC {inr(r.itc_claimed)} on {r.nature.replace('_', ' ')}",
                f"Invoice {r.invoice_no} dated {d(r.invoice_date)} is classed as {r.nature.replace('_', ' ')}, a blocked credit.",
                r.itc_claimed, rows(pu[(pu["vendor_key"] == r.vendor_key) & (pu["doc"] == r.doc)], COLS + ["nature"]))
            for r in pu.itertuples()]


@rule("GST-009", "GST", "ITC claimed exceeds tax charged on the invoice", "high", ["purchases"], params=TOL)
def itc_over_tax(data, p, ctx):
    """Credit recorded is more than the GST shown on the invoice."""
    pu = data.purchases
    pu = pu[pu["itc_claimed"] > pu["gst"] + p["tolerance"]]
    return [Hit(f"over|{r.vendor_key}|{r.doc}", f"{r.vendor_name}: invoice {r.invoice_no} ITC exceeds tax charged by {inr(r.itc_claimed - r.gst)}",
                f"GST on invoice {inr(r.gst)}; ITC claimed {inr(r.itc_claimed)}.", r.itc_claimed - r.gst,
                rows(pu[(pu["vendor_key"] == r.vendor_key) & (pu["doc"] == r.doc)], COLS)) for r in pu.itertuples()]
