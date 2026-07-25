"""
AstroOS — SDK Service Unit Tests (Module 25, Phase 1)
"""

import pytest

from apps.api.domain.sdk import ApiVersion
from apps.api.services.sdk_service import SdkService


class TestSdkService:
    def test_get_versions_returns_v1(self):
        versions = SdkService.get_versions()
        assert "v1" in versions
        assert versions["v1"].status == "current"

    def test_get_version_known(self):
        v = SdkService.get_version("v1")
        assert v is not None
        assert v.version == "v1"

    def test_get_version_unknown(self):
        v = SdkService.get_version("v99")
        assert v is None

    def test_success_response(self):
        resp = SdkService.success(data={"planet": "sun"})
        assert resp.success is True
        assert resp.data == {"planet": "sun"}
        assert resp.error is None
        assert resp.version == "v1"
        assert resp.request_id.startswith("req_")

    def test_success_with_pagination(self):
        from apps.api.domain.sdk import Pagination
        pagination = Pagination(limit=10, offset=0, total=50)
        resp = SdkService.success(data=[1, 2, 3], pagination=pagination)
        assert resp.pagination.total == 50

    def test_error_response(self):
        resp = SdkService.error("NOT_FOUND", "Resource not found")
        assert resp.success is False
        assert resp.error.code == "NOT_FOUND"
        assert resp.error.message == "Resource not found"
        assert resp.version == "v1"
