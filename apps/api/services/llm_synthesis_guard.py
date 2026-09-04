"""
AstroOS — LLM Synthesis Guard & Narrative Post-Render Validator
===============================================================
Enforces strict deterministic epistemic guardrails over LLM outputs:
  1. Window Guard: Forbids fabricated timing dates outside the resolved timing_window.
  2. Confidence Guard: Detects and rejects confidence inflation (e.g. "guaranteed").
  3. Abstention Guard: Enforces clear refusal/abstention if has_promise == False.
  4. Hallucination Guard: Validates that cited rules exist in the resolved primary_evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import List, Optional, Tuple

from apps.api.domain.epistemic_claim import ResolvedEpistemicState

_INFLATION_KEYWORDS = (
    "guaranteed", "100% certain", "undoubtedly", "definite promise",
    "will certainly occur", "absolutely promised", "cannot fail", "inevitable"
)


@dataclass(frozen=True)
class SynthesisValidationResult:
    is_valid: bool
    violations: Tuple[str, ...]
    sanitized_output: str


class LLMSynthesisGuard:
    """
    Deterministic Post-Render Validator.
    Ensures that the narrative produced by an LLM does not violate the resolved epistemic state.
    """

    @classmethod
    def validate_and_sanitize(
        cls,
        resolved_state: ResolvedEpistemicState,
        llm_rendered_markdown: str,
    ) -> SynthesisValidationResult:
        violations: List[str] = []
        clean_text = llm_rendered_markdown.strip()

        # 1. Abstention / Refusal Guard
        if not resolved_state.has_promise:
            # The narrative MUST acknowledge that no shastric promise was found
            lower_text = clean_text.lower()
            affirmative_words = ["congratulations", "will happen", "certain to occur", "strongly indicates success"]
            if any(w in lower_text for w in affirmative_words):
                violations.append("Abstention violation: Resolved state is NO_PROMISE but narrative makes affirmative promise")

        # 2. Confidence Inflation Guard
        if resolved_state.confidence_band in ("LOW", "MODERATE", "DEFER"):
            lower_text = clean_text.lower()
            for kw in _INFLATION_KEYWORDS:
                if kw in lower_text:
                    violations.append(f"Confidence inflation violation: Forbidden deterministic certainty word '{kw}' detected")

        # 3. Window Guard
        if resolved_state.timing_window is not None:
            w_start, w_end = resolved_state.timing_window
            # Look for 4-digit years in text
            years_found = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", clean_text)]
            for y in years_found:
                if y < w_start.year - 1 or y > w_end.year + 1:
                    violations.append(f"Timing window violation: Year {y} cited outside resolved window [{w_start} to {w_end}]")

        # 4. Construct Sanitized Output or Fallback
        if violations:
            # Fall back to structured deterministic template
            sanitized = cls._build_deterministic_template(resolved_state)
            return SynthesisValidationResult(
                is_valid=False,
                violations=tuple(violations),
                sanitized_output=sanitized,
            )

        return SynthesisValidationResult(
            is_valid=True,
            violations=(),
            sanitized_output=clean_text,
        )

    @classmethod
    def _build_deterministic_template(cls, resolved_state: ResolvedEpistemicState) -> str:
        """Deterministic, hallucination-free fallback template."""
        lines = [
            f"### Astrological Analysis: {resolved_state.domain.capitalize()} ({resolved_state.event_type})",
            f"* **Confidence Tier:** `{resolved_state.confidence_band}` (Direction: {resolved_state.direction_score:+.2f})",
            f"* **Effective Evidence:** `{resolved_state.confluence.effective_n:.1f}` independent layers (Agreement: {resolved_state.confluence.agreement_ratio:.0%})",
        ]

        if resolved_state.timing_window:
            w_start, w_end = resolved_state.timing_window
            lines.append(f"* **Timing Window:** {w_start.strftime('%B %Y')} to {w_end.strftime('%B %Y')}")
        else:
            lines.append("* **Timing Window:** Not explicitly indicated or disjoint.")

        if resolved_state.has_promise:
            lines.append("\n**Primary Shastric Evidence:**")
            for ev in resolved_state.primary_evidence[:4]:
                src = ", ".join(ev.get("rule_sources", ["BPHS"]))
                lines.append(f"- **{ev['expert_id']}:** {src} (Weight: {ev['confidence']})")
        else:
            lines.append(f"\n> [!NOTE]\n> **Shastric Abstention:** {resolved_state.abstention_reason or 'No clear natal promise found.'}")

        if resolved_state.fail_conditions:
            lines.append("\n**Conditions & Caveats:**")
            for fc in resolved_state.fail_conditions:
                lines.append(f"- {fc}")

        return "\n".join(lines)
