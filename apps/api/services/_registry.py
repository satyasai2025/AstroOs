"""
AstroOS — Generic In-Process Registry Helper

`rule_registry.py` and `technique_registry.py` each independently
reimplemented the same `_REGISTRY: dict[K, T]` + register/get/all/hash/clear
pattern. This module factors out that shared mechanics; each registry module
keeps its own public function-based API (register_rule/get_rule/... vs
register_technique/get_technique/...) and its own key shape (str vs
tuple[str, int]) and duplicate/idempotent semantics — only the underlying
dict bookkeeping is shared.
"""

from __future__ import annotations

import hashlib
from typing import Callable, Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class Registry(Generic[K, V]):
    """Minimal in-process dict-backed registry: register (raise on duplicate
    key), idempotent set, get, all (registration order), a reproducibility
    hash over sorted keys, and a test-only clear."""

    def __init__(self, *, hash_line: Callable[[K, V], str]) -> None:
        self._items: dict[K, V] = {}
        self._hash_line = hash_line

    def register(self, key: K, value: V, *, duplicate_message: str) -> None:
        if key in self._items:
            raise ValueError(duplicate_message)
        self._items[key] = value

    def contains(self, key: K) -> bool:
        return key in self._items

    def set(self, key: K, value: V) -> None:
        """Unconditional insert/overwrite — used for idempotent registration."""
        self._items[key] = value

    def get(self, key: K) -> V | None:
        return self._items.get(key)

    def all(self) -> list[V]:
        """All registered values, in registration order."""
        return list(self._items.values())

    def hash(self) -> str:
        """SHA-256 over sorted keys, one `hash_line(key, value)` per entry."""
        hasher = hashlib.sha256()
        for key in sorted(self._items):
            hasher.update(self._hash_line(key, self._items[key]).encode())
        return hasher.hexdigest()

    def clear(self) -> None:
        self._items.clear()
