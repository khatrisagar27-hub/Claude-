"""Purchase register rules."""
import pandas as pd

from app.audit.dataset import party_lookup
from app.audit.helpers import d, rows
from app.audit.registry import Hit, rule
from app.money import inr
from app.statute import MSME_CATEGORIES_43BH, MSME_DAYS_NO_AGREEMENT, MSME_DAYS_WITH_AGREEMENT

COLS = ["invoice_no", "invoice_date", "vendor_name", "taxable_value", "gst", "total", "source_row"]


def by_doc(frame, r):
    return frame[(frame["vendor_key"] == r.vendor_key) & (frame["doc"] == r.doc)]


@rule("PUR-001", "Purchases", "Vendor invoice booked more than once", "critical", ["purchases"])
def duplicate_invoice(data, p, ctx):
    """The same vendor invoice number is booked two or more times."""
    pu = data.purchases
    hits = []
    for (key, doc), g in pu[pu.duplicated(["vendor_key", "doc"], keep=False)].groupby(["vendor_key", "doc"]):
        extra = g["total"].sum() - g["total"].iloc[0]
        hits.append(Hit(f"{key}|{doc}", f"{g['vendor_name'].iloc[0]}: invoice {g['invoice_no'].iloc[0]} booked {len(g)} times",
                        f"Invoice {g['invoice_no'].iloc[0]} from {g['vendor_name'].iloc[0]} is booked {len(g)} times. "
                        f"Excess booked: {inr(extra)}; GST credit on the repeats: {inr(g['itc_claimed'].sum() - g['itc_claimed'].iloc[0])}.",
                        extra, rows(g, COLS + ["paid_date", "amount_paid"])))
    return hits


@rule("PUR-002", "Purchases", "Probable duplicate: same vendor and amount, different number", "high", ["purchases"],
      params={"window_days": (15, "Days between the invoices"), "min_amount": (10000, "Minimum invoice total (₹)")}, fraud=True)
def probable_duplicate(data, p, ctx):
    """Invoices from one vendor for an identical total within a short window under different numbers."""
    pu = data.purchases[data.purchases["total"] >= p["min_amount"]]
    hits = []
    for (key, total), g in pu[pu.duplicated(["vendor_key", "total"], keep=False)].groupby(["vendor_key", "total"]):
        g = g.sort_values("invoice_date")
        close = g["invoice_date"].diff().dt.days <= p["window_days"]
        if g["doc"].nunique() > 1 and close.any():
            hits.append(Hit(f"{key}|{total:.2f}", f"{g['vendor_name'].iloc[0]}: {len(g)} invoices of {inr(total)}",
                            f"Invoices {', '.join(g['invoice_no'])} are each for {inr(total)} within {p['window_days']} days. "
                            f"Confirm these are separate supplies.", total * (len(g) - 1), rows(g, COLS + ["paid_date"])))
    return hits


@rule("PUR-003", "Purchases", "Invoice without purchase order", "medium", ["purchases.po_no"],
      params={"min_amount": (100000, "Minimum invoice total (₹)")})
def no_po(data, p, ctx):
    """Invoices at or above the limit with no purchase order reference."""
    pu = data.purchases
    pu = pu[(pu["po_no"] == "") & (pu["total"] >= p["min_amount"])]
    return [Hit(f"nopo|{r.vendor_key}|{r.doc}", f"{r.vendor_name}: invoice {r.invoice_no} {inr(r.total)} without PO",
                f"Invoice {r.invoice_no} dated {d(r.invoice_date)} for {inr(r.total)} has no purchase order. "
                f"Check who authorised the purchase.", r.total, rows(by_doc(pu, r), COLS)) for r in pu.itertuples()]


@rule("PUR-004", "Purchases", "Invoiced value exceeds purchase order", "high", ["purchases.po_amount"],
      params={"tolerance_pct": (5, "Tolerance over PO value (%)")})
def over_po(data, p, ctx):
    """Total invoiced against a PO is more than the PO value plus tolerance."""
    pu = data.purchases[(data.purchases["po_no"] != "") & data.purchases["po_amount"].notna()]
    hits = []
    for (key, po), g in pu.groupby(["vendor_key", "po_no"]):
        po_value, billed = g["po_amount"].max(), g["total"].sum()
        if po_value > 0 and billed > po_value * (1 + p["tolerance_pct"] / 100):
            hits.append(Hit(f"{key}|{po}", f"PO {po}: billed {inr(billed)} against PO value {inr(po_value)}",
                            f"{g['vendor_name'].iloc[0]} has billed {inr(billed)} on PO {po} valued {inr(po_value)} "
                            f"({(billed / po_value - 1) * 100:.1f}% over).", billed - po_value, rows(g, COLS + ["po_no", "po_amount"])))
    return hits


