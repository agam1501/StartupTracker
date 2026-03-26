import uuid
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.crud import (
    create_acquisition,
    create_company,
    get_acquisition,
    list_acquisitions,
)
from app.services.db import get_session

# ---------------------------------------------------------------------------
# CRUD tests
# ---------------------------------------------------------------------------


class TestAcquisitionCrud:
    @pytest.mark.asyncio
    async def test_create_and_get(self, session):
        acquirer = await create_company(session, "BigCorp")
        target = await create_company(session, "SmallStartup")
        await session.flush()

        acq = await create_acquisition(
            session,
            acquirer_id=acquirer.id,
            target_id=target.id,
            amount_usd=50_000_000,
            announced_date=date(2026, 1, 15),
            source_url="https://example.com/acq",
            confidence_score=0.92,
        )
        await session.flush()

        fetched = await get_acquisition(session, acq.id)
        assert fetched is not None
        assert fetched.acquirer_id == acquirer.id
        assert fetched.target_id == target.id
        assert float(fetched.amount_usd) == 50_000_000
        assert fetched.confidence_score == 0.92

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, session):
        result = await get_acquisition(session, uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, session):
        c1 = await create_company(session, "Acquirer1")
        c2 = await create_company(session, "Target1")
        c3 = await create_company(session, "Target2")
        await create_acquisition(session, acquirer_id=c1.id, target_id=c2.id)
        await create_acquisition(session, acquirer_id=c1.id, target_id=c3.id)
        await session.flush()

        results, total = await list_acquisitions(session)
        assert total == 2

    @pytest.mark.asyncio
    async def test_list_filter_by_acquirer(self, session):
        c1 = await create_company(session, "Acquirer1")
        c2 = await create_company(session, "Acquirer2")
        c3 = await create_company(session, "Target1")
        await create_acquisition(session, acquirer_id=c1.id, target_id=c3.id)
        await create_acquisition(session, acquirer_id=c2.id, target_id=c3.id)
        await session.flush()

        results, total = await list_acquisitions(session, acquirer_id=c1.id)
        assert total == 1

    @pytest.mark.asyncio
    async def test_list_filter_by_target(self, session):
        c1 = await create_company(session, "Acquirer")
        c2 = await create_company(session, "Target1")
        c3 = await create_company(session, "Target2")
        await create_acquisition(session, acquirer_id=c1.id, target_id=c2.id)
        await create_acquisition(session, acquirer_id=c1.id, target_id=c3.id)
        await session.flush()

        results, total = await list_acquisitions(session, target_id=c2.id)
        assert total == 1

    @pytest.mark.asyncio
    async def test_create_minimal(self, session):
        c1 = await create_company(session, "A")
        c2 = await create_company(session, "B")
        acq = await create_acquisition(session, acquirer_id=c1.id, target_id=c2.id)
        await session.flush()

        assert acq.amount_usd is None
        assert acq.announced_date is None
        assert acq.confidence_score is None


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


@pytest.fixture
async def client(session: AsyncSession):
    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


class TestAcquisitionsAPI:
    @pytest.mark.asyncio
    async def test_list_empty(self, client):
        resp = await client.get("/acquisitions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_with_data(self, client, session):
        c1 = await create_company(session, "BigCo")
        c2 = await create_company(session, "SmallCo")
        await create_acquisition(
            session,
            acquirer_id=c1.id,
            target_id=c2.id,
            amount_usd=10_000_000,
        )
        await session.flush()

        resp = await client.get("/acquisitions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        item = data["items"][0]
        assert item["acquirer_name"] == "BigCo"
        assert item["target_name"] == "SmallCo"

    @pytest.mark.asyncio
    async def test_get_detail(self, client, session):
        c1 = await create_company(session, "Buyer")
        c2 = await create_company(session, "Seller")
        acq = await create_acquisition(
            session,
            acquirer_id=c1.id,
            target_id=c2.id,
            amount_usd=5_000_000,
            confidence_score=0.85,
        )
        await session.flush()

        resp = await client.get(f"/acquisitions/{acq.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["acquirer_name"] == "Buyer"
        assert data["target_name"] == "Seller"
        assert data["confidence_score"] == 0.85

    @pytest.mark.asyncio
    async def test_get_404(self, client):
        resp = await client.get("/acquisitions/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_filter_by_acquirer(self, client, session):
        c1 = await create_company(session, "Buyer1")
        c2 = await create_company(session, "Buyer2")
        c3 = await create_company(session, "Target")
        await create_acquisition(session, acquirer_id=c1.id, target_id=c3.id)
        await create_acquisition(session, acquirer_id=c2.id, target_id=c3.id)
        await session.flush()

        resp = await client.get("/acquisitions", params={"acquirer_id": str(c1.id)})
        assert resp.json()["total"] == 1
