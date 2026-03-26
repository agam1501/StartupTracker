"""Add sector column to companies table

Revision ID: 002
Revises: 001
Create Date: 2026-03-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: str = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("sector", sa.Text(), nullable=True))
    op.create_index("ix_companies_sector", "companies", ["sector"])


def downgrade() -> None:
    op.drop_index("ix_companies_sector", table_name="companies")
    op.drop_column("companies", "sector")
