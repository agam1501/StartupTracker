from datetime import date
from decimal import Decimal

from app.services.llm import FundingExtraction
from app.services.normalization import (
    normalize_company_name,
    normalize_investor_name,
    normalize_round_type,
    parse_amount,
    parse_date,
    validate_extraction,
)


class TestNormalizeCompanyName:
    def test_basic(self):
        assert normalize_company_name("OpenAI Inc.") == "openai"

    def test_llc(self):
        assert normalize_company_name("Widgets LLC") == "widgets"

    def test_whitespace(self):
        assert normalize_company_name("  Some   Company  ") == "some company"


class TestNormalizeInvestorName:
    def test_basic(self):
        assert normalize_investor_name("  Sequoia  Capital  ") == "sequoia capital"


class TestNormalizeRoundType:
    def test_known(self):
        assert normalize_round_type("series a") == "Series A"
        assert normalize_round_type("Seed") == "Seed"
        assert normalize_round_type("Pre-Seed") == "Pre-Seed"

    def test_unknown(self):
        assert normalize_round_type("Bridge") == "Unknown"


class TestParseAmount:
    def test_valid(self):
        assert parse_amount(5000000) == Decimal("5000000")

    def test_none(self):
        assert parse_amount(None) is None

    def test_negative(self):
        assert parse_amount(-100) is None

    def test_invalid_string(self):
        assert parse_amount("not a number") is None


class TestParseDate:
    def test_valid(self):
        assert parse_date("2026-01-15") == date(2026, 1, 15)

    def test_date_object(self):
        d = date(2026, 3, 1)
        assert parse_date(d) == d

    def test_none(self):
        assert parse_date(None) is None

    def test_invalid(self):
        assert parse_date("not-a-date") is None


class TestValidateExtraction:
    def test_valid(self):
        e = FundingExtraction(
            company="Acme Inc",
            round_type="Series A",
            amount_usd=Decimal("10000000"),
            investors=["Sequoia", ""],
            announcement_date="2026-01-15",
        )
        result = validate_extraction(e)
        assert result is not None
        assert result.company == "Acme Inc"
        assert result.round_type == "Series A"
        assert result.investors == ["Sequoia"]

    def test_empty_company(self):
        e = FundingExtraction(company="", round_type="Seed")
        assert validate_extraction(e) is None

    def test_whitespace_company(self):
        e = FundingExtraction(company="   ", round_type="Seed")
        assert validate_extraction(e) is None
