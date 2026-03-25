import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.investor import InvestorResponse


class FundingRoundBase(BaseModel):
    round_type: str
    amount_usd: Decimal | None = None
    valuation_usd: Decimal | None = None
    announced_date: date | None = None
    source_url: str | None = None


class FundingRoundCreate(FundingRoundBase):
    company_id: uuid.UUID


class FundingRoundResponse(FundingRoundBase):
    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    investors: list[InvestorResponse] = []

    model_config = {"from_attributes": True}
