"""Validate and normalize LLM extraction output."""

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from app.services.llm import FundingExtraction


def normalize_company_name(name: str) -> str:
    """Lowercase, strip suffixes (Inc, LLC, etc.), collapse whitespace."""
    n = name.lower().strip()
    n = re.sub(r"\b(inc|llc|ltd|corp|co|plc)\.?\b", "", n)
    n = re.sub(r"[^\w\s]", "", n)
    return re.sub(r"\s+", " ", n).strip()


def normalize_investor_name(name: str) -> str:
    """Lowercase, collapse whitespace."""
    return re.sub(r"\s+", " ", name.strip().lower())


ROUND_TYPE_MAP = {
    "pre-seed": "Pre-Seed",
    "preseed": "Pre-Seed",
    "seed": "Seed",
    "series a": "Series A",
    "series b": "Series B",
    "series c": "Series C",
    "series d": "Series D",
}


def normalize_round_type(raw: str) -> str:
    """Map common variations to canonical round types."""
    return ROUND_TYPE_MAP.get(raw.lower().strip(), "Unknown")


def parse_amount(val) -> Decimal | None:
    """Parse an amount, returning None if invalid."""
    if val is None:
        return None
    try:
        d = Decimal(str(val))
        return d if d > 0 else None
    except (InvalidOperation, ValueError):
        return None


def parse_date(val) -> date | None:
    """Parse a YYYY-MM-DD date string."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val))
    except (ValueError, TypeError):
        return None


def validate_extraction(extraction: FundingExtraction) -> FundingExtraction | None:
    """Validate and normalize an extraction. Returns None if invalid."""
    if not extraction.company or not extraction.company.strip():
        return None

    return FundingExtraction(
        company=extraction.company.strip(),
        round_type=normalize_round_type(extraction.round_type),
        amount_usd=parse_amount(extraction.amount_usd),
        valuation_usd=parse_amount(extraction.valuation_usd),
        investors=[i.strip() for i in extraction.investors if i.strip()],
        announcement_date=parse_date(extraction.announcement_date),
    )
