"""
AstroOS — SBC CellNum Vedha Engine Unit Tests

Regression-anchors this session's real-source verifications:
- packages/shared/sbc_cellnum_table.py's Right/Front/Left paths for
  Dhanishtha and Shatabhisha, cross-checked against
  sarvatobhadra_grid.py's independently-derived (Saravali + live-JHora
  confirmed) Forward/Opposite/Backward values.
- The source tool's own real audit-log example (Janma Rasi Pisces at
  CellNum 39, Rahu transiting through Shatabhisha) — reused here only
  to regression-test the CellNum path-lookup mechanism itself, not the
  benefic-only casting gate (that example predates, and is superseded
  by, the confirmed-from-VBA benefic-only rule; Rahu is asserted NOT to
  register as a caster in this engine, matching the corrected rule).
"""

from packages.shared.sbc_cellnum_table import cellnum_for_nakshatra, vedha_path
from apps.api.services.sbc_vedha_engine import SBCVedhaEngine, SBCTransitPlanet

# Roughly each planet's own mean daily motion (matches gati_classifier's
# table) so a "default speed" test planet lands in the "sama" (normal)
# gati bucket -> "front" direction, unless a test explicitly wants
# retrograde ("right") or fast/atichara ("left").
_MEAN_SPEED = {
    "sun": 0.9856, "moon": 13.176, "mars": 0.524, "mercury": 1.383,
    "jupiter": 0.083, "venus": 1.2, "saturn": 0.034, "rahu": 0.0529, "ketu": 0.0529,
}


def _planet(planet, nakshatra, rashi="aries", rashi_degree=10.0, speed=None,
            retrograde=False, combust=False, tithi=None):
    if speed is None:
        speed = _MEAN_SPEED.get(planet, 1.0)
    return SBCTransitPlanet(
        planet=planet, nakshatra=nakshatra, rashi=rashi, rashi_degree=rashi_degree,
        speed_deg_per_day=speed, is_retrograde=retrograde, is_combust=combust, tithi=tithi,
    )


# ── CellNum table: Dhanishtha / Shatabhisha column-mapping regression ──────

def test_dhanishtha_left_matches_saravali_forward_ashlesha():
    assert vedha_path("dhanishtha", "left")[-1] == cellnum_for_nakshatra("ashlesha")


def test_dhanishtha_front_matches_saravali_opposite_vishakha():
    assert vedha_path("dhanishtha", "front")[-1] == cellnum_for_nakshatra("vishakha")


def test_dhanishtha_right_matches_saravali_backward_shravana():
    assert vedha_path("dhanishtha", "right") == (cellnum_for_nakshatra("shravana"),)


def test_shatabhisha_left_matches_saravali_forward_pushya():
    assert vedha_path("shatabhisha", "left")[-1] == cellnum_for_nakshatra("pushya")


def test_shatabhisha_front_matches_saravali_opposite_swati():
    assert vedha_path("shatabhisha", "front")[-1] == cellnum_for_nakshatra("swati")


def test_shatabhisha_right_matches_saravali_backward_abhijit():
    """The specific pair JHora-confirmed this session (screenshot
    right-click "Highlight aspects FROM this star" on Shatabhisha)."""
    assert vedha_path("shatabhisha", "right")[-1] == cellnum_for_nakshatra("abhijit")


# ── Real audit-log example: path lookup only, not the benefic gate ─────────

def test_janma_pisces_cell39_in_shatabhisha_left_path():
    pisces_cellnum = 39
    assert pisces_cellnum in vedha_path("shatabhisha", "left")


def test_rahu_does_not_register_as_a_caster_under_corrected_rule():
    engine = SBCVedhaEngine()
    rahu = _planet("rahu", "shatabhisha", speed=0.05)
    result = engine.check_cellnum(39, [rahu])
    assert result.hits == []
    assert result.total_score == 0.0


# ── Benefic-only casting gate ───────────────────────────────────────────────

