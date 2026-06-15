"""
Master data models — reference entities used across transactional data.

Models:
  Customer       — sales counterparties
  Vendor         — purchase counterparties
  Employee       — payroll and expense recipients
  GLAccount      — chart of accounts
  CostCenter     — organisational cost tracking units
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

import sqlalchemy as sa
from sqlalchemy import String, Boolean, Numeric, Date, Text, Integer, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Customer(Base):
    """Sales counterparty master."""
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("company_id", "customer_code", name="uq_customer_company_code"),
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
    customer_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True, index=True)
    pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, server_default="India")
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    credit_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    customer_group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]
    sales_invoices: Mapped[List["SalesInvoice"]] = relationship(  # type: ignore[name-defined]
        "SalesInvoice", back_populates="customer", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} code={self.customer_code!r} name={self.name!r}>"


class Vendor(Base):
    """Purchase counterparty master."""
    __tablename__ = "vendors"
    __table_args__ = (
        UniqueConstraint("company_id", "vendor_code", name="uq_vendor_company_code"),
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
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True, index=True)
    pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    msme_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Micro / Small / Medium / None"
    )
    msme_registration_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, server_default="India")
    payment_terms_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    bank_ifsc: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
    vendor_group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_related_party: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]
    purchase_invoices: Mapped[List["PurchaseInvoice"]] = relationship(  # type: ignore[name-defined]
        "PurchaseInvoice", back_populates="vendor", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Vendor id={self.id} code={self.vendor_code!r} name={self.name!r}>"


class Employee(Base):
    """Employee master for payroll and expense processing."""
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("company_id", "employee_code", name="uq_employee_company_code"),
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
    employee_code: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_of_joining: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_of_leaving: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Permanent / Contract / Consultant"
    )
    pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    aadhar_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    pf_account_number: Mapped[Optional[str]] = mapped_column(String(22), nullable=True)
    uan: Mapped[Optional[str]] = mapped_column(String(12), nullable=True, comment="Universal Account Number")
    esic_number: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    bank_ifsc: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
    cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("cost_centers.id", ondelete="SET NULL"),
        nullable=True,
    )
    basic_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    gross_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter", lazy="select")
    payroll_records: Mapped[List["PayrollRecord"]] = relationship(  # type: ignore[name-defined]
        "PayrollRecord", back_populates="employee", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Employee id={self.id} code={self.employee_code!r} name={self.full_name!r}>"


class GLAccount(Base):
    """General Ledger chart of accounts."""
    __tablename__ = "gl_accounts"
    __table_args__ = (
        UniqueConstraint("company_id", "account_code", name="uq_glaccount_company_code"),
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
    account_code: Mapped[str] = mapped_column(String(20), nullable=False)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Asset / Liability / Equity / Revenue / Expense"
    )
    account_subtype: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    parent_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("gl_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_control_account: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    is_bank_account: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    is_cash_account: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.false())
    normal_balance: Mapped[str] = mapped_column(
        String(6), nullable=False, server_default="debit",
        comment="debit / credit"
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Self-referential relationship
    parent: Mapped[Optional["GLAccount"]] = relationship(
        "GLAccount", remote_side="GLAccount.id", lazy="select"
    )
    children: Mapped[List["GLAccount"]] = relationship(
        "GLAccount", back_populates="parent", lazy="select",
        foreign_keys="[GLAccount.parent_account_id]",
        overlaps="parent",
    )
    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<GLAccount id={self.id} code={self.account_code!r} name={self.account_name!r}>"


class CostCenter(Base):
    """Organisational cost tracking unit."""
    __tablename__ = "cost_centers"
    __table_args__ = (
        UniqueConstraint("company_id", "cost_center_code", name="uq_costcenter_company_code"),
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
    cost_center_code: Mapped[str] = mapped_column(String(50), nullable=False)
    cost_center_name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_cost_center_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("cost_centers.id", ondelete="SET NULL"),
        nullable=True,
    )
    manager_employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=True,
        comment="FK to employees.id — set programmatically to avoid circular FK",
    )
    budget_annual: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true())
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Self-referential relationship
    parent: Mapped[Optional["CostCenter"]] = relationship(
        "CostCenter", remote_side="CostCenter.id", lazy="select"
    )
    children: Mapped[List["CostCenter"]] = relationship(
        "CostCenter", back_populates="parent", lazy="select",
        foreign_keys="[CostCenter.parent_cost_center_id]",
        overlaps="parent",
    )
    company: Mapped["Company"] = relationship("Company", lazy="select")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<CostCenter id={self.id} code={self.cost_center_code!r} "
            f"name={self.cost_center_name!r}>"
        )
