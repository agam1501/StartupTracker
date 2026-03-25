"""Initial schema with all core tables

Revision ID: 001
Revises:
Create Date: 2026-03-24
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_uuid_pk = dict(
    type_=UUID(as_uuid=True),
    primary_key=True,
    server_default=sa.text("gen_random_uuid()"),
)
_created_at = dict(
    type_=sa.DateTime(timezone=True),
    server_default=sa.text("now()"),
    nullable=False,
)


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", **_uuid_pk),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("created_at", **_created_at),
    )
    op.create_index(
        "ix_companies_normalized_name", "companies", ["normalized_name"]
    )

    op.create_table(
        "investors",
        sa.Column("id", **_uuid_pk),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
    )
    op.create_index(
        "ix_investors_normalized_name", "investors", ["normalized_name"]
    )

    op.create_table(
        "funding_rounds",
        sa.Column("id", **_uuid_pk),
        sa.Column(
            "company_id",
            UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("round_type", sa.Text(), nullable=False),
        sa.Column("amount_usd", sa.Numeric(), nullable=True),
        sa.Column("valuation_usd", sa.Numeric(), nullable=True),
        sa.Column("announced_date", sa.Date(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("created_at", **_created_at),
    )
    op.create_index(
        "ix_funding_rounds_company_id", "funding_rounds", ["company_id"]
    )

    op.create_table(
        "round_investors",
        sa.Column(
            "round_id",
            UUID(as_uuid=True),
            sa.ForeignKey("funding_rounds.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "investor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("investors.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "raw_sources",
        sa.Column("id", **_uuid_pk),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column(
            "processed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("created_at", **_created_at),
    )
    op.create_index(
        "ix_raw_sources_source_url",
        "raw_sources",
        ["source_url"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("round_investors")
    op.drop_table("funding_rounds")
    op.drop_table("raw_sources")
    op.drop_table("investors")
    op.drop_table("companies")