@rule("PUR-005", "Purchases", "Paid before goods were received", "high", ["purchases.grn_date"])
def paid_before_grn(data, p, ctx):
    """Goods invoices paid with no goods receipt recorded, or paid before the receipt date."""
    pu = data.purchases
    pu = pu[(pu["nature"] == "goods") & pu["paid_date"].notna() & (pu["grn_date"].isna() | (pu["paid_date"] < pu["grn_date"]))]
    return [Hit(f"grn|{r.vendor_key}|{r.doc}", f"{r.vendor_name}: invoice {r.invoice_no} paid "
                + ("without goods receipt" if pd.isna(r.grn_date) else "before goods receipt"),
                f"Paid {inr(r.amount_paid)} on {d(r.paid_date)}; goods receipt "
                + ("not recorded." if pd.isna(r.grn_date) else f"dated {d(r.grn_date)}."),
                r.amount_paid, rows(by_doc(pu, r), COLS + ["grn_date", "paid_date", "amount_paid"])) for r in pu.itertuples()]


@rule("PUR-006", "Purchases", "Delayed payment to micro or small enterprise", "high", ["purchases", "parties.msme_category"],
      law="MSMED Act, 2006 s.15 and s.16 (interest at 3x bank rate, monthly rests); Income-tax Act, 1961 s.43B(h)")
def msme_delay(data, p, ctx):
    """Micro and small suppliers not paid within the statutory period, counted from acceptance
    (goods receipt date, else invoice date). The period is the agreed credit days capped at 45, or
    15 days where the engagement is marked as having no written agreement. Whether the supplier
    is a trader (outside s.43B(h) by common view) must be checked on review."""
    category = party_lookup(data.parties, "msme_category")
    credit = party_lookup(data.parties, "credit_days")
    pu = data.purchases.copy()
    pu["msme"] = pu["vendor_key"].map(category).combine_first(pu["vendor_name"].str.upper().map(category))
    pu = pu[pu["msme"].isin(MSME_CATEGORIES_43BH)].copy()
    if pu.empty:
        return []
    if ctx.flag("msme_written_agreement", True):
        agreed = pd.to_numeric(pu["vendor_key"].map(credit), errors="coerce").fillna(MSME_DAYS_WITH_AGREEMENT)
        pu["allowed_days"] = agreed.clip(upper=MSME_DAYS_WITH_AGREEMENT).astype(int)
    else:
        pu["allowed_days"] = MSME_DAYS_NO_AGREEMENT
    pu["accepted"] = pu["grn_date"].fillna(pu["invoice_date"])
    pu["due"] = pu["accepted"] + pd.to_timedelta(pu["allowed_days"], unit="D")
    pu["settled"] = pu["paid_date"].fillna(ctx.as_at)
    pu["delay_days"] = (pu["settled"] - pu["due"]).dt.days
    pu = pu[pu["delay_days"] > 0]
    monthly = 3 * float(ctx.flag("rbi_bank_rate_pct", 0) or 0) / 100 / 12
    hits = []
    for r in pu.itertuples():
        unpaid = pd.isna(r.paid_date)
        text = (f"Invoice {r.invoice_no} ({r.msme} enterprise) accepted {d(r.accepted)}, payable by {d(r.due)} "
                f"({r.allowed_days} days). " + (f"Unpaid as at {d(ctx.as_at)}" if unpaid else f"Paid {d(r.paid_date)}")
                + f" — {r.delay_days} days late.")
        evidence = rows(by_doc(pu, r), COLS + ["msme", "accepted", "due", "paid_date", "delay_days"])
        if monthly:
            months, days = divmod(r.delay_days, 30)
            interest = round(r.total * ((1 + monthly) ** months * (1 + monthly * days / 30) - 1), 2)
            text += f" Interest u/s 16 at 3 x {ctx.flag('rbi_bank_rate_pct')}% with monthly rests: {inr(interest)}."
            evidence[0]["interest_s16"] = interest
        else:
            text += " Set the RBI bank rate on the engagement to compute s.16 interest."
        if r.due <= ctx.period_end and (unpaid or r.paid_date > ctx.period_end):
            text += f" Outstanding beyond the due date at year end: {inr(r.total)} is deductible only on payment (s.43B(h))."
        hits.append(Hit(f"msme|{r.vendor_key}|{r.doc}", f"{r.vendor_name}: invoice {r.invoice_no} paid {r.delay_days} days beyond MSME limit"
                        if not unpaid else f"{r.vendor_name}: invoice {r.invoice_no} unpaid {r.delay_days} days beyond MSME limit",
                        text, r.total, evidence))
    return hits


