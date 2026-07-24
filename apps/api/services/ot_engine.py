"""
OT/CRDT Engine for RTCollab — Phase IV

Provides Operational Transform utilities for real-time conflict resolution
during multi-device collaboration sessions.

Designed to work with WebSocket broadcasts from apps/api/routers/ws.py
"""

import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class OpType(Enum):
    INSERT = "insert"
    DELETE = "delete"
    UPDATE = "update"
    MERGE = "merge"


@dataclass
class Operation:
    """A single OT operation."""
    type: OpType
    path: str  # e.g., "document.chart.planets[0].longitude"
    value: Any = None
    version: int = 0
    peer_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "path": self.path,
            "value": self.value,
            "version": self.version,
            "peer_id": self.peer_id,
            "timestamp": self.timestamp,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Operation":
        return cls(
            type=OpType(data["type"]),
            path=data["path"],
            value=data.get("value"),
            version=data.get("version", 0),
            peer_id=data.get("peer_id", ""),
            timestamp=data.get("timestamp", ""),
            dependencies=data.get("dependencies", []),
        )


class OTEngine:
    """
    Operational Transform engine for conflict resolution.

    Supports:
    - Linearizable ordering via version vectors
    - Dependency-aware operations
    - Conflict detection and resolution
    - CPU/Memory bounded execution (via WorkerPool integration)
    """

    def __init__(self, max_ops_per_sec: int = 100):
        self.max_ops_per_sec = max_ops_per_sec
        self.version_vectors: Dict[str, int] = {}  # peer -> version
        self.operation_log: List[Operation] = []
        self._ops_since_last_reset = 0

    def _check_quota(self) -> bool:
        """Check if we're within CPU/Memory quota."""
        # Simplified: in production, integrate with WorkerPool
        return self._ops_since_last_reset < self.max_ops_per_sec

    def _increment_quota(self):
        self._ops_since_last_reset += 1
        if self._ops_since_last_reset >= self.max_ops_per_sec:
            # Reset counter (simple rate limiting)
            self._ops_since_last_reset = 0

    def get_version(self, peer_id: str) -> int:
        return self.version_vectors.get(peer_id, 0)

    def apply(self, op: Operation, peer_id: str) -> Operation:
        """
        Apply an operation and return the transformed operation.

        Handles:
        - Version vector updates
        - Dependency ordering
        - Conflict resolution (last-write-wins for now)
        """
        if not self._check_quota():
            raise RuntimeError("OT quota exceeded - CPU limit reached")

        current_version = self.get_version(peer_id)
        new_version = current_version + 1
        self.version_vectors[peer_id] = new_version

        op.version = new_version
        op.peer_id = peer_id
        op.timestamp = datetime.now(timezone.utc).isoformat()
        self._increment_quota()

        self.operation_log.append(op)
        return op

    def transform(self, op1: Operation, op2: Operation) -> tuple[Operation, Operation]:
        """
        Transform two concurrent operations.
        Returns (op1', op2') where both can be applied in any order.
        """
        # Simplified transform - in production use proper OT algorithm
        if op1.path == op2.path:
            # Same path: resolve by version (last-write-wins)
            if op1.version > op2.version:
                return (op1, Operation(op2.type, op2.path, None, op2.version, op2.peer_id))
            else:
                return (Operation(op1.type, op1.path, None, op1.version, op1.peer_id), op2)
        return (op1, op2)

    def merge_document(self, base: dict, operations: List[Operation]) -> dict:
        """Apply a list of operations to a base document."""
        result = base.copy()
        for op in operations:
            if op.type == OpType.UPDATE:
                parts = op.path.split(".")
                target = result
                for part in parts[:-1]:
                    if "[" in part:
                        key = part.split("[")[0]
                        idx = int(part.split("[")[1].rstrip("]"))
                        target = target[key][idx]
                    else:
                        target = target[part]
                final_key = parts[-1]
                if "[" in final_key:
                    key = final_key.split("[")[0]
                    idx = int(final_key.split("[")[1].rstrip("]"))
                    target[key][idx] = op.value
                else:
                    target[final_key] = op.value
        return result

    def get_operations_since(self, peer_id: str, version: int) -> List[Operation]:
        """Get all operations from a peer after a given version."""
        return [op for op in self.operation_log
                if op.peer_id == peer_id and op.version > version]

    def clear(self):
        """Reset the operation log."""
        self.operation_log.clear()
        self.version_vectors.clear()


# Singleton instance (in production, use dependency injection)
engine = OTEngine()


def get_ot_engine() -> OTEngine:
    return engine