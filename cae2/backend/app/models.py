"""All database tables.

Three groups:
  1. Practice    — users, clients, engagements
  2. Client data — one table per dataset, every row tied to an engagement
  3. Audit       — rule settings, runs, findings and their review trail
"""
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

Money = Numeric(18, 2)
Qty = Numeric(18, 3)


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ───────────────────────── 1. Practice ─────────────────────────

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20))  # partner | manager | staff
    password_hash: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    pan: Mapped[str | None] = mapped_column(String(10))
    gstin: Mapped[str | None] = mapped_column(String(15))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    engagements: Mapped[list["Engagement"]] = relationship(back_populates="client", cascade="all, delete-orphan")


class Engagement(Base):
    """One audit assignment: a client, a period, and the thresholds that apply to it."""
    __tablename__ = "engagements"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(30), default="internal_audit")
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    # Rupees. Impact at or above materiality escalates a finding to critical;
    # impact below the trivial threshold steps it down one level.
    materiality: Mapped[Decimal] = mapped_column(Money, default=0)
    trivial_threshold: Mapped[Decimal] = mapped_column(Money, default=0)
    # Applicability switches the engine cannot infer from data (see audit/context.py).
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    client: Mapped[Client] = relationship(back_populates="engagements")


# ───────────────────────── 2. Client data ─────────────────────────