@rule("PUR-007", "Purchases", "Vendor shares bank account or PAN with an employee", "critical", ["parties", "employees"], fraud=True)
def vendor_employee_match(data, p, ctx):
    """A vendor's bank account or PAN is the same as an employee's — conflict of interest or a fictitious vendor."""
    vendors = data.parties[data.parties["kind"].isin(["vendor", "both"])]
    hits = []
    for column, label in (("bank_account", "bank account"), ("pan", "PAN")):
        v = vendors[vendors[column] != ""]
        e = data.employees[data.employees[column] != ""]
        for m in v.merge(e, on=column, suffixes=("_vendor", "_emp")).itertuples():
            bought = data.purchases[data.purchases["vendor_key"].isin([m.code.upper(), m.gstin, m.name_vendor.upper()])]
            hits.append(Hit(f"{column}|{m.code}|{m.emp_code}", f"Vendor {m.name_vendor} and employee {m.name_emp} share a {label}",
                            f"Vendor {m.code} ({m.name_vendor}) and employee {m.emp_code} ({m.name_emp}) have the same {label} "
                            f"{getattr(m, column)}. Purchases from this vendor in the period: {inr(bought['total'].sum())}.",
                            bought["total"].sum(), rows(bought, COLS)))
    return hits


@rule("PUR-008", "Purchases", "Purchases split below approval limit", "high", ["purchases"],
      params={"approval_limit": (100000, "Approval limit (₹)"), "window_days": (3, "Window (days)")}, fraud=True)
def split_purchases(data, p, ctx):
    """Several invoices from one vendor, each under the approval limit, that together exceed it within a few days."""
    pu = data.purchases[data.purchases["total"] < p["approval_limit"]].sort_values("invoice_date")
    hits = []
    for key, g in pu.groupby("vendor_key"):
        used = set()
        for i, start in zip(g.index, g["invoice_date"]):
            if i in used:
                continue
            cluster = g[(g["invoice_date"] >= start) & (g["invoice_date"] <= start + pd.Timedelta(days=p["window_days"]))
                        & ~g.index.isin(used)]
            if len(cluster) >= 2 and cluster["total"].sum() >= p["approval_limit"]:
                used.update(cluster.index)
                hits.append(Hit(f"split|{key}|{d(start)}", f"{cluster['vendor_name'].iloc[0]}: {len(cluster)} invoices totalling "
                                f"{inr(cluster['total'].sum())} within {p['window_days']} days",
                                f"Each invoice is below the approval limit of {inr(p['approval_limit'])}; together they exceed it.",
                                cluster["total"].sum(), rows(cluster, COLS)))
    return hits


@rule("PUR-009", "Purchases", "Purchases from related parties", "low", ["purchases", "parties"],
      law="Companies Act, 2013 s.188; Income-tax Act, 1961 s.40A(2)(b)")
def related_party_purchases(data, p, ctx):
    """Total purchases from each party marked as related in the party master."""
    related = party_lookup(data.parties[data.parties["is_related_party"]], "name")
    pu = data.purchases
    pu = pu[pu["vendor_key"].isin(related) | pu["vendor_name"].str.upper().isin(related)]
    return [Hit(f"rp|{key}", f"Related party purchases: {g['vendor_name'].iloc[0]} {inr(g['total'].sum())}",
                f"{len(g)} invoice(s) totalling {inr(g['total'].sum())}. Check approval, reasonableness of price and disclosure.",
                g["total"].sum(), rows(g, COLS)) for key, g in pu.groupby("vendor_key")]


@rule("PUR-010", "Purchases", "Paid before the invoice date without a PO", "medium", ["purchases"])
def advance_without_po(data, p, ctx):
    """Payment made before the vendor's invoice date where no purchase order is recorded."""
    pu = data.purchases
    pu = pu[pu["paid_date"].notna() & (pu["paid_date"] < pu["invoice_date"]) & (pu["po_no"] == "")]
    return [Hit(f"adv|{r.vendor_key}|{r.doc}", f"{r.vendor_name}: {inr(r.amount_paid)} paid before invoice {r.invoice_no}",
                f"Paid on {d(r.paid_date)}, invoice dated {d(r.invoice_date)}, no PO on record. Check the basis for the advance.",
                r.amount_paid, rows(by_doc(pu, r), COLS + ["paid_date", "amount_paid"])) for r in pu.itertuples()]


@rule("PUR-011", "Purchases", "Invoice arithmetic does not agree", "medium", ["purchases"],
      params={"tolerance": (1.0, "Rounding tolerance (₹)")})
def arithmetic(data, p, ctx):
    """Taxable value plus taxes does not equal the invoice total."""
    pu = data.purchases
    pu = pu.assign(difference=(pu["taxable_value"] + pu["gst"] - pu["total"]).abs().round(2))
    bad = pu[pu["difference"] > p["tolerance"]]
    return [Hit(f"math|{r.vendor_key}|{r.doc}", f"{r.vendor_name}: invoice {r.invoice_no} total differs from taxable value + tax",
                f"Taxable {inr(r.taxable_value)} + GST {inr(r.gst)} against total {inr(r.total)}.", r.difference,
                rows(by_doc(bad, r), COLS + ["difference"])) for r in bad.itertuples()]
