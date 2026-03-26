import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pk_uuid


class MonitoredSource(Base, TimestampMixin):
    __tablename__ = "monitored_sources"

    id: Mapped[uuid.UUID] = pk_uuid()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)  # 'rss' or 'webpage'
    investor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investors.id", ondelete="SET NULL"),
        nullable=True,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    investor = relationship("Investor", lazy="selectin")
