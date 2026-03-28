import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanyDetailResponse, CompanyResponse, CompanyUpdate
from app.services.crud import delete_company, get_company, list_companies, update_company
from app.services.db import get_session

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=PaginatedResponse)
async def list_companies_endpoint(
    search: str | None = Query(None, description="Search by company name"),
    sector: str | None = Query(None, description="Filter by sector"),
    sort_by: str = Query("name", description="Sort by: name, created_at, sector"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    companies, total = await list_companies(
        session,
        search=search,
        sector=sector,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[CompanyResponse.model_validate(c) for c in companies],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{company_id}", response_model=CompanyDetailResponse)
async def get_company_endpoint(
    company_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    company = await get_company(session, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyDetailResponse.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyDetailResponse)
async def update_company_endpoint(
    company_id: uuid.UUID,
    body: CompanyUpdate,
    session: AsyncSession = Depends(get_session),
):
    updates = body.model_dump(exclude_unset=True)
    company = await update_company(session, company_id, **updates)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    await session.commit()
    return CompanyDetailResponse.model_validate(company)


@router.delete("/{company_id}", status_code=204)
async def delete_company_endpoint(
    company_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    deleted = await delete_company(session, company_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Company not found")
    await session.commit()
    return Response(status_code=204)
