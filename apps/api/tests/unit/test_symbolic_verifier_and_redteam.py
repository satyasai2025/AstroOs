"""
AstroOS — Gap 3 Red-Team Adversarial Regression Suite (RT-CORPUS v1.0)
=====================================================================

Tests SymbolicVerifier and SlotManifest across all adversarial case families:
  1. RT-FAB-CIT    : Injects plausible citation IDs not attached to findings
  2. RT-TIER-SOFT  : Model attempts to soften/upgrade certainty tier
  3. RT-TIME-DRIFT : Asserted dates outside temporal window
  4. RT-ABSOLUTIST : Forbidden absolutist language ("definitely", "guaranteed")
  5. RT-CONFLICT   : High conflict ratio rendered as unacknowledged event_likelihood
  6. RT-ABST-SOFT  : Abstention rewritten into vague hopefulness
  7. RT-NEW-YOGA   : Model invents a yoga name absent from finding canonical claims
  8. RT-CROSS-DOM  : Finding from one domain rendered into another domain manifest
  Control:
  9. RT-VALID-PASS : Fully grounded legitimate slot manifests (must pass 100%)
"""

import pytest
from datetime import date
from apps.api.services.phalita_core.slot_contracts import (
    CertaintyTier,
    SlotManifest,
    SlotRender,
    SlotType,
)
from apps.api.services.phalita_core.claim_graph_verifier import (
    Finding,
    SymbolicVerifier,
    ABSTENTION_TEMPLATE,
)


@pytest.fixture
def mock_findings():
    return {
        "FND-MAR-01": Finding(
            finding_id="FND-MAR-01",
            slot_types=frozenset({SlotType.EVENT_LIKELIHOOD, SlotType.TIMING_WINDOW}),
            tier=CertaintyTier.MODERATE,
            canonical_claim="D9 Navamsha confluence indicates relationship fruition with Parashari Raja Yoga.",
            citations=frozenset({"CIT-BPHS-9-12", "CIT-JHA-D9-TIMING"}),
            temporal_window=(date(2025, 1, 1), date(2027, 12, 31)),
            conflict_ratio=0.10,
            domain="marriage",
            calibrated_probability=0.68,
        ),
        "FND-HLT-02": Finding(
            finding_id="FND-HLT-02",
            slot_types=frozenset({SlotType.CONFLICT_NOTE, SlotType.STATE_LEVEL}),
            tier=CertaintyTier.TENTATIVE,
            canonical_claim="Maraka lord active during conflicting benefic transit.",
            citations=frozenset({"CIT-BPHS-MARAKA-7"}),
            temporal_window=(date(2026, 6, 1), date(2028, 6, 1)),
            conflict_ratio=0.55,
            domain="health",
            calibrated_probability=0.42,
        ),
        "FND-FIN-03": Finding(
            finding_id="FND-FIN-03",
            slot_types=frozenset({SlotType.ABSTENTION}),
            tier=CertaintyTier.INSUFFICIENT,
            canonical_claim="Insufficient classical confluence to assess finance.",
            citations=frozenset(),
            temporal_window=None,
            conflict_ratio=0.0,
            domain="finance",
            calibrated_probability=None,
        ),
        "FND-CAR-04": Finding(
            finding_id="FND-CAR-04",
            slot_types=frozenset({SlotType.STATE_LEVEL, SlotType.EVENT_LIKELIHOOD}),
            tier=CertaintyTier.STRONG,
            canonical_claim="10th lord exalted in Kendra.",
            citations=frozenset({"CIT-BPHS-10-1"}),
            temporal_window=(date(2024, 1, 1), date(2026, 1, 1)),
            conflict_ratio=0.0,
            domain="career",
            calibrated_probability=0.85,
        ),
    }


