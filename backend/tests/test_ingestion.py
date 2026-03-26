from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.services.ingestion import ingest_url
from app.services.llm import FundingExtraction


class TestIngestUrl:
    @pytest.mark.asyncio
    async def test_full_pipeline(self, session):
        extraction = FundingExtraction(
            company="TestCo",
            round_type="Series A",
            amount_usd=Decimal("5000000"),
            investors=["Alpha Fund", "Beta Capital"],
            announcement_date="2026-03-01",
        )

        with (
            patch(
                "app.services.ingestion.fetch_article_text",
                new_callable=AsyncMock,
                return_value="Article about TestCo raising $5M",
            ),
            patch(
                "app.services.ingestion.extract_funding",
                new_callable=AsyncMock,
                return_value=extraction,
            ),
        ):
            result = await ingest_url(session, "https://example.com/article1")

        assert result["status"] == "ingested"
        assert result["company"] == "TestCo"
        assert result["round_type"] == "Series A"

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
                "app.services.ingestion.extract_funding",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            result = await ingest_url(session, "https://example.com/nodata")

        assert result["status"] == "extraction_failed"

    @pytest.mark.asyncio
    async def test_duplicate_round_detection(self, session):
        extraction = FundingExtraction(
            company="DupCo",
            round_type="Seed",
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
            # First ingestion
            r1 = await ingest_url(session, "https://example.com/dup1")
            assert r1["status"] == "ingested"

            # Second ingestion with same company+round
            r2 = await ingest_url(session, "https://example.com/dup2")
            assert r2["status"] == "duplicate_round"
