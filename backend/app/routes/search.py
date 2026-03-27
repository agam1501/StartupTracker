from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.investor import Investor
from app.services.db import get_session
from app.services.normalization import normalize_name

router = APIRouter(tags=["search"])


@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
):
    normalized = normalize_name(q)
    pattern = f"%{normalized}%"

    companies_q = (
        select(Company.id, Company.name, Company.sector)
        .where(Company.normalized_name.ilike(pattern))
        .limit(limit)
    )
    investors_q = (
        select(Investor.id, Investor.name, Investor.investor_type)
        .where(Investor.normalized_name.ilike(pattern))
        .limit(limit)
    )

    company_rows = (await session.execute(companies_q)).all()
    investor_rows = (await session.execute(investors_q)).all()

    return {
        "companies": [{"id": str(r.id), "name": r.name, "sector": r.sector} for r in company_rows],
        "investors": [
            {"id": str(r.id), "name": r.name, "investor_type": r.investor_type}
            for r in investor_rows
        ],
    }
