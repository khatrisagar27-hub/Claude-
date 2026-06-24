"""
Import all ORM models so that Alembic's autogenerate and any module that does
``from app.models import *`` will have all table metadata available.
"""
from app.models.tenant import Tenant, Company
from app.models.user import User
from app.models.master import Customer, Vendor, Employee, GLAccount, CostCenter
from app.models.transaction import (
    SalesInvoice,
    PurchaseInvoice,
    JournalEntry,
    JournalEntryLine,
    BankTransaction,
    InventoryMovement,
    PayrollRecord,
)
from app.models.audit import AuditRule, RuleExecution, AuditException
from app.models.workflow import ManagementQuery, QueryResponse, RemediationAction
from app.models.risk import RiskScore, FraudIndicator, GSTReconciliation, WorkingCapitalMetric
from app.models.ingestion import SyncJob, UploadedFile

__all__ = [
    "Tenant",
    "Company",
    "User",
    "Customer",
    "Vendor",
    "Employee",
    "GLAccount",
    "CostCenter",
    "SalesInvoice",
    "PurchaseInvoice",
    "JournalEntry",
    "JournalEntryLine",
    "BankTransaction",
    "InventoryMovement",
    "PayrollRecord",
    "AuditRule",
    "RuleExecution",
    "AuditException",
    "ManagementQuery",
    "QueryResponse",
    "RemediationAction",
    "RiskScore",
    "FraudIndicator",
    "GSTReconciliation",
    "WorkingCapitalMetric",
    "SyncJob",
    "UploadedFile",
]