class ImportBatch(Base):
    __tablename__ = "import_batches"
    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(ForeignKey("engagements.id"), index=True)
    dataset: Mapped[str] = mapped_column(String(30))
    filename: Mapped[str] = mapped_column(String(300))
    mode: Mapped[str] = mapped_column(String(10))  # replace | append
    rows_read: Mapped[int] = mapped_column(Integer, default=0)
    rows_loaded: Mapped[int] = mapped_column(Integer, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    unmapped_columns: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[list] = mapped_column(JSON, default=list)  # assumptions made while loading
    uploaded_by: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class _Data:
    """Columns shared by every client-data table."""
    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(ForeignKey("engagements.id"), index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"))
    source_row: Mapped[int] = mapped_column(Integer, default=0)  # row number in the uploaded file


class Party(_Data, Base):
    """Customer / vendor master."""
    __tablename__ = "parties"
    code: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(10), default="vendor")  # customer | vendor | both
    gstin: Mapped[str | None] = mapped_column(String(15))
    pan: Mapped[str | None] = mapped_column(String(10))
    bank_account: Mapped[str | None] = mapped_column(String(40))
    address: Mapped[str | None] = mapped_column(String(400))
    msme_category: Mapped[str | None] = mapped_column(String(10))  # micro | small | medium
    is_related_party: Mapped[bool] = mapped_column(Boolean, default=False)
    credit_days: Mapped[int | None] = mapped_column(Integer)


class LedgerEntry(_Data, Base):
    """The books: one row per voucher line (day book)."""
    __tablename__ = "ledger_entries"
    voucher_no: Mapped[str] = mapped_column(String(60))
    voucher_date: Mapped[date] = mapped_column(Date)
    voucher_type: Mapped[str] = mapped_column(String(30))  # sales, purchase, payment, receipt, journal, contra, ...
    ledger: Mapped[str] = mapped_column(String(200))
    ledger_group: Mapped[str | None] = mapped_column(String(100))
    debit: Mapped[Decimal] = mapped_column(Money, default=0)
    credit: Mapped[Decimal] = mapped_column(Money, default=0)
    narration: Mapped[str | None] = mapped_column(Text)
    entered_by: Mapped[str | None] = mapped_column(String(100))
    entered_on: Mapped[date | None] = mapped_column(Date)


class SalesInvoice(_Data, Base):
    __tablename__ = "sales_invoices"
    invoice_no: Mapped[str] = mapped_column(String(60))
    invoice_date: Mapped[date] = mapped_column(Date)
    customer_code: Mapped[str | None] = mapped_column(String(60))
    customer_name: Mapped[str] = mapped_column(String(200))
    customer_gstin: Mapped[str | None] = mapped_column(String(15))
    place_of_supply: Mapped[str | None] = mapped_column(String(2))  # GST state code
    supply_type: Mapped[str] = mapped_column(String(10), default="goods")  # goods | services
    taxable_value: Mapped[Decimal] = mapped_column(Money, default=0)
    cgst: Mapped[Decimal] = mapped_column(Money, default=0)
    sgst: Mapped[Decimal] = mapped_column(Money, default=0)
    igst: Mapped[Decimal] = mapped_column(Money, default=0)
    total: Mapped[Decimal] = mapped_column(Money, default=0)
    irn: Mapped[str | None] = mapped_column(String(64))
    eway_bill_no: Mapped[str | None] = mapped_column(String(12))
    due_date: Mapped[date | None] = mapped_column(Date)
    amount_received: Mapped[Decimal] = mapped_column(Money, default=0)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    entered_on: Mapped[date | None] = mapped_column(Date)


class PurchaseInvoice(_Data, Base):
    __tablename__ = "purchase_invoices"
    invoice_no: Mapped[str] = mapped_column(String(60))
    invoice_date: Mapped[date] = mapped_column(Date)
    booking_date: Mapped[date | None] = mapped_column(Date)
    vendor_code: Mapped[str | None] = mapped_column(String(60))
    vendor_name: Mapped[str] = mapped_column(String(200))
    vendor_gstin: Mapped[str | None] = mapped_column(String(15))
    # Drives TDS section and blocked-credit checks. See statute.TDS_NATURES.
    nature: Mapped[str] = mapped_column(String(30), default="goods")
    taxable_value: Mapped[Decimal] = mapped_column(Money, default=0)
    cgst: Mapped[Decimal] = mapped_column(Money, default=0)
    sgst: Mapped[Decimal] = mapped_column(Money, default=0)
    igst: Mapped[Decimal] = mapped_column(Money, default=0)
    total: Mapped[Decimal] = mapped_column(Money, default=0)
    itc_claimed: Mapped[Decimal] = mapped_column(Money, default=0)
    tds_deducted: Mapped[Decimal] = mapped_column(Money, default=0)
    po_no: Mapped[str | None] = mapped_column(String(60))
    po_amount: Mapped[Decimal | None] = mapped_column(Money)
    grn_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    paid_date: Mapped[date | None] = mapped_column(Date)
    amount_paid: Mapped[Decimal] = mapped_column(Money, default=0)


class BankTxn(_Data, Base):
    __tablename__ = "bank_transactions"
    account: Mapped[str] = mapped_column(String(60), default="")
    txn_date: Mapped[date] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(String(400))
    reference: Mapped[str | None] = mapped_column(String(100))
    counterparty: Mapped[str | None] = mapped_column(String(200))
    mode: Mapped[str | None] = mapped_column(String(20))  # neft, rtgs, cheque, upi, cash, ...
    withdrawal: Mapped[Decimal] = mapped_column(Money, default=0)
    deposit: Mapped[Decimal] = mapped_column(Money, default=0)


class StockMove(_Data, Base):
    """Quantity is always positive; movement_type gives the direction."""
    __tablename__ = "stock_movements"
    move_date: Mapped[date] = mapped_column(Date)
    item_code: Mapped[str] = mapped_column(String(60))
    item_name: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str] = mapped_column(String(60), default="MAIN")
    movement_type: Mapped[str] = mapped_column(String(20))  # opening | receipt | issue | adjust_in | adjust_out
    quantity: Mapped[Decimal] = mapped_column(Qty, default=0)
    rate: Mapped[Decimal] = mapped_column(Money, default=0)
    reference: Mapped[str | None] = mapped_column(String(60))


class Employee(_Data, Base):
    __tablename__ = "employees"
    emp_code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(200))
    pan: Mapped[str | None] = mapped_column(String(10))
    bank_account: Mapped[str | None] = mapped_column(String(40))
    address: Mapped[str | None] = mapped_column(String(400))
    date_joined: Mapped[date | None] = mapped_column(Date)
    date_left: Mapped[date | None] = mapped_column(Date)


