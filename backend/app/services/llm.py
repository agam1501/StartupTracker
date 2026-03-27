"""LLM-based structured extraction of funding/acquisition data from article text."""

import hashlib
import json
import logging
from collections import OrderedDict
from datetime import date
from decimal import Decimal

import httpx
from pydantic import BaseModel, field_validator

from app.config import settings

logger = logging.getLogger(__name__)

# LRU-style cache keyed by content hash, capped at settings.llm_cache_max_size
_extraction_cache: OrderedDict[str, "ArticleExtraction | None"] = OrderedDict()

SYSTEM_PROMPT = """You are a structured data extraction system.

Analyze the given article and classify it as one of:
- "funding" - a startup funding round announcement
- "acquisition" - a company acquisition/merger announcement
- "irrelevant" - not about funding or acquisitions

Rules:
- Only extract explicitly stated information
- Do NOT guess or infer missing values
- If unknown, return null
- Return valid JSON only
- Normalize currency to USD if explicitly convertible
- Provide a confidence_score (0.0-1.0) for your extraction
- Classify the company into one of these sectors: AI/ML, Fintech, \
Healthcare/Biotech, SaaS/Enterprise, E-Commerce/Retail, Climate/Energy, \
Cybersecurity, EdTech, Real Estate/PropTech, Transportation/Logistics, \
Media/Entertainment, Food/Agriculture, Hardware/Robotics, Crypto/Web3, Other
- Do not include explanations"""

USER_PROMPT_TEMPLATE = """Analyze the following article and extract structured data:

ARTICLE:
{article_text}

First determine the event_type: "funding", "acquisition", or "irrelevant".

If "funding", return:
{{
  "event_type": "funding",
  "funding": {{
    "company": "string",
    "round_type": "Seed | Pre-Seed | Series A | Series B | Series C | Series D | Unknown",
    "amount_usd": number | null,
    "valuation_usd": number | null,
    "investors": ["string"],
    "announcement_date": "YYYY-MM-DD" | null,
    "sector": "sector name" | null,
    "confidence_score": number (0.0-1.0),
    "revenue_usd": number | null
  }}
}}

If "acquisition", return:
{{
  "event_type": "acquisition",
  "acquisition": {{
    "acquirer": "string",
    "target": "string",
    "amount_usd": number | null,
    "announcement_date": "YYYY-MM-DD" | null,
    "sector": "sector name" | null,
    "confidence_score": number (0.0-1.0)
  }}
}}

If "irrelevant", return:
{{
  "event_type": "irrelevant"
}}"""


ALLOWED_ROUND_TYPES = {
    "Pre-Seed",
    "Seed",
    "Series A",
    "Series B",
    "Series C",
    "Series D",
    "Unknown",
}


class FundingExtraction(BaseModel):
    company: str
    round_type: str
    amount_usd: Decimal | None = None
    valuation_usd: Decimal | None = None
    investors: list[str] = []
    announcement_date: date | None = None
    sector: str | None = None
    confidence_score: float | None = None
    revenue_usd: Decimal | None = None

    @field_validator("round_type")
    @classmethod
    def validate_round_type(cls, v: str) -> str:
        return v if v in ALLOWED_ROUND_TYPES else "Unknown"


class AcquisitionExtraction(BaseModel):
    acquirer: str
    target: str
    amount_usd: Decimal | None = None
    announcement_date: date | None = None
    sector: str | None = None
    confidence_score: float | None = None


class ArticleExtraction(BaseModel):
    event_type: str
    funding: FundingExtraction | None = None
    acquisition: AcquisitionExtraction | None = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        allowed = {"funding", "acquisition", "irrelevant"}
        return v if v in allowed else "irrelevant"


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _cache_put(key: str, value: "ArticleExtraction | None") -> None:
    """Insert into the LRU cache, evicting oldest entry if full."""
    _extraction_cache[key] = value
    if len(_extraction_cache) > settings.llm_cache_max_size:
        _extraction_cache.popitem(last=False)


async def _call_llm(
    article_text: str,
    *,
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 2,
) -> dict | None:
    """Call LLM API and return parsed JSON dict, or None on failure."""
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set, skipping extraction")
        return None

    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.openai_timeout) as client:
                resp = await client.post(
                    f"{settings.openai_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()

            raw = resp.json()["choices"][0]["message"]["content"]
            return json.loads(raw)

        except (
            httpx.HTTPError,
            json.JSONDecodeError,
            KeyError,
            ValueError,
        ) as e:
            logger.warning("Extraction attempt %d failed: %s", attempt + 1, e)
            if attempt == max_retries:
                return None

    return None


async def extract_article(
    article_text: str,
    *,
    max_retries: int = 2,
) -> ArticleExtraction | None:
    """Extract structured data from an article, detecting event type.

    Returns ArticleExtraction with event_type and type-specific data,
    or None if extraction fails entirely.
    Results are cached by content hash.
    """
    h = _content_hash(article_text)
    if h in _extraction_cache:
        return _extraction_cache[h]

    user_prompt = USER_PROMPT_TEMPLATE.format(article_text=article_text[:8000])
    data = await _call_llm(
        article_text,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_retries=max_retries,
    )

    if not data:
        _cache_put(h, None)
        return None

    try:
        result = ArticleExtraction.model_validate(data)
        _cache_put(h, result)
        return result
    except ValueError as e:
        logger.warning("Failed to parse extraction: %s", e)
        _cache_put(h, None)
        return None


async def extract_funding(
    article_text: str,
    *,
    max_retries: int = 2,
) -> FundingExtraction | None:
    """Backward-compatible wrapper that extracts funding data only.

    Uses the new multi-event extraction under the hood but only returns
    FundingExtraction if the article is about funding.
    """
    result = await extract_article(article_text, max_retries=max_retries)
    if result and result.event_type == "funding" and result.funding:
        return result.funding
    return None
