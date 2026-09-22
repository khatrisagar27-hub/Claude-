"""
Volume test data: ~2 lakh clean transactions plus planted anomalies with known counts.
Creates a separate company "Stress Test Industries Pvt Ltd" (the demo company is untouched)
and writes the expected exception count per rule to stress_expected.json.
Run: python scripts/stress_seed.py      then: python scripts/stress_check.py
Needs Postgres — the SQLite test suite cannot reproduce Postgres/DuckDB type behaviour.
"""
import os
import sys
_backend = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, _backend if os.path.exists(_backend) else os.path.join(os.path.dirname(__file__), '..'))

import json
import random
import uuid
from collections import Counter
from datetime import date, datetime, timedelta

os.environ.setdefault("DATABASE_URL", "postgresql://cae_user:cae_password@localhost:5432/cae_db")
os.environ.setdefault("SECRET_KEY", "seed-script-secret-key-32chars-xx")

from app.database import engine, Base
import app.models  # noqa: F401

T = Base.metadata.tables
rng = random.Random(7)
U = uuid.uuid4
START, END = date(2024, 4, 1), date(2026, 8, 31)
SPAN = (END - START).days
EXP = {}
EXPECTED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stress_expected.json")


def weekday_date(start=START, span=SPAN):
    while True:
        d = start + timedelta(days=rng.randint(0, span))
        if d.weekday() < 5:
            return d


def days_of_week(wd):
    return [d for d in (START + timedelta(days=x) for x in range(SPAN)) if d.weekday() == wd]


def dt(d, days=0):
    return datetime(d.year, d.month, d.day, 11, 0) + timedelta(days=days)


def money(lo, hi):
    return round(rng.uniform(lo, hi), 2)


def fy(d):
    return d.year if d.month >= 4 else d.year - 1


def ins(table, rows):
    # executemany takes its column list from the first row, so give every row every key.
    keys = set().union(*rows)
    rows = [{k: r.get(k) for k in keys} for r in rows]
    with engine.begin() as c:
        for i in range(0, len(rows), 5000):
            c.execute(T[table].insert(), rows[i:i + 5000])
    print(f"  {table}: {len(rows):,}")


now = datetime.now()
tenant_id, CID = U(), U()
ins("tenants", [dict(id=tenant_id, name="Stress Tenant", slug=f"stress-{tenant_id.hex[:6]}", plan="enterprise", is_active=True, created_at=now)])
ins("companies", [dict(id=CID, tenant_id=tenant_id, name="Stress Test Industries Pvt Ltd", is_active=True, created_at=now)])
users = [U() for _ in range(15)]
SAT, SUN, MON = days_of_week(5), days_of_week(6), days_of_week(0)

# ---------------- masters ----------------
customers = [dict(id=U(), company_id=CID, customer_code=f"C{i:04d}", name=f"Customer {i}", country="India",
                  gstin=f"27AAAC{i:04d}X1Z{i % 10}" if i >= 20 else None, is_active=True, created_at=now) for i in range(400)]
B2B = customers[20:]
vendors = [dict(id=U(), company_id=CID, vendor_code=f"V{i:04d}", name=f"Vendor {i}", country="India",
                msme_status="Micro" if i < 60 else None, bank_account_number=f"50100{i:08d}",
                is_related_party=False, is_active=True, created_at=now) for i in range(300)]
employees = [dict(id=U(), company_id=CID, employee_code=f"E{i:04d}", full_name=f"Employee {i}",
                  bank_account_number=f"91900{i:08d}", is_active=True, date_of_joining=date(2020, 1, 1),
                  created_at=now) for i in range(500)]
for i in range(5):                       # PUR-022: vendor paid into an employee's account
    vendors[100 + i]["bank_account_number"] = employees[i]["bank_account_number"]
EXP["PUR-022"] = 5
for i in range(490, 500):                # PAY-001 / PAY-004
    employees[i]["is_active"] = False
    if i < 498:
        employees[i]["date_of_leaving"] = date(2025, 12, 31)
EXP["PAY-001"], EXP["PAY-004"] = 10, 8
for i in range(4):                       # PAY-003
    employees[400 + i]["bank_account_number"] = employees[300 + i]["bank_account_number"]
