from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base

round_investors = Table(
    "round_investors",
    Base.metadata,
    Column("round_id", UUID(as_uuid=True), ForeignKey("funding_rounds.id", ondelete="CASCADE"), primary_key=True),
    Column("investor_id", UUID(as_uuid=True), ForeignKey("investors.id", ondelete="CASCADE"), primary_key=True),
)
