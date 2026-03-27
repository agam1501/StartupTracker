"""Cron entry point for batch ingestion of RSS feeds and webpage sources."""

import asyncio
import logging

from app.config import settings
from app.services.crud import get_active_sources, mark_source_checked
from app.services.db import async_session
from app.services.ingestion import ingest_rss_feed, ingest_webpage_source

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FEED_URLS = [u.strip() for u in settings.feed_urls.split(",") if u.strip()]


async def main():
    async with async_session() as session:
        # DB-driven sources take priority
        db_sources = await get_active_sources(session)

        if db_sources:
            for source in db_sources:
                logger.info(
                    "Processing %s source: %s (%s)",
                    source.source_type,
                    source.name,
                    source.url,
                )
                if source.source_type == "rss":
                    results = await ingest_rss_feed(session, source.url)
                elif source.source_type == "webpage":
                    results = await ingest_webpage_source(session, source.url)
                else:
                    logger.warning("Unknown source type: %s", source.source_type)
                    continue

                for r in results:
                    logger.info("  %s -> %s", r["url"], r["status"])
                await mark_source_checked(session, source.id)
                await session.commit()
        elif FEED_URLS:
            # Fallback to env var
            logger.info("No DB sources found, falling back to FEED_URLS env var")
            for feed_url in FEED_URLS:
                logger.info("Processing feed: %s", feed_url)
                results = await ingest_rss_feed(session, feed_url)
                for r in results:
                    logger.info("  %s -> %s", r["url"], r["status"])
        else:
            logger.warning("No sources configured (DB or FEED_URLS), nothing to ingest")


if __name__ == "__main__":
    asyncio.run(main())
