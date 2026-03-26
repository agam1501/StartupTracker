"""Sector taxonomy for company classification."""

SECTORS: set[str] = {
    "AI/ML",
    "Fintech",
    "Healthcare/Biotech",
    "SaaS/Enterprise",
    "E-Commerce/Retail",
    "Climate/Energy",
    "Cybersecurity",
    "EdTech",
    "Real Estate/PropTech",
    "Transportation/Logistics",
    "Media/Entertainment",
    "Food/Agriculture",
    "Hardware/Robotics",
    "Crypto/Web3",
    "Other",
}

SECTORS_LIST: list[str] = sorted(SECTORS)


def validate_sector(value: str | None) -> str | None:
    """Validate a sector value. Returns None for invalid/empty values."""
    if not value:
        return None
    # Case-insensitive match
    lookup = {s.lower(): s for s in SECTORS}
    return lookup.get(value.lower())