def test_jupiter_and_venus_always_cast():
    engine = SBCVedhaEngine()
    for planet in ("jupiter", "venus"):
        p = _planet(planet, "dhanishtha")
        result = engine.check("vishakha", [p])
        assert result.hits, f"{planet} should register a hit"


def test_sun_mars_saturn_rahu_ketu_never_cast():
    engine = SBCVedhaEngine()
    for planet in ("sun", "mars", "saturn", "rahu", "ketu"):
        p = _planet(planet, "dhanishtha")
        result = engine.check("vishakha", [p])
        assert result.hits == [], f"{planet} should never cast a Vedha"


def test_moon_benefic_only_when_tithi_6_to_20():
    engine = SBCVedhaEngine()
    waxing_gibbous = _planet("moon", "dhanishtha", tithi=10)
    new_moon = _planet("moon", "dhanishtha", tithi=1)

    assert engine.check("vishakha", [waxing_gibbous]).hits
    assert engine.check("vishakha", [new_moon]).hits == []


def test_moon_casts_all_three_directions_regardless_of_speed():
    engine = SBCVedhaEngine()
    moon = _planet("moon", "dhanishtha", tithi=10, speed=13.0)
    hit_ashlesha = engine.check("ashlesha", [moon])   # left path
    hit_vishakha = engine.check("vishakha", [moon])   # front path
    hit_shravana = engine.check("shravana", [moon])   # right path
    assert hit_ashlesha.hits and hit_vishakha.hits and hit_shravana.hits


def test_mercury_not_benefic_when_conjunct_a_malefic_in_same_nakshatra():
    engine = SBCVedhaEngine()
    mercury = _planet("mercury", "dhanishtha")
    saturn = _planet("saturn", "dhanishtha")
    result = engine.check("vishakha", [mercury, saturn])
    assert result.hits == []


def test_mercury_benefic_when_alone():
    engine = SBCVedhaEngine()
    mercury = _planet("mercury", "dhanishtha")
    result = engine.check("vishakha", [mercury])
    assert result.hits


# ── Motion-state -> direction rule ──────────────────────────────────────────

def test_retrograde_planet_casts_right_direction_only():
    engine = SBCVedhaEngine()
    venus_retro = _planet("venus", "shatabhisha", retrograde=True, speed=-0.5)
    assert engine.check("abhijit", [venus_retro]).hits  # right path -> Abhijit
    assert engine.check("swati", [venus_retro]).hits == []  # front path, not cast


def test_normal_speed_planet_casts_front_direction_only():
    engine = SBCVedhaEngine()
    jupiter_normal = _planet("jupiter", "dhanishtha", speed=0.08)
    assert engine.check("vishakha", [jupiter_normal]).hits  # front path
    assert engine.check("ashlesha", [jupiter_normal]).hits == []  # left path, not cast


# ── Scoring ──────────────────────────────────────────────────────────────

def test_combust_planet_scores_zero_but_still_registers_as_a_hit():
    engine = SBCVedhaEngine()
    combust_jupiter = _planet("jupiter", "dhanishtha", combust=True)
    result = engine.check("vishakha", [combust_jupiter])
    assert len(result.hits) == 1
    assert result.hits[0].score == 0.0
    assert result.total_score == 0.0


def test_retrograde_doubles_the_dignity_score():
    engine = SBCVedhaEngine()
    # Venus exalted in Pisces (dignity multiplier 3) at Shatabhisha -> right -> Abhijit.
    venus = _planet("venus", "shatabhisha", rashi="pisces", rashi_degree=25.0, retrograde=True)
    result = engine.check("abhijit", [venus])
    assert result.total_score == 5.0 * 3.0 * 2.0


def test_benefic_malefic_same_nakshatra_zeroes_entire_total():
    engine = SBCVedhaEngine()
    jupiter = _planet("jupiter", "dhanishtha")
    mars = _planet("mars", "dhanishtha")
    result = engine.check("vishakha", [jupiter, mars])
    assert result.zeroed_by_malefic_conjunction is True
    assert result.total_score == 0.0
    assert result.hits[0].score > 0  # per-hit score is untouched; only the total is zeroed
