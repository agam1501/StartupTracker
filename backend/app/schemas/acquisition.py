import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class AcquisitionCreate(BaseModel):
    acquirer_id: uuid.UUID
    target_id: uuid.UUID
    amount_usd: Decimal | None = None
    announced_date: date | None = None
    source_url: str | None = None
    confidence_score: float | None = None


class AcquisitionResponse(BaseModel):
    id: uuid.UUID
    acquirer_id: uuid.UUID
    acquirer_name: str | None = None
    target_id: uuid.UUID
    target_name: str | None = None
    amount_usd: Decimal | None = None
    announced_date: date | None = None
    source_url: str | None = None
    confidence_score: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
