"""Rules over the books of account (day book / ledger entries).

Journal-entry tests follow the selection criteria in SA 240 para 33(a) and A44:
entries without explanation, large or round amounts, entries near period end,
back-dated entries, and entries to unusual accounts.
"""
import numpy as np
import pandas as pd

from app.audit.helpers import d, month, rows
from app.audit.registry import Hit, rule
from app.money import inr

LINES = ["voucher_no", "voucher_date", "voucher_type", "ledger", "debit", "credit", "narration", "entered_by", "source_row"]
SA240 = "SA 240 para 33(a): testing of journal entries"


def vouchers(lg: pd.DataFrame) -> pd.DataFrame:
    """One row per voucher with its value (total debits)."""
    return lg.groupby("vkey", as_index=False).agg(
        voucher_no=("voucher_no", "first"), voucher_date=("voucher_date", "first"), voucher_type=("voucher_type", "first"),
        value=("debit", "sum"), credits=("credit", "sum"), narration=("narration", "max"), entered_by=("entered_by", "first"),
        entered_on=("entered_on", "max"), has_cash_bank=("is_cash", "max"), bank=("is_bank", "max"), income=("is_income", "max"))


def journals(data) -> pd.DataFrame:
    return vouchers(data.ledger[data.ledger["voucher_type"] == "journal"])


def lines_of(data, vkey):
    return rows(data.ledger[data.ledger["vkey"] == vkey], LINES)


def monthly(frame, key, title, detail, **kw):
    """One finding per month for population-type tests."""
    hits = []
    for m, g in frame.groupby(frame["voucher_date"].dt.to_period("M").dt.start_time):
        hits.append(Hit(f"{key}|{m:%Y-%m}", title.format(n=len(g), month=month(m)),
                        detail.format(n=len(g), month=month(m), value=inr(g["value"].sum())), 0,
                        rows(g.sort_values("value", ascending=False), ["voucher_no", "voucher_date", "value", "narration", "entered_by"]), **kw))
    return hits


@rule("JE-001", "Books", "Voucher does not balance", "critical", ["ledger"])
def unbalanced(data, p, ctx):
    """Total debits differ from total credits within a voucher — the extract is incomplete or the books are corrupt."""
    v = vouchers(data.ledger[data.ledger["voucher_type"] != "opening"])
    v = v[(v["value"] - v["credits"]).abs() > 0.01]
    return [Hit(f"unbal|{r.vkey}", f"{r.voucher_type.title()} {r.voucher_no} dated {d(r.voucher_date)} is out of balance by {inr(abs(r.value - r.credits))}",
                f"Debits {inr(r.value)}, credits {inr(r.credits)}.", abs(r.value - r.credits), lines_of(data, r.vkey))
            for r in v.itertuples()]


@rule("JE-002", "Books", "Journals without narration", "medium", ["ledger"], law=SA240,
      params={"min_amount": (50000, "Minimum voucher value (₹)")})
def no_narration(data, p, ctx):
    """Journal vouchers at or above the limit with no narration on any line."""
    j = journals(data)
    j = j[(j["narration"] == "") & (j["value"] >= p["min_amount"])]
    return monthly(j, "nonarr", "{n} journal(s) without narration in {month}",
                   "{n} journal voucher(s) totalling {value} carry no narration. Obtain the supporting papers and approval.")


@rule("JE-003", "Books", "Large journal entry", "medium", ["ledger"], law=SA240,
      params={"min_amount": (1000000, "Voucher value at or above (₹)")})
def large_journal(data, p, ctx):
    """Individual journal vouchers at or above the limit."""
    j = journals(data)
    return [Hit(f"large|{r.vkey}", f"Journal {r.voucher_no} dated {d(r.voucher_date)} for {inr(r.value)}",
                f"Narration: {r.narration or '(none)'}. Entered by {r.entered_by or 'not recorded'}. Verify support and approval.",
                r.value, lines_of(data, r.vkey)) for r in j[j["value"] >= p["min_amount"]].itertuples()]


@rule("JE-004", "Books", "Back-dated voucher", "medium", ["ledger.entered_on"], law=SA240,
      params={"lag_days": (30, "Days between voucher date and entry"), "min_amount": (100000, "Minimum voucher value (₹)")}, fraud=True)
