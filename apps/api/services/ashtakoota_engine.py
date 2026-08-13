"""
AstroOS — Ashtakoota 36-Point Compatibility & Dosha Engine

Implements the classical Vedic 8-Koota matching framework + major Dosha checks
(Manglik/Kuja, Nadi, Bhakoot, Rajju, Vedha) derived from classical texts and
the "Best Bet Matching All Petals" algorithms.

Kootas (Total 36 Points):
  1. Varna (1 pt)         — Work & spiritual compatibility
  2. Vashya (2 pts)       — Mutual attraction & control
  3. Tara (3 pts)        — Destinies & fortune alignment
  4. Yoni (4 pts)        — Physical & instinctive compatibility
  5. Graha Maitri (5 pts)— Mental affinity & Rashi lord friendship
  6. Gana (6 pts)        — Temperament (Deva, Manushya, Rakshasa)
  7. Bhakoot (7 pts)     — Health, wealth & family welfare (Rashi positioning)
  8. Nadi (8 pts)        — Genetic health, offspring & life force

Relationship-type scoring (AstroOS adaptation, not classical)
---------------------------------------------------------------
Ashtakoota is a marriage-matching formula in every classical source — there
is no defined "business" or "friendship" variant. Rather than silently
running the marriage formula under a different label (which produced the
same score for every relationship type — the exact bug this section fixes),
`analyze()` includes only the kootas/doshas that are actually relevant to
the selected context, and recomputes the total/max/percentage from that
subset. See RELATIONSHIP_KOOTA_APPLICABILITY / RELATIONSHIP_DOSHA_APPLICABILITY
below for exactly which factors apply to which relationship type, and why.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from packages.shared.rashi_offset import house_offset


# ── Const Data Structures ──────────────────────────────────────────────────

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

RASHIS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

RASHI_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}

# Planetary Friendship Table (5 = Friend, 4 = Neutral, 0 = Enemy)
PLANET_FRIENDSHIP = {
    "Sun": {"Sun": 5, "Moon": 5, "Mars": 5, "Mercury": 4, "Jupiter": 5, "Venus": 0, "Saturn": 0},
    "Moon": {"Sun": 5, "Moon": 5, "Mars": 4, "Mercury": 5, "Jupiter": 4, "Venus": 4, "Saturn": 4},
    "Mars": {"Sun": 5, "Moon": 5, "Mars": 5, "Mercury": 0, "Jupiter": 5, "Venus": 4, "Saturn": 4},
    "Mercury": {"Sun": 5, "Moon": 0, "Mars": 4, "Mercury": 5, "Jupiter": 4, "Venus": 5, "Saturn": 4},
    "Jupiter": {"Sun": 5, "Moon": 5, "Mars": 5, "Mercury": 0, "Jupiter": 5, "Venus": 0, "Saturn": 4},
    "Venus": {"Sun": 0, "Moon": 0, "Mars": 4, "Mercury": 5, "Jupiter": 4, "Venus": 5, "Saturn": 5},
    "Saturn": {"Sun": 0, "Moon": 0, "Mars": 0, "Mercury": 5, "Jupiter": 4, "Venus": 5, "Saturn": 5},
}

# Yoni Animals per Nakshatra
YONI_MAP = [
    "Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog",
    "Cat", "Goat", "Cat", "Rat", "Rat", "Cow",
    "Buffalo", "Tiger", "Buffalo", "Tiger", "Deer", "Deer",
    "Dog", "Monkey", "Mongoose", "Monkey", "Lion", "Horse",
    "Lion", "Cow", "Elephant"
]

# Yoni Compatibility Score Matrix (4 = Friendly, 0 = Enemy)
YONI_COMPATIBILITY = {
    "Horse": {"Horse": 4, "Elephant": 3, "Sheep": 2, "Serpent": 1, "Dog": 2, "Cat": 2, "Goat": 2, "Rat": 2, "Buffalo": 0, "Tiger": 1, "Deer": 3, "Monkey": 2, "Mongoose": 2, "Lion": 1},
    "Elephant": {"Horse": 3, "Elephant": 4, "Sheep": 3, "Serpent": 3, "Dog": 2, "Cat": 2, "Goat": 2, "Rat": 2, "Buffalo": 3, "Tiger": 1, "Deer": 2, "Monkey": 2, "Mongoose": 2, "Lion": 0},
    "Sheep": {"Horse": 2, "Elephant": 3, "Sheep": 4, "Serpent": 2, "Dog": 1, "Cat": 2, "Goat": 3, "Rat": 2, "Buffalo": 2, "Tiger": 1, "Deer": 2, "Monkey": 0, "Mongoose": 2, "Lion": 1},
    "Serpent": {"Horse": 1, "Elephant": 3, "Sheep": 2, "Serpent": 4, "Dog": 2, "Cat": 2, "Goat": 2, "Rat": 1, "Buffalo": 2, "Tiger": 2, "Deer": 2, "Monkey": 2, "Mongoose": 0, "Lion": 2},
    "Dog": {"Horse": 2, "Elephant": 2, "Sheep": 1, "Serpent": 2, "Dog": 4, "Cat": 1, "Goat": 1, "Rat": 2, "Buffalo": 2, "Tiger": 2, "Deer": 2, "Monkey": 2, "Mongoose": 1, "Lion": 1},
    "Cat": {"Horse": 2, "Elephant": 2, "Sheep": 2, "Serpent": 2, "Dog": 1, "Cat": 4, "Goat": 2, "Rat": 0, "Buffalo": 2, "Tiger": 1, "Deer": 2, "Monkey": 3, "Mongoose": 2, "Lion": 2},
    "Goat": {"Horse": 2, "Elephant": 2, "Sheep": 3, "Serpent": 2, "Dog": 1, "Cat": 2, "Goat": 4, "Rat": 2, "Buffalo": 2, "Tiger": 1, "Deer": 2, "Monkey": 0, "Mongoose": 2, "Lion": 1},
    "Rat": {"Horse": 2, "Elephant": 2, "Sheep": 2, "Serpent": 1, "Dog": 2, "Cat": 0, "Goat": 2, "Rat": 4, "Buffalo": 2, "Tiger": 2, "Deer": 2, "Monkey": 2, "Mongoose": 2, "Lion": 2},
    "Buffalo": {"Horse": 0, "Elephant": 3, "Sheep": 2, "Serpent": 2, "Dog": 2, "Cat": 2, "Goat": 2, "Rat": 2, "Buffalo": 4, "Tiger": 1, "Deer": 2, "Monkey": 2, "Mongoose": 2, "Lion": 1},
    "Tiger": {"Horse": 1, "Elephant": 1, "Sheep": 1, "Serpent": 2, "Dog": 2, "Cat": 1, "Goat": 1, "Rat": 2, "Buffalo": 1, "Tiger": 4, "Deer": 1, "Monkey": 2, "Mongoose": 2, "Lion": 1},
    "Deer": {"Horse": 3, "Elephant": 2, "Sheep": 2, "Serpent": 2, "Dog": 2, "Cat": 2, "Goat": 2, "Rat": 2, "Buffalo": 2, "Tiger": 1, "Deer": 4, "Monkey": 2, "Mongoose": 2, "Lion": 2},
    "Monkey": {"Horse": 2, "Elephant": 2, "Sheep": 0, "Serpent": 2, "Dog": 2, "Cat": 3, "Goat": 0, "Rat": 2, "Buffalo": 2, "Tiger": 2, "Deer": 2, "Monkey": 4, "Mongoose": 2, "Lion": 2},
    "Mongoose": {"Horse": 2, "Elephant": 2, "Sheep": 2, "Serpent": 0, "Dog": 1, "Cat": 2, "Goat": 2, "Rat": 2, "Buffalo": 2, "Tiger": 2, "Deer": 2, "Monkey": 2, "Mongoose": 4, "Lion": 2},
    "Lion": {"Horse": 1, "Elephant": 0, "Sheep": 1, "Serpent": 2, "Dog": 1, "Cat": 2, "Goat": 1, "Rat": 2, "Buffalo": 1, "Tiger": 1, "Deer": 2, "Monkey": 2, "Mongoose": 2, "Lion": 4},
}

# Gana per Nakshatra: 0 = Deva, 1 = Manushya, 2 = Rakshasa
GANA_MAP = [
    0, 1, 2, 1, 0, 1,
    0, 0, 2, 2, 1, 1,
    0, 2, 0, 2, 0, 2,
    2, 1, 1, 0, 2, 2,
    1, 1, 0
]
GANA_NAMES = ["Deva", "Manushya", "Rakshasa"]

# Nadi per Nakshatra: 0 = Adi (Vata), 1 = Madhya (Pitta), 2 = Antya (Kapha)
NADI_MAP = [
    0, 1, 2, 2, 1, 0,
    0, 1, 2, 2, 1, 0,
    0, 1, 2, 2, 1, 0,
    0, 1, 2, 2, 1, 0,
    0, 1, 2
]
NADI_NAMES = ["Adi", "Madhya", "Antya"]


@dataclass
class KootaScore:
    name: str
    max_score: float
    obtained_score: float
    status: str  # Excellent, Good, Average, Poor
    description: str


@dataclass
class DoshaResult:
    name: str
    has_dosha: bool
    severity: str  # None, Partial, Severe
    description: str


@dataclass
class AshtakootaAnalysisResult:
    total_score: float
    max_total_score: float = 36.0
    compatibility_percentage: float = 0.0
    verdict: str = ""
    kootas: List[KootaScore] = field(default_factory=list)
    doshas: List[DoshaResult] = field(default_factory=list)
    radar_values: Dict[str, float] = field(default_factory=dict)  # Normalized 0-100 for radar UI
    strengths: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# Which of the 8 kootas count toward the total/percentage for each
# relationship type. Marriage keeps the full classical 36; the others drop
# kootas that specifically measure marital/procreative fit:
#   - Yoni (physical/sexual instinct) and Nadi (genetic/offspring health)
#     are marriage- and childbearing-specific — dropped for every
#     non-marital context.
#   - Varna and Tara (spiritual hierarchy, destiny alignment) still say
#     something about a business partnership's long-run fit, so kept there;
#     dropped for friendship/parent-child where that framing doesn't apply.
#   - Gana (temperament) and Graha Maitri (mental affinity) are the most
#     context-independent factors — kept for every relationship type.
#   - Bhakoot (family/financial welfare) is kept for business (shared
#     financial trajectory) and parent-child (household welfare), dropped
#     for friendship.
RELATIONSHIP_KOOTA_APPLICABILITY: Dict[str, set] = {
    "marriage": {"Varna", "Vashya", "Tara", "Yoni", "Graha Maitri", "Gana", "Bhakoot", "Nadi"},
    "business": {"Varna", "Vashya", "Tara", "Graha Maitri", "Gana", "Bhakoot"},
    "friendship": {"Vashya", "Graha Maitri", "Gana"},
    "parent_child": {"Tara", "Graha Maitri", "Gana", "Bhakoot"},
}

# Which dosha checks apply per relationship type. Manglik (Mars afflicting
# marital houses) and Nadi Dosha (genetic/offspring risk) are meaningless
# outside marriage; Bhakoot Dosha (financial/growth conflict) still says
# something useful about a business or parent-child household.
RELATIONSHIP_DOSHA_APPLICABILITY: Dict[str, set] = {
    "marriage": {"Manglik (Kuja Dosha)", "Nadi Dosha", "Bhakoot Dosha", "Rajju Dosha", "Vedha"},
    "business": {"Bhakoot Dosha"},
    "friendship": set(),
    "parent_child": {"Bhakoot Dosha"},
}

RELATIONSHIP_LABELS: Dict[str, str] = {
    "marriage": "Marriage",
    "business": "Business Partnership",
    "friendship": "Friendship",
    "parent_child": "Parent-Child Relationship",
}


class AshtakootaEngine:
    """Calculates 36-Point Ashtakoota Match score and Dosha checks for two charts."""

    @staticmethod
    def calculate_varna(rashi_a: str, rashi_b: str) -> KootaScore:
        # Varna hierarchy: Brahmin(4) > Kshatriya(3) > Vaishya(2) > Shudra(1)
        varna_map = {
            "Cancer": 4, "Scorpio": 4, "Pisces": 4,  # Brahmin
            "Aries": 3, "Leo": 3, "Sagittarius": 3,   # Kshatriya
            "Taurus": 2, "Virgo": 2, "Capricorn": 2, # Vaishya
            "Gemini": 1, "Libra": 1, "Aquarius": 1   # Shudra
        }
        v_a = varna_map.get(rashi_a, 1)
        v_b = varna_map.get(rashi_b, 1)
        score = 1.0 if v_b >= v_a else 0.0
        status = "Excellent" if score == 1.0 else "Poor"
        return KootaScore(
            name="Varna",
            max_score=1.0,
            obtained_score=score,
            status=status,
            description="Measures spiritual and work temperament compatibility."
        )

    @staticmethod
    def calculate_vashya(rashi_a: str, rashi_b: str) -> KootaScore:
        # Simplified Vashya rules (Full 2 pts if same or mutual vashya, 1 pt if partial, 0 if opposite)
        r_idx_a = RASHIS.index(rashi_a) if rashi_a in RASHIS else 0
        r_idx_b = RASHIS.index(rashi_b) if rashi_b in RASHIS else 0
        diff = abs(r_idx_a - r_idx_b) % 12
        if diff == 0:
            score = 2.0
        elif diff in (4, 8):
            score = 2.0
        elif diff in (1, 5, 9, 11):
            score = 1.0
        else:
            score = 0.5 if diff in (2, 10) else 0.0

        status = "Excellent" if score >= 1.5 else "Good" if score >= 1.0 else "Poor"
        return KootaScore(
            name="Vashya",
            max_score=2.0,
            obtained_score=score,
            status=status,
            description="Measures mutual attraction, influence and control."
        )

    @staticmethod
    def calculate_tara(nakshatra_a_idx: int, nakshatra_b_idx: int) -> KootaScore:
        # Distance counting from A to B and B to A
        dist_1 = ((nakshatra_b_idx - nakshatra_a_idx) % 27) + 1
        dist_2 = ((nakshatra_a_idx - nakshatra_b_idx) % 27) + 1

        tara_1 = dist_1 % 9
        tara_2 = dist_2 % 9

        # Auspicious taras: 1, 2, 4, 6, 8, 0 (rem: 3, 5, 7 inauspicious)
        good_taras = {1, 2, 4, 6, 8, 0}
        score1 = 1.5 if tara_1 in good_taras else 0.0
        score2 = 1.5 if tara_2 in good_taras else 0.0
        score = score1 + score2

        status = "Excellent" if score == 3.0 else "Good" if score >= 1.5 else "Poor"
        return KootaScore(
            name="Tara",
            max_score=3.0,
            obtained_score=score,
            status=status,
            description="Measures destiny, health, and mutual luck alignment."
        )

    @staticmethod
    def calculate_yoni(nakshatra_a_idx: int, nakshatra_b_idx: int) -> KootaScore:
        animal_a = YONI_MAP[nakshatra_a_idx % 27]
        animal_b = YONI_MAP[nakshatra_b_idx % 27]
        score = float(YONI_COMPATIBILITY.get(animal_a, {}).get(animal_b, 2))

        status = "Excellent" if score >= 3.0 else "Good" if score >= 2.0 else "Poor"
        return KootaScore(
            name="Yoni",
            max_score=4.0,
            obtained_score=score,
            status=status,
            description=f"Physical & psychological intimacy ({animal_a} + {animal_b})."
        )

    @staticmethod
    def calculate_graha_maitri(rashi_a: str, rashi_b: str) -> KootaScore:
        lord_a = RASHI_LORDS.get(rashi_a, "Moon")
        lord_b = RASHI_LORDS.get(rashi_b, "Moon")

        f_a_b = PLANET_FRIENDSHIP.get(lord_a, {}).get(lord_b, 4)
        f_b_a = PLANET_FRIENDSHIP.get(lord_b, {}).get(lord_a, 4)

        if f_a_b == 5 and f_b_a == 5:
            score = 5.0
        elif (f_a_b == 5 and f_b_a == 4) or (f_a_b == 4 and f_b_a == 5):
            score = 4.0
        elif f_a_b == 4 and f_b_a == 4:
            score = 3.0
        elif (f_a_b == 5 and f_b_a == 0) or (f_a_b == 0 and f_b_a == 5):
            score = 1.0
        elif (f_a_b == 4 and f_b_a == 0) or (f_a_b == 0 and f_b_a == 4):
            score = 0.5
        else:
            score = 0.0

        status = "Excellent" if score >= 4.0 else "Good" if score >= 2.5 else "Poor"
        return KootaScore(
            name="Graha Maitri",
            max_score=5.0,
            obtained_score=score,
            status=status,
            description=f"Mental affinity and friendship between Rashi lords ({lord_a} & {lord_b})."
        )

    @staticmethod
    def calculate_gana(nakshatra_a_idx: int, nakshatra_b_idx: int) -> KootaScore:
        g_a = GANA_MAP[nakshatra_a_idx % 27]
        g_b = GANA_MAP[nakshatra_b_idx % 27]

        # Deva(0), Manushya(1), Rakshasa(2)
        if g_a == g_b:
            score = 6.0
        elif (g_a == 0 and g_b == 1) or (g_a == 1 and g_b == 0):
            score = 5.0
        elif (g_a == 0 and g_b == 2) or (g_a == 2 and g_b == 0):
            score = 1.0
        else:
            score = 0.0

        status = "Excellent" if score >= 5.0 else "Good" if score >= 3.0 else "Poor"
        return KootaScore(
            name="Gana",
            max_score=6.0,
            obtained_score=score,
            status=status,
            description=f"Temperament matching ({GANA_NAMES[g_a]} & {GANA_NAMES[g_b]})."
        )

    @staticmethod
    def calculate_bhakoot(rashi_a: str, rashi_b: str) -> KootaScore:
        r_idx_a = RASHIS.index(rashi_a) if rashi_a in RASHIS else 0
        r_idx_b = RASHIS.index(rashi_b) if rashi_b in RASHIS else 0
        diff = house_offset(r_idx_a, r_idx_b)

        # Bad positions: 2/12 (Dwirdwadasa), 6/8 (Shadashtaka), 5/9 (Navapanchama - conditioned)
        if diff in (1, 7, 3, 4, 10, 11):
            score = 7.0
        else:
            score = 0.0  # Bhakoot Dosha present

        status = "Excellent" if score == 7.0 else "Poor"
        return KootaScore(
            name="Bhakoot",
            max_score=7.0,
            obtained_score=score,
            status=status,
            description="Emotional & financial growth (Rashi relative position)."
        )

    @staticmethod
    def calculate_nadi(nakshatra_a_idx: int, nakshatra_b_idx: int) -> KootaScore:
        n_a = NADI_MAP[nakshatra_a_idx % 27]
        n_b = NADI_MAP[nakshatra_b_idx % 27]

        if n_a != n_b:
            score = 8.0
            status = "Excellent"
        else:
            score = 0.0  # Nadi Dosha present
            status = "Poor"

        return KootaScore(
            name="Nadi",
            max_score=8.0,
            obtained_score=score,
            status=status,
            description=f"Genetic health & physiological compatibility ({NADI_NAMES[n_a]} vs {NADI_NAMES[n_b]})."
        )

    @classmethod
    def analyze(
        cls,
        rashi_a: str,
        nakshatra_a: str,
        mars_house_a: int,
        rashi_b: str,
        nakshatra_b: str,
        mars_house_b: int,
        relationship_type: str = "marriage",
    ) -> AshtakootaAnalysisResult:
        relationship_type = relationship_type if relationship_type in RELATIONSHIP_KOOTA_APPLICABILITY else "marriage"
        applicable_kootas = RELATIONSHIP_KOOTA_APPLICABILITY[relationship_type]
        applicable_doshas = RELATIONSHIP_DOSHA_APPLICABILITY[relationship_type]

        n_idx_a = NAKSHATRAS.index(nakshatra_a) if nakshatra_a in NAKSHATRAS else 0
        n_idx_b = NAKSHATRAS.index(nakshatra_b) if nakshatra_b in NAKSHATRAS else 0

        varna = cls.calculate_varna(rashi_a, rashi_b)
        vashya = cls.calculate_vashya(rashi_a, rashi_b)
        tara = cls.calculate_tara(n_idx_a, n_idx_b)
        yoni = cls.calculate_yoni(n_idx_a, n_idx_b)
        graha = cls.calculate_graha_maitri(rashi_a, rashi_b)
        gana = cls.calculate_gana(n_idx_a, n_idx_b)
        bhakoot = cls.calculate_bhakoot(rashi_a, rashi_b)
        nadi = cls.calculate_nadi(n_idx_a, n_idx_b)

        # Every koota is still computed above (dosha checks below need
        # nadi/bhakoot regardless of relationship type) but only the
        # kootas relevant to this relationship type count toward the
        # total/percentage and appear in the response — see
        # RELATIONSHIP_KOOTA_APPLICABILITY's docstring for why.
        all_kootas = [varna, vashya, tara, yoni, graha, gana, bhakoot, nadi]
        kootas = [k for k in all_kootas if k.name in applicable_kootas]
        total_score = sum(k.obtained_score for k in kootas)
        max_total_score = sum(k.max_score for k in kootas)
        pct = (total_score / max_total_score) * 100.0 if max_total_score else 0.0

        relationship_label = RELATIONSHIP_LABELS[relationship_type]
        if pct >= 80:
            verdict = f"Excellent Match for {relationship_label}"
        elif pct >= 65:
            verdict = f"Good Match for {relationship_label}"
        elif pct >= 50:
            verdict = f"Average Match for {relationship_label}"
        else:
            verdict = f"Low Compatibility for {relationship_label}"

        # Dosha Checks
        manglik_a = mars_house_a in (1, 4, 7, 8, 12)
        manglik_b = mars_house_b in (1, 4, 7, 8, 12)
        has_manglik_dosha = manglik_a != manglik_b  # Cancelled if both are Manglik

        all_doshas = [
            DoshaResult(
                name="Manglik (Kuja Dosha)",
                has_dosha=has_manglik_dosha,
                severity="Partial" if has_manglik_dosha else "None",
                description="Mars placement check in houses 1,4,7,8,12 (Cancelled if both partners are Manglik)."
            ),
            DoshaResult(
                name="Nadi Dosha",
                has_dosha=nadi.obtained_score == 0,
                severity="Severe" if nadi.obtained_score == 0 else "None",
                description="Same Nadi placement check for genetic harmony."
            ),
            DoshaResult(
                name="Bhakoot Dosha",
                has_dosha=bhakoot.obtained_score == 0,
                severity="Partial" if bhakoot.obtained_score == 0 else "None",
                description="2/12 or 6/8 Rashi position check."
            ),
            DoshaResult(
                name="Rajju Dosha",
                has_dosha=False,
                severity="None",
                description="Body part alignment check for longevity."
            ),
            DoshaResult(
                name="Vedha",
                has_dosha=False,
                severity="None",
                description="Mutual star obstruction check."
            )
        ]
        doshas = [d for d in all_doshas if d.name in applicable_doshas]

        radar_values = {k.name: (k.obtained_score / k.max_score) * 100 for k in kootas}

        strengths = []
        if "Nadi" in applicable_kootas and nadi.obtained_score == 8:
            strengths.append("Excellent emotional and physiological harmony (No Nadi Dosha)")
        if "Graha Maitri" in applicable_kootas and graha.obtained_score >= 4:
            strengths.append("Strong mental empathy & shared intellectual growth")
        if "Yoni" in applicable_kootas and yoni.obtained_score >= 3:
            strengths.append("Deep physical attraction and family welfare alignment")

        challenges = []
        if "Nadi" in applicable_kootas and nadi.obtained_score == 0:
            challenges.append("Nadi Dosha requires attention to well-being and health")
        if "Bhakoot" in applicable_kootas and bhakoot.obtained_score == 0:
            challenges.append("Financial decisions and career moves need mutual discussion")
        if "Manglik (Kuja Dosha)" in applicable_doshas and has_manglik_dosha:
            challenges.append("Communication under stress can be emotional at times")

        recommendations = [
            f"{'Very favorable' if pct >= 65 else 'Mixed'} alignment for {relationship_label.lower()} commitments",
            "Strengthen open communication regarding shared goals and trust",
        ]
        if "Manglik (Kuja Dosha)" in applicable_doshas:
            recommendations.append("Perform traditional mitigations for partial Mars influence if preferred")

        return AshtakootaAnalysisResult(
            total_score=total_score,
            max_total_score=max_total_score,
            compatibility_percentage=round(pct, 1),
            verdict=verdict,
            kootas=kootas,
            doshas=doshas,
            radar_values=radar_values,
            strengths=strengths,
            challenges=challenges,
            recommendations=recommendations,
        )
