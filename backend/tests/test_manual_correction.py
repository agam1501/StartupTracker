import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.crud import create_company, create_funding_round, create_investor
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


class TestCompanyUpdate:
    @pytest.mark.asyncio
    async def test_patch_name(self, client, session):
        c = await create_company(session, "Old Name")
        await session.flush()

        resp = await client.patch(f"/companies/{c.id}", json={"name": "New Name"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New Name"
        assert data["normalized_name"] == "new name"

    @pytest.mark.asyncio
    async def test_patch_sector(self, client, session):
        c = await create_company(session, "Acme")
        await session.flush()

        resp = await client.patch(f"/companies/{c.id}", json={"sector": "AI/ML"})
        assert resp.status_code == 200
        assert resp.json()["sector"] == "AI/ML"

    @pytest.mark.asyncio
    async def test_patch_status(self, client, session):
        c = await create_company(session, "Acme")
        await session.flush()

        resp = await client.patch(f"/companies/{c.id}", json={"status": "acquired"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "acquired"

    @pytest.mark.asyncio
    async def test_patch_not_found(self, client):
        fake_id = uuid.uuid4()
        resp = await client.patch(f"/companies/{fake_id}", json={"name": "X"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_patch_empty_body(self, client, session):
        c = await create_company(session, "Acme")
        await session.flush()

        resp = await client.patch(f"/companies/{c.id}", json={})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Acme"


class TestCompanyDelete:
    @pytest.mark.asyncio
    async def test_delete(self, client, session):
        c = await create_company(session, "Acme")
        await session.flush()

        resp = await client.delete(f"/companies/{c.id}")
        assert resp.status_code == 204

        resp = await client.get(f"/companies/{c.id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client):
        fake_id = uuid.uuid4()
        resp = await client.delete(f"/companies/{fake_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_cascades_funding_rounds(self, client, session):
        c = await create_company(session, "Acme")
        inv = await create_investor(session, "VC Fund")
        fr = await create_funding_round(
            session,
            company_id=c.id,
            round_type="Series A",
            investor_ids=[inv.id],
        )
        await session.flush()
        round_id = fr.id

        resp = await client.delete(f"/companies/{c.id}")
        assert resp.status_code == 204

        resp = await client.get(f"/funding-rounds/{round_id}")
        assert resp.status_code == 404


class TestFundingRoundUpdate:
    @pytest.mark.asyncio
    async def test_patch_amount(self, client, session):
        c = await create_company(session, "Acme")
        fr = await create_funding_round(
            session, company_id=c.id, round_type="Seed", amount_usd=1_000_000
        )
        await session.flush()

        resp = await client.patch(f"/funding-rounds/{fr.id}", json={"amount_usd": 2000000})
        assert resp.status_code == 200
        assert float(resp.json()["amount_usd"]) == 2_000_000

    @pytest.mark.asyncio
    async def test_patch_round_type(self, client, session):
        c = await create_company(session, "Acme")
        fr = await create_funding_round(session, company_id=c.id, round_type="Seed")
        await session.flush()

        resp = await client.patch(f"/funding-rounds/{fr.id}", json={"round_type": "Series A"})
        assert resp.status_code == 200
        assert resp.json()["round_type"] == "Series A"

    @pytest.mark.asyncio
    async def test_patch_not_found(self, client):
        fake_id = uuid.uuid4()
        resp = await client.patch(f"/funding-rounds/{fake_id}", json={"round_type": "Seed"})
        assert resp.status_code == 404


class TestFundingRoundDelete:
    @pytest.mark.asyncio
    async def test_delete(self, client, session):
        c = await create_company(session, "Acme")
        fr = await create_funding_round(session, company_id=c.id, round_type="Seed")
        await session.flush()

        resp = await client.delete(f"/funding-rounds/{fr.id}")
        assert resp.status_code == 204

        resp = await client.get(f"/funding-rounds/{fr.id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client):
        fake_id = uuid.uuid4()
        resp = await client.delete(f"/funding-rounds/{fake_id}")
        assert resp.status_code == 404
