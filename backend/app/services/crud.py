import re
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.funding_round import FundingRound
from app.models.investor import Investor
from app.models.raw_source import RawSource
from app.models.round_investor import round_investors


def normalize_name(name: str) -> str:
    """Lowercase, strip common suffixes, collapse whitespace."""
    n = name.lower().strip()
    n = re.sub(r"\b(inc|llc|ltd|corp|co|plc)\.?\b", "", n)
    n = re.sub(r"[^\w\s]", "", n)
    return re.sub(r"\s+", " ", n).strip()


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------


async def create_company(
    session: AsyncSession,
    name: str,
    website: str | None = None,
) -> Company:
    company = Company(
        name=name,
        normalized_name=normalize_name(name),
        website=website,
    )
    session.add(company)
    await session.flush()
    return company


async def get_company(
    session: AsyncSession,
    company_id: uuid.UUID,
) -> Company | None:
    stmt = (
        select(Company)
        .options(selectinload(Company.funding_rounds).selectinload(FundingRound.investors))
        .where(Company.id == company_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_companies(
    session: AsyncSession,
    *,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Company], int]:
    base = select(Company)
    count_base = select(func.count()).select_from(Company)

    if search:
        pattern = f"%{normalize_name(search)}%"
        base = base.where(Company.normalized_name.ilike(pattern))
        count_base = count_base.where(Company.normalized_name.ilike(pattern))

    total = (await session.execute(count_base)).scalar_one()

    stmt = base.order_by(Company.name).offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows), total


# ---------------------------------------------------------------------------
# Funding rounds
# ---------------------------------------------------------------------------


async def create_funding_round(
    session: AsyncSession,
    *,
    company_id: uuid.UUID,
    round_type: str,
    amount_usd: float | None = None,
    valuation_usd: float | None = None,
    announced_date=None,
    source_url: str | None = None,
    investor_ids: list[uuid.UUID] | None = None,
) -> FundingRound:
    fr = FundingRound(
        company_id=company_id,
        round_type=round_type,
        amount_usd=amount_usd,
        valuation_usd=valuation_usd,
        announced_date=announced_date,
        source_url=source_url,
    )
    session.add(fr)
    await session.flush()

    if investor_ids:
        for inv_id in investor_ids:
            await session.execute(
                round_investors.insert().values(round_id=fr.id, investor_id=inv_id)
            )
        await session.flush()

    return fr


async def get_funding_round(
    session: AsyncSession,
    round_id: uuid.UUID,
) -> FundingRound | None:
    stmt = (
        select(FundingRound)
        .options(selectinload(FundingRound.investors))
        .where(FundingRound.id == round_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_funding_rounds(
    session: AsyncSession,
    *,
    company_id: uuid.UUID | None = None,
    round_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[FundingRound], int]:
    base = select(FundingRound).options(
        selectinload(FundingRound.investors),
        selectinload(FundingRound.company),
    )
    count_base = select(func.count()).select_from(FundingRound)

    if company_id:
        base = base.where(FundingRound.company_id == company_id)
        count_base = count_base.where(FundingRound.company_id == company_id)
    if round_type:
        base = base.where(FundingRound.round_type == round_type)
        count_base = count_base.where(FundingRound.round_type == round_type)

    total = (await session.execute(count_base)).scalar_one()

    stmt = (
        base.order_by(FundingRound.announced_date.desc().nullslast())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await session.execute(stmt)).scalars().unique().all()
    return list(rows), total


# ---------------------------------------------------------------------------
# Investors
# ---------------------------------------------------------------------------


async def create_investor(
    session: AsyncSession,
    name: str,
) -> Investor:
    investor = Investor(name=name, normalized_name=normalize_name(name))
    session.add(investor)
    await session.flush()
    return investor


async def get_investor(
    session: AsyncSession,
    investor_id: uuid.UUID,
) -> Investor | None:
    stmt = select(Investor).where(Investor.id == investor_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_investors(
    session: AsyncSession,
    *,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Investor], int]:
    base = select(Investor)
    count_base = select(func.count()).select_from(Investor)

    if search:
        pattern = f"%{normalize_name(search)}%"
        base = base.where(Investor.normalized_name.ilike(pattern))
        count_base = count_base.where(Investor.normalized_name.ilike(pattern))

    total = (await session.execute(count_base)).scalar_one()

    stmt = base.order_by(Investor.name).offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows), total


async def get_investor_by_normalized_name(
    session: AsyncSession,
    normalized_name: str,
) -> Investor | None:
    stmt = select(Investor).where(Investor.normalized_name == normalized_name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Raw sources
# ---------------------------------------------------------------------------


async def create_raw_source(
    session: AsyncSession,
    *,
    source_url: str,
    title: str | None = None,
    content: str | None = None,
) -> RawSource:
    rs = RawSource(source_url=source_url, title=title, content=content)
    session.add(rs)
    await session.flush()
    return rs


async def get_raw_source_by_url(
    session: AsyncSession,
    source_url: str,
) -> RawSource | None:
    stmt = select(RawSource).where(RawSource.source_url == source_url)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_unprocessed_sources(
    session: AsyncSession,
    *,
    limit: int = 50,
) -> list[RawSource]:
    stmt = (
        select(RawSource)
        .where(RawSource.processed.is_(False))
        .order_by(RawSource.created_at)
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)


async def mark_source_processed(
    session: AsyncSession,
    source_id: uuid.UUID,
) -> None:
    stmt = select(RawSource).where(RawSource.id == source_id)
    result = await session.execute(stmt)
    rs = result.scalar_one_or_none()
    if rs:
        rs.processed = True
        await session.flush()


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


async def get_stats(session: AsyncSession) -> dict:
    total_companies = (
        await session.execute(select(func.count()).select_from(Company))
    ).scalar_one()
    total_rounds = (
        await session.execute(select(func.count()).select_from(FundingRound))
    ).scalar_one()
    total_investors = (
        await session.execute(select(func.count()).select_from(Investor))
    ).scalar_one()
    total_funding = (
        await session.execute(select(func.coalesce(func.sum(FundingRound.amount_usd), 0)))
    ).scalar_one()
    return {
        "total_companies": total_companies,
        "total_rounds": total_rounds,
        "total_investors": total_investors,
        "total_funding_usd": float(total_funding),
    }
