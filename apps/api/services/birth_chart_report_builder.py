"""
AstroOS — Birth Chart Foundation Report Builder (Module 20 / 21)

Compiles the comprehensive, Classical Vedic-grade 2-page A4 Birth Chart Foundation Reference
Sheet strictly from canonical D1/D9 calculation snapshots and shared engines.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import swisseph as swe

from apps.api.domain.horoscope import D1Chart
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.avastha_engine import AvasthaEngine
from apps.api.services.badhaka_maraka_engine import BadhakaMarakaEngine
from apps.api.services.chart_svg_renderer import render_north_indian_svg
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper, datetime_to_jd, jd_to_datetime
from apps.api.services.pinda_engine import PindaEngine
from apps.api.services.shadbala_engine import ShadbalaEngine
from apps.api.services.vimsopaka_engine import VimsopakaEngine
from packages.shared.enums import Rashi

# Nakshatras 27 list & lords
NAKSHATRAS = [
    ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"),
    ("Rohini", "Moon"), ("Mrigashira", "Mars"), ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"), ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"), ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"), ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"), ("Purva Ashadha", "Venus"), ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"), ("Dhanishta", "Mars"), ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"), ("Revati", "Mercury"),
]

RASHI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

RASHI_ABBR = [
    "Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"
]

TITHIS = [
    "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi",
    "Shukla Panchami", "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami",
    "Shukla Navami", "Shukla Dashami", "Shukla Ekadashi", "Shukla Dwadashi",
    "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima",
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi",
    "Krishna Panchami", "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami",
    "Krishna Navami", "Krishna Dashami", "Krishna Ekadashi", "Krishna Dwadashi",
    "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya",
]

YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Sobhana", "Atiganda",
    "Sukarma", "Dhriti", "Sula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha",
    "Shiva", "Siddha", "Sadhya", "Subha", "Sukla", "Brahma", "Indra", "Vaidhriti"
]

KARANAS = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti (Bhadra)",
    "Shakuni", "Chatushpada", "Naga", "Kintughna"
]

DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}

DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

# This report's "Time of Birth"/"Timezone"/sunrise/sunset fields are all
# labeled IST — consistent with the report's implicit India/New-Delhi-only
# scope (default place_name, fixed "IST (UTC +05:30)" timezone field).
# `birth_dt` itself is always UTC (the `birth_datetime_utc` param), so
# display-only fields need this offset applied; the underlying chart
# calculation is untouched — it already operates in UTC/JD throughout.
IST_OFFSET = timedelta(hours=5, minutes=30)


def format_dms(deg_float: float) -> str:
    """Format decimal degrees into DD° MM' SS.SS\""""
    deg_in_sign = deg_float % 30.0
    d = int(deg_in_sign)
    rem_m = (deg_in_sign - d) * 60.0
    m = int(rem_m)
    s = (rem_m - m) * 60.0
    return f"{d:02d}° {m:02d}' {int(s):02d}\""


def get_navamsha_rashi_idx(lon: float) -> int:
    """Calculates 0-indexed D9 Navamsha sign from sidereal longitude (0-360)."""
    rashi_idx = int(lon / 30.0) % 12
    deg_in_rashi = lon % 30.0
    nav_pada = int(deg_in_rashi / (30.0 / 9.0))  # 0..8
    
    element = rashi_idx % 4
    if element == 0:
        start = 0  # Aries
    elif element == 1:
        start = 9  # Capricorn
    elif element == 2:
        start = 6  # Libra
    else:
        start = 3  # Cancer
        
    return (start + nav_pada) % 12