EXP["PAY-003"] = 4
for i in range(5):                       # SAL-010: 5 customers with a ₹50,000 limit
    customers[200 + i]["credit_limit"] = 50000
EXP["SAL-010"] = 5
ins("customers", customers); ins("vendors", vendors); ins("employees", employees)


# ---------------- sales ----------------
def sale(num, d, amt, cust=None, **kw):
    gross = round(amt / 1.18, 2); tax = round(amt - gross, 2)
    r = dict(id=U(), company_id=CID, customer_id=(cust or rng.choice(B2B))["id"], invoice_number=num,
             invoice_date=d, due_date=d + timedelta(days=30), currency="INR", exchange_rate=1,
             gross_amount=gross, discount_amount=round(gross * rng.uniform(0, 0.08), 2), taxable_amount=gross,
             cgst_amount=round(tax / 2, 2), sgst_amount=round(tax / 2, 2), igst_amount=0, cess_amount=0,
             tds_amount=0, total_amount=amt, paid_amount=amt, outstanding_amount=0, reverse_charge=False,
             e_invoice_irn="IRN" + uuid.uuid4().hex, e_way_bill_number=f"{rng.randint(10**11, 10**12 - 1)}",
             status="paid", erp_source="tally", created_at=dt(d, rng.randint(0, 3)))
    r.update(kw)
    return r


S = [sale(f"S/{i:06d}", weekday_date(), money(5000, 490000)) for i in range(60000)]
for i in range(80):
    S.append(sale(f"S/{i:06d}", weekday_date(), money(5000, 90000)))
EXP["SAL-001"] = 80
for i in range(120):
    S.append(sale(f"SR/{i}", weekday_date(), float(rng.randint(100, 450) * 1000)))
for i in range(60):
    d = weekday_date(); S.append(sale(f"SL/{i}", d, money(150000, 400000), created_at=dt(d, 70)))
EXP["SAL-004"] = 60
for i in range(70):
    r = sale(f"SD/{i}", weekday_date(), money(20000, 90000)); r["discount_amount"] = round(r["gross_amount"] * 0.25, 2); S.append(r)
EXP["SAL-005"] = 70
for i in range(200):
    S.append(sale(f"SE/{i}", weekday_date(), money(60000, 400000), e_way_bill_number=None))
EXP["SAL-007"] = 200
for i in range(40):
    S.append(sale(f"SM/{i}", weekday_date(), money(150000, 400000), erp_source="manual"))
EXP["SAL-009"] = 40
for i in range(5):                       # SAL-010: ₹80,000 open against a ₹50,000 limit
    S.append(sale(f"SCL/{i}", weekday_date(), 80000.0, cust=customers[200 + i], status="confirmed",
                  paid_amount=0, outstanding_amount=80000.0))
for c in range(3):
    for k in range(7):
        S.append(sale(f"SC/{c}/{k}", date(2025, 6, 2 + k), money(10000, 50000), cust=customers[20 + c], status="cancelled"))
EXP["SAL-016"] = 3
for i in range(25):                      # SAL-019: 50 weekend; 30 Monday decoys must not be flagged
    S.append(sale(f"SWSat/{i}", rng.choice(SAT), money(600000, 900000)))
    S.append(sale(f"SWSun/{i}", rng.choice(SUN), money(600000, 900000)))
for i in range(30):
    S.append(sale(f"SMon/{i}", rng.choice(MON), money(600000, 900000)))
EXP["SAL-019"] = 50
# SAL-021: B2B without IRN once a *prior* FY crossed ₹5 Cr. Data starts FY 2024-25, so only
# FY 2025-26 invoices qualify; B2C and FY 2024-25 decoys must not be flagged.
for i in range(45):
    S.append(sale(f"SI/{i}", weekday_date(date(2025, 4, 1), 480), money(20000, 900000), e_invoice_irn=None))
for i in range(10):
    S.append(sale(f"SIb2c/{i}", weekday_date(date(2025, 4, 1), 480), money(20000, 90000), cust=customers[i], e_invoice_irn=None))
    S.append(sale(f"SIfy24/{i}", weekday_date(date(2024, 4, 1), 300), money(20000, 90000), e_invoice_irn=None))