def backdated(data, p, ctx):
    """Vouchers keyed in long after the date they bear."""
    v = vouchers(data.ledger[data.ledger["voucher_type"] != "opening"])
    v["lag"] = (v["entered_on"] - v["voucher_date"]).dt.days
    v = v[(v["lag"] > p["lag_days"]) & (v["value"] >= p["min_amount"])]
    return [Hit(f"backdate|{r.vkey}", f"{r.voucher_type.title()} {r.voucher_no} dated {d(r.voucher_date)} entered {int(r.lag)} days later",
                f"Value {inr(r.value)}, entered on {d(r.entered_on)} by {r.entered_by or 'not recorded'}.", r.value,
                lines_of(data, r.vkey)) for r in v.itertuples()]


@rule("JE-005", "Books", "Journal voucher touching cash or bank", "medium", ["ledger"], law=SA240,
      params={"min_amount": (10000, "Minimum voucher value (₹)")})
def journal_cash_bank(data, p, ctx):
    """Cash or bank moved through a journal instead of a payment, receipt or contra voucher,
    bypassing the usual cash/bank controls."""
    j = journals(data)
    j = j[(j["has_cash_bank"] | j["bank"]) & (j["value"] >= p["min_amount"])]
    return [Hit(f"jcash|{r.vkey}", f"Journal {r.voucher_no} dated {d(r.voucher_date)} posts to cash/bank — {inr(r.value)}",
                f"Narration: {r.narration or '(none)'}.", r.value, lines_of(data, r.vkey)) for r in j.itertuples()]


@rule("JE-006", "Books", "Journal to income accounts at period end", "high", ["ledger"],
      law="SA 240 para 27 (presumed fraud risk in revenue) and para 33(a)",
      params={"last_days": (5, "Days before period end"), "min_amount": (100000, "Minimum voucher value (₹)")}, fraud=True)
def topside_revenue(data, p, ctx):
    """Journals hitting sales/income ledgers in the last days of the period, or dated in the
    period but entered after it."""
    j = journals(data)
    window = (j["voucher_date"] > ctx.period_end - pd.Timedelta(days=p["last_days"])) & (j["voucher_date"] <= ctx.period_end)
    late = (j["voucher_date"] <= ctx.period_end) & (j["entered_on"] > ctx.period_end)
    j = j[j["income"] & (window | late) & (j["value"] >= p["min_amount"])]
    return [Hit(f"topside|{r.vkey}", f"Journal {r.voucher_no} dated {d(r.voucher_date)} adjusts income — {inr(r.value)}",
                f"Narration: {r.narration or '(none)'}. Entered by {r.entered_by or 'not recorded'}"
                + (f" on {d(r.entered_on)}" if not pd.isna(r.entered_on) else "") + ".", r.value, lines_of(data, r.vkey))
            for r in j.itertuples()]


@rule("JE-007", "Books", "Suspense account not cleared", "high", ["ledger"],
      law="Schedule III, Companies Act 2013: balances must be classified by nature")
def suspense(data, p, ctx):
    """Ledgers named or grouped as suspense that carry a balance as at the data date."""
    lg = data.ledger
    sus = lg[(lg["ledger"].str.contains("suspense", case=False) | lg["ledger_group"].str.contains("suspense", case=False))
             & (lg["voucher_date"] <= ctx.as_at)]
    hits = []
    for name, g in sus.groupby("ledger"):
        balance = round(g["debit"].sum() - g["credit"].sum(), 2)
        if abs(balance) > 0.01:
            hits.append(Hit(f"suspense|{name}", f"{name}: balance {inr(abs(balance))} {'Dr' if balance > 0 else 'Cr'}",
                            f"{len(g)} entries; balance uncleared as at {d(ctx.as_at)}. Identify and reclassify each item.",
                            abs(balance), rows(g, LINES)))
    return hits


@rule("JE-008", "Books", "Vouchers dated outside the engagement period", "medium", ["ledger"])
def outside_period(data, p, ctx):
    """Entries dated before the period start or after the period end (opening balances excluded)."""
    lg = data.ledger[data.ledger["voucher_type"] != "opening"]
    v = vouchers(lg[(lg["voucher_date"] < ctx.period_start) | (lg["voucher_date"] > ctx.period_end)])
    if v.empty:
        return []
    return [Hit("outside-period", f"{len(v)} voucher(s) dated outside {d(ctx.period_start)} to {d(ctx.period_end)}",
                f"Value {inr(v['value'].sum())}. Confirm the extract covers the right period.", 0,
                rows(v, ["voucher_no", "voucher_date", "voucher_type", "value", "narration"]))]


