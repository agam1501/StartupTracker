import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm import (
    AcquisitionExtraction,
    ArticleExtraction,
    FundingExtraction,
    _content_hash,
    _extraction_cache,
    extract_article,
    extract_funding,
)


class TestFundingExtraction:
    def test_valid_extraction(self):
        e = FundingExtraction(
            company="Acme",
            round_type="Series A",
            amount_usd=Decimal("10000000"),
            investors=["Sequoia"],
            announcement_date="2026-01-15",
            sector="AI/ML",
            confidence_score=0.95,
        )
        assert e.company == "Acme"
        assert e.round_type == "Series A"
        assert e.sector == "AI/ML"
        assert e.confidence_score == 0.95

    def test_unknown_round_type(self):
        e = FundingExtraction(company="X", round_type="Bridge Round")
        assert e.round_type == "Unknown"

    def test_nullable_fields(self):
        e = FundingExtraction(company="X", round_type="Seed")
        assert e.amount_usd is None
        assert e.valuation_usd is None
        assert e.announcement_date is None
        assert e.investors == []
        assert e.sector is None
        assert e.confidence_score is None
        assert e.revenue_usd is None


class TestAcquisitionExtraction:
    def test_valid(self):
        e = AcquisitionExtraction(
            acquirer="BigCorp",
            target="SmallStartup",
            amount_usd=Decimal("50000000"),
            announcement_date="2026-02-01",
            sector="AI/ML",
            confidence_score=0.88,
        )
        assert e.acquirer == "BigCorp"
        assert e.target == "SmallStartup"
        assert e.confidence_score == 0.88

    def test_minimal(self):
        e = AcquisitionExtraction(acquirer="A", target="B")
        assert e.amount_usd is None
        assert e.sector is None


class TestArticleExtraction:
    def test_funding_event(self):
        e = ArticleExtraction(
            event_type="funding",
            funding=FundingExtraction(company="X", round_type="Seed"),
        )
        assert e.event_type == "funding"
        assert e.funding is not None
        assert e.acquisition is None

    def test_acquisition_event(self):
        e = ArticleExtraction(
            event_type="acquisition",
            acquisition=AcquisitionExtraction(acquirer="A", target="B"),
        )
        assert e.event_type == "acquisition"
        assert e.acquisition is not None

    def test_irrelevant_event(self):
        e = ArticleExtraction(event_type="irrelevant")
        assert e.event_type == "irrelevant"
        assert e.funding is None
        assert e.acquisition is None

    def test_unknown_event_type_defaults_irrelevant(self):
        e = ArticleExtraction(event_type="nonsense")
        assert e.event_type == "irrelevant"


