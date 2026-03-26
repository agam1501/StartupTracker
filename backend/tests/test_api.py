import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.crud import create_company, create_funding_round, create_investor
from app.services.db import get_session


@pytest.fixture
async def client(session: AsyncSession):
    """Override DB dependency to use test session, then yield an async client."""

    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


class TestCompaniesAPI:
    @pytest.mark.asyncio
    async def test_list_empty(self, client):
        resp = await client.get("/companies")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_with_data(self, client, session):
        await create_company(session, "Acme Corp")
        await create_company(session, "Beta Inc")
        await session.flush()

        resp = await client.get("/companies")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_list_search(self, client, session):
        await create_company(session, "Acme Corp")
        await create_company(session, "Beta Inc")
        await session.flush()

        resp = await client.get("/companies", params={"search": "acme"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_list_pagination(self, client, session):
        for i in range(5):
            await create_company(session, f"Co {i}")
        await session.flush()

        resp = await client.get("/companies", params={"page": 1, "page_size": 2})
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_detail(self, client, session):
        c = await create_company(session, "Acme Corp", website="https://acme.com")
        await session.flush()

        resp = await client.get(f"/companies/{c.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Acme Corp"
        assert data["website"] == "https://acme.com"
        assert "funding_rounds" in data

    @pytest.mark.asyncio
    async def test_get_404(self, client):
        resp = await client.get("/companies/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestFundingRoundsAPI:
    @pytest.mark.asyncio
    async def test_list_empty(self, client):
        resp = await client.get("/funding-rounds")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_list_with_filter(self, client, session):
        c = await create_company(session, "Co")
        await create_funding_round(
            session, company_id=c.id, round_type="Seed", amount_usd=1_000_000
        )
        await create_funding_round(
            session, company_id=c.id, round_type="Series A", amount_usd=10_000_000
        )
        await session.flush()

        resp = await client.get("/funding-rounds", params={"round_type": "Seed"})
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["round_type"] == "Seed"

    @pytest.mark.asyncio
    async def test_get_detail(self, client, session):
        c = await create_company(session, "Co")
        inv = await create_investor(session, "VC Fund")
        fr = await create_funding_round(
            session,
            company_id=c.id,
            round_type="Series A",
            investor_ids=[inv.id],
        )
        await session.flush()

        resp = await client.get(f"/funding-rounds/{fr.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["round_type"] == "Series A"
        assert len(data["investors"]) == 1

    @pytest.mark.asyncio
    async def test_get_404(self, client):
        resp = await client.get("/funding-rounds/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestIngestAPI:
    @pytest.mark.asyncio
    async def test_ingest_new(self, client):
        resp = await client.post(
            "/ingest",
            json={
                "source_url": "https://example.com/article",
                "title": "Test Article",
            },
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["source_url"] == "https://example.com/article"
        assert data["processed"] is False

    @pytest.mark.asyncio
    async def test_ingest_duplicate(self, client):
        payload = {
            "source_url": "https://example.com/dup",
            "title": "Dup",
        }
        resp1 = await client.post("/ingest", json=payload)
        assert resp1.status_code == 202

        resp2 = await client.post("/ingest", json=payload)
        assert resp2.status_code == 200
        assert resp2.json()["id"] == resp1.json()["id"]
