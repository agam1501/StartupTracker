import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import PaginatedResponse
from app.schemas.monitored_source import (
    MonitoredSourceCreate,
    MonitoredSourceResponse,
    MonitoredSourceUpdate,
)
from app.services.crud import (
    create_monitored_source,
    get_monitored_source,
    list_monitored_sources,
    update_monitored_source,
)
from app.services.db import get_session

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=PaginatedResponse)
async def list_sources_endpoint(
    source_type: str | None = Query(None, description="Filter by source type (rss/webpage)"),
    active: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    sources, total = await list_monitored_sources(
        session, source_type=source_type, active=active, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[MonitoredSourceResponse.model_validate(s) for s in sources],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{source_id}", response_model=MonitoredSourceResponse)
async def get_source_endpoint(
    source_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    source = await get_monitored_source(session, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return MonitoredSourceResponse.model_validate(source)


@router.post("", response_model=MonitoredSourceResponse, status_code=201)
async def create_source_endpoint(
    body: MonitoredSourceCreate,
    session: AsyncSession = Depends(get_session),
):
    if body.source_type not in ("rss", "webpage"):
        raise HTTPException(status_code=422, detail="source_type must be 'rss' or 'webpage'")
    source = await create_monitored_source(
        session,
        name=body.name,
        url=body.url,
        source_type=body.source_type,
        investor_id=body.investor_id,
        active=body.active,
    )
    await session.commit()
    return MonitoredSourceResponse.model_validate(source)


@router.patch("/{source_id}", response_model=MonitoredSourceResponse)
async def update_source_endpoint(
    source_id: uuid.UUID,
    body: MonitoredSourceUpdate,
    session: AsyncSession = Depends(get_session),
):
    updates = body.model_dump(exclude_unset=True)
    if "source_type" in updates and updates["source_type"] not in ("rss", "webpage"):
        raise HTTPException(status_code=422, detail="source_type must be 'rss' or 'webpage'")
    source = await update_monitored_source(session, source_id, **updates)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await session.commit()
    return MonitoredSourceResponse.model_validate(source)
