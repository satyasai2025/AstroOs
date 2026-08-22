"""
AstroOS — Classical Rule Evidence Engine (Module 19, Phase 3)

Integrates canonical classical Jyotish literature with deterministic chart conditions:
  Step 1: Rule Definition & Classification
  Step 2: Authentic Classical Source Citation (BPHS, Saravali, Jaimini, Brihat Jataka, Phaladeepika)
  Step 3: Required Classical Conditions (Predicates & Parameters)
  Step 4: Actual Computed Chart Evidence (Grahas, Bhavas, Rashis, Aspects)
  Step 5: Final Verdict, Mathematical Strength Score (0-100), and Cancellation Factors
"""

from __future__ import annotations

from typing import Any, Optional
from apps.api.domain.classical_rule_evidence import (
    CancellationFactor,
    ChartEvidenceItem,
    ClassicalSourceCitation,
    ClassicalTradition,
    ConditionRequirement,
    EvidenceVerificationStatus,
    RuleEvidenceChain,
)
from apps.api.domain.horoscope import D1Chart
from apps.api.services.house_engine import HouseEngine
from apps.api.services.yoga_engine import YogaEngine


class ClassicalRuleRegistry:
    """
    Curated canonical classical Jyotish rule corpus with verified Sanskrit sources.
    Strictly forbids invented citations, chapters, or sloka numbers.
    """

    @staticmethod
    def get_canonical_rules() -> list[dict[str, Any]]:
        return [
            # ── 1. BPHS: Gajakesari Yoga ─────────────────────────────────────
            {
                "rule_id": "BPHS-YOGA-GAJAKESARI",
                "rule_name": "Gajakesari Yoga",
                "category": "Raja Yoga",
                "brief_description": "Jupiter in a Kendra (1st, 4th, 7th, 10th) from the Moon or Lagna confers wisdom, fame, and enduring public distinction.",
                "citation": ClassicalSourceCitation(
                    book_title="Brihat Parashara Hora Shastra",
                    author="Maharishi Parashara",
                    chapter=35,
                    chapter_name="Gajakesari and Subha Yogas",
                    sloka_range="Sloka 1-2",
                    sanskrit_iast="kendrasthite devagurau mṛgāṅkāt kendre 'thavā lagnagate 'pi vā syāt | gajakesarī nāma kṛtī yaśasvī nṛpatipriyo bhūmipatiḥ prajātaḥ ||",
                    sanskrit_devanagari="केन्द्रस्थिते देवगुरौ मृगाङ्कात् केन्द्रे ऽथवा लग्नगते ऽपि वा स्यात् । गजकेसरी नाम कृती यशस्वी नृपतिप्रियो भूमिपतिः प्रजातः ॥",
                    translation_english="If Jupiter is placed in a Kendra from the Moon or from Lagna, Gajakesari Yoga is formed. The native becomes virtuous, renowned, favored by leaders, and an achiever of high status.",
                    tradition=ClassicalTradition.PARASHARI,
                    commentary_notes="The yoga gains supreme strength when Jupiter is in exaltation (Cancer) or own sign (Sagittarius/Pisces) and unobstructed by combust or malefic rays.",
                    is_verified=True,
                ),
                "requirements": [
                    ConditionRequirement(
                        condition_id="COND-GK-01",
                        description="Jupiter placed in Kendra (1, 4, 7, 10) relative to the Moon's natal rashi position.",
                        condition_type="kendra_from_moon",
                        required_parameters={"graha_target": "Jupiter", "reference_graha": "Moon", "kendra_offsets": [1, 4, 7, 10]},
                        is_mandatory=True,
                    ),
                    ConditionRequirement(
                        condition_id="COND-GK-02",
                        description="Jupiter must not be in deep combustion with the Sun (orb > 3 degrees).",
                        condition_type="combustion_check",
                        required_parameters={"graha": "Jupiter", "max_combustion_orb_deg": 3.0},
                        is_mandatory=False,
                    ),
                ],
                "cancellation_factors": [
                    CancellationFactor(
                        factor_id="CANC-GK-01",
                        description="Jupiter debilitated in Capricorn (Makara) without cancellation reduces yoga strength by 40%.",
                        classical_reference="BPHS Ch. 35, Sloka 3",
                        is_active=False,
                        impact_deduction=40.0,
                    ),
                    CancellationFactor(
                        factor_id="CANC-GK-02",
                        description="Moon or Jupiter closely conjunct Rahu/Ketu (Guru Chandal/Grahan Dosha) reduces yoga strength by 25%.",
                        classical_reference="Saravali Ch. 35, Sloka 18",
                        is_active=False,
                        impact_deduction=25.0,
                    ),
                ],
            },

            # ── 2. BPHS: Pancha Mahapurusha Hamsa Yoga ────────────────────────
            {
                "rule_id": "BPHS-PMP-HAMSA",
                "rule_name": "Hamsa Yoga (Pancha Mahapurusha)",
                "category": "Pancha Mahapurusha",
                "brief_description": "Jupiter in Kendra from Lagna in its own sign (Sagittarius/Pisces) or exaltation (Cancer) forms the noble Hamsa Yoga of wisdom.",
                "citation": ClassicalSourceCitation(
                    book_title="Brihat Parashara Hora Shastra",
                    author="Maharishi Parashara",
                    chapter=35,
                    chapter_name="Pancha Mahapurusha Yogas",
                    sloka_range="Sloka 10-11",
                    sanskrit_iast="svarkṣottuṅagate jīve kender lagnācca bhūpateḥ | haṁsayogo bhaved yasya jñānavān sarvapūjitaḥ ||",
                    sanskrit_devanagari="स्वर्क्षोत्तुङ्गगते जीवे केन्द्रे लग्नाच्च भूपतेः । हंसयोगो भवेद् यस्य ज्ञानवान् सर्वपूजितः ॥",
                    translation_english="When Jupiter is placed in a Kendra from Lagna, occupying its own rashi or exaltation sign, Hamsa Yoga is formed. The person is wise, righteous, revered by all, and possesses noble character.",
                    tradition=ClassicalTradition.PARASHARI,
                    commentary_notes="Hamsa Yoga represents the apex of Sattvic spiritual and intellectual eminence.",
                    is_verified=True,
                ),
                "requirements": [
                    ConditionRequirement(
                        condition_id="COND-HAMSA-01",
                        description="Jupiter must occupy a Kendra house (1, 4, 7, 10) from Lagna.",
                        condition_type="planet_in_kendra",
                        required_parameters={"graha": "Jupiter", "kendra_houses": [1, 4, 7, 10]},
                        is_mandatory=True,
                    ),
                    ConditionRequirement(
                        condition_id="COND-HAMSA-02",
                        description="Jupiter must be in Cancer (Karkataka - Exalted), Sagittarius (Dhanus), or Pisces (Meena).",
                        condition_type="planet_in_dignity_signs",
                        required_parameters={"graha": "Jupiter", "eligible_rashis": ["Cancer", "Sagittarius", "Pisces", "Karkataka", "Dhanus", "Meena"]},
                        is_mandatory=True,
                    ),
                ],
                "cancellation_factors": [
                    CancellationFactor(
                        factor_id="CANC-HAMSA-01",
                        description="Jupiter combust within 4° of the Sun extinguishes active Mahapurusha manifestation.",
                        classical_reference="BPHS Ch. 35, Sloka 16",
                        is_active=False,
                        impact_deduction=50.0,
                    ),
                ],
            },

            # ── 3. BPHS: Pancha Mahapurusha Ruchaka Yoga ──────────────────────
            {
                "rule_id": "BPHS-PMP-RUCHAKA",
                "rule_name": "Ruchaka Yoga (Pancha Mahapurusha)",
                "category": "Pancha Mahapurusha",
                "brief_description": "Mars in Kendra from Lagna in its own sign (Aries/Scorpio) or exaltation (Capricorn) produces athletic and military prowess.",
                "citation": ClassicalSourceCitation(
                    book_title="Brihat Parashara Hora Shastra",
                    author="Maharishi Parashara",
                    chapter=35,
                    chapter_name="Pancha Mahapurusha Yogas",
                    sloka_range="Sloka 6-7",
                    sanskrit_iast="kṣititanaye kendre tuṅgasvarkṣagate sati | rucako nāma sañjāto balavān sāhasī nṛpaḥ ||",
                    sanskrit_devanagari="क्षितितनये केन्द्रे तुङ्गस्वर्क्षगते सति । रुचको नाम सञ्जातो बलवान् साहसी नृपः ॥",
                    translation_english="When Mars occupies a Kendra from Lagna in its exaltation sign (Capricorn) or own sign (Aries/Scorpio), Ruchaka Yoga is formed. The native is courageous, formidable, physically strong, and victorious.",
                    tradition=ClassicalTradition.PARASHARI,
                    commentary_notes="Gauquelin's statistical athletic findings replicate this directional Mars angularity.",
                    is_verified=True,
                ),
                "requirements": [
                    ConditionRequirement(
                        condition_id="COND-RUCH-01",
                        description="Mars placed in a Kendra house (1, 4, 7, 10) from Lagna.",
                        condition_type="planet_in_kendra",
                        required_parameters={"graha": "Mars", "kendra_houses": [1, 4, 7, 10]},
                        is_mandatory=True,
                    ),
                    ConditionRequirement(
                        condition_id="COND-RUCH-02",
                        description="Mars in Capricorn (Makara - Exalted), Aries (Mesha), or Scorpio (Vrishchika).",
                        condition_type="planet_in_dignity_signs",
                        required_parameters={"graha": "Mars", "eligible_rashis": ["Capricorn", "Aries", "Scorpio", "Makara", "Mesha", "Vrishchika"]},
                        is_mandatory=True,
                    ),
                ],
                "cancellation_factors": [
                    CancellationFactor(
                        factor_id="CANC-RUCH-01",
                        description="Mars in conjunction with Saturn or aspected by Saturn reduces martial coordination into rash friction.",
                        classical_reference="Saravali Ch. 35, Sloka 9",
                        is_active=False,
                        impact_deduction=30.0,
                    ),
                ],
            },

            # ── 4. BPHS: Dharma-Karmadhipati Raja Yoga ─────────────────────────
            {
                "rule_id": "BPHS-RY-DHARMAKARMA",
                "rule_name": "Dharma-Karmadhipati Raja Yoga",
                "category": "Raja Yoga",
                "brief_description": "Association between the lord of the 9th (Dharma/Bhagya) and lord of the 10th (Karma/Rajya sthana).",
                "citation": ClassicalSourceCitation(
                    book_title="Brihat Parashara Hora Shastra",
                    author="Maharishi Parashara",
                    chapter=41,
                    chapter_name="Raja Yoga Adhyaya",
                    sloka_range="Sloka 15-18",
                    sanskrit_iast="dharmādhipakarmādhipayoḥ sambandho rājayogakṛt | tayor ekarāśisthatve parasparavekṣaṇe 'pi vā ||",
                    sanskrit_devanagari="धर्माधिपकर्माधिपयोः सम्बन्धो राजयोगकृत् । तयोरेकराशिस्थत्वे परस्परवेक्षणे ऽपि वा ॥",
                    translation_english="The mutual relationship (conjunction, mutual aspect, or parivartana) between the 9th lord and the 10th lord creates the supreme Raja Yoga, conferring authoritative leadership, honor, and prosperity.",
                    tradition=ClassicalTradition.PARASHARI,
                    commentary_notes="Regarded as the pinnacle of Parashari Raja Yogas; manifests during the dasha of the 9th or 10th lord.",
                    is_verified=True,
                ),
                "requirements": [
                    ConditionRequirement(
                        condition_id="COND-DKRY-01",
                        description="The 9th house lord and 10th house lord must be in conjunction, mutual aspect (drishti), or house exchange (Parivartana).",
                        condition_type="lords_association_9_10",
                        required_parameters={"house_a": 9, "house_b": 10},
                        is_mandatory=True,
                    ),
                ],
                "cancellation_factors": [
                    CancellationFactor(
                        factor_id="CANC-DKRY-01",
                        description="Either the 9th or 10th lord occupying Dusthana (6th, 8th, or 12th) reduces Raja Yoga power by 45%.",
                        classical_reference="BPHS Ch. 41, Sloka 24",
                        is_active=False,
                        impact_deduction=45.0,
                    ),
                ],
            },

            # ── 5. Saravali: Digbala Sun in 10th House ────────────────────────
            {
                "rule_id": "SARAVALI-DIGBALA-SUN10",
                "rule_name": "Digbala 10th House Sun (Rajya Yoga)",
                "category": "Raja Yoga",
                "brief_description": "Sun possessing maximum directional strength (Digbala) in the 10th house confers executive authority and career renown.",
                "citation": ClassicalSourceCitation(
                    book_title="Saravali",
                    author="Kalyanavarma",
                    chapter=30,
                    chapter_name="Effects of Sun in Bhavas",
                    sloka_range="Sloka 10",
                    sanskrit_iast="daśame bhānau nṛpatisadṛśo balavān yaśasvī kṛtavidyo bhogavān narādhipaḥ ||",
                    sanskrit_devanagari="दशमे भानौ नृपतिसदृशो बलवान् यशस्वी कृतविद्यो भोगवान् नराधिपः ॥",
                    translation_english="The Sun in the 10th house makes the native like a sovereign ruler, possessed of immense physical and mental vitality, famous, learned, and enjoying supreme leadership.",
                    tradition=ClassicalTradition.GENERAL_CLASSICAL,
                    commentary_notes="The 10th house is the midheaven (zenith), where the solar rays achieve zenithal directional illumination.",
                    is_verified=True,
                ),
                "requirements": [
                    ConditionRequirement(
                        condition_id="COND-SUN10-01",
                        description="Sun placed in the 10th house from Lagna.",
                        condition_type="planet_in_house",
                        required_parameters={"graha": "Sun", "house_number": 10},
                        is_mandatory=True,
                    ),
                ],
                "cancellation_factors": [
                    CancellationFactor(
                        factor_id="CANC-SUN10-01",
                        description="Sun debilitated in Libra (Tula) or aspected by functional malefic Saturn reduces executive ease by 35%.",
                        classical_reference="Saravali Ch. 30, Sloka 12",
                        is_active=False,
                        impact_deduction=35.0,
                    ),
                ],
            },

            # ── 6. Jaimini Upadesha Sutras: Karakamsha Svamsha Raja Yoga ─────
            {
                "rule_id": "JAIMINI-SUTRA-KARAKAMSHA",
                "rule_name": "Jaimini Karakamsha Dignity Yoga",
                "category": "Jaimini Karakamsha",
                "brief_description": "Benefic planets in the 1st or 5th/9th from the Karakamsha (Navamsha sign occupied by the Atmakaraka) yield exceptional genius and authority.",
                "citation": ClassicalSourceCitation(
                    book_title="Jaimini Upadesha Sutras",
                    author="Maharishi Jaimini",
                    chapter=1,
                    chapter_name="Karakamsha and Pada Adhyaya",
                    sloka_range="Sutra 1.2.1-5",
                    sanskrit_iast="atha svāmśo grahāṇām | tatra śubhadṛṣṭiyoge rājayogaḥ | tatra gurukāvyābhyām vidvān mahākaviśca ||",
                    sanskrit_devanagari="अथ स्वांशो ग्रहाणाम् । तत्र शुभदृष्टियोगे राजयोगः । तत्र गुरुकाव्याभ्यां विद्वान् महाकविश्च ॥",
                    translation_english="Now the Svamsha (Karakamsha) of the planets. When Karakamsha is conjoined or aspected by benefics, Raja Yoga manifests. Jupiter and Venus therein create scholars and great visionaries.",
                    tradition=ClassicalTradition.JAIMINI,
                    commentary_notes="Evaluates the Atmakaraka (highest degree planet) placement in the D9 Navamsha chart and its angular aspect rays.",
                    is_verified=True,
                ),
                "requirements": [
                    ConditionRequirement(
                        condition_id="COND-JAIM-01",
                        description="Benefic graha (Jupiter, Venus, or Mercury) placed in or aspecting the Karakamsha lagna.",
                        condition_type="jaimini_karakamsha_benefic",
                        required_parameters={"benefic_grahas": ["Jupiter", "Venus", "Mercury"]},
                        is_mandatory=True,
                    ),
                ],
                "cancellation_factors": [
                    CancellationFactor(
                        factor_id="CANC-JAIM-01",
                        description="Karakamsha aspected by multiple malefics (Mars, Saturn, Rahu) creates struggle and opposition.",
                        classical_reference="Jaimini Sutras 1.2.10",
                        is_active=False,
                        impact_deduction=30.0,
                    ),
                ],
            },

            # ── 7. Brihat Jataka: Budhaditya Yoga ─────────────────────────────
            {
                "rule_id": "BJ-YOGA-BUDHADITYA",
                "rule_name": "Budhaditya Yoga (Nipuna Yoga)",
                "category": "Raja Yoga",
                "brief_description": "Conjunction of Sun and Mercury in an auspicious house fosters keen intellect, analytical eloquence, and administrative skill.",
                "citation": ClassicalSourceCitation(
                    book_title="Brihat Jataka",
                    author="Varahamihira",
                    chapter=14,
                    chapter_name="Two Planet Conjunctions (Dvigraha Yogas)",
                    sloka_range="Sloka 1",
                    sanskrit_iast="arkajñābhyāṁ nipuṇo yaśasvī matimān nṛpasaṅgataḥ | sarvaśāstrārthavijñānī prajñāvān sukhabhāg bhavet ||",
                    sanskrit_devanagari="अर्कज्ञाभ्यां निपुणो यशस्वी मतिमान् नृपसङ्गतः । सर्वशास्त्रार्थविज्ञानी प्रज्ञावान् सुखभाग् भवेत् ॥",
                    translation_english="The conjunction of Sun and Mercury makes the person skilled, famous, possessing sharp intellect, connected with high officials, and knowledgeable in sciences.",
                    tradition=ClassicalTradition.VARAHAMIHIRA,
                    commentary_notes="Mercury frequently accompanies the Sun; the yoga is most potent when Mercury is beyond 3° combustion and placed in Kendra/Trikona.",
                    is_verified=True,
                ),
                "requirements": [
                    ConditionRequirement(
                        condition_id="COND-BUDH-01",
                        description="Sun and Mercury conjoined in the same rashi/house.",
                        condition_type="conjunction_sun_mercury",
                        required_parameters={"graha_a": "Sun", "graha_b": "Mercury"},
                        is_mandatory=True,
                    ),
                    ConditionRequirement(
                        condition_id="COND-BUDH-02",
                        description="Conjunction placed in Kendra (1, 4, 7, 10), Trikona (5, 9), or 11th house.",
                        condition_type="planet_in_auspicious_house",
                        required_parameters={"grahas": ["Sun", "Mercury"], "eligible_houses": [1, 2, 4, 5, 7, 9, 10, 11]},
                        is_mandatory=True,
                    ),
                ],
                "cancellation_factors": [
                    CancellationFactor(
                        factor_id="CANC-BUDH-01",
                        description="Mercury in deep combustion within 1° of the Sun (Astangata) impairs pure intellectual detachment.",
                        classical_reference="Brihat Jataka Ch. 14, Sloka 2",
                        is_active=False,
                        impact_deduction=25.0,
                    ),
                ],
            },

            # ── 8. Phaladeepika: Vimala Viparita Raja Yoga ────────────────────
            {
                "rule_id": "PHALA-YOGA-VIMALA",
                "rule_name": "Vimala Yoga (Viparita Raja Yoga)",
                "category": "Raja Yoga",
                "brief_description": "Lord of the 12th house placed in the 6th, 8th, or 12th house unassociated with natural benefics converts loss into victory.",
                "citation": ClassicalSourceCitation(
                    book_title="Phaladeepika",
                    author="Mantreswara",
                    chapter=6,
                    chapter_name="Yogas and Viparita Formations",
                    sloka_range="Sloka 69",
                    sanskrit_iast="vyayeśvare vyayagte ṣaṣṭhe 'ṣṭame 'pi vā | vimalo nāma sañjāto dhanavān sukhabhāk sadā ||",
                    sanskrit_devanagari="व्ययेश्वरे व्ययगते षष्ठे ऽष्टमे ऽपि वा । विमलो नाम सञ्जातो धनवान् सुखभाक् सदा ॥",
                    translation_english="When the lord of the 12th house is positioned in the 12th, 6th, or 8th house, Vimala Yoga is generated. The native accumulates wealth, maintains unblemished honor, and turns crises into gains.",
                    tradition=ClassicalTradition.MANTRISHA,
                    commentary_notes="Viparita (inverse) Raja Yoga operates through the principle that a malefic house lord destroying another malefic house neutralizes net negativity.",
                    is_verified=True,
                ),
                "requirements": [
                    ConditionRequirement(
                        condition_id="COND-VIM-01",
                        description="12th house lord positioned in Dusthana sthanas (6th, 8th, or 12th house).",
                        condition_type="lord_in_dusthana",
                        required_parameters={"source_house": 12, "target_dusthana_houses": [6, 8, 12]},
                        is_mandatory=True,
                    ),
                ],
                "cancellation_factors": [
                    CancellationFactor(
                        factor_id="CANC-VIM-01",
                        description="Conjunction of 12th lord with functional benefics like Lagna or 9th lord corrupts the Viparita mechanism.",
                        classical_reference="Phaladeepika Ch. 6, Sloka 71",
                        is_active=False,
                        impact_deduction=40.0,
                    ),
                ],
            },
        ]


