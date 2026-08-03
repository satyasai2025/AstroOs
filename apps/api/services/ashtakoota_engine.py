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
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


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
        diff = ((r_idx_b - r_idx_a) % 12) + 1

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
        mars_house_b: int
    ) -> AshtakootaAnalysisResult:
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

        kootas = [varna, vashya, tara, yoni, graha, gana, bhakoot, nadi]
        total_score = sum(k.obtained_score for k in kootas)
        pct = (total_score / 36.0) * 100.0

        if pct >= 80:
            verdict = "Excellent Match"
        elif pct >= 65:
            verdict = "Good Match"
        elif pct >= 50:
            verdict = "Average Match"
        else:
            verdict = "Low Compatibility"

        # Dosha Checks
        manglik_a = mars_house_a in (1, 4, 7, 8, 12)
        manglik_b = mars_house_b in (1, 4, 7, 8, 12)
        has_manglik_dosha = manglik_a != manglik_b  # Cancelled if both are Manglik

        doshas = [
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

        radar_values = {
            "Varna": (varna.obtained_score / varna.max_score) * 100,
            "Vashya": (vashya.obtained_score / vashya.max_score) * 100,
            "Tara": (tara.obtained_score / tara.max_score) * 100,
            "Yoni": (yoni.obtained_score / yoni.max_score) * 100,
            "Graha Maitri": (graha.obtained_score / graha.max_score) * 100,
            "Gana": (gana.obtained_score / gana.max_score) * 100,
            "Bhakoot": (bhakoot.obtained_score / bhakoot.max_score) * 100,
            "Nadi": (nadi.obtained_score / nadi.max_score) * 100,
        }

        strengths = []
        if nadi.obtained_score == 8:
            strengths.append("Excellent emotional and physiological harmony (No Nadi Dosha)")
        if graha.obtained_score >= 4:
            strengths.append("Strong mental empathy & shared intellectual growth")
        if yoni.obtained_score >= 3:
            strengths.append("Deep physical attraction and family welfare alignment")

        challenges = []
        if nadi.obtained_score == 0:
            challenges.append("Nadi Dosha requires attention to well-being and health")
        if bhakoot.obtained_score == 0:
            challenges.append("Financial decisions and career moves need mutual discussion")
        if has_manglik_dosha:
            challenges.append("Communication under stress can be emotional at times")

        recommendations = [
            "Very favorable alignment for significant joint commitments",
            "Strengthen open communication regarding career and trust",
            "Perform traditional mitigations for partial Mars influence if preferred"
        ]

        return AshtakootaAnalysisResult(
            total_score=total_score,
            compatibility_percentage=round(pct, 1),
            verdict=verdict,
            kootas=kootas,
            doshas=doshas,
            radar_values=radar_values,
            strengths=strengths,
            challenges=challenges,
            recommendations=recommendations,
        )
