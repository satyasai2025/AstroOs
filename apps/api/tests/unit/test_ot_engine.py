"""
Unit tests for OT Engine — Phase IV

Tests operational transform logic for RTCollab conflict resolution.
"""

import pytest
from apps.api.services.ot_engine import (
    OTEngine,
    Operation,
    OpType,
    get_ot_engine,
    clear_session_engine,
)


@pytest.fixture
def ot_engine():
    """Create a fresh OT engine for each test."""
    return OTEngine(max_ops_per_sec=100)


class TestOperation:
    def test_operation_creation(self):
        op = Operation(
            type=OpType.INSERT,
            path="chart.planets[0].longitude",
            value=120.5,
        )
        assert op.type == OpType.INSERT
        assert op.path == "chart.planets[0].longitude"
        assert op.value == 120.5

    def test_operation_to_dict(self):
        op = Operation(type=OpType.UPDATE, path="chart.name", value="Aries")
        data = op.to_dict()
        assert data["type"] == "update"
        assert data["path"] == "chart.name"
        assert data["value"] == "Aries"

    def test_operation_from_dict(self):
        data = {
            "type": "delete",
            "path": "chart.planets[1]",
            "value": None,
            "version": 5,
            "peer_id": "peer123",
        }
        op = Operation.from_dict(data)
        assert op.type == OpType.DELETE
        assert op.path == "chart.planets[1]"
        assert op.version == 5
        assert op.peer_id == "peer123"


