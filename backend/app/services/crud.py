import uuid
from datetime import UTC

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.acquisition import Acquisition
from app.models.company import Company
from app.models.funding_round import FundingRound
from app.models.investor import Investor
from app.models.monitored_source import MonitoredSource
from app.models.raw_source import RawSource
from app.models.round_investor import round_investors
from app.services.normalization import normalize_name

# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------


async def create_company(
    session: AsyncSession,
    name: str,
    website: str | None = None,
    sector: str | None = None,
) -> Company:
    company = Company(
        name=name,
        normalized_name=normalize_name(name),
        website=website,
        sector=sector,
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


async def update_company_sector(
    session: AsyncSession,
    company_id: uuid.UUID,
    sector: str,
) -> None:
    """Update a company's sector if not already set."""
    stmt = select(Company).where(Company.id == company_id)
    result = await session.execute(stmt)
    company = result.scalar_one_or_none()
    if company and not company.sector:
        company.sector = sector
        await session.flush()


async def update_company_revenue(
    session: AsyncSession,
    company_id: uuid.UUID,
    revenue_usd,
    revenue_as_of_date=None,
) -> None:
    """Update a company's revenue if not already set or if new date is more recent."""
    stmt = select(Company).where(Company.id == company_id)
    result = await session.execute(stmt)
    company = result.scalar_one_or_none()
    if not company:
        return

    # Update if company has no revenue, or new data has a more recent date
    should_update = False
    if company.revenue_usd is None:
        should_update = True
    elif revenue_as_of_date and (
        company.revenue_as_of_date is None or revenue_as_of_date > company.revenue_as_of_date
    ):
        should_update = True

    if should_update:
        company.revenue_usd = revenue_usd
        company.revenue_as_of_date = revenue_as_of_date
        await session.flush()


async def update_company_status(
    session: AsyncSession,
    company_id: uuid.UUID,
    status: str,
) -> None:
    """Update a company's status (e.g., 'acquired', 'ipo', 'defunct')."""
    stmt = select(Company).where(Company.id == company_id)
    result = await session.execute(stmt)
    company = result.scalar_one_or_none()
    if company:
        company.status = status
        await session.flush()


async def update_company(
    session: AsyncSession,
    company_id: uuid.UUID,
    **kwargs,
) -> Company | None:
    stmt = (
        select(Company)
        .options(selectinload(Company.funding_rounds).selectinload(FundingRound.investors))
        .where(Company.id == company_id)
    )
    result = await session.execute(stmt)
    company = result.scalar_one_or_none()
    if not company:
        return None
    if "name" in kwargs:
        kwargs["normalized_name"] = normalize_name(kwargs["name"])
    for key, value in kwargs.items():
        if hasattr(company, key):
            setattr(company, key, value)
    await session.flush()
    return company


async def delete_company(
    session: AsyncSession,
    company_id: uuid.UUID,
) -> bool:
    stmt = select(Company).where(Company.id == company_id)
    result = await session.execute(stmt)
    company = result.scalar_one_or_none()
    if not company:
        return False
    await session.delete(company)
    await session.flush()
    return True


async def list_companies(
    session: AsyncSession,
    *,
    search: str | None = None,
    sector: str | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Company], int]:
    base = select(Company)
    count_base = select(func.count()).select_from(Company)

    if search:
        pattern = f"%{normalize_name(search)}%"
        base = base.where(Company.normalized_name.ilike(pattern))
        count_base = count_base.where(Company.normalized_name.ilike(pattern))

    if sector:
        base = base.where(Company.sector == sector)
        count_base = count_base.where(Company.sector == sector)

    total = (await session.execute(count_base)).scalar_one()

    # Sorting
    sort_columns = {
        "name": Company.name,
        "created_at": Company.created_at,
        "sector": Company.sector,
    }
    col = sort_columns.get(sort_by, Company.name)
    order = col.desc().nullslast() if sort_order == "desc" else col.asc().nullslast()

    stmt = base.order_by(order).offset((page - 1) * page_size).limit(page_size)
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
    confidence_score: float | None = None,
) -> FundingRound:
    fr = FundingRound(
        company_id=company_id,
        round_type=round_type,
        amount_usd=amount_usd,
        valuation_usd=valuation_usd,
        announced_date=announced_date,
        source_url=source_url,
        confidence_score=confidence_score,
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


async def update_funding_round(
    session: AsyncSession,
    round_id: uuid.UUID,
    **kwargs,
) -> FundingRound | None:
    stmt = (
        select(FundingRound)
        .options(selectinload(FundingRound.investors))
        .where(FundingRound.id == round_id)
    )
    result = await session.execute(stmt)
    fr = result.scalar_one_or_none()
    if not fr:
        return None
    for key, value in kwargs.items():
        if hasattr(fr, key):
            setattr(fr, key, value)
    await session.flush()
    return fr


async def delete_funding_round(
    session: AsyncSession,
    round_id: uuid.UUID,
) -> bool:
    stmt = select(FundingRound).where(FundingRound.id == round_id)
    result = await session.execute(stmt)
    fr = result.scalar_one_or_none()
    if not fr:
        return False
    await session.delete(fr)
    await session.flush()
    return True


async def list_funding_rounds(
    session: AsyncSession,
    *,
    company_id: uuid.UUID | None = None,
    round_type: str | None = None,
    investor_id: uuid.UUID | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str = "date",
    sort_order: str = "desc",
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
    if investor_id:
        base = base.where(
            FundingRound.id.in_(
                select(round_investors.c.round_id).where(
                    round_investors.c.investor_id == investor_id
                )
            )
        )
        count_base = count_base.where(
            FundingRound.id.in_(
                select(round_investors.c.round_id).where(
                    round_investors.c.investor_id == investor_id
                )
            )
        )
    if min_amount is not None:
        base = base.where(FundingRound.amount_usd >= min_amount)
        count_base = count_base.where(FundingRound.amount_usd >= min_amount)
    if max_amount is not None:
        base = base.where(FundingRound.amount_usd <= max_amount)
        count_base = count_base.where(FundingRound.amount_usd <= max_amount)
    if date_from:
        base = base.where(FundingRound.announced_date >= date_from)
        count_base = count_base.where(FundingRound.announced_date >= date_from)
    if date_to:
        base = base.where(FundingRound.announced_date <= date_to)
        count_base = count_base.where(FundingRound.announced_date <= date_to)

    total = (await session.execute(count_base)).scalar_one()

    sort_columns = {
        "date": FundingRound.announced_date,
        "amount": FundingRound.amount_usd,
        "round_type": FundingRound.round_type,
    }
    col = sort_columns.get(sort_by, FundingRound.announced_date)
    order = col.desc().nullslast() if sort_order == "desc" else col.asc().nullslast()

    stmt = base.order_by(order).offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(stmt)).scalars().unique().all()
    return list(rows), total


# ---------------------------------------------------------------------------
# Investors
# ---------------------------------------------------------------------------


async def create_investor(
    session: AsyncSession,
    name: str,
    investor_type: str | None = None,
    website: str | None = None,
) -> Investor:
    investor = Investor(
        name=name,
        normalized_name=normalize_name(name),
        investor_type=investor_type,
        website=website,
    )
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


async def get_investor_rounds(
    session: AsyncSession,
    investor_id: uuid.UUID,
) -> list[FundingRound]:
    """Get all funding rounds an investor participated in."""
    stmt = (
        select(FundingRound)
        .join(round_investors, round_investors.c.round_id == FundingRound.id)
        .where(round_investors.c.investor_id == investor_id)
        .options(
            selectinload(FundingRound.investors),
            selectinload(FundingRound.company),
        )
        .order_by(FundingRound.announced_date.desc().nullslast())
    )
    rows = (await session.execute(stmt)).scalars().unique().all()
    return list(rows)


async def list_investors(
    session: AsyncSession,
    *,
    search: str | None = None,
    investor_type: str | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Investor], int]:
    base = select(Investor)
    count_base = select(func.count()).select_from(Investor)

    if search:
        pattern = f"%{normalize_name(search)}%"
        base = base.where(Investor.normalized_name.ilike(pattern))
        count_base = count_base.where(Investor.normalized_name.ilike(pattern))

    if investor_type:
        base = base.where(Investor.investor_type == investor_type)
        count_base = count_base.where(Investor.investor_type == investor_type)

    total = (await session.execute(count_base)).scalar_one()

    sort_columns = {
        "name": Investor.name,
    }
    col = sort_columns.get(sort_by, Investor.name)
    order = col.desc().nullslast() if sort_order == "desc" else col.asc().nullslast()

    stmt = base.order_by(order).offset((page - 1) * page_size).limit(page_size)
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
# Acquisitions
# ---------------------------------------------------------------------------


