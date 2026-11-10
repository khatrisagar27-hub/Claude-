"""Sales register rules."""
import re

import pandas as pd

from app.audit.dataset import fy_start_year, party_lookup
from app.audit.helpers import d, month, rows
from app.audit.registry import Hit, rule
from app.money import inr
from app.statute import EWAY_BILL_LIMIT

COLS = ["invoice_no", "invoice_date", "customer_name", "taxable_value", "gst", "total", "source_row"]


def live(data):
    return data.sales[~data.sales["is_cancelled"]]


@rule("SAL-001", "Sales", "Duplicate invoice number", "high", ["sales"],
      law="CGST Rules, r.46(b): invoice number must be unique for a financial year")
def duplicate_number(data, p, ctx):
    """Two or more live invoices carry the same number in one financial year."""
    s = live(data).assign(fy=lambda x: fy_start_year(x["invoice_date"]))
    hits = []
    for (fy, doc), g in s[s.duplicated(["fy", "doc"], keep=False)].groupby(["fy", "doc"]):
        extra = g["total"].sum() - g["total"].iloc[0]
        hits.append(Hit(f"{fy}|{doc}", f"Invoice no. {g['invoice_no'].iloc[0]} used {len(g)} times",
                        f"Invoice number {g['invoice_no'].iloc[0]} appears on {len(g)} invoices in FY {fy}-{str(fy + 1)[2:]}. "
                        f"Value of the repeated invoices: {inr(extra)}. Check for double billing or revenue recorded twice.",
                        extra, rows(g, COLS)))
    return hits


@rule("SAL-002", "Sales", "Gaps in invoice number series", "medium", ["sales"],
      law="CGST Rules, r.46(b): consecutive serial number",
      params={"min_series": (5, "Smallest series to test (invoices)")})
def series_gaps(data, p, ctx):
    """Numbers missing inside a running invoice series. Cancelled invoices count as accounted for."""
    s = data.sales.copy()
    parts = s["invoice_no"].str.extract(r"^(?P<prefix>.*?)(?P<num>\d+)$")
    s = s.assign(prefix=parts["prefix"], num=pd.to_numeric(parts["num"])).dropna(subset=["num"])
    hits = []
    for prefix, g in s.groupby("prefix"):
        nums = sorted(set(g["num"].astype(int)))
        span = nums[-1] - nums[0] + 1
        if len(nums) < p["min_series"] or span > 5 * len(nums):
            continue  # not a running series
        missing = sorted(set(range(nums[0], nums[-1] + 1)) - set(nums))
        if missing:
            sample = ", ".join(f"{prefix}{n}" for n in missing[:15]) + (" …" if len(missing) > 15 else "")
            hits.append(Hit(f"series|{prefix}", f"{len(missing)} invoice number(s) missing in series '{prefix or 'numeric'}'",
                            f"Series runs {prefix}{nums[0]} to {prefix}{nums[-1]} with {len(missing)} number(s) not in the "
                            f"register: {sample}. Obtain the cancelled/unused copies or explanation.",
                            0, [{"missing_invoice_no": f"{prefix}{n}"} for n in missing[:200]]))
    return hits


@rule("SAL-003", "Sales", "Sales entered after period end but dated within it", "high", ["sales.entered_on"],
      law="AS 9 / Ind AS 115: revenue cut-off; SA 240 (presumed risk in revenue recognition)",
      params={"grace_days": (0, "Days after period end allowed for entry")}, fraud=True)
def backdated_after_period(data, p, ctx):
    """Invoices dated on or before the period end that were keyed in after it — a cut-off risk."""
    s = live(data)
    late = s[(s["invoice_date"] <= ctx.period_end) &
             (s["entered_on"] > ctx.period_end + pd.Timedelta(days=p["grace_days"]))]
    return [Hit(f"{r.doc}|{d(r.invoice_date)}", f"Invoice {r.invoice_no} dated {d(r.invoice_date)} entered on {d(r.entered_on)}",
                f"Invoice {r.invoice_no} to {r.customer_name} for {inr(r.total)} is dated {d(r.invoice_date)} but was entered "
                f"on {d(r.entered_on)}, after the period end {d(ctx.period_end)}. Verify dispatch/delivery evidence for cut-off.",
                r.taxable_value, rows(late[late["doc"] == r.doc], COLS + ["entered_on"]))
            for r in late.itertuples()]


@rule("SAL-004", "Sales", "E-invoice (IRN) not generated", "high", ["sales"],
      law="CGST Rules, r.48(4) and r.48(5): B2B invoice without IRN is not a valid tax invoice; penalty s.122")