class TestOTEngine:
    def test_engine_initial_state(self, ot_engine):
        assert ot_engine.get_version("peer1") == 0
        assert len(ot_engine.operation_log) == 0

    def test_apply_single_operation(self, ot_engine):
        op = Operation(type=OpType.INSERT, path="chart.name", value="Aries")
        result = ot_engine.apply(op, "peer1")

        assert result.version == 1
        assert result.peer_id == "peer1"
        assert len(ot_engine.operation_log) == 1

    def test_multiple_peers_version_vectors(self, ot_engine):
        op1 = Operation(type=OpType.UPDATE, path="chart.name", value="Aries")
        op2 = Operation(type=OpType.UPDATE, path="chart.name", value="Taurus")

        ot_engine.apply(op1, "peer1")
        ot_engine.apply(op2, "peer2")

        assert ot_engine.get_version("peer1") == 1
        assert ot_engine.get_version("peer2") == 1
        assert ot_engine.get_version("peer_unknown") == 0

    def test_transform_concurrent_same_path(self, ot_engine):
        op1 = Operation(type=OpType.UPDATE, path="chart.name", value="Aries")
        op2 = Operation(type=OpType.UPDATE, path="chart.name", value="Taurus")

        ot_engine.apply(op1, "peer1")
        ot_engine.apply(op2, "peer2")

        t1, t2 = ot_engine.transform(op1, op2)
        # Last-write-wins: peer2's op has higher version
        assert t1.value is None or t1.version < t2.version

    def test_transform_delete_wins_over_update(self, ot_engine):
        d = Operation(type=OpType.DELETE, path="chart.name")
        u = Operation(type=OpType.UPDATE, path="chart.name", value="Taurus")
        ot_engine.apply(d, "peer1")
        ot_engine.apply(u, "peer2")

        t1, t2 = ot_engine.transform(d, u)
        assert t1.type == OpType.DELETE
        assert t2.value is None

    def test_transform_double_delete_is_idempotent(self, ot_engine):
        d1 = Operation(type=OpType.DELETE, path="chart.name")
        d2 = Operation(type=OpType.DELETE, path="chart.name")
        ot_engine.apply(d1, "peer1")
        ot_engine.apply(d2, "peer2")

        t1, t2 = ot_engine.transform(d1, d2)
        assert t1.type == OpType.DELETE
        assert t2.value is None

    def test_transform_tie_break_is_deterministic(self, ot_engine):
        op1 = Operation(type=OpType.UPDATE, path="chart.name", value="Aries")
        op2 = Operation(type=OpType.UPDATE, path="chart.name", value="Taurus")
        ot_engine.apply(op1, "peer1")
        ot_engine.apply(op2, "peer2")

        first = ot_engine.transform(op1, op2)
        second = ot_engine.transform(op1, op2)
        assert first[0].value == second[0].value
        assert first[1].value == second[1].value

    def test_transform_insert_shifts_higher_index(self, ot_engine):
        ins = Operation(type=OpType.INSERT, path="chart.planets[1]", value="X")
        upd = Operation(type=OpType.UPDATE, path="chart.planets[3]", value="Y")
        ot_engine.apply(ins, "peer1")
        ot_engine.apply(upd, "peer2")

        t1, t2 = ot_engine.transform(ins, upd)
        assert t1.path == "chart.planets[1]"
        assert t2.path == "chart.planets[4]"

    def test_transform_delete_shifts_higher_index_down(self, ot_engine):
        d = Operation(type=OpType.DELETE, path="chart.planets[1]")
        upd = Operation(type=OpType.UPDATE, path="chart.planets[3]", value="Y")
        ot_engine.apply(d, "peer1")
        ot_engine.apply(upd, "peer2")

        t1, t2 = ot_engine.transform(d, upd)
        assert t1.path == "chart.planets[1]"
        assert t2.path == "chart.planets[2]"

    def test_transform_insert_does_not_shift_lower_index(self, ot_engine):
        ins = Operation(type=OpType.INSERT, path="chart.planets[3]", value="X")
        upd = Operation(type=OpType.UPDATE, path="chart.planets[1]", value="Y")
        ot_engine.apply(ins, "peer1")
        ot_engine.apply(upd, "peer2")

        t1, t2 = ot_engine.transform(ins, upd)
        assert t1.path == "chart.planets[3]"
        assert t2.path == "chart.planets[1]"

    def test_transform_concurrent_different_paths(self, ot_engine):
        op1 = Operation(type=OpType.INSERT, path="chart.name", value="Aries")
        op2 = Operation(type=OpType.INSERT, path="chart.house[0]", value="Aries")

        t1, t2 = ot_engine.transform(op1, op2)
        # Different paths should not conflict
        assert t1.path == op1.path
        assert t2.path == op2.path

    def test_merge_document(self, ot_engine):
        base = {"chart": {"name": "", "planets": [{"longitude": 0}]}}
        ops = [
            Operation(type=OpType.UPDATE, path="chart.name", value="Aries"),
            Operation(type=OpType.UPDATE, path="chart.planets[0].longitude", value=120.5),
        ]

        for op in ops:
            ot_engine.apply(op, "peer1")

        result = ot_engine.merge_document(base, ops)
        assert result["chart"]["name"] == "Aries"
        assert result["chart"]["planets"][0]["longitude"] == 120.5

    def test_get_operations_since(self, ot_engine):
        op1 = Operation(type=OpType.INSERT, path="a", value=1)
        op2 = Operation(type=OpType.INSERT, path="b", value=2)

        ot_engine.apply(op1, "peer1")
        ot_engine.apply(op2, "peer1")

        ops = ot_engine.get_operations_since("peer1", 0)
        assert len(ops) == 2

        ops_after_1 = ot_engine.get_operations_since("peer1", 1)
        assert len(ops_after_1) == 1
        assert ops_after_1[0].path == "b"

    def test_clear_resets_state(self, ot_engine):
        op = Operation(type=OpType.INSERT, path="chart.name", value="Aries")
        ot_engine.apply(op, "peer1")

        ot_engine.clear()

        assert ot_engine.get_version("peer1") == 0
        assert len(ot_engine.operation_log) == 0


class TestOTEngineSingleton:
    def test_get_ot_engine_returns_singleton(self):
        engine1 = get_ot_engine()
        engine2 = get_ot_engine()
        assert engine1 is engine2


class TestOTEngineSessionScoping:
    def test_same_session_id_returns_same_engine(self):
        e1 = get_ot_engine("session-a")
        e2 = get_ot_engine("session-a")
        assert e1 is e2
        clear_session_engine("session-a")

    def test_different_sessions_have_independent_state(self):
        e1 = get_ot_engine("session-b")
        e2 = get_ot_engine("session-c")
        assert e1 is not e2

        e1.apply(Operation(type=OpType.UPDATE, path="chart.name", value="Aries"), "peer1")
        assert e1.get_version("peer1") == 1
        assert e2.get_version("peer1") == 0

        clear_session_engine("session-b")
        clear_session_engine("session-c")

    def test_clear_session_engine_removes_state(self):
        e1 = get_ot_engine("session-d")
        e1.apply(Operation(type=OpType.UPDATE, path="chart.name", value="Aries"), "peer1")

        clear_session_engine("session-d")
        e2 = get_ot_engine("session-d")
        assert e2 is not e1
        assert e2.get_version("peer1") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])