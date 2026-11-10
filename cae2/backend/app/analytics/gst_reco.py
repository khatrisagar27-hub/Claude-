"""GSTR-2B against the purchase register.

Match key: supplier GSTIN + invoice number (case, separators and leading zeros
ignored). Each line ends in exactly one status:

  matched         in both, tax agrees within tolerance
  value_mismatch  in both, tax differs
  probable_match  same GSTIN, same taxable value and tax, invoice number differs
  not_in_2b       ITC claimed in books, supplier has not reported the invoice
  not_in_books    reported by supplier, not booked

ITC at risk = ITC claimed on not_in_2b lines
            + ITC claimed in excess of 2B tax on value_mismatch lines
            + ITC claimed on lines 2B marks as "ITC not available".
"""
import pandas as pd

COLUMNS = ["gstin", "party", "books_invoice_no", "portal_invoice_no", "invoice_date", "books_taxable", "books_tax",
           "itc_claimed", "portal_taxable", "portal_tax", "itc_available", "status", "at_risk"]


def reconcile(purchases: pd.DataFrame, gstr2b: pd.DataFrame, tolerance: float = 1.0) -> pd.DataFrame:
    books = purchases[(purchases["vendor_gstin"] != "") & ((purchases["gst"] > 0) | (purchases["itc_claimed"] > 0))]
    b = books.groupby(["vendor_gstin", "doc"], as_index=False).agg(
        party=("vendor_name", "first"), books_invoice_no=("invoice_no", "first"), invoice_date=("invoice_date", "min"),
        books_taxable=("taxable_value", "sum"), books_tax=("gst", "sum"), itc_claimed=("itc_claimed", "sum"),
    ).rename(columns={"vendor_gstin": "gstin"})
    g = gstr2b.assign(tax=gstr2b["cgst"] + gstr2b["sgst"] + gstr2b["igst"]).groupby(["supplier_gstin", "doc"], as_index=False).agg(
        portal_party=("supplier_name", "first"), portal_invoice_no=("invoice_no", "first"), portal_date=("invoice_date", "min"),
        portal_taxable=("taxable_value", "sum"), portal_tax=("tax", "sum"), itc_available=("itc_available", "all"),
    ).rename(columns={"supplier_gstin": "gstin"})

    m = b.merge(g, on=["gstin", "doc"], how="outer", indicator=True)
    m["status"] = m["_merge"].map({"left_only": "not_in_2b", "right_only": "not_in_books", "both": "matched"}).astype(str)
    both = m["_merge"] == "both"
    m.loc[both & ((m["books_tax"] - m["portal_tax"]).abs() > tolerance), "status"] = "value_mismatch"

    # Second pass: pair leftovers of the same supplier with identical amounts.
    left = m[m["status"] == "not_in_2b"]
    drop = []
    for i, row in left.iterrows():
        candidates = m[(m["status"] == "not_in_books") & (m["gstin"] == row["gstin"])
                       & ((m["portal_tax"] - row["books_tax"]).abs() <= tolerance)
                       & ((m["portal_taxable"] - row["books_taxable"]).abs() <= tolerance)]
        if len(candidates):
            j = candidates.index[0]
            for col in ("portal_party", "portal_invoice_no", "portal_date", "portal_taxable", "portal_tax", "itc_available"):
                m.at[i, col] = m.at[j, col]
            m.at[i, "status"] = "probable_match"
            m.at[j, "status"] = "paired"
            drop.append(j)
    m = m.drop(index=drop)

    m["party"] = m["party"].fillna(m["portal_party"]).fillna("")
    m["invoice_date"] = m["invoice_date"].fillna(m["portal_date"])
    for col in ("books_taxable", "books_tax", "itc_claimed", "portal_taxable", "portal_tax"):
        m[col] = m[col].fillna(0.0).round(2)
    for col in ("books_invoice_no", "portal_invoice_no"):
        m[col] = m[col].fillna("")
    m["itc_available"] = m["itc_available"].map(lambda v: True if pd.isna(v) else bool(v))
    m["at_risk"] = 0.0
    m.loc[m["status"] == "not_in_2b", "at_risk"] = m["itc_claimed"]
    excess = (m["itc_claimed"] - m["portal_tax"]).clip(lower=0)
    m.loc[m["status"] == "value_mismatch", "at_risk"] = excess
    blocked = m["status"].isin(["matched", "value_mismatch", "probable_match"]) & ~m["itc_available"]
    m.loc[blocked, "at_risk"] = m["itc_claimed"]
    m["at_risk"] = m["at_risk"].round(2)
    return m[COLUMNS + ["doc"]].sort_values(["status", "gstin", "doc"]).reset_index(drop=True)


def summarise(reco: pd.DataFrame) -> dict:
    statuses = {}
    for status, g in reco.groupby("status"):
        statuses[status] = {"lines": int(len(g)), "books_tax": round(float(g["books_tax"].sum()), 2),
                            "itc_claimed": round(float(g["itc_claimed"].sum()), 2),
                            "portal_tax": round(float(g["portal_tax"].sum()), 2)}
    return {"statuses": statuses, "itc_claimed": round(float(reco["itc_claimed"].sum()), 2),
            "itc_in_2b": round(float(reco["portal_tax"].sum()), 2), "itc_at_risk": round(float(reco["at_risk"].sum()), 2)}
