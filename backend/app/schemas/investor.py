import uuid

from pydantic import BaseModel


class InvestorBase(BaseModel):
    name: str


class InvestorCreate(InvestorBase):
    pass


class InvestorResponse(InvestorBase):
    id: uuid.UUID
    normalized_name: str
    investor_type: str | None = None
    website: str | None = None

    model_config = {"from_attributes": True}
