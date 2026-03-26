import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm import FundingExtraction, _extraction_cache, extract_funding


class TestFundingExtraction:
    def test_valid_extraction(self):
        e = FundingExtraction(
            company="Acme",
            round_type="Series A",
            amount_usd=Decimal("10000000"),
            investors=["Sequoia"],
            announcement_date="2026-01-15",
        )
        assert e.company == "Acme"
        assert e.round_type == "Series A"

    def test_unknown_round_type(self):
        e = FundingExtraction(company="X", round_type="Bridge Round")
        assert e.round_type == "Unknown"

    def test_nullable_fields(self):
        e = FundingExtraction(company="X", round_type="Seed")
        assert e.amount_usd is None
        assert e.valuation_usd is None
        assert e.announcement_date is None
        assert e.investors == []


class TestExtractFunding:
    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        _extraction_cache.clear()
        yield
        _extraction_cache.clear()

    @pytest.mark.asyncio
    async def test_no_api_key(self):
        with patch("app.services.llm.OPENAI_API_KEY", ""):
            result = await extract_funding("some article text")
            assert result is None

    @pytest.mark.asyncio
    async def test_successful_extraction(self):
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "company": "TestCo",
                                "round_type": "Series A",
                                "amount_usd": 5000000,
                                "valuation_usd": None,
                                "investors": ["VC Fund"],
                                "announcement_date": "2026-03-01",
                            }
                        )
                    }
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = mock_response

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with (
            patch("app.services.llm.OPENAI_API_KEY", "test-key"),
            patch("app.services.llm.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await extract_funding("Acme raised $5M Series A")

        assert result is not None
        assert result.company == "TestCo"
        assert result.round_type == "Series A"
        assert result.amount_usd == Decimal("5000000")

    @pytest.mark.asyncio
    async def test_caching(self):
        cached = FundingExtraction(company="Cached", round_type="Seed")
        with patch("app.services.llm.OPENAI_API_KEY", "test-key"):
            # Pre-populate cache
            from app.services.llm import _content_hash

            h = _content_hash("cached article")
            _extraction_cache[h] = cached

            result = await extract_funding("cached article")
            assert result is not None
            assert result.company == "Cached"
