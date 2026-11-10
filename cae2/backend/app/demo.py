"""Demo engagement: a fictitious trading company for FY 2025-26 with a known
exception planted for every rule. Used by `python -m app.demo` and by the tests.

Everything is generated from a fixed seed, so the same data — and therefore the
same findings — comes out every time.
"""
import io
import random
from datetime import date, timedelta

import pandas as pd

from app.statute import gstin_check_digit

START, END = date(2025, 4, 1), date(2026, 3, 31)
HOME = "27"
ENGAGEMENT_SETTINGS = {"einvoice_applicable": True, "tds_194q_applicable": True, "data_as_at": "2026-03-31"}


def gstin(state: str, pan: str) -> str:
    body = f"{state}{pan}1Z"
    return body + gstin_check_digit(body)


def _pan(i: int, kind: str = "C") -> str:
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    return f"AA{letters[i % 24]}{kind}{letters[(i * 7) % 24]}{1000 + i * 37:04d}{letters[(i * 5) % 24]}"


def demo_frames(seed: int = 7) -> dict[str, pd.DataFrame]:
    rnd = random.Random(seed)
    day = lambda offset: START + timedelta(days=offset)

    # ── parties ──
    vendor_names = ["Apex Polymers", "Bharat Steel Traders", "Chirag Packaging", "Deccan Fasteners", "Eastern Chemicals",
                    "Falcon Logistics Supplies", "Ganesh Industrial Stores", "Harsh Consultants", "Indus Hardware", "Jai Contractors",
                    "Kapoor & Co Chartered Engineers", "Laxmi Estates", "Mahavir Metals", "Navkar Tubes", "Om Fabricators",
                    "Prime Legal Associates", "Ratna Alloys", "Sai Motors", "Tulsi Caterers", "Unity Electricals"]
    vendors = []
    for i, name in enumerate(vendor_names, start=1):
        pan = _pan(i)
        vendors.append(dict(code=f"V{i:03d}", name=name, kind="vendor", gstin=gstin(HOME if i % 3 else "24", pan), pan=pan,
                            bank_account=f"50100{i:07d}", address=f"{i} Industrial Estate, Pune", msme_category=None,
                            is_related_party="No", credit_days=30))
    v = {row["code"]: row for row in vendors}
    v["V003"]["msme_category"], v["V003"]["credit_days"] = "micro", 45
    v["V004"]["msme_category"], v["V004"]["credit_days"] = "small", 60
    v["V005"]["msme_category"] = "medium"
    v["V006"]["is_related_party"] = "Yes"
    v["V007"]["bank_account"] = "917020011223344"            # same as employee E010
    v["V008"].update(gstin=None, pan=None)                   # unregistered, PAN not on record
    v["V014"]["gstin"] = v["V014"]["gstin"][:-1] + ("A" if v["V014"]["gstin"][-1] != "A" else "B")  # bad check digit
    customer_names = ["Aarav Retail", "Bluestar Distributors", "Crest Infra", "Dhanraj Stores", "Everest Marketing", "Fortune Agencies",
                      "Galaxy Enterprises", "Hind Traders", "Ideal Sales Corp", "Jupiter Mart", "Kiran Wholesale", "Lotus Impex"]
    customers = []
    for i, name in enumerate(customer_names, start=1):
        state = HOME if i % 4 else "29"
        customers.append(dict(code=f"C{i:03d}", name=name, kind="customer", gstin=gstin(state, _pan(40 + i)), pan=_pan(40 + i),
                              bank_account=None, address=f"{i} Market Road", msme_category=None,
                              is_related_party="Yes" if i == 3 else "No", credit_days=30))
    c = {row["code"]: row for row in customers}

    # ── sales ──
    sales, seq = [], 0

    def sale(when, cust, taxable, **over):
        nonlocal seq
        seq += 1
        while seq in (101, 102):   # SAL-002: two numbers never used
            seq += 1
        inter = cust["gstin"][:2] != HOME
        gst = round(taxable * 0.18, 2)
        row = dict(invoice_no=f"INV/25-26/{seq:04d}", invoice_date=when, customer_code=cust["code"], customer_name=cust["name"],
                   customer_gstin=cust["gstin"], place_of_supply=cust["gstin"][:2], supply_type="goods", taxable_value=taxable,
                   cgst=0 if inter else gst / 2, sgst=0 if inter else gst / 2, igst=gst if inter else 0,
                   total=round(taxable + gst, 2), irn=f"IRN{seq:061d}", eway_bill_no=f"{271000000000 + seq}",
                   due_date=when + timedelta(days=30), is_cancelled="No", entered_on=when)
        row["amount_received"] = row["total"] if (END - when).days > 45 else 0
        row.update(over)
        sales.append(row)
        return row

    for month in range(12):
        first = date(2025 + (month + 3) // 12, (month + 3) % 12 + 1, 1)
        for n in range(40):
            cust = customers[rnd.randrange(len(customers))]
            if cust["code"] == "C005" and month > 0:
                cust = customers[0]
            sale(first + timedelta(days=min(n * 24 // 40, 24)), cust, rnd.randrange(20, 300) * 1000.0)
    sales[49]["invoice_no"] = sales[48]["invoice_no"]                                   # SAL-001 duplicate number
    for row in sales[60:63]:
        row["irn"] = None                                                                # SAL-004
    for row in [r for r in sales[70:90] if r["total"] > 50000][:4]:
        row["eway_bill_no"] = None                                                       # SAL-005
    wrong = next(r for r in sales[100:] if r["igst"] > 0)                               # SAL-006
    wrong["cgst"] = wrong["sgst"] = wrong["igst"] / 2
    wrong["igst"] = 0
    sales[120]["total"] += 500                                                           # SAL-007
    for row in sales[:40]:
        if row["customer_code"] == "C005":
            row["amount_received"] = 0                                                   # SAL-008 old unpaid
    sale(date(2025, 4, 10), c["C005"], 250000.0, amount_received=0)
    sale(date(2025, 10, 14), c["C008"], 88000.0)                                  # SAL-010
    sale(date(2025, 10, 14), c["C008"], 88000.0)
    for n in range(12):                                                                  # SAL-011 March bunching
        sale(date(2026, 3, 29 + n % 3), customers[n % 12], 900000.0)
    for row in sale(date(2026, 3, 30), c["C002"], 400000.0), sale(date(2026, 3, 31), c["C009"], 350000.0):
        row["entered_on"] = date(2026, 4, 5)                                             # SAL-003
    august = [r for r in sales if r["invoice_date"].month == 8]
    for row in august[:4]:
        row["is_cancelled"] = "Yes"                                                      # SAL-012

    # ── purchases ──
    purchases, pseq = [], 0

    def buy(when, vend, taxable, nature="goods", tds_rate=0.0, **over):
        nonlocal pseq
        pseq += 1
        gst = round(taxable * 0.18, 2) if vend["gstin"] else 0.0
        inter = bool(vend["gstin"]) and vend["gstin"][:2] != HOME
        total = round(taxable + gst, 2)
        credit = vend["credit_days"] or 30
        paid = when + timedelta(days=min(credit, 25))
        row = dict(invoice_no=f"{vend['code']}/{pseq:04d}", invoice_date=when, booking_date=when + timedelta(days=2),
                   vendor_code=vend["code"], vendor_name=vend["name"], vendor_gstin=vend["gstin"], nature=nature,
                   taxable_value=taxable, cgst=0 if inter else gst / 2, sgst=0 if inter else gst / 2, igst=gst if inter else 0,
                   total=total, itc_claimed=gst, tds_deducted=round(taxable * tds_rate / 100, 2),
                   po_no=f"PO-{pseq:05d}", po_amount=total, grn_date=when + timedelta(days=1) if nature == "goods" else None,
                   due_date=when + timedelta(days=credit), paid_date=paid if paid <= END else None)
        row["amount_paid"] = total if row["paid_date"] else 0
        row.update(over)
        purchases.append(row)
        return row

    goods_vendors = [v[f"V{i:03d}"] for i in (1, 2, 5, 7, 9, 13)]
    for n in range(240):   # each vendor bills about every nine days, so ordinary trade does not look like splitting
        buy(day(n // 6 * 9 + n % 6), goods_vendors[n % len(goods_vendors)], float(rnd.randrange(10000, 95000)))
    for month in range(12):
        when = date(2025 + (month + 3) // 12, (month + 3) % 12 + 1, 5)
        buy(when, v["V010"], 60000.0, "contract", 2)        # 194C, company: 2% — correct
        buy(when, v["V011"], 40000.0, "professional", 10)   # 194J: 10% — correct
        buy(when, v["V012"], 80000.0, "rent", 10)           # 194I: 10% — correct
        if month < 4:
            buy(when, v["V015"], 60000.0, "contract", 0)    # TDS-001: nothing deducted
            buy(when, v["V016"], 75000.0, "professional", 5)  # TDS-002: 5% instead of 10%
            buy(when, v["V008"], 30000.0, "professional", 10)  # TDS-003: no PAN, 20% due
        if month < 8:
            buy(when + timedelta(days=3), v["V017"], 900000.0, tds_rate=0)  # 194Q crossed, nothing deducted
    first = purchases[10]
    purchases.append(dict(first, booking_date=first["booking_date"] + timedelta(days=20)))          # PUR-001
    buy(date(2025, 7, 3), v["V002"], 64000.0)
    buy(date(2025, 7, 9), v["V002"], 64000.0)                                                       # PUR-002
    buy(date(2025, 8, 4), v["V001"], 180000.0, po_no=None, po_amount=None)                          # PUR-003
    buy(date(2025, 8, 20), v["V005"], 150000.0, po_no=None, po_amount=None)
    buy(date(2025, 9, 2), v["V009"], 110000.0, po_no="PO-BLANKET-1", po_amount=100000.0)            # PUR-004
    buy(date(2025, 9, 12), v["V013"], 70000.0, grn_date=date(2025, 10, 20))                         # PUR-005 paid before GRN
    buy(date(2025, 9, 15), v["V013"], 52000.0, grn_date=None)
    buy(date(2025, 6, 1), v["V003"], 90000.0, grn_date=date(2025, 6, 2), paid_date=date(2025, 8, 30))  # PUR-006 paid late
    buy(date(2026, 1, 5), v["V004"], 140000.0, paid_date=None, amount_paid=0)                       # PUR-006 unpaid at year end
    for n, amount in enumerate((45000.0, 40000.0, 38000.0)):                                        # PUR-008
        buy(date(2025, 11, 10 + n), v["V009"], amount)
    buy(date(2025, 12, 1), v["V006"], 95000.0)                                                      # PUR-009 related party
    buy(date(2025, 10, 20), v["V002"], 30000.0, po_no=None, po_amount=None, paid_date=date(2025, 10, 5))  # PUR-010
    odd = buy(date(2025, 12, 15), v["V001"], 50000.0)
    odd["total"] += 750                                                                             # PUR-011
    odd["po_amount"] = odd["total"]
    odd["amount_paid"] = odd["total"]
    buy(date(2025, 5, 14), v["V020"], 200000.0, paid_date=None, amount_paid=0)                      # GST-004 unpaid > 180 days
    buy(date(2025, 2, 15), v["V020"], 60000.0, booking_date=date(2025, 12, 5))                      # GST-005 booked late
    buy(date(2025, 6, 18), v["V014"], 85000.0)                                                      # GST-006 invalid GSTIN
    buy(date(2025, 7, 22), v["V018"], 700000.0, nature="motor_vehicle")                             # GST-008
    buy(date(2025, 8, 9), v["V019"], 25000.0, nature="food_beverage")
    over = buy(date(2025, 9, 25), v["V002"], 40000.0)
    over["itc_claimed"] += 1200                                                                     # GST-009

    # ── GSTR-2B: mirrors the purchase register, then diverges ──
    gstr2b = []
    for row in purchases:
        if not row["vendor_gstin"] or row["vendor_code"] == "V014":
            continue
        gstr2b.append(dict(supplier_gstin=row["vendor_gstin"], supplier_name=row["vendor_name"], invoice_no=row["invoice_no"],
                           invoice_date=row["invoice_date"], taxable_value=row["taxable_value"], cgst=row["cgst"], sgst=row["sgst"],
                           igst=row["igst"], itc_available="Yes", return_period=f"{row['invoice_date']:%m-%Y}"))
    seen, unique = set(), []
    for row in gstr2b:                                         # the supplier reported the duplicate-booked invoice once
        key = (row["supplier_gstin"], row["invoice_no"])
        if key not in seen:
            seen.add(key)
            unique.append(row)
    gstr2b = unique
    v13 = [r for r in gstr2b if r["supplier_name"] == "Mahavir Metals"]
    for row in v13[:3]:
        gstr2b.remove(row)                                                                          # GST-001
    low = next(r for r in gstr2b if r["supplier_name"] == "Apex Polymers")
    low["cgst"], low["sgst"] = low["cgst"] - 900, low["sgst"] - 900                                  # GST-002
    ghost = gstin("27", _pan(77))
    for n in range(2):                                                                               # GST-003
        gstr2b.append(dict(supplier_gstin=ghost, supplier_name="Zenith Supplies", invoice_no=f"ZS-{n + 1}", invoice_date=date(2025, 11, 3),
                           taxable_value=50000.0, cgst=4500.0, sgst=4500.0, igst=0.0, itc_available="Yes", return_period="11-2025"))
    renamed = next(r for r in gstr2b if r["supplier_name"] == "Bharat Steel Traders")
    renamed["invoice_no"] = "BST/2025/" + renamed["invoice_no"].split("/")[-1]                      # probable match
    blocked = next(r for r in gstr2b if r["supplier_name"] == "Indus Hardware")
    blocked["itc_available"] = "No"                                                                 # GST-007

    # ── employees and payroll ──
    employees = []
    for i in range(1, 23):
        employees.append(dict(emp_code=f"E{i:03d}", name=f"Employee {i:02d}", pan=_pan(100 + i, "P"), bank_account=f"3020{i:08d}",
                              address=f"Flat {i}, Staff Colony", date_joined=date(2022, 1, 1) + timedelta(days=i * 20), date_left=None))
    e = {row["emp_code"]: row for row in employees}
    e["E005"]["date_left"] = date(2025, 8, 15)                 # PAY-002
    e["E010"]["bank_account"] = "917020011223344"              # PUR-007 (vendor V007)
    e["E012"]["bank_account"] = e["E011"]["bank_account"]      # PAY-003
    e["E014"]["pan"] = e["E013"]["pan"]                        # PAY-004
    payroll = []

    def pay(code, month_start, basic, **over):
        gross = round(basic * 1.5, 2)
        pf = round(min(basic, 15000) * 0.12)
        esi = -(-gross * 0.0075 // 1) if gross <= 21000 else 0
        row = dict(emp_code=code, pay_month=month_start, basic=basic, gross=gross, pf_employee=pf, esi_employee=esi, other_deductions=200.0)
        row.update(over)
        row.setdefault("net_pay", row["gross"] - row["pf_employee"] - row["esi_employee"] - row["other_deductions"])
        payroll.append(row)
        return row

    for month in range(12):
        m = date(2025 + (month + 3) // 12, (month + 3) % 12 + 1, 1)
        for i in range(1, 23):
            code = f"E{i:03d}"
            basic = 10000.0 + i * 1500
            if code == "E005" and m > date(2025, 12, 1):
                continue                                         # stays on payroll four months after leaving
            if code == "E006" and m >= date(2025, 11, 1):
                basic *= 1.8                                     # PAY-005
            row = pay(code, m, basic)
            if code == "E001":
                row["pf_employee"] = 800.0                       # PAY-006: basic 11,500, PF due 1,380
                row["net_pay"] = row["gross"] - row["pf_employee"] - row["esi_employee"] - 200
            if code == "E002":
                row["esi_employee"] = 0.0                        # PAY-007: gross 19,500
                row["net_pay"] = row["gross"] - row["pf_employee"] - 200
            if code == "E009" and month == 5:
                row["net_pay"] = row["gross"]                    # PAY-008
        if month < 3:
            pay("E099", m, 18000.0)                              # PAY-001
    pay("E015", date(2026, 1, 1), 32500.0)                       # PAY-009

    # ── stock ──
    stock = []

    def move(when, item, kind, qty, rate, ref="auto"):
        stock.append(dict(move_date=when, item_code=item, item_name=f"Item {item}", location="MAIN", movement_type=kind,
                          quantity=qty, rate=rate, reference=f"{kind[:3].upper()}-{len(stock) + 1:05d}" if ref == "auto" else ref))

    for i in range(1, 9):
        item, rate = f"I{i:02d}", 100.0 * i
        move(START, item, "opening", 500, rate, None)
        if item == "I04":
            continue                                              # INV-002: never moves
        for month in range(12):
            m = date(2025 + (month + 3) // 12, (month + 3) % 12 + 1, 8)
            move(m, item, "receipt", 300, rate * (1 + rnd.uniform(-0.03, 0.03)))
            move(m + timedelta(days=12), item, "issue", 290, rate)
    move(date(2025, 6, 25), "I03", "issue", 2500, 300.0)          # INV-001
    move(date(2025, 6, 28), "I03", "receipt", 2500, 300.0)
    move(date(2025, 12, 31), "I05", "adjust_out", 400, 500.0)     # INV-003
    move(date(2025, 10, 9), "I06", "receipt", 200, 950.0)         # INV-004 (average about 600)
    move(date(2025, 11, 2), "I07", "issue", 10, 700.0, None)      # INV-005
    move(date(2025, 11, 3), "I07", "adjust_in", 10, 700.0, None)

    # ── books ──
    ledger, vseq = [], {}

    def voucher(when, kind, lines, narration="", by="accounts1", entered=None):
        vseq[kind] = vseq.get(kind, 0) + 1
        for name, group, dr, cr in lines:
            ledger.append(dict(voucher_no=f"{kind[:3].upper()}{vseq[kind]:05d}", voucher_date=when, voucher_type=kind, ledger=name,
                               ledger_group=group, debit=dr, credit=cr, narration=narration, entered_by=by, entered_on=entered or when))

    DEBTORS, CREDITORS, BANK, CASH = "Sundry Debtors", "Sundry Creditors", "Bank Accounts", "Cash-in-Hand"
    voucher(START, "opening", [("Cash", CASH, 50000, 0), ("HDFC Bank", BANK, 2500000, 0), ("Capital Account", "Capital Account", 0, 2550000)])
    for row in sales:
        if row["is_cancelled"] == "Yes":
            continue
        gst = row["cgst"] + row["sgst"] + row["igst"]
        voucher(row["invoice_date"], "sales", [(row["customer_name"], DEBTORS, row["taxable_value"] + gst, 0),
                                               ("Sales", "Sales Accounts", 0, row["taxable_value"]), ("Output GST", "Duties & Taxes", 0, gst)],
                f"Sale {row['invoice_no']}", entered=row["entered_on"])
    for row in purchases:
        gst = row["cgst"] + row["sgst"] + row["igst"]
        voucher(row["booking_date"], "purchase", [("Purchases", "Purchase Accounts", row["taxable_value"], 0), ("Input GST", "Duties & Taxes", gst, 0),
                                                  (row["vendor_name"], CREDITORS, 0, row["taxable_value"] + gst)], f"Purchase {row['invoice_no']}")
        if row["paid_date"] and row["paid_date"] <= END:
            voucher(row["paid_date"], "payment", [(row["vendor_name"], CREDITORS, row["amount_paid"], 0), ("HDFC Bank", BANK, 0, row["amount_paid"])],
                    f"Payment {row['invoice_no']}", by="accounts2")
    J = "journal"
    voucher(date(2025, 6, 30), J, [("Depreciation", "Indirect Expenses", 41000, 0), ("Accumulated Depreciation", "Fixed Assets", 0, 40000)],
            "Depreciation Q1")                                                                                    # JE-001
    voucher(date(2025, 7, 15), J, [("Miscellaneous Expenses", "Indirect Expenses", 82000, 0), ("Sundry Payables", CREDITORS, 0, 82000)])   # JE-002
    voucher(date(2025, 7, 28), J, [("Repairs", "Indirect Expenses", 67000, 0), ("Sundry Payables", CREDITORS, 0, 67000)])
    voucher(date(2025, 9, 30), J, [("Provision for Expenses", "Indirect Expenses", 2500000, 0), ("Provisions", "Provisions", 0, 2500000)],
            "Half-year provision as per management estimate")                                                     # JE-003
    voucher(date(2025, 6, 10), "payment", [("Advance to Supplier", "Loans & Advances (Asset)", 200000, 0), ("HDFC Bank", BANK, 0, 200000)],
            "Advance", entered=date(2025, 8, 20))                                                                 # JE-004
    voucher(date(2025, 8, 11), J, [("Travelling Expenses", "Indirect Expenses", 75000, 0), ("HDFC Bank", BANK, 0, 75000)], "Travel reimbursement")  # JE-005
    voucher(date(2026, 3, 30), J, [("Bluestar Distributors", DEBTORS, 800000, 0), ("Sales", "Sales Accounts", 0, 800000)], "Sales adjustment")     # JE-006
    voucher(date(2025, 10, 6), J, [("Suspense A/c", "Suspense A/c", 135000, 0), ("Sundry Payables", CREDITORS, 0, 135000)], "Unidentified debit")  # JE-007
    voucher(date(2026, 4, 5), "payment", [("Electricity Charges", "Indirect Expenses", 22000, 0), ("HDFC Bank", BANK, 0, 22000)], "April bill")   # JE-008
    voucher(date(2025, 11, 20), J, [("Bonus Payable Expense", "Indirect Expenses", 500000, 0), ("Bonus Payable", "Provisions", 0, 500000)],
            "Bonus provision")                                                                                    # JE-010
    voucher(date(2025, 7, 6), J, [("Commission Expense", "Indirect Expenses", 160000, 0), ("Sundry Payables", CREDITORS, 0, 160000)],
            "Commission accrual")                                                                                 # JE-012 (a Sunday)
    voucher(date(2025, 5, 12), "payment", [("Repairs & Maintenance", "Indirect Expenses", 150000, 0), ("Cash", CASH, 0, 150000)],
            "Cash paid to contractor")                                                                            # TRE-001 and JE-009
    voucher(date(2025, 5, 14), "payment", [("Freight Outward", "Direct Expenses", 30000, 0), ("Cash", CASH, 0, 30000)], "Lorry freight")
    voucher(date(2025, 5, 20), "receipt", [("Cash", CASH, 300000, 0), ("Galaxy Enterprises", DEBTORS, 0, 300000)], "Cash received")   # TRE-002
    voucher(date(2025, 6, 2), "receipt", [("Cash", CASH, 50000, 0), ("Loan from Director", "Loans (Liability)", 0, 50000)], "Loan taken")  # TRE-003
    voucher(date(2025, 6, 20), "payment", [("Loan from Director", "Loans (Liability)", 25000, 0), ("Cash", CASH, 0, 25000)], "Part repaid")

    # ── bank statement ──
    bank = []
    for n, row in enumerate(purchases):
        if row["paid_date"] and row["paid_date"] <= END:
            bank.append(dict(account="HDFC-001", txn_date=row["paid_date"], description=f"NEFT {row['vendor_name']}", reference=f"UTR{n:09d}",
                             counterparty=row["vendor_name"], mode="neft", withdrawal=row["amount_paid"], deposit=0))
    for n, row in enumerate(sales):
        if row["amount_received"]:
            bank.append(dict(account="HDFC-001", txn_date=row["invoice_date"] + timedelta(days=28), description=f"RTGS {row['customer_name']}",
                             reference=f"RCP{n:09d}", counterparty=row["customer_name"], mode="rtgs", withdrawal=0, deposit=row["amount_received"]))
    extra = lambda when, party, out=0, into=0, ref="auto": bank.append(dict(
        account="HDFC-001", txn_date=when, description=f"TRF {party}", reference=f"X{len(bank):09d}" if ref == "auto" else ref,
        counterparty=party, mode="rtgs", withdrawal=out, deposit=into))
    extra(date(2025, 9, 10), "Shree Enterprises", out=500000)                    # TRE-004
    extra(date(2025, 9, 12), "Shree Enterprises", into=500000)
    extra(date(2025, 10, 3), "Vinayak Traders", out=250000, ref=None)            # TRE-005
    extra(date(2025, 12, 9), "Pooja Services", out=75000)                        # TRE-006
    extra(date(2025, 12, 9), "Pooja Services", out=75000)

    return {"parties": pd.DataFrame(vendors + customers), "sales": pd.DataFrame(sales), "purchases": pd.DataFrame(purchases),
            "gstr2b": pd.DataFrame(gstr2b), "employees": pd.DataFrame(employees), "payroll": pd.DataFrame(payroll),
            "stock": pd.DataFrame(stock), "ledger": pd.DataFrame(ledger), "bank": pd.DataFrame(bank)}


def to_xlsx(frame: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    frame.to_excel(out, index=False)
    return out.getvalue()


def load_demo(db, user: str = "demo"):
    """Creates the demo client and engagement, loads every dataset through the
    normal importer, and runs the audit."""
    from app.audit.engine import run_audit
    from app.ingest.loader import import_file
    from app.models import Client, Engagement

    client = Client(name="Demo Traders Private Limited", pan="AAGCD4821K", gstin=gstin(HOME, "AAGCD4821K"))
    db.add(client)
    db.flush()
    eng = Engagement(client_id=client.id, name="Internal audit FY 2025-26", kind="internal_audit", period_start=START, period_end=END,
                     materiality=1000000, trivial_threshold=5000, settings=dict(ENGAGEMENT_SETTINGS))
    db.add(eng)
    db.commit()
    for dataset, frame in demo_frames().items():
        batch = import_file(db, eng, dataset, f"demo_{dataset}.xlsx", to_xlsx(frame), "replace", user)
        assert batch.rows_rejected == 0, (dataset, batch.errors[:3])
    return eng, run_audit(db, eng, user)


if __name__ == "__main__":
    from app.db import SessionLocal, init_db

    init_db()
    with SessionLocal() as session:
        engagement, run = load_demo(session)
        s = run.summary
        print(f"Demo engagement #{engagement.id} loaded. Findings: {s['new']} new. Risk score {s['risk']['overall']}.")
        failed = [r["code"] for r in s["rules"] if r["status"] == "error"]
        print("Rules that failed:", ", ".join(failed) if failed else "none")
        print("Open the app and complete first-run setup to sign in.")
