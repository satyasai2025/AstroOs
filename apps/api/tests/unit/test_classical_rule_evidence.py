"""
Unit tests for Classical Rule Evidence Engine (Module 19, Phase 3)
"""

import pytest
from apps.api.domain.classical_rule_evidence import (
    ClassicalTradition,
    EvidenceVerificationStatus,
)
from apps.api.services.classical_rule_evidence_engine import (
    ClassicalRuleEvidenceEngine,
    ClassicalRuleRegistry,
)


class TestClassicalRuleEvidenceEngine:
    def test_canonical_registry_integrity(self):
        rules = ClassicalRuleRegistry.get_canonical_rules()
        assert len(rules) >= 8

        traditions = {r["citation"].tradition for r in rules}
        assert ClassicalTradition.PARASHARI in traditions
        assert ClassicalTradition.JAIMINI in traditions
        assert ClassicalTradition.VARAHAMIHIRA in traditions
        assert ClassicalTradition.MANTRISHA in traditions

        for r in rules:
            cit = r["citation"]
            assert cit.book_title
            assert cit.author
            assert cit.chapter > 0
            assert cit.chapter_name
            assert cit.sloka_range
            assert len(cit.sanskrit_iast) > 10
            assert len(cit.sanskrit_devanagari) > 10
            assert len(cit.translation_english) > 15
            assert cit.is_verified is True
            assert len(r["requirements"]) >= 1

    def test_gajakesari_yoga_evidence_chain_satisfied(self):
        engine = ClassicalRuleEvidenceEngine()
        # Mock chart with Jupiter in 1st house (Cancer - Exalted) and Moon in 4th house
        chart_data = {
            "planets": [
                {"planet": "Jupiter", "house_number": 1, "rashi": "Cancer", "dignity": "exalted", "is_combust": False},
                {"planet": "Moon", "house_number": 4, "rashi": "Libra", "dignity": "neutral", "is_combust": False},
                {"planet": "Sun", "house_number": 10, "rashi": "Aries", "dignity": "exalted", "is_combust": False},
            ]
        }
        chains = engine.evaluate_chart_evidence(chart_data, rule_ids=["BPHS-YOGA-GAJAKESARI"])
        assert len(chains) == 1
        gk_chain = chains[0]

        # 5-Stage verification
        # Step 1: Rule Identity
        assert gk_chain.rule_id == "BPHS-YOGA-GAJAKESARI"
        assert gk_chain.rule_name == "Gajakesari Yoga"
        assert gk_chain.category == "Raja Yoga"

        # Step 2: Canonical Citation
        assert gk_chain.citation.book_title == "Brihat Parashara Hora Shastra"
        assert gk_chain.citation.chapter == 35

        # Step 3 & 4: Required conditions vs Actual chart evidence
        assert len(gk_chain.required_conditions) >= 1
        assert len(gk_chain.actual_evidence) == len(gk_chain.required_conditions)
        assert gk_chain.actual_evidence[0].is_satisfied is True
        assert "Moon" in gk_chain.actual_evidence[0].actual_chart_value

        # Step 5: Fructification Verdict & Strength
        assert gk_chain.status == EvidenceVerificationStatus.SATISFIED
        assert gk_chain.strength_score >= 90.0
        assert len(gk_chain.audit_trace) >= 4

    def test_hamsa_mahapurusha_yoga_satisfied(self):
        engine = ClassicalRuleEvidenceEngine()
        chart_data = {
            "planets": [
                {"planet": "Jupiter", "house_number": 1, "rashi": "Cancer", "dignity": "exalted", "is_combust": False},
                {"planet": "Sun", "house_number": 5, "rashi": "Scorpio", "is_combust": False},
            ]
        }
        chains = engine.evaluate_chart_evidence(chart_data, rule_ids=["BPHS-PMP-HAMSA"])
        assert len(chains) == 1
        hamsa = chains[0]

        assert hamsa.status == EvidenceVerificationStatus.SATISFIED
        assert hamsa.strength_score == 100.0  # Exalted in Kendra bonus
        assert hamsa.citation.author == "Maharishi Parashara"

    def test_cancellation_factor_activation(self):
        engine = ClassicalRuleEvidenceEngine()
        # Jupiter in Capricorn (Debilitated in 1st house) -> triggers CANC-GK-01 (-40%)
        chart_data = {
            "planets": [
                {"planet": "Jupiter", "house_number": 1, "rashi": "Capricorn", "dignity": "debilitated", "is_combust": False},
                {"planet": "Moon", "house_number": 4, "rashi": "Aries", "dignity": "neutral", "is_combust": False},
            ]
        }
        chains = engine.evaluate_chart_evidence(chart_data, rule_ids=["BPHS-YOGA-GAJAKESARI"])
        assert len(chains) == 1
        gk = chains[0]

        # Cancellation factor should be active
        active_cancs = [c for c in gk.cancellation_factors if c.is_active]
        assert len(active_cancs) >= 1
        assert active_cancs[0].factor_id == "CANC-GK-01"
        assert gk.strength_score <= 60.0  # Penalized by 40%
        assert gk.status == EvidenceVerificationStatus.CANCELLED_AFFLICTED

    def test_saravali_and_jaimini_rules_evaluated(self):
        engine = ClassicalRuleEvidenceEngine()
        chart_data = {
            "planets": [
                {"planet": "Sun", "house_number": 10, "rashi": "Simha", "dignity": "own_sign", "is_combust": False},
                {"planet": "Jupiter", "house_number": 9, "rashi": "Dhanus", "dignity": "own_sign", "is_combust": False},
                {"planet": "Mercury", "house_number": 10, "rashi": "Simha", "is_combust": False},
            ]
        }
        chains = engine.evaluate_chart_evidence(chart_data)
        assert len(chains) >= 8

        sun10 = next((c for c in chains if c.rule_id == "SARAVALI-DIGBALA-SUN10"), None)
        assert sun10 is not None
        assert sun10.citation.author == "Kalyanavarma"
        assert sun10.status == EvidenceVerificationStatus.SATISFIED

        budhaditya = next((c for c in chains if c.rule_id == "BJ-YOGA-BUDHADITYA"), None)
        assert budhaditya is not None
        assert budhaditya.citation.book_title == "Brihat Jataka"
        assert budhaditya.status == EvidenceVerificationStatus.SATISFIED
