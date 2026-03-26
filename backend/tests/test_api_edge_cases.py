"""Edge case tests for API routes."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.crud import (
    create_company,
    create_funding_round,
    create_investor,
)
from app.services.db import get_session


@pytest.fixture
async def client(session: AsyncSession):
    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


class TestCompaniesAPIEdge:
    @pytest.mark.asyncio
    async def test_search_special_characters(self, client, session):
        await create_company(session, "C3.ai")
        await session.flush()

        resp = await client.get("/companies", params={"search": "C3"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_no_match(self, client, session):
        await create_company(session, "Acme Corp")
        await session.flush()

        resp = await client.get("/companies", params={"search": "zzzznotfound"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_pagination_beyond_total(self, client, session):
        await create_company(session, "Co1")
        await session.flush()

        resp = await client.get("/companies", params={"page": 999, "page_size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_get_invalid_uuid(self, client):
        resp = await client.get("/companies/not-a-uuid")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_company_detail_includes_funding_rounds(self, client, session):
        c = await create_company(session, "Acme Corp")
        inv = await create_investor(session, "VC Fund")
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Seed",
            amount_usd=1_000_000,
            investor_ids=[inv.id],
        )
        await session.flush()

        resp = await client.get(f"/companies/{c.id}")
        data = resp.json()
        assert len(data["funding_rounds"]) == 1
        assert data["funding_rounds"][0]["round_type"] == "Seed"
        assert len(data["funding_rounds"][0]["investors"]) == 1


class TestFundingRoundsAPIEdge:
    @pytest.mark.asyncio
    async def test_filter_no_match(self, client, session):
        c = await create_company(session, "Co")
        await create_funding_round(
            session, company_id=c.id, round_type="Seed", amount_usd=1_000_000
        )
        await session.flush()

        resp = await client.get("/funding-rounds", params={"round_type": "Series C"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_filter_by_company_id(self, client, session):
        c1 = await create_company(session, "Co1")
        c2 = await create_company(session, "Co2")
        await create_funding_round(session, company_id=c1.id, round_type="Seed")
        await create_funding_round(session, company_id=c2.id, round_type="Series A")
        await session.flush()

        resp = await client.get("/funding-rounds", params={"company_id": str(c1.id)})
        data = resp.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_invalid_uuid(self, client):
        resp = await client.get("/funding-rounds/not-a-uuid")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_round_with_no_investors(self, client, session):
        c = await create_company(session, "Co")
        fr = await create_funding_round(session, company_id=c.id, round_type="Seed")
        await session.flush()

        resp = await client.get(f"/funding-rounds/{fr.id}")
        data = resp.json()
        assert data["investors"] == []


class TestInvestorsAPIEdge:
    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, client, session):
        await create_investor(session, "Sequoia Capital")
        await session.flush()

        resp = await client.get("/investors", params={"search": "SEQUOIA"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_pagination(self, client, session):
        for i in range(5):
            await create_investor(session, f"Fund {i}")
        await session.flush()

        resp = await client.get("/investors", params={"page": 1, "page_size": 2})
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2


class TestIngestAPIEdge:
    @pytest.mark.asyncio
    async def test_missing_url(self, client):
        resp = await client.post("/ingest", json={"title": "No URL"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_url(self, client):
        resp = await client.post("/ingest", json={"source_url": ""})
        # FastAPI may accept empty string depending on schema validation
        # but the important thing is it doesn't crash
        assert resp.status_code in (200, 202, 422)


class TestStatsAPIEdge:
    @pytest.mark.asyncio
    async def test_stats_with_null_amounts(self, client, session):
        """Rounds with no amount_usd should not affect total funding."""
        c = await create_company(session, "Co")
        await create_funding_round(session, company_id=c.id, round_type="Seed")
        await session.flush()

        resp = await client.get("/stats")
        data = resp.json()
        assert data["total_rounds"] == 1
        assert data["total_funding_usd"] == 0

    @pytest.mark.asyncio
    async def test_stats_multiple_rounds(self, client, session):
        c = await create_company(session, "Co")
        await create_funding_round(
            session, company_id=c.id, round_type="Seed", amount_usd=1_000_000
        )
        await create_funding_round(
            session, company_id=c.id, round_type="Series A", amount_usd=10_000_000
        )
        await session.flush()

        resp = await client.get("/stats")
        data = resp.json()
        assert data["total_rounds"] == 2
        assert data["total_funding_usd"] == 11_000_000
