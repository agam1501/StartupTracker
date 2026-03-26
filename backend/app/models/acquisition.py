import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pk_uuid


class Acquisition(Base, TimestampMixin):
    __tablename__ = "acquisitions"

    id: Mapped[uuid.UUID] = pk_uuid()
    acquirer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount_usd: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    announced_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    acquirer = relationship("Company", foreign_keys=[acquirer_id], lazy="selectin")
    target = relationship("Company", foreign_keys=[target_id], lazy="selectin")
