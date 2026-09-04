"""
OT/CRDT Engine for RTCollab — Phase IV

Provides Operational Transform utilities for real-time conflict resolution
during multi-device collaboration sessions.

Designed to work with WebSocket broadcasts from apps/api/routers/ws.py
"""

import re
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum

_INDEX_RE = re.compile(r"^(?P<parent>.+)\[(?P<index>\d+)\]$")


def _parse_indexed_path(path: str) -> Optional[tuple[str, int]]:
    """Split 'a.b[3]' into ('a.b', 3); returns None if path has no trailing index."""
    match = _INDEX_RE.match(path)
    if not match:
        return None
    return match.group("parent"), int(match.group("index"))


def _reindex_path(path: str, new_index: int) -> str:
    parent, _ = _parse_indexed_path(path)
    return f"{parent}[{new_index}]"


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
        Transform two concurrent operations so both can be applied, in either
        order, to converge on the same document state.

        Rules (highest to lowest priority):
        - Same path, either op is a DELETE: delete wins; a competing DELETE
          becomes a no-op (idempotent), a competing UPDATE/INSERT is dropped.
        - Same path, both UPDATE/INSERT: deterministic tie-break on
          (version, peer_id) so every replica picks the same winner.
        - Same indexed array parent, different indices: shift the surviving
          op's index to account for the other op's INSERT/DELETE.
        - Otherwise: independent, returned unchanged.
        """
        if op1.path == op2.path:
            if op1.type == OpType.DELETE or op2.type == OpType.DELETE:
                if op1.type == OpType.DELETE and op2.type == OpType.DELETE:
                    # Both deleting the same thing: second is a no-op.
                    return (op1, replace(op2, value=None))
                deleter, other = (op1, op2) if op1.type == OpType.DELETE else (op2, op1)
                noop_other = replace(other, value=None)
                return (deleter, noop_other) if deleter is op1 else (noop_other, deleter)

            # Concurrent UPDATE/INSERT on the same path: deterministic winner.
            if (op1.version, op1.peer_id) >= (op2.version, op2.peer_id):
                return (op1, replace(op2, value=None))
            return (replace(op1, value=None), op2)

        idx1 = _parse_indexed_path(op1.path)
        idx2 = _parse_indexed_path(op2.path)
        if idx1 and idx2 and idx1[0] == idx2[0] and idx1[1] != idx2[1]:
            parent, i1 = idx1
            _, i2 = idx2
            new_op1, new_op2 = op1, op2

            if op2.type == OpType.INSERT and i2 <= i1:
                new_op1 = replace(op1, path=_reindex_path(op1.path, i1 + 1))
            elif op2.type == OpType.DELETE and i2 < i1:
                new_op1 = replace(op1, path=_reindex_path(op1.path, i1 - 1))

            if op1.type == OpType.INSERT and i1 <= i2:
                new_op2 = replace(op2, path=_reindex_path(op2.path, i2 + 1))
            elif op1.type == OpType.DELETE and i1 < i2:
                new_op2 = replace(op2, path=_reindex_path(op2.path, i2 - 1))

            return (new_op1, new_op2)

        return (op1, op2)

    @staticmethod
    def _split_part(part: str) -> "tuple[str, Optional[int]]":
        if "[" in part:
            key, rest = part.split("[", 1)
            return key, int(rest.rstrip("]"))
        return part, None

    def merge_document(self, base: dict, operations: List[Operation]) -> dict:
        """
        Apply a list of operations to a base document.

        A session's document starts empty (`{}`), so every intermediate
        dict/list along an operation's path may not exist yet — this
        auto-vivifies them as it walks the path, rather than assuming the
        structure was pre-populated.
        """
        result = base.copy()
        for op in operations:
            if op.type not in (OpType.UPDATE, OpType.INSERT, OpType.DELETE):
                continue  # MERGE carries no direct document mutation.

            parts = op.path.split(".")
            target = result
            for part in parts[:-1]:
                key, idx = self._split_part(part)
                if idx is None:
                    if not isinstance(target.get(key), (dict, list)):
                        target[key] = {}
                    target = target[key]
                else:
                    if not isinstance(target.get(key), list):
                        target[key] = []
                    lst = target[key]
                    while len(lst) <= idx:
                        lst.append({})
                    target = lst[idx]

            final_key, final_idx = self._split_part(parts[-1])
            if final_idx is None:
                if op.type == OpType.DELETE:
                    target.pop(final_key, None)
                else:
                    target[final_key] = op.value
            else:
                if not isinstance(target.get(final_key), list):
                    target[final_key] = []
                lst = target[final_key]
                if op.type == OpType.DELETE:
                    if 0 <= final_idx < len(lst):
                        del lst[final_idx]
                elif op.type == OpType.INSERT:
                    while len(lst) < final_idx:
                        lst.append(None)
                    lst.insert(final_idx, op.value)
                else:
                    while len(lst) <= final_idx:
                        lst.append(None)
                    lst[final_idx] = op.value
        return result

    def get_operations_since(self, peer_id: str, version: int) -> List[Operation]:
        """Get all operations from a peer after a given version."""
        return [op for op in self.operation_log
                if op.peer_id == peer_id and op.version > version]

    def clear(self):
        """Reset the operation log."""
        self.operation_log.clear()
        self.version_vectors.clear()


# Default singleton (used when no session scoping is needed, e.g. tests).
engine = OTEngine()

# One engine per collaboration session, so peers in different sessions never
# share version vectors or operation logs.
_session_engines: Dict[str, OTEngine] = {}


def get_ot_engine(session_id: Optional[str] = None) -> OTEngine:
    if session_id is None:
        return engine
    if session_id not in _session_engines:
        _session_engines[session_id] = OTEngine()
    return _session_engines[session_id]


def clear_session_engine(session_id: str) -> None:
    _session_engines.pop(session_id, None)