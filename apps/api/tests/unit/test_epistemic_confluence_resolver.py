"""
AstroOS — Unit Tests for Epistemic Governance, Confluence Resolver, and LLM Guard
"""

import pytest
from datetime import date

from apps.api.domain.epistemic_claim import Claim, ResolvedEpistemicState
from apps.api.services.confluence_resolver import ConfluenceResolver
from apps.api.services.llm_synthesis_guard import LLMSynthesisGuard


def test_confluence_resolver_redundancy_adjustment():
    """Verify that two rules relying on the same underlying planet/house have discounted Effective-N."""
    claim1 = Claim(
        expert_id="jha.d1_bhavachalita",
        domain="career",
        event_type="career.promotion",
        claim_type="promise",
        direction=0.85,
        support={"house": 10},
        rule_sources=("BPHS Ch. 29",),
        expert_internal_confidence=0.9,
        underlying_factors=("jupiter", "10th_house"),
    )

    # Claim 2 uses the EXACT same underlying factors (correlated/redundant)
    claim2 = Claim(
        expert_id="divisional.d10_dignity",
        domain="career",
        event_type="career.promotion",
        claim_type="promise",
        direction=0.80,
        support={"d10_house": 10},
        rule_sources=("BPHS Ch. 7",),
        expert_internal_confidence=0.85,
        underlying_factors=("jupiter", "10th_house"),
    )

    resolved = ConfluenceResolver.resolve([claim1, claim2], "career", "career.promotion")
    assert resolved.confluence.raw_claims_count == 2
    # Effective-N must be strictly less than 2 due to 100% factor overlap
    assert resolved.confluence.effective_n < 2.0
    assert resolved.confluence.redundancy_discount > 0.0


def test_confluence_resolver_timing_window_intersection():
    """Verify that timing windows are strictly intersected (never averaged)."""
    # Dasha timing window: Jan 2026 to Dec 2028
    claim_dasha = Claim(
        expert_id="vimsottari.ad",
        domain="career",
        event_type="career.promotion",
        claim_type="timing",
        direction=0.8,
        support={},
        rule_sources=(),
        expert_internal_confidence=0.9,
        timing_window=(date(2026, 1, 1), date(2028, 12, 31)),
    )

    # Gochar timing window: March 2027 to Oct 2027
    claim_gochar = Claim(
        expert_id="gochar.jupiter_10th",
        domain="career",
        event_type="career.promotion",
        claim_type="timing",
        direction=0.85,
        support={},
        rule_sources=(),
        expert_internal_confidence=0.85,
        timing_window=(date(2027, 3, 1), date(2027, 10, 31)),
    )

    resolved = ConfluenceResolver.resolve([claim_dasha, claim_gochar], "career", "career.promotion")
    # Expected intersection: exactly [2027-03-01 to 2027-10-31]
    assert resolved.timing_window == (date(2027, 3, 1), date(2027, 10, 31))


def test_confluence_resolver_refusal_and_abstention():
    """Verify that when evidence is weak or negative, resolver emits DEFER and has_promise=False."""
    neg_claim = Claim(
        expert_id="dusthana.affliction",
        domain="marriage",
        event_type="marriage.ceremony",
        claim_type="promise",
        direction=-0.75,
        support={},
        rule_sources=(),
        expert_internal_confidence=0.8,
        underlying_factors=("saturn_in_7th",),
    )

    resolved = ConfluenceResolver.resolve([neg_claim], "marriage", "marriage.ceremony")
    assert resolved.has_promise is False
    assert resolved.confidence_band == "DEFER"
    assert resolved.abstention_reason is not None


def test_llm_synthesis_guard_catches_inflation():
    """Verify that LLMSynthesisGuard catches confidence inflation like 'guaranteed'."""
    claim = Claim(
        expert_id="jha.d1_bhavachalita",
        domain="career",
        event_type="career.promotion",
        claim_type="promise",
        direction=0.75,
        support={},
        rule_sources=(),
        expert_internal_confidence=0.8,
        underlying_factors=("sun", "10th_house"),
    )

    resolved = ConfluenceResolver.resolve([claim], "career", "career.promotion")

    hallucinated_text = "This promotion is guaranteed to happen in 2027!"
    res = LLMSynthesisGuard.validate_and_sanitize(resolved, hallucinated_text)

    assert res.is_valid is False
    assert any("Confidence inflation" in v for v in res.violations)
    assert "guaranteed" not in res.sanitized_output
