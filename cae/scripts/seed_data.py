"""
Seed data: Bharat Steel & Alloys Pvt Ltd
Maharashtra | ₹120 Cr turnover | 2 years of transactions
Run: python scripts/seed_data.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import uuid
import random
from datetime import datetime, timedelta, date
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "postgresql://cae_user:cae_password@localhost:5432/cae_db")
os.environ.setdefault("SECRET_KEY", "seed-script-secret-key-32chars-xx")

from app.database import SessionLocal, engine, Base
from app.models import *  # noqa
from app.utils.security import get_password_hash

Base.metadata.create_all(bind=engine)
db = SessionLocal()
rng = random.Random(42)


def uid():
    return uuid.uuid4()


def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, delta))


def rand_dt(start: date, end: date) -> datetime:
    d = rand_date(start, end)
    return datetime(d.year, d.month, d.day, rng.randint(8, 18), rng.randint(0, 59))


def dec(val: float) -> Decimal:
    return Decimal(str(round(val, 2)))


print("Seeding tenant and company…")

from app.models.tenant import Tenant, Company
tenant_id = uid()
tenant = Tenant(id=tenant_id, name="Sagar Khatri & Associates", slug="ska", plan="enterprise", is_active=True)
db.add(tenant)

company_id = uid()
company = Company(
    id=company_id, tenant_id=tenant_id,
    name="Bharat Steel & Alloys Pvt Ltd",
    gstin="27AABCB1234M1Z5", pan="AABCB1234M", cin="U27100MH2005PTC153876",
    entity_type="Private Limited", industry_sector="Steel Manufacturing",
    city="Pune", state="Maharashtra", is_active=True,
)
db.add(company)

print("Seeding users…")

from app.models.user import User
users = []
for role, name, email in [
    ("partner", "Sagar Khatri", "sagar@ska.in"),
    ("manager", "Priya Sharma", "priya@ska.in"),
    ("auditor", "Rahul Desai", "rahul@ska.in"),
    ("cfo", "Vikram Joshi", "cfo@bharat-steel.in"),
    ("management", "Deepak Gupta", "md@bharat-steel.in"),
    ("process_owner", "Anita Singh", "purchase@bharat-steel.in"),
]:
    u = User(
        id=uid(), tenant_id=tenant_id, company_id=company_id,
        email=email, password_hash=get_password_hash("CAE@2024"),
        full_name=name, role=role, is_active=True,
    )
    db.add(u)
    users.append(u)

db.commit()

print("Seeding master data…")

from app.models.master import Customer, Vendor, Employee, GLAccount, CostCenter

for code, name, acct_type in [
    ("4001", "Sales Revenue", "Revenue"), ("5001", "Raw Material Cost", "Expense"),
    ("1001", "Trade Receivables", "Asset"), ("1002", "Inventory - RM", "Asset"),
    ("2001", "Trade Payables", "Liability"), ("9001", "Suspense Account", "Asset"),
]:
    db.add(GLAccount(id=uid(), company_id=company_id, account_code=code, account_name=name, account_type=acct_type))

for cc, cn in [("CC-MFG", "Manufacturing"), ("CC-SALES", "Sales"), ("CC-ADMIN", "Administration")]:
    db.add(CostCenter(id=uid(), company_id=company_id, cost_center_code=cc, cost_center_name=cn))

customer_ids = []
for i in range(1, 61):
    c = Customer(
        id=uid(), company_id=company_id,
        customer_code=f"CUST-{i:04d}",
        name=f"{'Related Party Co' if i <= 2 else 'Industrial Corp'} {i}",
        gstin=f"27CUST{i:04d}Z1Z{i%9+1}" if i not in (58, 59) else None,
        city=rng.choice(["Mumbai", "Pune", "Nagpur", "Nashik"]),
        state="Maharashtra",
        credit_limit=dec(rng.randint(500, 5000) * 10000),
        is_active=i not in (58, 59),
    )
    db.add(c)
    customer_ids.append(c.id)

vendor_ids = []
for i in range(1, 81):
    v = Vendor(
        id=uid(), company_id=company_id,
        vendor_code=f"VEND-{i:04d}",
        name=f"{'Related Vendor' if i <= 5 else 'Steel Suppliers'} {i}",
        gstin=f"27VEND{i:04d}Z1Z{i%9+1}" if i not in (78, 79, 80) else None,
        bank_account_number=f"SBI{i:010d}",
        is_related_party=i <= 5,
        msme_status="Small" if i > 60 else None,
        is_active=True,
    )
    db.add(v)
    vendor_ids.append(v.id)

employee_ids = []
for i in range(1, 101):
    e = Employee(
        id=uid(), company_id=company_id,
        employee_code=f"EMP-{i:04d}",
        full_name=f"Employee {i}",
        department=rng.choice(["Production", "Finance", "Sales", "HR"]),
        designation=rng.choice(["Executive", "Manager", "Senior Executive"]),
        bank_account_number=f"HDFC{i:010d}",
        pf_account_number=f"MH{i:08d}",
        date_of_joining=rand_date(date(2018, 1, 1), date(2023, 12, 31)),
        is_active=True,
    )
    db.add(e)
    employee_ids.append(e.id)

db.commit()

print("Seeding transactions…")

START = date(2023, 1, 1)
END = date(2024, 12, 31)

from app.models.transaction import SalesInvoice, PurchaseInvoice, JournalEntry, BankTransaction, InventoryMovement, PayrollRecord

print("  Sales invoices…")
DUPE_INV_NO = "SI/2024/00042-DUPE"
for i in range(1, 801):
    inv_no = DUPE_INV_NO if i in (100, 101, 102, 103) else f"SI/{rng.randint(2023,2024)}/{i:05d}"
    inv_date = rand_date(START, END)
    taxable = float(rng.randint(50, 5000) * 1000)
    if i % 60 == 0:
        taxable = float(rng.choice([200000, 500000, 1000000]))
    gst = taxable * 0.18
    total = taxable + gst
    status = "cancelled" if i in (500, 501, 502) else ("paid" if rng.random() > 0.5 else "pending")
    db.add(SalesInvoice(
        id=uid(), company_id=company_id,
        customer_id=rng.choice(customer_ids),
        invoice_number=inv_no, invoice_date=inv_date,
        gross_amount=dec(taxable), taxable_amount=dec(taxable),
        cgst_amount=dec(gst/2), sgst_amount=dec(gst/2), igst_amount=dec(0),
        total_amount=dec(total), outstanding_amount=dec(total if status == "pending" else 0),
        e_way_bill_number=f"EWB{i:010d}" if total > 50000 and i % 12 != 0 else None,
        status=status, erp_source="erp",
        raw_data={"payment_mode": "cash"} if i in (200, 201, 202) else None,
    ))

db.commit()
print("  Purchase invoices…")
for i in range(1, 601):
    inv_no = "VI-DUPE-001" if i in (300, 301, 302, 303) else f"VI-{i:06d}"
    inv_date = rand_date(START, END)
    taxable = float(rng.randint(20, 2000) * 1000)
    gst = taxable * 0.12
    total = taxable + gst
    db.add(PurchaseInvoice(
        id=uid(), company_id=company_id,
        vendor_id=vendor_ids[5] if i in (300, 301, 302, 303) else rng.choice(vendor_ids),
        invoice_number=inv_no, invoice_date=inv_date,
        our_po_number=f"PO/{i:06d}" if i % 8 != 0 else None,
        gross_amount=dec(taxable), taxable_amount=dec(taxable),
        cgst_amount=dec(gst/2), sgst_amount=dec(gst/2), igst_amount=dec(0),
        total_amount=dec(total), outstanding_amount=dec(total),
        itc_eligible=i % 15 != 0,
        status="paid" if rng.random() > 0.4 else "pending",
    ))

db.commit()
print("  Journal entries…")
user_ids = [str(u.id) for u in users[:3]]
for i in range(1, 301):
    entry_date = rand_date(START, END)
    total_dr = float(rng.randint(10, 500) * 10000)
    prepared = user_ids[i % 3]
    approved = prepared if i % 40 == 0 else user_ids[(i + 1) % 3]
    narration = None if i % 27 == 0 else f"Journal entry {i} — accrual"
    db.add(JournalEntry(
        id=uid(), company_id=company_id,
        voucher_number=f"JE/{entry_date.year}/{i:05d}",
        entry_date=entry_date,
        voucher_type=rng.choice(["journal", "journal", "payment", "receipt"]),
        narration=narration,
        total_debit=dec(total_dr), total_credit=dec(total_dr),
        posted_by_user_id=uuid.UUID(prepared),
        is_reversed=i % 100 == 0,
        is_posted=True, status="posted",
        erp_source="erp",
        raw_data={"approved_by": approved, "self_approved": prepared == approved},
    ))

db.commit()
print("  Bank transactions…")
for i in range(1, 401):
    txn_date = rand_date(START, END)
    amount = float(rng.randint(5, 5000) * 10000)
    txn_type = "debit" if rng.random() > 0.4 else "credit"
    mode = rng.choice(["NEFT", "RTGS", "UPI", "IMPS", "cheque"])
    if i % 60 == 0:
        mode = "cash"
        amount = float(rng.randint(15000, 50000))
        txn_type = "debit"
    db.add(BankTransaction(
        id=uid(), company_id=company_id,
        transaction_date=txn_date, amount=dec(amount),
        transaction_type=txn_type, transaction_mode=mode,
        reference_number=f"REF{i:010d}",
        description=f"Payment/Receipt {i}",
        counterparty_name=f"Party {rng.randint(1, 100)}",
        raw_data={"is_director_account": True} if i in (350, 351, 352) else {"approved_by": user_ids[0] if amount < 500000 else (None if i % 120 == 0 else user_ids[1])},
    ))

db.commit()
print("  Inventory movements…")
materials = [f"MAT-{i:04d}" for i in range(1, 51)]
for i in range(1, 601):
    mv_date = rand_date(START, END)
    qty = float(rng.randint(10, 1000))
    rate = float(rng.randint(500, 50000))
    mv_type = rng.choice(["goods_receipt", "goods_issue", "goods_issue", "transfer", "adjustment"])
    mat = rng.choice(materials)
    if i > 570 and mat == "MAT-0001" and mv_type == "goods_issue":
        qty = 99999.0
    db.add(InventoryMovement(
        id=uid(), company_id=company_id,
        movement_date=mv_date, item_code=mat,
        movement_type=mv_type, quantity=dec(qty),
        unit_of_measure="MT", unit_cost=dec(rate),
        total_value=dec(qty * rate),
        warehouse_from="WH-PUNE-01", warehouse_to="WH-PUNE-02" if mv_type == "transfer" else None,
        reference_document_number=f"REF/{i:06d}",
        raw_data={"off_hours": True} if i % 67 == 0 else None,
    ))

db.commit()
print("  Payroll…")
for emp_id in employee_ids[:30]:
    base = float(rng.randint(25000, 250000))
    for yr in [2023, 2024]:
        for mo in range(1, 13):
            pf = base * 0.12
            tds = base * 0.10 if base > 50000 else 0
            net = base - pf - tds
            db.add(PayrollRecord(
                id=uid(), company_id=company_id, employee_id=emp_id,
                pay_period_year=yr, pay_period_month=mo,
                basic_salary=dec(base), gross_earnings=dec(base),
                total_deductions=dec(pf + tds), net_pay=dec(net),
                pf_employee=dec(pf), pf_employer=dec(pf),
                tds_income_tax=dec(tds), payment_date=date(yr, mo, 28),
                status="paid",
            ))

# Ghost employee (PAY-001 seed)
ghost = Employee(
    id=uid(), company_id=company_id, employee_code="EMP-GHOST",
    full_name="Ghost Employee", department="IT", designation="Consultant",
    bank_account_number="GHOST1234567890", is_active=False,
)
db.add(ghost)
db.flush()
for yr in [2023, 2024]:
    for mo in range(1, 13):
        db.add(PayrollRecord(
            id=uid(), company_id=company_id, employee_id=ghost.id,
            pay_period_year=yr, pay_period_month=mo,
            basic_salary=dec(85000), gross_earnings=dec(85000),
            total_deductions=dec(10200), net_pay=dec(74800),
            pf_employee=dec(10200), pf_employer=dec(10200),
            tds_income_tax=dec(0), payment_date=date(yr, mo, 28),
            status="paid",
        ))

db.commit()
print("  Payroll done.")

print("Seeding audit rules…")

from app.models.audit import AuditRule

RULES = [
    ("SAL-001","Duplicate Invoice Number","revenue","Fraud","critical","daily"),
    ("SAL-002","Round Amount Invoice","revenue","Fraud","medium","daily"),
    ("SAL-003","Month-End Sales Spike","revenue","Financial Reporting","high","monthly"),
    ("SAL-004","Revenue Cut-Off Manipulation","revenue","Financial Reporting","critical","monthly"),
    ("SAL-005","Excessive Discount","revenue","Revenue Leakage","high","daily"),
    ("SAL-007","Missing E-Way Bill","revenue","GST","high","daily"),
    ("SAL-009","Manual Invoice Override","revenue","Authorization","critical","daily"),
    ("SAL-010","Credit Limit Breach","revenue","Financial","high","daily"),
    ("SAL-016","Invoice Cancellation Abuse","revenue","Fraud","high","monthly"),
    ("SAL-019","Weekend Invoicing","revenue","Fraud","medium","daily"),
    ("SAL-022","Cash Invoice >₹2L","revenue","Compliance","critical","daily"),
    ("SAL-034","Duplicate Sale Same Customer-Day-Amount","revenue","Fraud","critical","daily"),
    ("PUR-001","Duplicate Vendor Invoice","expenditure","Fraud","critical","daily"),
    ("PUR-002","PO-Invoice Amount Mismatch","expenditure","Authorization","high","daily"),
    ("PUR-004","Invoice Without PO","expenditure","Authorization","high","daily"),
    ("PUR-006","Split Purchase Orders","expenditure","Authorization","high","monthly"),
    ("PUR-010","Bank Account Changed Before Payment","expenditure","Fraud","critical","daily"),
    ("PUR-013","Advance Payment Without Approval","expenditure","Authorization","high","daily"),
    ("PUR-016","Duplicate Payment","expenditure","Fraud","critical","daily"),
    ("PUR-021","Same Day PO and Invoice","expenditure","Fraud","high","daily"),
    ("PUR-022","Vendor Address Matches Employee","expenditure","Fraud","critical","daily"),
    ("PUR-031","MSME Payment Delayed","expenditure","Compliance","high","weekly"),
    ("INV-001","Negative Stock Balance","inventory","Operational","critical","daily"),
    ("INV-002","Inventory Shrinkage >2%","inventory","Fraud","high","monthly"),
    ("INV-005","Slow Moving Stock","inventory","Working Capital","medium","monthly"),
    ("INV-007","Ghost Inventory","inventory","Fraud","critical","monthly"),
    ("INV-010","Off-Hours Inventory Movement","inventory","Fraud","high","daily"),
    ("INV-015","Over-Receipt on PO","inventory","Fraud","high","daily"),
    ("JE-001","Manual JE Without Narration","bank_reconciliation","Financial Reporting","high","daily"),
    ("JE-002","Late Closing JE","bank_reconciliation","Financial Reporting","critical","monthly"),
    ("JE-003","Large Manual JE","bank_reconciliation","Authorization","high","daily"),
    ("JE-005","Uncleared Suspense Account","bank_reconciliation","Financial Reporting","high","weekly"),
    ("JE-006","Orphan Reversal","bank_reconciliation","Fraud","critical","daily"),
    ("JE-009","Unbalanced Journal Entry","bank_reconciliation","Financial Reporting","critical","daily"),
    ("JE-011","SoD Violation Self Approval","bank_reconciliation","Authorization","critical","daily"),
    ("JE-015","Prior Period JE","bank_reconciliation","Financial Reporting","high","monthly"),
    ("PAY-001","Ghost Employee","payroll","Fraud","critical","monthly"),
    ("PAY-002","Salary Spike >50%","payroll","Authorization","high","monthly"),
    ("PAY-003","Duplicate Bank Account in Payroll","payroll","Fraud","critical","monthly"),
    ("PAY-004","Post-Termination Pay","payroll","Fraud","critical","monthly"),
    ("PAY-005","PF/ESI Not Deposited","payroll","Compliance","high","monthly"),
    ("PAY-009","Bank Account Changed in Pay Month","payroll","Fraud","critical","monthly"),
    ("TRE-001","Cash Payment >₹10K","bank_reconciliation","Compliance","high","daily"),
    ("TRE-002","Circular Bank Transfer","bank_reconciliation","Fraud","critical","daily"),
    ("TRE-004","Unapproved Transfer >₹5L","bank_reconciliation","Authorization","critical","daily"),
    ("TRE-005","Multiple Payments Same Party Day","bank_reconciliation","Fraud","high","daily"),
    ("TRE-006","Director Account Payment","bank_reconciliation","Fraud","critical","daily"),
    ("TRE-010","Structured Cash Withdrawal","bank_reconciliation","Fraud","critical","daily"),
]

for rule_code, rule_name, category, risk_area, severity, frequency in RULES:
    db.add(AuditRule(
        id=uid(), company_id=company_id,
        rule_code=rule_code, rule_name=rule_name,
        category=category, risk_area=risk_area,
        severity=severity, run_frequency=frequency,
        rule_type="python", is_active=True,
        auto_raise_exception=True,
        description=f"Detects {rule_name} in {category} transactions.",
        remediation_guidance=f"Review and obtain documentation for {rule_name}. Escalate if unresolved within 7 days.",
    ))

db.commit()
print(f"  {len(RULES)} rules seeded.")

print("\n✅ Seed complete!")
print(f"   Company ID: {company_id}")
print(f"   Login: sagar@ska.in / CAE@2024")
print(f"   Next: python scripts/run_first_audit.py")
db.close()
