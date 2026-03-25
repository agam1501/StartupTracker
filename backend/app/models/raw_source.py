import uuid

from sqlalchemy import Boolean, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, pk_uuid


class RawSource(Base, TimestampMixin):
    __tablename__ = "raw_sources"

    id: Mapped[uuid.UUID] = pk_uuid()
    source_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
