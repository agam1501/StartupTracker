"""Deduplication for companies, investors, and funding rounds."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acquisition import Acquisition
from app.models.company import Company
from app.models.funding_round import FundingRound
from app.models.investor import Investor
from app.services.crud import create_company, create_investor
from app.services.normalization import normalize_name

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 85  # rapidfuzz score threshold (0-100)
ROUND_DATE_WINDOW_DAYS = 7
MIN_PREFIX_LEN = 4  # minimum prefix length for substring candidate search


def _candidate_query(model, normalized: str):
    """Build a query that narrows fuzzy match candidates using a substring filter.

    For short names (< MIN_PREFIX_LEN chars), loads all rows since the set is
    likely small. For longer names, filters by normalized_name containing the
    first MIN_PREFIX_LEN characters.
    """
    if len(normalized) < MIN_PREFIX_LEN:
        return select(model)
    prefix = normalized[:MIN_PREFIX_LEN]
    return select(model).where(model.normalized_name.ilike(f"%{prefix}%"))


def _fuzzy_match(a: str, b: str) -> float:
    """Return similarity score (0-100) between two strings."""
    try:
        from rapidfuzz import fuzz

        return fuzz.ratio(a, b)
    except ImportError:
        # Fallback: exact match only
        return 100.0 if a == b else 0.0


async def get_or_create_company(
    session: AsyncSession,
    name: str,
    website: str | None = None,
) -> Company:
    """Find existing company by normalized name (exact + fuzzy), or create new."""
    normalized = normalize_name(name)

    # Exact match first
    stmt = select(Company).where(Company.normalized_name == normalized)
    result = await session.execute(stmt)
    exact = result.scalar_one_or_none()
    if exact:
        return exact

    # Fuzzy match against candidate companies (substring filter to avoid loading all rows)
    candidates_stmt = _candidate_query(Company, normalized)
    candidates = (await session.execute(candidates_stmt)).scalars().all()
    for company in candidates:
        score = _fuzzy_match(normalized, company.normalized_name)
        if score >= FUZZY_THRESHOLD:
            logger.info(
                "Fuzzy matched '%s' to existing '%s' (score=%.1f)",
                name,
                company.name,
                score,
            )
            return company

    # No match, create new
    return await create_company(session, name, website=website)


async def get_or_create_investor(
    session: AsyncSession,
    name: str,
) -> Investor:
    """Find existing investor by normalized name (exact + fuzzy), or create new."""
    normalized = normalize_name(name)

    # Exact match
    stmt = select(Investor).where(Investor.normalized_name == normalized)
    result = await session.execute(stmt)
    exact = result.scalar_one_or_none()
    if exact:
        return exact

    # Fuzzy match against candidate investors (substring filter)
    candidates_stmt = _candidate_query(Investor, normalized)
    candidates = (await session.execute(candidates_stmt)).scalars().all()
    for investor in candidates:
        score = _fuzzy_match(normalized, investor.normalized_name)
        if score >= FUZZY_THRESHOLD:
            logger.info(
                "Fuzzy matched investor '%s' to existing '%s' (score=%.1f)",
                name,
                investor.name,
                score,
            )
            return investor

    return await create_investor(session, name)


async def is_duplicate_round(
    session: AsyncSession,
    company_id,
    round_type: str,
    announced_date=None,
    amount_usd=None,
) -> bool:
    """Check if a similar funding round already exists.

    Match criteria: same company + same round type + within date window.
    """
    stmt = select(FundingRound).where(
        FundingRound.company_id == company_id,
        FundingRound.round_type == round_type,
    )
    existing = (await session.execute(stmt)).scalars().all()

    if not existing:
        return False

    for fr in existing:
        # If no dates to compare, match on type alone
        if announced_date is None or fr.announced_date is None:
            return True

        # Check date window
        delta = abs((announced_date - fr.announced_date).days)
        if delta <= ROUND_DATE_WINDOW_DAYS:
            return True

    return False


ACQUISITION_DATE_WINDOW_DAYS = 30


async def is_duplicate_acquisition(
    session: AsyncSession,
    acquirer_id,
    target_id,
    announced_date=None,
) -> bool:
    """Check if a similar acquisition already exists.

    Match criteria: same acquirer + same target + within date window.
    """
    stmt = select(Acquisition).where(
        Acquisition.acquirer_id == acquirer_id,
        Acquisition.target_id == target_id,
    )
    existing = (await session.execute(stmt)).scalars().all()

    if not existing:
        return False

    for acq in existing:
        if announced_date is None or acq.announced_date is None:
            return True
        delta = abs((announced_date - acq.announced_date).days)
        if delta <= ACQUISITION_DATE_WINDOW_DAYS:
            return True

    return False
