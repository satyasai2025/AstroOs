"""
AstroOS — Chart History & Management API Unit Tests
Tests /api/v1/horoscope/my-charts, DELETE /api/v1/horoscope/charts/{id},
and POST /api/v1/horoscope/charts/{id}/set-default.
"""

from datetime import datetime, timezone
import uuid
import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import get_current_user_from_bearer, get_db_session
from apps.api.domain.user import UserRole
from apps.api.main import app
from apps.api.models.astrology import BirthChartModel
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.tests.conftest import make_user


@pytest.fixture
def chart_user():
    return make_user(email="chartuser@astroos.dev", role=UserRole.GUEST)


@pytest.mark.asyncio
async def test_chart_delete_and_set_default_via_api(chart_user, db_session):
    user_id = chart_user.id.value
    repo = BirthChartRepository(db_session)

    # Seed 2 charts
    c1_id = await repo.get_or_create(
        birth_datetime_utc=datetime(1990, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="W",
        user_id=user_id,
        subject_name="Chart One",
    )
    c2_id = await repo.get_or_create(
        birth_datetime_utc=datetime(1992, 5, 10, 14, 30, 0, tzinfo=timezone.utc),
        latitude=19.0760,
        longitude=72.8777,
        ayanamsa="lahiri",
        house_system="W",
        user_id=user_id,
        subject_name="Chart Two",
    )

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db
    app.dependency_overrides[get_current_user_from_bearer] = lambda: chart_user

    with TestClient(app) as client:
        # 1. List charts
        res = client.get("/api/v1/horoscope/my-charts")
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["total"] == 2
        assert len(data["charts"]) == 2

        # c1 should initially be default (first chart)
        c1_data = next(c for c in data["charts"] if c["id"] == str(c1_id))
        assert c1_data["is_default"] is True

        # 2. Set c2 as default
        res_default = client.post(f"/api/v1/horoscope/charts/{c2_id}/set-default", json={})
        assert res_default.status_code in (200, 204), res_default.text

        # Verify default changed
        res2 = client.get("/api/v1/horoscope/my-charts")
        assert res2.status_code == 200
        data2 = res2.json()
        c2_data = next(c for c in data2["charts"] if c["id"] == str(c2_id))
        c1_data_after = next(c for c in data2["charts"] if c["id"] == str(c1_id))
        assert c2_data["is_default"] is True
        assert c1_data_after["is_default"] is False

        # 3. Delete c1
        res_delete = client.delete(f"/api/v1/horoscope/charts/{c1_id}")
        assert res_delete.status_code in (200, 204), res_delete.text

        # Verify c1 is gone
        res3 = client.get("/api/v1/horoscope/my-charts")
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3["total"] == 1
        assert data3["charts"][0]["id"] == str(c2_id)

    app.dependency_overrides.clear()
