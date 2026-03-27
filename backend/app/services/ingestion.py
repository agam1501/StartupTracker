"""Full ingestion pipeline: fetch -> extract -> normalize -> dedup -> insert."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.crud import (
    create_acquisition,
    create_funding_round,
    create_raw_source,
    get_raw_source_by_url,
    mark_source_processed,
    update_company_sector,
)
from app.services.dedup import (
    get_or_create_company,
    get_or_create_investor,
    is_duplicate_acquisition,
    is_duplicate_round,
)
from app.services.fetcher import fetch_article_text, parse_rss_feed
from app.services.link_discovery import discover_links
from app.services.llm import extract_article
from app.services.normalization import (
    validate_acquisition_extraction,
    validate_extraction,
)

logger = logging.getLogger(__name__)


async def _handle_funding(session, extraction, url, raw):
    """Process a funding extraction. Does NOT commit — caller handles that."""
    validated = validate_extraction(extraction.funding)
    if not validated:
        await mark_source_processed(session, raw.id)
        return {"url": url, "status": "validation_failed"}

    company = await get_or_create_company(session, validated.company)

    # Update sector if LLM provided one and company doesn't have one
    if validated.sector:
        await update_company_sector(session, company.id, validated.sector)

    if await is_duplicate_round(
        session,
        company.id,
        validated.round_type,
        validated.announcement_date,
        validated.amount_usd,
    ):
        await mark_source_processed(session, raw.id)
        return {"url": url, "status": "duplicate_round", "company": company.name}

    investor_ids = []
    for inv_name in validated.investors:
        inv = await get_or_create_investor(session, inv_name)
        investor_ids.append(inv.id)

    await create_funding_round(
        session,
        company_id=company.id,
        round_type=validated.round_type,
        amount_usd=validated.amount_usd,
        valuation_usd=validated.valuation_usd,
        announced_date=validated.announcement_date,
        source_url=url,
        investor_ids=investor_ids,
        confidence_score=validated.confidence_score,
    )

    await mark_source_processed(session, raw.id)

    return {
        "url": url,
        "status": "ingested",
        "event_type": "funding",
        "company": company.name,
        "round_type": validated.round_type,
    }


async def _handle_acquisition(session, extraction, url, raw):
    """Process an acquisition extraction. Does NOT commit — caller handles that."""
    validated = validate_acquisition_extraction(extraction.acquisition)
    if not validated:
        await mark_source_processed(session, raw.id)
        return {"url": url, "status": "validation_failed"}

    acquirer = await get_or_create_company(session, validated.acquirer)
    target = await get_or_create_company(session, validated.target)

    # Update sectors if provided
    if validated.sector:
        await update_company_sector(session, target.id, validated.sector)

    if await is_duplicate_acquisition(
        session,
        acquirer.id,
        target.id,
        validated.announcement_date,
    ):
        await mark_source_processed(session, raw.id)
        return {
            "url": url,
            "status": "duplicate_acquisition",
            "acquirer": acquirer.name,
            "target": target.name,
        }

    await create_acquisition(
        session,
        acquirer_id=acquirer.id,
        target_id=target.id,
        amount_usd=validated.amount_usd,
        announced_date=validated.announcement_date,
        source_url=url,
        confidence_score=validated.confidence_score,
    )

    await mark_source_processed(session, raw.id)

    return {
        "url": url,
        "status": "ingested",
        "event_type": "acquisition",
        "acquirer": acquirer.name,
        "target": target.name,
    }


async def ingest_url(
    session: AsyncSession,
    url: str,
    title: str | None = None,
) -> dict:
    """Process a single URL through the full pipeline.

    All database writes happen in a single transaction — on failure,
    everything is rolled back so no partial data is persisted.
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

    try:
        # 3. Store raw source
        if not existing:
            raw = await create_raw_source(
                session, source_url=url, title=title, content=text[:50000]
            )
        else:
            raw = existing
            if not raw.content:
                raw.content = text[:50000]

        # 4. LLM extraction (multi-event)
        extraction = await extract_article(text)
        if not extraction:
            await mark_source_processed(session, raw.id)
            await session.commit()
            return {"url": url, "status": "extraction_failed"}

        # 5. Branch on event type
        if extraction.event_type == "funding" and extraction.funding:
            result = await _handle_funding(session, extraction, url, raw)
        elif extraction.event_type == "acquisition" and extraction.acquisition:
            result = await _handle_acquisition(session, extraction, url, raw)
        else:
            # Irrelevant article
            await mark_source_processed(session, raw.id)
            result = {"url": url, "status": "irrelevant"}

        # Single commit for the entire pipeline
        await session.commit()
        return result

    except Exception:
        logger.exception("Ingestion failed for %s, rolling back", url)
        await session.rollback()
        return {"url": url, "status": "error"}


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


async def ingest_webpage_source(
    session: AsyncSession,
    page_url: str,
) -> list[dict]:
    """Discover links from a webpage and ingest new articles."""
    entries = await discover_links(page_url)
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
