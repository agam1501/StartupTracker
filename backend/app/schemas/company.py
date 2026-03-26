import uuid
from datetime import datetime

from pydantic import BaseModel


class CompanyBase(BaseModel):
    name: str
    website: str | None = None
    sector: str | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    id: uuid.UUID
    normalized_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyDetailResponse(CompanyResponse):
    funding_rounds: list["FundingRoundResponse"] = []


from app.schemas.funding_round import FundingRoundResponse  # noqa: E402

CompanyDetailResponse.model_rebuild()
