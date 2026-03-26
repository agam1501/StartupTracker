import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pk_uuid


class FundingRound(Base, TimestampMixin):
    __tablename__ = "funding_rounds"

    id: Mapped[uuid.UUID] = pk_uuid()
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_type: Mapped[str] = mapped_column(Text, nullable=False)
    amount_usd: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    valuation_usd: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    announced_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    company = relationship("Company", back_populates="funding_rounds")
    investors = relationship("Investor", secondary="round_investors", lazy="selectin")

    @hybrid_property
    def company_name(self) -> str | None:
        return self.company.name if self.company else None
