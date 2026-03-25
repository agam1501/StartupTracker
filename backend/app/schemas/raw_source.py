import uuid
from datetime import datetime

from pydantic import BaseModel


class RawSourceCreate(BaseModel):
    source_url: str
    title: str | None = None
    content: str | None = None


class RawSourceResponse(BaseModel):
    id: uuid.UUID
    source_url: str
    title: str | None
    processed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
