"""
AstroOS — Relocation Engine Unit Tests

Verifies the deterministic relocation fact producer:
  - determinism (same inputs -> same facts)
  - astronomical invariants (MC == ecliptic longitude of the RAMC;
    sidereal == tropical - ayanamsa)
  - relocated chart behaviour (Ascendant changes with the target location)
  - house / angular-status classification
  - Vedic Atmakaraka selection
  - midpoint in-orb consistency
  - local-space cardinal directions
  - frozen reference vector (Santa Monica -> Provo, tropical)
"""

from __future__ import annotations

import datetime
import math

import swisseph as swe
import pytest

from apps.api.services.relocation_engine import RelocationEngine

REDFORD_BIRTH = datetime.datetime(1936, 8, 19, 3, 2, 0)  # 1936-08-18 8:02pm PDT
SANTA_MONICA = (34.0195, -118.4912)
PROVO = (40.2338, -111.6585)


def _jd_ut(dt: datetime.datetime) -> float:
    _et, ut = swe.utc_to_jd(dt.year, dt.month, dt.day,
                            dt.hour, dt.minute,
                            dt.second + dt.microsecond / 1e6,
                            swe.GREG_CAL)
    return ut


def _facts(engine: RelocationEngine, birth, place, target, prefix="relocation"):
    return {f.key: f.value for f in engine.compute_facts(
        birth, place[0], place[1], target[0], target[1], prefix)}


# ── determinism & structure ───────────────────────────────────────────────────


def test_engine_is_deterministic():
    eng = RelocationEngine(ayanamsa="tropical")
    f1 = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    f2 = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    assert f1 == f2


def test_engine_emits_required_base_facts():
    eng = RelocationEngine(ayanamsa="tropical")
    f = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    for key in (
        "relocation.evaluated",
        "relocation.ascendant.degree",
        "relocation.ascendant.sign",
        "relocation.midheaven.degree",
        "relocation.midheaven.sign",
        "relocation.atmakaraka.planet",
        "relocation.paran.count",
        "relocation.lines.in_orb_count",
    ):
        assert key in f, key


# ── astronomical invariants ───────────────────────────────────────────────────


def test_midheaven_equals_ecliptic_longitude_of_ramc():
    """MC is the ecliptic longitude of the RAMC (LST at Greenwich + lon)."""
    jd_ut = _jd_ut(REDFORD_BIRTH)
    st_hours = swe.sidtime(jd_ut)
    ramc = (st_hours + PROVO[1] / 15.0) % 24.0 * 15.0
    eps = swe.calc_ut(jd_ut, swe.ECL_NUT, swe.FLG_SWIEPH)[0][0]
    ra_r = math.radians(ramc)
    expected = math.degrees(math.atan2(
        math.sin(ra_r), math.cos(ra_r) * math.cos(math.radians(eps)))) % 360.0

    eng = RelocationEngine(ayanamsa="tropical")
    f = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    # tolerances loose enough to absorb mean-vs-apparent sidereal time paths
    assert abs(f["relocation.midheaven.degree"] - expected) < 1e-3


def test_sidereal_equals_tropical_minus_ayanamsa():
    trop = RelocationEngine(ayanamsa="tropical")
    sid = RelocationEngine(ayanamsa="lahiri")
    ft = _facts(trop, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    fs = _facts(sid, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    jd_ut = _jd_ut(REDFORD_BIRTH)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)
    assert abs((ft["relocation.ascendant.degree"] - ayanamsa) % 360
               - fs["relocation.ascendant.degree"]) < 1e-3
    assert abs((ft["relocation.midheaven.degree"] - ayanamsa) % 360
               - fs["relocation.midheaven.degree"]) < 1e-3


def test_planet_sidereal_longitude_matches_swiss_ephemeris():
    eng = RelocationEngine(ayanamsa="lahiri")
    f = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    jd_ut = _jd_ut(REDFORD_BIRTH)
    pos, _r = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    assert abs(f["relocation.planet.sun.longitude"] - pos[0]) < 1e-3


# ── relocation behaviour ──────────────────────────────────────────────────────


def test_ascendant_changes_with_target_location():
    eng = RelocationEngine(ayanamsa="tropical")
    natal = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, SANTA_MONICA)
    provo = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    assert provo["relocation.ascendant.degree"] != natal["relocation.ascendant.degree"]


def test_frozen_reference_vector_santa_monica_to_provo():
    """Engine-computed reference vector (tropical Placidus)."""
    eng = RelocationEngine(ayanamsa="tropical", house_system="P")
    f = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    assert abs(f["relocation.ascendant.degree"] - 344.8584) < 1e-2
    assert abs(f["relocation.midheaven.degree"] - 261.8526) < 1e-2
    assert f["relocation.ascendant.sign"] == "pisces"
    assert f["relocation.midheaven.sign"] == "sagittarius"


# ── houses / angular status ───────────────────────────────────────────────────


def test_house_numbers_are_1_to_12_and_statuses_valid():
    eng = RelocationEngine(ayanamsa="tropical")
    f = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    for p in ("sun", "moon", "mars", "mercury", "jupiter", "venus",
              "saturn", "uranus", "neptune", "pluto", "rahu", "ketu"):
        house = f[f"relocation.planet.{p}.house"]
        status = f[f"relocation.planet.{p}.angular_status"]
        assert 1 <= house <= 12
        assert status in ("angular", "succedent", "cadent")
        expected = {1, 4, 7, 10} if status == "angular" else (
            {2, 5, 8, 11} if status == "succedent" else {3, 6, 9, 12})
        assert house in expected, (p, house, status)


