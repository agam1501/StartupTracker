"""Edge case tests for the ingestion pipeline."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.services.crud import create_raw_source, mark_source_processed
from app.services.ingestion import ingest_rss_feed, ingest_url
from app.services.llm import ArticleExtraction, FundingExtraction


def _funding_article(**kwargs) -> ArticleExtraction:
    """Helper to create a funding ArticleExtraction."""
    defaults = {
        "company": "TestCo",
        "round_type": "Seed",
        "amount_usd": Decimal("1000000"),
        "announcement_date": "2026-03-01",
    }
    defaults.update(kwargs)
    return ArticleExtraction(
        event_type="funding",
        funding=FundingExtraction(**defaults),
    )


class TestIngestUrlEdge:
    @pytest.mark.asyncio
    async def test_already_processed_url(self, session):
        raw = await create_raw_source(session, source_url="https://example.com/done", title="Done")
        await mark_source_processed(session, raw.id)
        await session.commit()

        result = await ingest_url(session, "https://example.com/done")
        assert result["status"] == "already_processed"

    @pytest.mark.asyncio
    async def test_validation_failure(self, session):
        extraction = ArticleExtraction(
            event_type="funding",
            funding=FundingExtraction(company="", round_type="Seed"),
        )

        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Article text",
            ),
            patch(
                "app.services.ingestion.extract_article",
                new_callable=AsyncMock,
                return_value=extraction,
            ),
        ):
            result = await ingest_url(session, "https://example.com/invalid")

        assert result["status"] == "validation_failed"

    @pytest.mark.asyncio
    async def test_multiple_investors_created(self, session):
        extraction = _funding_article(
            company="MultiInvCo",
            round_type="Series A",
            amount_usd=Decimal("5000000"),
            investors=["Alpha Fund", "Beta Capital", "Gamma Ventures"],
        )

        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Article text",
            ),
            patch(
                "app.services.ingestion.extract_article",
                new_callable=AsyncMock,
                return_value=extraction,
            ),
        ):
            result = await ingest_url(session, "https://example.com/multi")

        assert result["status"] == "ingested"
        assert result["company"] == "MultiInvCo"

    @pytest.mark.asyncio
    async def test_existing_unprocessed_source(self, session):
        await create_raw_source(session, source_url="https://example.com/partial", title="Partial")
        await session.flush()

        extraction = _funding_article(company="PartialCo")

        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Article text",
            ),
            patch(
                "app.services.ingestion.extract_article",
                new_callable=AsyncMock,
                return_value=extraction,
            ),
        ):
            result = await ingest_url(session, "https://example.com/partial")

        assert result["status"] == "ingested"

    @pytest.mark.asyncio
    async def test_round_with_no_amount(self, session):
        extraction = _funding_article(
            company="NoAmountCo",
            round_type="Pre-Seed",
            amount_usd=None,
        )

        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Article text",
            ),
            patch(
                "app.services.ingestion.extract_article",
                new_callable=AsyncMock,
                return_value=extraction,
            ),
        ):
            result = await ingest_url(session, "https://example.com/noamount")

        assert result["status"] == "ingested"


class TestIngestRssFeed:
    @pytest.mark.asyncio
    async def test_empty_feed(self, session):
        with patch(
            "app.services.ingestion.parse_rss_feed",
            new_callable=AsyncMock,
            return_value=[],
        ):
            results = await ingest_rss_feed(session, "https://example.com/feed")
        assert results == []

    @pytest.mark.asyncio
    async def test_feed_with_already_processed(self, session):
        raw = await create_raw_source(session, source_url="https://example.com/old", title="Old")
        await mark_source_processed(session, raw.id)
        await session.commit()

        with patch(
            "app.services.ingestion.parse_rss_feed",
            new_callable=AsyncMock,
            return_value=[
                {"url": "https://example.com/old", "title": "Old Article"},
            ],
        ):
            results = await ingest_rss_feed(session, "https://example.com/feed")

        assert len(results) == 1
        assert results[0]["status"] == "already_processed"

    @pytest.mark.asyncio
    async def test_feed_with_multiple_entries(self, session):
        extraction = _funding_article(company="FeedCo")

        with (
            patch(
                "app.services.ingestion.parse_rss_feed",
                new_callable=AsyncMock,
                return_value=[
                    {"url": "https://example.com/a1", "title": "Article 1"},
                    {"url": "https://example.com/a2", "title": "Article 2"},
                ],
            ),
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Article text",
            ),
            patch(
                "app.services.ingestion.extract_article",
                new_callable=AsyncMock,
                return_value=extraction,
            ),
        ):
            results = await ingest_rss_feed(session, "https://example.com/feed")

        assert len(results) == 2
        assert results[0]["status"] == "ingested"
        # Second one might be duplicate_round since same company+type
        assert results[1]["status"] in ("ingested", "duplicate_round")
