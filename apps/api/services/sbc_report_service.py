"""
AstroOS — Sarvatobhadra Chakra (SBC) Report Service

Computes a full-grid SBC snapshot at a given moment: which 28-system
(Abhijit-aware) nakshatra each of the 9 grahas currently occupies, plus
(optionally) the Vedha result onto a specified Janma element, using
sbc_vedha_engine.SBCVedhaEngine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_rashi,
)
from apps.api.services.sbc_vedha_engine import (
    SBCPointVedhaSummary,
    SBCRawVedhaHit,
    SBCSynthesis,
    SBCTransitPlanet,
    SBCVedhaEngine,
    SBCVedhaHit,
    SBCVedhaResult,
    SBC_SANGYA_DEFINITIONS,
)
from apps.api.services.gati_classifier import classify_gati
from packages.shared.constants import DEGREES_PER_NAKSHATRA, DEGREES_PER_PADA
from packages.shared.sarvatobhadra_grid import longitude_to_sbc_nakshatra
from packages.shared.sbc_cellnum_table import NAKSHATRA_TO_CELLNUM, cellnum_for_nakshatra

PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]

SBC_28_NAKSHATRAS_ORDER = [
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra", "punarvasu",
    "pushya", "ashlesha", "magha", "purva_phalguni", "uttara_phalguni", "hasta",
    "chitra", "swati", "vishakha", "anuradha", "jyeshtha", "mula", "purva_ashadha",
    "uttara_ashadha", "abhijit", "shravana", "dhanishtha", "shatabhisha",
    "purva_bhadrapada", "uttara_bhadrapada", "revati"
]

NAKSHATRA_DISPLAY_NAMES: dict[str, str] = {
    "ashwini": "Ashwini", "bharani": "Bharani", "krittika": "Krittika", "rohini": "Rohini",
    "mrigashira": "Mrigashira", "ardra": "Ardra", "punarvasu": "Punarvasu", "pushya": "Pushya",
    "ashlesha": "Ashlesha", "magha": "Magha", "purva_phalguni": "Purva Phalguni",
    "uttara_phalguni": "Uttara Phalguni", "hasta": "Hasta", "chitra": "Chitra",
    "swati": "Swati", "vishakha": "Vishakha", "anuradha": "Anuradha", "jyeshtha": "Jyeshtha",
    "mula": "Mula", "purva_ashadha": "Purva Ashadha", "uttara_ashadha": "Uttara Ashadha",
    "abhijit": "Abhijit", "shravana": "Shravana", "dhanishtha": "Dhanishtha",
    "shatabhisha": "Shatabhisha", "purva_bhadrapada": "Purva Bhadrapada",
    "uttara_bhadrapada": "Uttara Bhadrapada", "revati": "Revati"
}

RASHI_DISPLAY_NAMES: dict[str, tuple[str, str]] = {
    "aries": ("Mesha", "♈"), "taurus": ("Vrishabha", "♉"), "gemini": ("Mithuna", "♊"),
    "cancer": ("Karka", "♋"), "leo": ("Simha", "♌"), "virgo": ("Kanya", "♍"),
    "libra": ("Tula", "♎"), "scorpio": ("Vrishchika", "♏"), "sagittarius": ("Dhanu", "♐"),
    "capricorn": ("Makara", "♑"), "aquarius": ("Kumbha", "♒"), "pisces": ("Meena", "♓")
}

VARA_NAMES: list[tuple[str, str]] = [
    ("Monday", "Moon"), ("Tuesday", "Mars"), ("Wednesday", "Mercury"),
    ("Thursday", "Jupiter"), ("Friday", "Venus"), ("Saturday", "Saturn"), ("Sunday", "Sun")
]

TITHI_GROUPS: dict[int, tuple[str, str]] = {
    1: ("Nanda", "1, 6, 11"), 2: ("Bhadra", "2, 7, 12"), 3: ("Jaya", "3, 8, 13"),
    4: ("Rikta", "4, 9, 14"), 5: ("Purna", "5, 10, 15/30"),
}

NAMA_AKSHARAS: dict[str, list[str]] = {
    "ashwini": ["Chu", "Che", "Cho", "La"], "bharani": ["Lee", "Lu", "Le", "Lo"],
    "krittika": ["A", "Ee", "U", "Ea"], "rohini": ["O", "Va", "Vee", "Vu"],
    "mrigashira": ["Ve", "Vo", "Ka", "Kee"], "ardra": ["Ku", "Gha", "Nga", "Chha"],
    "punarvasu": ["Ke", "Ko", "Ha", "Hee"], "pushya": ["Hu", "He", "Ho", "Da"],
    "ashlesha": ["Dee", "Du", "De", "Do"], "magha": ["Ma", "Mee", "Mu", "Me"],
    "purva_phalguni": ["Mo", "Ta", "Tee", "Tu"], "uttara_phalguni": ["Te", "To", "Pa", "Pee"],
    "hasta": ["Pu", "Sha", "Na", "Tha"], "chitra": ["Pe", "Po", "Ra", "Ree"],
    "swati": ["Ru", "Re", "Ro", "Ta"], "vishakha": ["Tee", "Tue", "Teae", "Too"],
    "anuradha": ["Na", "Nee", "Nu", "Ne"], "jyeshtha": ["No", "Ya", "Yee", "Yu"],
    "mula": ["Ye", "Yo", "Bha", "Bhee"], "purva_ashadha": ["Bhu", "Dha", "Bha", "Dha"],
    "uttara_ashadha": ["Bhe", "Bho", "Ja", "Jee"], "abhijit": ["Ju", "Je", "Jo", "Kha"],
    "shravana": ["Khee", "Khu", "Khe", "Kho"], "dhanishtha": ["Ga", "Gee", "Gu", "Ge"],
    "shatabhisha": ["Go", "Sa", "See", "Su"], "purva_bhadrapada": ["Se", "So", "Da", "Dee"],
    "uttara_bhadrapada": ["Du", "Tha", "Jha", "Da"], "revati": ["De", "Do", "Chaa", "Chee"],
}


def _get_tithi_info(tithi_num: int) -> tuple[str, str]:
    paksha = "Shukla" if tithi_num <= 15 else "Krishna"
    t_idx = ((tithi_num - 1) % 15) + 1
    tithi_names = [
        "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
        "Shasthi", "Saptami", "Ashtami", "Navami", "Dashami",
        "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima" if paksha == "Shukla" else "Amavasya"
    ]
    name = f"{paksha} {tithi_names[t_idx - 1]}"
    group_num = ((t_idx - 1) % 5) + 1
    group_name = TITHI_GROUPS[group_num][0]
    return name, group_name


@dataclass
class SBCGridPlanetPosition:
    planet: str
    nakshatra: str
    pada: int
    cellnum: int
    rashi: str
    rashi_degree: float
    is_retrograde: bool
    is_combust: bool
    speed_deg_per_day: float
    motion: str
    ray_direction: str


@dataclass
class SBCNatalAttributes:
    nama_akshara: str
    janma_rashi: str
    janma_rashi_icon: str
    tithi_name: str
    tithi_group: str
    tithi_number: int
    vara_name: str
    vara_lord: str


@dataclass
class SBCReport:

    moment_utc: datetime
    tithi_number: int
    positions: list[SBCGridPlanetPosition]
    janma_nakshatra: Optional[str]
    natal_attributes: Optional[SBCNatalAttributes]
    sensitive_points: list[SBCPointVedhaSummary]
    benefic_vedhas: list[SBCVedhaHit]
    malefic_vedhas: list[SBCVedhaHit]
    raw_hits: list[SBCRawVedhaHit]
    convention_used: str
    total_benefic_score: float
    total_malefic_score: float
    vedha_result: Optional[SBCVedhaResult]
    synthesis: Optional[SBCSynthesis] = None


class SBCReportService:
    def __init__(self, wrapper: EphemerisWrapper, vedha_engine: SBCVedhaEngine | None = None) -> None:
        self._wrapper = wrapper
        self._vedha_engine = vedha_engine or SBCVedhaEngine()

    def build_report(
        self,
        moment_utc: datetime,
        janma_nakshatra: Optional[str] = None,
        birth_datetime_utc: Optional[datetime] = None,
        birth_latitude: Optional[float] = None,
        birth_longitude: Optional[float] = None,
        ayanamsa: Optional[str] = "lahiri",
    ) -> SBCReport:
        jd_transit = datetime_to_jd(moment_utc)
        ayanamsa_transit = self._wrapper.get_ayanamsa(jd_transit)

        effective_janma = janma_nakshatra or "rohini"
        natal_attr: Optional[SBCNatalAttributes] = None

        if birth_datetime_utc is not None:
            jd_birth = datetime_to_jd(birth_datetime_utc)
            ayanamsa_birth = self._wrapper.get_ayanamsa(jd_birth)
            natal_moon_trop = self._wrapper.get_planet_position("moon", jd_birth)
            natal_moon_sid = self._wrapper.to_sidereal(natal_moon_trop.longitude, ayanamsa_birth)
            natal_sun_trop = self._wrapper.get_planet_position("sun", jd_birth)
            natal_sun_sid = self._wrapper.to_sidereal(natal_sun_trop.longitude, ayanamsa_birth)
            effective_janma = longitude_to_sbc_nakshatra(natal_moon_sid)
            natal_rashi_token, _ = longitude_to_rashi(natal_moon_sid)
            natal_tithi_res = self._wrapper.get_tithi(natal_moon_sid, natal_sun_sid)
            rem_deg = natal_moon_sid % DEGREES_PER_NAKSHATRA
            natal_pada = max(1, min(4, int(rem_deg / DEGREES_PER_PADA) + 1))
            r_name, r_icon = RASHI_DISPLAY_NAMES.get(natal_rashi_token, (natal_rashi_token.capitalize(), "♈"))
            t_name, t_group = _get_tithi_info(natal_tithi_res.number)
            v_name, v_lord = VARA_NAMES[birth_datetime_utc.weekday()]
            syllables = NAMA_AKSHARAS.get(effective_janma, ["A", "Ba", "Ca", "Da"])
            nama_syl = syllables[natal_pada - 1] if natal_pada <= len(syllables) else syllables[0]
            natal_attr = SBCNatalAttributes(
                nama_akshara=nama_syl,
                janma_rashi=r_name,
                janma_rashi_icon=r_icon,
                tithi_name=t_name,
                tithi_group=t_group,
                tithi_number=natal_tithi_res.number,
                vara_name=v_name,
                vara_lord=v_lord,
            )
        else:
            syllables = NAMA_AKSHARAS.get(effective_janma, ["A", "Ba", "Ca", "Da"])
            natal_attr = SBCNatalAttributes(
                nama_akshara=syllables[0],
                janma_rashi="Vrishabha",
                janma_rashi_icon="♉",
                tithi_name="Shukla Panchami",
                tithi_group="Purna",
                tithi_number=5,
                vara_name="Friday",
                vara_lord="Venus",
            )

        janma_idx = SBC_28_NAKSHATRAS_ORDER.index(effective_janma) if effective_janma in SBC_28_NAKSHATRAS_ORDER else 0
        sangya_offsets = SBC_SANGYA_DEFINITIONS["narapati_jayacharya"]["offsets"]
        sensitive_points_map = []
        for key, name, offset_1based in sangya_offsets:
            offset_0based = offset_1based - 1
            target_n_token = SBC_28_NAKSHATRAS_ORDER[(janma_idx + offset_0based) % 28]
            sensitive_points_map.append({
                "key": key,
                "name": name,
                "nakshatra_token": target_n_token,
                "nakshatra_name": NAKSHATRA_DISPLAY_NAMES.get(target_n_token, target_n_token.capitalize()),
                "nakshatra_number": SBC_28_NAKSHATRAS_ORDER.index(target_n_token) + 1,
                "cellnum": cellnum_for_nakshatra(target_n_token),
            })

        sun_trop = self._wrapper.get_planet_position("sun", jd_transit)
        sun_sid = self._wrapper.to_sidereal(sun_trop.longitude, ayanamsa_transit)
        moon_trop = self._wrapper.get_planet_position("moon", jd_transit)
        moon_sid = self._wrapper.to_sidereal(moon_trop.longitude, ayanamsa_transit)
        positions: list[SBCGridPlanetPosition] = []
        transit_planets: list[SBCTransitPlanet] = []
        for planet in PLANETS:
            tropical = sun_trop if planet == "sun" else (moon_trop if planet == "moon" else self._wrapper.get_planet_position(planet, jd_transit))
            sidereal_lon = sun_sid if planet == "sun" else (moon_sid if planet == "moon" else self._wrapper.to_sidereal(tropical.longitude, ayanamsa_transit))
            nakshatra_sbc = longitude_to_sbc_nakshatra(sidereal_lon)
            rashi, rashi_degree = longitude_to_rashi(sidereal_lon)
            is_combust = self._wrapper.is_combust(planet, sidereal_lon, sun_sid)[0] if planet not in ("sun", "rahu", "ketu") else False
            rem_deg = sidereal_lon % DEGREES_PER_NAKSHATRA
            pada = max(1, min(4, int(rem_deg / DEGREES_PER_PADA) + 1))
            if planet == "moon":
                motion_str, ray_dir = "Normal", "All 3"
            elif tropical.is_retrograde:
                motion_str, ray_dir = "Retrograde", "Right"
            else:
                gati = classify_gati(planet, tropical.speed_deg_per_day, False)
                motion_str = "Fast" if gati in ("chara", "atichara") else ("Stationary" if gati in ("manda", "atimanda") else "Normal")
                ray_dir = "Left" if gati in ("chara", "atichara") else "Front"
            positions.append(SBCGridPlanetPosition(planet, nakshatra_sbc, pada, NAKSHATRA_TO_CELLNUM[nakshatra_sbc], rashi, rashi_degree, tropical.is_retrograde, is_combust, tropical.speed_deg_per_day, motion_str, ray_dir))
        tithi_info = self._wrapper.get_tithi(moon_sid, sun_sid)
        for pos in positions:
            transit_planets.append(SBCTransitPlanet(pos.planet, pos.nakshatra, pos.rashi, pos.rashi_degree, pos.speed_deg_per_day, pos.is_retrograde, pos.is_combust, tithi_info.number if pos.planet == "moon" else None))
        analysis = self._vedha_engine.evaluate_full(sensitive_points_map, transit_planets, janma_nakshatra=effective_janma)
        return SBCReport(moment_utc, tithi_info.number, positions, effective_janma, natal_attr, analysis.sensitive_points, analysis.benefic_vedhas, analysis.malefic_vedhas, analysis.raw_hits, analysis.convention_used, analysis.total_benefic_score, analysis.total_malefic_score, analysis.legacy_result, analysis.synthesis)

