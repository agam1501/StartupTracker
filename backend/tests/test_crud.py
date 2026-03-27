import pytest

from app.services.crud import (
    create_company,
    create_funding_round,
    create_investor,
    create_raw_source,
    get_company,
    get_investor,
    get_investor_by_normalized_name,
    get_raw_source_by_url,
    list_companies,
    list_funding_rounds,
    list_investors,
    list_unprocessed_sources,
    mark_source_processed,
)
from app.services.normalization import normalize_name

# ---------------------------------------------------------------------------
# normalize_name
# ---------------------------------------------------------------------------


class TestNormalizeName:
    def test_basic(self):
        assert normalize_name("OpenAI") == "openai"

    def test_strip_suffix(self):
        assert normalize_name("Acme Inc.") == "acme"
        assert normalize_name("Widgets LLC") == "widgets"

    def test_collapse_whitespace(self):
        assert normalize_name("  Some   Company  ") == "some company"


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------


class TestCompanyCrud:
    @pytest.mark.asyncio
    async def test_create_and_get(self, session):
        c = await create_company(session, "Acme Inc.", website="https://acme.com")
        await session.flush()

        fetched = await get_company(session, c.id)
        assert fetched is not None
        assert fetched.name == "Acme Inc."
        assert fetched.normalized_name == "acme"
        assert fetched.website == "https://acme.com"

    @pytest.mark.asyncio
    async def test_list_with_search(self, session):
        await create_company(session, "Alpha Corp")
        await create_company(session, "Beta Ltd")
        await create_company(session, "Alphabetical Inc")
        await session.commit()

        results, total = await list_companies(session, search="alpha")
        assert total == 2
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_pagination(self, session):
        for i in range(5):
            await create_company(session, f"Company {i}")
        await session.commit()

        page1, total = await list_companies(session, page=1, page_size=2)
        assert total == 5
        assert len(page1) == 2

        page3, _ = await list_companies(session, page=3, page_size=2)
        assert len(page3) == 1

    @pytest.mark.asyncio
    async def test_create_with_sector(self, session):
        c = await create_company(session, "AI Startup", sector="AI/ML")
        await session.flush()

        fetched = await get_company(session, c.id)
        assert fetched is not None
        assert fetched.sector == "AI/ML"

    @pytest.mark.asyncio
    async def test_list_filter_by_sector(self, session):
        await create_company(session, "AI Co", sector="AI/ML")
        await create_company(session, "Fin Co", sector="Fintech")
        await create_company(session, "AI Co 2", sector="AI/ML")
        await session.commit()

        results, total = await list_companies(session, sector="AI/ML")
        assert total == 2
        assert all(c.sector == "AI/ML" for c in results)

    @pytest.mark.asyncio
    async def test_list_sector_with_search(self, session):
        await create_company(session, "Alpha AI", sector="AI/ML")
        await create_company(session, "Alpha Fin", sector="Fintech")
        await create_company(session, "Beta AI", sector="AI/ML")
        await session.commit()

        results, total = await list_companies(session, search="alpha", sector="AI/ML")
        assert total == 1
        assert results[0].name == "Alpha AI"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, session):
        import uuid

        result = await get_company(session, uuid.uuid4())
        assert result is None


# ---------------------------------------------------------------------------
# Funding rounds
# ---------------------------------------------------------------------------


class TestFundingRoundCrud:
    @pytest.mark.asyncio
    async def test_create_with_investors(self, session):
        c = await create_company(session, "TestCo")
        inv = await create_investor(session, "Sequoia Capital")
        await session.commit()

        fr = await create_funding_round(
            session,
            company_id=c.id,
            round_type="Series A",
            amount_usd=10_000_000,
            investor_ids=[inv.id],
        )
        await session.commit()

        assert fr.round_type == "Series A"
        assert fr.company_id == c.id

    @pytest.mark.asyncio
    async def test_list_filter_by_company(self, session):
        c1 = await create_company(session, "Co1")
        c2 = await create_company(session, "Co2")
        await create_funding_round(session, company_id=c1.id, round_type="Seed")
        await create_funding_round(session, company_id=c2.id, round_type="Series A")
        await session.commit()

        results, total = await list_funding_rounds(session, company_id=c1.id)
        assert total == 1
        assert results[0].round_type == "Seed"

    @pytest.mark.asyncio
    async def test_list_filter_by_type(self, session):
        c = await create_company(session, "Co")
        await create_funding_round(session, company_id=c.id, round_type="Seed")
        await create_funding_round(session, company_id=c.id, round_type="Series A")
        await session.commit()

        results, total = await list_funding_rounds(session, round_type="Seed")
        assert total == 1


# ---------------------------------------------------------------------------
# Investors
# ---------------------------------------------------------------------------


class TestInvestorCrud:
    @pytest.mark.asyncio
    async def test_create_and_search(self, session):
        await create_investor(session, "Andreessen Horowitz")
        await create_investor(session, "Sequoia Capital")
        await session.commit()

        results, total = await list_investors(session, search="sequoia")
        assert total == 1
        assert results[0].name == "Sequoia Capital"

    @pytest.mark.asyncio
    async def test_get_by_normalized_name(self, session):
        await create_investor(session, "Y Combinator")
        await session.commit()

        inv = await get_investor_by_normalized_name(session, "y combinator")
        assert inv is not None
        assert inv.name == "Y Combinator"

    @pytest.mark.asyncio
    async def test_get_investor(self, session):
        created = await create_investor(session, "Tiger Global")
        await session.flush()

        fetched = await get_investor(session, created.id)
        assert fetched is not None
        assert fetched.name == "Tiger Global"


# ---------------------------------------------------------------------------
# Raw sources
# ---------------------------------------------------------------------------


class TestRawSourceCrud:
    @pytest.mark.asyncio
    async def test_create_and_find_by_url(self, session):
        rs = await create_raw_source(
            session,
            source_url="https://example.com/article1",
            title="Test Article",
        )
        await session.commit()

        found = await get_raw_source_by_url(session, "https://example.com/article1")
        assert found is not None
        assert found.id == rs.id

    @pytest.mark.asyncio
    async def test_unprocessed_list_and_mark(self, session):
        rs = await create_raw_source(
            session,
            source_url="https://example.com/a",
        )
        await session.flush()

        unprocessed = await list_unprocessed_sources(session)
        assert len(unprocessed) == 1

        await mark_source_processed(session, rs.id)
        await session.flush()

        unprocessed = await list_unprocessed_sources(session)
        assert len(unprocessed) == 0
