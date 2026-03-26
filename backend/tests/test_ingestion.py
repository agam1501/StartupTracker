from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.services.ingestion import ingest_url
from app.services.llm import (
    AcquisitionExtraction,
    ArticleExtraction,
    FundingExtraction,
)


def _funding_extraction(**kwargs) -> ArticleExtraction:
    """Helper to create a funding ArticleExtraction."""
    defaults = {
        "company": "TestCo",
        "round_type": "Series A",
        "amount_usd": Decimal("5000000"),
        "investors": ["Alpha Fund"],
        "announcement_date": "2026-03-01",
        "sector": "AI/ML",
        "confidence_score": 0.9,
    }
    defaults.update(kwargs)
    return ArticleExtraction(
        event_type="funding",
        funding=FundingExtraction(**defaults),
    )


def _acquisition_extraction(**kwargs) -> ArticleExtraction:
    """Helper to create an acquisition ArticleExtraction."""
    defaults = {
        "acquirer": "BigCorp",
        "target": "SmallStartup",
        "amount_usd": Decimal("50000000"),
        "announcement_date": "2026-02-15",
        "sector": "Fintech",
        "confidence_score": 0.85,
    }
    defaults.update(kwargs)
    return ArticleExtraction(
        event_type="acquisition",
        acquisition=AcquisitionExtraction(**defaults),
    )


def _irrelevant_extraction() -> ArticleExtraction:
    return ArticleExtraction(event_type="irrelevant")


class TestIngestUrl:
    @pytest.mark.asyncio
    async def test_full_pipeline_funding(self, session):
        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Article about TestCo raising $5M",
            ),
            patch(
                "app.services.ingestion.extract_article",
                new_callable=AsyncMock,
                return_value=_funding_extraction(),
            ),
        ):
            result = await ingest_url(session, "https://example.com/article1")

        assert result["status"] == "ingested"
        assert result["event_type"] == "funding"
        assert result["company"] == "TestCo"
        assert result["round_type"] == "Series A"

    @pytest.mark.asyncio
    async def test_full_pipeline_acquisition(self, session):
        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="BigCorp acquires SmallStartup for $50M",
            ),
            patch(
                "app.services.ingestion.extract_article",
                new_callable=AsyncMock,
                return_value=_acquisition_extraction(),
            ),
        ):
            result = await ingest_url(session, "https://example.com/acq1")

        assert result["status"] == "ingested"
        assert result["event_type"] == "acquisition"
        assert result["acquirer"] == "BigCorp"
        assert result["target"] == "SmallStartup"

    @pytest.mark.asyncio
    async def test_irrelevant_article(self, session):
        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Weather forecast",
            ),
            patch(
                "app.services.ingestion.extract_article",
                new_callable=AsyncMock,
                return_value=_irrelevant_extraction(),
            ),
        ):
            result = await ingest_url(session, "https://example.com/weather")

        assert result["status"] == "irrelevant"

    @pytest.mark.asyncio
    async def test_fetch_failure(self, session):
        with patch(
            "app.services.ingestion.fetch_article_text",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await ingest_url(session, "https://example.com/bad")

        assert result["status"] == "fetch_failed"

    @pytest.mark.asyncio
    async def test_extraction_failure(self, session):
        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Some text",
            ),
            patch(
                "app.services.ingestion.extract_article",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            result = await ingest_url(session, "https://example.com/nodata")

        assert result["status"] == "extraction_failed"

    @pytest.mark.asyncio
    async def test_duplicate_round_detection(self, session):
        extraction = _funding_extraction(
            company="DupCo", round_type="Seed", announcement_date="2026-03-01"
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
            r1 = await ingest_url(session, "https://example.com/dup1")
            assert r1["status"] == "ingested"

            r2 = await ingest_url(session, "https://example.com/dup2")
            assert r2["status"] == "duplicate_round"

    @pytest.mark.asyncio
    async def test_duplicate_acquisition_detection(self, session):
        extraction = _acquisition_extraction()

        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Acquisition article",
            ),
            patch(
                "app.services.ingestion.extract_article",
                new_callable=AsyncMock,
                return_value=extraction,
            ),
        ):
            r1 = await ingest_url(session, "https://example.com/acq-dup1")
            assert r1["status"] == "ingested"

            r2 = await ingest_url(session, "https://example.com/acq-dup2")
            assert r2["status"] == "duplicate_acquisition"
