"""Inventory rules over stock movements (quantity positive, type gives direction)."""
import pandas as pd

from app.audit.helpers import d, rows
from app.audit.registry import Hit, rule
from app.money import inr

COLS = ["move_date", "item_code", "location", "movement_type", "quantity", "rate", "reference", "source_row"]
SIGN = {"opening": 1, "receipt": 1, "adjust_in": 1, "issue": -1, "adjust_out": -1}
ORDER = {"opening": 0, "receipt": 1, "adjust_in": 2, "issue": 3, "adjust_out": 4}


def signed(data) -> pd.DataFrame:
    st = data.stock.copy()
    st["signed_qty"] = st["quantity"] * st["movement_type"].map(SIGN)
    st["order"] = st["movement_type"].map(ORDER)  # within a day, inward before outward
    return st.sort_values(["move_date", "order", "id"])


def average_rate(st: pd.DataFrame) -> pd.Series:
    """Weighted average inward rate per item (opening and receipts)."""
    inward = st[st["movement_type"].isin(["opening", "receipt"]) & (st["rate"] > 0)]
    value = (inward["quantity"] * inward["rate"]).groupby(inward["item_code"]).sum()
    return (value / inward.groupby("item_code")["quantity"].sum()).rename("avg_rate")


@rule("INV-001", "Inventory", "Stock balance goes negative", "high", ["stock"])
def negative_stock(data, p, ctx):
    """Running quantity of an item at a location falls below zero — issues recorded before receipts, or missing receipts."""
    st, hits = signed(data), []
    for (item, loc), g in st.groupby(["item_code", "location"]):
        balance = g["signed_qty"].cumsum()
        if balance.min() < -0.001:
            first = g.loc[balance[balance < -0.001].index[0]]
            hits.append(Hit(f"neg|{item}|{loc}", f"{item} at {loc}: stock negative, lowest {balance.min():,.3f}",
                            f"Balance first goes negative on {d(first['move_date'])}.", 0,
                            rows(g.assign(balance=balance.round(3)), COLS + ["balance"])))
    return hits


@rule("INV-002", "Inventory", "Non-moving stock", "medium", ["stock"], law="AS 2 / Ind AS 2: lower of cost and net realisable value",
      params={"days": (180, "Days without an issue")})
def non_moving(data, p, ctx):
    """Items held at the data date with no issue for the set number of days. Value at weighted average inward rate."""
    st = signed(data)
    st = st[st["move_date"] <= ctx.as_at]
    rate, hits = average_rate(st), []
    for item, g in st.groupby("item_code"):
        closing = g["signed_qty"].sum()
        issues = g[g["movement_type"] == "issue"]
        last = issues["move_date"].max() if len(issues) else g["move_date"].min()
        idle = (ctx.as_at - last).days
        if closing > 0.001 and idle > p["days"]:
            value = closing * float(rate.get(item, 0))
            hits.append(Hit(f"idle|{item}", f"{item}: {closing:,.2f} units idle for {idle} days — {inr(value)}",
                            ("Last issued " + d(last) if len(issues) else "Never issued since " + d(last))
                            + f". Closing quantity {closing:,.3f} valued at {inr(value)}. Assess net realisable value.",
                            value, rows(g.tail(20), COLS)))
    return hits


@rule("INV-003", "Inventory", "High stock write-offs and shortages", "high", ["stock"],
      law="CARO 2020 para 3(ii)(a): report discrepancies of 10% or more in aggregate for each class of inventory",
      params={"pct": (2, "Adjusted-out share of inward quantity (%)")})
def adjustments(data, p, ctx):
    """Quantity adjusted out (shortage, write-off) as a share of opening plus receipts."""
    st, hits = data.stock, []
    rate = average_rate(st)
    for item, g in st.groupby("item_code"):
        inward = g.loc[g["movement_type"].isin(["opening", "receipt"]), "quantity"].sum()
        lost = g.loc[g["movement_type"] == "adjust_out", "quantity"].sum()
        if inward > 0 and lost / inward * 100 > p["pct"]:
            value = lost * float(rate.get(item, 0))
            hits.append(Hit(f"adj|{item}", f"{item}: {lost / inward * 100:.1f}% of stock adjusted out — {inr(value)}",
                            f"{lost:,.3f} of {inward:,.3f} units written off or short. Check approval and physical verification records.",
                            value, rows(g[g["movement_type"] == "adjust_out"], COLS)))
    return hits


@rule("INV-004", "Inventory", "Receipt rate far from the item's average", "medium", ["stock.rate"],
      params={"variance_pct": (25, "Variance from average rate (%)"), "min_receipts": (3, "Minimum receipts for the item")})
def rate_variance(data, p, ctx):
    """Receipts priced well above or below the item's weighted average inward rate."""
    st = data.stock[(data.stock["movement_type"] == "receipt") & (data.stock["rate"] > 0)]
    st = st.join(average_rate(data.stock), on="item_code")
    st["variance_pct"] = ((st["rate"] / st["avg_rate"] - 1) * 100).round(1)
    counts = st.groupby("item_code")["rate"].transform("size")
    odd = st[(counts >= p["min_receipts"]) & (st["variance_pct"].abs() > p["variance_pct"])]
    return [Hit(f"rate|{item}", f"{item}: {len(g)} receipt(s) priced more than {p['variance_pct']}% from average",
                f"Average inward rate {inr(g['avg_rate'].iloc[0])}. Check purchase orders and price approvals.",
                float(((g["rate"] - g["avg_rate"]).clip(lower=0) * g["quantity"]).sum()),
                rows(g, COLS + ["avg_rate", "variance_pct"])) for item, g in odd.groupby("item_code")]


@rule("INV-005", "Inventory", "Stock movements without a reference document", "low", ["stock.reference"])
def no_reference(data, p, ctx):
    """Receipts, issues and adjustments with no document reference."""
    st = data.stock[(data.stock["reference"] == "") & (data.stock["movement_type"] != "opening")]
    return [Hit(f"noref|{kind}", f"{len(g)} {kind.replace('_', ' ')} movement(s) without reference",
                "Movements cannot be traced to a GRN, issue slip or approval.", 0, rows(g, COLS))
            for kind, g in st.groupby("movement_type")]
