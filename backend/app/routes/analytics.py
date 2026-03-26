from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics import (
    acquisitions_summary,
    co_investor_pairs,
    funding_by_month,
    funding_by_sector,
    round_type_distribution,
    sector_summary,
    top_investors,
)
from app.services.db import get_session

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/funding-by-sector")
async def funding_by_sector_endpoint(
    session: AsyncSession = Depends(get_session),
):
    return await funding_by_sector(session)


@router.get("/funding-by-month")
async def funding_by_month_endpoint(
    sector: str | None = Query(None, description="Filter by sector"),
    months: int = Query(12, ge=1, le=60, description="Number of months to look back"),
    session: AsyncSession = Depends(get_session),
):
    return await funding_by_month(session, sector=sector, months=months)


@router.get("/top-investors")
async def top_investors_endpoint(
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    return await top_investors(session, limit=limit)


@router.get("/co-investors")
async def co_investors_endpoint(
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    return await co_investor_pairs(session, limit=limit)


@router.get("/sector-summary")
async def sector_summary_endpoint(
    session: AsyncSession = Depends(get_session),
):
    return await sector_summary(session)


@router.get("/acquisitions-summary")
async def acquisitions_summary_endpoint(
    session: AsyncSession = Depends(get_session),
):
    return await acquisitions_summary(session)


@router.get("/round-type-distribution")
async def round_type_distribution_endpoint(
    session: AsyncSession = Depends(get_session),
):
    return await round_type_distribution(session)
