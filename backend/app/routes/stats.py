from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.crud import get_stats
from app.services.db import get_session


class StatsResponse(BaseModel):
    total_companies: int
    total_rounds: int
    total_investors: int
    total_funding_usd: float
    total_acquisitions: int
    top_sector: str | None


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats_endpoint(
    session: AsyncSession = Depends(get_session),
):
    return await get_stats(session)
