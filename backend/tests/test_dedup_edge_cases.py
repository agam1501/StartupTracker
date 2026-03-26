"""Edge case tests for deduplication logic."""

from datetime import date

import pytest

from app.services.crud import create_company, create_funding_round, create_investor
from app.services.dedup import (
    _fuzzy_match,
    get_or_create_company,
    get_or_create_investor,
    is_duplicate_round,
)


class TestFuzzyMatch:
    def test_identical_strings(self):
        assert _fuzzy_match("acme", "acme") == 100.0

    def test_completely_different(self):
        score = _fuzzy_match("abc", "xyz")
        assert score < 50

    def test_empty_strings(self):
        score = _fuzzy_match("", "")
        assert score == 100.0  # Both empty = identical

    def test_one_empty(self):
        score = _fuzzy_match("acme", "")
        assert score < 50

    def test_very_similar(self):
        # Should be above fuzzy threshold
        score = _fuzzy_match("sequoia capital", "sequoia capitl")
        assert score >= 85


class TestCompanyDedupEdge:
    @pytest.mark.asyncio
    async def test_fuzzy_match_similar_names(self, session):
        """Companies with very similar names should be deduped."""
        original = await create_company(session, "Stripe Inc")
        await session.flush()

        # "Stripe" should match "Stripe Inc" via normalization
        found = await get_or_create_company(session, "Stripe")
        assert found.id == original.id

    @pytest.mark.asyncio
    async def test_different_companies_not_merged(self, session):
        """Companies with different names should stay separate."""
        c1 = await create_company(session, "Apple")
        await session.flush()

        c2 = await get_or_create_company(session, "Google")
        assert c2.id != c1.id

    @pytest.mark.asyncio
    async def test_preserves_website_on_create(self, session):
        c = await get_or_create_company(session, "NewCo", website="https://newco.com")
        assert c.website == "https://newco.com"

    @pytest.mark.asyncio
    async def test_case_insensitive_match(self, session):
        original = await create_company(session, "Anthropic")
        await session.flush()

        found = await get_or_create_company(session, "ANTHROPIC")
        assert found.id == original.id


class TestInvestorDedupEdge:
    @pytest.mark.asyncio
    async def test_case_insensitive_match(self, session):
        original = await create_investor(session, "Sequoia Capital")
        await session.flush()

        found = await get_or_create_investor(session, "sequoia capital")
        assert found.id == original.id

    @pytest.mark.asyncio
    async def test_multiple_investors_no_cross_match(self, session):
        inv1 = await create_investor(session, "Alpha Fund")
        inv2 = await create_investor(session, "Beta Capital")
        await session.flush()

        found = await get_or_create_investor(session, "Alpha Fund")
        assert found.id == inv1.id
        assert found.id != inv2.id


class TestRoundDedupEdge:
    @pytest.mark.asyncio
    async def test_boundary_date_exactly_7_days(self, session):
        """Rounds exactly 7 days apart should still be considered duplicates."""
        c = await create_company(session, "Co")
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Series A",
            announced_date=date(2026, 3, 1),
        )
        await session.flush()

        assert await is_duplicate_round(session, c.id, "Series A", date(2026, 3, 8))

    @pytest.mark.asyncio
    async def test_boundary_date_8_days(self, session):
        """Rounds 8 days apart should not be duplicates."""
        c = await create_company(session, "Co")
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Series A",
            announced_date=date(2026, 3, 1),
        )
        await session.flush()

        assert not await is_duplicate_round(session, c.id, "Series A", date(2026, 3, 9))

    @pytest.mark.asyncio
    async def test_null_existing_date_matches(self, session):
        """If existing round has no date, it should match on type alone."""
        c = await create_company(session, "Co")
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Seed",
            # No announced_date
        )
        await session.flush()

        assert await is_duplicate_round(session, c.id, "Seed", date(2026, 3, 1))

    @pytest.mark.asyncio
    async def test_null_new_date_matches(self, session):
        """If new round has no date, it should match on type alone."""
        c = await create_company(session, "Co")
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Seed",
            announced_date=date(2026, 3, 1),
        )
        await session.flush()

        assert await is_duplicate_round(session, c.id, "Seed", None)

    @pytest.mark.asyncio
    async def test_different_company_same_round_not_duplicate(self, session):
        """Same round type for different companies should not be duplicates."""
        c1 = await create_company(session, "Co1")
        c2 = await create_company(session, "Co2")
        await create_funding_round(
            session,
            company_id=c1.id,
            round_type="Series A",
            announced_date=date(2026, 3, 1),
        )
        await session.flush()

        assert not await is_duplicate_round(session, c2.id, "Series A", date(2026, 3, 1))
