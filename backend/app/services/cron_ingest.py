"""Cron entry point for batch ingestion of RSS feeds."""

import asyncio
import logging
import os

from app.services.db import async_session
from app.services.ingestion import ingest_rss_feed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FEED_URLS = [u.strip() for u in os.environ.get("FEED_URLS", "").split(",") if u.strip()]


async def main():
    if not FEED_URLS:
        logger.warning("No FEED_URLS configured, nothing to ingest")
        return

    async with async_session() as session:
        for feed_url in FEED_URLS:
            logger.info("Processing feed: %s", feed_url)
            results = await ingest_rss_feed(session, feed_url)
            for r in results:
                logger.info("  %s -> %s", r["url"], r["status"])


if __name__ == "__main__":
    asyncio.run(main())
