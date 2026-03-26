"""Edge case tests for LLM extraction."""

import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm import FundingExtraction, _extraction_cache, extract_funding


class TestFundingExtractionEdge:
    def test_zero_amount(self):
        e = FundingExtraction(company="X", round_type="Seed", amount_usd=Decimal("0"))
        assert e.amount_usd == Decimal("0")

    def test_very_large_amount(self):
        e = FundingExtraction(
            company="X",
            round_type="Seed",
            amount_usd=Decimal("100000000000"),
        )
        assert e.amount_usd == Decimal("100000000000")

    def test_many_investors(self):
        investors = [f"Fund {i}" for i in range(20)]
        e = FundingExtraction(company="X", round_type="Seed", investors=investors)
        assert len(e.investors) == 20

    def test_round_type_case_normalization(self):
        """FundingExtraction validator normalizes unknown types to 'Unknown'."""
        e = FundingExtraction(company="X", round_type="series A")
        # The validator maps lowercase "series a" via the known types
        # but the model validator uses its own mapping, not normalize_round_type
        assert e.round_type == "Unknown"


class TestExtractFundingEdge:
    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        _extraction_cache.clear()
        yield
        _extraction_cache.clear()

    @pytest.mark.asyncio
    async def test_malformed_json_response(self):
        """LLM returns invalid JSON - should return None."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"choices": [{"message": {"content": "not valid json"}}]}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with (
            patch("app.services.llm.OPENAI_API_KEY", "test-key"),
            patch("app.services.llm.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await extract_funding("article text")

        assert result is None

    @pytest.mark.asyncio
    async def test_api_http_error_returns_none(self):
        """HTTP error from OpenAI should return None after retries."""
        import httpx as _httpx

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            side_effect=_httpx.HTTPStatusError(
                "Server Error",
                request=_httpx.Request("POST", "http://test"),
                response=_httpx.Response(500),
            )
        )

        with (
            patch("app.services.llm.OPENAI_API_KEY", "test-key"),
            patch("app.services.llm.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await extract_funding("article text http error")

        assert result is None

    @pytest.mark.asyncio
    async def test_empty_text(self):
        """Empty article text with no API key should return None."""
        with patch("app.services.llm.OPENAI_API_KEY", ""):
            result = await extract_funding("")
            assert result is None

    @pytest.mark.asyncio
    async def test_partial_json_response(self):
        """LLM returns valid JSON but missing required fields."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        # Missing 'company' field
        mock_resp.json.return_value = {
            "choices": [
                {"message": {"content": json.dumps({"round_type": "Seed", "amount_usd": 1000000})}}
            ]
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with (
            patch("app.services.llm.OPENAI_API_KEY", "test-key"),
            patch("app.services.llm.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await extract_funding("article text")

        # Should return None since company is required
        assert result is None
