"""
AstroOS — Workstream C: Machine-Loadable Rule Registry Loader & Runtime Enforcement.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional

import yaml

RULE_ID_RE = re.compile(r"^JHA-\d+[A-Z]?(-\d+)?$")
VALID_SLOT_TYPES = {
    "state_level",
    "event_likelihood",
    "timing_window",
    "conflict_note",
    "abstention",
    "remediation_ref",
}


@dataclass(frozen=True)
class RegistryRule:
    rule_id: str
    domain: str
    statement: str
    status: str
    formula: dict
    weight_prior: Optional[dict]
    precedence_tier: Optional[int]
    produces_finding_types: FrozenSet[str]

    @property
    def benchmark_eligible(self) -> bool:
        return self.status != "UNVERIFIED"


class RuleRegistry:
    def __init__(self, path: str | Path):
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        self.version = raw.get("registry_version", "REG-0")
        self.rules: Dict[str, RegistryRule] = {}

        for r in raw.get("rules", []):
            rid = r.get("rule_id") or r.get("id")
            assert rid and RULE_ID_RE.match(rid), f"bad rule id: {rid}"
            assert r.get("status") in ("VERIFIED_SOURCE", "DOCTRINE_DECISION", "UNVERIFIED")
            bad = set(r.get("produces_finding_types", [])) - VALID_SLOT_TYPES
            assert not bad, f"{rid}: illegal finding types {bad}"

            self.rules[rid] = RegistryRule(
                rule_id=rid,
                domain=r.get("domain", "general"),
                statement=r.get("statement", ""),
                status=r.get("status"),
                formula=r.get("formula", {}),
                weight_prior=r.get("weight_prior"),
                precedence_tier=r.get("precedence_tier"),
                produces_finding_types=frozenset(r.get("produces_finding_types", [])),
            )

        with open(path, "rb") as f:
            self.hash = hashlib.sha256(f.read()).hexdigest()[:16]

    def benchmark_rules(self) -> List[RegistryRule]:
        return [r for r in self.rules.values() if r.benchmark_eligible]
