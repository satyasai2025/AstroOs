"""
AstroOS — Declarative Shastric Rule Engine
===========================================

Canonical Reference: docs/CANONICAL_PREDICTION_FRAMEWORK.md (Steps 1 to 9)
Evaluates structured Shastric rules against CanonicalFacts and outputs explicit RuleEvaluationResults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from apps.api.services.phalita_core.canonical_facts_generator import CanonicalFacts
from apps.api.services.phalita_core.technique_resolver import ResolvedTechniquePlan, TechniqueResolver


@dataclass(frozen=True)
class RuleEvaluationItem:
    rule_id: str
    rule_name: str
    sanskrit_source: str             # e.g., "BPHS Ch. 12, Sl. 4" or "Jaimini Upadesha Sutras 1.2"
    rule_category: str                # "NATAL_PROMISE", "DIVISIONAL_VARGA", "CHARA_KARAKA", "DASHA_TIMING", "TRANSIT_TRIGGER", "UPAGRAHA_SHADOW"
    is_fired: bool
    signal_delta: float               # -2.0 to +2.0 contribution to signal score
    confidence_weight: float          # 0.0 to 1.0
    rationale: str
    astronomical_evidence: str        # Exact coordinates and planets involved


@dataclass(frozen=True)
class RuleEngineEvaluationResult:
    domain: str
    total_rules_evaluated: int
    fired_rules_count: int
    positive_promisers: Tuple[RuleEvaluationItem, ...]
    inhibiting_factors: Tuple[RuleEvaluationItem, ...]
    net_raw_rule_signal: float
    rule_traces: Tuple[str, ...]


class ShastricRuleEngine:
    """
    Pure declarative Shastric Rule Engine.
    """

    @classmethod
    def evaluate_rules(
        cls,
        facts: CanonicalFacts,
        domain: str,
    ) -> RuleEngineEvaluationResult:
        """
        Executes domain-specific Shastric rules against CanonicalFacts.
        """
        plan: ResolvedTechniquePlan = TechniqueResolver.resolve_domain_plan(domain)
        fired_items: List[RuleEvaluationItem] = []
        rule_traces: List[str] = []

        planet_map = {p.planet.lower(): p for p in facts.planets}
        bhava_map = {b.house_number: b for b in facts.bhavachalita_houses}

        primary_bhava = bhava_map.get(plan.primary_bhava)
        primary_lord_name = primary_bhava.bhava_lord.lower() if primary_bhava else ""
        primary_lord_planet = planet_map.get(primary_lord_name)

        # -------------------------------------------------------------
        # 1. NATAL BHAVA LORD DIGNITY & PLACEMENT (Step 1 & 2)
        # -------------------------------------------------------------
        if primary_lord_planet:
            d_score = primary_lord_planet.dignity_score
            is_strong = d_score >= 6
            is_debilitated = d_score <= 2 and not primary_lord_planet.is_debilitation_cancelled

            if is_strong:
                item = RuleEvaluationItem(
                    rule_id=f"RULE_LORD_STRONG_{plan.primary_bhava}",
                    rule_name=f"Primary Bhava Lord {primary_lord_planet.planet} Fortified",
                    sanskrit_source="BPHS Bhava Karaka Adhyaya",
                    rule_category="NATAL_PROMISE",
                    is_fired=True,
                    signal_delta=1.25,
                    confidence_weight=0.90,
                    rationale=f"Lord of {plan.sanskrit_bhava_name} ({primary_lord_planet.planet}) holds strong dignity ({primary_lord_planet.dignity_label}, {d_score}/9).",
                    astronomical_evidence=f"{primary_lord_planet.planet} at {primary_lord_planet.rashi_name} {primary_lord_planet.rashi_degree}° in House {primary_lord_planet.house_from_lagna}.",
                )
                fired_items.append(item)
                rule_traces.append(f"[RULE_PROMISE] {item.rationale}")
            elif is_debilitated:
                item = RuleEvaluationItem(
                    rule_id=f"RULE_LORD_DEBILITATED_{plan.primary_bhava}",
                    rule_name=f"Primary Bhava Lord {primary_lord_planet.planet} Debilitated",
                    sanskrit_source="BPHS Bhava Nasha Adhyaya",
                    rule_category="NATAL_PROMISE",
                    is_fired=True,
                    signal_delta=-1.20,
                    confidence_weight=0.85,
                    rationale=f"Lord of {plan.sanskrit_bhava_name} ({primary_lord_planet.planet}) is debilitated without cancellation.",
                    astronomical_evidence=f"{primary_lord_planet.planet} in {primary_lord_planet.rashi_name} (Dignity {d_score}/9).",
                )
                fired_items.append(item)
                rule_traces.append(f"[RULE_INHIBITION] {item.rationale}")

        # -------------------------------------------------------------
        # 2. NAISARGIKA KARAKA PLACEMENT
        # -------------------------------------------------------------
        for k_name in plan.naisargika_karakas:
            kp = planet_map.get(k_name.lower())
            if kp:
                if kp.house_from_lagna in (1, 4, 5, 7, 9, 10, 11) and kp.dignity_score >= 5:
                    item = RuleEvaluationItem(
                        rule_id=f"RULE_KARAKA_FORTIFIED_{k_name.upper()}",
                        rule_name=f"Natural Karaka {k_name} Well-Placed",
                        sanskrit_source="Saravali Ch. 34",
                        rule_category="NATAL_PROMISE",
                        is_fired=True,
                        signal_delta=0.85,
                        confidence_weight=0.80,
                        rationale=f"Natural Karaka {k_name} for {domain} is well-placed in House {kp.house_from_lagna} with favorable dignity ({kp.dignity_label}).",
                        astronomical_evidence=f"{k_name} at {kp.rashi_name} {kp.rashi_degree}° in House {kp.house_from_lagna}.",
                    )
                    fired_items.append(item)
                    rule_traces.append(f"[RULE_KARAKA] {item.rationale}")

        # -------------------------------------------------------------
        # 3. DIVISIONAL VARGA CONFIRMATION & BHAVOTTAMA (Step 3 & 6)
        # -------------------------------------------------------------
        varga_num = plan.primary_varga
        varga_planets = [v for v in facts.vargas if v.varga_number == varga_num]
        bhavottama_in_varga = [v for v in varga_planets if v.is_bhavottama]

        if bhavottama_in_varga:
            names = ", ".join(v.planet for v in bhavottama_in_varga)
            item = RuleEvaluationItem(
                rule_id=f"RULE_BHAVOTTAMA_D{varga_num}",
                rule_name=f"Bhavottama Alignment in D{varga_num}",
                sanskrit_source="Phaladeepika Ch. 3 (Kimshukadi Yogas)",
                rule_category="DIVISIONAL_VARGA",
                is_fired=True,
                signal_delta=1.10,
                confidence_weight=0.85,
                rationale=f"Bhavottama (same house across D1 and D{varga_num}) identified for: {names}. Amplifies domain potency.",
                astronomical_evidence=f"Planets {names} occupy matching houses in D1 and D{varga_num}.",
            )
            fired_items.append(item)
            rule_traces.append(f"[RULE_VARGA] {item.rationale}")

        # -------------------------------------------------------------
        # 4. 7 CHARA KARAKA & KARAKAMSHA ALIGNMENT (Step 5)
        # -------------------------------------------------------------
        for ck in facts.chara_karakas:
            if ck.karaka_role in plan.relevant_chara_karaka_roles:
                if ck.house_from_lagna in (1, 4, 5, 7, 9, 10, 11) or ck.house_from_karakamsha in (1, 5, 9):
                    item = RuleEvaluationItem(
                        rule_id=f"RULE_CHARA_{ck.karaka_role}_{ck.planet.upper()}",
                        rule_name=f"{ck.full_name} ({ck.karaka_role}) Prominence",
                        sanskrit_source="Jaimini Sutras 1.2",
                        rule_category="CHARA_KARAKA",
                        is_fired=True,
                        signal_delta=0.90,
                        confidence_weight=0.80,
                        rationale=f"{ck.karaka_role} ({ck.planet}) occupies auspicious house ({ck.house_from_lagna} from Lagna, {ck.house_from_karakamsha} from Karakamsha {facts.karakamsha_lagna_rashi}).",
                        astronomical_evidence=f"{ck.planet} deg-in-sign: {ck.degree_in_sign}°, KL: {facts.karakamsha_lagna_rashi}.",
                    )
                    fired_items.append(item)
                    rule_traces.append(f"[RULE_CHARA] {item.rationale}")

        # -------------------------------------------------------------
        # 5. TEMPORAL DASHA ACTIVATION (Step 7)
        # -------------------------------------------------------------
        active_md = facts.active_d1_dasha.get("MD", "").lower()
        active_ad = facts.active_d1_dasha.get("AD", "").lower()

        md_planet = planet_map.get(active_md)
        ad_planet = planet_map.get(active_ad)

        md_activates = False
        ad_activates = False

        if md_planet and (md_planet.house_from_lagna in (plan.primary_bhava,) + plan.supporting_bhavas or md_planet.bhavachalita_house == plan.primary_bhava):
            md_activates = True
        if ad_planet and (ad_planet.house_from_lagna in (plan.primary_bhava,) + plan.supporting_bhavas or ad_planet.bhavachalita_house == plan.primary_bhava):
            ad_activates = True

        if md_activates or ad_activates:
            lords_str = f"MD {facts.active_d1_dasha.get('MD')}" + (f" + AD {facts.active_d1_dasha.get('AD')}" if ad_activates else "")
            item = RuleEvaluationItem(
                rule_id="RULE_DASHA_ACTIVATION",
                rule_name=f"Vimshottari Dasha Activates {plan.sanskrit_bhava_name}",
                sanskrit_source="BPHS Vimshottari Dasha Phala",
                rule_category="DASHA_TIMING",
                is_fired=True,
                signal_delta=1.40,
                confidence_weight=0.95,
                rationale=f"Active Dasha ({lords_str}) directly connects to House {plan.primary_bhava} / {plan.supporting_bhavas}.",
                astronomical_evidence=f"Active 5-level: {facts.active_d1_dasha.get('MD')}-{facts.active_d1_dasha.get('AD')}-{facts.active_d1_dasha.get('PD')}.",
            )
            fired_items.append(item)
            rule_traces.append(f"[RULE_DASHA] {item.rationale}")

        # -------------------------------------------------------------
        # 6. ASHTAKAVARGA & TRANSIT REKHA GATING (Step 8)
        # -------------------------------------------------------------
        primary_h_idx = plan.primary_bhava - 1
        sav_pts = facts.sarvashtakavarga_rekhas[primary_h_idx] if len(facts.sarvashtakavarga_rekhas) > primary_h_idx else 28

        if sav_pts >= plan.sav_threshold:
            item = RuleEvaluationItem(
                rule_id=f"RULE_SAV_HIGH_{plan.primary_bhava}",
                rule_name=f"Sarvashtakavarga Fortification ({sav_pts} Bindus)",
                sanskrit_source="Ashtakavarga Adhyaya",
                rule_category="TRANSIT_TRIGGER",
                is_fired=True,
                signal_delta=0.75,
                confidence_weight=0.85,
                rationale=f"House {plan.primary_bhava} holds {sav_pts} SAV bindus (Threshold >= {plan.sav_threshold}), providing strong transit reception.",
                astronomical_evidence=f"SAV House {plan.primary_bhava} = {sav_pts} bindus.",
            )
            fired_items.append(item)
            rule_traces.append(f"[RULE_SAV] {item.rationale}")
        elif sav_pts < 24:
            item = RuleEvaluationItem(
                rule_id=f"RULE_SAV_LOW_{plan.primary_bhava}",
                rule_name=f"Sarvashtakavarga Deficit ({sav_pts} Bindus)",
                sanskrit_source="Ashtakavarga Adhyaya",
                rule_category="TRANSIT_TRIGGER",
                is_fired=True,
                signal_delta=-0.80,
                confidence_weight=0.80,
                rationale=f"House {plan.primary_bhava} has depleted SAV bindus ({sav_pts} < 24), dampening event manifestation.",
                astronomical_evidence=f"SAV House {plan.primary_bhava} = {sav_pts} bindus.",
            )
            fired_items.append(item)
            rule_traces.append(f"[RULE_SAV_DEFICIT] {item.rationale}")

        # -------------------------------------------------------------
        # 7. UPAGRAHA INTERFERENCE / SHADOW (Mandi & Gulika)
        # -------------------------------------------------------------
        mandi = next((u for u in facts.upagrahas if u.name.lower() == "mandi"), None)
        gulika = next((u for u in facts.upagrahas if u.name.lower() == "gulika"), None)

        if domain == "marriage" and mandi and mandi.house_number == 7:
            item = RuleEvaluationItem(
                rule_id="RULE_MANDI_7TH_DELAY",
                rule_name="Mandi in 7th House (Marital Delay)",
                sanskrit_source="Vinay Jha Canonical Upagraha Framework",
                rule_category="UPAGRAHA_SHADOW",
                is_fired=True,
                signal_delta=-1.30,
                confidence_weight=0.90,
                rationale="Mandi occupies 7th house: Causes obstruction and delay in marital union without outright denial.",
                astronomical_evidence=f"Mandi at {mandi.rashi_name} {mandi.rashi_degree}° in House 7.",
            )
            fired_items.append(item)
            rule_traces.append(f"[RULE_UPAGRAHA] {item.rationale}")

        if domain == "accident" and gulika and gulika.house_number in (6, 8, 12):
            item = RuleEvaluationItem(
                rule_id=f"RULE_GULIKA_DUSTHANA_{gulika.house_number}",
                rule_name=f"Gulika in Dusthana House {gulika.house_number}",
                sanskrit_source="Vinay Jha Upagraha Rules (8th Mrityu Weight)",
                rule_category="UPAGRAHA_SHADOW",
                is_fired=True,
                signal_delta=1.20,
                confidence_weight=0.85,
                rationale=f"Gulika in House {gulika.house_number} amplifies sudden crisis, acute trauma, and health vulnerability.",
                astronomical_evidence=f"Gulika at {gulika.rashi_name} {gulika.rashi_degree}° in House {gulika.house_number}.",
            )
            fired_items.append(item)
            rule_traces.append(f"[RULE_UPAGRAHA] {item.rationale}")

        # Separate into promisers vs inhibiting factors
        positives = tuple(r for r in fired_items if r.signal_delta > 0)
        negatives = tuple(r for r in fired_items if r.signal_delta < 0)
        net_signal = sum(r.signal_delta for r in fired_items)

        return RuleEngineEvaluationResult(
            domain=domain,
            total_rules_evaluated=12,
            fired_rules_count=len(fired_items),
            positive_promisers=positives,
            inhibiting_factors=negatives,
            net_raw_rule_signal=round(net_signal, 2),
            rule_traces=tuple(rule_traces),
        )
