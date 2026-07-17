"""
AstroOS — SDK Domain Model Unit Tests (Module 25, Phase 1)
"""

import dataclasses

import pytest

from apps.api.domain.sdk import ApiError, ApiResponse, ApiVersion, Pagination, SdkConfig


class TestApiVersion:
    def test_is_frozen(self):
        v = ApiVersion(version="v1", status="current")
        with pytest.raises(dataclasses.FrozenInstanceError):
            v.status = "deprecated"

    def test_defaults(self):
        v = ApiVersion(version="v1", status="current")
        assert v.deprecated_at is None
        assert v.release_notes == ""


class TestApiError:
    def test_is_frozen(self):
        e = ApiError(code="ERR", message="error")
        with pytest.raises(dataclasses.FrozenInstanceError):
            e.code = "OTHER"

    def test_optional_fields(self):
        e = ApiError(code="ERR", message="error", details={"field": "x"})
        assert e.details == {"field": "x"}
        assert e.request_id is None


class TestPagination:
    def test_defaults(self):
        p = Pagination()
        assert p.limit == 100
        assert p.offset == 0
        assert p.total is None

    def test_with_total(self):
        p = Pagination(limit=10, offset=20, total=100)
        assert p.total == 100


class TestApiResponse:
    def test_success_response(self):
        r = ApiResponse(success=True, data={"key": "val"})
        assert r.success is True
        assert r.data == {"key": "val"}
        assert r.error is None

    def test_error_response(self):
        err = ApiError(code="NOT_FOUND", message="not found")
        r = ApiResponse(success=False, error=err)
        assert r.success is False
        assert r.error.code == "NOT_FOUND"

    def test_default_version(self):
        r = ApiResponse(success=True)
        assert r.version == "v1"


class TestSdkConfig:
    def test_defaults(self):
        c = SdkConfig()
        assert c.base_url == "https://api.astroos.dev/v1"
        assert c.timeout == 30
        assert c.retry_count == 3
