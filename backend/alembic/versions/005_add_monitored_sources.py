"""Add monitored_sources table.

Revision ID: 005
Revises: 004
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "monitored_sources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False, unique=True),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column(
            "investor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_monitored_sources_source_type", "monitored_sources", ["source_type"])
    op.create_index("ix_monitored_sources_active", "monitored_sources", ["active"])


def downgrade() -> None:
    op.drop_index("ix_monitored_sources_active", table_name="monitored_sources")
    op.drop_index("ix_monitored_sources_source_type", table_name="monitored_sources")
    op.drop_table("monitored_sources")