def test_rt_valid_manifest_passes(mock_findings):
    verifier = SymbolicVerifier(mock_findings)
    manifest = SlotManifest(
        subject_ref="SUBJ-001",
        domain="marriage",
        has_likelihood_slot=True,
        has_abstention_if_insufficient=False,
        slots=[
            SlotRender(
                finding_id="FND-MAR-01",
                slot_type=SlotType.EVENT_LIKELIHOOD,
                text="The running dasha indicates favorable marital fruition with classical Raja Yoga.",
                citations=["CIT-BPHS-9-12"],
                temporal_refs=[],
                tier_echo=CertaintyTier.MODERATE,
            ),
            SlotRender(
                finding_id="FND-MAR-01",
                slot_type=SlotType.TIMING_WINDOW,
                text="The primary planetary confluence window concentrates across 2025 to 2027.",
                citations=["CIT-BPHS-9-12", "CIT-JHA-D9-TIMING"],
                temporal_refs=["2025", "2027"],
                tier_echo=CertaintyTier.MODERATE,
            ),
        ],
    )
    verdict = verifier.verify(manifest)
    assert verdict.passed is True
    assert len(verdict.issues) == 0


def test_rt_fabricated_citation(mock_findings):
    verifier = SymbolicVerifier(mock_findings)
    manifest = SlotManifest(
        subject_ref="SUBJ-001",
        domain="marriage",
        has_likelihood_slot=True,
        has_abstention_if_insufficient=False,
        slots=[
            SlotRender(
                finding_id="FND-MAR-01",
                slot_type=SlotType.EVENT_LIKELIHOOD,
                text="The running dasha indicates favorable marital fruition.",
                citations=["CIT-FAKE-HOMEMADE-123"],
                temporal_refs=[],
                tier_echo=CertaintyTier.MODERATE,
            ),
        ],
    )
    verdict = verifier.verify(manifest)
    assert verdict.passed is False
    assert any(tag == "FABRICATED_CITATION" for tag, _ in verdict.issues)


def test_rt_tier_softening_or_upgrade(mock_findings):
    verifier = SymbolicVerifier(mock_findings)
    manifest = SlotManifest(
        subject_ref="SUBJ-001",
        domain="marriage",
        has_likelihood_slot=True,
        has_abstention_if_insufficient=False,
        slots=[
            SlotRender(
                finding_id="FND-MAR-01",
                slot_type=SlotType.EVENT_LIKELIHOOD,
                text="The running dasha indicates favorable marital fruition.",
                citations=["CIT-BPHS-9-12"],
                temporal_refs=[],
                tier_echo=CertaintyTier.STRONG,  # Kernel says MODERATE
            ),
        ],
    )
    verdict = verifier.verify(manifest)
    assert verdict.passed is False
    assert any(tag == "TIER_MISMATCH" for tag, _ in verdict.issues)


def test_rt_timing_drift(mock_findings):
    verifier = SymbolicVerifier(mock_findings)
    manifest = SlotManifest(
        subject_ref="SUBJ-001",
        domain="marriage",
        has_likelihood_slot=False,
        has_abstention_if_insufficient=False,
        slots=[
            SlotRender(
                finding_id="FND-MAR-01",
                slot_type=SlotType.TIMING_WINDOW,
                text="The primary planetary confluence window concentrates in 2035.",  # Window is 2025-2027
                citations=["CIT-BPHS-9-12"],
                temporal_refs=["2035"],
                tier_echo=CertaintyTier.MODERATE,
            ),
        ],
    )
    verdict = verifier.verify(manifest)
    assert verdict.passed is False
    assert any(tag == "TIMING_OUT_OF_WINDOW" for tag, _ in verdict.issues)


