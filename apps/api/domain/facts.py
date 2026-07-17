"""
AstroOS — Fact Domain Object (Module 13)

A Fact is a single standardized, named value derived from an existing
calculation engine's output — e.g. "planet.jupiter.house" = 1. This is
the ONLY vocabulary the Rule Engine is allowed to read from; it never
sees a D1Chart, a YogaResult, a BalaComponentResult, or any other
engine-internal object directly. FactBuilder is the sole translator
from "engine output" to "Fact"; RuleEngine only ever reads Facts back
out of a FactRegistry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Fact:
    """
    key: dotted-path string, e.g. "planet.jupiter.house", "yoga.BPHS-PM-001.present"
    value: the standardized value (bool/int/float/str) — never a Python
      object from an engine's own domain model.
    source: which engine/module produced this fact, e.g. "graha_engine",
      "yoga_engine" — kept for traceability, not used in evaluation logic.
    """
    key: str
    value: Any
    source: str
