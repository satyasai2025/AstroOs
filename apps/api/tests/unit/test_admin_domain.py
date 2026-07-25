"""
AstroOS — Admin Domain Model Unit Tests (Module 23, Phase 1)
"""

import dataclasses
import uuid
from datetime import datetime

import pytest

from apps.api.domain.admin import AdminUserSummary, ModuleHealth, SystemStatus


class TestModuleHealth:
    def test_is_frozen(self):
        h = ModuleHealth(module_name="test", status="ok", version="1.0")
        with pytest.raises(dataclasses.FrozenInstanceError):
            h.status = "error"

    def test_default_message(self):
        h = ModuleHealth(module_name="test", status="ok", version="1.0")
        assert h.message == ""


class TestSystemStatus:
    def test_defaults(self):
        s = SystemStatus(status="healthy")
        assert s.modules == {}
        assert s.ephemeris_mode == ""

    def test_with_modules(self):
        h = ModuleHealth(module_name="test", status="ok", version="1.0")
        s = SystemStatus(status="healthy", modules={"test": h})
        assert s.modules["test"].module_name == "test"


class TestAdminUserSummary:
    def test_is_frozen(self):
        u = AdminUserSummary(
            id=uuid.uuid4(), email="a@b.com", display_name="A",
            role="admin", status="active",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            u.role = "researcher"

    def test_optional_dates(self):
        u = AdminUserSummary(
            id=uuid.uuid4(), email="a@b.com", display_name="A",
            role="researcher", status="active",
        )
        assert u.created_at is None
        assert u.last_login_at is None
