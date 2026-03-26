import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import PaginatedResponse
from app.schemas.investor import InvestorResponse
from app.services.crud import get_investor, list_investors
from app.services.db import get_session

router = APIRouter(prefix="/investors", tags=["investors"])


@router.get("", response_model=PaginatedResponse)
async def list_investors_endpoint(
    search: str | None = Query(None, description="Search by investor name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    investors, total = await list_investors(session, search=search, page=page, page_size=page_size)
    return PaginatedResponse(
        items=[InvestorResponse.model_validate(i) for i in investors],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{investor_id}", response_model=InvestorResponse)
async def get_investor_endpoint(
    investor_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    investor = await get_investor(session, investor_id)
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    return InvestorResponse.model_validate(investor)
