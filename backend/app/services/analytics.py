"""Analytics aggregation queries for charts and dashboards."""

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acquisition import Acquisition
from app.models.company import Company
from app.models.funding_round import FundingRound
from app.models.investor import Investor
from app.models.round_investor import round_investors


async def funding_by_sector(session: AsyncSession) -> list[dict]:
    """Total funding amount and round count grouped by sector."""
    stmt = (
        select(
            Company.sector,
            func.count(FundingRound.id).label("round_count"),
            func.coalesce(func.sum(FundingRound.amount_usd), 0).label("total_amount"),
        )
        .join(FundingRound, FundingRound.company_id == Company.id)
        .where(Company.sector.isnot(None))
        .group_by(Company.sector)
        .order_by(func.sum(FundingRound.amount_usd).desc().nullslast())
    )
    rows = (await session.execute(stmt)).all()
    return [
        {"sector": r.sector, "round_count": r.round_count, "total_amount": float(r.total_amount)}
        for r in rows
    ]


async def funding_by_month(
    session: AsyncSession,
    *,
    sector: str | None = None,
    months: int = 12,
) -> list[dict]:
    """Funding time series grouped by month."""
    cutoff = date.today() - timedelta(days=months * 30)

    base = (
        select(
            func.date_trunc("month", FundingRound.announced_date).label("month"),
            func.count(FundingRound.id).label("round_count"),
            func.coalesce(func.sum(FundingRound.amount_usd), 0).label("total_amount"),
        )
        .where(FundingRound.announced_date.isnot(None))
        .where(FundingRound.announced_date >= cutoff)
    )

    if sector:
        base = base.join(Company, Company.id == FundingRound.company_id).where(
            Company.sector == sector
        )

    stmt = base.group_by("month").order_by("month")
    rows = (await session.execute(stmt)).all()
    return [
        {
            "month": r.month.isoformat() if r.month else None,
            "round_count": r.round_count,
            "total_amount": float(r.total_amount),
        }
        for r in rows
    ]


async def top_investors(
    session: AsyncSession,
    *,
    limit: int = 20,
) -> list[dict]:
    """Top investors ranked by deal count and total invested."""
    stmt = (
        select(
            Investor.id,
            Investor.name,
            func.count(round_investors.c.round_id).label("deal_count"),
            func.coalesce(func.sum(FundingRound.amount_usd), 0).label("total_invested"),
        )
        .join(round_investors, round_investors.c.investor_id == Investor.id)
        .join(FundingRound, FundingRound.id == round_investors.c.round_id)
        .group_by(Investor.id, Investor.name)
        .order_by(func.count(round_investors.c.round_id).desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "deal_count": r.deal_count,
            "total_invested": float(r.total_invested),
        }
        for r in rows
    ]


async def co_investor_pairs(
    session: AsyncSession,
    *,
    limit: int = 20,
) -> list[dict]:
    """Most frequent co-investor pairs (self-join on round_investors)."""
    ri1 = round_investors.alias("ri1")
    ri2 = round_investors.alias("ri2")
    inv1 = Investor.__table__.alias("inv1")
    inv2 = Investor.__table__.alias("inv2")

    stmt = (
        select(
            inv1.c.name.label("investor_a"),
            inv2.c.name.label("investor_b"),
            func.count().label("shared_deals"),
        )
        .select_from(ri1)
        .join(ri2, (ri1.c.round_id == ri2.c.round_id) & (ri1.c.investor_id < ri2.c.investor_id))
        .join(inv1, inv1.c.id == ri1.c.investor_id)
        .join(inv2, inv2.c.id == ri2.c.investor_id)
        .group_by(inv1.c.name, inv2.c.name)
        .order_by(func.count().desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "investor_a": r.investor_a,
            "investor_b": r.investor_b,
            "shared_deals": r.shared_deals,
        }
        for r in rows
    ]


async def sector_summary(session: AsyncSession) -> list[dict]:
    """Per-sector stats: company count, round count, total funding, avg round size."""
    stmt = (
        select(
            Company.sector,
            func.count(func.distinct(Company.id)).label("company_count"),
            func.count(FundingRound.id).label("round_count"),
            func.coalesce(func.sum(FundingRound.amount_usd), 0).label("total_funding"),
            func.coalesce(func.avg(FundingRound.amount_usd), 0).label("avg_round_size"),
        )
        .outerjoin(FundingRound, FundingRound.company_id == Company.id)
        .where(Company.sector.isnot(None))
        .group_by(Company.sector)
        .order_by(func.count(func.distinct(Company.id)).desc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "sector": r.sector,
            "company_count": r.company_count,
            "round_count": r.round_count,
            "total_funding": float(r.total_funding),
            "avg_round_size": float(r.avg_round_size),
        }
        for r in rows
    ]


async def acquisitions_summary(session: AsyncSession) -> list[dict]:
    """Top acquirers by acquisition count."""
    stmt = (
        select(
            Company.id,
            Company.name,
            func.count(Acquisition.id).label("acquisition_count"),
            func.coalesce(func.sum(Acquisition.amount_usd), 0).label("total_spent"),
        )
        .join(Acquisition, Acquisition.acquirer_id == Company.id)
        .group_by(Company.id, Company.name)
        .order_by(func.count(Acquisition.id).desc())
        .limit(20)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "acquisition_count": r.acquisition_count,
            "total_spent": float(r.total_spent),
        }
        for r in rows
    ]


async def round_type_distribution(session: AsyncSession) -> list[dict]:
    """Distribution of funding rounds by type."""
    stmt = (
        select(
            FundingRound.round_type,
            func.count(FundingRound.id).label("count"),
            func.coalesce(func.sum(FundingRound.amount_usd), 0).label("total_amount"),
        )
        .group_by(FundingRound.round_type)
        .order_by(func.count(FundingRound.id).desc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "round_type": r.round_type,
            "count": r.count,
            "total_amount": float(r.total_amount),
        }
        for r in rows
    ]
