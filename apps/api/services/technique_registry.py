"""
AstroOS — Technique Registry

Central in-code catalogue of TechniqueDefinitions, mirroring the
`_REGISTRY: dict[str, T]` + register/get/all convention already used by
rule_registry.py, dasha_registry.py and
jaimini_yoga_registry.py.

Techniques defined in code (see services/techniques/) register themselves
here at import time. This registry performs NO astrology and NO persistence;
it is the runtime lookup the TechniqueEngine and TechniqueResolver read from.
Persistence of technique metadata lives in models/technique.py +
repositories/technique_repository.py and is synced separately — the code
registry stays the authoritative source for the evaluable definition.

Because techniques may be re-imported (fixtures, tests) the registry keys on
(technique_id, version) so multiple immutable versions can coexist, matching
the soft-append versioning used for knowledge rules (migration 0008).
"""

from __future__ import annotations

from apps.api.domain.technique import TechniqueDefinition
from apps.api.services._registry import Registry

_registry: Registry[tuple[str, int], TechniqueDefinition] = Registry(
    hash_line=lambda key, technique: f"{key[0]}:{key[1]}\n"
)


def register_technique(technique: TechniqueDefinition) -> None:
    """Register a technique version; raises on duplicate (id, version)."""
    key = (technique.technique_id, technique.version)
    _registry.register(
        key, technique,
        duplicate_message=(
            f"Duplicate technique registered: {technique.technique_id!r} "
            f"v{technique.version}"
        ),
    )


def all_techniques() -> list[TechniqueDefinition]:
    """Every registered technique version, in registration order."""
    return _registry.all()


def get_technique(technique_id: str, version: int | None = None) -> TechniqueDefinition | None:
    """Look up a technique. With no version, returns the highest version."""
    if version is not None:
        return _registry.get((technique_id, version))
    versions = [t for t in all_techniques() if t.technique_id == technique_id]
    if not versions:
        return None
    return max(versions, key=lambda t: t.version)


def techniques_by_objective(objective: str) -> list[TechniqueDefinition]:
    """All current-version techniques whose objective matches (resolver aid)."""
    latest: dict[str, TechniqueDefinition] = {}
    for t in all_techniques():
        if t.objective != objective:
            continue
        cur = latest.get(t.technique_id)
        if cur is None or t.version > cur.version:
            latest[t.technique_id] = t
    return list(latest.values())


def registry_hash() -> str:
    """SHA-256 over (technique_id, version) pairs — experiment reproducibility,
    same idea as rule_registry.registry_hash()."""
    return _registry.hash()


def clear_registry() -> None:
    """Test-only: clear all registrations."""
    _registry.clear()
