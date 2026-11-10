"""Indian-style money formatting used in every narrative: ₹1,23,45,678.90."""


def inr(amount) -> str:
    amount = float(amount or 0)
    if amount != amount:  # NaN
        return "₹—"
    sign = "-" if amount < 0 else ""
    whole, frac = f"{abs(amount):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    return f"{sign}₹{whole}.{frac}"
