"""
AstroOS — Gap 3: Symbolic Claim-Graph Grounding & Deterministic Verifier.

Rebuilds the claim graph from SlotManifest and verifies it is an exact SUBGRAPH
of the finding set. Zero model calls. Replaces embedding similarity as the primary
grounding mechanism.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

from apps.api.services.phalita_core.slot_contracts import CertaintyTier, SlotManifest, SlotType


@dataclass(frozen=True)
class Finding:
    finding_id: str
    slot_types: FrozenSet[SlotType]
    tier: CertaintyTier
    canonical_claim: str
    citations: FrozenSet[str]
    temporal_window: Optional[Tuple[date, date]]
    conflict_ratio: float
    domain: str = "general"
    calibrated_probability: Optional[float] = None


FORBIDDEN_PATTERNS: List[Tuple[str, str]] = [
    (r"\b(will definitely|is certain|guaranteed|unavoidable|destined)\b", "ABSOLUTIST_LANGUAGE"),
    (r"\b(cannot be predicted|no conclusion possible|impossible to say)\b", "OVER_SOFTENING"),
    (r"\b(\d{4})\b.*\b(\d{4})\b.*\b(unless|remedy|therefore)\b", "DATE_ADJACENT_INFERENCE"),
]

ABSTENTION_TEMPLATE = "The classical rule base provides insufficient confluence to assess this domain for this chart."
YOGA_TERM = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+){0,2})\s+[Yy]ogas?\b")


@dataclass
class SymbolicVerdict:
    passed: bool
    issues: List[Tuple[str, str]]

    @property
    def report(self) -> str:
        return "\n".join(f"[{t}] {d}" for t, d in self.issues) if self.issues else "PASS"


class SymbolicVerifier:
    def __init__(self, findings: Dict[str, Finding]):
        self.findings = findings
        # Build whitelist of legitimate yogas from canonical claims
        self.allowed_yogas = self._extract_allowed_yogas(findings.values())

    @staticmethod
    def _extract_allowed_yogas(findings: Sequence[Finding]) -> Set[str]:
        allowed = set()
        for f in findings:
            for m in YOGA_TERM.finditer(f.canonical_claim):
                full = m.group(1).lower().strip()
                allowed.add(full)
                # Also allow individual yoga components (e.g., "Raja" from "Parashari Raja")
                for part in full.split():
                    if len(part) >= 3 and part not in ("with", "classical", "parashari", "the", "and"):
                        allowed.add(part)
        return allowed

    def verify(self, manifest: SlotManifest) -> SymbolicVerdict:
        issues: List[Tuple[str, str]] = []

        for s in manifest.slots:
            f = self.findings.get(s.finding_id)
            if f is None:
                issues.append(("UNKNOWN_FINDING_REF", s.finding_id))
                continue

            # 1. Cross-domain check (RT-CROSS-DOM)
            if f.domain != "general" and f.domain.lower() != manifest.domain.lower():
                issues.append((
                    "CROSS_DOMAIN_VIOLATION",
                    f"{s.finding_id}: finding belongs to domain '{f.domain}', cannot be rendered in '{manifest.domain}' manifest",
                ))

            # 2. Slot-type legality
            if s.slot_type not in f.slot_types:
                issues.append((
                    "ILLEGAL_SLOT_TYPE",
                    f"{s.finding_id}: {s.slot_type.value} not permitted (finding offers {sorted(t.value for t in f.slot_types)})",
                ))

            # 3. Tier echo match
            if s.tier_echo != f.tier:
                issues.append((
                    "TIER_MISMATCH",
                    f"{s.finding_id}: echoed {s.tier_echo.value}, kernel says {f.tier.value}",
                ))

            # 4. Citation closure
            illegal_cit = set(s.citations) - set(f.citations)
            if illegal_cit:
                issues.append((
                    "FABRICATED_CITATION",
                    f"{s.finding_id}: {sorted(illegal_cit)} not attached to finding",
                ))

            # 5. Temporal closure
            if s.temporal_refs and f.temporal_window is None:
                issues.append(("FABRICATED_TIMING", f"{s.finding_id}: finding has no temporal window"))
            elif s.temporal_refs and f.temporal_window is not None:
                lo, hi = f.temporal_window
                for ref in s.temporal_refs:
                    y = self._parse_year(ref)
                    if y is None or not (lo.year - 1 <= y <= hi.year + 1):
                        issues.append((
                            "TIMING_OUT_OF_WINDOW",
                            f"{s.finding_id}: '{ref}' outside [{lo}, {hi}]",
                        ))

            # 6. Conflict obligation
            if f.conflict_ratio > 0.35 and s.slot_type == SlotType.EVENT_LIKELIHOOD:
                issues.append((
                    "CONFLICT_UNACKNOWLEDGED",
                    f"{s.finding_id}: likelihood slot present while conflict_ratio={f.conflict_ratio:.2f} — must use conflict_note framing",
                ))

            # 7. Forbidden-language lint
            for pat, tag in FORBIDDEN_PATTERNS:
                if re.search(pat, s.text, flags=re.IGNORECASE):
                    issues.append((tag, f"{s.finding_id}: {s.text[:80]}..."))

            # 8. Abstention template check
            if s.slot_type == SlotType.ABSTENTION:
                if ABSTENTION_TEMPLATE not in s.text:
                    issues.append((
                        "ABSTENTION_TEMPLATE_VIOLATION",
                        f"{s.finding_id}: abstention must include the canonical insufficient-confluence sentence",
                    ))

            # 9. Yoga name whitelist check (RT-NEW-YOGA)
            for m in YOGA_TERM.finditer(s.text):
                raw_yoga = m.group(1).lower().strip()
                tokens = [t for t in raw_yoga.split() if t not in ("classical", "the", "a", "an", "this", "parashari", "auspicious", "powerful")]
                is_allowed = any(t in self.allowed_yogas for t in tokens) if tokens else (raw_yoga in self.allowed_yogas)
                if not is_allowed:
                    issues.append((
                        "FABRICATED_YOGA",
                        f"{s.finding_id}: invented yoga name '{m.group(0)}' not in canonical findings",
                    ))

        # 10. Conflict-note obligation at manifest level
        rendered_fids = {s.finding_id for s in manifest.slots}
        high_conflict_rendered = [
            fid for fid in rendered_fids
            if fid in self.findings and self.findings[fid].conflict_ratio > 0.35
        ]
        noted = {s.finding_id for s in manifest.slots if s.slot_type == SlotType.CONFLICT_NOTE}
        missing = set(high_conflict_rendered) - noted
        if missing:
            issues.append((
                "CONFLICT_NOTE_MISSING",
                f"rendered findings with conflict_ratio > 0.35 lack conflict_note: {sorted(missing)}",
            ))

        return SymbolicVerdict(passed=not issues, issues=issues)

    @staticmethod
    def _parse_year(ref: str) -> Optional[int]:
        m = re.search(r"\b(1[89]\d{2}|20\d{2})\b", ref)
        return int(m.group(1)) if m else None
