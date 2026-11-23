"""Audit engagements (Statutory / Internal) and engagement scoping of exceptions and jobs

Revision ID: 003
Revises: 002
Create Date: 2026-10-31 00:00:00.000000
"""
from alembic import op
from sqlalchemy import text

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 001 builds the schema from the ORM models, so a fresh database already has all of this.
    bind = op.get_bind()
    from app.database import Base
    import app.models  # noqa: F401
    Base.metadata.tables["audit_engagements"].create(bind=bind, checkfirst=True)
    for stmt in (
        "ALTER TABLE audit_exceptions ADD COLUMN IF NOT EXISTS engagement_id UUID "
        "REFERENCES audit_engagements(id) ON DELETE CASCADE",
        "CREATE INDEX IF NOT EXISTS ix_audit_exceptions_engagement_id ON audit_exceptions (engagement_id)",
        "ALTER TABLE sync_jobs ADD COLUMN IF NOT EXISTS engagement_id UUID "
        "REFERENCES audit_engagements(id) ON DELETE CASCADE",
        "CREATE INDEX IF NOT EXISTS ix_sync_jobs_engagement_id ON sync_jobs (engagement_id)",
        "ALTER TABLE sync_jobs ADD COLUMN IF NOT EXISTS result_json JSON",
        # Workflow columns the API never filled: give them defaults so creation cannot fail on them
        "ALTER TABLE management_queries ALTER COLUMN raised_by_name SET DEFAULT ''",
        "ALTER TABLE remediation_actions ALTER COLUMN responsible_name SET DEFAULT ''",
    ):
        bind.execute(text(stmt))


def downgrade() -> None:
    bind = op.get_bind()
    for stmt in (
        "ALTER TABLE sync_jobs DROP COLUMN IF EXISTS result_json",
        "ALTER TABLE sync_jobs DROP COLUMN IF EXISTS engagement_id",
        "ALTER TABLE audit_exceptions DROP COLUMN IF EXISTS engagement_id",
        "DROP TABLE IF EXISTS audit_engagements",
    ):
        bind.execute(text(stmt))
