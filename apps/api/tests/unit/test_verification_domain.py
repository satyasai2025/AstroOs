"""
AstroOS — Verification Domain Model Unit Tests (Module 16, Phase 1)
"""

import dataclasses
import uuid
from datetime import date

import pytest

from apps.api.domain.verification import (
    Alignment,
    RuleVerificationSummary,
    VerificationFindings,
    VerificationPair,
    VerificationStrength,
)


class TestAlignment:
    def test_enum_values(self):
        assert Alignment.CONFIRMED.value == "confirmed"
        assert Alignment.UNTESTED.value == "untested"
        assert Alignment.CATEGORY_MISMATCH.value == "category_mismatch"
        assert Alignment.NOT_APPLICABLE.value == "not_applicable"

    def test_all_members_present(self):
        assert len(Alignment) == 4


class TestVerificationStrength:
    def test_enum_values(self):
        assert VerificationStrength.HIGH.value == "high"
        assert VerificationStrength.MEDIUM.value == "medium"
        assert VerificationStrength.LOW.value == "low"
        assert VerificationStrength.UNKNOWN.value == "unknown"

    def test_all_members_present(self):
        assert len(VerificationStrength) == 4


class TestVerificationPair:
    def test_is_frozen(self):
        pair = _pair()
        with pytest.raises(dataclasses.FrozenInstanceError):
            pair.alignment = Alignment.UNTESTED

    def test_stores_event_fields(self):
        eid = uuid.uuid4()
        pair = _pair(
            event_id=eid, event_title="Promotion", event_description="Got promoted",
            event_category="career", event_is_verified=True,
        )
        assert pair.event_title == "Promotion"
        assert pair.event_description == "Got promoted"
        assert pair.event_category == "career"
        assert pair.event_is_verified is True

    def test_stores_rule_fields(self):
        pair = _pair(rule_id="RULE-001", rule_name="Test Rule", rule_matched=True)
        assert pair.rule_id == "RULE-001"
        assert pair.rule_name == "Test Rule"
        assert pair.rule_matched is True

    def test_stores_derived_facts_and_domains(self):
        pair = _pair(
            derived_facts={"career.leadership": "high", "wealth.potential": 0.8},
            inferred_domains=("career", "wealth"),
        )
        assert pair.derived_facts["career.leadership"] == "high"
        assert pair.inferred_domains == ("career", "wealth")

    def test_stores_alignment_and_strength(self):
        pair = _pair(alignment=Alignment.CONFIRMED, strength=VerificationStrength.HIGH)
        assert pair.alignment == Alignment.CONFIRMED
        assert pair.strength == VerificationStrength.HIGH


class TestRuleVerificationSummary:
    def test_is_frozen(self):
        summary = _summary()
        with pytest.raises(dataclasses.FrozenInstanceError):
            summary.times_matched = 5

    def test_counts(self):
        summary = _summary(
            total_evaluations=10, times_matched=7, times_confirmed=5,
            times_untested=1, times_mismatched=1,
        )
        assert summary.total_evaluations == 10
        assert summary.times_matched == 7
        assert summary.times_confirmed == 5
        assert summary.times_untested == 1
        assert summary.times_mismatched == 1

    def test_strengths_dict(self):
        summary = _summary(strengths={"HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 4})
        assert summary.strengths["HIGH"] == 3
        assert summary.strengths["UNKNOWN"] == 4

    def test_event_id_lists(self):
        eid = uuid.uuid4()
        summary = _summary(
            event_ids_confirmed=(eid,),
            event_ids_untested=(),
            event_ids_mismatched=(),
        )
        assert eid in summary.event_ids_confirmed


class TestVerificationFindings:
    def test_is_frozen(self):
        findings = _findings()
        with pytest.raises(dataclasses.FrozenInstanceError):
            findings.total_pairs = 0

    def test_counts(self):
        findings = _findings(total_events=5, total_rules_evaluated=3, total_pairs=15)
        assert findings.total_events == 5
        assert findings.total_rules_evaluated == 3
        assert findings.total_pairs == 15

    def test_engine_version_default(self):
        findings = _findings()
        assert findings.engine_version == "1.0"

    def test_holds_pairs_and_summaries(self):
        pair = _pair()
        summary = _summary()
        findings = VerificationFindings(
            chart_id=uuid.uuid4(),
            period_covered=(date(2000, 1, 1), date(2010, 1, 1)),
            total_events=1, total_rules_evaluated=1, total_pairs=1,
            rule_summaries=(summary,),
            verification_pairs=(pair,),
        )
        assert len(findings.verification_pairs) == 1
        assert len(findings.rule_summaries) == 1


# ── Helpers ──────────────────────────────────────────────────────────────────


def _pair(**overrides) -> VerificationPair:
    defaults = dict(
        rule_id="RULE-001", rule_name="Test Rule", rule_category="general",
        rule_matched=True,
        event_id=uuid.uuid4(), event_date=date(2005, 1, 1),
        event_title="Test Event", event_description=None,
        event_category="career", event_is_verified=False,
        derived_facts={}, inferred_domains=("career",),
        alignment=Alignment.CONFIRMED, strength=VerificationStrength.MEDIUM,
        explanation="Test explanation.",
    )
    defaults.update(overrides)
    return VerificationPair(**defaults)


def _summary(**overrides) -> RuleVerificationSummary:
    defaults = dict(
        rule_id="RULE-001", rule_name="Test Rule", rule_category="general",
        total_evaluations=5, times_matched=3,
        times_confirmed=2, times_untested=1, times_mismatched=0,
        strengths={"HIGH": 1, "MEDIUM": 1, "LOW": 0, "UNKNOWN": 3},
        event_ids_confirmed=(uuid.uuid4(),),
        event_ids_untested=(),
        event_ids_mismatched=(),
    )
    defaults.update(overrides)
    return RuleVerificationSummary(**defaults)


def _findings(**overrides) -> VerificationFindings:
    defaults = dict(
        chart_id=uuid.uuid4(),
        period_covered=(date(2000, 1, 1), date(2010, 1, 1)),
        total_events=0, total_rules_evaluated=0, total_pairs=0,
        rule_summaries=(),
        verification_pairs=(),
    )
    defaults.update(overrides)
    return VerificationFindings(**defaults)
