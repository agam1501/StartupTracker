"""Discover article links from VC firm press/news pages."""

import logging
import re
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

# URL path patterns that suggest an article or press release
ARTICLE_PATTERNS = [
    re.compile(r"/blog/"),
    re.compile(r"/press/"),
    re.compile(r"/news/"),
    re.compile(r"/announcements?/"),
    re.compile(r"/perspectives?/"),
    re.compile(r"/noteworthy/"),
    re.compile(r"/newsroom/"),
    re.compile(r"/portfolio/"),
    re.compile(r"/20\d{2}/"),  # Year in URL (2000-2099)
]

# Paths to exclude (navigation, assets, etc.)
EXCLUDE_PATTERNS = [
    re.compile(r"\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|pdf)(\?|$)", re.IGNORECASE),
    re.compile(r"/(login|signup|register|contact|about|careers|privacy|terms)(/|$)"),
    re.compile(r"^#"),
    re.compile(r"^mailto:"),
    re.compile(r"^javascript:"),
]


def _is_article_url(url: str, base_domain: str) -> bool:
    """Check if a URL looks like an article based on path heuristics."""
    parsed = urlparse(url)

    # Must be same domain or subdomain
    if not parsed.netloc.endswith(base_domain):
        return False

    path = parsed.path.lower()

    # Exclude non-article resources
    for pattern in EXCLUDE_PATTERNS:
        if pattern.search(url):
            return False

    # Must not be the root or a very short path
    if len(path.rstrip("/")) < 5:
        return False

    # Check article patterns
    for pattern in ARTICLE_PATTERNS:
        if pattern.search(path):
            return True

    return False


def _extract_base_domain(url: str) -> str:
    """Extract the base domain from a URL (e.g., 'a16z.com' from 'https://a16z.com/path')."""
    parsed = urlparse(url)
    parts = parsed.netloc.split(".")
    # Handle cases like www.example.com -> example.com
    if len(parts) > 2 and parts[0] == "www":
        return ".".join(parts[1:])
    return parsed.netloc


async def discover_links(page_url: str, max_links: int = 50) -> list[dict[str, str]]:
    """Fetch a webpage and extract article-like links.

    Returns a list of {url, title} dicts, similar to parse_rss_feed output.
    """
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(page_url, headers={"User-Agent": "StartupTracker/0.1"})
            resp.raise_for_status()
            html = resp.text
    except httpx.HTTPError as e:
        logger.warning("Failed to fetch page %s: %s", page_url, e)
        return []

    return extract_links_from_html(html, page_url, max_links)


def extract_links_from_html(html: str, base_url: str, max_links: int = 50) -> list[dict[str, str]]:
    """Extract article-like links from HTML content."""
    base_domain = _extract_base_domain(base_url)

    # Simple regex to find <a> tags with href
    link_pattern = re.compile(
        r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )

    seen_urls: set[str] = set()
    results: list[dict[str, str]] = []

    for match in link_pattern.finditer(html):
        href = match.group(1).strip()
        raw_title = match.group(2).strip()

        # Resolve relative URLs
        full_url = urljoin(base_url, href)

        # Normalize
        parsed = urlparse(full_url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        normalized = normalized.rstrip("/")

        if normalized in seen_urls:
            continue

        if not _is_article_url(full_url, base_domain):
            continue

        seen_urls.add(normalized)

        # Clean title: strip HTML tags
        title = re.sub(r"<[^>]+>", "", raw_title).strip()
        title = re.sub(r"\s+", " ", title)

        results.append({"url": full_url, "title": title or None})

        if len(results) >= max_links:
            break

    return results
