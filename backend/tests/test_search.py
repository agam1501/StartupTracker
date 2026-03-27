import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.crud import create_company, create_investor
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


class TestGlobalSearch:
    @pytest.mark.asyncio
    async def test_search_returns_companies_and_investors(self, client, session):
        await create_company(session, "Stripe")
        await create_investor(session, "Sequoia Capital")
        await session.flush()

        resp = await client.get("/search", params={"q": "str"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["companies"]) == 1
        assert data["companies"][0]["name"] == "Stripe"
        assert data["investors"] == []

    @pytest.mark.asyncio
    async def test_search_investors(self, client, session):
        await create_investor(session, "Sequoia Capital")
        await session.flush()

        resp = await client.get("/search", params={"q": "sequoia"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["investors"]) == 1
        assert data["investors"][0]["name"] == "Sequoia Capital"

    @pytest.mark.asyncio
    async def test_search_too_short(self, client):
        resp = await client.get("/search", params={"q": "a"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_search_no_results(self, client):
        resp = await client.get("/search", params={"q": "zzzzz"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["companies"] == []
        assert data["investors"] == []
