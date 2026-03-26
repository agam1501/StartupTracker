"""Add acquisitions table

Revision ID: 003
Revises: 002
Create Date: 2026-03-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "003"
down_revision: str = "002"
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
        "acquisitions",
        sa.Column("id", **_uuid_pk),
        sa.Column(
            "acquirer_id",
            UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_id",
            UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount_usd", sa.Numeric(), nullable=True),
        sa.Column("announced_date", sa.Date(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", **_created_at),
    )
    op.create_index("ix_acquisitions_acquirer_id", "acquisitions", ["acquirer_id"])
    op.create_index("ix_acquisitions_target_id", "acquisitions", ["target_id"])


def downgrade() -> None:
    op.drop_index("ix_acquisitions_target_id", table_name="acquisitions")
    op.drop_index("ix_acquisitions_acquirer_id", table_name="acquisitions")
    op.drop_table("acquisitions")
