"""
Tests for Saravali Shadbala Evaluation and Summary Engine.
"""

import pytest
from datetime import datetime, timezone

from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.shadbala.saravali_summary import (
    CLASSICAL_SEVEN,
    REQUIRED_SHADBALA_VIRUPAS,
    REQUIRED_SHADBALA_RUPAS,
    INDIVIDUAL_SUB_BALA_REQUIREMENTS,
    SaravaliShadbalaEvaluator,
)


def _make_result(cid: str, name: str, planet: str, val: float) -> BalaComponentResult:
    return BalaComponentResult(
        component_id=cid,
        component_name=name,
        rule_version="1.0",
        planet=planet,
        value_shashtiamsas=val,
        trace=(),
    )


def test_saravali_evaluator_complete_aggregation():
    # Build realistic test components
    planets = CLASSICAL_SEVEN
    
    naisargika = [_make_result("SHADBALA-NAISARGIKA", "Naisargika Bala", p, 30.0) for p in planets]
    dig = [_make_result("SHADBALA-DIG", "Dig Bala", p, 40.0) for p in planets]
    drik = [_make_result("SHADBALA-DRIK", "Drik Bala", p, 5.0) for p in planets]
    chesta = [_make_result("SHADBALA-CHESTA", "Chesta Bala", p, 45.0) for p in planets]
    paksha = [_make_result("SHADBALA-PAKSHA", "Paksha Bala", p, 35.0) for p in planets]
    ayana = [_make_result("SHADBALA-AYANA", "Ayana Bala", p, 42.0) for p in planets]
    yuddha = [_make_result("SHADBALA-YUDDHA", "Yuddha Bala", p, 0.0) for p in planets]
    uchcha = [_make_result("SHADBALA-UCHCHA", "Uchcha Bala", p, 50.0) for p in planets]
    kendradi = [_make_result("SHADBALA-KENDRADI", "Kendradi Bala", p, 60.0) for p in planets]
    drekkana = [_make_result("SHADBALA-DREKKANA", "Drekkana Bala", p, 15.0) for p in planets]
    saptavargaja = [_make_result("SHADBALA-SAPTAVARGAJA", "Saptavargaja Bala", p, 120.0) for p in planets]
    ojayugmarasyamsa = [_make_result("SHADBALA-OJAYUGMA", "Ojayugmarasyamsa Bala", p, 15.0) for p in planets]
    tribhaga = [_make_result("SHADBALA-TRIBHAGA", "Tribhaga Bala", p, 60.0) for p in planets]
    nathonnata = [_make_result("SHADBALA-NATHONNATA", "Nathonnata Bala", p, 30.0) for p in planets]
    dina_hora = [_make_result("SHADBALA-DINAHORA", "Dina Hora Bala", p, 45.0) for p in planets]

    report = SaravaliShadbalaEvaluator.evaluate(
        naisargika=naisargika,
        dig=dig,
        drik=drik,
        chesta=chesta,
        paksha=paksha,
        ayana=ayana,
        yuddha=yuddha,
        uchcha=uchcha,
        kendradi=kendradi,
        drekkana=drekkana,
        saptavargaja=saptavargaja,
        ojayugmarasyamsa=ojayugmarasyamsa,
        tribhaga=tribhaga,
        nathonnata=nathonnata,
        dina_hora=dina_hora,
    )

    assert len(report.planets) == 7
    assert report.strongest_planet != ""
    assert report.weakest_planet != ""
    assert report.average_strength_ratio > 0

    # Test Sun (Chesta equals Ayana)
    sun_summary = next(p for p in report.planets if p.planet == "sun")
    assert sun_summary.chesta_bala_virupas == sun_summary.ayana_bala_virupas
    assert sun_summary.required_virupas == 390.0
    assert sun_summary.required_rupas == 6.5
    assert sun_summary.total_rupas == round(sun_summary.total_virupas / 60.0, 4)

    # Test Moon (Chesta equals Paksha)
    moon_summary = next(p for p in report.planets if p.planet == "moon")
    assert moon_summary.chesta_bala_virupas == moon_summary.paksha_bala_virupas
    assert moon_summary.required_virupas == 360.0

    # Test individual sub-bala requirements
    for p in report.planets:
        assert len(p.sub_bala_checks) == 5
        keys = [c.bala_key for c in p.sub_bala_checks]
        assert "sthana_bala" in keys
        assert "dig_bala" in keys
        assert "kala_bala" in keys
        assert "chesta_bala" in keys
        assert "ayana_bala" in keys
        assert p.ishta_bala_virupas >= 0.0
        assert p.kashta_bala_virupas >= 0.0
        assert p.rank in range(1, 8)