class BirthChartReportBuilder:
    """
    Stateless compiler for the Birth Chart Foundation Report.
    Consumes canonical D1Chart, Ephemeris, Ashtakavarga, and Shadbala objects.
    """

    def __init__(self, wrapper: Optional[EphemerisWrapper] = None) -> None:
        self._wrapper = wrapper or EphemerisWrapper("data/ephemeris")
        self._ashtakavarga_engine = AshtakavargaEngine()
        self._avastha_engine = AvasthaEngine()
        self._vimsopaka_engine = VimsopakaEngine(ephemeris_wrapper=self._wrapper)
        self._pinda_engine = PindaEngine(self._ashtakavarga_engine)
        self._divisional_engine = DivisionalEngine(self._wrapper)
        self._shadbala_engine = ShadbalaEngine(
            divisional_engine=self._divisional_engine, ephemeris_wrapper=self._wrapper,
        )
        self._badhaka_maraka_engine = BadhakaMarakaEngine()
        # Vimshottari comes from the canonical engine — the builder must not
        # derive dasha periods itself (report tier spec, "Data Integrity").
        self._dasha_engine = DashaEngine(self._wrapper)

    def build_report_data(
        self,
        chart: D1Chart,
        subject_name: str = "Arjun Sharma",
        gender: str = "Male",
        birth_datetime_utc: Optional[datetime] = None,
        place_name: str = "New Delhi, India",
        latitude: float = 28.6139,
        longitude: float = 77.2090,
        ayanamsa_name: str = "Lahiri (CHITRAPAKSHA)",
        house_system_code: str = "Whole Sign",
        ayanamsa: str = "lahiri",
    ) -> dict[str, Any]:
        """
        Gathers all astronomical facts, matrices, and SVG diagrams into a structured dict
        for Jinja2 rendering.

        `ayanamsa` is the raw engine code (e.g. "lahiri") needed by
        VimsopakaEngine's divisional-chart computation — kept separate
        from `ayanamsa_name`, which is the display string already used
        throughout this report. `house_system_code` doubles as both:
        engines here accept single-letter codes ("W", "P", ...), so a
        multi-character display value falls back to whole-sign ("W").
        """
        birth_dt = birth_datetime_utc or datetime(1995, 1, 1, 12, 0, tzinfo=timezone.utc)
        house_system_raw = house_system_code if len(house_system_code) == 1 else "W"
        
        # ── 1. Lagna & Planets Computation ────────────────────────────────────
        asc_lon = chart.ascendant.sidereal_longitude
        asc_rashi_idx = int(asc_lon / 30.0) % 12
        asc_nav_idx = get_navamsha_rashi_idx(asc_lon)
        
        # Chara Karakas (7-karaka scheme: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn)
        classical_7 = [
            p for p in chart.planets
            if p.planet.capitalize() in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        ]
        # Sort by degree within sign descending
        sorted_karakas = sorted(classical_7, key=lambda p: p.rashi_degree, reverse=True)
        karaka_tags = ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]
        karaka_map = {
            sorted_karakas[i].planet.capitalize(): karaka_tags[i]
            for i in range(min(len(sorted_karakas), len(karaka_tags)))
        }

        # Planetary table items
        planet_rows = []
        d1_house_planets: dict[int, list[str]] = {h: [] for h in range(1, 13)}
        d9_house_planets: dict[int, list[str]] = {h: [] for h in range(1, 13)}

        # Add Lagna row
        nak_idx_asc = int(asc_lon / (360.0 / 27.0)) % 27
        pada_asc = int((asc_lon % (360.0 / 27.0)) / (360.0 / 108.0)) + 1
        planet_rows.append({
            "name": "Ascendant",
            "symbol": "♈",
            "karaka": "—",
            "rashi_name": RASHI_NAMES[asc_rashi_idx],
            "rashi_abbr": RASHI_ABBR[asc_rashi_idx],
            "degree_dms": format_dms(asc_lon),
            "nakshatra": NAKSHATRAS[nak_idx_asc][0],
            "pada": pada_asc,
            "navamsa_rashi": RASHI_NAMES[asc_nav_idx],
            "navamsa_abbr": RASHI_ABBR[asc_nav_idx],
            "house": 1,
            "dignity": "—",
            "is_retrograde": False,
            "retro_symbol": "",
            "is_combust": False,
        })
        d1_house_planets[1].append("As")
        d9_house_planets[1].append("As")

        # Process each planet
        moon_lon = 0.0
        sun_lon = 0.0

        planet_symbols = {
            "Sun": "☉", "Moon": "☽", "Mars": "♂", "Mercury": "☿",
            "Jupiter": "♃", "Venus": "♀", "Saturn": "♄", "Rahu": "☊", "Ketu": "☋"
        }

        for p in chart.planets:
            p_name = p.planet.capitalize()
            p_lon = p.sidereal_longitude
            if p_name == "Moon":
                moon_lon = p_lon
            elif p_name == "Sun":
                sun_lon = p_lon

            p_rashi_idx = int(p_lon / 30.0) % 12
            p_nav_idx = get_navamsha_rashi_idx(p_lon)
            nak_idx = int(p_lon / (360.0 / 27.0)) % 27
            pada = int((p_lon % (360.0 / 27.0)) / (360.0 / 108.0)) + 1
            
            # House relative to Lagna
            d1_house = ((p_rashi_idx - asc_rashi_idx + 12) % 12) + 1
            d9_house = ((p_nav_idx - asc_nav_idx + 12) % 12) + 1
            
            d1_house_planets[d1_house].append(p_name)
            d9_house_planets[d9_house].append(p_name)

            dignity_val = (p.dignity.value if p.dignity else "neutral").capitalize()
            if dignity_val.lower() == "moolatrikona":
                dignity_val = "Moolatrikona"
            elif dignity_val.lower() == "own":
                dignity_val = "Own Sign"
            elif dignity_val.lower() == "friendly":
                dignity_val = "Friend"

            planet_rows.append({
                "name": p_name,
                "symbol": planet_symbols.get(p_name, "●"),
                "karaka": karaka_map.get(p_name, "—"),
                "rashi_name": RASHI_NAMES[p_rashi_idx],
                "rashi_abbr": RASHI_ABBR[p_rashi_idx],
                "degree_dms": format_dms(p_lon),
                "nakshatra": NAKSHATRAS[nak_idx][0],
                "pada": pada,
                "navamsa_rashi": RASHI_NAMES[p_nav_idx],
                "navamsa_abbr": RASHI_ABBR[p_nav_idx],
                "house": d1_house,
                "dignity": dignity_val,
                "is_retrograde": getattr(p, "is_retrograde", False),
                "retro_symbol": "℞" if getattr(p, "is_retrograde", False) else "—",
                "is_combust": getattr(p, "is_combust", False),
            })

        # ── 2. Panchanga Calculations ─────────────────────────────────────────
        elongation = (moon_lon - sun_lon + 360.0) % 360.0
        tithi_idx = int(elongation / 12.0) % 30
        tithi_name = TITHIS[tithi_idx]
        tithi_left = (1.0 - ((elongation % 12.0) / 12.0)) * 100.0

        moon_nak_idx = int(moon_lon / (360.0 / 27.0)) % 27
        moon_nak_name = NAKSHATRAS[moon_nak_idx][0]
        moon_nak_left = (1.0 - ((moon_lon % (360.0 / 27.0)) / (360.0 / 27.0))) * 100.0

        yoga_deg = (sun_lon + moon_lon) % 360.0
        yoga_idx = int(yoga_deg / (360.0 / 27.0)) % 27
        yoga_name = YOGAS[yoga_idx]

        karana_idx = int(elongation / 6.0) % 60
        karana_name = KARANAS[karana_idx % len(KARANAS)]

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        vaara = days[birth_dt.weekday()]

        # Real Lahiri ayanamsa value and sunrise/sunset for this exact
        # birth moment/location, via EphemerisWrapper — replacing what were
        # previously fixed literal strings shown on every chart regardless
        # of birth date or place.
        birth_jd = datetime_to_jd(birth_dt)
        ayanamsa_deg = self._wrapper.get_ayanamsa(birth_jd)
        ayanamsa_value_str = format_dms(ayanamsa_deg)
        sunrise_jd, sunset_jd = self._wrapper.get_sunrise_sunset(birth_jd, latitude, longitude)
        sunrise_str = (jd_to_datetime(sunrise_jd) + IST_OFFSET).strftime("%H:%M:%S") if sunrise_jd else "N/A"
        sunset_str = (jd_to_datetime(sunset_jd) + IST_OFFSET).strftime("%H:%M:%S") if sunset_jd else "N/A"

        # ── 3. North Indian SVG Kundalis (Dimensions: 215 x 215) ──────────────
        d1_svg = render_north_indian_svg(
            ascendant_rashi_num=asc_rashi_idx + 1,
            planets_in_houses=d1_house_planets,
            chart_title="D1 Rasi Chart",
            width=210,
            height=210,
        )
        d9_svg = render_north_indian_svg(
            ascendant_rashi_num=asc_nav_idx + 1,
            planets_in_houses=d9_house_planets,
            chart_title="D9 Navamsha Chart",
            width=210,
            height=210,
        )

        # ── 4. Vimshottari Dasha Grid ─────────────────────────────────────────
        # Sourced from the canonical DashaEngine, NOT recomputed here.
        #
        # This block previously derived the whole Vimshottari tree inline. Its
        # first (partial) mahadasha used a fraction formula that let the
        # antardashas run far past the mahadasha's own end date — for an
        # 8 Aug 1912 chart the Mars mahadasha ended 1919 while its antardashas
        # ran to 2027. It also violated the report-tier rule that builders
        # assemble canonical output rather than recalculate it.
        dasha_tree = self._dasha_engine.compute_vimshottari(
            birth_datetime_utc=birth_dt,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            max_depth=2,          # mahadasha + antardasha
        )

        def _fmt(d) -> str:
            return d.strftime("%d %b %Y")

        def _span(days: int) -> str:
            years, rem = divmod(days, 365)
            months, day = divmod(rem, 30)
            return f"{years}Y {months}M {day}D"

        today = datetime.now(timezone.utc).date()
        dasha_timeline = []
        active_md_lord = ""
        active_md_range = ""
        active_antardashas: list[dict[str, Any]] = []

        for md in dasha_tree.mahadashas:
            antardashas = [
                {
                    "lord": ad.lord.capitalize(),
                    "start": _fmt(ad.start_date),
                    "end": _fmt(ad.end_date),
                    "duration": _span(ad.duration_days),
                }
                for ad in md.sub_periods
            ]
            dasha_timeline.append({
                "mahadasha": md.lord.capitalize(),
                "start": _fmt(md.start_date),
                "end": _fmt(md.end_date),
                "duration": _span(md.duration_days),
                "antardashas": antardashas,
            })

            # The mahadasha actually running now, by date — not a positional
            # guess. Falls back to the first period for charts whose whole
            # cycle is still in the future.
            if md.start_date <= today <= md.end_date:
                active_md_lord = md.lord.capitalize()
                active_md_range = f"{_fmt(md.start_date)} – {_fmt(md.end_date)}"
                # ALL antardasas of the running mahadasa — the report prints
                # the full sub-cycle as a table, and consumers that want only
                # the one in progress can filter on `is_current`.
                active_antardashas = [
                    {
                        "lord": a.lord.capitalize(),
                        "start": _fmt(a.start_date),
                        "end": _fmt(a.end_date),
                        "duration": _span(a.duration_days),
                        "is_current": a.start_date <= today <= a.end_date,
                    }
                    for a in md.sub_periods
                ]

        if not active_md_lord and dasha_timeline:
            first = dasha_timeline[0]
            active_md_lord = first["mahadasha"]
            active_md_range = f"{first['start']} – {first['end']}"
            active_antardashas = first["antardashas"]

        # ── 5. Ashtakavarga & SAV Full 12x7 Matrix ────────────────────────────
        # Real Bhinnashtakavarga per graha (order matches _CLASSICAL_SEVEN:
        # sun, moon, mars, mercury, jupiter, venus, saturn) summed into
        # Sarvashtakavarga — both from AshtakavargaEngine, not hardcoded.
        bhinna_results = self._ashtakavarga_engine.compute_bhinnashtakavarga(chart)
        bhinna_by_planet = {r.target_planet: r for r in bhinna_results}
        sarva = self._ashtakavarga_engine.compute_sarvashtakavarga(chart, bhinna_results)
        _AV_PLANET_ORDER = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        sav_rows = []
        for sign_idx, sign_name in enumerate(RASHI_NAMES):
            binds = [bhinna_by_planet[p].bindus_by_rashi[sign_idx] for p in _AV_PLANET_ORDER]
            sav_rows.append({
                "sign": sign_name,
                "bindus": binds,
                "total": sarva.bindus_by_rashi[sign_idx],
            })
        sav_planet_totals = [
            sum(bhinna_by_planet[p].bindus_by_rashi) for p in _AV_PLANET_ORDER
        ]
        sav_grand_total = sarva.total_bindus
        sign_totals = [row["total"] for row in sav_rows]
        sav_summary = {
            "total_bindu": sav_grand_total,
            "average_per_sign": round(sav_grand_total / 12.0, 2),
            "maximum": max(sign_totals),
            "minimum": min(sign_totals),
        }

        # ── 6. Planetary Avasthas ─────────────────────────────────────────────
        _AVASTHA_ELIGIBLE = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}
        avastha_results = self._avastha_engine.compute_all(
            [p for p in chart.planets if p.planet in _AVASTHA_ELIGIBLE]
        )
        avastha_rows = [
            {
                "planet": a.planet.capitalize(),
                "baladi": a.baladi_avastha,
                "deeptadi": a.deeptadi_avastha,
            }
            for a in avastha_results
        ]

        # ── 7. Shadbala Breakdown Matrix ────────────────────────────────────
        # Real per-planet totals from ShadbalaEngine, now that every
        # classical 6-fold component is implemented (see
        # not_yet_implemented_components() — empty since the Abda/Masa
        # Bala fix). Grand total = Sthana + Dig + Kala + Chesta +
        # Naisargika + Drik Bala, each summed to Rupas (Shashtiamsas/60).
        phase1 = self._shadbala_engine.compute_phase1_components(chart)  # naisargika, dig, drik
        phase2 = self._shadbala_engine.compute_phase2_components(chart)  # chesta, paksha, ayana, yuddha
        sthana = self._shadbala_engine.compute_sthana_bala_components(chart)  # uchcha, kendradi, drekkana
        saptavargaja = self._shadbala_engine.compute_saptavargaja_bala(
            chart, birth_datetime_utc=birth_dt, latitude=latitude, longitude=longitude,
            ayanamsa=ayanamsa, house_system=house_system_raw,
        )
        ojayugmarasyamsa = self._shadbala_engine.compute_ojayugmarasyamsa_bala(
            chart, birth_datetime_utc=birth_dt, latitude=latitude, longitude=longitude,
            ayanamsa=ayanamsa, house_system=house_system_raw,
        )
        tribhaga = self._shadbala_engine.compute_tribhaga_bala(chart, latitude=latitude, longitude=longitude)
        nathonnata = self._shadbala_engine.compute_nathonnata_bala(chart, latitude=latitude, longitude=longitude)
        dina_hora = self._shadbala_engine.compute_dina_hora_bala(chart, latitude=latitude, longitude=longitude)
        abda = self._shadbala_engine.compute_abda_bala(chart, birth_datetime_utc=birth_dt)
        masa = self._shadbala_engine.compute_masa_bala(chart, birth_datetime_utc=birth_dt)

        _SHASHTIAMSAS_PER_RUPA = 60.0
        _CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

        def _rupas_by_planet(*component_lists):
            totals = {p: 0.0 for p in _CLASSICAL_SEVEN}
            for results in component_lists:
                for r in results:
                    totals[r.planet] += r.value_shashtiamsas
            return {p: round(v / _SHASHTIAMSAS_PER_RUPA, 2) for p, v in totals.items()}

        sthana_rupas = _rupas_by_planet(
            sthana["uchcha_bala"], sthana["kendradi_bala"], sthana["drekkana_bala"],
            saptavargaja, ojayugmarasyamsa,
        )
        dig_rupas = _rupas_by_planet(phase1["dig_bala"])
        kala_rupas = _rupas_by_planet(
            phase2["paksha_bala"], phase2["ayana_bala"], phase2["yuddha_bala"],
            tribhaga, nathonnata, dina_hora, abda, masa,
        )
        chesta_rupas = _rupas_by_planet(phase2["chesta_bala"])
        naisargika_rupas = _rupas_by_planet(phase1["naisargika_bala"])
        drik_rupas = _rupas_by_planet(phase1["drik_bala"])

        shadbala_rows = []
        for p in _CLASSICAL_SEVEN:
            total = (
                sthana_rupas[p] + dig_rupas[p] + kala_rupas[p]
                + chesta_rupas[p] + naisargika_rupas[p] + drik_rupas[p]
            )
            shadbala_rows.append({
                "planet": p.capitalize(),
                "sthana": sthana_rupas[p],
                "dig": dig_rupas[p],
                "kala": kala_rupas[p],
                "chesta": chesta_rupas[p],
                "naisargika": naisargika_rupas[p],
                "drik": drik_rupas[p],
                "total": round(total, 2),
            })

        # ── 7b. Badhaka & Maraka Houses ──────────────────────────────────────
        badhaka_maraka = self._badhaka_maraka_engine.compute(chart)
        badhaka_maraka_data = {
            "badhaka_house": badhaka_maraka.badhaka_house,
            "badhaka_sign": badhaka_maraka.badhaka_sign.capitalize(),
            "badhaka_lord": badhaka_maraka.badhaka_lord.capitalize(),
            "maraka_houses": list(badhaka_maraka.maraka_houses),
            "maraka_signs": [s.capitalize() for s in badhaka_maraka.maraka_signs],
            "maraka_lords": [p.capitalize() for p in badhaka_maraka.maraka_lords],
        }

        # ── 8. Vimsopaka Bala (Shadvarga scheme) ────────────────────────────
        vimsopaka_result = self._vimsopaka_engine.compute_all(
            chart,
            birth_datetime_utc=birth_dt,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system_raw,
        )
        vimsopaka_rows = [
            {
                "planet": p.planet.capitalize(),
                "score": f"{p.shadvarga.vimsopaka_score:.2f}",
                "category": p.shadvarga.category,
            }
            for p in vimsopaka_result.planets
        ]

        # ── 9. Pindas ─────────────────────────────────────────────────────────
        # Real per-planet Rasi/Graha/Sodhya Pinda from PindaEngine, built on
        # the (now-fixed) Shodhita Ashtakavarga — cross-verified against
        # PyJHora byte-for-byte for this exact birth data. Previously this
        # was a single fixed "337/337/337/1011" constant shown on every
        # chart regardless of input.
        pinda_results = self._pinda_engine.compute(chart)
        pinda_rows = [
            {"planet": p.planet.capitalize(), "rasi": p.rasi_pinda, "graha": p.graha_pinda, "sodhya": p.sodhya_pinda}
            for p in pinda_results
        ]

        return {
            "subject_name": subject_name,
            "gender": gender,
            "birth_date": birth_dt.strftime("%d %b %Y"),
            "birth_time": (birth_dt + IST_OFFSET).strftime("%H:%M:%S (IST)"),
            "place": place_name,
            "birth_datetime_utc": birth_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "latitude": f"{latitude:.4f}° {'N' if latitude >= 0 else 'S'}",
            "longitude": f"{longitude:.4f}° {'E' if longitude >= 0 else 'W'}",
            "timezone": "IST (UTC +05:30)",
            "ayanamsa": ayanamsa_name,
            "ayanamsa_value": ayanamsa_value_str,
            "house_system": house_system_code,
            "calendar": "Gregorian",
            "ephemeris_version": "Swiss Ephemeris 2.10",
            "coordinate_system": "Sidereal",
            "chart_type": "Geocentric Tropical",
            "panchanga": {
                "tithi": f"{tithi_name} ({tithi_left:.1f}% left)",
                "nakshatra": f"{moon_nak_name} ({moon_nak_left:.1f}% left)",
                "yoga": yoga_name,
                "karana": karana_name,
                "vaara": vaara,
                "hora": "Sun Hora",
                "sunrise": sunrise_str,
                "sunset": sunset_str,
            },
            "planets": planet_rows,
            "d1_svg": d1_svg,
            "d9_svg": d9_svg,
            "dasha_timeline": dasha_timeline,
            "active_md_lord": active_md_lord,
            "active_md_range": active_md_range,
            "active_antardashas": active_antardashas,
            "sav_rows": sav_rows,
            "sav_data": {r["sign"]: r["total"] for r in sav_rows},
            "sav_planet_totals": sav_planet_totals,
            "sav_grand_total": sav_grand_total,
            "sav_summary": sav_summary,
            "avasthas": avastha_rows,
            "shadbala": shadbala_rows,
            "vimsopaka": vimsopaka_rows,
            "pindas": pinda_rows,
            "badhaka_maraka": badhaka_maraka_data,
        }

