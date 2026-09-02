"""
AstroOS Meena Numerology Engine
Implements Meena's Numerology Principles with strict mathematical precision,
Loshu/Vedic number grid, compound numbers, day-by-day personal cycle calendar,
letter-by-letter calculation derivations, and repeated numbers synchronicity scanner.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import Counter
from datetime import datetime
import calendar
from apps.api.schemas.meena_numerology import (
    LifeChapterDTO,
    ActivityRecommendationDTO,
    NameVibrationStoryDTO,
    YearForecastDTO,
    MonthForecastDTO,
    GrowthBlindspotDTO,
    MissingNumberActivationDTO,
    LetterValDTO,
    NameLayerAuditDTO,
    DayEnergyDTO,
    CalculationAuditDTO,
    MeenaStoryReportResponse,
    ActivityFinderResponse,
    RepeatedNumberScanResponse,
    HelpConceptDTO,
    MeenaHelpResponse,
)


# ----------------------------------------------------------------------
# 1. CANONICAL MAPPING TABLES (INTERNAL ONLY)
# ----------------------------------------------------------------------

CHALDEAN_MAP: Dict[str, int] = {
    'A': 1, 'I': 1, 'J': 1, 'Q': 1, 'Y': 1,
    'B': 2, 'K': 2, 'R': 2,
    'C': 3, 'G': 3, 'L': 3, 'S': 3,
    'D': 4, 'M': 4, 'T': 4,
    'E': 5, 'H': 5, 'N': 5, 'X': 5,
    'U': 6, 'V': 6, 'W': 6,
    'O': 7, 'Z': 7,
    'F': 8, 'P': 8
}

PYTHAGOREAN_MAP: Dict[str, int] = {
    'A': 1, 'J': 1, 'S': 1,
    'B': 2, 'K': 2, 'T': 2,
    'C': 3, 'L': 3, 'U': 3,
    'D': 4, 'M': 4, 'V': 4,
    'E': 5, 'N': 5, 'W': 5,
    'F': 6, 'O': 6, 'X': 6,
    'G': 7, 'P': 7, 'Y': 7,
    'H': 8, 'Q': 8, 'Z': 8,
    'I': 9, 'R': 9
}

VOWELS: Set[str] = {'A', 'E', 'I', 'O', 'U'}

MONTH_NAMES: List[str] = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

_INTERNAL_ARCHETYPE_MAP: Dict[int, Dict[str, str]] = {
    0: {
        "title": "The Chapter of Pure Potential & Starting Clean",
        "essence": "A phase of dissolution and infinite possibility. Unmanifest energy waiting to be given shape.",
        "advice": "Do not force things. Return to the drawing board and build upon solid, authentic foundations."
    },
    1: {
        "title": "The Chapter of Independent Leadership & Fresh Initiatives",
        "essence": "A phase of pioneering energy, self-confidence, and establishing your unique identity.",
        "advice": "Step into personal authority. Cut through self-doubt and take the driver's seat of your life."
    },
    2: {
        "title": "The Chapter of Intuitive Harmony & Emotional Alignment",
        "essence": "A phase emphasizing emotional sensitivity, partnership, listening, and diplomatic balance.",
        "advice": "Do not rush decisions. Harmonize your inner feelings with external actions, and maintain clear boundaries."
    },
    3: {
        "title": "The Chapter of Creative Space & Expanding Wisdom",
        "essence": "A phase of self-expression, joyful communication, mentoring, and making space for new learning.",
        "advice": "Create actual calendar and mental space for your gifts. Share your wisdom generously with your community."
    },
    4: {
        "title": "The Chapter of Foundation, Discipline & Organization",
        "essence": "A demanding phase focused on systematic effort, practical stability, and resilience under pressure.",
        "advice": "Embrace structure and routine. True freedom comes from mastering practical discipline."
    },
    5: {
        "title": "The Chapter of Dynamic Adaptability & Progressive Growth",
        "essence": "A rapid phase of movement, trade, networking, and learning to balance intellectual curiosity.",
        "advice": "Stay focused on essential priorities. Adapt quickly without scattering your core energy."
    },
    6: {
        "title": "The Chapter of Domestic Grace, Beauty & Nurturing Responsibility",
        "essence": "A phase of harmonizing family, domestic elegance, mentoring, and unconditional service.",
        "advice": "Care for others with healthy detachment. Do not turn love into over-control or martyrdom."
    },
    7: {
        "title": "The Chapter of Quiet Mastery, Restraint & Inner Reflection",
        "essence": "A deep phase of research, spiritual poise, silence, and learning that peace comes from non-reactivity.",
        "advice": "Step back from unnecessary drama. Practice stillness, emotional restraint, and observe before acting."
    },
    8: {
        "title": "The Chapter of Structural Achievement & Material Authority",
        "essence": "A major phase of executive responsibility, wealth management, and building generational assets.",
        "advice": "Lead with ethical integrity and fairness. Manage resources wisely without attachment to power."
    },
    9: {
        "title": "The Chapter of Fullness, Culmination & Safe Completion",
        "essence": "A phase of fulfilling major responsibilities, safe transitions, completing long cycles, and humanitarian service.",
        "advice": "Release what has served its purpose with gratitude. Step forward with total confidence into your completion."
    }
}

_ANNUAL_THEMES: Dict[int, str] = {
    1: "🌱 A Year of New Beginnings, Independence & Fresh Projects",
    2: "🤝 A Year of Partnership, Patience & Emotional Diplomacy",
    3: "🎨 A Year of Creative Expression, Joy & Active Communication",
    4: "🏗️ A Year of Foundation, Organization & Disciplined Structure",
    5: "🦋 A Year of Freedom, Dynamic Transition & Broadening Horizons",
    6: "❤️ A Year of Family, Relationship Harmony, Beauty & Service",
    7: "🔍 A Year of Introspection, Deep Research, Silence & Poise",
    8: "👑 A Year of Executive Achievement, Material Focus & Authority",
    9: "🌅 A Year of Culmination, Releasing Old Baggage & Completion"
}

_MONTHLY_THEMES: Dict[int, str] = {
    1: "🌱 Month of Independent Action & Fresh Launches",
    2: "🤝 Month of Emotional Diplomacy & Strategic Alliances",
    3: "🎨 Month of Creative Networking, Marketing & Joy",
    4: "🏗️ Month of Hard Structure, Budgeting & Organization",
    5: "🦋 Month of Commercial Agility, Sales, Deals & Travel",
    6: "❤️ Month of Family Harmony, Beauty, Wardrobe & Home",
    7: "🔍 Month of Research, Silence, Observation & Poise",
    8: "👑 Month of Executive Authority, Material Milestones & Contracts",
    9: "🌅 Month of Culmination, Clearing Open Loops & Forgiveness"
}

_MONTHLY_STRATEGIES: Dict[int, str] = {
    1: "Ideal for starting personal projects, independent decisions, and taking the initiative without waiting for consensus.",
    2: "Focus on active listening, collaborative agreements, and emotional patience. Avoid reactive confrontations.",
    3: "Great for public presentations, artistic work, social connections, and making room for joyful creative hobbies.",
    4: "Audit practical finances, implement systematic work routines, and handle physical maintenance tasks.",
    5: "Favorable for commercial negotiations, bargain shopping, booking travel, and pivoting quickly on new opportunities.",
    6: "Nurture domestic relationships, upgrade wardrobe/living space, and resolve family matters with calm grace.",
    7: "Step back from unnecessary social noise. Practice non-reactivity, research deeply, and recharge your mental storage.",
    8: "Push forward on career milestones, negotiate financial terms, and make high-level executive decisions.",
    9: "Wrap up unfinished responsibilities, declutter your physical/mental space, and release old resentment loops."
}

_SHADOW_PATTERNS: Dict[int, Dict[str, str]] = {
    0: {
        "title": "Inherited Balance & Untested Foundations",
        "tendency": "Growing up with an inherent sense of balance and fairness, but never having core values stress-tested under real adversity, which can lead to untested assumptions.",
        "correction": "Deliberately step into unfamiliar situations that challenge your assumptions. Treat every equal-rooted stability as a gift to be verified through experience, not taken for granted."
    },
    1: {
        "title": "Over-Impatience & Ego Isolation",
        "tendency": "Tendency to demand immediate outcomes, dismiss others' input prematurely, or feel frustrated when others move slower than you.",
        "correction": "Practice collaborative listening. Allow projects and people natural gestation time without forcing control."
    },
    2: {
        "title": "Boundary Leaks & Decision Paralysis",
        "tendency": "Absorbing others' negative emotional states like a sponge, over-pleasing to avoid friction, and delaying vital decisions due to self-doubt.",
        "correction": "Enforce the 90-Minute Rule: observe others' moods without taking them personally. Practice making small independent decisions daily."
    },
    3: {
        "title": "Scattered Energy & Superficial Escapism",
        "tendency": "Starting multiple exciting creative projects without finishing them, avoiding difficult emotional depth through excessive socializing or humor.",
        "correction": "Focus on one primary creative priority until completion before launching new initiatives. Dedicate time to silent introspection."
    },
    4: {
        "title": "Rigidity & Resistance to Necessary Change",
        "tendency": "Getting trapped in rigid routines, over-worrying about financial worst-case scenarios, and resisting new methods due to perfectionism.",
        "correction": "Incorporate deliberate flexibility into your plans. View unexpected changes as creative upgrades rather than structural threats."
    },
    5: {
        "title": "Restlessness & Impulsive Commitments",
        "tendency": "Chasing novel distractions when projects reach routine stages, making abrupt promises, or feeling trapped by necessary long-term commitments.",
        "correction": "Cultivate voluntary discipline. Anchor mental freedom inside steady daily routines rather than through impulsive escapes."
    },
    6: {
        "title": "Martyrdom Complex & Over-Interference",
        "tendency": "Over-giving until resentment builds, attempting to fix or micromanage other adults' lives, and confusing boundary-setting with selfishness.",
        "correction": "Nurture with healthy detachment. Allow loved ones the dignity of solving their own problems while maintaining your self-care."
    },
    7: {
        "title": "Cynical Withdrawal & Intellectual Pride",
        "tendency": "Distancing yourself emotionally when misunderstood, over-analyzing relationships into cold detachment, or becoming overly skeptical.",
        "correction": "Balance intellectual solitude with warm human connection. Share your insights without demanding universal agreement."
    },
    8: {
        "title": "Excessive Control & Fear of Vulnerability",
        "tendency": "Equating self-worth solely with material results, struggling to delegate tasks, and viewing emotional vulnerability as a tactical weakness.",
        "correction": "Lead through empowerment rather than absolute control. Remember that enduring authority includes compassion and ethical generosity."
    },
    9: {
        "title": "Resentment Grasping & Savior Burnout",
        "tendency": "Holding onto past betrayals long after relationships have ended, carrying the emotional weight of everyone else, and explosive emotional resets.",
        "correction": "Clear your 2GB mental storage: actively forgive and release past chapters so you are completely unburdened for incoming cycles."
    }
}


_MISSING_NUMBER_GUIDELINES: Dict[int, Dict[str, str]] = {
    1: {
        "ruler": "☀️ Sun (Sūrya)",
        "quality": "Independent Leadership, Initiative & Originality",
        "activation": "Take proactive charge of decisions without waiting for external permission. Speak first in meetings and avoid excessive self-doubt.",
        "relational_tip": "Partner or brainstorm with a Number 1 individual to absorb decisiveness and pioneering momentum."
    },
    2: {
        "ruler": "🌙 Moon (Candra)",
        "quality": "Intuitive Sensitivity, Empathy & Diplomacy",
        "activation": "Practice active listening and patience. Give yourself a 90-minute pause to observe feelings before making critical choices.",
        "relational_tip": "Spend time in calming environments and consult a diplomatic Number 2 partner for balanced mediation."
    },
    3: {
        "ruler": "✨ Jupiter (Guru)",
        "quality": "Creative Expression, Optimism & Knowledge Sharing",
        "activation": "Engage in public speaking, writing, artistic hobbies, and sharing knowledge generously without fear of judgment.",
        "relational_tip": "Surround yourself with inspiring, communicative Number 3 friends to spark creative multiplication."
    },
    4: {
        "ruler": "⚡ Rahu",
        "quality": "Disruption, Structural Organization & Innovation",
        "activation": "Establish a disciplined daily system, audit your finances methodically, and embrace unconventional innovative solutions.",
        "relational_tip": "Collaborate with a practical Number 4 colleague to build grounded operational structures."
    },
    5: {
        "ruler": "💬 Mercury (Budha)",
        "quality": "Commercial Agility, Networking & Versatility",
        "activation": "Step out of your comfort zone, engage in commercial negotiations, and build relationships on healthy two-way reciprocity.",
        "relational_tip": "Connect with versatile Number 5 peers to learn rapid adaptability and commercial negotiation."
    },
    6: {
        "ruler": "💎 Venus (Śukra)",
        "quality": "Aesthetic Harmony, Luxury, Beauty & Domestic Nurturing",
        "activation": "Beautify your living space, invest in self-care, wear refined clothing, and nurture family relationships with healthy boundaries.",
        "relational_tip": "Seek counsel from a supportive Number 6 loved one to create warmth and aesthetic refinement."
    },
    7: {
        "ruler": "🧘 Ketu",
        "quality": "Strategic Stillness, Deep Research & Introspection",
        "activation": "Schedule regular quiet time for research, study, and meditation. Practice non-reactivity rather than forcing frantic effort.",
        "relational_tip": "Learn from analytical, introspective Number 7 mentors who understand the power of silence."
    },
    8: {
        "ruler": "👑 Saturn (Śani)",
        "quality": "Executive Authority, Wealth & Generational Impact",
        "activation": "Take full ownership of long-term financial duties, handle contracts decisively, and lead with fair ethical authority.",
        "relational_tip": "Work alongside steady, disciplined Number 8 leaders to build enduring material assets."
    },
    9: {
        "ruler": "🔥 Mars (Maṅgala)",
        "quality": "Protective Courage, Forgiveness & Cycle Completion",
        "activation": "Complete unfinished projects, actively forgive past grievances to free your 2GB mental space, and stand up for others.",
        "relational_tip": "Align with dynamic Number 9 champions when you need the courage to close old chapters and execute missions."
    }
}


# ----------------------------------------------------------------------
# 2. COMPUTATIONAL UTILITIES
# ----------------------------------------------------------------------

def digital_root(n: int) -> int:
    """Calculates the single-digit digital root (1-9) of an integer."""
    if n == 0:
        return 0
    return (n - 1) % 9 + 1


def sum_digits(n: int) -> int:
    """Returns the direct sum of digits of an integer."""
    return sum(int(d) for d in str(abs(n)))


def format_reduction_steps(n: int) -> str:
    """Formats the step-by-step reduction of an integer to its digital root."""
    curr = n
    steps = [str(curr)]
    while curr > 9:
        digits = [int(d) for d in str(curr)]
        curr = sum(digits)
        step_str = " + ".join(str(d) for d in digits) + f" = {curr}"
        steps.append(step_str)
    return " -> ".join(steps) if len(steps) > 1 else str(n)


# ----------------------------------------------------------------------
# 3. CORE SERVICE CLASS
# ----------------------------------------------------------------------

class AstroOSMeenaEngine:
    """Core calculation and narrative engine for Meena's Numerology Method."""

    @classmethod
    def calculate_core_numbers(cls, day: int, month: int, year: int) -> Tuple[int, int]:
        moolank = digital_root(day)
        total_sum = sum_digits(day) + sum_digits(month) + sum_digits(year)
        bhagyank = digital_root(total_sum)
        return moolank, bhagyank

    @classmethod
    def audit_name_layer(cls, layer_name: str, name_str: str, is_full_legal: bool = False) -> NameLayerAuditDTO:
        clean_text = "".join(c for c in name_str.upper() if c.isalpha() or c.isspace()).strip()
        letters_list: List[LetterValDTO] = []
        
        ch_vals = []
        py_vals = []
        soul_vals = []
        pers_vals = []

        for c in clean_text:
            if c.isalpha():
                c_val = CHALDEAN_MAP.get(c, 0)
                p_val = PYTHAGOREAN_MAP.get(c, 0)
                is_v = c in VOWELS
                letters_list.append(LetterValDTO(
                    char=c,
                    chaldean_val=c_val,
                    pythagorean_val=p_val,
                    is_vowel=is_v
                ))
                ch_vals.append(c_val)
                py_vals.append(p_val)
                if is_v:
                    soul_vals.append(p_val)
                else:
                    pers_vals.append(p_val)

        ch_raw = sum(ch_vals)
        ch_red = digital_root(ch_raw)
        ch_formula = " + ".join(f"{l.char}({l.chaldean_val})" for l in letters_list) + f" = {ch_raw} -> {format_reduction_steps(ch_raw)}"

        py_raw = sum(py_vals)
        py_red = digital_root(py_raw)
        py_formula = " + ".join(f"{l.char}({l.pythagorean_val})" for l in letters_list) + f" = {py_raw} -> {format_reduction_steps(py_raw)}"

        soul_formula = None
        soul_num = None
        pers_formula = None
        pers_num = None

        if is_full_legal:
            s_raw = sum(soul_vals)
            soul_num = digital_root(s_raw)
            vowel_letters = [l for l in letters_list if l.is_vowel]
            soul_formula = "Vowels: " + " + ".join(f"{l.char}({l.pythagorean_val})" for l in vowel_letters) + f" = {s_raw} -> {format_reduction_steps(s_raw)}"

            p_raw = sum(pers_vals)
            pers_num = digital_root(p_raw)
            cons_letters = [l for l in letters_list if not l.is_vowel]
            pers_formula = "Consonants: " + " + ".join(f"{l.char}({l.pythagorean_val})" for l in cons_letters) + f" = {p_raw} -> {format_reduction_steps(p_raw)}"

        return NameLayerAuditDTO(
            layer_name=layer_name,
            raw_name=name_str,
            letters=letters_list,
            chaldean_formula=ch_formula,
            chaldean_raw_sum=ch_raw,
            chaldean_reduced=ch_red,
            pythagorean_formula=py_formula,
            pythagorean_raw_sum=py_raw,
            pythagorean_reduced=py_red,
            soul_urge_formula=soul_formula,
            soul_urge_number=soul_num,
            personality_formula=pers_formula,
            personality_number=pers_num
        )

    @classmethod
    def calculate_name_metrics(
        cls,
        full_name: str,
        public_name: Optional[str] = None,
        daily_name: Optional[str] = None
    ) -> Dict[str, Any]:
        clean_full = "".join(c for c in full_name.upper() if c.isalpha() or c.isspace()).strip()
        if not any(c.isalpha() for c in clean_full):
            raise ValueError("Full name must contain at least one alphabetic character.")

        clean_pub = "".join(c for c in (public_name or full_name).upper() if c.isalpha() or c.isspace()).strip()
        if daily_name:
            daily_source = daily_name
        elif clean_pub:
            daily_source = clean_pub.split()[0]
        else:
            daily_source = full_name
        clean_daily = "".join(c for c in daily_source.upper() if c.isalpha()).strip()

        ch_full_raw = sum(CHALDEAN_MAP.get(c, 0) for c in clean_full if c.isalpha())
        ch_full = digital_root(ch_full_raw)

        ch_pub_raw = sum(CHALDEAN_MAP.get(c, 0) for c in clean_pub if c.isalpha())
        ch_pub = digital_root(ch_pub_raw)

        ch_daily_raw = sum(CHALDEAN_MAP.get(c, 0) for c in clean_daily if c.isalpha())
        ch_daily = digital_root(ch_daily_raw)

        py_full_raw = sum(PYTHAGOREAN_MAP.get(c, 0) for c in clean_full if c.isalpha())
        py_full = digital_root(py_full_raw)

        py_pub_raw = sum(PYTHAGOREAN_MAP.get(c, 0) for c in clean_pub if c.isalpha())
        py_pub = digital_root(py_pub_raw)

        py_daily_raw = sum(PYTHAGOREAN_MAP.get(c, 0) for c in clean_daily if c.isalpha())
        py_daily = digital_root(py_daily_raw)

        soul_raw = sum(PYTHAGOREAN_MAP.get(c, 0) for c in clean_full if c in VOWELS)
        soul_num = digital_root(soul_raw)

        pers_raw = sum(PYTHAGOREAN_MAP.get(c, 0) for c in clean_full if c.isalpha() and c not in VOWELS)
        personality_num = digital_root(pers_raw)

        words = clean_full.split()
        initials_sum = sum(PYTHAGOREAN_MAP.get(w[0], 0) for w in words if w)
        balance_num = digital_root(initials_sum)

        # Hidden Passion: Most frequent single digit from full name letters
        letter_digits = [PYTHAGOREAN_MAP.get(c, 0) for c in clean_full if c.isalpha()]
        digit_counts = Counter(letter_digits)
        # Find digit with highest frequency
        if digit_counts:
            hidden_passion = max(digit_counts.keys(), key=lambda k: (digit_counts[k], -k))
            hidden_passion_count = digit_counts[hidden_passion]
        else:
            hidden_passion = 1
            hidden_passion_count = 1

        return {
            "clean_full": clean_full,
            "clean_pub": clean_pub,
            "clean_daily": clean_daily,
            "ch_full_raw": ch_full_raw,
            "ch_full": ch_full,
            "ch_pub_raw": ch_pub_raw,
            "ch_pub": ch_pub,
            "ch_daily_raw": ch_daily_raw,
            "ch_daily": ch_daily,
            "py_full_raw": py_full_raw,
            "py_full": py_full,
            "py_pub_raw": py_pub_raw,
            "py_pub": py_pub,
            "py_daily_raw": py_daily_raw,
            "py_daily": py_daily,
            "soul_raw": soul_raw,
            "soul_num": soul_num,
            "pers_raw": pers_raw,
            "personality_num": personality_num,
            "balance_num": balance_num,
            "initials_sum": initials_sum,
            "hidden_passion": hidden_passion,
            "hidden_passion_count": hidden_passion_count
        }

    @classmethod
    def calculate_challenges_and_pinnacles(
        cls, day: int, month: int, year: int, bhagyank: int
    ) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        d_root = digital_root(day)
        m_root = digital_root(month)
        y_root = digital_root(year)

        c1 = abs(d_root - m_root)
        c2 = abs(d_root - y_root)
        primary_c3 = abs(c1 - c2)
        c4 = abs(m_root - y_root)

        challenges = {
            "c1": c1,
            "c2": c2,
            "primary_c3": primary_c3,
            "c4": c4
        }

        first_pinnacle_end_age = 36 - bhagyank
        p1 = digital_root(m_root + d_root)
        p2 = digital_root(d_root + y_root)
        p3 = digital_root(p1 + p2)
        p4 = digital_root(m_root + y_root)

        pinnacles = [
            {"index": 1, "start": 0, "end": first_pinnacle_end_age, "num": p1, "challenge": c1},
            {"index": 2, "start": first_pinnacle_end_age + 1, "end": first_pinnacle_end_age + 9, "num": p2, "challenge": c2},
            {"index": 3, "start": first_pinnacle_end_age + 10, "end": first_pinnacle_end_age + 18, "num": p3, "challenge": primary_c3},
            {"index": 4, "start": first_pinnacle_end_age + 19, "end": None, "num": p4, "challenge": c4},
        ]

        return challenges, pinnacles

    @classmethod
    def get_activity_dates(
        cls,
        activity_category: str,
        day: int,
        month: int,
        target_year: int,
        target_month: int,
    ) -> Tuple[List[int], str, str]:
        """
        Single source of truth for activity category -> date mapping.
        """
        current_year = datetime.now().year
        if target_year > current_year + 5:
            raise ValueError(
                f"Activity date finding is limited to a 5-year window "
                f"(up to {current_year + 5})."
            )
        if not (1 <= target_month <= 12):
            raise ValueError("target_month must be between 1 and 12.")

        num_days = calendar.monthrange(target_year, target_month)[1]
        py, pm, pd_map = cls.calculate_personal_cycles(day, month, target_year, target_month)

        category = activity_category.lower()
        if "shop" in category or "deal" in category:
            best_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) == 5]
            reasoning = "Operates on dynamic commercial clarity and bargaining agility."
            advice = "Great for comparing deals, electronic purchases, and discovering bargains."
        elif "luxe" in category or "beauty" in category:
            best_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) == 6]
            reasoning = "Operates on aesthetic harmony, luxury, and artistic beauty."
            advice = "Perfect for clothing, jewelry, salon visits, and home decoration."
        elif "career" in category or "interview" in category:
            best_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) in (1, 8)]
            reasoning = "Operates on leadership initiative (1) and executive authority (8)."
            advice = "Best for interviews, launching projects, meeting superiors, and signing milestones."
        elif "property" in category or "asset" in category:
            best_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) in (4, 8)]
            reasoning = "Operates on structural foundation (4) and enduring long-term wealth (8)."
            advice = "Favorable for visiting properties, negotiating lease agreements, and finalizing assets."
        elif "vehicle" in category or "travel" in category:
            best_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) in (5, 9)]
            reasoning = "Operates on rapid mobility (5) and protective culmination of journeys (9)."
            advice = "Ideal for vehicle maintenance, test drives, ticket bookings, and beginning travels."
        elif "restraint" in category or "silence" in category:
            best_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) == 7]
            reasoning = "Operates on internal poise, spiritual study, and non-reactive calm."
            advice = "Avoid entering heated arguments, signing hasty contracts, or impulsive spending."
        else:
            best_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) in (py, pm)]
            reasoning = "Aligned with your major personal monthly rhythm."
            advice = "Good general gateway dates for personal priorities."

        return best_dates, reasoning, advice

    @classmethod
    def calculate_personal_cycles(
        cls, day: int, month: int, target_year: int, target_month: int
    ) -> Tuple[int, int, Dict[int, int]]:
        d_root = digital_root(day)
        m_root = digital_root(month)
        y_root = digital_root(target_year)

        personal_year = digital_root(d_root + m_root + y_root)
        personal_month = digital_root(personal_year + target_month)

        personal_dates = {}
        for date in range(1, 32):
            personal_dates[date] = digital_root(personal_month + digital_root(date))

        return personal_year, personal_month, personal_dates

    @classmethod
    def scan_repeated_number(
        cls,
        sequence: str,
        day: Optional[int] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        target_year: Optional[int] = None
    ) -> RepeatedNumberScanResponse:
        clean = sequence.replace(":", "").replace(" ", "").strip()
        digits_only = "".join(c for c in clean if c.isdigit())
        if not digits_only or len(set(digits_only)) != 1:
            raise ValueError(
                "Sequence must contain only one repeated digit "
                "(e.g. '111', '333', '7777')."
            )
        digit_count = len(digits_only)
        first_char = digits_only[0]

        meanings = {
            "0": {
                "signal": "Karmic Clean Slate & Void of Potential",
                "meaning": "You are at a complete turning point where old karmic accounts are closing. The slate is wiped clean.",
                "directive": "Do not carry forward old baggage or unresolved resentment. Start fresh with total sincerity.",
                "warning": "Avoid feeling lost or aimless; recognize that a blank canvas gives you full creative authorship."
            },
            "1": {
                "signal": "Conscious Initiative & Independent Leadership",
                "meaning": "Your active conscious intent and willpower are in sharp alignment. A green light for independent action.",
                "directive": "Step forward with confidence. Launch the project, make the call, or set the boundary you've been delaying.",
                "warning": "Avoid over-impatience, stubborn self-isolation, or waiting for others' validation."
            },
            "2": {
                "signal": "Emotional Sensitivity & Partnership Alignment",
                "meaning": "Your intuitive subconscious is receiving cues. Highlights relationships, emotional balance, and diplomatic timing.",
                "directive": "Practice active listening and emotional poise. Seek collaborative solutions rather than aggressive debates.",
                "warning": "Watch out for emotional boundary leaks. Enforce the 90-minute reset rule before reacting."
            },
            "3": {
                "signal": "Creative Expression & Joyful Expansion",
                "meaning": "Your creative centers are active. Indicates that your voice, perspective, and ideas need authentic expression.",
                "directive": "Speak your truth, write down your concepts, and make calendar space for uplifting creative pursuits.",
                "warning": "Avoid scattering your focus across too many superficial distractions."
            },
            "4": {
                "signal": "Structural Foundation & Grounded Stability",
                "meaning": "A call to organize practical routines, secure physical/financial roots, and implement discipline.",
                "directive": "Focus on the foundational details: audit finances, streamline operations, and commit to steady effort.",
                "warning": "Avoid rigidity, catastrophic worry about security, or resisting healthy updates."
            },
            "5": {
                "signal": "Dynamic Adaptability, Commerce & Progressive Shift",
                "meaning": "High momentum indicating rapid trade opportunities, communication breakthroughs, or travel.",
                "directive": "Stay versatile and adaptable. Embrace positive transitions and negotiate with agility.",
                "warning": "Avoid restlessness, making impulsive promises, or abandoning solid long-term plans."
            },
            "6": {
                "signal": "Domestic Harmony, Beauty & Compassionate Service",
                "meaning": "Highlights family commitments, aesthetic harmony, relationship repair, and mentoring others.",
                "directive": "Infuse grace and warmth into your immediate environment. Resolve domestic friction with kindness.",
                "warning": "Avoid martyr behavior, emotional manipulation, or attempting to micromanage loved ones."
            },
            "7": {
                "signal": "Quiet Mastery, Restraint & Strategic Stillness",
                "meaning": "Deep intuition and analytical insight are heightened. A reminder that peace and power lie in non-reactivity.",
                "directive": "Step back into observation. Study, research, practice silence, and avoid rushed public arguments.",
                "warning": "Avoid cynical withdrawal, intellectual arrogance, or emotional coldness toward peers."
            },
            "8": {
                "signal": "Executive Authority, Wealth & Generational Impact",
                "meaning": "High karmic and material responsibility. Your ability to lead, manage resources, and achieve is activated.",
                "directive": "Step into executive leadership with fairness. Handle financial transactions and contracts decisively.",
                "warning": "Avoid ruthless ambition, obsession with control, or fear of material vulnerability."
            },
            "9": {
                "signal": "Culmination, Releasing Baggage & Safe Completion",
                "meaning": "Major cycles are culminating. A signal to forgive, release old ties, and complete long-standing duties.",
                "directive": "Close open loops with gratitude. Clean your 2GB mental space to prepare for the next 9-year cycle.",
                "warning": "Avoid clinging to expired situations or indulging in explosive emotional resentment."
            }
        }

        data = meanings.get(first_char, meanings["1"])

        # MEENA'S REPETITION COUNT LAW:
        # < 3 digits: No special synchronicity value (baseline probability)
        # == 3 digits: The Sweet Spot (Optimal flow & favorable timing)
        # >= 4 digits: Overload & Congestion (Not good, hyper-fixation loop)
        if digit_count < 3:
            signal_status = "⚠️ Normal Pattern (< 3 Digits: No Synchronicity Value)"
            is_favorable = False
            subconscious_signal = "Baseline Random Background Noise"
            psychological_meaning = f"In Meena's Numerology Method, sequences with fewer than 3 digits ({sequence}) carry no special synchronicity value. They are normal everyday occurrences without subconscious timing importance."
            actionable_directive = "Do not over-analyze single or double numbers. Carry on with your normal daily tasks without looking for hidden signs."
            shadow_warning = "Avoid superstitious over-interpretation of random everyday numbers."
        elif digit_count == 3:
            signal_status = "✨ Auspicious Synchronicity (Exactly 3 Digits: Optimal Flow & Favorable)"
            is_favorable = True
            subconscious_signal = data["signal"]
            psychological_meaning = f"In Meena's Numerology Method, exactly 3 repeated digits ({sequence}) is the auspicious sweet spot. It signals optimal timing, clean subconscious-conscious alignment, and a favorable green light."
            actionable_directive = data["directive"]
            shadow_warning = data["warning"]
        else:
            signal_status = "🚨 Energetic Overload & Imbalance (4+ Digits: Not Favorable / Red Alert)"
            is_favorable = False
            subconscious_signal = f"Mental Congestion & Hyper-Fixation Warning ({data['signal']})"
            psychological_meaning = f"In Meena's Numerology Method, seeing 4 or more repeated digits ({sequence}) is NOT a good sign. It indicates severe mental overload, hyper-fixation, over-grasping onto an outcome, and a 2GB mental space clogged with worry loops."
            actionable_directive = "STOP immediately. Enforce the strict 90-Minute Reset Protocol: step away from the problem, avoid impulsive decisions, and clear your 2GB mental storage before acting."
            shadow_warning = f"Obsessive control, anxiety loops, and trying to force an outcome that needs patient gestation."

        # Personalized synthesis when birth profile is present
        personal_res = None
        personal_guidance = None
        if day and month and year:
            moolank, bhagyank = cls.calculate_core_numbers(day, month, year)
            t_year = target_year or datetime.now().year
            py = digital_root(digital_root(day) + digital_root(month) + digital_root(t_year))
            s_num = int(first_char) if first_char.isdigit() else 1

            if digit_count >= 4:
                personal_res = f"⚠️ Overload Alert for Chart (Root {moolank} in Year {py})"
                personal_guidance = f"You are currently in Personal Year {py}. Seeing 4+ digits ({sequence}) indicates that you are over-stressing your {data['signal']} axis. Release the mental grip."
            elif digit_count == 3:
                if s_num == py:
                    personal_res = f"🎯 Direct Timing Multiplier (Matches Personal Year {py})"
                    personal_guidance = f"Seeing {sequence} is a high-priority green light for you in {target_year}. It aligns directly with your active Personal Year {py} cycle."
                elif s_num == moolank:
                    personal_res = f"🧬 Core Instinct Synchronization (Matches Root {moolank})"
                    personal_guidance = f"Seeing {sequence} confirms that your natural spontaneous instincts (Root {moolank}) are in exact harmony with your environment right now."
                elif s_num == bhagyank:
                    personal_res = f"🧭 Destiny Evolutionary Call (Matches Destiny {bhagyank})"
                    personal_guidance = f"Seeing {sequence} signals a major alignment with your overarching life purpose (Destiny {bhagyank})."
                else:
                    personal_res = f"⚖️ Complementary Balancing Frequency"
                    personal_guidance = f"While your operating nature is Root {moolank} in Personal Year {py}, seeing {sequence} brings complementary {data['signal']} into your current circumstances."

        return RepeatedNumberScanResponse(
            sequence=sequence,
            digit_count=digit_count,
            signal_status=signal_status,
            is_favorable=is_favorable,
            subconscious_signal=subconscious_signal,
            psychological_meaning=psychological_meaning,
            personal_resonance=personal_res,
            personal_custom_guidance=personal_guidance,
            actionable_directive=actionable_directive,
            shadow_warning=shadow_warning
        )

    @classmethod
    def generate_story_report(
        cls,
        day: int,
        month: int,
        year: int,
        full_name: str,
        public_name: Optional[str] = None,
        daily_name: Optional[str] = None,
        target_year: Optional[int] = None,
        target_month: int = 9,
    ) -> MeenaStoryReportResponse:
        current_year = datetime.now().year
        if target_year is None:
            target_year = current_year
        if target_year > current_year + 5:
            raise ValueError(
                f"Forecasts are limited to a rolling 5-year window "
                f"(max {current_year + 5})."
            )
        moolank, bhagyank = cls.calculate_core_numbers(day, month, year)
        name_data = cls.calculate_name_metrics(full_name, public_name, daily_name)
        challenges, pinnacles = cls.calculate_challenges_and_pinnacles(day, month, year, bhagyank)
        py, pm, pd_map = cls.calculate_personal_cycles(day, month, target_year, target_month)

        d_root = digital_root(day)
        m_root = digital_root(month)
        y_root = digital_root(year)

        # Build Loshu / Vedic Number Grid from Date of Birth + Core numbers
        dob_digits = [int(d) for d in f"{day}{month}{year}" if d != '0']
        all_grid_digits = dob_digits + [moolank, bhagyank]
        counts = Counter(all_grid_digits)
        loshu_grid = {str(k): counts.get(k, 0) for k in range(1, 10)}

        num_days = calendar.monthrange(target_year, target_month)[1] if (1 <= target_month <= 12) else 30

        # Day-by-Day Calendar Energy Breakdown
        day_categories_meta = {
            1: ("🌱", "Career, Initiation & Independent Action"),
            2: ("🤝", "Partnership, Listening & Emotional Calm"),
            3: ("🎨", "Creative Expression, Marketing & Networking"),
            4: ("🏗️", "Hard Structure, Budgeting & Organization"),
            5: ("🦋", "Deals, Trade, Sales & Swift Movement"),
            6: ("❤️", "Family Harmony, Luxury, Beauty & Home"),
            7: ("🔍", "Restraint, Silence, Research & Poise"),
            8: ("👑", "Executive Authority, Contracts & Property"),
            9: ("🌅", "Culmination, Closing Loops & Safe Completion")
        }
        month_calendar_days: List[DayEnergyDTO] = []
        for d in range(1, num_days + 1):
            d_r = digital_root(d)
            pd_val = digital_root(pm + d_r)
            is_peak = (pd_val == py or pd_val == pm)
            icon, cat_name = day_categories_meta.get(pd_val, ("✨", "General Action"))
            dow = calendar.day_name[calendar.weekday(target_year, target_month, d)][:3]
            raw_s = pm + d_r
            calc_formula = f"Personal Month ({pm}) + Day {d} (Root: {d_r}) = {raw_s} -> Personal Date {pd_val}"

            month_calendar_days.append(DayEnergyDTO(
                date=d,
                day_of_week=dow,
                personal_month_number=pm,
                day_root=d_r,
                personal_date_number=pd_val,
                dominant_category=cat_name,
                category_icon=icon,
                calculation_formula=calc_formula,
                is_peak_date=is_peak
            ))

        # Calculation Audit Formulations
        moolank_formula = (
            f"Day {day} -> {format_reduction_steps(day)}"
            if day > 9
            else f"Day {day} -> {day}"
        )
        
        b_digits_sum = sum_digits(day) + sum_digits(month) + sum_digits(year)
        bhagyank_formula = f"Full Date: {day}/{month}/{year} -> Sum of digits: {b_digits_sum} -> {format_reduction_steps(b_digits_sum)}"

        # Name Layers Calculation Audits
        daily_audit = cls.audit_name_layer("1. Daily Spoken / Calling Name", name_data["clean_daily"])
        public_audit = cls.audit_name_layer("2. Public / Social / Professional Name", name_data["clean_pub"])
        legal_audit = cls.audit_name_layer("3. Official Legal / Document Name", full_name, is_full_legal=True)

        c1_formula = f"|Day Root ({d_root}) - Month Root ({m_root})| = |{d_root - m_root}| = {challenges['c1']}"
        c2_formula = f"|Day Root ({d_root}) - Year Root ({y_root})| = |{d_root - y_root}| = {challenges['c2']}"
        c3_formula = f"|C1 ({challenges['c1']}) - C2 ({challenges['c2']})| = |{challenges['c1'] - challenges['c2']}| = {challenges['primary_c3']} (Primary Inner Test)"
        c4_formula = f"|Month Root ({m_root}) - Year Root ({y_root})| = |{m_root - y_root}| = {challenges['c4']}"

        first_p_age = 36 - bhagyank
        first_p_formula = f"36 - Destiny Number ({bhagyank}) = {first_p_age} Years (Chapter 1 spans Age 0 to {first_p_age})"
        p1_formula = f"Month Root ({m_root}) + Day Root ({d_root}) = {m_root + d_root} -> {pinnacles[0]['num']} (Age 0 to {first_p_age})"
        p2_formula = f"Day Root ({d_root}) + Year Root ({y_root}) = {d_root + y_root} -> {pinnacles[1]['num']} (Age {first_p_age + 1} to {first_p_age + 9})"
        p3_formula = f"P1 ({pinnacles[0]['num']}) + P2 ({pinnacles[1]['num']}) = {pinnacles[0]['num'] + pinnacles[1]['num']} -> {pinnacles[2]['num']} (Age {first_p_age + 10} to {first_p_age + 18})"
        p4_formula = f"Month Root ({m_root}) + Year Root ({y_root}) = {m_root + y_root} -> {pinnacles[3]['num']} (Age {first_p_age + 19} and Onward)"

        target_y_root = digital_root(target_year)
        py_formula = f"Day Root ({d_root}) + Month Root ({m_root}) + Year Root {target_year} ({target_y_root}) = {d_root + m_root + target_y_root} -> Personal Year {py}"
        pm_formula = f"Personal Year ({py}) + Target Month ({target_month}) = {py + target_month} -> Personal Month {pm}"
        pd_sample_formula = f"Personal Month ({pm}) + Calendar Date (e.g. 9) = {pm + 9} -> {digital_root(pm + 9)} (Personal Date {digital_root(pm + 9)})"

        maturity_num = digital_root(name_data["py_full"] + bhagyank)
        maturity_formula = f"Maturity Number: Pythagorean Name ({name_data['py_full']}) + Destiny ({bhagyank}) = {name_data['py_full'] + bhagyank} -> {maturity_num} (Activates at Age 40, Dominant after 50)"
        
        balance_initials_str = " + ".join(f"{w[0]}({PYTHAGOREAN_MAP.get(w[0], 0)})" for w in full_name.upper().split() if w and w[0].isalpha())
        balance_formula = f"Balance Number: Initials: {balance_initials_str} = {name_data['initials_sum']} -> {name_data['balance_num']} (Personal-Family Poise)"
        
        hp_formula = f"Hidden Passion: Number {name_data['hidden_passion']} appears {name_data['hidden_passion_count']} times in full name (Inner Core Drive)"

        calculation_audit = CalculationAuditDTO(
            moolank_number=moolank,
            moolank_compound=day,
            moolank_formula=moolank_formula,
            bhagyank_number=bhagyank,
            bhagyank_compound=b_digits_sum,
            bhagyank_formula=bhagyank_formula,
            soul_urge_number=name_data["soul_num"],
            soul_urge_compound=name_data["soul_raw"],
            personality_number=name_data["personality_num"],
            personality_compound=name_data["pers_raw"],
            maturity_number=maturity_num,
            maturity_formula=maturity_formula,
            balance_number=name_data["balance_num"],
            balance_formula=balance_formula,
            hidden_passion_number=name_data["hidden_passion"],
            hidden_passion_formula=hp_formula,
            names_breakdown=[daily_audit, public_audit, legal_audit],
            loshu_grid=loshu_grid,
            challenge_c1_formula=c1_formula,
            challenge_c2_formula=c2_formula,
            challenge_primary_c3_formula=c3_formula,
            challenge_c4_formula=c4_formula,
            first_pinnacle_age_formula=first_p_formula,
            pinnacle_p1_formula=p1_formula,
            pinnacle_p2_formula=p2_formula,
            pinnacle_p3_formula=p3_formula,
            pinnacle_p4_formula=p4_formula,
            personal_year_formula=py_formula,
            personal_month_formula=pm_formula,
            personal_date_formula_sample=pd_sample_formula,
            month_calendar_days=month_calendar_days
        )

        core_descriptions = {
            1: "You possess an innate drive for self-direction, pioneering courage, and original initiative. You prefer taking proactive responsibility.",
            2: "You are gifted with deep empathy, intuitive sensitivity, and relational diplomacy. You naturally perceive unexpressed group dynamics.",
            3: "You are vibrant, communicative, and intellectually optimistic. You bring creative solutions, wisdom, and uplifting perspective.",
            4: "You are an unconventional structural thinker, grounded in systematic organization, resilience, and methodical execution.",
            5: "You possess high mental agility, rapid adaptability, and commercial acumen. You thrive on intellectual freedom and networking.",
            6: "You have an instinct for aesthetic harmony, nurturing leadership, and domestic elegance. You create supportive environments.",
            7: "You are deeply analytical, intuitive, and contemplative. You seek the underlying principles behind events and value quiet depth.",
            8: "You are built for executive capability, structural mastery, and enduring achievement. You understand long-term value.",
            9: "You are dynamic, protective, and purpose-driven. You possess the courage to drive transformations and complete major missions."
        }
        core_story = core_descriptions.get(moolank, "A uniquely balanced profile with versatile strengths.")

        destiny_descriptions = {
            1: "Your life journey calls you to pioneer independent paths, overcome self-doubt, and lead with quiet self-assurance.",
            2: "Your path guides you to master emotional diplomacy, active listening, and building constructive, balanced alliances.",
            3: "Your journey calls you to communicate meaningful insights, cultivate creative space, and share wisdom generously.",
            4: "Your path challenges you to build solid foundations, turn raw ideas into reality, and innovate with practical discipline.",
            5: "Your destiny is centered on mental agility, trade, communication, and learning to stay grounded through self-discipline.",
            6: "Your journey directs you toward constructive service, domestic elegance, and mentoring others with balanced boundaries.",
            7: "Your path is about developing poise, analytical mastery, and discovering that stillness is stronger than reactive force.",
            8: "Your destiny is to master worldly responsibility, manage resources wisely, and establish enduring generational value.",
            9: "Your journey is about culminating major cycles, giving your best with healthy detachment, and guiding safe closures."
        }
        destiny_story = destiny_descriptions.get(bhagyank, "A destiny dedicated to purposeful growth.")

        superpowers = {
            1: "Independent initiative, pioneering courage, and decisive leadership.",
            2: "Deep intuition, emotional empathy, and diplomatic mediation.",
            3: "Inspiring communication, creative optimism, and community engagement.",
            4: "Inventive originality, structural discipline, and steadfast resilience.",
            5: "Rapid learning, commercial negotiation, and versatile adaptability.",
            6: "Harmonizing relationships, aesthetic refinement, and nurturing care.",
            7: "Analytical depth, spiritual poise, and strategic stillness.",
            8: "Executive stamina, resource management, and enduring achievement.",
            9: "Courageous transformation, protective strength, and safe completion."
        }
        hidden_superpower = superpowers.get(name_data["py_full"], "Adaptable inner resilience.")

        inner_tests = {
            0: "Mastering the courage to begin anew without anxiety or feeling displaced.",
            1: "Overcoming self-doubt and the urge to wait for external permission.",
            2: "Mastering emotional boundaries: learning not to absorb others' stress, and avoiding indecision.",
            3: "Overcoming scattered focus, avoiding superficiality, and sharing your deeper wisdom.",
            4: "Balancing strict discipline with mental flexibility and avoiding rigid worry.",
            5: "Channeling restless energy through voluntary discipline and consistent focus.",
            6: "Avoiding martyr tendencies, over-controlling outcomes, or conditional giving.",
            7: "Overcoming cynical withdrawal, practicing silence, and avoiding reactive arguments.",
            8: "Balancing material ambition with ethical compassion and healthy delegation.",
            9: "Releasing past resentments with gratitude and avoiding explosive emotional resets."
        }
        inner_test = inner_tests.get(challenges["primary_c3"], "Maintaining balanced self-discipline.")

        # Diplomatic Shadow / Growth Blindspots
        core_shadow = _SHADOW_PATTERNS.get(moolank, _SHADOW_PATTERNS[2])
        destiny_shadow = _SHADOW_PATTERNS.get(bhagyank, _SHADOW_PATTERNS[5])
        challenge_shadow = _SHADOW_PATTERNS.get(challenges["primary_c3"], _SHADOW_PATTERNS[1])
        
        growth_blindspots = [
            GrowthBlindspotDTO(
                blindspot_title=f"Core Instinct Shadow (Number {moolank}): {core_shadow['title']}",
                tendency_description=core_shadow["tendency"],
                corrective_action=core_shadow["correction"]
            ),
            GrowthBlindspotDTO(
                blindspot_title=f"Life Path Shadow (Number {bhagyank}): {destiny_shadow['title']}",
                tendency_description=destiny_shadow["tendency"],
                corrective_action=destiny_shadow["correction"]
            ),
            GrowthBlindspotDTO(
                blindspot_title=f"Major Inner Test (Challenge {challenges['primary_c3']}): {challenge_shadow['title']}",
                tendency_description=inner_test,
                corrective_action=challenge_shadow["correction"]
            )
        ]

        name_vibrations = [
            NameVibrationStoryDTO(
                name_type="Daily Spoken Name",
                name_value=name_data["clean_daily"],
                chaldean_compound=name_data["ch_daily_raw"],
                chaldean_reduced=name_data["ch_daily"],
                pythagorean_compound=name_data["py_daily_raw"],
                pythagorean_reduced=name_data["py_daily"],
                vibrational_essence=f"Carries an active daily resonance of energy {name_data['ch_daily']} (Compound: {name_data['ch_daily_raw']}). Shapes your intimate relationships and instinctive reactions.",
                strategic_note="This is the sound vibration triggered every time you are called aloud. It acts directly on your day-to-day emotional field."
            ),
            NameVibrationStoryDTO(
                name_type="Public / Social Name",
                name_value=name_data["clean_pub"],
                chaldean_compound=name_data["ch_pub_raw"],
                chaldean_reduced=name_data["ch_pub"],
                pythagorean_compound=name_data["py_pub_raw"],
                pythagorean_reduced=name_data["py_pub"],
                vibrational_essence=f"Operates at social resonance {name_data['ch_pub']} (Compound: {name_data['ch_pub_raw']}). Governs your public reputation, professional warmth, and social sphere.",
                strategic_note="Used for professional networking, social media, and how acquaintances perceive your presence."
            ),
            NameVibrationStoryDTO(
                name_type="Official Legal / Document Name",
                name_value=full_name,
                chaldean_compound=name_data["ch_full_raw"],
                chaldean_reduced=name_data["ch_full"],
                pythagorean_compound=name_data["py_full_raw"],
                pythagorean_reduced=name_data["py_full"],
                vibrational_essence=f"Operates at formal resonance {name_data['ch_full']} (Compound: {name_data['ch_full_raw']}). Governs your institutional karma, legal documentation, and career stability.",
                strategic_note="Shapes your formal identity on passports, contracts, and banking agreements."
            )
        ]

        life_chapters = []
        for p in pinnacles:
            idx = p["index"]
            p_num = p["num"]
            c_num = p.get("challenge", 0)
            age_span = f"Age {p['start']} to {p['end']}" if p["end"] else f"Age {p['start']} and Onward"
            archetype_info = _INTERNAL_ARCHETYPE_MAP.get(p_num, _INTERNAL_ARCHETYPE_MAP[1])
            life_chapters.append(
                LifeChapterDTO(
                    chapter_index=idx,
                    age_span=age_span,
                    pinnacle_number=p_num,
                    challenge_number=c_num,
                    chapter_title=archetype_info["title"],
                    description=archetype_info["essence"],
                    key_advice=archetype_info["advice"]
                )
            )

        active_year = _ANNUAL_THEMES.get(py, "A year of meaningful evolution.")
        active_month = _MONTHLY_THEMES.get(pm, "A month of focused activity.")
        active_month_guidance = _MONTHLY_STRATEGIES.get(pm, "Align daily decisions with constructive focus.")
        target_month_name = MONTH_NAMES[target_month - 1] if 1 <= target_month <= 12 else f"Month {target_month}"

        # 12-Month Calendar Breakdown for Target Year
        all_twelve_months = []
        for m_idx in range(1, 13):
            cal_pm = digital_root(py + m_idx)
            m_days = calendar.monthrange(target_year, m_idx)[1]
            m_peak_dates = [d for d in range(1, m_days + 1) if digital_root(cal_pm + digital_root(d)) in (cal_pm, py)]
            all_twelve_months.append(
                MonthForecastDTO(
                    month_index=m_idx,
                    month_name=MONTH_NAMES[m_idx - 1],
                    personal_month_number=cal_pm,
                    monthly_theme=_MONTHLY_THEMES.get(cal_pm, "A month of progress."),
                    strategic_focus=_MONTHLY_STRATEGIES.get(cal_pm, "Focus on balanced growth."),
                    peak_launch_dates=m_peak_dates[:6]
                )
            )

        peak_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) in (py, pm)]

        deal_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) == 5]
        luxe_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) == 6]
        career_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) in (1, 8)]
        property_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) in (4, 8)]
        travel_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) in (5, 9)]
        restraint_dates = [d for d in range(1, num_days + 1) if pd_map.get(d) == 7]

        activity_guide = [
            ActivityRecommendationDTO(
                activity="🛍️ Shopping & Best Deals",
                best_dates=deal_dates,
                ideal_energy="Dynamic commercial clarity and sharp bargaining agility.",
                practical_advice="Ideal for electronics, comparing options, negotiating discounts, and discovering unexpected value."
            ),
            ActivityRecommendationDTO(
                activity="👗 Luxury, Beauty & Wardrobe",
                best_dates=luxe_dates,
                ideal_energy="Aesthetic appreciation, elegance, and harmonious satisfaction.",
                practical_advice="Perfect for clothing, jewelry, salon visits, and home decor. Approach with calm appreciation without over-spending."
            ),
            ActivityRecommendationDTO(
                activity="💼 Job Interviews, Executive Decisions & Authority",
                best_dates=career_dates,
                ideal_energy="High initiative, executive presence, and professional credibility.",
                practical_advice="Best for presentations, leadership meetings, pitching ideas, and signing career milestones."
            ),
            ActivityRecommendationDTO(
                activity="🏠 Property & Long-Term Real Estate Assets",
                best_dates=property_dates,
                ideal_energy="Structural stability, disciplined foundation, and enduring security.",
                practical_advice="Favorable for inspecting property, finalizing lease terms, and solidifying long-term financial plans."
            ),
            ActivityRecommendationDTO(
                activity="🚗 Vehicle Purchase & Travel Launches",
                best_dates=travel_dates,
                ideal_energy="Smooth movement, mobility, and safe completion of journeys.",
                practical_advice="Great for test-drives, servicing vehicles, booking trips, and launching long-distance travel."
            ),
            ActivityRecommendationDTO(
                activity="🧘 Days to Step Back & Avoid Rushed Arguments (Practice Restraint)",
                best_dates=restraint_dates,
                ideal_energy="Deep research, calm observation, and non-reactive poise.",
                practical_advice="Do not engage in petty arguments or rush into high-pressure deals on these days. Practice silence and observe."
            )
        ]

        roadmap_guidance = {
            1: "Focus on launching personal projects, taking independent leadership, and setting a brand new multi-year trajectory.",
            2: "Focus on deepening partnerships, emotional patience, active listening, and harmonious alliances.",
            3: "Focus on creative expansion, self-expression, joyful communication, and making space for new learning.",
            4: "Focus on disciplined work, organization, structural security, and solidifying physical/financial foundations.",
            5: "Focus on adaptability, travel, networking, business expansion, and embracing positive change.",
            6: "Focus on family harmony, domestic beauty, service, and nurturing commitments with grace and detachment.",
            7: "Focus on spiritual study, introspection, research, silence, and building internal resilience.",
            8: "Focus on executive leadership, career growth, material achievements, and establishing lasting value.",
            9: "Focus on completing long-standing responsibilities, forgiving old ties, and decluttering to prepare for a fresh cycle."
        }

        five_year_roadmap = []
        for offset in range(6):
            f_year = target_year + offset
            f_py = digital_root(digital_root(day) + digital_root(month) + digital_root(f_year))
            five_year_roadmap.append(
                YearForecastDTO(
                    year=f_year,
                    personal_year_number=f_py,
                    annual_theme=_ANNUAL_THEMES.get(f_py, "A year of meaningful evolution."),
                    guidance=roadmap_guidance.get(f_py, "Align with authentic growth.")
                )
            )

        ninety_min = (
            "Subconscious Reset Protocol: Biological emotional surges naturally reset in 90 minutes. "
            "If distress lingers beyond this, it is mental grasping onto past loops. Step back into neutral observation, "
            "and clear your 2GB mental space: let go of old mental clutter to welcome fresh opportunities."
        )

        # Missing Numbers & Behavioral Integration (Dormant Energies)
        missing_digits = [n for n in range(1, 10) if loshu_grid.get(str(n), 0) == 0]
        missing_numbers_activation = []
        for n in missing_digits:
            guideline = _MISSING_NUMBER_GUIDELINES.get(n)
            if guideline:
                missing_numbers_activation.append(
                    MissingNumberActivationDTO(
                        number=n,
                        planetary_ruler=guideline["ruler"],
                        dormant_quality=guideline["quality"],
                        behavioral_activation=guideline["activation"],
                        relational_balance_tip=guideline["relational_tip"]
                    )
                )

        return MeenaStoryReportResponse(
            core_nature_story=core_story,
            life_purpose_story=destiny_story,
            hidden_superpower=hidden_superpower,
            inner_test_to_master=inner_test,
            growth_blindspots=growth_blindspots,
            missing_numbers_activation=missing_numbers_activation,
            name_vibrations=name_vibrations,
            life_chapters=life_chapters,
            active_year_theme=active_year,
            target_month_index=target_month,
            target_month_name=target_month_name,
            active_month_theme=active_month,
            active_month_guidance=active_month_guidance,
            all_twelve_months=all_twelve_months,
            peak_launch_dates=peak_dates[:6],
            five_year_roadmap=five_year_roadmap,
            activity_guide=activity_guide,
            ninety_minute_rule_reminder=ninety_min,
            calculation_audit=calculation_audit
        )

    @classmethod
    def get_help_concepts(cls) -> MeenaHelpResponse:
        overview = (
            "Meena's Numerology Method is an empowering, holistic framework that combines ancient sound vibrations "
            "with cognitive psychology. It helps you understand your natural strengths, navigate life chapters, "
            "and identify optimal timing for daily decisions without superstition or fear."
        )

        concepts = [
            HelpConceptDTO(
                concept="🧠 The 2GB Mental Space Principle",
                explanation="Your subconscious bandwidth operates like a 2GB memory card. When storage is clogged with past grievances and worry loops, there is no bandwidth left to download fresh wealth opportunities, creative insights, or serendipitous timing.",
                practical_takeaway="Actively clear mental clutter. Forgive old loops to free up the 2GB space needed to attract new lucky outcomes."
            ),
            HelpConceptDTO(
                concept="⏳ The 90-Minute Emotional Mastery Rule",
                explanation="Biologically, an emotional surge has a neurochemical lifespan of 90 minutes. If distress lasts for hours or days, it is conscious mental grasping onto the story.",
                practical_takeaway="Give yourself a strict 90-minute window to observe an emotion neutrally without making high-stakes decisions. Then step forward with clarity."
            ),
            HelpConceptDTO(
                concept="🗣️ Sound Vibration vs. Spelling Tricks",
                explanation="Adding silent extra letters to a name without changing how it is spoken aloud does not alter the physical sound frequency you emit. The atmosphere and people respond to spoken sound resonance.",
                practical_takeaway="Focus on how your daily calling name resonates and align it with authentic behavioral karma."
            ),
            HelpConceptDTO(
                concept="🌿 Instinctive Core Nature (Birth Day)",
                explanation="The day of the month you were born represents your baseline operating style, your natural temperament, and how you react spontaneously.",
                practical_takeaway="Understand your core nature so you can leverage your natural strengths without fighting against your authentic self."
            ),
            HelpConceptDTO(
                concept="🧭 Overarching Life Purpose (Destiny)",
                explanation="Calculated from your entire birth date, this represents the overarching skill-set and lessons that your life experiences are constantly shaping you to master.",
                practical_takeaway="Align major career and lifestyle milestones with this long-term current to experience natural momentum."
            ),
            HelpConceptDTO(
                concept="📖 Four Major Life Chapters",
                explanation="Human lives unfold in four distinct developmental seasons (Pinnacles), each with a specific developmental theme and strategic focus.",
                practical_takeaway="Navigate each chapter according to its seasonal demand (building, quiet reflection, or wisdom sharing)."
            )
        ]

        return MeenaHelpResponse(
            method_overview=overview,
            concepts=concepts
        )
