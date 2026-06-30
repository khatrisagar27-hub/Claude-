"""
Lightweight object factories for tests.

The transaction models carry many NOT NULL columns that the engines never look
at.  These helpers fill those with sane defaults so each test only has to specify
the handful of fields relevant to the rule under test.
"""
from __future__ import annotations

import uuid
from datetime import date

from app.models.audit import AuditException
from app.models.transaction import (
    InventoryMovement,
    JournalEntry,
    PurchaseInvoice,
    SalesInvoice,
)
from app.models.user import User
from app.utils.security import get_password_hash

TENANT_ID = uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")

# Fixed company ids shared by helpers so tests can scope queries to one tenant.
# NOTE: these deliberately contain hex letters. SQLite gives its UUID/CHAR
# columns NUMERIC affinity, so an all-digit UUID string (e.g. "1111...") would be
# silently coerced to a float on storage. Real ids (uuid4/gen_random_uuid) always
# contain letters, so this only matters for hand-picked test fixtures.
COMPANY_ID = uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
OTHER_COMPANY_ID = uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


def make_sales_invoice(company_id: uuid.UUID = COMPANY_ID, **overrides) -> SalesInvoice:
    defaults = dict(
        id=uuid.uuid4(),
        company_id=company_id,
        invoice_number=f"INV-{uuid.uuid4().hex[:8]}",
        invoice_date=date(2024, 3, 15),
        due_date=date(2024, 4, 15),
        gross_amount=1000,
        discount_amount=0,
        taxable_amount=1000,
        cgst_amount=0,
        sgst_amount=0,
        igst_amount=0,
        cess_amount=0,
        tds_amount=0,
        total_amount=1000,
        paid_amount=0,
        outstanding_amount=0,
        status="confirmed",
    )
    defaults.update(overrides)
    return SalesInvoice(**defaults)


def make_purchase_invoice(company_id: uuid.UUID = COMPANY_ID, **overrides) -> PurchaseInvoice:
    defaults = dict(
        id=uuid.uuid4(),
        company_id=company_id,
        vendor_id=uuid.uuid4(),
        invoice_number=f"BILL-{uuid.uuid4().hex[:8]}",
        invoice_date=date(2024, 3, 15),
        due_date=date(2024, 4, 15),
        gross_amount=1000,
        discount_amount=0,
        taxable_amount=1000,
        cgst_amount=0,
        sgst_amount=0,
        igst_amount=0,
        cess_amount=0,
        tds_amount=0,
        total_amount=1000,
        paid_amount=0,
        outstanding_amount=0,
        itc_eligible=True,
        status="approved",
    )
    defaults.update(overrides)
    return PurchaseInvoice(**defaults)


def make_journal_entry(company_id: uuid.UUID = COMPANY_ID, **overrides) -> JournalEntry:
    defaults = dict(
        id=uuid.uuid4(),
        company_id=company_id,
        voucher_number=f"JV-{uuid.uuid4().hex[:8]}",
        entry_date=date(2024, 3, 15),
        voucher_type="journal",
        total_debit=1000,
        total_credit=1000,
        status="posted",
        posted_by_user_id=uuid.uuid4(),
    )
    defaults.update(overrides)
    return JournalEntry(**defaults)


def make_inventory_movement(company_id: uuid.UUID = COMPANY_ID, **overrides) -> InventoryMovement:
    defaults = dict(
        id=uuid.uuid4(),
        company_id=company_id,
        movement_date=date(2024, 3, 15),
        movement_type="goods_receipt",
        item_code=f"ITEM-{uuid.uuid4().hex[:6]}",
        unit_of_measure="NOS",
        quantity=10,
        unit_cost=100,
        total_value=1000,
    )
    defaults.update(overrides)
    return InventoryMovement(**defaults)


def make_user(company_id: uuid.UUID = COMPANY_ID, password: str = "S3cret-pass", **overrides) -> User:
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        company_id=company_id,
        email=f"user-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash(password),
        full_name="Test User",
        role="auditor",
        is_active=True,
    )
    defaults.update(overrides)
    return User(**defaults)


def make_audit_exception(company_id: uuid.UUID = COMPANY_ID, **overrides) -> AuditException:
    defaults = dict(
        id=uuid.uuid4(),
        company_id=company_id,
        title="Test exception",
        category="revenue",
        severity="high",
        financial_impact=100000,
        status="open",
        detected_on=date(2024, 3, 15),
    )
    defaults.update(overrides)
    return AuditException(**defaults)
