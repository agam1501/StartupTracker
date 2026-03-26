import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pk_uuid


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = pk_uuid()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)
    sector: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    revenue_usd: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    revenue_as_of_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    funding_rounds = relationship("FundingRound", back_populates="company", lazy="selectin")
