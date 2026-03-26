import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MonitoredSourceCreate(BaseModel):
    name: str
    url: str
    source_type: str  # 'rss' or 'webpage'
    investor_id: uuid.UUID | None = None
    active: bool = True


class MonitoredSourceUpdate(BaseModel):
    name: str | None = None
    active: bool | None = None
    source_type: str | None = None
    investor_id: uuid.UUID | None = None


class MonitoredSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    url: str
    source_type: str
    investor_id: uuid.UUID | None = None
    active: bool
    last_checked_at: datetime | None = None
    created_at: datetime