def irn_missing(data, p, ctx):
    """B2B invoices without an IRN. Runs only where e-invoicing is marked applicable on the engagement."""
    if not ctx.flag("einvoice_applicable"):
        return []
    s = live(data)
    s = s[(s["customer_gstin"] != "") & (s["irn"] == "")]
    return [Hit(f"irn|{m}", f"{len(g)} B2B invoice(s) without IRN in {month(m)}",
                f"{len(g)} invoice(s) to registered customers in {month(m)} carry no IRN. Invoice value {inr(g['total'].sum())}, "
                f"GST {inr(g['gst'].sum())}. The recipient's input tax credit is also at risk.",
                g["gst"].sum(), rows(g, COLS + ["customer_gstin"]))
            for m, g in s.groupby(s["invoice_date"].dt.to_period("M").dt.start_time)]


@rule("SAL-005", "Sales", "E-way bill not recorded", "medium", ["sales"],
      law=f"CGST Rules, r.138(1): consignment value exceeding Rs {EWAY_BILL_LIMIT:,}; penalty s.129",
      params={"limit": (EWAY_BILL_LIMIT, "Consignment value limit (₹)")})
def eway_missing(data, p, ctx):
    """Goods invoices above the limit with no e-way bill number. Exempt goods and
    Rule 138(14) cases cannot be identified from the register — review the list."""
    s = live(data)
    s = s[(s["supply_type"] == "goods") & (s["total"] > p["limit"]) & (s["eway_bill_no"] == "")]
    return [Hit(f"ewb|{m}", f"{len(g)} goods invoice(s) above {inr(p['limit'])} without e-way bill in {month(m)}",
                f"{len(g)} goods invoice(s) in {month(m)} exceed {inr(p['limit'])} and have no e-way bill number recorded. "
                f"Total value {inr(g['total'].sum())}.", 0, rows(g, COLS))
            for m, g in s.groupby(s["invoice_date"].dt.to_period("M").dt.start_time)]


@rule("SAL-006", "Sales", "Wrong tax head for place of supply", "high", ["sales.place_of_supply"],
      law="IGST Act s.5 (inter-State) / CGST Act s.9 (intra-State); refund route s.77 CGST, s.19 IGST")
def wrong_tax_head(data, p, ctx):
    """IGST charged on an intra-State supply, or CGST/SGST on an inter-State one.
    Needs the client's GSTIN on record. SEZ supplies (IGST within the State) will appear here — exclude on review."""
    if not ctx.home_state:
        return []
    s = live(data)
    s = s[s["place_of_supply"] != ""]
    inter = s["place_of_supply"].str.zfill(2) != ctx.home_state
    wrong = s[(inter & (s["cgst"] + s["sgst"] > 0)) | (~inter & (s["igst"] > 0))]
    hits = []
    for r in wrong.itertuples():
        is_inter = str(r.place_of_supply).zfill(2) != ctx.home_state
        amount = r.cgst + r.sgst if is_inter else r.igst
        hits.append(Hit(f"{r.doc}|{d(r.invoice_date)}", f"Invoice {r.invoice_no}: {'CGST/SGST' if is_inter else 'IGST'} charged on "
                        f"{'inter' if is_inter else 'intra'}-State supply",
                        f"Place of supply is State {str(r.place_of_supply).zfill(2)}; the client is registered in State "
                        f"{ctx.home_state}. Tax of {inr(amount)} is under the wrong head and is payable again under the correct one.",
                        amount, rows(wrong[wrong["doc"] == r.doc], COLS + ["place_of_supply", "cgst", "sgst", "igst"])))
    return hits


@rule("SAL-007", "Sales", "Invoice arithmetic does not agree", "medium", ["sales"],
      params={"tolerance": (1.0, "Rounding tolerance (₹)")})
def arithmetic(data, p, ctx):
    """Taxable value plus taxes does not equal the invoice total, or CGST differs from SGST."""
    s = live(data)
    s = s.assign(difference=(s["taxable_value"] + s["gst"] - s["total"]).abs().round(2))
    bad = s[(s["difference"] > p["tolerance"]) | ((s["cgst"] - s["sgst"]).abs() > p["tolerance"])]
    return [Hit(f"{r.doc}|{d(r.invoice_date)}", f"Invoice {r.invoice_no}: total differs from taxable value + tax",
                f"Taxable {inr(r.taxable_value)} + CGST {inr(r.cgst)} + SGST {inr(r.sgst)} + IGST {inr(r.igst)} "
                f"against invoice total {inr(r.total)}.", r.difference,
                rows(bad[bad["doc"] == r.doc], COLS + ["cgst", "sgst", "igst", "difference"]))
            for r in bad.itertuples()]


@rule("SAL-008", "Sales", "Receivables overdue beyond limit", "medium", ["sales"],
      law="AS 4 / Ind AS 109: assess recoverability and provision",
      params={"overdue_days": (180, "Days past due date"), "default_credit_days": (30, "Credit days where no due date")})
