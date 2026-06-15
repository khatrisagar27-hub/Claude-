"""
Transaction models — financial document records ingested from ERP systems.

Models:
  SalesInvoice        — AR invoices / sales orders
  PurchaseInvoice     — AP invoices / purchase orders
  JournalEntry        — GL journal entry headers
  JournalEntryLine    — individual debit/credit lines
  BankTransaction     — bank statement lines
  InventoryMovement   — stock in/out records
  PayrollRecord       — monthly payroll disbursement records
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

import sqlalchemy as sa
from sqlalchemy import (
    String, Boolean, Numeric, Date, DateTime, Text, Integer,
    UniqueConstraint, ForeignKey, text, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class SalesInvoice(Base):
    """Accounts Receivable invoice / sales document."""
    __tablename__ = "sales_invoices"
    __table_args__ = (
        UniqueConstraint("company_id", "invoice_number", name="uq_salesinvoice_company_number"),
        Index("ix_salesinvoice_company_date", "company_id", "invoice_date"),
        Index("ix_salesinvoice_customer", "customer_id"),
        Index("ix_salesinvoice_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    po_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="Customer purchase order reference")
    sales_order_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False, server_default="1.000000")

    # Amounts
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    cgst_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    sgst_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    igst_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    cess_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    tds_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    outstanding_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # GST
    place_of_supply: Mapped[Optional[str]] = mapped_column(String(2), nullable=True, comment="2-digit state code")
    reverse_charge: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    e_invoice_irn: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="IRP Invoice Reference Number")
    e_way_bill_number: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)

    # Status and classification
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="draft",
        comment="draft / confirmed / part_paid / paid / cancelled / overdue"
    )
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("cost_centers.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ERP metadata
    erp_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="tally / sap / zoho / etc.")
    erp_internal_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]
    customer: Mapped[Optional["Customer"]] = relationship(  # type: ignore[name-defined]
        "Customer", back_populates="sales_invoices", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<SalesInvoice id={self.id} number={self.invoice_number!r} total={self.total_amount}>"


class PurchaseInvoice(Base):
    """Accounts Payable invoice / purchase document."""
    __tablename__ = "purchase_invoices"
    __table_args__ = (
        UniqueConstraint("company_id", "invoice_number", name="uq_purchaseinvoice_company_number"),
        Index("ix_purchaseinvoice_company_date", "company_id", "invoice_date"),
        Index("ix_purchaseinvoice_vendor", "vendor_id"),
        Index("ix_purchaseinvoice_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vendors.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, comment="Vendor's invoice number")
    our_po_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="Our purchase order")
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    receipt_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="Goods/services receipt date")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False, server_default="1.000000")

    # Amounts
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    cgst_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    sgst_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    igst_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    cess_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    tds_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    tds_section: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="194C / 194J / 194Q / etc.")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    outstanding_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # GST
    vendor_gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    place_of_supply: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    reverse_charge: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    itc_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true(), comment="Input Tax Credit eligibility")
    e_way_bill_number: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="pending",
        comment="pending / approved / part_paid / paid / disputed / cancelled"
    )
    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True), nullable=True
    )
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("cost_centers.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ERP metadata
    erp_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    erp_internal_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]
    vendor: Mapped[Optional["Vendor"]] = relationship(  # type: ignore[name-defined]
        "Vendor", back_populates="purchase_invoices", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<PurchaseInvoice id={self.id} number={self.invoice_number!r} total={self.total_amount}>"


class JournalEntry(Base):
    """GL Journal entry header — balanced debit/credit voucher."""
    __tablename__ = "journal_entries"
    __table_args__ = (
        UniqueConstraint("company_id", "voucher_number", name="uq_je_company_voucher"),
        Index("ix_je_company_date", "company_id", "entry_date"),
        Index("ix_je_status", "status"),
        Index("ix_je_voucher_type", "voucher_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    voucher_number: Mapped[str] = mapped_column(String(100), nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    voucher_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="payment / receipt / contra / journal / purchase / sales / debit_note / credit_note"
    )
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    narration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    total_debit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_credit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    is_posted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    is_reversed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    reversal_of_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("journal_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="draft",
        comment="draft / posted / reversed / cancelled"
    )
    posted_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True), nullable=True
    )
    posted_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    # ERP metadata
    erp_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    erp_internal_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]
    lines: Mapped[List["JournalEntryLine"]] = relationship(
        "JournalEntryLine", back_populates="journal_entry",
        cascade="all, delete-orphan", lazy="select"
    )
    reversal_of: Mapped[Optional["JournalEntry"]] = relationship(
        "JournalEntry", remote_side="JournalEntry.id", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<JournalEntry id={self.id} voucher={self.voucher_number!r} date={self.entry_date}>"


class JournalEntryLine(Base):
    """Individual debit or credit line within a journal entry."""
    __tablename__ = "journal_entry_lines"
    __table_args__ = (
        Index("ix_jeline_je_id", "journal_entry_id"),
        Index("ix_jeline_account", "account_id"),
        Index("ix_jeline_cost_center", "cost_center_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("gl_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    account_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="Denormalized for quick access")
    account_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("cost_centers.id", ondelete="SET NULL"),
        nullable=True,
    )
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    narration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Reference to source document
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="sales_invoice / purchase_invoice / bank_transaction / payroll"
    )
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True), nullable=True
    )

    # Relationships
    journal_entry: Mapped["JournalEntry"] = relationship(
        "JournalEntry", back_populates="lines", lazy="select"
    )
    account: Mapped[Optional["GLAccount"]] = relationship("GLAccount", lazy="select")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<JournalEntryLine id={self.id} line={self.line_number} "
            f"dr={self.debit_amount} cr={self.credit_amount}>"
        )


class BankTransaction(Base):
    """Bank statement line item — used for reconciliation."""
    __tablename__ = "bank_transactions"
    __table_args__ = (
        Index("ix_banktxn_company_date", "company_id", "transaction_date"),
        Index("ix_banktxn_account", "bank_account_id"),
        Index("ix_banktxn_reconciled", "is_reconciled"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bank_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("gl_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    transaction_type: Mapped[str] = mapped_column(
        String(10), nullable=False,
        comment="debit / credit"
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cheque_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    transaction_mode: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="NEFT / RTGS / IMPS / UPI / cheque / cash / ECS"
    )
    counterparty_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    counterparty_account: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    counterparty_ifsc: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
    utr_number: Mapped[Optional[str]] = mapped_column(String(22), nullable=True, comment="UTR for NEFT/RTGS")
    is_reconciled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    reconciled_with_je_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True), nullable=True
    )

    # ERP metadata
    erp_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<BankTransaction id={self.id} date={self.transaction_date} "
            f"type={self.transaction_type!r} amount={self.amount}>"
        )


class InventoryMovement(Base):
    """Stock movement record — goods receipts, issues, transfers, adjustments."""
    __tablename__ = "inventory_movements"
    __table_args__ = (
        Index("ix_invmov_company_date", "company_id", "movement_date"),
        Index("ix_invmov_item", "item_code"),
        Index("ix_invmov_type", "movement_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    movement_date: Mapped[date] = mapped_column(Date, nullable=False)
    movement_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="goods_receipt / goods_issue / transfer / adjustment / return / opening"
    )
    item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    item_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    item_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hsn_sac_code: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, server_default="NOS")
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    total_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    warehouse_from: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    warehouse_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reference_document_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="purchase_invoice / sales_invoice / production_order / manual"
    )
    reference_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True), nullable=True
    )
    reference_document_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    closing_stock_qty: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 3), nullable=True)
    closing_stock_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ERP metadata
    erp_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    erp_internal_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<InventoryMovement id={self.id} date={self.movement_date} "
            f"item={self.item_code!r} qty={self.quantity} type={self.movement_type!r}>"
        )


class PayrollRecord(Base):
    """Monthly payroll disbursement record per employee."""
    __tablename__ = "payroll_records"
    __table_args__ = (
        UniqueConstraint("company_id", "employee_id", "pay_period_year", "pay_period_month",
                         name="uq_payroll_employee_period"),
        Index("ix_payroll_company_period", "company_id", "pay_period_year", "pay_period_month"),
        Index("ix_payroll_employee", "employee_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pay_period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    pay_period_month: Mapped[int] = mapped_column(Integer, nullable=False, comment="1-12")
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Earnings
    basic_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    hra: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    special_allowance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    conveyance_allowance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    medical_allowance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    lta: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    performance_bonus: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    other_earnings: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    gross_earnings: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Deductions
    pf_employee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    pf_employer: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    esic_employee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    esic_employer: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    professional_tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    tds_income_tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    advance_deduction: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    other_deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0.00")
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Net
    net_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    days_worked: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    days_absent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    leaves_taken: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Payment
    payment_mode: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="bank_transfer / cheque / cash"
    )
    bank_utr: Mapped[Optional[str]] = mapped_column(String(22), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="processed",
        comment="draft / processed / paid / cancelled"
    )

    # ERP metadata
    erp_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]
    employee: Mapped["Employee"] = relationship(  # type: ignore[name-defined]
        "Employee", back_populates="payroll_records", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<PayrollRecord id={self.id} employee_id={self.employee_id} "
            f"period={self.pay_period_year}-{self.pay_period_month:02d} net={self.net_pay}>"
        )