@rule("JE-009", "Books", "Cash balance goes negative", "high", ["ledger"],
      law="Books cannot show a credit cash balance; indicates unrecorded receipts or payments recorded early")
def negative_cash(data, p, ctx):
    """Day-end balance of a cash ledger falls below zero. Needs the opening balance in the
    extract (voucher type 'opening'); without it, days before the first receipts may show falsely."""
    cash = data.ledger[data.ledger["is_cash"]]
    hits = []
    for name, g in cash.groupby("ledger"):
        daily = (g["debit"] - g["credit"]).groupby(g["voucher_date"]).sum().sort_index().cumsum().round(2)
        negative = daily[daily < -0.5]
        if len(negative):
            hits.append(Hit(f"negcash|{name}", f"{name}: negative on {len(negative)} day(s), lowest {inr(negative.min())}",
                            f"First on {d(negative.index[0])}; lowest balance {inr(negative.min())} on {d(negative.idxmin())}.",
                            abs(negative.min()), [{"date": d(day), "closing_balance": bal} for day, bal in negative.head(200).items()]))
    return hits


@rule("JE-010", "Books", "Round-sum journals", "low", ["ledger"], law=SA240,
      params={"round_unit": (100000, "Multiple of (₹)"), "min_amount": (100000, "Minimum voucher value (₹)")}, fraud=True)
def round_sum(data, p, ctx):
    """Journals for exact multiples of the round unit — often estimates or adjustments without workings."""
    j = journals(data)
    j = j[(j["value"] >= p["min_amount"]) & (np.isclose(j["value"] % p["round_unit"], 0))]
    return monthly(j, "round", "{n} round-sum journal(s) in {month}",
                   "{n} journal(s) totalling {value} are exact multiples of " + inr(p["round_unit"]) + ". Ask for the workings.")


@rule("JE-011", "Books", "Voucher amounts depart from Benford's law", "low", ["ledger"], law=SA240,
      params={"min_vouchers": (300, "Minimum vouchers to test"), "mad_limit": (0.015, "Mean absolute deviation limit")}, fraud=True)
def benford(data, p, ctx):
    """First-digit distribution of voucher values compared with Benford's expected frequencies.
    A mean absolute deviation above 0.015 is Nigrini's threshold for nonconformity. This is an
    indicator for where to sample, not evidence of misstatement."""
    values = vouchers(data.ledger[data.ledger["voucher_type"] != "opening"])["value"]
    values = values[values >= 10]
    if len(values) < p["min_vouchers"]:
        return []
    first = values.map(lambda x: int(f"{x:e}"[0]))
    table, mad = [], 0.0
    for digit in range(1, 10):
        expected, actual = np.log10(1 + 1 / digit), float((first == digit).mean())
        mad += abs(actual - expected) / 9
        table.append({"first_digit": digit, "expected_pct": round(expected * 100, 1), "actual_pct": round(actual * 100, 1)})
    if mad <= p["mad_limit"]:
        return []
    worst = max(table, key=lambda t: t["actual_pct"] - t["expected_pct"])
    return [Hit("benford", f"Voucher amounts do not follow Benford's law (MAD {mad:.4f})",
                f"{len(values)} vouchers tested. Mean absolute deviation {mad:.4f} against a limit of {p['mad_limit']}. "
                f"Digit {worst['first_digit']} is most over-represented ({worst['actual_pct']}% against {worst['expected_pct']}%). "
                f"Direct sampling at amounts beginning with that digit.", 0, table)]


@rule("JE-012", "Books", "Journals dated on Sundays", "low", ["ledger"], law=SA240,
      params={"min_amount": (100000, "Minimum voucher value (₹)")}, fraud=True)
def sunday_journals(data, p, ctx):
    """Journal vouchers dated on a Sunday at or above the limit."""
    j = journals(data)
    j = j[(j["voucher_date"].dt.dayofweek == 6) & (j["value"] >= p["min_amount"])]
    return monthly(j, "sunday", "{n} journal(s) dated on a Sunday in {month}", "{n} journal(s) totalling {value} are dated on a Sunday.")