def overdue_receivables(data, p, ctx):
    """Unpaid invoices more than the set number of days past due as at the data date."""
    s = live(data).copy()
    s["outstanding"] = (s["total"] - s["amount_received"]).round(2)
    credit = pd.to_numeric(s["customer_key"].map(party_lookup(data.parties, "credit_days")), errors="coerce").fillna(p["default_credit_days"])
    s["due"] = s["due_date"].fillna(s["invoice_date"] + pd.to_timedelta(credit, unit="D"))
    s["days_overdue"] = (ctx.as_at - s["due"]).dt.days
    s = s[(s["outstanding"] > 1) & (s["days_overdue"] > p["overdue_days"])]
    return [Hit(f"overdue|{key}", f"{g['customer_name'].iloc[0]}: {inr(g['outstanding'].sum())} overdue more than {p['overdue_days']} days",
                f"{len(g)} invoice(s) outstanding beyond {p['overdue_days']} days as at {d(ctx.as_at)}; oldest is "
                f"{int(g['days_overdue'].max())} days overdue. Consider balance confirmation and provision.",
                g["outstanding"].sum(), rows(g.sort_values("days_overdue", ascending=False),
                                             ["invoice_no", "invoice_date", "total", "outstanding", "days_overdue"]))
            for key, g in s.groupby("customer_key")]


@rule("SAL-009", "Sales", "Sales to related parties", "low", ["sales", "parties"],
      law="Companies Act, 2013 s.188; AS 18 / Ind AS 24 disclosure")
def related_party_sales(data, p, ctx):
    """Total sales to each party marked as related in the party master."""
    related = party_lookup(data.parties[data.parties["is_related_party"]], "name")
    s = live(data)
    s = s[s["customer_key"].isin(related) | s["customer_name"].str.upper().isin(related)]
    return [Hit(f"rp|{key}", f"Related party sales: {g['customer_name'].iloc[0]} {inr(g['total'].sum())}",
                f"{len(g)} invoice(s) totalling {inr(g['total'].sum())}. Check approval, arm's length pricing and disclosure.",
                g["total"].sum(), rows(g, COLS)) for key, g in s.groupby("customer_key")]


@rule("SAL-010", "Sales", "Same customer, same day, same amount", "medium", ["sales"],
      params={"min_amount": (10000, "Minimum invoice total (₹)")})
def same_day_same_amount(data, p, ctx):
    """Possible double billing: identical totals to one customer on one date under different numbers."""
    s = live(data)
    s = s[s["total"] >= p["min_amount"]]
    dup = s[s.duplicated(["customer_key", "invoice_date", "total"], keep=False)]
    hits = []
    for (key, day, total), g in dup.groupby(["customer_key", "invoice_date", "total"]):
        if g["doc"].nunique() > 1:
            hits.append(Hit(f"{key}|{d(day)}|{total:.2f}", f"{len(g)} invoices of {inr(total)} to {g['customer_name'].iloc[0]} on {d(day)}",
                            f"Invoices {', '.join(g['invoice_no'])} are for the same amount on the same day.",
                            total * (len(g) - 1), rows(g, COLS)))
    return hits


@rule("SAL-011", "Sales", "Sales bunched at month end", "medium", ["sales"], law="SA 240: revenue recognition",
      params={"last_days": (3, "Days at month end"), "share_pct": (40, "Share of month's sales (%)"),
              "min_invoices": (20, "Minimum invoices in the month")}, fraud=True)
def month_end_bunching(data, p, ctx):
    """Months in which the last few days carry an unusually large share of the month's sales."""
    s, hits = live(data), []
    for m, g in s.groupby(s["invoice_date"].dt.to_period("M")):
        tail = g[g["invoice_date"].dt.day > m.days_in_month - p["last_days"]]
        month_total = g["taxable_value"].sum()
        if len(g) >= p["min_invoices"] and month_total > 0 and tail["taxable_value"].sum() / month_total * 100 > p["share_pct"]:
            share = tail["taxable_value"].sum() / month_total * 100
            hits.append(Hit(f"bunch|{m}", f"{share:.0f}% of {m.strftime('%b-%Y')} sales booked in the last {p['last_days']} days",
                            f"{inr(tail['taxable_value'].sum())} of {inr(month_total)} was invoiced in the last {p['last_days']} days. "
                            f"Test dispatch documents and post-period credit notes.", tail["taxable_value"].sum(), rows(tail, COLS)))
    return hits


@rule("SAL-012", "Sales", "High invoice cancellations", "medium", ["sales"],
      params={"ratio_pct": (5, "Cancelled share of invoices (%)"), "min_cancelled": (3, "Minimum cancelled invoices")}, fraud=True)
def cancellations(data, p, ctx):
    """Months where cancelled invoices exceed the set share of all invoices raised."""
    s, hits = data.sales, []
    for m, g in s.groupby(s["invoice_date"].dt.to_period("M")):
        c = g[g["is_cancelled"]]
        if len(c) >= p["min_cancelled"] and len(c) / len(g) * 100 > p["ratio_pct"]:
            hits.append(Hit(f"cancel|{m}", f"{len(c)} of {len(g)} invoices cancelled in {m.strftime('%b-%Y')}",
                            f"{len(c) / len(g) * 100:.1f}% of invoices were cancelled, value {inr(c['total'].sum())}. "
                            f"Check authorisation and whether goods had already moved.", c["total"].sum(), rows(c, COLS)))
    return hits