EXP["SAL-021"] = 45
for i in range(30):
    c, d, a = B2B[50 + i], weekday_date(), money(10000, 90000)
    S.append(sale(f"SX/{i}/a", d, a, cust=c)); S.append(sale(f"SX/{i}/b", d, a, cust=c))
for k, a in enumerate([11111.11, 22222.22]):     # one customer, one day, two duplicate pairs
    S.append(sale(f"SY/{k}/a", date(2025, 3, 4), a, cust=B2B[99])); S.append(sale(f"SY/{k}/b", date(2025, 3, 4), a, cust=B2B[99]))
EXP["SAL-034"] = 32
# Random clean amounts can land on an exact thousand too, so count from the data.
EXP["SAL-002"] = sum(1 for r in S if r["total_amount"] >= 100000 and r["status"] != "cancelled"
                     and round(r["total_amount"] * 100) % 100000 == 0)
ins("sales_invoices", S)


# ---------------- purchases ----------------
def pur(v, num, d, amt, **kw):
    gross = round(amt / 1.18, 2); tax = round(amt - gross, 2)
    r = dict(id=U(), company_id=CID, vendor_id=v["id"], invoice_number=num, our_po_number=f"PO{rng.randint(1, 10**7)}",
             invoice_date=d, due_date=d + timedelta(days=30), receipt_date=d, currency="INR", exchange_rate=1,
             gross_amount=gross, discount_amount=0, taxable_amount=gross, cgst_amount=round(tax / 2, 2),
             sgst_amount=round(tax / 2, 2), igst_amount=0, cess_amount=0, tds_amount=0, total_amount=amt,
             paid_amount=amt, outstanding_amount=0, reverse_charge=False, itc_eligible=True, status="paid",
             approved_by_user_id=rng.choice(users), erp_source="tally", created_at=dt(d))
    r.update(kw)
    r["outstanding_amount"] = round(r["total_amount"] - r["paid_amount"], 2)
    return r


P = []
for i in range(30000):
    v = vendors[i % 300]
    P.append(pur(v, f"{v['vendor_code']}/B{i}", weekday_date(), money(10000, 95000) if rng.random() < .8 else money(100000, 400000)))
for i in range(50):
    v = vendors[150 + i]
    P += [pur(v, f"DUP/{i}", weekday_date(), money(10000, 90000)), pur(v, f"DUP/{i}", weekday_date(), money(10000, 90000))]
for v in (vendors[250], vendors[251]):   # same invoice number at two vendors = two findings
    P += [pur(v, "1", weekday_date(), money(10000, 90000)), pur(v, "1", weekday_date(), money(10000, 90000))]
EXP["PUR-001"] = 52
for i in range(40):
    a = money(100000, 300000); P.append(pur(vendors[100 + i], f"PM/{i}", weekday_date(), a, raw_data={"po_value": round(a / 1.2, 2)}))
EXP["PUR-002"] = 40
for i in range(60):
    P.append(pur(vendors[100 + i], f"NP/{i}", weekday_date(), money(150000, 450000), our_po_number=None))
for i in range(25):                      # unapproved, pending, no PO — MSME vendors, so PUR-031 too
    P.append(pur(vendors[i], f"UA/{i}", date(2026, 5, 4), money(600000, 900000), our_po_number=None,
                 approved_by_user_id=None, status="pending", paid_amount=0))
EXP["PUR-004"], EXP["PUR-013"] = 85, 25
for i in range(20):
    a = money(50000, 90000); v = vendors[200 + i]
    P += [pur(v, f"DP/{i}/a", weekday_date(), a), pur(v, f"DP/{i}/b", weekday_date(), a)]
for i in range(5):                       # PUR-006: two just-below-limit bills, same vendor, same day
    d = weekday_date()
    P += [pur(vendors[260 + i], f"SPL/{i}/{k}", d, money(60000, 95000)) for k in range(2)]
for i in range(80):
    d = date(2026, 5, 1) + timedelta(days=i % 30)
    P.append(pur(vendors[i % 60], f"MS/{i}", d, money(20000, 90000), status="approved", paid_amount=0))
