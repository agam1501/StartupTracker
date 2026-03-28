from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
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


class TestIngestRateLimiting:
    @pytest.mark.asyncio
    async def test_ingest_under_limit(self, client):
        """First request should succeed (202 for new URL)."""
        resp = await client.post("/ingest", json={"source_url": "https://example.com/a1"})
        assert resp.status_code == 202

    @pytest.mark.asyncio
    async def test_ingest_rate_limit_exceeded(self, client):
        """Exceeding the rate limit returns 429."""
        with patch("app.routes.ingest.settings.rate_limit_ingest", "2/minute"):
            # Reset limiter storage for clean test
            from app.limiter import limiter

            limiter.reset()

            for i in range(2):
                resp = await client.post(
                    "/ingest", json={"source_url": f"https://example.com/rl-{i}"}
                )
                assert resp.status_code in (200, 202), f"Request {i} failed: {resp.status_code}"

            # Third request should be rate limited
            resp = await client.post(
                "/ingest", json={"source_url": "https://example.com/rl-blocked"}
            )
            assert resp.status_code == 429
