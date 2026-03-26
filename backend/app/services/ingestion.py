"""Full ingestion pipeline: fetch -> extract -> normalize -> dedup -> insert."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.crud import (
    create_funding_round,
    create_raw_source,
    get_raw_source_by_url,
    mark_source_processed,
)
from app.services.dedup import get_or_create_company, get_or_create_investor, is_duplicate_round
from app.services.fetcher import fetch_article_text, parse_rss_feed
from app.services.llm import extract_funding
from app.services.normalization import validate_extraction

logger = logging.getLogger(__name__)


async def ingest_url(
    session: AsyncSession,
    url: str,
    title: str | None = None,
) -> dict:
    """Process a single URL through the full pipeline.

    Returns a status dict with outcome details.
    """
    # 1. Check if already processed
    existing = await get_raw_source_by_url(session, url)
    if existing and existing.processed:
        return {"url": url, "status": "already_processed"}

    # 2. Fetch article text
    text = await fetch_article_text(url)
    if not text:
        return {"url": url, "status": "fetch_failed"}

    # 3. Store raw source
    if not existing:
        raw = await create_raw_source(session, source_url=url, title=title, content=text[:50000])
    else:
        raw = existing
        if not raw.content:
            raw.content = text[:50000]

    # 4. LLM extraction
    extraction = await extract_funding(text)
    if not extraction:
        await mark_source_processed(session, raw.id)
        await session.commit()
        return {"url": url, "status": "extraction_failed"}

    # 5. Validate and normalize
    validated = validate_extraction(extraction)
    if not validated:
        await mark_source_processed(session, raw.id)
        await session.commit()
        return {"url": url, "status": "validation_failed"}

    # 6. Dedup company
    company = await get_or_create_company(session, validated.company)

    # 7. Check for duplicate round
    if await is_duplicate_round(
        session,
        company.id,
        validated.round_type,
        validated.announcement_date,
        validated.amount_usd,
    ):
        await mark_source_processed(session, raw.id)
        await session.commit()
        return {"url": url, "status": "duplicate_round", "company": company.name}

    # 8. Dedup investors
    investor_ids = []
    for inv_name in validated.investors:
        inv = await get_or_create_investor(session, inv_name)
        investor_ids.append(inv.id)

    # 9. Create funding round
    await create_funding_round(
        session,
        company_id=company.id,
        round_type=validated.round_type,
        amount_usd=validated.amount_usd,
        valuation_usd=validated.valuation_usd,
        announced_date=validated.announcement_date,
        source_url=url,
        investor_ids=investor_ids,
    )

    # 10. Mark processed
    await mark_source_processed(session, raw.id)
    await session.commit()

    return {
        "url": url,
        "status": "ingested",
        "company": company.name,
        "round_type": validated.round_type,
    }


async def ingest_rss_feed(
    session: AsyncSession,
    feed_url: str,
) -> list[dict]:
    """Parse an RSS feed and ingest all new articles."""
    entries = await parse_rss_feed(feed_url)
    results = []

    for entry in entries:
        url = entry["url"]
        title = entry.get("title")

        # Skip already-processed URLs
        existing = await get_raw_source_by_url(session, url)
        if existing and existing.processed:
            results.append({"url": url, "status": "already_processed"})
            continue

        result = await ingest_url(session, url, title=title)
        results.append(result)

    return results
