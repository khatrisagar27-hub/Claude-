"""Cash and bank rules.

Cash tests read the books: a voucher that credits a cash ledger is a cash payment,
one that debits it is a cash receipt, and the other lines of that voucher say what
the cash was for.
"""
import pandas as pd

from app.audit.helpers import d, month, rows
from app.audit.registry import Hit, rule
from app.money import inr
from app.statute import CASH_LOAN_LIMIT, CASH_PAYMENT_LIMIT, CASH_PAYMENT_LIMIT_TRANSPORT, CASH_RECEIPT_LIMIT

LINES = ["voucher_no", "voucher_date", "voucher_type", "ledger", "ledger_group", "debit", "credit", "narration", "source_row"]
BANK = ["txn_date", "account", "description", "reference", "counterparty", "withdrawal", "deposit", "source_row"]


def cash_counterparts(data, side: str) -> pd.DataFrame:
    """Non-cash lines of vouchers in which cash is paid out (side='credit') or received (side='debit')."""
    lg = data.ledger[~data.ledger["voucher_type"].isin(["contra", "opening"])]
    cash_vouchers = lg.loc[lg["is_cash"] & (lg[side] > 0), "vkey"].unique()
    other = "debit" if side == "credit" else "credit"
    return lg[lg["vkey"].isin(cash_vouchers) & ~lg["is_cash"] & ~lg["is_bank"] & (lg[other] > 0)].assign(amount=lambda x: x[other])


@rule("TRE-001", "Treasury", "Cash payment above the s.40A(3) limit", "high", ["ledger"],
      law=f"Income-tax Act, 1961 s.40A(3): Rs {CASH_PAYMENT_LIMIT:,} per person per day "
          f"(Rs {CASH_PAYMENT_LIMIT_TRANSPORT:,} for goods carriage); exceptions in Rule 6DD",
      params={"limit": (CASH_PAYMENT_LIMIT, "Limit per person per day (₹)"),
              "transport_limit": (CASH_PAYMENT_LIMIT_TRANSPORT, "Limit for goods carriage (₹)")})
def cash_payments(data, p, ctx):
    """Cash paid to one ledger in one day above the limit. The whole payment is disallowable.
    Loan repayments are tested under TRE-003; Rule 6DD exceptions need review."""
    c = cash_counterparts(data, "credit")
    c = c[~c["is_loan"]]
    hits = []
    for (day, ledger), g in c.groupby(["voucher_date", "ledger"]):
        transport = any(word in ledger.lower() for word in ("freight", "transport", "lorry", "cartage"))
        limit, paid = (p["transport_limit"] if transport else p["limit"]), g["amount"].sum()
        if paid > limit:
            hits.append(Hit(f"40a3|{d(day)}|{ledger}", f"Cash {inr(paid)} paid to {ledger} on {d(day)}",
                            f"Aggregate cash payment of {inr(paid)} in a day exceeds {inr(limit)}. "
                            f"Disallowance of {inr(paid)} unless covered by Rule 6DD.", paid, rows(g, LINES)))
    return hits


@rule("TRE-002", "Treasury", "Cash receipt of Rs 2 lakh or more", "critical", ["ledger"],
      law="Income-tax Act, 1961 s.269ST; penalty s.271DA equal to the amount received",
      params={"limit": (CASH_RECEIPT_LIMIT, "Limit (₹)")})
def cash_receipts(data, p, ctx):
    """Cash received from one ledger in one day at or above the limit. Receipts in respect of
    a single transaction or one event spread over days also count and need review."""
    c = cash_counterparts(data, "debit")
    c = c[~c["is_loan"]]
    hits = []
    for (day, ledger), g in c.groupby(["voucher_date", "ledger"]):
        if g["amount"].sum() >= p["limit"]:
            hits.append(Hit(f"269st|{d(day)}|{ledger}", f"Cash {inr(g['amount'].sum())} received from {ledger} on {d(day)}",
                            f"Aggregate cash receipt of {inr(g['amount'].sum())} from one person in a day. "
                            f"Penalty exposure equal to the amount.", g["amount"].sum(), rows(g, LINES)))
    return hits


@rule("TRE-003", "Treasury", "Loan or deposit taken or repaid in cash", "critical", ["ledger.ledger_group"],
      law="Income-tax Act, 1961 s.269SS (acceptance) and s.269T (repayment); penalties s.271D, s.271E",
      params={"limit": (CASH_LOAN_LIMIT, "Limit (₹)")})
