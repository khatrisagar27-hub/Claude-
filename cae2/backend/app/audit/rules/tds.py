"""TDS on payments to resident vendors, computed from the purchase register.

Base is the taxable value (GST shown separately is excluded — CBDT Circular 23/2017).
Not determinable from the register and therefore for the reviewer: lower-deduction
certificates (s.197), transporter declarations (s.194C(6)), and whether an
individual/HUF payer is liable to deduct at all.
"""
import pandas as pd

from app.audit.dataset import fy_start_year, party_lookup
from app.audit.helpers import rows
from app.audit.registry import Hit, rule
from app.money import inr
from app.statute import (TDS_NATURES, TDS_RATE_NO_PAN, TDS_RATE_NO_PAN_194Q, gstin_pan, law_ref, pan_is_individual_or_huf,
                         pan_valid, tds_version)

TOL = {"tolerance": (10.0, "Shortfall ignored up to (₹)")}
COLS = ["vendor", "pan", "section", "fy", "base", "rate_applied", "expected", "deducted", "shortfall"]


def tds_position(data, ctx) -> pd.DataFrame:
    """Expected against actual TDS per vendor, nature and financial year."""
    pu = data.purchases[data.purchases["nature"].isin(TDS_NATURES)].copy()
    if not ctx.flag("tds_194q_applicable"):
        pu = pu[pu["nature"] != "goods"]
    if pu.empty:
        return pd.DataFrame(columns=COLS + ["vendor_key", "nature", "pan_ok"])
    master_pan = party_lookup(data.parties, "pan")
    pu["pan"] = pu["vendor_key"].map(master_pan).combine_first(pu["vendor_name"].str.upper().map(master_pan)).fillna("")
    pu["pan"] = pu["pan"].where(pu["pan"] != "", pu["vendor_gstin"].map(gstin_pan))  # a GSTIN embeds the PAN
    pu["fy"] = fy_start_year(pu["invoice_date"])
    pu = pu.sort_values("invoice_date", kind="stable")
    out = []
    for (key, nature, fy), g in pu.groupby(["vendor_key", "nature", "fy"]):
        pan, pan_ok = g["pan"].iloc[0], pan_valid(g["pan"].iloc[0])
        versions = [tds_version(nature, day.date()) for day in g["invoice_date"]]
        if any(v is None for v in versions):
            continue
        last = versions[-1]

        def rate(v):
            if not pan_ok:
                return max(v["rate"], TDS_RATE_NO_PAN_194Q if v["section"] == "s.194Q" else TDS_RATE_NO_PAN)
            return v.get("rate_ind", v["rate"]) if pan_is_individual_or_huf(pan) else v["rate"]

        rates = pd.Series([rate(v) for v in versions], index=g.index)
        base, total = g["taxable_value"], g["taxable_value"].sum()
        if last["basis"] == "aggregate":
            liable = base if total > last["limit"] else base * 0
        elif last["basis"] == "single_or_aggregate":
            liable = base if total > last["limit"] else base.where(base > last["single"], 0)
        elif last["basis"] == "monthly":
            monthly = base.groupby(g["invoice_date"].dt.to_period("M")).transform("sum")
            liable = base.where(monthly > last["limit"], 0)
        else:  # excess: only the purchases above the limit, taken in date order
            running = base.cumsum()
            liable = (running - last["limit"]).clip(lower=0).clip(upper=base)
        expected = round(float((liable * rates / 100).sum()), 2)
        if expected <= 0:
            continue
        deducted = round(float(g["tds_deducted"].sum()), 2)
        out.append(dict(vendor_key=key, nature=nature, vendor=g["vendor_name"].iloc[0], pan=pan, pan_ok=pan_ok,
                        section=last["section"], fy=f"{fy}-{str(fy + 1)[2:]}", base=round(float(liable.sum()), 2),
                        rate_applied=float(rates.iloc[-1]), expected=expected, deducted=deducted,
                        shortfall=round(expected - deducted, 2)))
    return pd.DataFrame(out, columns=COLS + ["vendor_key", "nature", "pan_ok"])


def _hit(r, pos, ctx, kind):
    line = pos[(pos["vendor_key"] == r.vendor_key) & (pos["nature"] == r.nature) & (pos["fy"] == r.fy)]
    return Hit(f"{kind}|{r.vendor_key}|{r.nature}|{r.fy}",
               f"{r.vendor}: TDS {'not deducted' if kind == 'nil' else 'short deducted'} {r.section[2:]} — {inr(r.shortfall)}",
               f"{r.nature.replace('_', ' ').title()} payments of {inr(r.base)} in FY {r.fy} attract TDS at {r.rate_applied:g}% "
               f"= {inr(r.expected)}; deducted {inr(r.deducted)}. Shortfall {inr(r.shortfall)}, plus interest u/s 201(1A). "
               f"30% of the expense ({inr(r.base * 0.30)}) is disallowable u/s 40(a)(ia) until the tax is paid. "
               f"[{law_ref(r.section, ctx.period_start.date())}]", r.shortfall, rows(line, COLS))


@rule("TDS-001", "TDS", "TDS not deducted", "high", ["purchases"],
      law="Income-tax Act, 1961 ss.194C/194J/194I/194H/194A/194Q, s.201, s.40(a)(ia)", params=TOL)
def not_deducted(data, p, ctx):
    """Payments crossing the section threshold on which no tax was deducted."""
    pos = tds_position(data, ctx)
    return [_hit(r, pos, ctx, "nil") for r in pos[(pos["deducted"] == 0) & (pos["shortfall"] > p["tolerance"])].itertuples()]


@rule("TDS-002", "TDS", "TDS short deducted", "high", ["purchases"],
      law="Income-tax Act, 1961 ss.194C/194J/194I/194H/194A/194Q, s.201, s.40(a)(ia)", params=TOL)
def short_deducted(data, p, ctx):
    """Tax deducted is less than the amount due at the applicable rate."""
    pos = tds_position(data, ctx)
    return [_hit(r, pos, ctx, "short") for r in pos[(pos["deducted"] > 0) & (pos["shortfall"] > p["tolerance"])].itertuples()]


@rule("TDS-003", "TDS", "Deductee PAN missing or invalid", "medium", ["purchases"],
      law=f"Income-tax Act, 1961 s.206AA: deduct at {TDS_RATE_NO_PAN:g}% where PAN is not furnished")
def pan_missing(data, p, ctx):
    """Vendors liable to TDS with no valid PAN on record; the higher rate has been used in TDS-001/002."""
    pos = tds_position(data, ctx)
    pos = pos[~pos["pan_ok"].astype(bool)]
    return [Hit(f"pan|{key}", f"{g['vendor'].iloc[0]}: no valid PAN — TDS at higher rate",
                f"PAN on record: '{g['pan'].iloc[0] or 'blank'}'. Obtain the PAN or deduct at the s.206AA rate.",
                0, rows(g, COLS)) for key, g in pos.groupby("vendor_key")]