EXP["PUR-031"] = 80 + 25
ins("purchase_invoices", P)

# Oracles for rules that also fire on coincidences in random data, computed independently here.
split = Counter((p["vendor_id"], p["invoice_date"]) for p in P if 50000 <= p["total_amount"] < 100000 and p["status"] != "cancelled")
EXP["PUR-006"] = sum(1 for n in split.values() if n >= 2)
dup_paid = Counter((p["vendor_id"], p["total_amount"]) for p in P if p["status"] == "paid")
EXP["PUR-016"] = sum(1 for n in dup_paid.values() if n >= 2)

# ---------------- journals ----------------
J, L = [], []


def je(num, d, amt, vtype="journal", narr="Being provision for expenses", posted=None, user=None, lines=None, **kw):
    jid = U()
    J.append(dict(id=jid, company_id=CID, voucher_number=num, entry_date=d, voucher_type=vtype, narration=narr,
                  currency="INR", total_debit=amt, total_credit=amt, is_posted=True, is_reversed=False,
                  status="posted", posted_by_user_id=user or rng.choice(users),
                  posted_at=posted or dt(d, rng.randint(0, 3)), created_at=dt(d)))
    J[-1].update(kw)
    for n, (code, name, dr, cr) in enumerate(lines or [("5001", "Expenses", amt, 0), ("2001", "Creditors", 0, amt)]):
        L.append(dict(id=U(), journal_entry_id=jid, line_number=n + 1, account_code=code, account_name=name,
                      debit_amount=dr, credit_amount=cr, currency="INR"))


for i in range(20000):
    je(f"JV/{i}", weekday_date(), money(1000, 450000), vtype=rng.choice(["journal", "payment", "receipt"]))
for i in range(40): je(f"JN/{i}", weekday_date(), money(150000, 450000), narr="")
EXP["JE-001"] = 40
for i in range(30):
    d = date(2025, 2, 3) + timedelta(days=i); je(f"JL/{i}", d, money(150000, 450000), posted=dt(d, 25))
for i in range(30): je(f"JB/{i}", weekday_date(), money(1500000, 5000000))
EXP["JE-003"] = 30
for i in range(25):
    a = money(60000, 400000); je(f"JS/{i}", weekday_date(), a, lines=[("SUSP01", "Suspense A/c", a, 0), ("2001", "Creditors", 0, a)])
EXP["JE-005"] = 25
for i in range(15): je(f"JR/{i}", weekday_date(), money(10000, 90000), is_reversed=True)
EXP["JE-006"] = 15
for i in range(25):
    a = money(10000, 90000); je(f"JU/{i}", weekday_date(), a, lines=[("5001", "Expenses", a, 0), ("2001", "Creditors", 0, a - 5000)])
EXP["JE-009"] = 25
for i in range(12): je(f"JX/{i}", weekday_date(), money(600000, 900000), user=users[0])
EXP["JE-011"] = 1
for i in range(20):                      # dated late March, posted 2 April: prior financial year
    je(f"JP/{i}", date(2025, 3, 10 + i), money(150000, 450000), posted=dt(date(2025, 4, 2)))
EXP["JE-002"] = sum(1 for j in J if j["total_debit"] > 100000 and (j["posted_at"].date() - j["entry_date"]).days > 10)
EXP["JE-015"] = sum(1 for j in J if j["total_debit"] > 100000 and fy(j["entry_date"]) < fy(j["posted_at"].date()))
ins("journal_entries", J); ins("journal_entry_lines", L)

# ---------------- bank ----------------
B = []


def bank(d, amt, typ="debit", mode="NEFT", party=None, ref="auto", desc="Vendor payment"):
    B.append(dict(id=U(), company_id=CID, transaction_date=d, transaction_type=typ, amount=amt, transaction_mode=mode,
                  counterparty_name=party or f"Vendor {rng.randint(0, 299)}",
                  reference_number=(f"UTR{rng.randint(10**9, 10**10)}" if ref == "auto" else ref),
                  description=desc, is_reconciled=True, created_at=dt(d)))


for i in range(20000):
    bank(weekday_date(), money(1000, 380000), typ=rng.choice(["debit", "credit"]), mode=rng.choice(["NEFT", "RTGS", "UPI", "cheque"]))