async def create_acquisition(
    session: AsyncSession,
    *,
    acquirer_id: uuid.UUID,
    target_id: uuid.UUID,
    amount_usd: float | None = None,
    announced_date=None,
    source_url: str | None = None,
    confidence_score: float | None = None,
) -> Acquisition:
    acq = Acquisition(
        acquirer_id=acquirer_id,
        target_id=target_id,
        amount_usd=amount_usd,
        announced_date=announced_date,
        source_url=source_url,
        confidence_score=confidence_score,
    )
    session.add(acq)
    await session.flush()
    return acq


async def get_acquisition(
    session: AsyncSession,
    acquisition_id: uuid.UUID,
) -> Acquisition | None:
    stmt = (
        select(Acquisition)
        .options(
            selectinload(Acquisition.acquirer),
            selectinload(Acquisition.target),
        )
        .where(Acquisition.id == acquisition_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_acquisitions(
    session: AsyncSession,
    *,
    acquirer_id: uuid.UUID | None = None,
    target_id: uuid.UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str = "date",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Acquisition], int]:
    base = select(Acquisition).options(
        selectinload(Acquisition.acquirer),
        selectinload(Acquisition.target),
    )
    count_base = select(func.count()).select_from(Acquisition)

    if acquirer_id:
        base = base.where(Acquisition.acquirer_id == acquirer_id)
        count_base = count_base.where(Acquisition.acquirer_id == acquirer_id)
    if target_id:
        base = base.where(Acquisition.target_id == target_id)
        count_base = count_base.where(Acquisition.target_id == target_id)
    if date_from:
        base = base.where(Acquisition.announced_date >= date_from)
        count_base = count_base.where(Acquisition.announced_date >= date_from)
    if date_to:
        base = base.where(Acquisition.announced_date <= date_to)
        count_base = count_base.where(Acquisition.announced_date <= date_to)

    total = (await session.execute(count_base)).scalar_one()

    sort_columns = {
        "date": Acquisition.announced_date,
        "amount": Acquisition.amount_usd,
    }
    col = sort_columns.get(sort_by, Acquisition.announced_date)
    order = col.desc().nullslast() if sort_order == "desc" else col.asc().nullslast()

    stmt = base.order_by(order).offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(stmt)).scalars().unique().all()
    return list(rows), total


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
    total_acquisitions = (
        await session.execute(select(func.count()).select_from(Acquisition))
    ).scalar_one()

    # Top sector by company count
    top_sector_row = (
        await session.execute(
            select(Company.sector, func.count().label("cnt"))
            .where(Company.sector.isnot(None))
            .group_by(Company.sector)
            .order_by(func.count().desc())
            .limit(1)
        )
    ).first()
    top_sector = top_sector_row[0] if top_sector_row else None

    return {
        "total_companies": total_companies,
        "total_rounds": total_rounds,
        "total_investors": total_investors,
        "total_funding_usd": float(total_funding),
        "total_acquisitions": total_acquisitions,
        "top_sector": top_sector,
    }


