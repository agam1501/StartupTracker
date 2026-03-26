from datetime import date

import pytest

from app.services.crud import create_company, create_funding_round, create_investor
from app.services.dedup import get_or_create_company, get_or_create_investor, is_duplicate_round


class TestCompanyDedup:
    @pytest.mark.asyncio
    async def test_exact_match(self, session):
        original = await create_company(session, "Acme Inc.")
        await session.flush()

        found = await get_or_create_company(session, "Acme Inc.")
        assert found.id == original.id

    @pytest.mark.asyncio
    async def test_normalized_match(self, session):
        original = await create_company(session, "Acme Inc.")
        await session.flush()

        found = await get_or_create_company(session, "acme")
        assert found.id == original.id

    @pytest.mark.asyncio
    async def test_new_company(self, session):
        c = await get_or_create_company(session, "Brand New Co")
        assert c.name == "Brand New Co"


class TestInvestorDedup:
    @pytest.mark.asyncio
    async def test_exact_match(self, session):
        original = await create_investor(session, "Sequoia Capital")
        await session.flush()

        found = await get_or_create_investor(session, "Sequoia Capital")
        assert found.id == original.id

    @pytest.mark.asyncio
    async def test_new_investor(self, session):
        inv = await get_or_create_investor(session, "New Fund")
        assert inv.name == "New Fund"


class TestRoundDedup:
    @pytest.mark.asyncio
    async def test_duplicate_same_type_and_date(self, session):
        c = await create_company(session, "Co")
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Series A",
            announced_date=date(2026, 3, 1),
        )
        await session.flush()

        assert await is_duplicate_round(session, c.id, "Series A", date(2026, 3, 3))

    @pytest.mark.asyncio
    async def test_not_duplicate_different_type(self, session):
        c = await create_company(session, "Co")
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Seed",
            announced_date=date(2026, 3, 1),
        )
        await session.flush()

        assert not await is_duplicate_round(session, c.id, "Series A", date(2026, 3, 1))

    @pytest.mark.asyncio
    async def test_not_duplicate_outside_window(self, session):
        c = await create_company(session, "Co")
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Series A",
            announced_date=date(2026, 1, 1),
        )
        await session.flush()

        assert not await is_duplicate_round(session, c.id, "Series A", date(2026, 3, 1))

    @pytest.mark.asyncio
    async def test_no_existing_rounds(self, session):
        c = await create_company(session, "Co")
        await session.flush()

        assert not await is_duplicate_round(session, c.id, "Seed")