for i in range(50): bank(weekday_date(), money(12000, 90000), mode="cash", party=f"Cash Party {i}")
for i in range(10):                      # 3 x ₹9,000 to one party in a day: ₹27,000 breaches s.40A(3)
    d = weekday_date()
    for _ in range(3): bank(d, 9000.0, mode="cash", party=f"Split Cash Party {i}")
bank(date(2025, 1, 6), 50000.0, mode="cash", party="Repeat Cash Party"); bank(date(2025, 2, 6), 50000.0, mode="cash", party="Repeat Cash Party")
for i in range(10):
    d = weekday_date(); a = money(600000, 900000)
    bank(d, a, party=f"Rotation Party {i}"); bank(d + timedelta(days=1), a, typ="credit", party=f"Rotation Party {i}")
EXP["TRE-002"] = 10
for i in range(30): bank(weekday_date(), money(600000, 900000), mode="RTGS", ref=None, party=f"NoRef Party {i}")
EXP["TRE-004"] = 30
for i in range(10):
    d = weekday_date()
    for _ in range(3): bank(d, money(200000, 300000), party=f"Multi Party {i}")
for i in range(15): bank(weekday_date(), money(150000, 400000), party=f"Mr Director {i}", desc="Loan to director")
EXP["TRE-006"] = 15
for i in range(8):
    d = weekday_date()
    for _ in range(2): bank(d, money(850000, 980000), mode="cash", party="Self")
EXP["TRE-010"] = 8
for i in range(6):                       # SAL-022: 2 x ₹1.2 lakh cash from one person in a day
    d = weekday_date()
    for _ in range(2): bank(d, 120000.0, typ="credit", mode="cash", party=f"Cash Buyer {i}")
EXP["SAL-022"] = 6
cash_sum = Counter()
for b in B:
    if b["transaction_type"] == "debit" and b["transaction_mode"] == "cash":
        cash_sum[(b["counterparty_name"], b["transaction_date"])] += b["amount"]
EXP["TRE-001"] = sum(1 for v in cash_sum.values() if v > 10000)
multi = Counter(); multi_amt = Counter()
for b in B:
    if b["transaction_type"] == "debit":
        k = (b["counterparty_name"], b["transaction_date"]); multi[k] += 1; multi_amt[k] += b["amount"]
EXP["TRE-005"] = sum(1 for k, n in multi.items() if n > 2 and multi_amt[k] > 500000)
ins("bank_transactions", B)

# ---------------- inventory ----------------
I = []


def mv(item, d, typ, qty, rate=500.0, wh_from=None, wh_to=None, ref=None):
    I.append(dict(id=U(), company_id=CID, movement_date=d, movement_type=typ, item_code=item, unit_of_measure="NOS",
                  quantity=qty, unit_cost=rate, total_value=round(qty * rate, 2), warehouse_from=wh_from, warehouse_to=wh_to,
                  reference_document_number=ref or f"R{rng.randint(1, 10**9)}", created_at=dt(d)))


recent = [d for d in (date(2026, 6, 1) + timedelta(days=x) for x in range(90)) if d.weekday() < 5]
for k in range(200):
    item = f"ITEM-{k:04d}"
    mv(item, date(2024, 4, 1), "opening", 5000, wh_to="WH-1")
    for _ in range(70):
        mv(item, weekday_date(), "goods_receipt", rng.randint(50, 200), wh_to="WH-1")
        mv(item, weekday_date(), "goods_issue", rng.randint(50, 150), wh_from="WH-1")
    mv(item, rng.choice(recent), "transfer", 100, wh_from="WH-1", wh_to="WH-2")
    mv(item, rng.choice(recent), "goods_issue", 10, wh_from="WH-2")
for k in range(10):
    item = f"NEG-{k}"; mv(item, weekday_date(), "goods_receipt", 100, wh_to="WH-1"); mv(item, rng.choice(recent), "goods_issue", 300, wh_from="WH-1")
EXP["INV-001"] = 10
for k in range(8):
    item = f"SHR-{k}"
    for _ in range(5): mv(item, weekday_date(), "goods_receipt", 1000, wh_to="WH-1")
    mv(item, rng.choice(recent), "adjustment", -500, wh_from="WH-1")