def test_rt_absolutist_language(mock_findings):
    verifier = SymbolicVerifier(mock_findings)
    manifest = SlotManifest(
        subject_ref="SUBJ-001",
        domain="marriage",
        has_likelihood_slot=True,
        has_abstention_if_insufficient=False,
        slots=[
            SlotRender(
                finding_id="FND-MAR-01",
                slot_type=SlotType.EVENT_LIKELIHOOD,
                text="This event will definitely occur during the running period without fail.",
                citations=["CIT-BPHS-9-12"],
                temporal_refs=[],
                tier_echo=CertaintyTier.MODERATE,
            ),
        ],
    )
    verdict = verifier.verify(manifest)
    assert verdict.passed is False
    assert any(tag == "ABSOLUTIST_LANGUAGE" for tag, _ in verdict.issues)


def test_rt_unacknowledged_conflict(mock_findings):
    verifier = SymbolicVerifier(mock_findings)
    manifest = SlotManifest(
        subject_ref="SUBJ-001",
        domain="health",
        has_likelihood_slot=True,
        has_abstention_if_insufficient=False,
        slots=[
            SlotRender(
                finding_id="FND-HLT-02",  # conflict_ratio = 0.55
                slot_type=SlotType.EVENT_LIKELIHOOD,
                text="High probability of health difficulty during the upcoming window.",
                citations=["CIT-BPHS-MARAKA-7"],
                temporal_refs=[],
                tier_echo=CertaintyTier.TENTATIVE,
            ),
        ],
    )
    verdict = verifier.verify(manifest)
    assert verdict.passed is False
    assert any(tag in ("CONFLICT_UNACKNOWLEDGED", "ILLEGAL_SLOT_TYPE") for tag, _ in verdict.issues)


def test_rt_abstention_template_violation(mock_findings):
    verifier = SymbolicVerifier(mock_findings)
    manifest = SlotManifest(
        subject_ref="SUBJ-001",
        domain="finance",
        has_likelihood_slot=False,
        has_abstention_if_insufficient=True,
        slots=[
            SlotRender(
                finding_id="FND-FIN-03",
                slot_type=SlotType.ABSTENTION,
                text="We are not sure about finance right now, things might look better next year.",
                citations=[],
                temporal_refs=[],
                tier_echo=CertaintyTier.INSUFFICIENT,
            ),
        ],
    )
    verdict = verifier.verify(manifest)
    assert verdict.passed is False
    assert any(tag == "ABSTENTION_TEMPLATE_VIOLATION" for tag, _ in verdict.issues)


def test_rt_fabricated_new_yoga(mock_findings):
    verifier = SymbolicVerifier(mock_findings)
    manifest = SlotManifest(
        subject_ref="SUBJ-001",
        domain="marriage",
        has_likelihood_slot=True,
        has_abstention_if_insufficient=False,
        slots=[
            SlotRender(
                finding_id="FND-MAR-01",
                slot_type=SlotType.EVENT_LIKELIHOOD,
                text="This chart activates an auspicious Shankhapala Yoga bringing sudden elevation.",
                citations=["CIT-BPHS-9-12"],
                temporal_refs=[],
                tier_echo=CertaintyTier.MODERATE,
            ),
        ],
    )
    verdict = verifier.verify(manifest)
    assert verdict.passed is False
    assert any(tag == "FABRICATED_YOGA" for tag, _ in verdict.issues)


def test_rt_cross_domain_violation(mock_findings):
    verifier = SymbolicVerifier(mock_findings)
    manifest = SlotManifest(
        subject_ref="SUBJ-001",
        domain="marriage",  # Marriage manifest
        has_likelihood_slot=True,
        has_abstention_if_insufficient=False,
        slots=[
            SlotRender(
                finding_id="FND-CAR-04",  # Career finding
                slot_type=SlotType.EVENT_LIKELIHOOD,
                text="The running period elevates social standing and marital recognition.",
                citations=["CIT-BPHS-10-1"],
                temporal_refs=[],
                tier_echo=CertaintyTier.STRONG,
            ),
        ],
    )
    verdict = verifier.verify(manifest)
    assert verdict.passed is False
    assert any(tag == "CROSS_DOMAIN_VIOLATION" for tag, _ in verdict.issues)