def _mock_llm_response(data: dict):
    """Create a mock httpx response returning the given data."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"choices": [{"message": {"content": json.dumps(data)}}]}
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)
    return mock_client


class TestExtractArticle:
    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        _extraction_cache.clear()
        yield
        _extraction_cache.clear()

    @pytest.mark.asyncio
    async def test_no_api_key(self):
        with patch("app.services.llm.settings.openai_api_key", ""):
            result = await extract_article("some article text")
            assert result is None

    @pytest.mark.asyncio
    async def test_funding_extraction(self):
        mock_data = {
            "event_type": "funding",
            "funding": {
                "company": "TestCo",
                "round_type": "Series A",
                "amount_usd": 5000000,
                "valuation_usd": None,
                "investors": ["VC Fund"],
                "announcement_date": "2026-03-01",
                "sector": "AI/ML",
                "confidence_score": 0.92,
                "revenue_usd": None,
            },
        }
        mock_client = _mock_llm_response(mock_data)

        with (
            patch("app.services.llm.settings.openai_api_key", "test-key"),
            patch(
                "app.services.llm.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            result = await extract_article("Acme raised $5M Series A")

        assert result is not None
        assert result.event_type == "funding"
        assert result.funding is not None
        assert result.funding.company == "TestCo"
        assert result.funding.sector == "AI/ML"
        assert result.funding.confidence_score == 0.92

    @pytest.mark.asyncio
    async def test_acquisition_extraction(self):
        mock_data = {
            "event_type": "acquisition",
            "acquisition": {
                "acquirer": "BigCorp",
                "target": "SmallCo",
                "amount_usd": 100000000,
                "announcement_date": "2026-02-15",
                "sector": "Fintech",
                "confidence_score": 0.85,
            },
        }
        mock_client = _mock_llm_response(mock_data)

        with (
            patch("app.services.llm.settings.openai_api_key", "test-key"),
            patch(
                "app.services.llm.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            result = await extract_article("BigCorp acquires SmallCo")

        assert result is not None
        assert result.event_type == "acquisition"
        assert result.acquisition is not None
        assert result.acquisition.acquirer == "BigCorp"

    @pytest.mark.asyncio
    async def test_irrelevant_article(self):
        mock_data = {"event_type": "irrelevant"}
        mock_client = _mock_llm_response(mock_data)

        with (
            patch("app.services.llm.settings.openai_api_key", "test-key"),
            patch(
                "app.services.llm.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            result = await extract_article("Weather forecast for today")

        assert result is not None
        assert result.event_type == "irrelevant"
        assert result.funding is None
        assert result.acquisition is None

    @pytest.mark.asyncio
    async def test_caching(self):
        cached = ArticleExtraction(
            event_type="funding",
            funding=FundingExtraction(company="Cached", round_type="Seed"),
        )
        with patch("app.services.llm.settings.openai_api_key", "test-key"):
            h = _content_hash("cached article")
            _extraction_cache[h] = cached

            result = await extract_article("cached article")
            assert result is not None
            assert result.funding.company == "Cached"


class TestExtractFunding:
    """Test backward-compatible extract_funding wrapper."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        _extraction_cache.clear()
        yield
        _extraction_cache.clear()

    @pytest.mark.asyncio
    async def test_no_api_key(self):
        with patch("app.services.llm.settings.openai_api_key", ""):
            result = await extract_funding("some article text")
            assert result is None

    @pytest.mark.asyncio
    async def test_successful_extraction(self):
        mock_data = {
            "event_type": "funding",
            "funding": {
                "company": "TestCo",
                "round_type": "Series A",
                "amount_usd": 5000000,
                "valuation_usd": None,
                "investors": ["VC Fund"],
                "announcement_date": "2026-03-01",
                "sector": "SaaS/Enterprise",
                "confidence_score": 0.9,
                "revenue_usd": None,
            },
        }
        mock_client = _mock_llm_response(mock_data)

        with (
            patch("app.services.llm.settings.openai_api_key", "test-key"),
            patch(
                "app.services.llm.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            result = await extract_funding("Acme raised $5M Series A")

        assert result is not None
        assert result.company == "TestCo"
        assert result.round_type == "Series A"
        assert result.amount_usd == Decimal("5000000")

    @pytest.mark.asyncio
    async def test_returns_none_for_acquisition(self):
        mock_data = {
            "event_type": "acquisition",
            "acquisition": {
                "acquirer": "BigCo",
                "target": "SmallCo",
                "amount_usd": 1000000,
            },
        }
        mock_client = _mock_llm_response(mock_data)

        with (
            patch("app.services.llm.settings.openai_api_key", "test-key"),
            patch(
                "app.services.llm.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            result = await extract_funding("BigCo acquires SmallCo")

        assert result is None

    @pytest.mark.asyncio
    async def test_caching(self):
        cached = ArticleExtraction(
            event_type="funding",
            funding=FundingExtraction(company="Cached", round_type="Seed"),
        )
        with patch("app.services.llm.settings.openai_api_key", "test-key"):
            h = _content_hash("cached article")
            _extraction_cache[h] = cached

            result = await extract_funding("cached article")
            assert result is not None
            assert result.company == "Cached"
