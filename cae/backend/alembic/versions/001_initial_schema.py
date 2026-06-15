"""Initial schema — all tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "tenants",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("plan", sa.String(50), nullable=False, server_default="starter"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "companies",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("gstin", sa.String(15), nullable=True),
        sa.Column("pan", sa.String(10), nullable=True),
        sa.Column("cin", sa.String(21), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("industry_sector", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("annual_turnover", sa.Numeric(15, 2), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "gl_accounts",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("account_code", sa.String(20), nullable=False),
        sa.Column("account_name", sa.String(200), nullable=False),
        sa.Column("account_type", sa.String(50), nullable=False),
        sa.Column("parent_code", sa.String(20), nullable=True),
        sa.Column("is_suspense", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("company_id", "account_code", name="uq_gl_company_code"),
    )

    op.create_table(
        "cost_centers",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("parent_code", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "customers",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("gstin", sa.String(15), nullable=True),
        sa.Column("pan", sa.String(10), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("credit_limit", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("outstanding_balance", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_related_party", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("last_transaction_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "code", name="uq_customer_company_code"),
    )

    op.create_table(
        "vendors",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("gstin", sa.String(15), nullable=True),
        sa.Column("pan", sa.String(10), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("bank_account_no", sa.String(50), nullable=True),
        sa.Column("ifsc_code", sa.String(11), nullable=True),
        sa.Column("is_approved", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_related_party", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_msme", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_bank_change_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "code", name="uq_vendor_company_code"),
    )

    op.create_table(
        "employees",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("emp_no", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("designation", sa.String(100), nullable=True),
        sa.Column("date_of_joining", sa.Date, nullable=True),
        sa.Column("date_of_leaving", sa.Date, nullable=True),
        sa.Column("bank_account_no", sa.String(50), nullable=True),
        sa.Column("pf_uan", sa.String(20), nullable=True),
        sa.Column("esi_ip", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "emp_no", name="uq_employee_company_empno"),
    )

    op.create_table(
        "sales_invoices",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("invoice_no", sa.String(100), nullable=False),
        sa.Column("invoice_date", sa.Date, nullable=False),
        sa.Column("customer_id", sa.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("customer_name", sa.String(300), nullable=True),
        sa.Column("gstin_customer", sa.String(15), nullable=True),
        sa.Column("hsn_code", sa.String(10), nullable=True),
        sa.Column("taxable_value", sa.Numeric(15, 2), nullable=False),
        sa.Column("cgst", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("sgst", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("igst", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("total_value", sa.Numeric(15, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("discount_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("cost_of_goods", sa.Numeric(15, 2), nullable=True),
        sa.Column("gross_margin_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("e_way_bill_no", sa.String(50), nullable=True),
        sa.Column("e_invoice_irn", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_cancelled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("credit_limit_approved", sa.Numeric(15, 2), nullable=True),
        sa.Column("payment_terms", sa.Integer, nullable=True),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("payment_received_date", sa.Date, nullable=True),
        sa.Column("salesperson", sa.String(100), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("source_system", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("posting_date", sa.Date, nullable=True),
        sa.Column("is_backdated", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_sales_inv_company_date", "sales_invoices", ["company_id", "invoice_date"])

    op.create_table(
        "purchase_invoices",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("vendor_id", sa.UUID(as_uuid=True), sa.ForeignKey("vendors.id"), nullable=True),
        sa.Column("vendor_name", sa.String(300), nullable=True),
        sa.Column("invoice_no", sa.String(100), nullable=False),
        sa.Column("invoice_date", sa.Date, nullable=False),
        sa.Column("po_no", sa.String(100), nullable=True),
        sa.Column("grn_no", sa.String(100), nullable=True),
        sa.Column("taxable_value", sa.Numeric(15, 2), nullable=False),
        sa.Column("cgst", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("sgst", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("igst", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("total_value", sa.Numeric(15, 2), nullable=False),
        sa.Column("itc_eligible", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("payment_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("payment_date", sa.Date, nullable=True),
        sa.Column("is_advance", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_emergency_purchase", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("source_system", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_purchase_inv_company_date", "purchase_invoices", ["company_id", "invoice_date"])

    op.create_table(
        "journal_entries",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("je_no", sa.String(100), nullable=False),
        sa.Column("je_date", sa.Date, nullable=False),
        sa.Column("period_month", sa.Integer, nullable=False),
        sa.Column("period_year", sa.Integer, nullable=False),
        sa.Column("je_type", sa.String(20), nullable=False),
        sa.Column("narration", sa.Text, nullable=True),
        sa.Column("total_debit", sa.Numeric(15, 2), nullable=False),
        sa.Column("total_credit", sa.Numeric(15, 2), nullable=False),
        sa.Column("prepared_by", sa.String(100), nullable=True),
        sa.Column("approved_by", sa.String(100), nullable=True),
        sa.Column("is_reversal", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("original_je_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("posting_time", sa.Time, nullable=True),
        sa.Column("source_system", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("is_suspicious", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_je_company_date", "journal_entries", ["company_id", "je_date"])

    op.create_table(
        "journal_entry_lines",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("je_id", sa.UUID(as_uuid=True), sa.ForeignKey("journal_entries.id"), nullable=False),
        sa.Column("gl_account_id", sa.UUID(as_uuid=True), sa.ForeignKey("gl_accounts.id"), nullable=True),
        sa.Column("gl_account_code", sa.String(20), nullable=True),
        sa.Column("cost_center_id", sa.UUID(as_uuid=True), sa.ForeignKey("cost_centers.id"), nullable=True),
        sa.Column("debit", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("credit", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("narration", sa.String(500), nullable=True),
    )

    op.create_table(
        "bank_transactions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("bank_account", sa.String(50), nullable=False),
        sa.Column("txn_date", sa.Date, nullable=False),
        sa.Column("value_date", sa.Date, nullable=True),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("txn_type", sa.String(10), nullable=False),
        sa.Column("reference_no", sa.String(100), nullable=True),
        sa.Column("narration", sa.Text, nullable=True),
        sa.Column("party_name", sa.String(300), nullable=True),
        sa.Column("channel", sa.String(20), nullable=True),
        sa.Column("is_reconciled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("movement_date", sa.Date, nullable=False),
        sa.Column("material_code", sa.String(50), nullable=False),
        sa.Column("material_name", sa.String(200), nullable=False),
        sa.Column("warehouse", sa.String(100), nullable=True),
        sa.Column("movement_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(15, 3), nullable=False),
        sa.Column("unit", sa.String(20), nullable=True),
        sa.Column("uom_rate", sa.Numeric(15, 4), nullable=True),
        sa.Column("value", sa.Numeric(15, 2), nullable=True),
        sa.Column("reference_doc", sa.String(100), nullable=True),
        sa.Column("approved_by", sa.String(100), nullable=True),
        sa.Column("is_suspicious", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "payroll_records",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("employee_id", sa.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("emp_no", sa.String(50), nullable=False),
        sa.Column("emp_name", sa.String(200), nullable=False),
        sa.Column("period_month", sa.Integer, nullable=False),
        sa.Column("period_year", sa.Integer, nullable=False),
        sa.Column("basic_pay", sa.Numeric(12, 2), nullable=False),
        sa.Column("allowances", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("gross_pay", sa.Numeric(12, 2), nullable=False),
        sa.Column("deductions", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("net_pay", sa.Numeric(12, 2), nullable=False),
        sa.Column("pf_employer", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("esi_employer", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("tds", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("bank_account", sa.String(50), nullable=True),
        sa.Column("payment_date", sa.Date, nullable=True),
        sa.Column("is_active_employee", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "audit_rules",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rule_code", sa.String(20), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("business_area", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("risk_category", sa.String(50), nullable=False),
        sa.Column("materiality_threshold", sa.Numeric(15, 2), nullable=True),
        sa.Column("likelihood_default", sa.Integer, nullable=False, server_default="3"),
        sa.Column("ifc_mapping", sa.String(200), nullable=True),
        sa.Column("owner_role", sa.String(50), nullable=True),
        sa.Column("frequency", sa.String(20), nullable=False, server_default="daily"),
        sa.Column("recommendation_template", sa.Text, nullable=True),
        sa.Column("escalation_days", sa.Integer, nullable=False, server_default="7"),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_audit_rules_area", "audit_rules", ["business_area", "is_enabled"])

    op.create_table(
        "rule_executions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rule_id", sa.UUID(as_uuid=True), sa.ForeignKey("audit_rules.id"), nullable=False),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exceptions_found", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("error_message", sa.Text, nullable=True),
    )

    op.create_table(
        "audit_exceptions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("rule_id", sa.UUID(as_uuid=True), sa.ForeignKey("audit_rules.id"), nullable=True),
        sa.Column("rule_code", sa.String(20), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("business_area", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("risk_category", sa.String(50), nullable=False),
        sa.Column("financial_impact", sa.Numeric(15, 2), nullable=True),
        sa.Column("likelihood_score", sa.Integer, nullable=True),
        sa.Column("impact_score", sa.Integer, nullable=True),
        sa.Column("composite_risk_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("evidence_json", sa.JSON, nullable=True),
        sa.Column("ai_explanation", sa.Text, nullable=True),
        sa.Column("ai_query_suggestion", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("assigned_to", sa.String(200), nullable=True),
        sa.Column("txn_references", sa.JSON, nullable=True),
        sa.Column("is_false_positive", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("false_positive_reason", sa.Text, nullable=True),
        sa.Column("acknowledged_by", sa.String(200), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_exceptions_company_status", "audit_exceptions", ["company_id", "status"])
    op.create_index("idx_exceptions_severity", "audit_exceptions", ["company_id", "severity"])

    op.create_table(
        "management_queries",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("exception_id", sa.UUID(as_uuid=True), sa.ForeignKey("audit_exceptions.id"), nullable=False),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("query_no", sa.String(30), unique=True, nullable=False),
        sa.Column("process_area", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("evidence_summary", sa.Text, nullable=True),
        sa.Column("suggested_question", sa.Text, nullable=False),
        sa.Column("assigned_to_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_to_name", sa.String(200), nullable=True),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("auditor_comment", sa.Text, nullable=True),
        sa.Column("raised_by_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("raised_by_name", sa.String(200), nullable=False),
        sa.Column("raised_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_mq_company_status", "management_queries", ["company_id", "status"])

    op.create_table(
        "query_responses",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("query_id", sa.UUID(as_uuid=True), sa.ForeignKey("management_queries.id"), nullable=False),
        sa.Column("response_text", sa.Text, nullable=False),
        sa.Column("responded_by_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("responded_by_name", sa.String(200), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("attachment_url", sa.String(500), nullable=True),
        sa.Column("auditor_review_status", sa.String(20), nullable=True),
        sa.Column("auditor_comment", sa.Text, nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "remediation_actions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("exception_id", sa.UUID(as_uuid=True), sa.ForeignKey("audit_exceptions.id"), nullable=True),
        sa.Column("control_gap_description", sa.Text, nullable=False),
        sa.Column("root_cause", sa.Text, nullable=True),
        sa.Column("action_plan", sa.Text, nullable=False),
        sa.Column("responsible_user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("responsible_name", sa.String(200), nullable=False),
        sa.Column("target_date", sa.Date, nullable=False),
        sa.Column("actual_closure_date", sa.Date, nullable=True),
        sa.Column("evidence_url", sa.String(500), nullable=True),
        sa.Column("retest_outcome", sa.String(30), nullable=True),
        sa.Column("residual_risk_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "risk_scores",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("score_date", sa.Date, nullable=False),
        sa.Column("entity_level", sa.String(30), nullable=False),
        sa.Column("entity_name", sa.String(200), nullable=False),
        sa.Column("likelihood", sa.Numeric(4, 2), nullable=False),
        sa.Column("impact", sa.Numeric(4, 2), nullable=False),
        sa.Column("materiality", sa.Numeric(4, 2), nullable=False),
        sa.Column("frequency", sa.Numeric(4, 2), nullable=False),
        sa.Column("control_weakness", sa.Numeric(4, 2), nullable=False),
        sa.Column("composite_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("risk_band", sa.String(20), nullable=False),
        sa.Column("exception_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "fraud_indicators",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("analysis_date", sa.Date, nullable=False),
        sa.Column("indicator_type", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("affected_transactions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("financial_exposure", sa.Numeric(15, 2), nullable=True),
        sa.Column("details_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "gst_reconciliation",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("gstr1_turnover", sa.Numeric(15, 2), nullable=True),
        sa.Column("books_turnover", sa.Numeric(15, 2), nullable=True),
        sa.Column("gstr3b_itc", sa.Numeric(15, 2), nullable=True),
        sa.Column("books_itc", sa.Numeric(15, 2), nullable=True),
        sa.Column("gstr2b_itc", sa.Numeric(15, 2), nullable=True),
        sa.Column("variance_turnover", sa.Numeric(15, 2), nullable=True),
        sa.Column("variance_itc", sa.Numeric(15, 2), nullable=True),
        sa.Column("risk_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("risk_category", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "period", name="uq_gst_recon_period"),
    )

    op.create_table(
        "working_capital_metrics",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("metric_date", sa.Date, nullable=False),
        sa.Column("receivables_total", sa.Numeric(15, 2), nullable=True),
        sa.Column("receivables_overdue", sa.Numeric(15, 2), nullable=True),
        sa.Column("receivables_0_30", sa.Numeric(15, 2), nullable=True),
        sa.Column("receivables_31_60", sa.Numeric(15, 2), nullable=True),
        sa.Column("receivables_61_90", sa.Numeric(15, 2), nullable=True),
        sa.Column("receivables_above_90", sa.Numeric(15, 2), nullable=True),
        sa.Column("payables_total", sa.Numeric(15, 2), nullable=True),
        sa.Column("payables_overdue", sa.Numeric(15, 2), nullable=True),
        sa.Column("inventory_value", sa.Numeric(15, 2), nullable=True),
        sa.Column("slow_moving_inventory", sa.Numeric(15, 2), nullable=True),
        sa.Column("wc_stress_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("dso", sa.Numeric(6, 2), nullable=True),
        sa.Column("dpo", sa.Numeric(6, 2), nullable=True),
        sa.Column("dio", sa.Numeric(6, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_processed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("exceptions_raised", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("triggered_by", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("sync_job_id", sa.UUID(as_uuid=True), sa.ForeignKey("sync_jobs.id"), nullable=True),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_size", sa.BigInteger, nullable=True),
        sa.Column("rows_parsed", sa.Integer, nullable=True),
        sa.Column("rows_imported", sa.Integer, nullable=True),
        sa.Column("parse_errors", sa.JSON, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="uploaded"),
        sa.Column("uploaded_by", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    tables = [
        "uploaded_files", "sync_jobs", "working_capital_metrics", "gst_reconciliation",
        "fraud_indicators", "risk_scores", "remediation_actions", "query_responses",
        "management_queries", "audit_exceptions", "rule_executions", "audit_rules",
        "payroll_records", "inventory_movements", "bank_transactions",
        "journal_entry_lines", "journal_entries", "purchase_invoices", "sales_invoices",
        "employees", "vendors", "customers", "cost_centers", "gl_accounts",
        "users", "companies", "tenants",
    ]
    for t in tables:
        op.drop_table(t)
