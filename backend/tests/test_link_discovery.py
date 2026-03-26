"""Tests for the link discovery service."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.link_discovery import (
    _extract_base_domain,
    _is_article_url,
    discover_links,
    extract_links_from_html,
)


class TestExtractBaseDomain:
    def test_simple_domain(self):
        assert _extract_base_domain("https://a16z.com/announcements/") == "a16z.com"

    def test_www_prefix(self):
        assert _extract_base_domain("https://www.sequoiacap.com/build/") == "sequoiacap.com"

    def test_subdomain(self):
        assert _extract_base_domain("https://news.crunchbase.com/feed/") == "news.crunchbase.com"


class TestIsArticleUrl:
    def test_blog_url(self):
        assert _is_article_url("https://a16z.com/blog/some-article", "a16z.com") is True

    def test_news_url(self):
        assert _is_article_url("https://a16z.com/news/funding-round", "a16z.com") is True

    def test_year_url(self):
        assert _is_article_url("https://a16z.com/2026/03/article", "a16z.com") is True

    def test_press_url(self):
        assert _is_article_url("https://a16z.com/press/new-fund", "a16z.com") is True

    def test_announcements_url(self):
        url = "https://a16z.com/announcements/series-b"
        assert _is_article_url(url, "a16z.com") is True

    def test_different_domain_rejected(self):
        assert _is_article_url("https://other.com/blog/article", "a16z.com") is False

    def test_root_url_rejected(self):
        assert _is_article_url("https://a16z.com/", "a16z.com") is False

    def test_asset_url_rejected(self):
        assert _is_article_url("https://a16z.com/blog/image.png", "a16z.com") is False

    def test_login_rejected(self):
        assert _is_article_url("https://a16z.com/login/", "a16z.com") is False

    def test_short_path_rejected(self):
        assert _is_article_url("https://a16z.com/ab", "a16z.com") is False

    def test_no_article_pattern(self):
        assert _is_article_url("https://a16z.com/team/partner", "a16z.com") is False


class TestExtractLinksFromHtml:
    def test_extracts_article_links(self):
        html = """
        <html><body>
        <a href="/blog/series-a-announcement">Series A for TestCo</a>
        <a href="/blog/market-outlook-2026">Market Outlook 2026</a>
        <a href="/about">About Us</a>
        </body></html>
        """
        results = extract_links_from_html(html, "https://a16z.com/announcements/")
        assert len(results) == 2
        assert results[0]["url"] == "https://a16z.com/blog/series-a-announcement"
        assert results[0]["title"] == "Series A for TestCo"

    def test_deduplicates_links(self):
        html = """
        <a href="/blog/article-1">First</a>
        <a href="/blog/article-1">Duplicate</a>
        """
        results = extract_links_from_html(html, "https://example.com/news/")
        assert len(results) == 1

    def test_resolves_relative_urls(self):
        html = '<a href="/news/funding">Funding News</a>'
        results = extract_links_from_html(html, "https://example.com/press/")
        assert results[0]["url"] == "https://example.com/news/funding"

    def test_respects_max_links(self):
        links = "".join(f'<a href="/blog/article-{i}">Article {i}</a>' for i in range(100))
        html = f"<html><body>{links}</body></html>"
        results = extract_links_from_html(html, "https://example.com/", max_links=5)
        assert len(results) == 5

    def test_strips_html_from_title(self):
        html = '<a href="/blog/test"><span class="bold">Bold Title</span></a>'
        results = extract_links_from_html(html, "https://example.com/")
        assert results[0]["title"] == "Bold Title"

    def test_empty_html(self):
        results = extract_links_from_html("", "https://example.com/")
        assert results == []

    def test_no_matching_links(self):
        html = '<a href="/about">About</a><a href="/contact">Contact</a>'
        results = extract_links_from_html(html, "https://example.com/")
        assert results == []


class TestDiscoverLinks:
    @pytest.mark.asyncio
    async def test_successful_discovery(self):
        html = '<a href="/blog/new-fund">New Fund Announcement</a>'
        mock_resp = AsyncMock()
        mock_resp.text = html
        mock_resp.raise_for_status = lambda: None

        with patch("app.services.link_discovery.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value.get = AsyncMock(return_value=mock_resp)

            results = await discover_links("https://a16z.com/announcements/")

        assert len(results) == 1
        assert results[0]["title"] == "New Fund Announcement"

    @pytest.mark.asyncio
    async def test_fetch_failure_returns_empty(self):
        import httpx

        with patch("app.services.link_discovery.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value.get = AsyncMock(
                side_effect=httpx.HTTPError("Connection failed")
            )

            results = await discover_links("https://broken.com/news/")

        assert results == []
