"""Working-capital position from the registers.

  DSO = closing receivables / sales invoiced in the period   x days
  DPO = closing payables    / purchases booked in the period x days
  DIO = closing stock value / cost of stock issued           x days
  Cash conversion cycle = DSO + DIO - DPO

Receivables, payables, sales and purchases are all taken gross of GST so each
ratio compares like with like. "days" runs from period start to the data date.
"""
import pandas as pd

BUCKETS = [("Not due", None, 0), ("1-30", 1, 30), ("31-60", 31, 60), ("61-90", 61, 90), ("91-180", 91, 180), ("Over 180", 181, None)]


def _ageing(frame, party_col, name_col, ctx, default_credit=30):
    f = frame[frame["outstanding"] > 1].copy()
    due = f["due_date"].fillna(f["invoice_date"] + pd.Timedelta(days=default_credit))
    f["days"] = (ctx.as_at - due).dt.days
    buckets = []
    for label, low, high in BUCKETS:
        mask = (f["days"] <= 0) if low is None else (f["days"] >= low) & ((f["days"] <= high) if high else True)
        buckets.append({"bucket": label, "amount": round(float(f.loc[mask, "outstanding"].sum()), 2), "invoices": int(mask.sum())})
    top = (f.groupby(party_col).agg(name=(name_col, "first"), outstanding=("outstanding", "sum"), oldest_days=("days", "max"))
           .sort_values("outstanding", ascending=False).head(10).reset_index(drop=True))
    top["outstanding"] = top["outstanding"].round(2)
    return {"total": round(float(f["outstanding"].sum()), 2), "buckets": buckets, "top": top.to_dict("records")}


def working_capital(data, ctx) -> dict:
    in_period = lambda col: (col >= ctx.period_start) & (col <= ctx.as_at)
    sales = data.sales[~data.sales["is_cancelled"]].assign(outstanding=lambda x: x["total"] - x["amount_received"])
    purchases = data.purchases.assign(outstanding=lambda x: x["total"] - x["amount_paid"])
    days = max((ctx.as_at - ctx.period_start).days + 1, 1)

    receivables = _ageing(sales, "customer_key", "customer_name", ctx)
    payables = _ageing(purchases, "vendor_key", "vendor_name", ctx)
    sales_total = float(sales.loc[in_period(sales["invoice_date"]), "total"].sum())
    purchase_total = float(purchases.loc[in_period(purchases["invoice_date"]), "total"].sum())

    stock_value = cost_issued = 0.0
    st = data.stock[data.stock["move_date"] <= ctx.as_at]
    if not st.empty:
        from app.audit.rules.inventory import SIGN, average_rate
        rate = st["item_code"].map(average_rate(st)).fillna(0)
        signed = st["quantity"] * st["movement_type"].map(SIGN)
        stock_value = float((signed * rate).sum())
        cost_issued = float((st["quantity"] * rate)[st["movement_type"] == "issue"].sum())

    ratio = lambda closing, flow: round(closing / flow * days, 1) if flow > 0 else None
    dso, dpo, dio = ratio(receivables["total"], sales_total), ratio(payables["total"], purchase_total), ratio(stock_value, cost_issued)
    ccc = round(dso + (dio or 0) - dpo, 1) if dso is not None and dpo is not None else None
    return {"as_at": ctx.as_at.strftime("%d-%m-%Y"), "days": days, "sales": round(sales_total, 2),
            "purchases": round(purchase_total, 2), "stock_value": round(stock_value, 2), "cost_issued": round(cost_issued, 2),
            "dso": dso, "dpo": dpo, "dio": dio, "ccc": ccc, "receivables": receivables, "payables": payables}
