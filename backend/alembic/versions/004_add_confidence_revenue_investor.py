"""Add confidence_score to funding_rounds, investor_type/website to investors,
revenue fields to companies

Revision ID: 004
Revises: 003
Create Date: 2026-03-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: str = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("funding_rounds", sa.Column("confidence_score", sa.Float(), nullable=True))
    op.add_column("investors", sa.Column("investor_type", sa.Text(), nullable=True))
    op.add_column("investors", sa.Column("website", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("revenue_usd", sa.Numeric(), nullable=True))
    op.add_column("companies", sa.Column("revenue_as_of_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "revenue_as_of_date")
    op.drop_column("companies", "revenue_usd")
    op.drop_column("investors", "website")
    op.drop_column("investors", "investor_type")
    op.drop_column("funding_rounds", "confidence_score")