def test_location_changed_and_natal_house_facts():
    eng = RelocationEngine(ayanamsa="tropical")
    same = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, SANTA_MONICA)
    moved = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    assert same["relocation.location_changed"] is False
    assert moved["relocation.location_changed"] is True
    # Relocated to Provo: planet houses differ from natal (R4 evidence).
    assert moved["relocation.house_changed.count"] >= 1
    assert moved["relocation.planet.moon.house_changed"] == (
        moved["relocation.planet.moon.house"] != moved["relocation.planet.moon.natal_house"])
    # Moon's longitude is invariant under relocation (R1 evidence).
    assert (moved["relocation.planet.moon.longitude"]
            == same["relocation.planet.moon.longitude"])


def test_whole_sign_house_system_differs_from_placidus():
    plac = RelocationEngine(ayanamsa="tropical", house_system="P")
    whole = RelocationEngine(ayanamsa="tropical", house_system="W")
    fp = _facts(plac, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    fw = _facts(whole, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    planets = ("sun", "moon", "mars", "mercury", "jupiter", "venus",
               "saturn", "uranus", "neptune", "pluto", "rahu", "ketu")
    assert any(fp[f"relocation.planet.{p}.house"]
               != fw[f"relocation.planet.{p}.house"] for p in planets)


# ── atmakaraka ────────────────────────────────────────────────────────────────


def test_atmakaraka_is_highest_degree_in_sign_planet():
    eng = RelocationEngine(ayanamsa="tropical")
    f = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    vedic = ("sun", "moon", "mars", "mercury", "jupiter",
             "venus", "saturn", "rahu", "ketu")
    degrees = {p: f[f"relocation.planet.{p}.longitude"] % 30.0 for p in vedic}
    expected = max(degrees, key=degrees.get)
    assert f["relocation.atmakaraka.planet"] == expected


# ── midpoints & parans & local space ──────────────────────────────────────────


def test_midpoint_in_orb_is_consistent_with_orbs():
    eng = RelocationEngine(ayanamsa="tropical", line_orb_deg=6.0)
    f = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    asc = f["relocation.ascendant.degree"]
    mc = f["relocation.midheaven.degree"]
    key = "relocation.midpoint.sun_jupiter"
    assert key + ".asc_orb" in f
    min_orb = min(f[f"{key}.asc_orb"], f[f"{key}.mc_orb"])
    assert f[f"{key}.in_orb"] == (min_orb <= 6.0)


def test_paran_members_are_angular_planets():
    eng = RelocationEngine(ayanamsa="tropical")
    f = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    members = set(f["relocation.paran.planets"].split(","))
    for p in members:
        assert f[f"relocation.planet.{p}.angular_status"] == "angular"


def test_local_space_directions_are_cardinal():
    eng = RelocationEngine(ayanamsa="tropical")
    f = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    for p in ("sun", "moon", "jupiter", "venus"):
        assert f[f"relocation.local_space.{p}.direction"] in (
            "north", "east", "south", "west")


def test_custom_prefix_supports_twin_locations():
    eng = RelocationEngine(ayanamsa="tropical")
    fa = {k.replace("relocation_a.", "relocation.", 1): v
          for k, v in _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO,
                             "relocation_a").items()}
    fb = {k.replace("relocation_b.", "relocation.", 1): v
          for k, v in _facts(eng, REDFORD_BIRTH, SANTA_MONICA, SANTA_MONICA,
                             "relocation_b").items()}
    assert fa["relocation.evaluated"] is True
    assert fb["relocation.evaluated"] is True
    assert fa["relocation.ascendant.degree"] != fb["relocation.ascendant.degree"]


def test_harmonic_family_classification():
    eng = RelocationEngine(ayanamsa="tropical")
    f = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, PROVO)
    assert f["relocation.ascendant.harmonic_family"] == "seventh"
    # A synthetic round-40 degree line would be ninth; label with minutes is seventh.
    from apps.api.services.relocation_engine import _harmonic_family
    assert _harmonic_family(140.0) == "ninth"
    assert _harmonic_family(72.0) == "fifth"
    assert _harmonic_family(108.0) == "fifth"
    assert _harmonic_family(128.5667) == "seventh"
    assert _harmonic_family(145.5) == "seventh"


def test_ninth_harmonic_to_angle_facts():
    from apps.api.services.relocation_engine import _in_ninth_harmonic
    # 40° off an angle is exactly the 9th harmonic (within orb).
    assert _in_ninth_harmonic(40.0, 0.0, 6.0) is True
    assert _in_ninth_harmonic(46.0, 0.0, 6.0) is True
    assert _in_ninth_harmonic(46.5, 0.0, 6.0) is False
    assert _in_ninth_harmonic(120.0, 0.0, 6.0) is True
    assert _in_ninth_harmonic(30.0, 0.0, 6.0) is False
    # Engine facts: Honolulu puts the Moon in 9th-harmonic relation.
    eng = RelocationEngine(ayanamsa="tropical", house_system="P")
    f = _facts(eng, REDFORD_BIRTH, SANTA_MONICA, (21.3069, -157.8583))
    assert f["relocation.planet.moon.ninth_harmonic_to_angle"] is True
