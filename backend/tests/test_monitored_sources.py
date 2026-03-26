"""Tests for monitored sources CRUD and API."""

import pytest

from app.services.crud import (
    create_monitored_source,
    get_active_sources,
    get_monitored_source,
    list_monitored_sources,
    mark_source_checked,
    update_monitored_source,
)


class TestMonitoredSourcesCRUD:
    @pytest.mark.asyncio
    async def test_create_and_get(self, session):
        ms = await create_monitored_source(
            session,
            name="TechCrunch",
            url="https://techcrunch.com/feed/",
            source_type="rss",
        )
        await session.commit()

        fetched = await get_monitored_source(session, ms.id)
        assert fetched is not None
        assert fetched.name == "TechCrunch"
        assert fetched.url == "https://techcrunch.com/feed/"
        assert fetched.source_type == "rss"
        assert fetched.active is True
        assert fetched.last_checked_at is None

    @pytest.mark.asyncio
    async def test_create_webpage_source(self, session):
        ms = await create_monitored_source(
            session,
            name="a16z Announcements",
            url="https://a16z.com/announcements/",
            source_type="webpage",
        )
        await session.commit()

        assert ms.source_type == "webpage"
        assert ms.active is True

    @pytest.mark.asyncio
    async def test_list_sources(self, session):
        await create_monitored_source(
            session, name="Feed A", url="https://a.com/feed", source_type="rss"
        )
        await create_monitored_source(
            session, name="Page B", url="https://b.com/news", source_type="webpage"
        )
        await session.commit()

        sources, total = await list_monitored_sources(session)
        assert total == 2
        assert len(sources) == 2

    @pytest.mark.asyncio
    async def test_list_filter_by_type(self, session):
        await create_monitored_source(
            session, name="Feed A", url="https://a.com/feed", source_type="rss"
        )
        await create_monitored_source(
            session, name="Page B", url="https://b.com/news", source_type="webpage"
        )
        await session.commit()

        rss_sources, rss_total = await list_monitored_sources(session, source_type="rss")
        assert rss_total == 1
        assert rss_sources[0].name == "Feed A"

    @pytest.mark.asyncio
    async def test_list_filter_by_active(self, session):
        await create_monitored_source(
            session, name="Active", url="https://a.com/feed", source_type="rss", active=True
        )
        await create_monitored_source(
            session, name="Inactive", url="https://b.com/feed", source_type="rss", active=False
        )
        await session.commit()

        active, total = await list_monitored_sources(session, active=True)
        assert total == 1
        assert active[0].name == "Active"

    @pytest.mark.asyncio
    async def test_update_source(self, session):
        ms = await create_monitored_source(
            session, name="Old Name", url="https://old.com/feed", source_type="rss"
        )
        await session.commit()

        updated = await update_monitored_source(session, ms.id, name="New Name", active=False)
        assert updated is not None
        assert updated.name == "New Name"
        assert updated.active is False

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_none(self, session):
        import uuid

        result = await update_monitored_source(session, uuid.uuid4(), name="Nope")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_active_sources(self, session):
        await create_monitored_source(
            session, name="Active RSS", url="https://a.com/feed", source_type="rss"
        )
        await create_monitored_source(
            session, name="Inactive RSS", url="https://b.com/feed", source_type="rss", active=False
        )
        await create_monitored_source(
            session, name="Active Web", url="https://c.com/news", source_type="webpage"
        )
        await session.commit()

        all_active = await get_active_sources(session)
        assert len(all_active) == 2

        rss_active = await get_active_sources(session, source_type="rss")
        assert len(rss_active) == 1
        assert rss_active[0].name == "Active RSS"

    @pytest.mark.asyncio
    async def test_mark_source_checked(self, session):
        ms = await create_monitored_source(
            session, name="Feed", url="https://feed.com/rss", source_type="rss"
        )
        await session.commit()
        assert ms.last_checked_at is None

        await mark_source_checked(session, ms.id)
        await session.commit()

        fetched = await get_monitored_source(session, ms.id)
        assert fetched.last_checked_at is not None


class TestMonitoredSourcesAPI:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    @pytest.mark.asyncio
    async def test_create_source_api(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session

        resp = client.post(
            "/sources",
            json={
                "name": "TechCrunch",
                "url": "https://techcrunch.com/feed/",
                "source_type": "rss",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "TechCrunch"
        assert data["source_type"] == "rss"
        assert data["active"] is True

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_invalid_source_type(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session

        resp = client.post(
            "/sources",
            json={
                "name": "Bad",
                "url": "https://bad.com",
                "source_type": "invalid",
            },
        )
        assert resp.status_code == 422

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_sources_api(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session

        await create_monitored_source(
            session, name="Feed", url="https://feed.com/rss", source_type="rss"
        )
        await session.commit()

        resp = client.get("/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Feed"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_source_api(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session

        ms = await create_monitored_source(
            session, name="Feed", url="https://feed.com/rss", source_type="rss"
        )
        await session.commit()

        resp = client.get(f"/sources/{ms.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Feed"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_source_not_found(self, client, session):
        import uuid

        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session

        resp = client.get(f"/sources/{uuid.uuid4()}")
        assert resp.status_code == 404

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_source_api(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session

        ms = await create_monitored_source(
            session, name="Old", url="https://old.com/rss", source_type="rss"
        )
        await session.commit()

        resp = client.patch(f"/sources/{ms.id}", json={"name": "New", "active": False})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New"
        assert data["active"] is False

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_filter_by_type_api(self, client, session):
        from app.main import app
        from app.services.db import get_session

        app.dependency_overrides[get_session] = lambda: session

        await create_monitored_source(
            session, name="RSS", url="https://rss.com/feed", source_type="rss"
        )
        await create_monitored_source(
            session, name="Web", url="https://web.com/news", source_type="webpage"
        )
        await session.commit()

        resp = client.get("/sources?source_type=rss")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "RSS"

        app.dependency_overrides.clear()
