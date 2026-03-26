"""Tests for enhanced list filtering and sorting."""

from datetime import date
from decimal import Decimal

import pytest

from app.services.crud import (
    create_acquisition,
    create_company,
    create_funding_round,
    create_investor,
    list_acquisitions,
    list_companies,
    list_funding_rounds,
    list_investors,
)


class TestCompanySorting:
    @pytest.mark.asyncio
    async def test_sort_by_name_asc(self, session):
        await create_company(session, "Zebra Corp")
        await create_company(session, "Alpha Inc")
        await session.commit()

        companies, _ = await list_companies(session, sort_by="name", sort_order="asc")
        assert companies[0].name == "Alpha Inc"
        assert companies[1].name == "Zebra Corp"

    @pytest.mark.asyncio
    async def test_sort_by_name_desc(self, session):
        await create_company(session, "Zebra Corp")
        await create_company(session, "Alpha Inc")
        await session.commit()

        companies, _ = await list_companies(session, sort_by="name", sort_order="desc")
        assert companies[0].name == "Zebra Corp"

    @pytest.mark.asyncio
    async def test_sort_by_sector(self, session):
        await create_company(session, "AI Co", sector="AI/ML")
        await create_company(session, "Fin Co", sector="Fintech")
        await session.commit()

        companies, _ = await list_companies(session, sort_by="sector", sort_order="asc")
        assert companies[0].sector == "AI/ML"


class TestFundingRoundFilters:
    @pytest.mark.asyncio
    async def test_filter_by_amount_range(self, session):
        c = await create_company(session, "TestCo")
        await create_funding_round(
            session, company_id=c.id, round_type="Seed", amount_usd=Decimal("500000")
        )
        await create_funding_round(
            session, company_id=c.id, round_type="Series A", amount_usd=Decimal("5000000")
        )
        await create_funding_round(
            session, company_id=c.id, round_type="Series B", amount_usd=Decimal("20000000")
        )
        await session.commit()

        rounds, total = await list_funding_rounds(session, min_amount=1000000, max_amount=10000000)
        assert total == 1
        assert rounds[0].round_type == "Series A"

    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, session):
        c = await create_company(session, "TestCo")
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Seed",
            announced_date=date(2025, 6, 1),
        )
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Series A",
            announced_date=date(2026, 1, 15),
        )
        await session.commit()

        rounds, total = await list_funding_rounds(
            session, date_from="2026-01-01", date_to="2026-12-31"
        )
        assert total == 1
        assert rounds[0].round_type == "Series A"

    @pytest.mark.asyncio
    async def test_filter_by_investor(self, session):
        c = await create_company(session, "TestCo")
        inv = await create_investor(session, "Target Fund")
        other_inv = await create_investor(session, "Other Fund")

        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Seed",
            investor_ids=[inv.id],
        )
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Series A",
            investor_ids=[other_inv.id],
        )
        await session.commit()

        rounds, total = await list_funding_rounds(session, investor_id=inv.id)
        assert total == 1
        assert rounds[0].round_type == "Seed"

    @pytest.mark.asyncio
    async def test_sort_by_amount(self, session):
        c = await create_company(session, "TestCo")
        await create_funding_round(
            session, company_id=c.id, round_type="Seed", amount_usd=Decimal("1000000")
        )
        await create_funding_round(
            session, company_id=c.id, round_type="Series A", amount_usd=Decimal("5000000")
        )
        await session.commit()

        rounds, _ = await list_funding_rounds(session, sort_by="amount", sort_order="desc")
        assert rounds[0].round_type == "Series A"

    @pytest.mark.asyncio
    async def test_sort_by_amount_asc(self, session):
        c = await create_company(session, "TestCo")
        await create_funding_round(
            session, company_id=c.id, round_type="Seed", amount_usd=Decimal("1000000")
        )
        await create_funding_round(
            session, company_id=c.id, round_type="Series A", amount_usd=Decimal("5000000")
        )
        await session.commit()

        rounds, _ = await list_funding_rounds(session, sort_by="amount", sort_order="asc")
        assert rounds[0].round_type == "Seed"


class TestInvestorFilters:
    @pytest.mark.asyncio
    async def test_filter_by_investor_type(self, session):
        await create_investor(session, "VC Fund", investor_type="VC")
        await create_investor(session, "Angel Smith", investor_type="Angel")
        await session.commit()

        investors, total = await list_investors(session, investor_type="VC")
        assert total == 1
        assert investors[0].name == "VC Fund"

    @pytest.mark.asyncio
    async def test_sort_by_name_desc(self, session):
        await create_investor(session, "Alpha Fund")
        await create_investor(session, "Zeta Capital")
        await session.commit()

        investors, _ = await list_investors(session, sort_by="name", sort_order="desc")
        assert investors[0].name == "Zeta Capital"


class TestAcquisitionFilters:
    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, session):
        c1 = await create_company(session, "Acquirer")
        c2 = await create_company(session, "Target1")
        c3 = await create_company(session, "Target2")

        await create_acquisition(
            session,
            acquirer_id=c1.id,
            target_id=c2.id,
            announced_date=date(2025, 6, 1),
        )
        await create_acquisition(
            session,
            acquirer_id=c1.id,
            target_id=c3.id,
            announced_date=date(2026, 2, 15),
        )
        await session.commit()

        acqs, total = await list_acquisitions(session, date_from="2026-01-01", date_to="2026-12-31")
        assert total == 1

    @pytest.mark.asyncio
    async def test_sort_by_amount(self, session):
        c1 = await create_company(session, "Acquirer")
        c2 = await create_company(session, "Small Target")
        c3 = await create_company(session, "Big Target")

        await create_acquisition(
            session,
            acquirer_id=c1.id,
            target_id=c2.id,
            amount_usd=Decimal("1000000"),
        )
        await create_acquisition(
            session,
            acquirer_id=c1.id,
            target_id=c3.id,
            amount_usd=Decimal("50000000"),
        )
        await session.commit()

        acqs, _ = await list_acquisitions(session, sort_by="amount", sort_order="desc")
        assert float(acqs[0].amount_usd) == 50000000.0


class TestEnhancedFiltersAPI:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    @pytest.mark.asyncio
    async def test_companies_sort_params(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session
        await create_company(session, "Zebra")
        await create_company(session, "Alpha")
        await session.commit()

        resp = client.get("/companies?sort_by=name&sort_order=desc")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert items[0]["name"] == "Zebra"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_funding_rounds_filter_params(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session
        c = await create_company(session, "TestCo")
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Seed",
            amount_usd=Decimal("500000"),
        )
        await create_funding_round(
            session,
            company_id=c.id,
            round_type="Series A",
            amount_usd=Decimal("5000000"),
        )
        await session.commit()

        resp = client.get("/funding-rounds?min_amount=1000000")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_investors_type_filter(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session
        await create_investor(session, "VC Fund", investor_type="VC")
        await create_investor(session, "Angel", investor_type="Angel")
        await session.commit()

        resp = client.get("/investors?investor_type=VC")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_acquisitions_date_filter(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session
        c1 = await create_company(session, "Acquirer")
        c2 = await create_company(session, "Target")
        await create_acquisition(
            session,
            acquirer_id=c1.id,
            target_id=c2.id,
            announced_date=date(2026, 3, 1),
        )
        await session.commit()

        resp = client.get("/acquisitions?date_from=2026-01-01&date_to=2026-12-31")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        app.dependency_overrides.clear()
