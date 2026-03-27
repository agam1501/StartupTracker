"""Add status column to companies table.

Revision ID: 007
Revises: 006
"""

import sqlalchemy as sa

from alembic import op

revision = "007"
down_revision = "006"


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("status", sa.Text(), server_default="active", nullable=False),
    )
    op.create_index("ix_companies_status", "companies", ["status"])


def downgrade() -> None:
    op.drop_index("ix_companies_status", "companies")
    op.drop_column("companies", "status")
