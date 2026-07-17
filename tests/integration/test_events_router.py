"""
Module 14 Phase 3 — Events router tests.

Exercises apps/api/routers/events.py end-to-end via FastAPI's
TestClient/ASGITransport against the REAL test Postgres database (the
same one EventRepository's own tests use) — dependency-injected the
normal FastAPI way, not a mocked repository, so this also verifies the
FastAPI <-> EventRepository wiring itself.
"""

import uuid
from datetime import date

import pytest
import pytest_asyncio
from fastapi import FastAPI

pytestmark = pytest.mark.asyncio
from httpx import ASGITransport, AsyncClient

from apps.api.dependencies import get_db_session
from apps.api.routers.events import router as events_router


@pytest_asyncio.fixture
async def app(db_session) -> FastAPI:
    app = FastAPI()

    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_db
    app.include_router(events_router, prefix="/api/v1")
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestCreateEvent:
    async def test_create_returns_201_and_event_body(self, client, birth_chart_id, db_session):
        response = await client.post("/api/v1/events", json={
            "chart_id": str(birth_chart_id), "event_date": "2010-05-01",
            "title": "Marriage", "category": "marriage", "is_verified": True,
        })
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Marriage"
        assert body["category"] == "marriage"
        assert body["is_verified"] is True
        assert uuid.UUID(body["id"])

    async def test_invalid_chart_id_returns_422(self, client, db_session):
        response = await client.post("/api/v1/events", json={
            "chart_id": str(uuid.uuid4()), "event_date": "2010-05-01", "title": "X",
        })
        assert response.status_code == 422

    async def test_blank_title_rejected_by_schema_validation(self, client, birth_chart_id, db_session):
        response = await client.post("/api/v1/events", json={
            "chart_id": str(birth_chart_id), "event_date": "2010-05-01", "title": "",
        })
        assert response.status_code == 422  # FastAPI's own request-validation 422, before repo is touched


class TestGetEvent:
    async def test_get_existing_event(self, client, birth_chart_id, db_session):
        create_resp = await client.post("/api/v1/events", json={
            "chart_id": str(birth_chart_id), "event_date": "2010-05-01", "title": "X",
        })
        event_id = create_resp.json()["id"]

        get_resp = await client.get(f"/api/v1/events/{event_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == event_id

    async def test_unknown_event_returns_404(self, client, db_session):
        response = await client.get(f"/api/v1/events/{uuid.uuid4()}")
        assert response.status_code == 404


class TestListEvents:
    async def test_lists_events_for_chart_ordered_by_date(self, client, birth_chart_id, db_session):
        await client.post("/api/v1/events", json={"chart_id": str(birth_chart_id), "event_date": "2015-01-01", "title": "Later"})
        await client.post("/api/v1/events", json={"chart_id": str(birth_chart_id), "event_date": "2005-01-01", "title": "Earlier"})

        response = await client.get("/api/v1/events", params={"chart_id": str(birth_chart_id)})
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert [e["title"] for e in body["events"]] == ["Earlier", "Later"]

    async def test_filters_by_category(self, client, birth_chart_id, db_session):
        await client.post("/api/v1/events", json={"chart_id": str(birth_chart_id), "event_date": "2005-01-01", "title": "A", "category": "career"})
        await client.post("/api/v1/events", json={"chart_id": str(birth_chart_id), "event_date": "2010-01-01", "title": "B", "category": "marriage"})

        response = await client.get("/api/v1/events", params={"chart_id": str(birth_chart_id), "category": "career"})
        assert [e["title"] for e in response.json()["events"]] == ["A"]


class TestUpdateEvent:
    async def test_partial_update_only_changes_supplied_fields(self, client, birth_chart_id, db_session):
        create_resp = await client.post("/api/v1/events", json={
            "chart_id": str(birth_chart_id), "event_date": "2010-05-01", "title": "Original",
            "description": "Original desc",
        })
        event_id = create_resp.json()["id"]

        patch_resp = await client.patch(f"/api/v1/events/{event_id}", json={"title": "Updated"})
        assert patch_resp.status_code == 200
        body = patch_resp.json()
        assert body["title"] == "Updated"
        assert body["description"] == "Original desc"

    async def test_can_explicitly_null_out_description(self, client, birth_chart_id, db_session):
        create_resp = await client.post("/api/v1/events", json={
            "chart_id": str(birth_chart_id), "event_date": "2010-05-01", "title": "X",
            "description": "Has value",
        })
        event_id = create_resp.json()["id"]

        patch_resp = await client.patch(f"/api/v1/events/{event_id}", json={"description": None})
        assert patch_resp.json()["description"] is None

    async def test_unknown_event_returns_404(self, client, db_session):
        response = await client.patch(f"/api/v1/events/{uuid.uuid4()}", json={"title": "X"})
        assert response.status_code == 404


class TestDeleteEvent:
    async def test_delete_returns_204_then_get_returns_404(self, client, birth_chart_id, db_session):
        create_resp = await client.post("/api/v1/events", json={
            "chart_id": str(birth_chart_id), "event_date": "2010-05-01", "title": "X",
        })
        event_id = create_resp.json()["id"]

        delete_resp = await client.delete(f"/api/v1/events/{event_id}")
        assert delete_resp.status_code == 204

        get_resp = await client.get(f"/api/v1/events/{event_id}")
        assert get_resp.status_code == 404

    async def test_unknown_event_returns_404(self, client, db_session):
        response = await client.delete(f"/api/v1/events/{uuid.uuid4()}")
        assert response.status_code == 404
