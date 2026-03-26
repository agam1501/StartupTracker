"""LLM-based structured extraction of funding data from article text."""

import hashlib
import json
import logging
import os
from datetime import date
from decimal import Decimal

import httpx
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Simple in-memory cache keyed by content hash
_extraction_cache: dict[str, "FundingExtraction | None"] = {}

SYSTEM_PROMPT = """You are a structured data extraction system.

Extract funding information from the given article.

Rules:
- Only extract explicitly stated information
- Do NOT guess or infer missing values
- If unknown, return null
- Return valid JSON only
- Normalize currency to USD if explicitly convertible
- Do not include explanations"""

USER_PROMPT_TEMPLATE = """Extract funding data from the following article:

ARTICLE:
{article_text}

Return JSON with this exact schema:
{{
  "company": "string",
  "round_type": "Seed | Pre-Seed | Series A | Series B | Series C | Series D | Unknown",
  "amount_usd": number | null,
  "valuation_usd": number | null,
  "investors": ["string"],
  "announcement_date": "YYYY-MM-DD" | null
}}"""


class FundingExtraction(BaseModel):
    company: str
    round_type: str
    amount_usd: Decimal | None = None
    valuation_usd: Decimal | None = None
    investors: list[str] = []
    announcement_date: date | None = None

    @field_validator("round_type")
    @classmethod
    def validate_round_type(cls, v: str) -> str:
        allowed = {
            "Pre-Seed",
            "Seed",
            "Series A",
            "Series B",
            "Series C",
            "Series D",
            "Unknown",
        }
        return v if v in allowed else "Unknown"


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


async def extract_funding(
    article_text: str,
    *,
    max_retries: int = 2,
) -> FundingExtraction | None:
    """Call LLM API to extract structured funding data from article text.

    Returns None if extraction fails or article has no funding info.
    Results are cached by content hash.
    """
    h = _content_hash(article_text)
    if h in _extraction_cache:
        return _extraction_cache[h]

    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set, skipping extraction")
        return None

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(article_text=article_text[:8000]),
            },
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{OPENAI_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()

            raw = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(raw)
            result = FundingExtraction.model_validate(data)
            _extraction_cache[h] = result
            return result

        except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Extraction attempt %d failed: %s", attempt + 1, e)
            if attempt == max_retries:
                _extraction_cache[h] = None
                return None

    return None