EXP["INV-002"] = 8
for k in range(6):
    mv(f"GHO-{k}", rng.choice(recent), "goods_receipt", 1000, rate=2000.0, wh_to="WH-1")
EXP["INV-007"] = 6
for k in range(12):
    for d in (date(2024, 6, 3), date(2024, 7, 1), date(2024, 8, 1)):
        mv(f"SLW-{k}", d, "goods_receipt", 100, wh_to="WH-1")
EXP["INV-005"] = 12
for k in range(10):
    mv(f"ITEM-{k:04d}", rng.choice(SAT if k < 5 else SUN), "goods_receipt", 1000, rate=300.0, wh_to="WH-1")
EXP["INV-010"] = 10
for k in range(10):
    for _ in range(3): mv(f"ITEM-{k:04d}", weekday_date(), "goods_receipt", 10, wh_to="WH-1", ref=f"PO-OVR-{k}")
EXP["INV-015"] = 10
ins("inventory_movements", I)

# ---------------- payroll ----------------
PR = []
months = [(y, m) for y in (2024, 2025, 2026) for m in range(1, 13) if date(2024, 4, 1) <= date(y, m, 1) <= date(2026, 8, 1)]
for idx, e in enumerate(employees):
    base = float(rng.randint(15000, 90000))
    for (y, m) in months:
        if e.get("date_of_leaving") and date(y, m, 1) > date(2026, 3, 1):
            continue
        sal = base * 2 if idx < 10 and (y, m) >= ((2026, 1) if idx < 5 else (2025, 7)) else base
        basic = round(sal * .5, 2)
        pf = round(min(basic, 15000) * .12, 2)
        if idx in (450, 451, 452) and (y, m) == (2025, 10):   # PAY-005: PF short in one month
            pf = round(pf / 2, 2)
        esi_ee = round(sal * .0075, 2) if sal <= 21000 else 0
        esi_er = round(sal * .0325, 2) if sal <= 21000 else 0
        tds = round(sal * .05, 2)
        ded = pf + esi_ee + tds + 200
        PR.append(dict(id=U(), company_id=CID, employee_id=e["id"], pay_period_year=y, pay_period_month=m,
                       payment_date=date(y, m, 28), basic_salary=basic, hra=round(sal * .2, 2), special_allowance=round(sal * .3, 2),
                       conveyance_allowance=0, medical_allowance=0, lta=0, performance_bonus=0, other_earnings=0,
                       gross_earnings=sal, pf_employee=pf, pf_employer=pf, esic_employee=esi_ee, esic_employer=esi_er,
                       professional_tax=200, tds_income_tax=tds, advance_deduction=0, other_deductions=0,
                       total_deductions=ded, net_pay=round(sal - ded, 2), status="paid", created_at=now))
EXP["PAY-002"] = 10
EXP["PAY-005"] = 1
for i in range(12):                      # PAY-009: gross ₹2L, net ₹80k
    PR.append(dict(PR[i * 29], id=U(), pay_period_year=2023, pay_period_month=1 + i, gross_earnings=200000,
                   basic_salary=100000, pf_employee=1800.0, pf_employer=1800.0, net_pay=80000))
EXP["PAY-009"] = 12
ins("payroll_records", PR)

# ---------------- rules (same catalogue as the demo seed) ----------------
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_data.py"), encoding="utf-8").read()
start = src.index("RULES = [")
RULES = eval(src[start + 8: src.index("\n]\n", start) + 2])
ins("audit_rules", [dict(id=U(), company_id=CID, rule_code=c, rule_name=n, category=cat, risk_area=ra, severity=sev,
                         run_frequency=f, rule_type="python", is_active=True, auto_raise_exception=True,
                         requires_approval=False, created_at=now) for c, n, cat, ra, sev, f in RULES])
for code, *_ in RULES:
    EXP.setdefault(code, 0)
json.dump({"company_id": str(CID), "expected": EXP}, open(EXPECTED_FILE, "w"), indent=1, sort_keys=True)
print(f"\nCompany {CID}; expected counts written to {EXPECTED_FILE}")
