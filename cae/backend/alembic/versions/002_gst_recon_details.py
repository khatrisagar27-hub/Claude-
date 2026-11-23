"""Invoice-level GST reconciliation detail

Revision ID: 002
Revises: 001
Create Date: 2026-10-30 00:00:00.000000
"""
from alembic import op
from sqlalchemy import text

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 001 builds the schema from the ORM models, so a fresh database already has the column.
    op.get_bind().execute(text("ALTER TABLE gst_reconciliation ADD COLUMN IF NOT EXISTS details_json JSON"))


def downgrade() -> None:
    op.get_bind().execute(text("ALTER TABLE gst_reconciliation DROP COLUMN IF EXISTS details_json"))
