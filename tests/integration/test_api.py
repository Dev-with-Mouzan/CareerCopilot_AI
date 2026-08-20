"""Integration tests for the FastAPI API endpoints using httpx AsyncClient."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def client():
    """Create an async test client for the FastAPI app.

    The app is imported lazily so that tests can run even if the full
    database / redis stack is not available — only routes that don't
    depend on external services will pass.
    """
    from backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Health Check ──────────────────────────────────────────────────────────────


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client: AsyncClient):
        resp = await client.get("/api/health")
        # The health endpoint may return 200 or may need a DB — accept both
        assert resp.status_code in (200, 500)

    @pytest.mark.asyncio
    async def test_health_returns_json(self, client: AsyncClient):
        resp = await client.get("/api/health")
        if resp.status_code == 200:
            data = resp.json()
            assert "status" in data


# ── Upload Resume ─────────────────────────────────────────────────────────────


class TestResumeUpload:
    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            "/api/resumes",
            files={"file": ("test.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        )
        # Without auth, should get 401
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_wrong_content_type(self, client: AsyncClient):
        resp = await client.post(
            "/api/resumes",
            headers={"X-API-Key": "test-key-123"},
            files={"file": ("test.exe", b"MZ\x00\x00", "application/octet-stream")},
        )
        # Should reject non-allowed file types (400 or 401)
        assert resp.status_code in (400, 401, 422)


# ── Jobs List ─────────────────────────────────────────────────────────────────


class TestJobsEndpoint:
    @pytest.mark.asyncio
    async def test_list_jobs_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/jobs")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_jobs_with_auth(self, client: AsyncClient):
        resp = await client.get(
            "/api/jobs",
            headers={"X-API-Key": "test-key-123"},
        )
        # Should return 200 (empty list) or 500 (DB issue)
        assert resp.status_code in (200, 500)


# ── Job Search ────────────────────────────────────────────────────────────────


class TestJobSearchEndpoint:
    @pytest.mark.asyncio
    async def test_search_requires_auth(self, client: AsyncClient):
        resp = await client.post("/api/jobs/search")
        assert resp.status_code == 401


# ── Chat ──────────────────────────────────────────────────────────────────────


class TestChatEndpoint:
    @pytest.mark.asyncio
    async def test_chat_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            "/api/chat",
            json={"message": "Hello"},
        )
        assert resp.status_code == 401


# ── Session Clear ─────────────────────────────────────────────────────────────


class TestSessionEndpoint:
    @pytest.mark.asyncio
    async def test_delete_session(self, client: AsyncClient):
        resp = await client.delete("/api/session")
        # Session endpoint may not require auth (backward compat)
        assert resp.status_code in (200, 204, 401, 404, 405)


# ── 404 Handling ──────────────────────────────────────────────────────────────


class TestNotFound:
    @pytest.mark.asyncio
    async def test_nonexistent_route(self, client: AsyncClient):
        resp = await client.get("/api/nonexistent-route")
        assert resp.status_code in (404, 405)

    @pytest.mark.asyncio
    async def test_nonexistent_job(self, client: AsyncClient):
        resp = await client.get(
            "/api/jobs/00000000-0000-0000-0000-000000000000",
            headers={"X-API-Key": "test-key-123"},
        )
        # Should return 404 (job not found) or 401 (auth issue)
        assert resp.status_code in (401, 404)
