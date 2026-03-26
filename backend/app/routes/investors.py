import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import PaginatedResponse
from app.schemas.funding_round import FundingRoundResponse
from app.schemas.investor import InvestorResponse
from app.services.crud import get_investor, get_investor_rounds, list_investors
from app.services.db import get_session

router = APIRouter(prefix="/investors", tags=["investors"])


@router.get("", response_model=PaginatedResponse)
async def list_investors_endpoint(
    search: str | None = Query(None, description="Search by investor name"),
    investor_type: str | None = Query(None, description="Filter by investor type"),
    sort_by: str = Query("name", description="Sort by: name"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    investors, total = await list_investors(
        session,
        search=search,
        investor_type=investor_type,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[InvestorResponse.model_validate(i) for i in investors],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{investor_id}")
async def get_investor_endpoint(
    investor_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    investor = await get_investor(session, investor_id)
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    rounds = await get_investor_rounds(session, investor_id)

    investor_data = InvestorResponse.model_validate(investor).model_dump()
    investor_data["funding_rounds"] = [
        FundingRoundResponse.model_validate(r).model_dump() for r in rounds
    ]
    return investor_data