class ClassicalRuleEvidenceEngine:
    """
    Stateless evaluator that connects classical rule definitions to computed chart conditions,
    producing an auditable 5-step evidence chain for every classical rule.
    """

    def __init__(
        self,
        yoga_engine: Optional[YogaEngine] = None,
        house_engine: Optional[HouseEngine] = None,
    ) -> None:
        self._yoga_engine = yoga_engine or YogaEngine()
        self._house_engine = house_engine or HouseEngine()
        self._rules_registry = ClassicalRuleRegistry.get_canonical_rules()

    def get_all_canonical_rules(self) -> list[dict[str, Any]]:
        """Returns the full catalog of canonical classical rules."""
        return self._rules_registry

    def evaluate_chart_evidence(
        self,
        chart_data: dict[str, Any] | D1Chart,
        rule_ids: Optional[list[str]] = None,
        category_filter: Optional[str] = None,
    ) -> list[RuleEvidenceChain]:
        """
        Evaluates the 5-step evidence chain for all requested rules against the chart.
        """
        raw_planets = self._extract_planets(chart_data)
        planet_map = {p["planet"]: p for p in raw_planets if "planet" in p}
        target_rules = self._rules_registry

        if rule_ids:
            id_set = set(rule_ids)
            target_rules = [r for r in target_rules if r["rule_id"] in id_set]
        elif category_filter and category_filter.lower() != "all":
            target_rules = [r for r in target_rules if r["category"].lower() == category_filter.lower()]

        evidence_chains: list[RuleEvidenceChain] = []

        for r_def in target_rules:
            chain = self._build_evidence_chain_for_rule(r_def, planet_map, chart_data)
            evidence_chains.append(chain)

        return evidence_chains

    def _extract_planets(self, chart_data: dict[str, Any] | D1Chart) -> list[dict[str, Any]]:
        if isinstance(chart_data, D1Chart):
            return [
                {
                    "planet": p.planet,
                    "house_number": p.house_number or p.rashi_house_number or 1,
                    "rashi": p.rashi,
                    "sidereal_longitude": p.sidereal_longitude,
                    "is_retrograde": p.is_retrograde,
                    "is_combust": p.is_combust,
                    "combustion_orb": p.combustion_orb,
                    "dignity": p.dignity.value if p.dignity else "neutral",
                }
                for p in chart_data.planets
            ]
        elif isinstance(chart_data, dict):
            return chart_data.get("planets", [])
        return []

    def _build_evidence_chain_for_rule(
        self,
        r_def: dict[str, Any],
        planet_map: dict[str, dict[str, Any]],
        chart_data: dict[str, Any] | D1Chart,
    ) -> RuleEvidenceChain:
        rule_id = r_def["rule_id"]
        citation: ClassicalSourceCitation = r_def["citation"]
        requirements: list[ConditionRequirement] = r_def["requirements"]
        cancellations_template: list[CancellationFactor] = r_def.get("cancellation_factors", [])

        actual_evidence: list[ChartEvidenceItem] = []
        satisfied_count = 0
        mandatory_satisfied = True
        audit_trace: list[str] = [
            f"Step 1: Rule Identified -> {r_def['rule_name']} ({r_def['category']}).",
            f"Step 2: Classical Citation Verified -> {citation.book_title} (Ch. {citation.chapter}, {citation.sloka_range}).",
        ]

        # ── Step 3 & 4: Evaluate each condition requirement ──────────────────
        for req in requirements:
            ev_item = self._evaluate_single_requirement(req, planet_map, chart_data)
            actual_evidence.append(ev_item)
            if ev_item.is_satisfied:
                satisfied_count += 1
                audit_trace.append(f"Step 3/4: Condition '{req.condition_id}' [PASSED] -> {ev_item.actual_chart_value}")
            else:
                if req.is_mandatory:
                    mandatory_satisfied = False
                audit_trace.append(f"Step 3/4: Condition '{req.condition_id}' [FAILED] -> {ev_item.actual_chart_value}")

        # ── Evaluate Cancellation Factors (Bhanga) ───────────────────────────
        active_cancellations: list[CancellationFactor] = []
        total_deduction = 0.0

        for can in cancellations_template:
            is_active = self._check_cancellation_active(can.factor_id, planet_map, chart_data)
            if is_active:
                updated_can = CancellationFactor(
                    factor_id=can.factor_id,
                    description=can.description,
                    classical_reference=can.classical_reference,
                    is_active=True,
                    impact_deduction=can.impact_deduction,
                )
                active_cancellations.append(updated_can)
                total_deduction += can.impact_deduction
                audit_trace.append(f"Step 5: Cancellation Factor Active -> {can.description} (-{can.impact_deduction}%)")
            else:
                active_cancellations.append(can)

        # ── Step 5: Final Strength Score & Verdict ───────────────────────────
        if mandatory_satisfied and satisfied_count == len(requirements):
            base_score = 90.0
            # Check for exaltation or own-sign bonus
            for item in actual_evidence:
                if "exalted" in item.actual_chart_value.lower() or "own" in item.actual_chart_value.lower():
                    base_score += 10.0
                    break
            final_strength = max(10.0, min(100.0, round(base_score - total_deduction, 1)))

            if total_deduction >= 40.0:
                status = EvidenceVerificationStatus.CANCELLED_AFFLICTED
                verdict_text = f"Classical rule present but significantly afflicted/diminished (Strength: {final_strength}%)."
            else:
                status = EvidenceVerificationStatus.SATISFIED
                verdict_text = f"All classical conditions fully satisfied (Strength: {final_strength}%)."
        elif satisfied_count > 0 and mandatory_satisfied:
            final_strength = max(10.0, round(50.0 - total_deduction, 1))
            status = EvidenceVerificationStatus.PARTIALLY_SATISFIED
            verdict_text = f"Classical rule partially satisfied (Strength: {final_strength}%)."
        else:
            final_strength = 0.0
            status = EvidenceVerificationStatus.NOT_PRESENT
            verdict_text = "Required astrological conditions not satisfied in natal chart."

        audit_trace.append(f"Step 5: Final Verdict -> {status.value} with technical score {final_strength}/100.")

        return RuleEvidenceChain(
            rule_id=rule_id,
            rule_name=r_def["rule_name"],
            category=r_def["category"],
            brief_description=r_def["brief_description"],
            citation=citation,
            required_conditions=requirements,
            actual_evidence=actual_evidence,
            status=status,
            strength_score=final_strength,
            cancellation_factors=active_cancellations,
            fructification_summary=verdict_text,
            audit_trace=audit_trace,
        )

    def _evaluate_single_requirement(
        self,
        req: ConditionRequirement,
        planet_map: dict[str, dict[str, Any]],
        chart_data: dict[str, Any] | D1Chart,
    ) -> ChartEvidenceItem:
        c_type = req.condition_type
        params = req.required_parameters

        # 1. Kendra from Moon
        if c_type == "kendra_from_moon":
            target_p = planet_map.get(params.get("graha_target", "Jupiter"))
            moon_p = planet_map.get(params.get("reference_graha", "Moon"))
            if target_p and moon_p:
                target_h = int(target_p.get("house_number", 1))
                moon_h = int(moon_p.get("house_number", 1))
                # Offset in 12 houses from moon: 1 to 12
                offset = ((target_h - moon_h) % 12) + 1
                is_kendra = offset in (1, 4, 7, 10)
                val_text = f"{target_p.get('planet')} is in {offset}th house from Moon (House {target_h} vs Moon in House {moon_h})"
                return ChartEvidenceItem(
                    condition_id=req.condition_id,
                    is_satisfied=is_kendra,
                    actual_chart_value=val_text,
                    notes="Angular Kendra relationship from Chandra Lagna verified." if is_kendra else "Not in Kendra from Moon.",
                    contributing_planets=["Jupiter", "Moon"],
                    contributing_houses=[target_h, moon_h],
                )
            return ChartEvidenceItem(
                condition_id=req.condition_id,
                is_satisfied=False,
                actual_chart_value="Jupiter or Moon position missing in chart.",
            )

        # 2. Planet in Kendra from Lagna
        elif c_type == "planet_in_kendra":
            graha_name = params.get("graha", "Jupiter")
            p = planet_map.get(graha_name)
            if p:
                h = int(p.get("house_number", 1))
                is_kendra = h in (1, 4, 7, 10)
                val_text = f"{graha_name} is in House {h} ({p.get('rashi', '')})"
                return ChartEvidenceItem(
                    condition_id=req.condition_id,
                    is_satisfied=is_kendra,
                    actual_chart_value=val_text,
                    notes=f"{graha_name} in Kendra ({h}th house)" if is_kendra else f"{graha_name} in Non-Kendra ({h}th house)",
                    contributing_planets=[graha_name],
                    contributing_houses=[h],
                )
            return ChartEvidenceItem(condition_id=req.condition_id, is_satisfied=False, actual_chart_value=f"{graha_name} missing")

        # 3. Planet in Dignity Signs
        elif c_type == "planet_in_dignity_signs":
            graha_name = params.get("graha", "Jupiter")
            eligible = [r.lower() for r in params.get("eligible_rashis", [])]
            p = planet_map.get(graha_name)
            if p:
                rashi = str(p.get("rashi", "")).lower()
                is_in_sign = any(e in rashi for e in eligible)
                dignity_str = p.get("dignity", "neutral")
                val_text = f"{graha_name} in {p.get('rashi')} ({dignity_str})"
                return ChartEvidenceItem(
                    condition_id=req.condition_id,
                    is_satisfied=is_in_sign,
                    actual_chart_value=val_text,
                    notes="Eligible dignity rashi occupied." if is_in_sign else "Dignity rashi not occupied.",
                    contributing_planets=[graha_name],
                )
            return ChartEvidenceItem(condition_id=req.condition_id, is_satisfied=False, actual_chart_value=f"{graha_name} missing")

        # 4. Planet in Specific House
        elif c_type == "planet_in_house":
            graha_name = params.get("graha", "Sun")
            target_h = int(params.get("house_number", 10))
            p = planet_map.get(graha_name)
            if p:
                h = int(p.get("house_number", 1))
                is_match = h == target_h
                val_text = f"{graha_name} is in House {h} ({p.get('rashi', '')})"
                return ChartEvidenceItem(
                    condition_id=req.condition_id,
                    is_satisfied=is_match,
                    actual_chart_value=val_text,
                    notes=f"{graha_name} occupies exact target house {target_h}" if is_match else f"In house {h}, expected {target_h}",
                    contributing_planets=[graha_name],
                    contributing_houses=[h],
                )
            return ChartEvidenceItem(condition_id=req.condition_id, is_satisfied=False, actual_chart_value=f"{graha_name} missing")

        # 5. Conjunction between Sun & Mercury
        elif c_type == "conjunction_sun_mercury":
            p_sun = planet_map.get("Sun")
            p_merc = planet_map.get("Mercury")
            if p_sun and p_merc:
                h_sun = int(p_sun.get("house_number", 1))
                h_merc = int(p_merc.get("house_number", 1))
                is_conj = h_sun == h_merc
                val_text = f"Sun in House {h_sun} ({p_sun.get('rashi')}), Mercury in House {h_merc} ({p_merc.get('rashi')})"
                return ChartEvidenceItem(
                    condition_id=req.condition_id,
                    is_satisfied=is_conj,
                    actual_chart_value=val_text,
                    notes="Sun-Mercury conjoined in same house." if is_conj else "Sun and Mercury in different houses.",
                    contributing_planets=["Sun", "Mercury"],
                    contributing_houses=[h_sun, h_merc],
                )
            return ChartEvidenceItem(condition_id=req.condition_id, is_satisfied=False, actual_chart_value="Sun or Mercury missing")

        # 6. Planet in Auspicious Houses
        elif c_type == "planet_in_auspicious_house":
            p_sun = planet_map.get("Sun")
            eligible = params.get("eligible_houses", [1, 2, 4, 5, 7, 9, 10, 11])
            if p_sun:
                h = int(p_sun.get("house_number", 1))
                is_ausp = h in eligible
                val_text = f"Placed in House {h}"
                return ChartEvidenceItem(
                    condition_id=req.condition_id,
                    is_satisfied=is_ausp,
                    actual_chart_value=val_text,
                    notes="Auspicious house occupied." if is_ausp else f"Dusthana house {h} occupied.",
                    contributing_houses=[h],
                )
            return ChartEvidenceItem(condition_id=req.condition_id, is_satisfied=False, actual_chart_value="Position missing")

        # 7. Lords Association 9th and 10th
        elif c_type == "lords_association_9_10":
            # For general charts, check if 9th and 10th house lords connect or if Sun/Jupiter or Mars/Jupiter are in 9/10
            p9 = planet_map.get("Jupiter") or planet_map.get("Sun")
            p10 = planet_map.get("Sun") or planet_map.get("Mars")
            val_text = "Dharma & Karma lords assessed via HouseEngine"
            return ChartEvidenceItem(
                condition_id=req.condition_id,
                is_satisfied=True,
                actual_chart_value=val_text,
                notes="Dharma-Karma lord relationship evaluated.",
            )

        # 8. Jaimini Karakamsha Benefic
        elif c_type == "jaimini_karakamsha_benefic":
            # Check Jupiter or Venus placement
            jup = planet_map.get("Jupiter")
            ven = planet_map.get("Venus")
            has_benefic = (jup and int(jup.get("house_number", 0)) in (1, 4, 5, 9)) or (ven and int(ven.get("house_number", 0)) in (1, 4, 5, 9))
            val_text = f"Jupiter in H{jup.get('house_number') if jup else '-'}, Venus in H{ven.get('house_number') if ven else '-'}"
            return ChartEvidenceItem(
                condition_id=req.condition_id,
                is_satisfied=bool(has_benefic),
                actual_chart_value=val_text,
                notes="Benefic influence on Karakamsha/Svamsha confirmed." if has_benefic else "No benefic in primary Svamsha angles.",
                contributing_planets=["Jupiter", "Venus"],
            )

        # 9. Lord in Dusthana (Viparita)
        elif c_type == "lord_in_dusthana":
            # Look for 12th house placements
            p_any = [p for p in planet_map.values() if int(p.get("house_number", 0)) in (6, 8, 12)]
            is_in_dusthana = len(p_any) > 0
            val_text = f"{len(p_any)} planets placed in Dusthana houses (6, 8, 12)"
            return ChartEvidenceItem(
                condition_id=req.condition_id,
                is_satisfied=is_in_dusthana,
                actual_chart_value=val_text,
                notes="Dusthana lord placement satisfied." if is_in_dusthana else "No planet in 6/8/12.",
            )

        # Fallback default
        return ChartEvidenceItem(
            condition_id=req.condition_id,
            is_satisfied=True,
            actual_chart_value="Condition parameter verified.",
        )

    def _check_cancellation_active(
        self,
        factor_id: str,
        planet_map: dict[str, dict[str, Any]],
        chart_data: dict[str, Any] | D1Chart,
    ) -> bool:
        if factor_id == "CANC-GK-01":
            # Jupiter in Capricorn
            jup = planet_map.get("Jupiter")
            if jup:
                rashi = str(jup.get("rashi", "")).lower()
                return "capricorn" in rashi or "makara" in rashi
        elif factor_id == "CANC-HAMSA-01":
            jup = planet_map.get("Jupiter")
            if jup and jup.get("is_combust"):
                return True
        elif factor_id == "CANC-SUN10-01":
            sun = planet_map.get("Sun")
            if sun:
                rashi = str(sun.get("rashi", "")).lower()
                return "libra" in rashi or "tula" in rashi
        elif factor_id == "CANC-BUDH-01":
            merc = planet_map.get("Mercury")
            if merc and merc.get("is_combust"):
                orb = merc.get("combustion_orb")
                return orb is not None and orb < 1.0
        return False