class PayrollLine(_Data, Base):
    __tablename__ = "payroll"
    emp_code: Mapped[str] = mapped_column(String(40))
    pay_month: Mapped[date] = mapped_column(Date)  # first day of the wage month
    basic: Mapped[Decimal] = mapped_column(Money, default=0)  # basic + DA (PF wages)
    gross: Mapped[Decimal] = mapped_column(Money, default=0)
    pf_employee: Mapped[Decimal] = mapped_column(Money, default=0)
    esi_employee: Mapped[Decimal] = mapped_column(Money, default=0)
    other_deductions: Mapped[Decimal] = mapped_column(Money, default=0)  # PT, TDS, advances
    net_pay: Mapped[Decimal] = mapped_column(Money, default=0)


class Gstr2bLine(_Data, Base):
    __tablename__ = "gstr2b"
    supplier_gstin: Mapped[str] = mapped_column(String(15))
    supplier_name: Mapped[str | None] = mapped_column(String(200))
    invoice_no: Mapped[str] = mapped_column(String(60))
    invoice_date: Mapped[date | None] = mapped_column(Date)
    taxable_value: Mapped[Decimal] = mapped_column(Money, default=0)
    cgst: Mapped[Decimal] = mapped_column(Money, default=0)
    sgst: Mapped[Decimal] = mapped_column(Money, default=0)
    igst: Mapped[Decimal] = mapped_column(Money, default=0)
    itc_available: Mapped[bool] = mapped_column(Boolean, default=True)
    return_period: Mapped[str | None] = mapped_column(String(7))  # MM-YYYY


# ───────────────────────── 3. Audit ─────────────────────────

class RuleSetting(Base):
    """Per-engagement override of a rule's on/off switch and parameters."""
    __tablename__ = "rule_settings"
    __table_args__ = (UniqueConstraint("engagement_id", "rule_code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(ForeignKey("engagements.id"), index=True)
    rule_code: Mapped[str] = mapped_column(String(20))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    params: Mapped[dict] = mapped_column(JSON, default=dict)


class AuditRun(Base):
    __tablename__ = "audit_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(ForeignKey("engagements.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    run_by: Mapped[str] = mapped_column(String(200), default="")
    # {"new":n,"updated":n,"cleared":n,"rules":[{code,status,hits,ms,error}],"risk":{...}}
    summary: Mapped[dict] = mapped_column(JSON, default=dict)


class Finding(Base):
    """One exception. Identity is (engagement, rule, fingerprint), so a re-run
    updates the same row and the reviewer's status and notes survive."""
    __tablename__ = "findings"
    __table_args__ = (
        UniqueConstraint("engagement_id", "rule_code", "fingerprint"),
        Index("ix_findings_eng_status", "engagement_id", "status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(ForeignKey("engagements.id"))
    rule_code: Mapped[str] = mapped_column(String(20))
    area: Mapped[str] = mapped_column(String(30))
    fingerprint: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(300))
    detail: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(10))  # critical | high | medium | low
    impact: Mapped[Decimal] = mapped_column(Money, default=0)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    law: Mapped[str] = mapped_column(String(300), default="")
    is_fraud_indicator: Mapped[bool] = mapped_column(Boolean, default=False)
    # open | queried | confirmed | dismissed | resolved | cleared
    status: Mapped[str] = mapped_column(String(12), default="open")
    first_run_id: Mapped[int] = mapped_column(ForeignKey("audit_runs.id"))
    last_run_id: Mapped[int] = mapped_column(ForeignKey("audit_runs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
    notes: Mapped[list["FindingNote"]] = relationship(cascade="all, delete-orphan", order_by="FindingNote.id")
    actions: Mapped[list["Action"]] = relationship(cascade="all, delete-orphan", order_by="Action.id")


class FindingNote(Base):
    """Review trail: comments, queries to management, their replies, status changes."""
    __tablename__ = "finding_notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"), index=True)
    kind: Mapped[str] = mapped_column(String(12))  # comment | query | response | status
    body: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Action(Base):
    """Remediation step agreed with management."""
    __tablename__ = "actions"
    id: Mapped[int] = mapped_column(primary_key=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"), index=True)
    description: Mapped[str] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(200), default="")
    due_date: Mapped[date | None] = mapped_column(Date)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_at: Mapped[datetime | None] = mapped_column(DateTime)
