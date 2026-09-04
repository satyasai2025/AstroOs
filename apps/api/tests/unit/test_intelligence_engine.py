"""
AstroOS — Unit Tests for Vinay Jha Intelligent Prediction Engine
"""

import pytest
from apps.api.services.intelligence import (
    StrengthModel,
    DignityScore,
    DrishtiModel,
    UpagrahaRulesEngine,
    LinkedSystemBuilder,
    CognitiveReasoner,
    DashaPeriod5Level,
    IntelligentPredictor,
    CognitiveVerifier,
)
from apps.api.services.intelligence.events import (
    MarriagePredictor,
    CareerPredictor,
    HealthPredictor,
    AccidentPredictor,
)


def test_strength_model_dignities_and_log_scale():
    # Sun exalted in Mesha (0)
    assert StrengthModel.get_dignity_score("Sun", 0) == DignityScore.UCHCHA
    assert StrengthModel.calculate_log_strength(DignityScore.UCHCHA) == 256.0

    # Sun debilitated in Tula (6)
    assert StrengthModel.get_dignity_score("Sun", 6) == DignityScore.NEECHA
    assert StrengthModel.calculate_log_strength(DignityScore.NEECHA) == 1.0

    # Jupiter in Cancer (3) -> Exalted
    assert StrengthModel.get_dignity_score("Jupiter", 3) == DignityScore.UCHCHA

    # Mars in Capricorn (9) -> Exalted
    assert StrengthModel.get_dignity_score("Mars", 9) == DignityScore.UCHCHA


def test_drishti_model_aspect_strengths():
    # Universal 7th house aspect
    assert DrishtiModel.get_aspect_strength("Sun", source_house=1, target_house=7) == 1.0

    # Mars special aspects (4th and 8th)
    assert DrishtiModel.get_aspect_strength("Mars", source_house=1, target_house=4) == 1.0
    assert DrishtiModel.get_aspect_strength("Mars", source_house=1, target_house=8) == 1.0

    # Jupiter special aspects (5th and 9th)
    assert DrishtiModel.get_aspect_strength("Jupiter", source_house=1, target_house=5) == 1.0
    assert DrishtiModel.get_aspect_strength("Jupiter", source_house=1, target_house=9) == 1.0

    # Saturn special aspects (3rd and 10th)
    assert DrishtiModel.get_aspect_strength("Saturn", source_house=1, target_house=3) == 1.0
    assert DrishtiModel.get_aspect_strength("Saturn", source_house=1, target_house=10) == 1.0


def test_upagraha_rules_evaluation():
    # Chart with Gulika in 8th and Mandi in 7th
    interferences = UpagrahaRulesEngine.evaluate_upagrahas(
        gulika_house=8,
        mandi_house=7,
        graha_houses={"Sun": 1, "Moon": 4, "Mars": 10, "Mercury": 2, "Jupiter": 9, "Venus": 7, "Saturn": 11},
        seventh_lord="Venus",
        eighth_lord="Mars",
    )

    # Check 8th house Mrityu indicator
    mrityu_rules = [i for i in interferences if i.rule_name == "GULIKA_8TH_MRITYU_INDICATOR"]
    assert len(mrityu_rules) == 1
    assert mrityu_rules[0].weight_delta == +2.5

    # Check 7th house Mandi obstacle
    mandi_rules = [i for i in interferences if i.rule_name == "MANDI_7TH_MARRIAGE_OBSTACLE"]
    assert len(mandi_rules) == 1
    assert mandi_rules[0].weight_delta < 0


