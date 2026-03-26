from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.fetcher import fetch_article_text, parse_rss_feed


class TestFetchArticleText:
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = lambda: None
        mock_resp.text = "<html><body><p>Article content here</p></body></html>"

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("app.services.fetcher.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_article_text("https://example.com/article")

        assert result is not None
        assert "Article content here" in result

    @pytest.mark.asyncio
    async def test_fetch_failure(self):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "404", request=httpx.Request("GET", "http://x"), response=httpx.Response(404)
            )
        )

        with patch("app.services.fetcher.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_article_text("https://example.com/missing")

        assert result is None


class TestParseRssFeed:
    @pytest.mark.asyncio
    async def test_parse_rss2(self):
        rss_xml = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Startup raises $10M</title>
                    <link>https://example.com/1</link>
                </item>
                <item>
                    <title>Another funding round</title>
                    <link>https://example.com/2</link>
                </item>
            </channel>
        </rss>"""

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = lambda: None
        mock_resp.text = rss_xml

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("app.services.fetcher.httpx.AsyncClient", return_value=mock_client):
            entries = await parse_rss_feed("https://example.com/feed")

        assert len(entries) == 2
        assert entries[0]["url"] == "https://example.com/1"
        assert entries[0]["title"] == "Startup raises $10M"

    @pytest.mark.asyncio
    async def test_fetch_failure(self):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "500", request=httpx.Request("GET", "http://x"), response=httpx.Response(500)
            )
        )

        with patch("app.services.fetcher.httpx.AsyncClient", return_value=mock_client):
            entries = await parse_rss_feed("https://example.com/feed")

        assert entries == []
