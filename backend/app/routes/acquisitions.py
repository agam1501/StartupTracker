import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.acquisition import AcquisitionResponse
from app.schemas.common import PaginatedResponse
from app.services.crud import get_acquisition, list_acquisitions
from app.services.db import get_session

router = APIRouter(prefix="/acquisitions", tags=["acquisitions"])


def _to_response(acq) -> dict:
    """Convert Acquisition ORM to response dict with computed names."""
    return {
        "id": acq.id,
        "acquirer_id": acq.acquirer_id,
        "acquirer_name": acq.acquirer.name if acq.acquirer else None,
        "target_id": acq.target_id,
        "target_name": acq.target.name if acq.target else None,
        "amount_usd": acq.amount_usd,
        "announced_date": acq.announced_date,
        "source_url": acq.source_url,
        "confidence_score": acq.confidence_score,
        "created_at": acq.created_at,
    }


@router.get("", response_model=PaginatedResponse)
async def list_acquisitions_endpoint(
    acquirer_id: uuid.UUID | None = Query(None),
    target_id: uuid.UUID | None = Query(None),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    sort_by: str = Query("date", description="Sort by: date, amount"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    acquisitions, total = await list_acquisitions(
        session,
        acquirer_id=acquirer_id,
        target_id=target_id,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[AcquisitionResponse.model_validate(_to_response(a)) for a in acquisitions],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{acquisition_id}", response_model=AcquisitionResponse)
async def get_acquisition_endpoint(
    acquisition_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    acq = await get_acquisition(session, acquisition_id)
    if not acq:
        raise HTTPException(status_code=404, detail="Acquisition not found")
    return AcquisitionResponse.model_validate(_to_response(acq))
