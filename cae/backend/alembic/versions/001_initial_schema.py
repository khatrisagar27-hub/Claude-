"""Initial schema — auto-generated from ORM models

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
from sqlalchemy import text

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # gen_random_uuid() is core from PostgreSQL 13; older servers need pgcrypto for it.
    if int(bind.execute(text("SHOW server_version_num")).scalar()) < 130000:
        bind.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    from app.database import Base
    import app.models  # noqa: registers all ORM models with Base
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from app.database import Base
    import app.models  # noqa
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
