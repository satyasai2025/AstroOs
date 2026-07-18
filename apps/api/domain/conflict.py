"""
AstroOS — Conflict Domain Objects (Phase D)

Represents documented doctrinal conflicts between astrological traditions.
Loaded from the YAML files in knowledge/conflicts/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ConflictPosition:
    """One position within a doctrinal conflict."""
    tradition: str
    source_ref: str
    position: str
    arguments: tuple[str, ...] = ()
    adherents: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConflictEvidence:
    """Evidence supporting each side of a conflict."""
    analysis: str
    for_parashari: tuple[str, ...] = ()
    for_kp: tuple[str, ...] = ()
    for_jaimini: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConflictResolution:
    """Resolution of a doctrinal conflict."""
    status: str  # "resolved", "partially-resolved", "unresolved"
    resolution: str = ""
    recommended_position: str = ""
    weight_of_evidence: str = ""


@dataclass(frozen=True)
class KnowledgeConflict:
    """A documented doctrinal conflict between traditions."""
    id: str
    name: str
    topic: str = ""
    domain: str = ""
    status: str = "active"
    confidence: str = "high"
    version: str = "1.0"
    last_verified: str = ""
    positions: tuple[ConflictPosition, ...] = ()
    evidence: Optional[ConflictEvidence] = None
    resolution: Optional[ConflictResolution] = None
    related_conflicts: tuple[str, ...] = ()