def test_linked_system_and_cognitive_reasoning():
    # Mesha Lagna (0)
    # Positions: Sun in Mesha (0), Moon in Karka (3), Mars in Makara (9), Venus in Tula (6), Jupiter in Meena (11)
    graha_pos = {
        "Sun": 0,
        "Moon": 3,
        "Mars": 9,
        "Mercury": 0,
        "Jupiter": 11,
        "Venus": 6,
        "Saturn": 10,
        "Rahu": 1,
        "Ketu": 7,
    }

    graph = LinkedSystemBuilder.build_graph(
        lagna_rashi_idx=0,
        graha_positions=graha_pos,
        gulika_rashi_idx=2,  # 3rd house (Upachaya) -> benefic
        mandi_rashi_idx=6,   # 7th house
    )

    assert graph.gulika_house == 3
    assert graph.mandi_house == 7

    # Test Marriage Dasha: Venus MD (7th lord), Jupiter AD (Karaka), Venus PD, Venus Sookshma, Jupiter Praana
    dasha_marriage = DashaPeriod5Level(
        mahadasha="Venus",
        antardasha="Jupiter",
        pratyantardasha="Venus",
        sookshma="Venus",
        praana="Jupiter",
    )

    res_marriage = MarriagePredictor.evaluate(graph, dasha_marriage)
    assert 0.0 <= res_marriage.probability_score <= 9.0
    assert len(res_marriage.level_assessments) == 5
    assert len(res_marriage.rule_traces) > 0

    # Test Career Dasha: Sun MD (5th lord in Lagna exalted), Mars AD (10th occupant exalted)
    dasha_career = DashaPeriod5Level(
        mahadasha="Sun",
        antardasha="Mars",
        pratyantardasha="Jupiter",
        sookshma="Sun",
        praana="Mars",
    )

    res_career = CareerPredictor.evaluate(graph, dasha_career)
    assert res_career.probability_score >= 5.0
    assert res_career.is_probable is True


def test_canonical_engine_consumption():
    from datetime import datetime, timezone
    from apps.api.services.dasha_engine import DashaEngine
    from apps.api.services.upagraha_engine import UpagrahaEngine
    from apps.api.services.intelligence import (
        extract_5level_periods_from_dasha_tree,
        LinkedSystemBuilder,
        CognitiveReasoner,
    )

    from apps.api.services.ephemeris_wrapper import EphemerisWrapper

    # 1. Compute canonical 5-level DashaTree via existing canonical dasha_engine
    ephem = EphemerisWrapper(ephemeris_path="data/ephemeris")
    dasha_engine = DashaEngine(ephemeris_wrapper=ephem)
    dt = datetime(1990, 5, 15, 12, 0, 0, tzinfo=timezone.utc)
    canonical_tree = dasha_engine.compute_vimshottari(
        birth_datetime_utc=dt,
        latitude=28.6139,
        longitude=77.2090,
        max_depth=5,
    )
    assert canonical_tree.system == "vimshottari"



    # 2. Cognitive layer consumes the canonical tree directly without duplicating dasha math
    extracted_5level = extract_5level_periods_from_dasha_tree(canonical_tree)
    assert len(extracted_5level) > 0
    first_period = extracted_5level[0]
    assert first_period.mahadasha != ""
    assert first_period.antardasha != ""
    assert first_period.pratyantardasha != ""
    assert first_period.sookshma != ""
    assert first_period.praana != ""

    # 3. Compute canonical UpagrahaReport without duplicating ephemeris math
    upagraha_engine = UpagrahaEngine()
    upagraha_report = upagraha_engine.compute_upagrahas(
        birth_datetime=dt,
        latitude=28.6139,
        longitude=77.2090,
    )
    assert upagraha_report.gulika.name == "Gulika"

    # 4. Cognitive LinkedSystem directly consumes canonical upagraha report
    graha_pos = {"Sun": 1, "Moon": 1, "Mars": 10, "Mercury": 1, "Jupiter": 3, "Venus": 0, "Saturn": 9}
    graph = LinkedSystemBuilder.from_canonical_report(
        lagna_rashi_idx=3,
        graha_positions=graha_pos,
        upagraha_report=upagraha_report,
    )

    # 5. Feed into Cognitive Reasoner
    res = CognitiveReasoner.evaluate_event_dasha(graph, first_period, "career")
    assert 0.0 <= res.cognitive_score <= 9.0


