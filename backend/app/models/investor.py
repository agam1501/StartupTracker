import uuid

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, pk_uuid


class Investor(Base):
    __tablename__ = "investors"

    id: Mapped[uuid.UUID] = pk_uuid()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
