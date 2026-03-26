import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import PaginatedResponse
from app.schemas.funding_round import FundingRoundResponse
from app.services.crud import get_funding_round, list_funding_rounds
from app.services.db import get_session

router = APIRouter(prefix="/funding-rounds", tags=["funding_rounds"])


@router.get("", response_model=PaginatedResponse)
async def list_funding_rounds_endpoint(
    company_id: uuid.UUID | None = Query(None),
    round_type: str | None = Query(None),
    investor_id: uuid.UUID | None = Query(None, description="Filter by investor"),
    min_amount: float | None = Query(None, description="Minimum amount USD"),
    max_amount: float | None = Query(None, description="Maximum amount USD"),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    sort_by: str = Query("date", description="Sort by: date, amount, round_type"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    rounds, total = await list_funding_rounds(
        session,
        company_id=company_id,
        round_type=round_type,
        investor_id=investor_id,
        min_amount=min_amount,
        max_amount=max_amount,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[FundingRoundResponse.model_validate(r) for r in rounds],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{round_id}", response_model=FundingRoundResponse)
async def get_funding_round_endpoint(
    round_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    fr = await get_funding_round(session, round_id)
    if not fr:
        raise HTTPException(status_code=404, detail="Funding round not found")
    return FundingRoundResponse.model_validate(fr)
