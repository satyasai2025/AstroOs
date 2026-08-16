"""Tests for the Dataset Import API router."""

import json
import os
import tempfile
from datetime import datetime, timezone
import uuid
import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import get_dataset_service, require_researcher
from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.main import create_app


@pytest.fixture
def app():
    app = create_app()
    now = datetime.now(timezone.utc)
    fake_user = User(
        id=UserId(uuid.uuid4()),
        email="researcher@astroos.io",
        display_name="Researcher",
        hashed_password="mock",
        role=UserRole.RESEARCHER,
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    # Override dataset_service dependency to return None (skip DB persistence)
    app.dependency_overrides[get_dataset_service] = lambda: None
    app.dependency_overrides[require_researcher] = lambda: fake_user
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def sample_csv():
    """Create a temporary CSV file for upload testing."""
    import csv
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name
        writer = csv.writer(f)
        writer.writerow(["fname", "lname", "gender", "lat", "lng", "year"])
        writer.writerow(["Test", "User", "M", 40.0, -74.0, 1990])
        writer.writerow(["Test2", "User2", "F", 34.0, -118.0, 1985])
    yield path
    os.unlink(path)


class TestDatasetsRouter:
    def test_list_schemas(self, client):
        response = client.get("/api/v1/datasets/schemas")
        assert response.status_code == 200
        data = response.json()
        assert "schemas" in data
        schema_names = [s["name"] for s in data["schemas"]]
        assert "astroos-dataset-schema.json" in schema_names
        assert "astroos-record-envelope-schema.json" in schema_names

    def test_get_dataset_schema(self, client):
        response = client.get("/api/v1/datasets/schemas/astroos-dataset-schema.json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        schema = response.json()
        assert schema["title"] == "AstroOS Dataset Metadata Schema"

    def test_get_record_schema(self, client):
        response = client.get("/api/v1/datasets/schemas/astroos-record-envelope-schema.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["title"] == "AstroOS Record Envelope Schema"

    def test_get_schema_not_found(self, client):
        response = client.get("/api/v1/datasets/schemas/nonexistent.json")
        assert response.status_code == 404

    def test_get_template_csv(self, client):
        response = client.get("/api/v1/datasets/templates/csv")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")

    def test_get_template_xlsx(self, client):
        response = client.get("/api/v1/datasets/templates/xlsx")
        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]

    def test_get_template_invalid_format(self, client):
        response = client.get("/api/v1/datasets/templates/pdf")
        assert response.status_code == 400

    def test_validate_dataset(self, client, sample_csv):
        with open(sample_csv, "rb") as f:
            response = client.post(
                "/api/v1/datasets/validate",
                files={"file": ("test.csv", f, "text/csv")},
                data={"rules": "standard"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert data["records"] == 2
        assert "l1" in data
        assert "l2" in data

    def test_import_dataset(self, client, sample_csv):
        with open(sample_csv, "rb") as f:
            response = client.post(
                "/api/v1/datasets/import",
                files={"file": ("test.csv", f, "text/csv")},
                data={
                    "dataset_id": "ASTRO-RS-COHORT-TEST-v0.1.0",
                    "adapter_type": "auto",
                    "export_format": "CSV",
                },
            )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] in ("completed", "running", "failed")

        # Check job status
        job_id = data["job_id"]
        status_resp = client.get(f"/api/v1/datasets/import/{job_id}/status")
        assert status_resp.status_code == 200
        job_data = status_resp.json()
        assert job_data["job_id"] == job_id

    def test_import_status_not_found(self, client):
        response = client.get("/api/v1/datasets/import/nonexistent-job-id/status")
        assert response.status_code == 404

    def test_import_unsupported_format(self, client):
        # Create a .pdf file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
            f.write(b"fake pdf content")
        try:
            with open(path, "rb") as f:
                response = client.post(
                    "/api/v1/datasets/import",
                    files={"file": ("test.pdf", f, "application/pdf")},
                    data={"dataset_id": "TEST-v0.1.0"},
                )
            assert response.status_code == 400
        finally:
            os.unlink(path)