# ---------------------------------------------------------------------------
# Monitored sources
# ---------------------------------------------------------------------------


async def create_monitored_source(
    session: AsyncSession,
    *,
    name: str,
    url: str,
    source_type: str,
    investor_id: uuid.UUID | None = None,
    active: bool = True,
) -> MonitoredSource:
    ms = MonitoredSource(
        name=name,
        url=url,
        source_type=source_type,
        investor_id=investor_id,
        active=active,
    )
    session.add(ms)
    await session.flush()
    return ms


async def get_monitored_source(
    session: AsyncSession,
    source_id: uuid.UUID,
) -> MonitoredSource | None:
    stmt = select(MonitoredSource).where(MonitoredSource.id == source_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_monitored_sources(
    session: AsyncSession,
    *,
    source_type: str | None = None,
    active: bool | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[MonitoredSource], int]:
    base = select(MonitoredSource)
    count_base = select(func.count()).select_from(MonitoredSource)

    if source_type:
        base = base.where(MonitoredSource.source_type == source_type)
        count_base = count_base.where(MonitoredSource.source_type == source_type)
    if active is not None:
        base = base.where(MonitoredSource.active.is_(active))
        count_base = count_base.where(MonitoredSource.active.is_(active))

    total = (await session.execute(count_base)).scalar_one()

    stmt = base.order_by(MonitoredSource.name).offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows), total


async def update_monitored_source(
    session: AsyncSession,
    source_id: uuid.UUID,
    **kwargs,
) -> MonitoredSource | None:
    stmt = select(MonitoredSource).where(MonitoredSource.id == source_id)
    result = await session.execute(stmt)
    ms = result.scalar_one_or_none()
    if not ms:
        return None
    for key, value in kwargs.items():
        if hasattr(ms, key):
            setattr(ms, key, value)
    await session.flush()
    return ms


async def get_active_sources(
    session: AsyncSession,
    source_type: str | None = None,
) -> list[MonitoredSource]:
    stmt = select(MonitoredSource).where(MonitoredSource.active.is_(True))
    if source_type:
        stmt = stmt.where(MonitoredSource.source_type == source_type)
    stmt = stmt.order_by(MonitoredSource.name)
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)


async def mark_source_checked(
    session: AsyncSession,
    source_id: uuid.UUID,
) -> None:
    from datetime import datetime

    stmt = select(MonitoredSource).where(MonitoredSource.id == source_id)
    result = await session.execute(stmt)
    ms = result.scalar_one_or_none()
    if ms:
        ms.last_checked_at = datetime.now(UTC)
        await session.flush()
