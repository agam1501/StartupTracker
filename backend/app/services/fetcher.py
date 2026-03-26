"""Fetch articles from URLs and extract text content."""

import logging
import xml.etree.ElementTree as ET

import httpx

logger = logging.getLogger(__name__)


async def fetch_article_text(url: str) -> str | None:
    """Fetch a URL and extract the main article text.

    Uses trafilatura if available, falls back to raw HTML.
    """
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "StartupTracker/0.1"})
            resp.raise_for_status()
            html = resp.text
    except httpx.HTTPError as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None

    try:
        import trafilatura

        text = trafilatura.extract(html)
        if text:
            return text
    except ImportError:
        logger.debug("trafilatura not installed, using raw HTML")

    # Fallback: strip tags naively
    import re

    clean = re.sub(r"<[^>]+>", " ", html)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:10000] if clean else None


async def parse_rss_feed(url: str) -> list[dict[str, str]]:
    """Parse an RSS/Atom feed and return list of {url, title} dicts."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "StartupTracker/0.1"})
            resp.raise_for_status()
            xml_text = resp.text
    except httpx.HTTPError as e:
        logger.warning("Failed to fetch RSS %s: %s", url, e)
        return []

    entries = []
    try:
        root = ET.fromstring(xml_text)
        # RSS 2.0
        for item in root.iter("item"):
            link = item.findtext("link", "").strip()
            title = item.findtext("title", "").strip()
            if link:
                entries.append({"url": link, "title": title})
        # Atom
        if not entries:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall(".//atom:entry", ns):
                link_el = entry.find("atom:link[@href]", ns)
                title = entry.findtext("atom:title", "", ns).strip()
                if link_el is not None:
                    entries.append({"url": link_el.get("href", ""), "title": title})
    except ET.ParseError as e:
        logger.warning("Failed to parse RSS %s: %s", url, e)

    return entries
