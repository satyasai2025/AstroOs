"""
AstroOS — Sarvatobhadra Chakra (SBC) Vedha Engine

Evaluates Vedha hits from transiting planets onto natal/Janma
elements and Sangyas using classical Sarvatobhadra Chakra ray paths.

Conventions and Rules:
- Documented Sangya definitions: Janma (1st), Karma (10th), Sanghatika (16th),
  Samudayika (18th), Adhana (19th), Vainashika (22nd), Manasa (25th),
  Jati (26th), Desha (27th), Abhisheka (28th) [Narapatijayacharya Svarodaya / Phaladeepika].
- Configurable ray direction mapping: Direct/Normal -> Front, Fast/Atichara -> Left,
  Retrograde/Vakra -> Right, Moon -> All 3 directions.
- Raw strength factors reported without arbitrary multipliers.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any

from packages.shared.dignity import compute_dignity_value
from packages.shared.sbc_cellnum_table import cellnum_for_nakshatra, vedha_path
from apps.api.services.gati_classifier import classify_gati

# ── Documented Conventions & Life Areas ───────────────────────────────────────

SANGYA_LIFE_AREAS: dict[str, dict[str, Any]] = {
    "janma": {
        "name": "Janma",
        "domain": "General well-being, physical body and vitality",
        "offset": 1,
    },
    "karma": {
        "name": "Karma",
        "domain": "Work, status, career action and professional authority",
        "offset": 10,
    },
    "sanghatika": {
        "name": "Sanghatika",
        "domain": "Loss of wealth, mental stress, conflict with associates and partnerships",
        "offset": 16,
    },
    "samudayika": {
        "name": "Samudayika",
        "domain": "Overall social and collective financial stability",
        "offset": 18,
    },
    "adhana": {
        "name": "Adhana",
        "domain": "Career foundation, residence change, root stability and core base",
        "offset": 19,
    },
    "vainashika": {
        "name": "Vainashika",
        "domain": "Ruin, loss of capital, complete breakdown and severe vulnerability",
        "offset": 22,
    },
    "manasa": {
        "name": "Manasa",
        "domain": "Mental state, anxiety, psychological peace and decision clarity",
        "offset": 25,
    },
    "jati": {
        "name": "Jati",
        "domain": "Health, family lineage, community standing and physical vitality",
        "offset": 26,
    },
    "desha": {
        "name": "Desha",
        "domain": "Travel, property, relocation, external environment and foreign relations",
        "offset": 27,
    },
    "abhisheka": {
        "name": "Abhisheka",
        "domain": "Rise, honor, promotion, royal protection and triumphant success",
        "offset": 28,
    },
}

GRAHA_VEDHA_RULES: dict[str, dict[str, str]] = {
    "sun": {
        "nature": "malefic",
        "impact": "Physical stress, fever/vitality drops, ego clashes, government/authority friction, and disputes regarding family or parental affairs.",
        "keywords": "Ego friction, authority pressure, physical fatigue",
    },
    "mars": {
        "nature": "malefic",
        "impact": "Sudden conflict, financial loss, blood pressure/pitta flare-ups, accidents, and aggressive disputes with partners/associates.",
        "keywords": "Sudden conflict, financial loss, aggressive dispute",
    },
    "saturn": {
        "nature": "malefic",
        "impact": "Prolonged delays, exhaustion, grief, obstruction in duties, chronic stagnation, and heavy burden on resources.",
        "keywords": "Chronic delays, stagnation, heavy responsibility",
    },
    "rahu": {
        "nature": "malefic",
        "impact": "Unseen fear, illusion, instability in career foundation, deception, and confusion regarding residence or core base.",
        "keywords": "Unseen anxiety, deception risk, base instability",
    },
    "ketu": {
        "nature": "malefic",
        "impact": "Sudden disruption, detachment, unexpected setbacks, misdiagnosis/ailments, and confusion in relationships.",
        "keywords": "Sudden disruption, detachment, unexpected setbacks",
    },
    "jupiter": {
        "nature": "benefic",
        "impact": "Divine grace, wise counsel, wealth expansion, auspicious protection, recovery from ailments, and honor.",
        "keywords": "Auspicious growth, wisdom, divine protection",
    },
    "venus": {
        "nature": "benefic",
        "impact": "Harmonious support, material comforts, financial gains, relationship ease, luxury, and artistic fulfillment.",
        "keywords": "Material comfort, financial gain, relationship harmony",
    },
    "moon": {
        "nature": "benefic",
        "impact": "Protective armor (Shield), emotional upliftment, mental serenity, victory over opponents, and unexpected comforts/support.",
        "keywords": "Protective shield, emotional uplift, peace",
    },
    "mercury": {
        "nature": "benefic",
        "impact": "Intellectual clarity, successful negotiations, commercial profits, smooth communication, and diplomatic success.",
        "keywords": "Intellectual clarity, profitable trade, smooth deals",
    },
}

SBC_SANGYA_DEFINITIONS: dict[str, dict[str, Any]] = {
    "narapati_jayacharya": {
        "description": "Classical 10 Sangyas from Narapatijayacharya Svarodaya / Phaladeepika",
        "offsets": [
            ("janma", "Janma", 1),
            ("karma", "Karma", 10),
            ("sanghatika", "Sanghatika", 16),
            ("samudayika", "Samudayika", 18),
            ("adhana", "Adhana", 19),
            ("vainashika", "Vainashika", 22),
            ("manasa", "Manasa", 25),
            ("jati", "Jati", 26),
            ("desha", "Desha", 27),
            ("abhisheka", "Abhisheka", 28),
        ],
    }
}

VEDHA_CONVENTIONS: dict[str, dict[str, Any]] = {
    "narapati_jayacharya": {
        "description": "Motion-to-Ray mapping from Narapatijayacharya / Classical SBC",
        "retrograde": "right",
        "fast": "left",
        "normal": "front",
        "moon": "all",
    }
}

_ALWAYS_BENEFIC = {"jupiter", "venus"}
_NEVER_BENEFIC = {"sun", "mars", "saturn", "rahu", "ketu"}


@dataclass
class SBCTransitPlanet:
    planet: str
    nakshatra: str
    rashi: str
    rashi_degree: float
    speed_deg_per_day: float
    is_retrograde: bool
    is_combust: bool
    tithi: Optional[int] = None


@dataclass
class SBCRawVedhaHit:
    planet: str
    direction: str
    from_nakshatra: str
    target_type: str
    target_key: str
    target_name: str
    nature: str
    strength_factors: dict[str, Any]
    source_convention: str = "narapati_jayacharya"


@dataclass
class SBCVedhaHit:
    planet: str
    direction: str
    from_nakshatra: str
    score: float = 0.0
    nature: str = "benefic"
    target_points: list[str] = field(default_factory=list)
    strength_factors: dict[str, Any] = field(default_factory=dict)


@dataclass
class SBCRiskItem:
    sangya_key: str
    sangya_name: str
    sangya_offset: int
    nakshatra_name: str
    transiting_planet: str
    transiting_nakshatra: str
    aspect_ray: str
    domain: str
    impact: str


@dataclass
class SBCProtectionItem:
    sangya_key: str
    sangya_name: str
    sangya_offset: int
    nakshatra_name: str
    transiting_planet: str
    transiting_nakshatra: str
    aspect_ray: str
    domain: str
    impact: str


@dataclass
class SBCSynthesis:
    high_risk_areas: list[SBCRiskItem]
    protective_shields: list[SBCProtectionItem]
    executive_summary: str
    saving_grace: str
    practical_advice: list[str]


@dataclass
class SBCVedhaResult:
    hits: list[SBCVedhaHit]
    total_score: float = 0.0
    zeroed_by_malefic_conjunction: bool = False


@dataclass
class SBCPointVedhaSummary:
    key: str
    name: str
    nakshatra_number: int
    nakshatra_token: str
    nakshatra_name: str
    status: str
    vedhas_received: list[str]
    benefic_hits: list[str]
    malefic_hits: list[str]


@dataclass
class SBCFullVedhaAnalysis:
    benefic_vedhas: list[SBCVedhaHit]
    malefic_vedhas: list[SBCVedhaHit]
    sensitive_points: list[SBCPointVedhaSummary]
    raw_hits: list[SBCRawVedhaHit]
    synthesis: SBCSynthesis
    total_benefic_score: float = 0.0
    total_malefic_score: float = 0.0
    legacy_result: Optional[SBCVedhaResult] = None
    convention_used: str = "narapati_jayacharya"


def _is_benefic_caster(planet: SBCTransitPlanet, all_planets: list[SBCTransitPlanet]) -> bool:
    if planet.planet in _ALWAYS_BENEFIC:
        return True
    if planet.planet in _NEVER_BENEFIC:
        return False
    if planet.planet == "moon":
        return planet.tithi is not None and 6 <= planet.tithi <= 20
    if planet.planet == "mercury":
        malefics_here = {
            p.planet
            for p in all_planets
            if p.planet in _NEVER_BENEFIC and p.nakshatra == planet.nakshatra
        }
        return not bool(malefics_here)
    return False


def _direction_for(planet: SBCTransitPlanet, convention: str = "narapati_jayacharya") -> str:
    rules = VEDHA_CONVENTIONS.get(convention, VEDHA_CONVENTIONS["narapati_jayacharya"])
    if planet.planet == "moon":
        return rules["moon"]
    if planet.is_retrograde:
        return rules["retrograde"]
    gati = classify_gati(planet.planet, planet.speed_deg_per_day, planet.is_retrograde)
    if gati in ("chara", "atichara"):
        return rules["fast"]
    return rules["normal"]


def _get_strength_factors(planet: SBCTransitPlanet, all_planets: list[SBCTransitPlanet]) -> dict[str, Any]:
    dignity = compute_dignity_value(planet.planet, planet.rashi, planet.rashi_degree) or "neutral"
    gati = classify_gati(planet.planet, planet.speed_deg_per_day, planet.is_retrograde)
    conjunctions = [p.planet for p in all_planets if p.planet != planet.planet and p.nakshatra == planet.nakshatra]
    paksha_bala = None
    if planet.planet == "moon" and planet.tithi is not None:
        paksha_bala = "shukla_paksha" if 1 <= planet.tithi <= 15 else "krishna_paksha"
    return {
        "is_retrograde": planet.is_retrograde,
        "is_combust": planet.is_combust,
        "speed_deg_day": round(planet.speed_deg_per_day, 4),
        "gati": gati,
        "dignity": dignity,
        "paksha_bala": paksha_bala,
        "conjunctions": conjunctions,
    }


class SBCVedhaEngine:
    def __init__(self, convention: str = "narapati_jayacharya"):
        self.convention = convention

    def check(
        self,
        janma_nakshatra: str,
        transiting_planets: list[SBCTransitPlanet],
    ) -> SBCVedhaResult:
        return self.check_cellnum(cellnum_for_nakshatra(janma_nakshatra), transiting_planets)

    def check_cellnum(
        self,
        janma_cellnum: int,
        transiting_planets: list[SBCTransitPlanet],
    ) -> SBCVedhaResult:
        hits: list[SBCVedhaHit] = []

        for planet in transiting_planets:
            if not _is_benefic_caster(planet, transiting_planets):
                continue

            direction = _direction_for(planet, self.convention)
            directions = ("front", "left", "right") if direction == "all" else (direction,)

            for d in directions:
                path = vedha_path(planet.nakshatra, d)
                if janma_cellnum in path:
                    strength = _get_strength_factors(planet, transiting_planets)
                    hits.append(
                        SBCVedhaHit(
                            planet=planet.planet,
                            direction=d,
                            from_nakshatra=planet.nakshatra,
                            score=1.0 if not planet.is_combust else 0.0,
                            nature="benefic",
                            strength_factors=strength,
                        )
                    )
                    break

        zeroed = False
        for hit in hits:
            caster = next(p for p in transiting_planets if p.planet == hit.planet)
            same_cell_malefics = [
                p
                for p in transiting_planets
                if p.planet in _NEVER_BENEFIC and p.nakshatra == caster.nakshatra
            ]
            if same_cell_malefics:
                zeroed = True
                break

        total = 0.0 if zeroed else sum(h.score for h in hits)
        return SBCVedhaResult(hits=hits, total_score=total, zeroed_by_malefic_conjunction=zeroed)

    def evaluate_full(
        self,
        sensitive_points_map: list[dict[str, Any]],
        transiting_planets: list[SBCTransitPlanet],
        janma_nakshatra: Optional[str] = None,
    ) -> SBCFullVedhaAnalysis:
        legacy_res = (
            self.check(janma_nakshatra, transiting_planets)
            if janma_nakshatra
            else SBCVedhaResult(hits=[], total_score=0.0, zeroed_by_malefic_conjunction=False)
        )

        benefic_entries: list[SBCVedhaHit] = []
        malefic_entries: list[SBCVedhaHit] = []
        raw_hits: list[SBCRawVedhaHit] = []

        point_benefic_hits: dict[str, list[str]] = {p["key"]: [] for p in sensitive_points_map}
        point_malefic_hits: dict[str, list[str]] = {p["key"]: [] for p in sensitive_points_map}
        point_all_vedhas: dict[str, list[str]] = {p["key"]: [] for p in sensitive_points_map}

        cellnum_to_points: dict[int, list[dict[str, Any]]] = {}
        for pt in sensitive_points_map:
            cnum = pt.get("cellnum")
            if cnum:
                cellnum_to_points.setdefault(cnum, []).append(pt)

        for planet in transiting_planets:
            is_ben = _is_benefic_caster(planet, transiting_planets)
            nature = "benefic" if is_ben else "malefic"
            direction = _direction_for(planet, self.convention)
            directions = ("front", "left", "right") if direction == "all" else (direction,)
            strength = _get_strength_factors(planet, transiting_planets)

            target_point_names: list[str] = []

            for d in directions:
                path = vedha_path(planet.nakshatra, d)
                for cellnum in path:
                    if cellnum in cellnum_to_points:
                        for pt in cellnum_to_points[cellnum]:
                            pt_name = pt["name"]
                            pt_key = pt["key"]
                            hit_str = f"{planet.planet.capitalize()} ({d.capitalize()})"

                            if hit_str not in point_all_vedhas[pt_key]:
                                point_all_vedhas[pt_key].append(hit_str)

                            raw_hits.append(
                                SBCRawVedhaHit(
                                    planet=planet.planet,
                                    direction=d,
                                    from_nakshatra=planet.nakshatra,
                                    target_type="sangya",
                                    target_key=pt_key,
                                    target_name=pt_name,
                                    nature=nature,
                                    strength_factors=strength,
                                    source_convention=self.convention,
                                )
                            )

                            if is_ben:
                                if hit_str not in point_benefic_hits[pt_key]:
                                    point_benefic_hits[pt_key].append(hit_str)
                            else:
                                if hit_str not in point_malefic_hits[pt_key]:
                                    point_malefic_hits[pt_key].append(hit_str)

                            if pt_name not in target_point_names:
                                target_point_names.append(pt_name)

            if target_point_names:
                dir_label = "All 3" if direction == "all" else direction.capitalize()
                entry = SBCVedhaHit(
                    planet=planet.planet,
                    direction=dir_label,
                    from_nakshatra=planet.nakshatra,
                    score=1.0 if not planet.is_combust else 0.0,
                    nature=nature,
                    target_points=target_point_names,
                    strength_factors=strength,
                )
                if is_ben:
                    benefic_entries.append(entry)
                else:
                    malefic_entries.append(entry)

        summaries: list[SBCPointVedhaSummary] = []
        for pt in sensitive_points_map:
            k = pt["key"]
            b_hits = point_benefic_hits[k]
            m_hits = point_malefic_hits[k]
            all_v = point_all_vedhas[k]

            if b_hits and not m_hits:
                status = "activated"
            elif m_hits and not b_hits:
                status = "afflicted"
            elif b_hits and m_hits:
                status = "mixed"
            else:
                status = "neutral"

            summaries.append(
                SBCPointVedhaSummary(
                    key=k,
                    name=pt["name"],
                    nakshatra_number=pt.get("nakshatra_number", 1),
                    nakshatra_token=pt.get("nakshatra_token", ""),
                    nakshatra_name=pt.get("nakshatra_name", ""),
                    status=status,
                    vedhas_received=all_v,
                    benefic_hits=b_hits,
                    malefic_hits=m_hits,
                )
            )

        synthesis = _build_sbc_synthesis(raw_hits, sensitive_points_map)

        return SBCFullVedhaAnalysis(
            benefic_vedhas=benefic_entries,
            malefic_vedhas=malefic_entries,
            sensitive_points=summaries,
            raw_hits=raw_hits,
            synthesis=synthesis,
            total_benefic_score=float(len(benefic_entries)),
            total_malefic_score=float(len(malefic_entries)),
            legacy_result=legacy_res,
            convention_used=self.convention,
        )


def _build_sbc_synthesis(
    raw_hits: list[SBCRawVedhaHit],
    sensitive_points_map: list[dict[str, Any]],
) -> SBCSynthesis:
    point_meta = {p["key"]: p for p in sensitive_points_map}
    high_risks: list[SBCRiskItem] = []
    protective_shields: list[SBCProtectionItem] = []

    seen_risk: set[tuple[str, str, str]] = set()
    seen_prot: set[tuple[str, str, str]] = set()

    for h in raw_hits:
        if h.target_type != "sangya":
            continue
        sangya_key = h.target_key
        sangya_info = SANGYA_LIFE_AREAS.get(sangya_key, {})
        graha_info = GRAHA_VEDHA_RULES.get(h.planet.lower(), {})
        pt_nak = point_meta.get(sangya_key, {}).get("nakshatra_name", "")
        offset = sangya_info.get("offset", point_meta.get(sangya_key, {}).get("offset", 1))
        domain = sangya_info.get("domain", "Sensitive life domain")
        impact_text = f"{h.planet.capitalize()} Vedha Impact: {graha_info.get('impact', '')}"

        sig = (sangya_key, h.planet.lower(), h.direction)
        if h.nature == "malefic":
            if sig not in seen_risk:
                seen_risk.add(sig)
                high_risks.append(
                    SBCRiskItem(
                        sangya_key=sangya_key,
                        sangya_name=h.target_name,
                        sangya_offset=offset,
                        nakshatra_name=pt_nak,
                        transiting_planet=h.planet.capitalize(),
                        transiting_nakshatra=h.from_nakshatra.replace("_", " ").title(),
                        aspect_ray="All 3" if h.direction == "all" else h.direction.capitalize(),
                        domain=domain,
                        impact=impact_text,
                    )
                )
        else:
            if sig not in seen_prot:
                seen_prot.add(sig)
                protective_shields.append(
                    SBCProtectionItem(
                        sangya_key=sangya_key,
                        sangya_name=h.target_name,
                        sangya_offset=offset,
                        nakshatra_name=pt_nak,
                        transiting_planet=h.planet.capitalize(),
                        transiting_nakshatra=h.from_nakshatra.replace("_", " ").title(),
                        aspect_ray="All 3" if h.direction == "all" else h.direction.capitalize(),
                        domain=domain,
                        impact=impact_text,
                    )
                )

    if high_risks:
        risk_names = ", ".join(f"{r.sangya_name} ({r.transiting_planet})" for r in high_risks[:3])
        exec_summary = (
            f"High Risk Area: {risk_names} under malefic Vedha. "
            "Caution advised in decision-making, aggressive investments, and physical stress."
        )
    else:
        exec_summary = "No major malefic Vedha afflictions on key Sangyas. General stability prevails."

    if protective_shields:
        prot_names = ", ".join(f"{p.sangya_name} ({p.transiting_planet})" for p in protective_shields[:3])
        saving_grace = (
            f"Saving Grace: {prot_names} receives auspicious Shubha Vedha shield, "
            "providing resilience, reputation protection, and ultimate recovery against disruptions."
        )
    else:
        saving_grace = "Neutral protective shielding; rely on foundational strength and conscious prudence."

    practical_advice: list[str] = []
    afflicted_keys = {r.sangya_key for r in high_risks}
    if "sanghatika" in afflicted_keys:
        practical_advice.append("Postpone large speculative outlays and verify partnership commitments.")
    if "jati" in afflicted_keys or "janma" in afflicted_keys:
        practical_advice.append("Prioritize physical vitality, avoid ego friction, and ensure adequate rest.")
    if "manasa" in afflicted_keys:
        practical_advice.append("Practice calming routines to alleviate psychological anxiety and indecisiveness.")
    if "adhana" in afflicted_keys:
        practical_advice.append("Double-check career foundations, contract fine-print, and residence plans.")
    if "vainashika" in afflicted_keys:
        practical_advice.append("Exercise extreme risk management and avoid unhedged capital exposures.")
    if not practical_advice:
        practical_advice.append("Maintain standard daily discipline and leverage benefic transit windows.")

    return SBCSynthesis(
        high_risk_areas=high_risks,
        protective_shields=protective_shields,
        executive_summary=exec_summary,
        saving_grace=saving_grace,
        practical_advice=practical_advice,
    )
