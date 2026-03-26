"""Edge case tests for the ingestion pipeline."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.services.crud import create_raw_source, mark_source_processed
from app.services.ingestion import ingest_rss_feed, ingest_url
from app.services.llm import FundingExtraction


class TestIngestUrlEdge:
    @pytest.mark.asyncio
    async def test_already_processed_url(self, session):
        """URLs already marked processed should be skipped."""
        raw = await create_raw_source(session, source_url="https://example.com/done", title="Done")
        await mark_source_processed(session, raw.id)
        await session.commit()

        result = await ingest_url(session, "https://example.com/done")
        assert result["status"] == "already_processed"

    @pytest.mark.asyncio
    async def test_validation_failure(self, session):
        """Extraction that fails validation (empty company) should return validation_failed."""
        extraction = FundingExtraction(
            company="",  # Empty company will fail validation
            round_type="Seed",
        )

        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Article text",
            ),
            patch(
                "app.services.ingestion.extract_funding",
                new_callable=AsyncMock,
                return_value=extraction,
            ),
        ):
            result = await ingest_url(session, "https://example.com/invalid")

        assert result["status"] == "validation_failed"

    @pytest.mark.asyncio
    async def test_multiple_investors_created(self, session):
        """Pipeline should create multiple investors for a single round."""
        extraction = FundingExtraction(
            company="MultiInvCo",
            round_type="Series A",
            amount_usd=Decimal("5000000"),
            investors=["Alpha Fund", "Beta Capital", "Gamma Ventures"],
            announcement_date="2026-03-01",
        )

        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Article text",
            ),
            patch(
                "app.services.ingestion.extract_funding",
                new_callable=AsyncMock,
                return_value=extraction,
            ),
        ):
            result = await ingest_url(session, "https://example.com/multi")

        assert result["status"] == "ingested"
        assert result["company"] == "MultiInvCo"

    @pytest.mark.asyncio
    async def test_existing_unprocessed_source(self, session):
        """A source that exists but is unprocessed should still go through pipeline."""
        await create_raw_source(session, source_url="https://example.com/partial", title="Partial")
        await session.flush()

        extraction = FundingExtraction(
            company="PartialCo",
            round_type="Seed",
            amount_usd=Decimal("1000000"),
            announcement_date="2026-03-01",
        )

        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Article text",
            ),
            patch(
                "app.services.ingestion.extract_funding",
                new_callable=AsyncMock,
                return_value=extraction,
            ),
        ):
            result = await ingest_url(session, "https://example.com/partial")

        assert result["status"] == "ingested"

    @pytest.mark.asyncio
    async def test_round_with_no_amount(self, session):
        """Rounds with no amount should still be created."""
        extraction = FundingExtraction(
            company="NoAmountCo",
            round_type="Pre-Seed",
            announcement_date="2026-03-01",
        )

        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Article text",
            ),
            patch(
                "app.services.ingestion.extract_funding",
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
        extraction = FundingExtraction(
            company="FeedCo",
            round_type="Seed",
            amount_usd=Decimal("1000000"),
            announcement_date="2026-03-01",
        )

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
                "app.services.ingestion.extract_funding",
                new_callable=AsyncMock,
                return_value=extraction,
            ),
        ):
            results = await ingest_rss_feed(session, "https://example.com/feed")

        assert len(results) == 2
        assert results[0]["status"] == "ingested"
        # Second one might be duplicate_round since same company+type
        assert results[1]["status"] in ("ingested", "duplicate_round")