def test_marriage_prediction():
    # Mesha Lagna (0), Venus (7th lord) in Libra (6) -> Svagriha (Score 7)
    graha_pos = {
        "Sun": 0, "Moon": 3, "Mars": 0, "Mercury": 1,
        "Jupiter": 8, "Venus": 6, "Saturn": 10, "Rahu": 1, "Ketu": 7,
    }
    graph = LinkedSystemBuilder.build_graph(
        lagna_rashi_idx=0,
        graha_positions=graha_pos,
        gulika_rashi_idx=2,
        mandi_rashi_idx=8,
    )
    dasha = DashaPeriod5Level(
        mahadasha="Venus",      # 7th Lord
        antardasha="Jupiter",   # 9th Lord / Karaka
        pratyantardasha="Venus",
        sookshma="Venus",
        praana="Jupiter",
    )
    res = MarriagePredictor.evaluate(graph, dasha)
    assert res.event_type == "marriage"
    assert 0.0 <= res.cognitive_score <= 9.0
    assert res.cognitive_score >= 5.0
    assert res.is_probable is True


def test_career_prediction():
    # Mesha Lagna (0), Sun (5th lord exalted in Lagna), Mars (10th lord/1st lord exalted in 10th Capricorn)
    graha_pos = {
        "Sun": 0, "Moon": 3, "Mars": 9, "Mercury": 0,
        "Jupiter": 11, "Venus": 6, "Saturn": 9, "Rahu": 1, "Ketu": 7,
    }
    graph = LinkedSystemBuilder.build_graph(
        lagna_rashi_idx=0,
        graha_positions=graha_pos,
        gulika_rashi_idx=9,  # 10th house Upachaya (+1.5 boost)
        mandi_rashi_idx=10,
    )
    dasha = DashaPeriod5Level(
        mahadasha="Mars",   # 10th occupant/lord
        antardasha="Sun",   # Exalted royal lord
        pratyantardasha="Mars",
        sookshma="Sun",
        praana="Jupiter",
    )
    res = CareerPredictor.evaluate(graph, dasha)
    assert res.event_type == "career"
    assert 0.0 <= res.cognitive_score <= 9.0
    assert res.cognitive_score >= 6.0
    assert res.is_probable is True


def test_health_prediction():
    # Karka Lagna (3), Saturn (7th/8th lord), Mars (rules 10th/5th), Gulika in 8th house (Kumbha=10)
    graha_pos = {
        "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 5,
        "Jupiter": 9, "Venus": 5, "Saturn": 10, "Rahu": 1, "Ketu": 7,
    }
    graph = LinkedSystemBuilder.build_graph(
        lagna_rashi_idx=3,
        graha_positions=graha_pos,
        gulika_rashi_idx=10,  # 8th house from Cancer (Kumbha) -> +2.5 Mrityu weight
        mandi_rashi_idx=10,
    )
    dasha = DashaPeriod5Level(
        mahadasha="Saturn",   # 8th house lord/occupant
        antardasha="Mars",    # Malefic
        pratyantardasha="Saturn",
        sookshma="Rahu",
        praana="Mars",
    )
    res = HealthPredictor.evaluate(graph, dasha)
    assert res.event_type == "health"
    assert 0.0 <= res.cognitive_score <= 9.0
    assert res.cognitive_score >= 5.0
    assert res.is_probable is True


def test_accident_prediction():
    # Mesha Lagna (0), Mars and Rahu in 8th house (Scorpio=7), Gulika in 8th house
    graha_pos = {
        "Sun": 6, "Moon": 7, "Mars": 7, "Mercury": 6,
        "Jupiter": 9, "Venus": 5, "Saturn": 0, "Rahu": 7, "Ketu": 1,
    }
    graph = LinkedSystemBuilder.build_graph(
        lagna_rashi_idx=0,
        graha_positions=graha_pos,
        gulika_rashi_idx=7,  # 8th house from Aries -> Mrityu indicator
        mandi_rashi_idx=7,
    )
    dasha = DashaPeriod5Level(
        mahadasha="Mars",  # 8th occupant & accident karaka
        antardasha="Rahu", # 8th occupant & trauma karaka
        pratyantardasha="Mars",
        sookshma="Rahu",
        praana="Ketu",
    )
    res = AccidentPredictor.evaluate(graph, dasha)
    assert res.event_type == "accident"
    assert 0.0 <= res.cognitive_score <= 9.0
    assert res.cognitive_score >= 5.0
    assert res.is_probable is True



