"""Tests for analytics service and API endpoints."""

from datetime import date
from decimal import Decimal

import pytest

from app.services.analytics import (
    acquisitions_summary,
    co_investor_pairs,
    funding_by_sector,
    round_type_distribution,
    sector_summary,
    top_investors,
)
from app.services.crud import (
    create_acquisition,
    create_company,
    create_funding_round,
    create_investor,
)


async def _seed_data(session):
    """Create test data for analytics queries."""
    # Companies with sectors
    c1 = await create_company(session, "AlphaAI", sector="AI/ML")
    c2 = await create_company(session, "BetaFin", sector="Fintech")
    c3 = await create_company(session, "GammaAI", sector="AI/ML")

    # Investors
    inv1 = await create_investor(session, "Fund One")
    inv2 = await create_investor(session, "Fund Two")
    inv3 = await create_investor(session, "Fund Three")

    # Funding rounds
    await create_funding_round(
        session,
        company_id=c1.id,
        round_type="Seed",
        amount_usd=Decimal("1000000"),
        announced_date=date(2026, 1, 15),
        investor_ids=[inv1.id, inv2.id],
    )
    await create_funding_round(
        session,
        company_id=c1.id,
        round_type="Series A",
        amount_usd=Decimal("5000000"),
        announced_date=date(2026, 2, 10),
        investor_ids=[inv1.id, inv3.id],
    )
    await create_funding_round(
        session,
        company_id=c2.id,
        round_type="Series A",
        amount_usd=Decimal("3000000"),
        announced_date=date(2026, 2, 20),
        investor_ids=[inv2.id],
    )
    await create_funding_round(
        session,
        company_id=c3.id,
        round_type="Seed",
        amount_usd=Decimal("2000000"),
        announced_date=date(2026, 3, 1),
        investor_ids=[inv1.id, inv2.id, inv3.id],
    )

    # Acquisition
    await create_acquisition(
        session,
        acquirer_id=c2.id,
        target_id=c3.id,
        amount_usd=Decimal("10000000"),
        announced_date=date(2026, 3, 15),
    )

    await session.commit()
    return {"companies": [c1, c2, c3], "investors": [inv1, inv2, inv3]}


class TestFundingBySector:
    @pytest.mark.asyncio
    async def test_groups_by_sector(self, session):
        await _seed_data(session)
        results = await funding_by_sector(session)

        assert len(results) == 2
        sectors = {r["sector"] for r in results}
        assert sectors == {"AI/ML", "Fintech"}

    @pytest.mark.asyncio
    async def test_correct_totals(self, session):
        await _seed_data(session)
        results = await funding_by_sector(session)

        ai_ml = next(r for r in results if r["sector"] == "AI/ML")
        assert ai_ml["round_count"] == 3  # Seed + Series A (AlphaAI) + Seed (GammaAI)
        assert ai_ml["total_amount"] == 8000000.0

        fintech = next(r for r in results if r["sector"] == "Fintech")
        assert fintech["round_count"] == 1
        assert fintech["total_amount"] == 3000000.0

    @pytest.mark.asyncio
    async def test_empty_db(self, session):
        results = await funding_by_sector(session)
        assert results == []


class TestTopInvestors:
    @pytest.mark.asyncio
    async def test_ranks_by_deal_count(self, session):
        await _seed_data(session)
        results = await top_investors(session)

        assert len(results) == 3
        # Fund One has 3 deals, Fund Two has 3 deals, Fund Three has 2 deals
        names = [r["name"] for r in results]
        assert "Fund Three" in names  # least deals, should be last
        assert results[-1]["deal_count"] <= results[0]["deal_count"]

    @pytest.mark.asyncio
    async def test_limit(self, session):
        await _seed_data(session)
        results = await top_investors(session, limit=1)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_empty_db(self, session):
        results = await top_investors(session)
        assert results == []


class TestCoInvestorPairs:
    @pytest.mark.asyncio
    async def test_finds_co_investors(self, session):
        await _seed_data(session)
        results = await co_investor_pairs(session)

        # Fund One + Fund Two co-invest in: AlphaAI Seed, GammaAI Seed = 2 deals
        # Fund One + Fund Three co-invest in: AlphaAI Series A, GammaAI Seed = 2 deals
        # Fund Two + Fund Three co-invest in: GammaAI Seed = 1 deal
        assert len(results) == 3
        assert results[0]["shared_deals"] >= results[-1]["shared_deals"]

    @pytest.mark.asyncio
    async def test_empty_db(self, session):
        results = await co_investor_pairs(session)
        assert results == []


class TestSectorSummary:
    @pytest.mark.asyncio
    async def test_includes_all_sectors(self, session):
        await _seed_data(session)
        results = await sector_summary(session)

        assert len(results) == 2
        ai_ml = next(r for r in results if r["sector"] == "AI/ML")
        assert ai_ml["company_count"] == 2
        assert ai_ml["round_count"] == 3

    @pytest.mark.asyncio
    async def test_empty_db(self, session):
        results = await sector_summary(session)
        assert results == []


class TestAcquisitionsSummary:
    @pytest.mark.asyncio
    async def test_lists_acquirers(self, session):
        await _seed_data(session)
        results = await acquisitions_summary(session)

        assert len(results) == 1
        assert results[0]["name"] == "BetaFin"
        assert results[0]["acquisition_count"] == 1
        assert results[0]["total_spent"] == 10000000.0

    @pytest.mark.asyncio
    async def test_empty_db(self, session):
        results = await acquisitions_summary(session)
        assert results == []


class TestRoundTypeDistribution:
    @pytest.mark.asyncio
    async def test_distribution(self, session):
        await _seed_data(session)
        results = await round_type_distribution(session)

        types = {r["round_type"]: r for r in results}
        assert "Seed" in types
        assert "Series A" in types
        assert types["Seed"]["count"] == 2
        assert types["Series A"]["count"] == 2

    @pytest.mark.asyncio
    async def test_empty_db(self, session):
        results = await round_type_distribution(session)
        assert results == []


class TestAnalyticsAPI:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    @pytest.mark.asyncio
    async def test_funding_by_sector_endpoint(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session
        await _seed_data(session)

        resp = client.get("/analytics/funding-by-sector")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_top_investors_endpoint(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session
        await _seed_data(session)

        resp = client.get("/analytics/top-investors?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_co_investors_endpoint(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session
        await _seed_data(session)

        resp = client.get("/analytics/co-investors")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sector_summary_endpoint(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session
        await _seed_data(session)

        resp = client.get("/analytics/sector-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_acquisitions_summary_endpoint(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session
        await _seed_data(session)

        resp = client.get("/analytics/acquisitions-summary")
        assert resp.status_code == 200

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_round_type_distribution_endpoint(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session
        await _seed_data(session)

        resp = client.get("/analytics/round-type-distribution")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

        app.dependency_overrides.clear()
