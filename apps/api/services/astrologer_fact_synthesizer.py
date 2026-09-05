"""
AstroOS — Master Astrologer Fact Synthesizer
============================================
Conforms strictly to:
  1. Vinay Jha Canonical Prediction Framework (docs/CANONICAL_PREDICTION_FRAMEWORK.md)
  2. Parashari Siddhanta:
     - D1 Bhavachalita for house placements and lordships (Rasi for math only).
     - Strictly 7 Chara Karakas (Never 8, Sapta-Karaka scheme).
     - Jha Log-Base-2 Main Strength (2^(dignity-1), 1.0 to 256.0).
     - Multi-level Vimshottari Dasha chain (MD -> AD -> PD).
     - Divisional Harmony: D9 Navamsha (Dharma/Spouse), D10 Dashamsha (Karma/Status).
     - Bhavottama detection (same bhava across divisionals).
     - Active Yogas (Raja, Dhana, Arishta).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from apps.api.domain.horoscope import D1Chart
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.dasha_lookup import find_active_dasha_chain
from apps.api.services.divisional_engine import compute_varga_sign
from apps.api.services.house_engine import HouseEngine
from apps.api.services.jaimini_engine import CharaKarakaEngine
from apps.api.services.jha_dignity_engine import JhaDignityEngine, RASHI_LIST, RASHI_LORDS
from apps.api.services.yoga_engine import YogaEngine
from packages.shared.rashi_offset import house_offset

_CANONICAL_GRAHAS = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")


@dataclass(frozen=True)
class AstrologerFactContext:
    subject_name: str
    birth_datetime_iso: str
    target_date_iso: str
    ayanamsa: str
    
    # 1. Foundation: Lagna & Luminaries
    ascendant: Dict[str, Any]
    moon: Dict[str, Any]
    sun: Dict[str, Any]
    
    # 2. Bhavachalita House Occupancies (1 to 12)
    bhavachalita_houses: Dict[int, List[str]]
    
    # 3. Strictly 7 Chara Karakas (AK to DK)
    chara_karakas_7: List[Dict[str, Any]]
    
    # 4. Jha Log-Base-2 Main Strength (1.0 to 256.0)
    main_strength_log2: Dict[str, Dict[str, Any]]
    
    # 5. Running Vimshottari Chain (MD -> AD -> PD)
    active_vimshottari: Dict[str, Any]
    
    # 6. Divisional Charts Harmony (D9 & D10)
    d9_navamsha: Dict[str, Any]
    d10_dashamsha: Dict[str, Any]
    bhavottama_planets: List[str]
    
    # 7. Active Shastric Yogas
    active_yogas: List[Dict[str, str]]
    
    # Pre-serialized prompt grounding text
    dense_grounding_text: str


class AstrologerFactSynthesizer:
    """
    Synthesizes full chart calculation domain models into a unified,
    canonical Shastric Fact Context for deterministic or LLM consultation.
    """

    def __init__(
        self,
        ephemeris_wrapper: Optional[EphemerisWrapper] = None,
        house_engine: Optional[HouseEngine] = None,
        dasha_engine: Optional[DashaEngine] = None,
        yoga_engine: Optional[YogaEngine] = None,
    ) -> None:
        from apps.api.services.ephemeris_wrapper import EphemerisWrapper
        self._ephemeris_wrapper = ephemeris_wrapper or EphemerisWrapper("data/ephemeris")
        self._house_engine = house_engine or HouseEngine()
        self._dasha_engine = dasha_engine or DashaEngine(self._ephemeris_wrapper)
        self._yoga_engine = yoga_engine or YogaEngine(self._house_engine)
        self._karaka_engine = CharaKarakaEngine()

    def synthesize(
        self,
        chart: D1Chart,
        target_date: Optional[date] = None,
        subject_name: str = "Native",
    ) -> AstrologerFactContext:
        eval_date = target_date or datetime.now(timezone.utc).date()

        # Normalize planets into dict[str, SiderealPosition]
        planets_dict = {}
        if isinstance(chart.planets, (list, tuple)):
            for pos in chart.planets:
                planets_dict[pos.planet.lower()] = pos
        elif isinstance(chart.planets, dict):
            planets_dict = {k.lower(): v for k, v in chart.planets.items()}

        # 1. Foundation: Ascendant, Moon, Sun
        asc = chart.ascendant
        asc_rashi_str = asc.rashi.value if hasattr(asc.rashi, "value") else str(asc.rashi)
        asc_sign_lord = RASHI_LORDS.get(asc_rashi_str.lower(), "mars")
        asc_nak_str = asc.nakshatra if isinstance(asc.nakshatra, str) else getattr(asc.nakshatra, "name", str(asc.nakshatra))
        
        asc_info = {
            "rashi": asc_rashi_str,
            "degree": round(asc.rashi_degree, 2),
            "nakshatra": asc_nak_str,
            "pada": asc.pada,
            "sign_lord": asc_sign_lord,
        }
        
        moon_pos = planets_dict.get("moon")
        moon_rashi_str = moon_pos.rashi.value if hasattr(moon_pos.rashi, "value") else str(moon_pos.rashi) if moon_pos else "Unknown"
        moon_nak_str = moon_pos.nakshatra.name if hasattr(moon_pos.nakshatra, "name") else str(moon_pos.nakshatra) if moon_pos else "Unknown"
        moon_info = {
            "rashi": moon_rashi_str,
            "degree": round(moon_pos.rashi_degree, 2) if moon_pos else 0.0,
            "nakshatra": moon_nak_str,
            "pada": moon_pos.pada if moon_pos else 1,
            "sign_lord": RASHI_LORDS.get(moon_rashi_str.lower(), ""),
        }
        
        sun_pos = planets_dict.get("sun")
        sun_rashi_str = sun_pos.rashi.value if hasattr(sun_pos.rashi, "value") else str(sun_pos.rashi) if sun_pos else "Unknown"
        sun_nak_str = sun_pos.nakshatra.name if hasattr(sun_pos.nakshatra, "name") else str(sun_pos.nakshatra) if sun_pos else "Unknown"
        sun_info = {
            "rashi": sun_rashi_str,
            "degree": round(sun_pos.rashi_degree, 2) if sun_pos else 0.0,
            "nakshatra": sun_nak_str,
            "pada": sun_pos.pada if sun_pos else 1,
            "sign_lord": RASHI_LORDS.get(sun_rashi_str.lower(), ""),
        }

        # 2. Bhavachalita House Occupancies (Houses 1 to 12)
        bhavachalita_houses: Dict[int, List[str]] = {h: [] for h in range(1, 13)}
        asc_rashi_idx = RASHI_LIST.index(asc_rashi_str.lower()) if asc_rashi_str.lower() in RASHI_LIST else 0
        for p_name, pos in planets_dict.items():
            h_num = getattr(pos, "house_number", None)
            if not h_num or h_num < 1 or h_num > 12:
                p_rashi_str = pos.rashi.value if hasattr(pos.rashi, "value") else str(pos.rashi)
                p_rashi_idx = RASHI_LIST.index(p_rashi_str.lower()) if p_rashi_str.lower() in RASHI_LIST else 0
                h_num = house_offset(asc_rashi_idx, p_rashi_idx)
            bhavachalita_houses[h_num].append(p_name.capitalize())

        # 3. Strictly 7 Chara Karakas (Sapta Karaka scheme per Jha canonical rule)
        karaka_result = self._karaka_engine.compute(chart, scheme="sapta_karaka")
        karakas_7 = [
            {
                "karaka": k.karaka_name,
                "planet": k.planet.capitalize(),
                "degree": round(k.karaka_degree, 2),
                "rank": k.rank,
            }
            for k in karaka_result.karakas
        ]

        # 4. Jha Log-Base-2 Main Strength (1.0 to 256.0)
        planet_positions_map = {
            p: pos.sidereal_longitude for p, pos in planets_dict.items()
        }
        main_strengths: Dict[str, Dict[str, Any]] = {}
        for p in _CANONICAL_GRAHAS:
            pos = planets_dict.get(p)
            if not pos:
                continue
            dignity = JhaDignityEngine.evaluate_planet_dignity(
                planet=p,
                sidereal_lon=pos.sidereal_longitude,
                chart_planet_positions=planet_positions_map,
                varga_code="D1",
                vimshopaka_weight=6.0,
            )
            main_strengths[p] = {
                "dignity_label": dignity.dignity_label,
                "dignity_tier": dignity.dignity_tier,
                "main_strength": dignity.main_strength,
                "panchadha_relation": dignity.panchadha_relation,
            }

        # 5. Running Vimshottari Chain (MD -> AD -> PD)
        from apps.api.services.dasha_engine import (
            _nakshatra_balance, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS, VIMSHOTTARI_TOTAL_YEARS, DashaTree
        )
        from apps.api.services.ephemeris_wrapper import longitude_to_nakshatra
        import swisseph as swe

        birth_dt = getattr(chart, "birth_datetime_utc", None)
        if not isinstance(birth_dt, datetime):
            jd = getattr(chart.ephemeris, "julian_day", 2448026.854167)
            yr, mo, dy, hr = swe.revjul(jd)
            hr_int = int(hr)
            min_int = int((hr - hr_int) * 60)
            sec_int = int(round(((hr - hr_int) * 60 - min_int) * 60))
            birth_dt = datetime(yr, mo, dy, hr_int, min_int, min(sec_int, 59), tzinfo=timezone.utc)

        moon_sid = moon_pos.sidereal_longitude if moon_pos else 0.0
        nak_info = longitude_to_nakshatra(moon_sid)
        first_lord, balance, first_start = _nakshatra_balance(
            moon_sid, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, birth_dt
        )
        mahadashas = self._dasha_engine._build_full_cycle(
            first_lord, first_start,
            VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, 3
        )
        dasha_tree = DashaTree(
            system="vimshottari",
            birth_date=birth_dt.date(),
            trigger_planet=first_lord,
            trigger_nakshatra=nak_info.nakshatra,
            trigger_nakshatra_number=nak_info.nakshatra_number,
            mahadashas=mahadashas,
            max_depth=3,
            total_cycle_years=VIMSHOTTARI_TOTAL_YEARS,
            balance_at_birth=balance,
            moon_longitude_at_trigger=moon_sid,
            ayanamsa_used=getattr(chart.ephemeris, "ayanamsa_value", 23.8),
            birth_datetime_utc=birth_dt,
        )
        active_chain = find_active_dasha_chain(dasha_tree, eval_date)
        active_dasha_info: Dict[str, Any] = {
            "evaluation_date": eval_date.isoformat(),
            "mahadasha": active_chain[0].lord.capitalize() if len(active_chain) > 0 else "None",
            "antardasha": active_chain[1].lord.capitalize() if len(active_chain) > 1 else "None",
            "pratyantardasha": active_chain[2].lord.capitalize() if len(active_chain) > 2 else "None",
            "mahadasha_end": active_chain[0].end_date.isoformat() if len(active_chain) > 0 else "",
            "antardasha_end": active_chain[1].end_date.isoformat() if len(active_chain) > 1 else "",
        }

        # 6. Divisional Charts (D9 Navamsha & D10 Dashamsha)
        d9_asc_sign, _ = compute_varga_sign("D9", asc.sidereal_longitude)
        d10_asc_sign, _ = compute_varga_sign("D10", asc.sidereal_longitude)
        
        moon_d9, _ = compute_varga_sign("D9", moon_pos.sidereal_longitude) if moon_pos else ("", 0)
        venus_pos = planets_dict.get("venus")
        venus_d9, _ = compute_varga_sign("D9", venus_pos.sidereal_longitude) if venus_pos else ("", 0)

        sun_d10, _ = compute_varga_sign("D10", sun_pos.sidereal_longitude) if sun_pos else ("", 0)
        saturn_pos = planets_dict.get("saturn")
        saturn_d10, _ = compute_varga_sign("D10", saturn_pos.sidereal_longitude) if saturn_pos else ("", 0)

        # Bhavottama detection (occupying SAME BHAVA across D1 and D9)
        d9_asc_idx = RASHI_LIST.index(d9_asc_sign.lower()) if d9_asc_sign.lower() in RASHI_LIST else 0
        bhavottama_planets: List[str] = []
        for p, pos in planets_dict.items():
            p_rashi_str = pos.rashi.value if hasattr(pos.rashi, "value") else str(pos.rashi)
            p_rashi_idx = RASHI_LIST.index(p_rashi_str.lower()) if p_rashi_str.lower() in RASHI_LIST else 0
            d1_h = house_offset(asc_rashi_idx, p_rashi_idx)
            
            p_d9_sign, _ = compute_varga_sign("D9", pos.sidereal_longitude)
            p_d9_idx = RASHI_LIST.index(p_d9_sign.lower()) if p_d9_sign.lower() in RASHI_LIST else 0
            d9_h = house_offset(d9_asc_idx, p_d9_idx)
            
            if d1_h == d9_h:
                bhavottama_planets.append(p.capitalize())

        d9_summary = {
            "ascendant_rashi": d9_asc_sign.capitalize(),
            "moon_navamsha": moon_d9.capitalize(),
            "venus_navamsha": venus_d9.capitalize(),
        }
        
        d10_summary = {
            "ascendant_rashi": d10_asc_sign.capitalize(),
            "sun_dashamsha": sun_d10.capitalize(),
            "saturn_dashamsha": saturn_d10.capitalize(),
        }

        # 7. Active Yogas
        all_yogas = self._yoga_engine.evaluate_all(chart)
        active_yogas = [
            {
                "name": y.name,
                "category": y.category.value if hasattr(y.category, "value") else str(y.category),
                "description": y.source_text,
            }
            for y in all_yogas
            if y.is_present
        ]

        # 8. Build Dense Fact Grounding String
        birth_iso = (
            getattr(chart, "birth_datetime_utc", None)
            or getattr(chart.ephemeris, "julian_day", "Recorded Birth")
        )
        if isinstance(birth_iso, datetime):
            birth_iso = birth_iso.isoformat()
        else:
            birth_iso = str(birth_iso)

        lines: List[str] = []
        lines.append(f"### NATAL HOROSCOPE FACTS ({subject_name})")
        lines.append(f"- Birth Record: {birth_iso} | Ayanamsa: {chart.ayanamsa_system}")
        lines.append(f"- Lagna (Ascendant): {asc_info['rashi']} {asc_info['degree']}° | Nakshatra: {asc_info['nakshatra']} (Pada {asc_info['pada']}) | Lord: {asc_info['sign_lord']}")
        lines.append(f"- Chandra (Moon): {moon_info['rashi']} {moon_info['degree']}° | Nakshatra: {moon_info['nakshatra']} (Pada {moon_info['pada']}) | Lord: {moon_info['sign_lord']}")
        lines.append(f"- Surya (Sun): {sun_info['rashi']} {sun_info['degree']}° | Nakshatra: {sun_info['nakshatra']} | Lord: {sun_info['sign_lord']}")
        
        lines.append("\n### BHAVACHALITA HOUSE PLACEMENTS (1 TO 12)")
        for h in range(1, 13):
            occupants = ", ".join(bhavachalita_houses[h]) if bhavachalita_houses[h] else "Vacant"
            lines.append(f"- House {h}: {occupants}")

        lines.append("\n### 7 CHARA KARAKAS (Vinay Jha Canonical Parashari Scheme)")
        for k in karakas_7:
            lines.append(f"- {k['karaka']}: {k['planet']} ({k['degree']}°)")

        lines.append("\n### PLANETARY DIGNITY & LOG-BASE-2 MAIN STRENGTH (1.0 to 256.0)")
        for p, s in main_strengths.items():
            lines.append(f"- {p.capitalize()}: {s['dignity_label']} (Tier {s['dignity_tier']}/9, Strength {s['main_strength']:.1f}x)")

        lines.append(f"\n### CURRENT VIMSHOTTARI TIMING (As of {eval_date.isoformat()})")
        lines.append(f"- Mahadasha: {active_dasha_info['mahadasha']} (Ends: {active_dasha_info['mahadasha_end']})")
        lines.append(f"- Antardasha: {active_dasha_info['antardasha']} (Ends: {active_dasha_info['antardasha_end']})")
        lines.append(f"- Pratyantardasha: {active_dasha_info['pratyantardasha']}")

        lines.append("\n### DIVISIONAL HARMONY & BHAVOTTAMA")
        lines.append(f"- D9 Navamsha Lagna: {d9_summary['ascendant_rashi']} | Moon: {d9_summary['moon_navamsha']} | Venus: {d9_summary['venus_navamsha']}")
        lines.append(f"- D10 Dashamsha Lagna: {d10_summary['ascendant_rashi']} | Sun: {d10_summary['sun_dashamsha']}")
        bhav_str = ", ".join(bhavottama_planets) if bhavottama_planets else "None"
        lines.append(f"- Bhavottama Planets (Same house across divisionals): {bhav_str}")

        lines.append(f"\n### ACTIVE SHASTRIC YOGAS ({len(active_yogas)} Detected)")
        for y in active_yogas[:8]:
            lines.append(f"- {y['name']} ({y['category']}): {y['description']}")

        dense_grounding_text = "\n".join(lines)

        return AstrologerFactContext(
            subject_name=subject_name,
            birth_datetime_iso=birth_iso,
            target_date_iso=eval_date.isoformat(),
            ayanamsa=chart.ayanamsa_system,
            ascendant=asc_info,
            moon=moon_info,
            sun=sun_info,
            bhavachalita_houses=bhavachalita_houses,
            chara_karakas_7=karakas_7,
            main_strength_log2=main_strengths,
            active_vimshottari=active_dasha_info,
            d9_navamsha=d9_summary,
            d10_dashamsha=d10_summary,
            bhavottama_planets=bhavottama_planets,
            active_yogas=active_yogas,
            dense_grounding_text=dense_grounding_text,
        )
