from datetime import datetime
"""
Pydantic Schemas for Meena's Numerology Engine in AstroOS.
User-facing schemas include transparent, step-by-step mathematical calculation derivations,
Vedic / Loshu 3x3 number grid, and complete daily personal cycle maps.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class MeenaNumerologyRequest(BaseModel):
    day: int = Field(..., ge=1, le=31, description="Day of birth (1-31)")
    month: int = Field(..., ge=1, le=12, description="Month of birth (1-12)")
    year: int = Field(..., ge=1800, le=2200, description="Year of birth")
    full_name: str = Field(
        ..., min_length=1,
        pattern=r'^[A-Za-z\s\.\-\']+$',
        description="Full official / legal document name (e.g. Bhagia Meena Rajesh)"
    )
    public_name: Optional[str] = Field(None, description="Public / social / professional name (e.g. Meena Bhagia)")
    daily_name: Optional[str] = Field(None, description="Daily calling / spoken / pet name (e.g. Meena)")
    target_year: Optional[int] = Field(
        default_factory=lambda: datetime.now().year,
        ge=1800, le=2200,
        description="Target year for annual/monthly timing"
    )
    target_month: Optional[int] = Field(
        default_factory=lambda: datetime.now().month,
        ge=1, le=12,
        description="Target month (1-12)"
    )


class LifeChapterDTO(BaseModel):
    chapter_index: int = Field(description="1 to 4")
    age_span: str = Field(description="e.g. 'Age 0 to 31'")
    pinnacle_number: int = Field(description="Pinnacle calculation number (1-9)")
    challenge_number: int = Field(description="Challenge calculation number (0-9)")
    chapter_title: str = Field(description="Engaging title, e.g. 'The Foundation & Effort Chapter'")
    description: str = Field(description="Story-driven explanation of this life stage")
    key_advice: str = Field(description="Actionable behavioral guidance")


class ActivityRecommendationDTO(BaseModel):
    activity: str = Field(description="e.g. 'Shopping & Best Deals', 'Job Interview', 'Property Purchase'")
    best_dates: List[int] = Field(description="List of best calendar dates in the selected month")
    ideal_energy: str = Field(description="Why these dates work (jargon-free)")
    practical_advice: str = Field(description="Strategic actionable advice")


class NameVibrationStoryDTO(BaseModel):
    name_type: str = Field(description="Daily Spoken / Public Social / Legal Document")
    name_value: str = Field(description="The name text")
    chaldean_compound: int = Field(description="Raw Chaldean sum (e.g. 10, 20, 33, 50)")
    chaldean_reduced: int = Field(description="Single-digit Chaldean vibration (1-8; 9 possible as compound reduction)")
    pythagorean_compound: int = Field(description="Raw Pythagorean sum (e.g. 73, 44, 18)")
    pythagorean_reduced: int = Field(description="Single-digit Pythagorean vibration (1-9)")
    vibrational_essence: str = Field(description="Emotional / social / commercial impact")
    strategic_note: str = Field(description="Practical advisory on this name vibration")


class YearForecastDTO(BaseModel):
    year: int = Field(description="Calendar year (e.g. 2026)")
    personal_year_number: int = Field(description="1 to 9")
    annual_theme: str = Field(description="Theme name with icon")
    guidance: str = Field(description="Story-driven strategic focus for this year")


class MonthForecastDTO(BaseModel):
    month_index: int = Field(description="1 to 12")
    month_name: str = Field(description="January to December")
    personal_month_number: int = Field(description="1 to 9")
    monthly_theme: str = Field(description="Theme name with icon")
    strategic_focus: str = Field(description="Practical focus for this specific month")
    peak_launch_dates: List[int] = Field(description="Peak alignment dates in this month")


class GrowthBlindspotDTO(BaseModel):
    blindspot_title: str = Field(description="Constructive title of the shadow pattern")
    tendency_description: str = Field(description="Diplomatic breakdown of the negative habit / overreaction")
    corrective_action: str = Field(description="Concrete behavioral correction required for success")


class LetterValDTO(BaseModel):
    char: str
    chaldean_val: int
    pythagorean_val: int
    is_vowel: bool


class NameLayerAuditDTO(BaseModel):
    layer_name: str
    raw_name: str
    letters: List[LetterValDTO]
    chaldean_formula: str
    chaldean_raw_sum: int
    chaldean_reduced: int
    pythagorean_formula: str
    pythagorean_raw_sum: int
    pythagorean_reduced: int
    soul_urge_formula: Optional[str] = None
    soul_urge_number: Optional[int] = None
    personality_formula: Optional[str] = None
    personality_number: Optional[int] = None


class DayEnergyDTO(BaseModel):
    date: int
    day_of_week: str
    personal_month_number: int
    day_root: int
    personal_date_number: int
    dominant_category: str
    category_icon: str
    calculation_formula: str
    is_peak_date: bool


class CalculationAuditDTO(BaseModel):
    moolank_number: int
    moolank_compound: int
    moolank_formula: str
    bhagyank_number: int
    bhagyank_compound: int
    bhagyank_formula: str
    soul_urge_number: int
    soul_urge_compound: int
    personality_number: int
    personality_compound: int
    maturity_number: Optional[int] = Field(None, description="Activates at age 40, dominant after 50: Name Number + Destiny Number")
    maturity_formula: Optional[str] = None
    balance_number: Optional[int] = Field(None, description="Sum of name initials: personality & family balance")
    balance_formula: Optional[str] = None
    hidden_passion_number: Optional[int] = Field(None, description="Most frequently repeated number in full name letters")
    hidden_passion_formula: Optional[str] = None
    names_breakdown: List[NameLayerAuditDTO]
    loshu_grid: Dict[str, int] = Field(description="Counts of each digit 1-9 in DOB + Core numbers")
    challenge_c1_formula: str
    challenge_c2_formula: str
    challenge_primary_c3_formula: str
    challenge_c4_formula: str
    first_pinnacle_age_formula: str
    pinnacle_p1_formula: str
    pinnacle_p2_formula: str
    pinnacle_p3_formula: str
    pinnacle_p4_formula: str
    personal_year_formula: str
    personal_month_formula: str
    personal_date_formula_sample: str
    month_calendar_days: List[DayEnergyDTO] = Field(description="Day-by-day calculated energies for all days in the target month")


class MissingNumberActivationDTO(BaseModel):
    number: int
    planetary_ruler: str
    dormant_quality: str
    behavioral_activation: str
    relational_balance_tip: str


class MeenaStoryReportResponse(BaseModel):
    core_nature_story: str = Field(description="Your instinctive nature & emotional baseline")
    life_purpose_story: str = Field(description="Your overarching destiny & life mission")
    hidden_superpower: str = Field(description="Deep inner strength & ambition")
    inner_test_to_master: str = Field(description="Core life lesson / emotional boundary test")
    growth_blindspots: List[GrowthBlindspotDTO] = Field(description="Diplomatic analysis of shadow patterns & necessary corrections")
    missing_numbers_activation: List[MissingNumberActivationDTO] = Field(default_factory=list, description="How to activate dormant energies of missing numbers through behavioral karma")
    name_vibrations: List[NameVibrationStoryDTO]
    life_chapters: List[LifeChapterDTO]
    active_year_theme: str = Field(description="Timing theme for the selected year")
    target_month_index: int = Field(description="Selected evaluation month (1-12)")
    target_month_name: str = Field(description="e.g. September")
    active_month_theme: str = Field(description="Timing theme for the selected month")
    active_month_guidance: str = Field(description="Strategic actionable guidance for this month")
    all_twelve_months: List[MonthForecastDTO] = Field(description="Complete 12-month calendar breakdown for the target year")
    peak_launch_dates: List[int] = Field(description="Highest priority dates in the selected month")
    five_year_roadmap: List[YearForecastDTO] = Field(description="5-Year upcoming trajectory and themes")
    activity_guide: List[ActivityRecommendationDTO]
    ninety_minute_rule_reminder: str = Field(description="Reminder on natural emotional resets")
    calculation_audit: CalculationAuditDTO = Field(description="Detailed step-by-step mathematical derivations and formulas")


class ActivityFinderRequest(BaseModel):
    day: int = Field(..., ge=1, le=31, description="Day of birth (1-31)")
    month: int = Field(..., ge=1, le=12, description="Month of birth (1-12)")
    year: Optional[int] = Field(None, ge=1800, le=2200, description="Optional year of birth")
    target_year: Optional[int] = Field(
        default_factory=lambda: datetime.now().year,
        ge=1800, le=2200,
        description="Target year (defaults to current year)"
    )
    target_month: int = Field(..., ge=1, le=12, description="Target month (1-12)")
    activity_category: str = Field(
        ..., min_length=1,
        description="shopping_deals | luxury_beauty | career_interview | property_assets | vehicle_travel | legal_contracts | family_resolution"
    )


class ActivityFinderResponse(BaseModel):
    activity_category: str
    target_month: int
    target_year: int
    recommended_dates: List[int]
    reasoning: str
    actionable_advice: str


class RepeatedNumberScanRequest(BaseModel):
    sequence: str = Field(
        ...,
        min_length=1,
        pattern=r'^[0-9:\s]+$',
        description="Repeated sequence of identical digits (e.g. 111, 333, 7777)"
    )
    day: Optional[int] = Field(None, ge=1, le=31, description="Optional Birth Day for personal interaction synthesis")
    month: Optional[int] = Field(None, ge=1, le=12, description="Optional Birth Month")
    year: Optional[int] = Field(None, ge=1800, le=2200, description="Optional Birth Year")
    target_year: Optional[int] = Field(
        default_factory=lambda: datetime.now().year,
        ge=1800, le=2200,
        description="Optional target year for Personal Year interaction"
    )


class RepeatedNumberScanResponse(BaseModel):
    sequence: str
    digit_count: int
    signal_status: str
    is_favorable: bool
    subconscious_signal: str
    psychological_meaning: str
    personal_resonance: Optional[str] = None
    personal_custom_guidance: Optional[str] = None
    actionable_directive: str
    shadow_warning: str


class HelpConceptDTO(BaseModel):
    concept: str
    explanation: str
    practical_takeaway: str


class MeenaHelpResponse(BaseModel):
    method_overview: str
    concepts: List[HelpConceptDTO]