def cash_loans(data, p, ctx):
    """Cash movements of the limit or more against loan/deposit ledgers. The sections also
    apply where the outstanding balance reaches the limit — check smaller amounts on review."""
    hits = []
    for side, section, verb in (("debit", "s.269SS", "accepted"), ("credit", "s.269T", "repaid")):
        c = cash_counterparts(data, side)
        c = c[c["is_loan"] & (c["amount"] >= p["limit"])]
        for r in c.itertuples():
            hits.append(Hit(f"{section}|{r.vkey}|{r.ledger}", f"Loan/deposit of {inr(r.amount)} {verb} in cash — {r.ledger}",
                            f"Voucher {r.voucher_no} dated {d(r.voucher_date)}: {inr(r.amount)} {verb} in cash ({section}). "
                            f"Penalty exposure equal to the amount.", r.amount, rows(data.ledger[data.ledger["vkey"] == r.vkey], LINES)))
    return hits


@rule("TRE-004", "Treasury", "Money paid out and returned by the same party", "high", ["bank.counterparty"],
      params={"window_days": (3, "Days between payment and return"), "min_amount": (100000, "Minimum amount (₹)")}, fraud=True)
def round_trip(data, p, ctx):
    """A bank payment to a party and a deposit of the same amount from that party within a few days."""
    b = data.bank[data.bank["counterparty"] != ""]
    out = b[b["withdrawal"] >= p["min_amount"]]
    back = b[b["deposit"] >= p["min_amount"]]
    pairs = out.merge(back, left_on=["counterparty", "withdrawal"], right_on=["counterparty", "deposit"], suffixes=("_out", "_in"))
    gap = (pairs["txn_date_in"] - pairs["txn_date_out"]).dt.days
    pairs = pairs[(gap >= 0) & (gap <= p["window_days"])].drop_duplicates("id_out")
    return [Hit(f"trip|{r.counterparty}|{d(r.txn_date_out)}|{r.withdrawal_out:.2f}",
                f"{inr(r.withdrawal_out)} paid to {r.counterparty} on {d(r.txn_date_out)} and received back on {d(r.txn_date_in)}",
                "Same amount out and back within the window. Establish the commercial purpose.", r.withdrawal_out,
                rows(b[b["id"].isin([r.id_out, r.id_in])], BANK)) for r in pairs.itertuples()]


@rule("TRE-005", "Treasury", "Large bank payments without a reference", "medium", ["bank"],
      params={"min_amount": (100000, "Minimum amount (₹)")})
def no_reference(data, p, ctx):
    """Withdrawals at or above the limit with no cheque/UTR reference recorded."""
    b = data.bank[(data.bank["withdrawal"] >= p["min_amount"]) & (data.bank["reference"] == "")]
    return [Hit(f"noref|{m:%Y-%m}", f"{len(g)} bank payment(s) without reference in {month(m)}",
                f"{len(g)} payment(s) totalling {inr(g['withdrawal'].sum())} have no reference number.", 0, rows(g, BANK))
            for m, g in b.groupby(b["txn_date"].dt.to_period("M").dt.start_time)]


@rule("TRE-006", "Treasury", "Same amount paid twice to a party on one day", "high", ["bank"],
      params={"min_amount": (10000, "Minimum amount (₹)")}, fraud=True)
def duplicate_bank_payment(data, p, ctx):
    """Two or more bank payments of the same amount to the same party (or with the same description) on the same day."""
    b = data.bank[data.bank["withdrawal"] >= p["min_amount"]].copy()
    b["payee"] = b["counterparty"].where(b["counterparty"] != "", b["description"]).str.upper()
    b = b[b["payee"] != ""]
    dup = b[b.duplicated(["payee", "txn_date", "withdrawal"], keep=False)]
    return [Hit(f"duppay|{payee}|{d(day)}|{amount:.2f}", f"{len(g)} payments of {inr(amount)} to {payee} on {d(day)}",
                "Check that the second payment is not a duplicate; confirm recovery if it is.", amount * (len(g) - 1), rows(g, BANK))
            for (payee, day, amount), g in dup.groupby(["payee", "txn_date", "withdrawal"])]
