'use client';

import React, { useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';
import { useCurrentUser } from '@/lib/auth';
import { fetchDashboardSummary, type DashboardSummary } from '@/lib/billing';
import { useActiveChart } from '@/lib/charts';
import { ActiveChartSelectorModal } from '@/components/layout/ActiveChartSelectorModal';
import Link from 'next/link';

// Lightweight Zero-Dependency SVG Icons
const SunIcon = () => (
  <svg className="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="5" strokeWidth="2" stroke="currentColor" fill="#FEF3C7" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
  </svg>
);

const KetuIcon = () => (
  <svg className="w-6 h-6 text-slate-700 dark:text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="9" strokeWidth="2" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 7v10m-4-5l4 4 4-4m-4-9a2 2 0 100 4 2 2 0 000-4z" />
  </svg>
);

const SaturnIcon = () => (
  <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="6" strokeWidth="2" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 12c0-4.418 8-8 16-8m-16 8c0 4.418 8 8 16 8" />
  </svg>
);

const MercuryIcon = () => (
  <svg className="w-6 h-6 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <circle cx="12" cy="13" r="5" strokeWidth="2" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8V3m0 0a4 4 0 00-4 4m4-4a4 4 0 014 4m-4 11v4m-3-2h6" />
  </svg>
);

const EditIcon = () => (
  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
  </svg>
);

const RefreshIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

const EyeIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
);

const GridIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <rect x="3" y="3" width="7" height="7" rx="1" strokeWidth="2" />
    <rect x="14" y="3" width="7" height="7" rx="1" strokeWidth="2" />
    <rect x="14" y="14" width="7" height="7" rx="1" strokeWidth="2" />
    <rect x="3" y="14" width="7" height="7" rx="1" strokeWidth="2" />
  </svg>
);

const CalendarIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" strokeWidth="2"/>
    <line x1="16" y1="2" x2="16" y2="6" strokeWidth="2"/>
    <line x1="8" y1="2" x2="8" y2="6" strokeWidth="2"/>
    <line x1="3" y1="10" x2="21" y2="10" strokeWidth="2"/>
  </svg>
);

const HardDriveIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <rect x="2" y="2" width="20" height="8" rx="2" ry="2" strokeWidth="2" />
    <rect x="2" y="14" width="20" height="8" rx="2" ry="2" strokeWidth="2" />
    <line x1="6" y1="6" x2="6.01" y2="6" strokeWidth="3" strokeLinecap="round" />
    <line x1="6" y1="18" x2="6.01" y2="18" strokeWidth="3" strokeLinecap="round" />
  </svg>
);

// Types
interface LifeChapter {
  chapter_index: number;
  age_span: string;
  pinnacle_number: number;
  challenge_number: number;
  chapter_title: string;
  description: string;
  key_advice: string;
}

interface ActivityRecommendation {
  activity: string;
  best_dates: number[];
  ideal_energy: string;
  practical_advice: string;
}

interface NameVibration {
  name_type: string;
  name_value: string;
  chaldean_compound: number;
  chaldean_reduced: number;
  pythagorean_compound: number;
  pythagorean_reduced: number;
  vibrational_essence: string;
  strategic_note: string;
}

interface YearForecast {
  year: number;
  personal_year_number: number;
  annual_theme: string;
  guidance: string;
}

interface MonthForecast {
  month_index: number;
  month_name: string;
  personal_month_number: number;
  monthly_theme: string;
  strategic_focus: string;
  peak_launch_dates: number[];
}

interface GrowthBlindspot {
  blindspot_title: string;
  tendency_description: string;
  corrective_action: string;
}

interface LetterVal {
  char: string;
  chaldean_val: number;
  pythagorean_val: number;
  is_vowel: boolean;
}

interface NameLayerAudit {
  layer_name: string;
  raw_name: string;
  letters: LetterVal[];
  chaldean_formula: string;
  chaldean_raw_sum: number;
  chaldean_reduced: number;
  pythagorean_formula: string;
  pythagorean_raw_sum: number;
  pythagorean_reduced: number;
  soul_urge_formula?: string;
  soul_urge_number?: number;
  personality_formula?: string;
  personality_number?: number;
}

interface DayEnergy {
  date: number;
  day_of_week: string;
  personal_month_number: number;
  day_root: number;
  personal_date_number: number;
  dominant_category: string;
  category_icon: string;
  calculation_formula: string;
  is_peak_date: boolean;
}

interface CalculationAudit {
  moolank_number: number;
  moolank_compound: number;
  moolank_formula: string;
  bhagyank_number: number;
  bhagyank_compound: number;
  bhagyank_formula: string;
  soul_urge_number: number;
  soul_urge_compound: number;
  personality_number: number;
  personality_compound: number;
  names_breakdown: NameLayerAudit[];
  loshu_grid: Record<string, number>;
  challenge_c1_formula: string;
  challenge_c2_formula: string;
  challenge_primary_c3_formula: string;
  challenge_c4_formula: string;
  first_pinnacle_age_formula: string;
  pinnacle_p1_formula: string;
  pinnacle_p2_formula: string;
  pinnacle_p3_formula: string;
  pinnacle_p4_formula: string;
  personal_year_formula: string;
  personal_month_formula: string;
  personal_date_formula_sample: string;
  month_calendar_days: DayEnergy[];
}

interface MissingNumberActivation {
  number: number;
  planetary_ruler: string;
  dormant_quality: string;
  behavioral_activation: string;
  relational_balance_tip: string;
}

interface LetterValDTO {
  char: string;
  position: number;
  chaldean_val: number;
  pythagorean_val: number;
  is_vowel: boolean;
  contribution_chaldean: number;
  contribution_pythagorean: number;
}

interface NameLayerAuditDTO {
  layer_name: string;
  source_name: string;
  chaldean_compound: number;
  chaldean_reduced: number;
  chaldean_formula: string;
  pythagorean_compound: number;
  pythagorean_reduced: number;
  pythagorean_formula: string;
  letters: LetterValDTO[];
}

interface DayEnergyDTO {
  date: number;
  day_of_week: string;
  personal_month_number: number;
  day_root: number;
  personal_date_number: number;
  dominant_category: string;
  category_icon: string;
  calculation_formula: string;
  is_peak_date: boolean;
}

interface GrowthBlindspotDTO {
  blindspot_title: string;
  tendency_description: string;
  corrective_action: string;
}

interface MissingNumberActivationDTO {
  number: number;
  planetary_ruler: string;
  dormant_quality: string;
  behavioral_activation: string;
  relational_balance_tip: string;
}

interface ActivityRecommendationDTO {
  activity: string;
  best_dates: number[];
  ideal_energy: string;
  practical_advice: string;
}

interface NameVibrationStoryDTO {
  name_type: string;
  name_value: string;
  chaldean_compound: number;
  chaldean_reduced: number;
  pythagorean_compound: number;
  pythagorean_reduced: number;
  vibrational_essence: string;
  strategic_note: string;
}

interface LifeChapterDTO {
  chapter_index: number;
  age_span: string;
  pinnacle_number: number;
  challenge_number: number;
  chapter_title: string;
  description: string;
  key_advice: string;
}

interface YearForecastDTO {
  year: number;
  personal_year_number: number;
  annual_theme: string;
  guidance: string;
}

interface MonthForecastDTO {
  month_index: number;
  month_name: string;
  personal_month_number: number;
  monthly_theme: string;
  strategic_focus: string;
  peak_launch_dates: number[];
}

interface CalculationAuditDTO {
  moolank_number: number;
  moolank_compound: number;
  moolank_formula: string;
  bhagyank_number: number;
  bhagyank_compound: number;
  bhagyank_formula: string;
  soul_urge_number: number;
  soul_urge_compound: number;
  personality_number: number;
  personality_compound: number;
  maturity_number?: number;
  maturity_formula?: string;
  balance_number?: number;
  balance_formula?: string;
  hidden_passion_number?: number;
  hidden_passion_formula?: string;
  names_breakdown: NameLayerAuditDTO[];
  loshu_grid: Record<string, number>;
  challenge_c1_formula: string;
  challenge_c2_formula: string;
  challenge_primary_c3_formula: string;
  challenge_c4_formula: string;
  first_pinnacle_age_formula: string;
  pinnacle_p1_formula: string;
  pinnacle_p2_formula: string;
  pinnacle_p3_formula: string;
  pinnacle_p4_formula: string;
  personal_year_formula: string;
  personal_month_formula: string;
  personal_date_formula_sample: string;
  month_calendar_days: DayEnergyDTO[];
}


interface HiddenPassionDetail {
  planet: string;
  hindiTitle: string;
  icon: string;
  coreDrive: string;
  superpower: string;
  repetitionRule: string;
  shadowWarning: string;
}

const HIDDEN_PASSION_GUIDE: Record<number, HiddenPassionDetail> = {
  1: {
    planet: '☀️ सूर्य (Sun)',
    hindiTitle: 'स्वतंत्र नेतृत्व व मौलिकता (Independent Leadership)',
    icon: '☀️',
    coreDrive: 'अपनी खुद की पहचान बनाना, प्रथम आना और किसी के अधीन काम न करने का आंतरिक स्वाभिमान।',
    superpower: 'Pioneering courage, decisive initiative, confidence, original vision.',
    repetitionRule: '1x = सामान्य उपस्थिति | 2x = 50% क्षमता | 3x = 100% सर्वोत्तम नेतृत्व | 4x+ = अत्यधिक अहंकार व हठ।',
    shadowWarning: 'अहंकार ("मैं ही हूँ"), दूसरों पर अपनी बात थोपना, और अनावश्यक अकेलापन।'
  },
  2: {
    planet: '🌙 चंद्र (Moon)',
    hindiTitle: 'शांति, कूटनीति व संवेदनशीलता (Diplomacy & Empathy)',
    icon: '🌙',
    coreDrive: 'लोगों को आपस में जोड़ना, सामंजस्य बनाना और पर्दे के पीछे रहकर मुख्य लीडर को अटूट समर्थन देना।',
    superpower: 'Intuitive empathy, emotional listening, diplomatic mediation, team collaboration.',
    repetitionRule: '1x = सामान्य उपस्थिति | 2x = 50% क्षमता | 3x = 100% शिखर कूटनीति | 4x+ = निर्णयहीनता व भावनात्मक निर्भरता।',
    shadowWarning: 'निर्णय दूसरों पर टालना (दोष से बचने के लिए) और हर 90 मिनट में मूड बदलना।'
  },
  3: {
    planet: '✨ गुरु (Jupiter)',
    hindiTitle: 'रचनात्मक अभिव्यक्ति व ज्ञान (Creative Expansion)',
    icon: '✨',
    coreDrive: 'ज्ञान और कला को दूसरों के साथ साझा करना, बोलना, लिखना, और जीवन में नई संभावनाओं के लिए स्पेस बनाना।',
    superpower: 'Wisdom sharing, inspiring speech, artistic optimism, teaching, creative expansion.',
    repetitionRule: '1x = सामान्य उपस्थिति | 2x = 50% क्षमता | 3x = 100% अभिव्यक्ति सिद्धि | 4x+ = हर चीज़ में अति (बोलना, खाना)।',
    shadowWarning: 'बिखराव (Scattered focus), अति-आशावाद, और ज्ञान को क्रियान्वित न करना।'
  },
  4: {
    planet: '⚡ राहु (Rahu)',
    hindiTitle: 'संरचना, अनुशासन व इनोवेशन (Structural Innovation)',
    icon: '⚡',
    coreDrive: 'पिकासो की तरह पुरानी व्यवस्था को नए अपरंपरागत तरीके से ढालना, तकनीकी और व्यावहारिक अनुशासन।',
    superpower: 'Groundbreaking innovation, methodical resilience, practical discipline, system redesign.',
    repetitionRule: '1x = सामान्य उपस्थिति | 2x = 50% क्षमता | 3x = 100% मास्टर स्ट्रक्चर | 4x+ = बेचैनी व काम अधूरा छोड़ना।',
    shadowWarning: 'रूढ़ियों में दम घुटना (Suffocation), अस्थिरता, और अचानक काम बीच में छोड़ देना।'
  },
  5: {
    planet: '💬 बुध (Mercury)',
    hindiTitle: 'व्यापार, चपलता व स्वतंत्रता (Dynamic Adaptability)',
    icon: '💬',
    coreDrive: 'तेज़ गति से संवाद, व्यापारिक अवसर पकड़ना, नई तकनीक व यात्रा का आनंद लेना, और त्वरित निर्णय।',
    superpower: 'Sharp commercial acumen, rapid learning, networking agility, versatile communication.',
    repetitionRule: '1x = सामान्य उपस्थिति | 2x = 50% क्षमता | 3x = 100% सर्वोत्तम चपलता (Sweet Spot) | 4x+ = ओवरथिंकिंग व नर्वसनेस।',
    shadowWarning: 'ओवर-प्लानिंग (ट्रेन छूटने तक सोचना), बेचैनी, और एक समय पर बहुत सारे काम फैलाना।'
  },
  6: {
    planet: '💎 शुक्र (Venus)',
    hindiTitle: 'सौंदर्य, पोषण व सामंजस्य (Harmonious Grace)',
    icon: '💎',
    coreDrive: 'घर और परिवेश में समरूपता (Symmetry) और लालित्य लाना, निःस्वार्थ प्रेम और दूसरों का पोषण करना।',
    superpower: 'Aesthetic elegance, domestic harmony, mentoring, love with healthy detachment.',
    repetitionRule: '1x = सामान्य उपस्थिति | 2x = 50% क्षमता | 3x = 100% कलात्मक अनुग्रह | 4x+ = अति-आसक्ति व दिखावा।',
    shadowWarning: 'अति-आसक्ति (फेविकॉल चिपकन), अपेक्षाएं बांधना, और दिखावे (Vanity) में धन व्यय करना।'
  },
  7: {
    planet: '🧘 केतु (Ketu)',
    hindiTitle: 'गहन शोध, एकांत व सत्य-खोज (Higher Intuition & Silence)',
    icon: '🧘',
    coreDrive: 'सतही शोर से दूर होकर गहराई में जाना, उच्च अंतर्ज्ञान (Higher Intuition), मौन और परम तटस्थता।',
    superpower: 'Distraction-free research, strategic stillness, non-reactivity, higher intuitive wisdom.',
    repetitionRule: '1x = सामान्य उपस्थिति | 2x = 50% क्षमता | 3x = 100% आंतरिक सिद्धि | 4x+ = अत्यधिक अलगाव व असंतोष।',
    shadowWarning: 'अकेलापन ("दुनिया भाड़ में जाए"), जीवन से निरंतर असंतोष, और लोगों से कटना।'
  },
  8: {
    planet: '👑 शनि (Saturn)',
    hindiTitle: 'कार्यकारी अधिकार व संपत्ति (Executive Mastery & Wealth)',
    icon: '👑',
    coreDrive: 'सच्चा भौतिक धन व संस्थागत साम्राज्य खड़ा करना — "लक्ष्मी चाहिए तो विष्णु जैसा संयमित चरित्र बनाओ।"',
    superpower: 'Executive endurance, resource management, enduring generational wealth, structural mastery.',
    repetitionRule: '1x = सामान्य उपस्थिति | 2x = 50% क्षमता | 3x = 100% अचल संपत्ति व सिद्धि | 4x+ = भय, निराशा व काम बीच में छोड़ना।',
    shadowWarning: 'अत्यधिक कठोरता, काम बीच में छोड़ने की निराशा, और केवल परिणामों से खुद को तौलना।'
  },
  9: {
    planet: '🔥 मंगल (Mars)',
    hindiTitle: 'साहस, रक्षा व चक्र-पूर्णता (Courageous Culmination)',
    icon: '🔥',
    coreDrive: 'चुनौतियों से न डरना, बड़े मिशन पूरे करना, कमजोरों की रक्षा करना और कृतज्ञता के साथ चक्र पूर्ण करना।',
    superpower: 'Protective strength, transformative action, mission completion, fearless determination.',
    repetitionRule: '1x = सामान्य उपस्थिति | 2x = 50% क्षमता | 3x = 100% सुरक्षित विजय | 4x+ = क्रोध, आवेश व अनावश्यक विवाद।',
    shadowWarning: 'आवेश में बिना सोचे कूदना, क्रोध, और अनावश्यक संघर्षों में अपनी ऊर्जा बर्बाद करना।'
  }
};


interface NumberInspectorData {
  title: string;
  badge: string;
  number: number;
  planet: string;
  icon: string;
  formula: string;
  explanation: string;
  meaning: string;
  actionDirective: string;
  warningNotice?: string;
}

const NUMBER_ARCHETYPE_DETAILS: Record<number, { planet: string; icon: string; theme: string; meaning: string; advice: string; warning: string }> = {
  1: {
    planet: '☀️ सूर्य (Sun)',
    icon: '☀️',
    theme: 'नई शुरुआत, स्वतंत्र नेतृत्व व मौलिक पहचान (New Beginnings & Leadership)',
    meaning: 'नौ-वर्षीय चक्र का प्रथम वर्ष या दिन — पुराने को पीछे छोड़कर नए प्रोजेक्ट्स, स्वतंत्र निर्णय और अपनी अलग पहचान बनाने का समय।',
    advice: 'पहल करें, नए काम की नींव रखें, और दूसरों की अनुमति का इंतजार किए बिना आगे बढ़ें।',
    warning: 'अहंकार, हठ, और जल्दबाजी में दूसरों की सलाह की अनदेखी करने से बचें।'
  },
  2: {
    planet: '🌙 चंद्र (Moon)',
    icon: '🌙',
    theme: 'शांति, कूटनीति, संबंध व संवेदनशीलता (Diplomacy, Cooperation & Patience)',
    meaning: 'सहयोग, सक्रिय श्रवण और संबंधों को गहरा करने का समय। इसमें बीज जमीन के नीचे चुपचाप अंकुरित होता है।',
    advice: 'धैर्य रखें, दूसरों के साथ साझेदारी बनाएं, और 90-मिनट के भावनात्मक रीसेट का पालन करें।',
    warning: 'निर्णयहीनता (दोष से बचने के लिए) और दूसरों की नकारात्मक भावनाओं को खुद पर लेने से बचें।'
  },
  3: {
    planet: '✨ गुरु (Jupiter)',
    icon: '✨',
    theme: 'रचनात्मकता, ज्ञान, अभिव्यक्ति व सामाजिक विस्तार (Creative Expression & Wisdom)',
    meaning: 'अपनी आवाज और ज्ञान को साझा करने, कलात्मक रुचियों के लिए समय/स्पेस बनाने और आशावाद का समय।',
    advice: 'लिखें, बोलें, प्रेजेंटेशन दें, और नई रचनात्मक संभावनाओं के लिए कैलेंडर में जगह बनाएं।',
    warning: 'बिखराव (Scattered energy), हर चीज में अति (बोलना, खाना), और काम अधूरा छोड़ना।'
  },
  4: {
    planet: '⚡ राहु (Rahu)',
    icon: '⚡',
    theme: 'संरचना, अनुशासन, इनोवेशन व आधार निर्माण (Structural Foundation & Routine)',
    meaning: 'पिकासो की तरह पुरानी व्यवस्था को नए तरीके से ढालना — डाइट, बजट, वित्तीय नींव और व्यावहारिक अनुशासन।',
    advice: 'सिस्टम बनाएं, कार्यप्रणाली को व्यवस्थित करें, और आधारभूत विवरणों पर ध्यान दें।',
    warning: 'रूढ़ियों में दम घुटना (Suffocation), काम बीच में छोड़ना, और अत्यधिक वित्तीय चिंता।'
  },
  5: {
    planet: '💬 बुध (Mercury)',
    icon: '💬',
    theme: 'बदलाव, व्यापार, यात्रा व चपलता (Dynamic Adaptability, Deals & Freedom)',
    meaning: 'तेज गति से नए अवसर, व्यापारिक डील्स, नेटवर्किंग, यात्रा और बदलाव को अपनाने का समय।',
    advice: 'सकारात्मक बदलाव को अपनाएं, डील्स की तुलना करें, और लचीलेपन के साथ आगे बढ़ें।',
    warning: 'ओवर-प्लानिंग (ट्रेन छूटने तक सोचते रहना), बेचैनी, और एक साथ बहुत काम फैलाना।'
  },
  6: {
    planet: '💎 शुक्र (Venus)',
    icon: '💎',
    theme: 'परिवार, सौंदर्य, लालित्य व सामंजस्य (Family, Aesthetic Grace & Detached Love)',
    meaning: 'घर, विवाह, सौंदर्य, घरेलू शांति और दूसरों की निःस्वार्थ सेवा करने का समय।',
    advice: 'घर और कार्यक्षेत्र में समरूपता लाएं, संबंधों में प्रेम और डिटैचमेंट बनाए रखें।',
    warning: 'अति-आसक्ति (फेविकॉल चिपकन), दिखावे (Vanity) में अत्यधिक खर्च, और जबरन दूसरों को सुधारने की कोशिश।'
  },
  7: {
    planet: '🧘 केतु (Ketu)',
    icon: '🧘',
    theme: 'आत्म-अध्ययन, मौन, उच्च अंतर्ज्ञान व शोध (Silence, Higher Intuition & Study)',
    meaning: 'सतही शोर से हटकर गहराई में उतरने, मौन रहने, और बिना किसी प्रतिक्रिया के साक्षी भाव रखने का समय।',
    advice: 'एकांत में अध्ययन और रिसर्च करें, मौन रहें, और अनावश्यक विवादों से हाथ रोक कर रखें।',
    warning: 'अकेलापन ("दुनिया भाड़ में जाए"), निरंतर असंतोष, और लोगों से कटना।'
  },
  8: {
    planet: '👑 शनि (Saturn)',
    icon: '👑',
    theme: 'करियर, भौतिक संपत्ति व दायित्व (Executive Authority & Real Wealth)',
    meaning: 'सच्चा भौतिक धन और संस्थागत अधिकार पाने का समय — "लक्ष्मी चाहिए तो विष्णु जैसा संयमित चरित्र बनाओ।"',
    advice: 'व्यावसायिक निर्णय लें, संपत्ति के अनुबंध फाइनल करें, और बड़े दायित्व को कुशलता से संभालें।',
    warning: 'भय, निराशावाद, काम बीच में छोड़ना, और केवल परिणाम से खुद को तौलना।'
  },
  9: {
    planet: '🔥 मंगल (Mars)',
    icon: '🔥',
    theme: 'विसर्जन, चक्र-पूर्णता व सुरक्षित समाप्ति (Culmination, Releasing Baggage & Gratitude)',
    meaning: '9-वर्षीय या मासिक चक्र का अंतिम चरण — पुराने कर्जों, क्लेशों और怨 को विसर्जित कर 2GB मेमोरी खाली करने का समय।',
    advice: 'खुले मामलों को बंद करें, क्षमा और कृतज्ञता के साथ आगे बढ़ें, और नए चक्र के लिए जगह बनाएं।',
    warning: 'पुरानी बातों को पकड़ कर बैठे रहना, क्रोध, और आवेश में बिना सोचे प्रतिक्रिया देना।'
  }
};

interface StoryReport {
  core_nature_story: string;
  life_purpose_story: string;
  hidden_superpower: string;
  inner_test_to_master: string;
  growth_blindspots: GrowthBlindspotDTO[];
  missing_numbers_activation?: MissingNumberActivationDTO[];
  name_vibrations: NameVibrationStoryDTO[];
  life_chapters: LifeChapterDTO[];
  active_year_theme: string;
  target_month_index: number;
  target_month_name: string;
  active_month_theme: string;
  active_month_guidance: string;
  all_twelve_months: MonthForecastDTO[];
  peak_launch_dates: number[];
  five_year_roadmap: YearForecastDTO[];
  activity_guide: ActivityRecommendationDTO[];
  ninety_minute_rule_reminder: string;
  calculation_audit: CalculationAuditDTO;
}

interface RepeatedNumberResult {
  sequence: string;
  digit_count: number;
  signal_status: string;
  is_favorable: boolean;
  subconscious_signal: string;
  psychological_meaning: string;
  personal_resonance?: string;
  personal_custom_guidance?: string;
  actionable_directive: string;
  shadow_warning: string;
}

// Classical Planetary Archetypes & Core Principles in Simple Conversational Language
interface ArchetypeDetail {
  num: number;
  planet: string;
  symbol?: string;
  archetype: string;
  principle: string;
  storyLines: string[];
  takeaway: string;
}

const PLANETARY_MAPPING: ArchetypeDetail[] = [
  {
    num: 0,
    planet: "Unmanifest Source",
    symbol: "⚪",
    archetype: "Kālī",
    principle: "Void & Dissolution",
    storyLines: [
      "Have you ever noticed how a computer becomes slow when it is filled with too many old and unnecessary files?",
      "Our mind works the same way.",
      "Past experiences, grudges, worries, and old stories take up mental space. Sometimes, instead of adding something new, we simply need to clear some space.",
      "Think of your mind as having 2 GB of mental space.",
      "What old thought are you still carrying that you no longer need?",
      "Let it go. Let the old story dissolve. Make some space."
    ],
    takeaway: "When the old clears, there is room for something new to emerge."
  },
  {
    num: 1,
    planet: "Sun / Sūrya",
    symbol: "☉",
    archetype: "Tārā",
    principle: "Beginning & Guidance",
    storyLines: [
      "Have you ever been in a dark room, and then someone lit a single small candle?",
      "Suddenly, you know exactly where to step.",
      "Number 1 is like that first light. You do not need to see the entire staircase right now; you just need enough light to take the very first step.",
      "Are you waiting for everyone else to tell you what to do?",
      "Trust your inner spark. Take the lead in your own life today."
    ],
    takeaway: "When you start walking with clarity, the path guides you forward."
  },
  {
    num: 2,
    planet: "Moon / Candra",
    symbol: "☾",
    archetype: "Tripurasundarī",
    principle: "Duality & Harmony",
    storyLines: [
      "Think of riding a bicycle. What happens if you only push the right pedal and never touch the left one? You lose balance and fall.",
      "Life works the same way between talking and listening, giving and receiving.",
      "When someone is upset, reacting immediately usually makes things worse.",
      "Take a gentle 90-minute pause. Listen not just to words, but to what people are feeling underneath."
    ],
    takeaway: "True strength is gentle. When you bring harmony inside, conflicts around you settle down on their own."
  },
  {
    num: 3,
    planet: "Jupiter / Guru",
    symbol: "♃",
    archetype: "Bhuvanēśvarī",
    principle: "Space & Creation",
    storyLines: [
      "Have you ever tried to paint or study on a desk that is completely cluttered with dirty cups and papers? Your mind feels trapped.",
      "The moment you wipe the table clean and create open space, ideas immediately start to flow.",
      "Number 3 reminds you to create room for joy, wisdom, and creative expression.",
      "Share what you know with someone today. Teach with a warm smile."
    ],
    takeaway: "When you open space in your heart, life fills it with abundance and wisdom."
  },
  {
    num: 4,
    planet: "Rāhu",
    symbol: "☊",
    archetype: "Bhairavī",
    principle: "Fire & Transformation",
    storyLines: [
      "Think about how smartphones were born. People did not just build slightly faster rotary phones; they completely rethought how we connect with the world.",
      "Number 4 is about breaking free from outdated habits that no longer serve you.",
      "Is there an old routine you follow just because it has always been done this way?",
      "Set up a clean, fresh daily discipline."
    ],
    takeaway: "Do not be afraid to do things differently. Real progress begins when you build fresh, practical foundations."
  },
  {
    num: 5,
    planet: "Mercury / Budha",
    symbol: "☿",
    archetype: "Chinnamastā",
    principle: "Life-Force & Sacrifice",
    storyLines: [
      "Think of a friendly shopkeeper who warmly offers you a fresh sample of fruit.",
      "They do not hoard everything for themselves. They know that giving genuine value upfront creates trust, friendship, and thriving trade.",
      "Energy must stay in motion. To learn a great skill, you gladly give your time and focus.",
      "Are you holding back out of fear of loss? Give freely, negotiate fairly, and stay curious."
    ],
    takeaway: "Life is a continuous, beautiful exchange. What you circulate with an open heart comes back multiplied."
  },
  {
    num: 6,
    planet: "Venus / Śukra",
    symbol: "♀",
    archetype: "Dhūmāvatī",
    principle: "Emptiness & Detachment",
    storyLines: [
      "Have you noticed how a simple, quiet room with almost no furniture can feel far more peaceful and luxurious than a room packed with expensive clutter?",
      "Number 6 teaches us that true beauty does not need to show off or shout.",
      "Stop worrying about what other people think. Stop trying to fix or manage everyone else's life.",
      "Take care of yourself. Appreciate simple elegance."
    ],
    takeaway: "When you let go of the need for approval, you find genuine peace and lasting beauty."
  },
  {
    num: 7,
    planet: "Ketu",
    symbol: "☋",
    archetype: "Bagalāmukhī",
    principle: "Stillness & Control",
    storyLines: [
      "Think of a master chess player. When the clock is ticking and the opponent makes an aggressive move, the master does not panic or wave their hands.",
      "They sit in deep, calm silence. In that still pause, the right move becomes crystal clear.",
      "When a sudden challenge comes your way, do not rush to fight or defend yourself.",
      "Just pause for 90 minutes. Stay still."
    ],
    takeaway: "Silence is your superpower. When you remain calm, confusion stops in its tracks."
  },
  {
    num: 8,
    planet: "Saturn / Śani",
    symbol: "♄",
    archetype: "Mātaṅgī",
    principle: "Knowledge & Expression",
    storyLines: [
      "Think of a master woodcarver who spends years practicing with simple tools before carving a temple gate that lasts for hundreds of years.",
      "They do not rush for overnight fame. They respect the craft, one cut at a time.",
      "Number 8 is about taking full responsibility for your life and your commitments.",
      "Keep your promises. Build patiently."
    ],
    takeaway: "Patience and honest discipline turn everyday effort into enduring success that outlasts time."
  },
  {
    num: 9,
    planet: "Mars / Maṅgala",
    symbol: "♂",
    archetype: "Kamalā",
    principle: "Abundance & Fulfilment",
    storyLines: [
      "Think of the lotus flower blooming gracefully on top of muddy water.",
      "It does not fight the mud; it rises above it into full, golden bloom.",
      "Number 9 represents completing an old chapter with pride, grace, and forgiveness.",
      "Whatever unfinished task or lingering resentment is holding you back—finish it today and forgive."
    ],
    takeaway: "Close the old doors with love and gratitude. You are ready to step into full, joyful abundance."
  }
];

// Dynamic Trait System for Numbers 1-9
const NUMBER_TRAITS: Record<number, {
  planet: string;
  symbol: string;
  theme: string;
  nature: string;
  purpose: string;
  vibration: string;
  balance: string;
  textColor: string;
  bgColor: string;
  borderColor: string;
}> = {
  1: {
    planet: 'Sun / Sūrya',
    symbol: '☉',
    theme: 'Leadership & Pioneer',
    nature: 'Independent • Leadership • Initiative • Self-expression',
    purpose: 'Pioneering Paths • Self-Reliance • Original Vision • Authority',
    vibration: 'Courage • Direct Action • Self-Determination • Bold Starts',
    balance: 'Initiative • Self-Respect • Assertiveness • Decisiveness',
    textColor: 'text-amber-700 dark:text-amber-400',
    bgColor: 'bg-amber-50 dark:bg-amber-500/10',
    borderColor: 'border-amber-200 dark:border-amber-500/30'
  },
  2: {
    planet: 'Moon / Candra',
    symbol: '☾',
    theme: 'Empathy & Diplomacy',
    nature: 'Sensitivity • Emotional Depth • Listening • Diplomacy',
    purpose: 'Emotional Mastery • Peaceful Alliances • Intuitive Counsel',
    vibration: 'Gentle Harmony • Mediation • Receptivity • Connection',
    balance: 'Patience • Active Listening • Diplomacy • Boundary Care',
    textColor: 'text-sky-700 dark:text-sky-400',
    bgColor: 'bg-sky-50 dark:bg-sky-500/10',
    borderColor: 'border-sky-200 dark:border-sky-500/30'
  },
  3: {
    planet: 'Jupiter / Guru',
    symbol: '♃',
    theme: 'Wisdom & Creative Expansion',
    nature: 'Creative Expression • Optimism • Warmth • Joy',
    purpose: 'Teaching • Wisdom Sharing • Community Building • Uplifting Others',
    vibration: 'Inspiration • Creative Voice • Social Charisma • Generosity',
    balance: 'Creative Focus • Optimism • Friendly Dialogue • Truth',
    textColor: 'text-amber-700 dark:text-amber-400',
    bgColor: 'bg-amber-50 dark:bg-amber-500/10',
    borderColor: 'border-amber-200 dark:border-amber-500/30'
  },
  4: {
    planet: 'Rāhu',
    symbol: '☊',
    theme: 'Disruption & Innovation',
    nature: 'Originality • Practical Systems • Unconventional Thinking',
    purpose: 'Building Solid Foundations • Disrupting Old Dogmas • Modern Tech',
    vibration: 'Strategic Structure • Tenacity • Inventive Design • Security',
    balance: 'Disciplined Routine • Methodical Planning • Flexible Execution',
    textColor: 'text-teal-700 dark:text-teal-400',
    bgColor: 'bg-teal-50 dark:bg-teal-500/10',
    borderColor: 'border-teal-200 dark:border-teal-500/30'
  },
  5: {
    planet: 'Mercury / Budha',
    symbol: '☿',
    theme: 'Commerce & Versatility',
    nature: 'Mental Agility • Communication • Adaptability • Commerce',
    purpose: 'Commercial Expansion • Networking • Rapid Learning • Versatility',
    vibration: 'Sharp Deals • Expressive Freedom • Curiosity • Fast Execution',
    balance: 'Adaptability • Communication • Planning • Business Acumen',
    textColor: 'text-emerald-700 dark:text-emerald-400',
    bgColor: 'bg-emerald-50 dark:bg-emerald-500/10',
    borderColor: 'border-emerald-200 dark:border-emerald-500/30'
  },
  6: {
    planet: 'Venus / Śukra',
    symbol: '♀',
    theme: 'Aesthetic Harmony & Luxury',
    nature: 'Aesthetic Refinement • Domestic Warmth • Beauty • Nurturing',
    purpose: 'Harmonizing Relationships • Aesthetic Creation • Service & Care',
    vibration: 'Elegance • Loving Support • Healing Environments • Luxury',
    balance: 'Detached Nurturing • Boundary Grace • Artistic Harmony',
    textColor: 'text-pink-700 dark:text-pink-400',
    bgColor: 'bg-pink-50 dark:bg-pink-500/10',
    borderColor: 'border-pink-200 dark:border-pink-500/30'
  },
  7: {
    planet: 'Ketu',
    symbol: '☋',
    theme: 'Stillness & Research',
    nature: 'Introspection • Analytical Depth • Prārabdha • Poise',
    purpose: 'Spiritual Realization • Deep Investigation • Strategic Non-Action',
    vibration: 'Observational Poise • Solitude • Quiet Wisdom • Insight',
    balance: 'Silent Inquiry • Deep Analysis • Non-Reactivity • Trust',
    textColor: 'text-indigo-700 dark:text-indigo-400',
    bgColor: 'bg-indigo-50 dark:bg-indigo-500/10',
    borderColor: 'border-indigo-200 dark:border-indigo-500/30'
  },
  8: {
    planet: 'Saturn / Śani',
    symbol: '♄',
    theme: 'Authority & Wealth',
    nature: 'Executive Discipline • Responsibility • Endurance • Duty',
    purpose: 'Generational Wealth • Worldly Authority • Structured Growth',
    vibration: 'Persistence • Material Realization • Ethical Power • Justice',
    balance: 'Executive Stamina • Resource Management • Prudent Focus',
    textColor: 'text-purple-700 dark:text-purple-400',
    bgColor: 'bg-purple-50 dark:bg-purple-500/10',
    borderColor: 'border-purple-200 dark:border-purple-500/30'
  },
  9: {
    planet: 'Mars / Maṅgala',
    symbol: '♂',
    theme: 'Courage & Culmination',
    nature: 'Protective Force • Courage • Compassion • Mission Drive',
    purpose: 'Culminating Old Chapters • Safe Transitions • Righteous Courage',
    vibration: 'Courageous Completion • Forgiveness • Noble Strength • Victory',
    balance: 'Detached Completion • Emotional Release • Fearless Action',
    textColor: 'text-rose-700 dark:text-rose-400',
    bgColor: 'bg-rose-50 dark:bg-rose-500/10',
    borderColor: 'border-rose-200 dark:border-rose-500/30'
  }
};

const getPlanetIcon = (num: number) => {
  switch (num) {
    case 1:
      return <SunIcon />;
    case 2:
      return (
        <svg className="w-6 h-6 text-sky-600 dark:text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      );
    case 3:
      return (
        <svg className="w-6 h-6 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="8" strokeWidth="2"/>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6l4 2"/>
        </svg>
      );
    case 4:
      return (
        <svg className="w-6 h-6 text-teal-600 dark:text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <polygon points="12,2 22,8.5 22,15.5 12,22 2,15.5 2,8.5" strokeWidth="2"/>
        </svg>
      );
    case 5:
      return <MercuryIcon />;
    case 6:
      return (
        <svg className="w-6 h-6 text-pink-600 dark:text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="9" r="6" strokeWidth="2"/>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v6m-3-3h6"/>
        </svg>
      );
    case 7:
      return <KetuIcon />;
    case 8:
      return <SaturnIcon />;
    case 9:
      return (
        <svg className="w-6 h-6 text-rose-600 dark:text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="10" cy="14" r="6" strokeWidth="2"/>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 10l6-6m0 0h-4m4 0v4"/>
        </svg>
      );
    default:
      return <SunIcon />;
  }
};

export function MeenaNumerologyDashboard() {
  const now = new Date();
  const [formData, setFormData] = useState({
    day: '',
    month: '',
    year: '',
    full_name: '',
    public_name: '',
    daily_name: '',
    target_year: now.getFullYear(),
    target_month: now.getMonth() + 1,
  });

  const [isEditingProfile, setIsEditingProfile] = useState<boolean>(true);
  const [showChaldeanTable, setShowChaldeanTable] = useState<boolean>(false);
  const [selectedDayInspector, setSelectedDayInspector] = useState<number>(now.getDate());
  const [selectedActivity, setSelectedActivity] = useState<string>('career_interview');
  const [selectedArchetype, setSelectedArchetype] = useState<ArchetypeDetail | null>(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState<boolean>(false);
  const [showRelevanceModal, setShowRelevanceModal] = useState<boolean>(false);
  const [activeChartModalOpen, setActiveChartModalOpen] = useState<boolean>(false);
  const [showHiddenPassionModal, setShowHiddenPassionModal] = useState<boolean>(false);
  const [activeHiddenPassionTab, setActiveHiddenPassionTab] = useState<number>(5);
  const [inspectedNumber, setInspectedNumber] = useState<NumberInspectorData | null>(null);

  // AstroOS Active Chart Integration
  const { activeSummary } = useActiveChart();
  const lastLoadedChartIdRef = useRef<string | null>(null);

  // AstroOS User-Level Tier & Subscription Integration
  const { data: user } = useCurrentUser();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    async function loadUserSummary() {
      try {
        const data = await fetchDashboardSummary();
        setSummary(data);
      } catch (err) {
        // Guest / free fallback
      }
    }
    loadUserSummary();
  }, []);

  // Sync with Active Chart automatically on mount or when chart changes
  useEffect(() => {
    if (activeSummary && activeSummary.birth_datetime_utc) {
      if (lastLoadedChartIdRef.current !== activeSummary.id) {
        lastLoadedChartIdRef.current = activeSummary.id;
        const bDate = new Date(activeSummary.birth_datetime_utc);
        const name = activeSummary.subject_name || '';
        const dName = name.split(' ')[0] || '';
        
        // Convert UTC timestamp to true local birth date using chart longitude / IST offset
        const tzOffsetHours = (activeSummary.birth_longitude !== undefined && activeSummary.birth_longitude !== null)
          ? activeSummary.birth_longitude / 15
          : 5.5;
        const localBirthMs = bDate.getTime() + tzOffsetHours * 3600 * 1000;
        const localDate = new Date(localBirthMs);

        const newForm = {
          day: String(localDate.getUTCDate()),
          month: String(localDate.getUTCMonth() + 1),
          year: String(localDate.getUTCFullYear()),
          full_name: name.toUpperCase(),
          public_name: name.toUpperCase(),
          daily_name: dName.toUpperCase(),
          target_year: formData.target_year || new Date().getFullYear(),
          target_month: formData.target_month || new Date().getMonth() + 1,
        };
        setFormData(newForm);
        setIsEditingProfile(false);
        fetchReport(newForm.target_month, newForm);
      }
    }
  }, [activeSummary]);

  // System-level entitlement: Admin, Researcher, or Paid Pro/Research Plan
  const isPaidUser =
    user?.role === 'admin' ||
    user?.role === 'researcher' ||
    summary?.plan_code === 'PRO' ||
    summary?.plan_code === 'RESEARCH' ||
    summary?.plan_code === 'CUSTOM' ||
    summary?.subscription_status === 'active' ||
    summary?.subscription_status === 'trialing';
  const [activityResult, setActivityResult] = useState<{ recommended_dates: number[]; reasoning: string; actionable_advice: string } | null>(null);
  const [isStorageCleared, setIsStorageCleared] = useState<boolean>(false);

  const [report, setReport] = useState<StoryReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Synchronicity Scanner State
  const [numberSequence, setNumberSequence] = useState<string>('');
  const [syncResult, setSyncResult] = useState<RepeatedNumberResult | null>(null);
  const [syncLoading, setSyncLoading] = useState<boolean>(false);

  const fetchReport = async (overrideMonth?: number, overrideForm?: typeof formData) => {
    const activeData = overrideForm ?? formData;
    const activeMonth = overrideMonth ?? activeData.target_month;
    if (!activeData.day || !activeData.month || !activeData.year || !activeData.full_name) {
      setError('Please enter your Birth Day, Month, Year, and Official Legal Document Name.');
      setIsEditingProfile(true);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.post<StoryReport>('/api/v1/numerology/meena/report', {
        day: parseInt(String(activeData.day)),
        month: parseInt(String(activeData.month)),
        year: parseInt(String(activeData.year)),
        full_name: activeData.full_name.trim(),
        public_name: activeData.public_name ? activeData.public_name.trim() : undefined,
        daily_name: activeData.daily_name ? activeData.daily_name.trim() : undefined,
        target_year: activeData.target_year,
        target_month: activeMonth,
      });
      setReport(data);
      findActivity(selectedActivity, activeMonth, activeData);
    } catch (err: any) {
      setError(err.message || 'Failed to generate numerology report. Make sure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const scanSynchronicity = async (seq: string) => {
    if (!seq.trim()) return;
    setNumberSequence(seq);
    setSyncLoading(true);
    try {
      const data = await api.post<RepeatedNumberResult>('/api/v1/numerology/meena/scan-repeated-number', {
        sequence: seq.trim(),
        day: formData.day ? parseInt(String(formData.day)) : undefined,
        month: formData.month ? parseInt(String(formData.month)) : undefined,
        year: formData.year ? parseInt(String(formData.year)) : undefined,
        target_year: formData.target_year || new Date().getFullYear(),
      });
      setSyncResult(data);
    } catch (e: any) {
      console.error(e);
    } finally {
      setSyncLoading(false);
    }
  };

  const findActivity = async (cat: string, overrideMonth?: number, overrideForm?: typeof formData) => {
    const activeData = overrideForm ?? formData;
    const targetMonth = overrideMonth ?? activeData.target_month;
    if (!activeData.day || !activeData.month || !activeData.year) return;
    setSelectedActivity(cat);
    try {
      const data = await api.post<any>('/api/v1/numerology/meena/activity-finder', {
        day: parseInt(String(activeData.day)),
        month: parseInt(String(activeData.month)),
        year: parseInt(String(activeData.year)),
        target_year: activeData.target_year,
        target_month: targetMonth,
        activity_category: cat,
      });
      setActivityResult(data);
    } catch (e: any) {
      console.error(e);
    }
  };

  // Compute daily name decomposition & occurrences
  const dailyAudit = report?.calculation_audit?.names_breakdown?.find(b => b.layer_name.includes('Daily')) || report?.calculation_audit?.names_breakdown?.[0];
  const letterCounts: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0 };
  if (dailyAudit) {
    dailyAudit.letters.forEach(l => {
      if (l.chaldean_val >= 1 && l.chaldean_val <= 9) {
        letterCounts[l.chaldean_val] = (letterCounts[l.chaldean_val] || 0) + 1;
      }
    });
  }

  // Selected Day Energy
  const currentDays = report?.calculation_audit?.month_calendar_days || [];
  const activeDayEnergy = currentDays.find(d => d.date === selectedDayInspector) || currentDays[0];

  return (
    <div className="min-h-screen bg-[#FAF9F6] dark:bg-slate-950 text-slate-900 dark:text-slate-100 p-4 sm:p-8 space-y-6 max-w-7xl mx-auto transition-colors">
      
      {/* 🧭 Top Navigation & Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          {/* Breadcrumbs */}
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">
            <span className="text-amber-600 font-bold">◇ Numerology</span>
            <span>&gt;</span>
            <span>Meena Method</span>
            <span>&gt;</span>
            <span className="text-slate-800 dark:text-slate-200">Life Map</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Numerology Life Map
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-0.5">
            Ancient Sound Vibration • Cognitive Psychology • Decision Timing
          </p>
        </div>

        {/* Action Badges & Recalculate */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setActiveChartModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold transition-all shadow-sm"
            title="Load birth data from an active chart in your workspace"
          >
            <span>🔄</span> {activeSummary ? `Chart: ${activeSummary.subject_name}` : 'Choose Saved Chart'}
          </button>



          <div className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 shadow-sm flex items-center gap-1.5">
            <span className="text-slate-400 font-normal">Tier:</span>
            <span
              className={`px-2 py-0.5 rounded-md text-[11px] font-bold ${
                isPaidUser
                  ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40'
                  : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
              }`}
            >
              {isPaidUser ? (summary?.plan_name || 'Pro Member') : 'Free Tier'}
            </span>
          </div>

          <div className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 shadow-sm">
            <span className="text-slate-400 mr-1.5 font-normal">Methodology</span>
            <span className="font-bold text-slate-900 dark:text-white">Meena Method v1.0</span>
          </div>

          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-bold transition-all shadow-sm"
          >
            <span>📥</span> PDF
          </button>
        </div>
      </div>

      {/* 👤 1. BIRTH PROFILE & 3 NAME LAYERS CARD */}
      <div className="bg-white dark:bg-slate-900 border border-amber-100 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
        <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800/80 pb-3">
          <h2 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            Birth Profile & Name Layers
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveChartModalOpen(true)}
              className="text-xs font-semibold text-amber-700 dark:text-amber-400 hover:underline flex items-center gap-1"
            >
              <span>📂</span> Choose Saved Chart
            </button>
            <button
              onClick={() => setIsEditingProfile(!isEditingProfile)}
              className="flex items-center gap-1.5 px-3 py-1 bg-amber-50 dark:bg-amber-500/10 hover:bg-amber-100 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-500/30 rounded-lg text-xs font-semibold transition-all"
            >
              <EditIcon /> {isEditingProfile ? 'Close Editor' : 'Edit'}
            </button>
          </div>
        </div>

        {/* Expandable Edit Panel */}
        {isEditingProfile && (
          <div className="p-4 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl space-y-4 animate-fadeIn">
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Birth Day (1-31)</label>
                <input
                  type="number"
                  placeholder="DD"
                  value={formData.day}
                  onChange={e => setFormData({ ...formData, day: e.target.value })}
                  className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs font-mono font-bold"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Birth Month (1-12)</label>
                <input
                  type="number"
                  placeholder="MM"
                  value={formData.month}
                  onChange={e => setFormData({ ...formData, month: e.target.value })}
                  className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs font-mono font-bold"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Birth Year</label>
                <input
                  type="number"
                  placeholder="YYYY"
                  value={formData.year}
                  onChange={e => setFormData({ ...formData, year: e.target.value })}
                  className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs font-mono font-bold"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Target Year</label>
                <input
                  type="number"
                  value={formData.target_year}
                  onChange={e => setFormData({ ...formData, target_year: parseInt(e.target.value) || new Date().getFullYear() })}
                  className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs font-mono font-bold"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-amber-700 dark:text-amber-400 block mb-1">Target Month</label>
                <select
                  value={formData.target_month}
                  onChange={e => {
                    const m = parseInt(e.target.value);
                    setFormData({ ...formData, target_month: m });
                    if (report) fetchReport(m);
                  }}
                  className="w-full bg-white dark:bg-slate-900 border border-amber-400 dark:border-amber-500/40 rounded-lg px-2.5 py-1.5 text-xs font-mono font-bold"
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                    <option key={m} value={m}>
                      Month {m} ({new Date(2026, m - 1).toLocaleString('default', { month: 'short' })})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">1. Official Legal / Document Name</label>
                <input
                  type="text"
                  placeholder="e.g. JOHN DOE"
                  value={formData.full_name}
                  onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs uppercase"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">2. Public / Social Name</label>
                <input
                  type="text"
                  placeholder="e.g. JOHN DOE"
                  value={formData.public_name}
                  onChange={e => setFormData({ ...formData, public_name: e.target.value })}
                  className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs uppercase"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">3. Daily Calling / Spoken Name</label>
                <input
                  type="text"
                  placeholder="e.g. JOHN"
                  value={formData.daily_name}
                  onChange={e => setFormData({ ...formData, daily_name: e.target.value })}
                  className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs uppercase"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  fetchReport();
                  setIsEditingProfile(false);
                }}
                className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-xs transition-all shadow"
              >
                Apply & Calculate
              </button>
            </div>
          </div>
        )}

        {/* Profile Details Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
          {/* Left Parameter Chips */}
          <div className="lg:col-span-3 grid grid-cols-3 sm:grid-cols-3 lg:grid-cols-1 gap-2 p-3 bg-slate-50 dark:bg-slate-950/60 rounded-xl border border-slate-200/80 dark:border-slate-800 text-xs font-mono">
            <div>
              <span className="text-[10px] text-slate-500 uppercase block">Birth Day</span>
              <span className="font-bold text-sm text-slate-900 dark:text-white">{formData.day ? String(formData.day).padStart(2, '0') : '—'}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 uppercase block">Birth Month</span>
              <span className="font-bold text-sm text-slate-900 dark:text-white">{formData.month ? String(formData.month).padStart(2, '0') : '—'}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 uppercase block">Birth Year</span>
              <span className="font-bold text-sm text-slate-900 dark:text-white">{formData.year || '—'}</span>
            </div>
            <div className="pt-1 border-t border-slate-200 dark:border-slate-800 col-span-3 lg:col-span-1 flex justify-between">
              <div>
                <span className="text-[10px] text-slate-500 uppercase block">Target Year</span>
                <span className="font-bold text-sm text-amber-700 dark:text-amber-400">{formData.target_year}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase block">Target Month</span>
                <span className="font-bold text-sm text-amber-700 dark:text-amber-400">{String(formData.target_month).padStart(2, '0')}</span>
              </div>
            </div>
          </div>

          {/* Right 3 Numbered Name Layer Badges */}
          <div className="lg:col-span-9 grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Layer 1 */}
            <div className="p-3.5 bg-slate-50 dark:bg-slate-950/60 border border-slate-200/90 dark:border-slate-800 rounded-xl space-y-1.5 flex flex-col justify-between">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 text-xs font-bold flex items-center justify-center font-mono">
                  1
                </span>
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">Official Legal / Document Name</span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                Governs formal contracts, assets & legal karma
              </p>
              <div className="text-sm font-extrabold text-slate-900 dark:text-white font-mono tracking-tight pt-1">
                {formData.full_name || '—'}
              </div>
            </div>

            {/* Layer 2 */}
            <div className="p-3.5 bg-slate-50 dark:bg-slate-950/60 border border-slate-200/90 dark:border-slate-800 rounded-xl space-y-1.5 flex flex-col justify-between">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold flex items-center justify-center font-mono">
                  2
                </span>
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">Public / Social / Professional Name</span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                Governs reputation, peers & social charisma
              </p>
              <div className="text-sm font-extrabold text-slate-900 dark:text-white font-mono tracking-tight pt-1">
                {formData.public_name || formData.full_name || '—'}
              </div>
            </div>

            {/* Layer 3 */}
            <div className="p-3.5 bg-slate-50 dark:bg-slate-950/60 border border-slate-200/90 dark:border-slate-800 rounded-xl space-y-1.5 flex flex-col justify-between">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 text-xs font-bold flex items-center justify-center font-mono">
                  3
                </span>
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">Daily Spoken / Calling / Pet Name</span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                Direct vibrational frequency on emotional baseline
              </p>
              <div className="text-sm font-extrabold text-slate-900 dark:text-white font-mono tracking-tight pt-1">
                {formData.daily_name || (formData.full_name ? formData.full_name.split(' ')[0] : '—')}
              </div>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/30 rounded-2xl text-xs text-rose-800 dark:text-rose-300 flex justify-between items-center">
          <span>⚠️ {error}</span>
          <button onClick={() => fetchReport()} className="font-bold underline hover:no-underline">Retry</button>
        </div>
      )}

      {loading && !report && (
        <div className="bg-white dark:bg-slate-900 border border-amber-200 dark:border-slate-800 rounded-2xl p-12 text-center space-y-3 shadow-sm">
          <div className="inline-block animate-spin text-2xl text-amber-500">⏳</div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">Calculating Meena Numerology Life Map...</h3>
          <p className="text-xs text-slate-500">Computing 3 name layers, 4 life chapters, Ank Chakra, and monthly timing cycles.</p>
        </div>
      )}

      {!report && !loading && (
        <div className="bg-white dark:bg-slate-900 border border-amber-200/80 dark:border-slate-800 rounded-2xl p-8 sm:p-12 text-center space-y-4 shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 text-3xl font-black flex items-center justify-center mx-auto border border-amber-300 dark:border-amber-500/30">
            ◇
          </div>
          <div className="max-w-md mx-auto space-y-1.5">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Meena Numerology Life Map</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Load an active birth chart from your workspace or enter your birth date and official document name in the editor above, then click <strong>Calculate Life Map</strong>.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-3 pt-2">
            <button
              onClick={() => setActiveChartModalOpen(true)}
              className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow"
            >
              📂 Select from Saved Charts
            </button>
            <button
              onClick={() => setIsEditingProfile(true)}
              className="px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold rounded-xl text-xs transition-all border border-slate-300 dark:border-slate-700"
            >
              ✍️ Enter Birth Details
            </button>
          </div>
        </div>
      )}

      {/* 🔢 2. DYNAMIC CORE METRIC CARDS ROW (1, 2, 3, 4) */}
      {report && (() => {
        const moolankVal = report.calculation_audit.moolank_number;
        const moolankTrait = NUMBER_TRAITS[moolankVal] || NUMBER_TRAITS[1];

        const bhagyankVal = report.calculation_audit.bhagyank_number;
        const bhagyankTrait = NUMBER_TRAITS[bhagyankVal] || NUMBER_TRAITS[7];

        const nameNumVal = dailyAudit?.chaldean_reduced ?? 8;
        const nameNumTrait = NUMBER_TRAITS[nameNumVal] || NUMBER_TRAITS[8];

        const balanceVal = report.calculation_audit.soul_urge_number;
        const balanceTrait = NUMBER_TRAITS[balanceVal] || NUMBER_TRAITS[5];

        return (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Moolank */}
            <div className={`bg-white dark:bg-slate-900 border ${moolankTrait.borderColor} rounded-2xl p-5 shadow-sm space-y-3 relative overflow-hidden`}>
              <div className="flex items-center justify-between">
                <span className={`w-5 h-5 rounded-full ${moolankTrait.bgColor} ${moolankTrait.textColor} text-xs font-bold flex items-center justify-center font-mono`}>
                  1
                </span>
                <div className="text-right">
                  <span className="text-xs font-bold text-slate-900 dark:text-white block">Moolank</span>
                  <span className="text-[10px] text-slate-500 font-mono">(Birth Day Number)</span>
                </div>
              </div>

              <div className="flex items-center gap-4 pt-1">
                {getPlanetIcon(moolankVal)}
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-black text-slate-900 dark:text-white font-mono">
                      {moolankVal}
                    </span>
                    <span className={`text-xs font-bold ${moolankTrait.textColor}`}>{moolankTrait.planet}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Instinctive Nature</span>
                <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                  {moolankTrait.nature}
                </p>
              </div>
            </div>

            {/* Card 2: Bhagyank */}
            <div className={`bg-white dark:bg-slate-900 border ${bhagyankTrait.borderColor} rounded-2xl p-5 shadow-sm space-y-3 relative overflow-hidden`}>
              <div className="flex items-center justify-between">
                <span className={`w-5 h-5 rounded-full ${bhagyankTrait.bgColor} ${bhagyankTrait.textColor} text-xs font-bold flex items-center justify-center font-mono`}>
                  2
                </span>
                <div className="text-right">
                  <span className="text-xs font-bold text-slate-900 dark:text-white block">Bhagyank</span>
                  <span className="text-[10px] text-slate-500 font-mono">(Destiny Number)</span>
                </div>
              </div>

              <div className="flex items-center gap-4 pt-1">
                {getPlanetIcon(bhagyankVal)}
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-black text-slate-900 dark:text-white font-mono">
                      {bhagyankVal}
                    </span>
                    <span className={`text-xs font-bold ${bhagyankTrait.textColor}`}>{bhagyankTrait.planet}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Life Purpose</span>
                <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                  {bhagyankTrait.purpose}
                </p>
              </div>
            </div>

            {/* Card 3: Name Number (Chaldean) */}
            <div className={`bg-white dark:bg-slate-900 border ${nameNumTrait.borderColor} rounded-2xl p-5 shadow-sm space-y-3 relative overflow-hidden`}>
              <div className="flex items-center justify-between">
                <span className={`w-5 h-5 rounded-full ${nameNumTrait.bgColor} ${nameNumTrait.textColor} text-xs font-bold flex items-center justify-center font-mono`}>
                  3
                </span>
                <div className="text-right">
                  <span className="text-xs font-bold text-slate-900 dark:text-white block">Name Number (Chaldean)</span>
                  <span className="text-[10px] text-slate-500 font-mono">Daily Spoken Name</span>
                </div>
              </div>

              <div className="flex items-center gap-4 pt-1">
                {getPlanetIcon(nameNumVal)}
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-black text-slate-900 dark:text-white font-mono">
                      {nameNumVal}
                    </span>
                    <span className={`text-xs font-bold ${nameNumTrait.textColor}`}>{nameNumTrait.planet}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Daily Vibration</span>
                <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                  {nameNumTrait.vibration}
                </p>
              </div>
            </div>

            {/* Card 4: Balance Number (Soul Urge / Initials) */}
            <div className={`bg-white dark:bg-slate-900 border ${balanceTrait.borderColor} rounded-2xl p-5 shadow-sm space-y-3 relative overflow-hidden`}>
              <div className="flex items-center justify-between">
                <span className={`w-5 h-5 rounded-full ${balanceTrait.bgColor} ${balanceTrait.textColor} text-xs font-bold flex items-center justify-center font-mono`}>
                  4
                </span>
                <div className="text-right">
                  <span className="text-xs font-bold text-slate-900 dark:text-white block">Balance Number</span>
                  <span className="text-[10px] text-slate-500 font-mono">(Initials & Core Will)</span>
                </div>
              </div>

              <div className="flex items-center gap-4 pt-1">
                {getPlanetIcon(balanceVal)}
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-black text-slate-900 dark:text-white font-mono">
                      {balanceVal}
                    </span>
                    <span className={`text-xs font-bold ${balanceTrait.textColor}`}>{balanceTrait.planet}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Balance Theme</span>
                <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                  {balanceTrait.balance}
                </p>
              </div>
            </div>
          </div>
        );
      })()}

      {/* 📊 3. TWO-COLUMN MASTER GRID LAYOUT */}
      {report && (
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* ================= LEFT COLUMN ================= */}
        <div className="lg:col-span-6 space-y-6">
          
          {/* Card 5: Name Analysis (Chaldean) */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold flex items-center justify-center font-mono">
                  5
                </span>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">Name Analysis (Chaldean)</h3>
                  <span className="text-[11px] text-slate-500">Using Meena Method — Letter to Number Mapping</span>
                </div>
              </div>
            </div>

            {/* Chaldean Table Banner */}
            <div className="p-3 bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 block">Chaldean Table Used</span>
                <span className="text-[11px] text-slate-500 font-mono">(9 is not used in Chaldean alphabets)</span>
              </div>
              <button
                onClick={() => setShowChaldeanTable(!showChaldeanTable)}
                className="px-3 py-1 bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-semibold transition-all shadow-sm"
              >
                {showChaldeanTable ? 'Hide Table' : 'View Table'}
              </button>
            </div>

            {/* Chaldean Reference Matrix Table Popup / Inline */}
            {showChaldeanTable && (
              <div className="p-3.5 bg-amber-50/50 dark:bg-slate-950 border border-amber-200 dark:border-slate-800 rounded-xl text-xs space-y-2 animate-fadeIn font-mono">
                <span className="font-bold text-amber-900 dark:text-amber-300 block">Chaldean Sound Matrix (1-8):</span>
                <div className="grid grid-cols-4 gap-2 text-[11px]">
                  <div><strong className="text-slate-900 dark:text-white">1:</strong> A, I, J, Q, Y</div>
                  <div><strong className="text-slate-900 dark:text-white">2:</strong> B, K, R</div>
                  <div><strong className="text-slate-900 dark:text-white">3:</strong> C, G, L, S</div>
                  <div><strong className="text-slate-900 dark:text-white">4:</strong> D, M, T</div>
                  <div><strong className="text-slate-900 dark:text-white">5:</strong> E, H, N, X</div>
                  <div><strong className="text-slate-900 dark:text-white">6:</strong> U, V, W</div>
                  <div><strong className="text-slate-900 dark:text-white">7:</strong> O, Z</div>
                  <div><strong className="text-slate-900 dark:text-white">8:</strong> F, P</div>
                </div>
              </div>
            )}

            {/* Letter Calculation & Occurrences */}
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center pt-1">
              {/* Daily Spoken Result */}
              <div className="sm:col-span-4 p-4 bg-slate-50 dark:bg-slate-950/70 border border-slate-200/80 dark:border-slate-800 rounded-xl text-center space-y-1">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 block uppercase font-mono">
                  {formData.daily_name || (formData.full_name ? formData.full_name.split(' ')[0] : '—')}
                </span>
                <span className="text-[10px] text-slate-500 block">(Daily Spoken Name)</span>
                <span className="text-4xl font-black text-slate-900 dark:text-white font-mono block pt-1">
                  {dailyAudit?.chaldean_reduced ?? '—'}
                </span>
              </div>

              {/* Letter Formula & Occurrences */}
              <div className="sm:col-span-8 space-y-2">
                <div className="p-3 bg-slate-50 dark:bg-slate-950/70 border border-slate-200/80 dark:border-slate-800 rounded-xl space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Letter Numbers</span>
                  <div className="flex flex-wrap gap-2 text-xs font-mono font-bold text-slate-800 dark:text-slate-200">
                    {dailyAudit?.letters?.map((l, i) => (
                      <span key={i} className="px-1.5 py-0.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded">
                        {l.char}({l.chaldean_val})
                      </span>
                    )) || <span className="text-slate-400 font-sans font-normal">No letters found</span>}
                  </div>
                  <div className="text-xs font-mono text-slate-600 dark:text-slate-400 pt-1">
                    {isPaidUser ? (
                      dailyAudit?.chaldean_formula || '—'
                    ) : (
                      <span className="text-amber-700 dark:text-amber-400 font-sans text-[11px] font-semibold flex items-center gap-1">
                        🔒 Step-by-step formula breakdown is reserved for Pro members.
                      </span>
                    )}
                  </div>
                </div>

                {/* Occurrences List */}
                <div className="p-3 bg-slate-50 dark:bg-slate-950/70 border border-slate-200/80 dark:border-slate-800 rounded-xl">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Occurrences</span>
                  <div className="grid grid-cols-3 gap-x-2 gap-y-1 text-[11px] font-mono">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => {
                      const count = letterCounts[num] || 0;
                      return (
                        <div key={num} className="flex justify-between items-center text-slate-600 dark:text-slate-400">
                          <span className="font-bold text-slate-800 dark:text-slate-200">{num}</span>
                          <span className={count > 0 ? 'text-amber-700 dark:text-amber-400 font-bold' : 'text-slate-400'}>
                            {count} time{count !== 1 ? 's' : ''}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>

            {/* Mini Summary Badges at bottom */}
            {(() => {
              const nameExcess = Object.entries(letterCounts)
                .filter(([_, count]) => count >= 4)
                .map(([num, count]) => `#${num} (${count}x)`);

              const nameMissing = [1, 2, 3, 4, 5, 6, 7, 8].filter(num => (letterCounts[num] || 0) === 0);

              const maxCount = Math.max(...Object.values(letterCounts));
              const topNums = Object.entries(letterCounts)
                .filter(([_, count]) => count === maxCount && count > 1)
                .map(([num]) => `#${num}`);

              const nameHiddenPassion = topNums.length === 1
                ? `${topNums[0]} (${maxCount}x)`
                : topNums.length > 1
                ? `${topNums.join(', ')} (${maxCount}x)`
                : (report?.calculation_audit?.hidden_passion_number
                    ? `#${report.calculation_audit.hidden_passion_number}`
                    : 'None (Even)');

              return (
                <div className="grid grid-cols-3 gap-2 pt-2 text-center text-xs font-mono">
                  <div className="p-2.5 bg-rose-50/60 dark:bg-rose-500/10 border border-rose-200/60 dark:border-rose-500/20 rounded-xl">
                    <span className="text-[10px] text-rose-700 dark:text-rose-400 font-bold block uppercase">Excess Numbers</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200 text-[11px]">
                      {nameExcess.length ? nameExcess.join(', ') : 'None (<4x)'}
                    </span>
                  </div>
                  <div className="p-2.5 bg-amber-50/60 dark:bg-amber-500/10 border border-amber-200/60 dark:border-amber-500/20 rounded-xl">
                    <span className="text-[10px] text-amber-700 dark:text-amber-400 font-bold block uppercase">Missing in Name</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200 text-[11px]">
                      {nameMissing.length ? nameMissing.join(', ') : 'None'}
                    </span>
                  </div>
                  <div 
                    onClick={() => {
                      if (topNums.length > 0) {
                        setActiveHiddenPassionTab(parseInt(topNums[0].replace('#', '')));
                      }
                      setShowHiddenPassionModal(true);
                    }}
                    className="p-2.5 bg-purple-50/60 hover:bg-purple-100/70 dark:bg-purple-500/10 dark:hover:bg-purple-500/20 border border-purple-200/60 dark:border-purple-500/20 rounded-xl cursor-pointer transition-all group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-purple-700 dark:text-purple-400 font-bold uppercase">Hidden Passion</span>
                      <span className="text-[9px] text-purple-600 dark:text-purple-400 group-hover:underline">Explore 1-9 ↗</span>
                    </div>
                    <span className="font-bold text-slate-800 dark:text-slate-200 text-[11px] block mt-0.5">
                      {nameHiddenPassion}
                    </span>
                  </div>
                </div>
              );
            })()}
          </div>

          {/* Card 7: Timing Cycle (2026) with Interactive Date Picker */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold flex items-center justify-center font-mono">
                  7
                </span>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Timing Cycle ({formData.target_year})</h3>
              </div>
              <span className="text-xs text-slate-500 font-mono">
                {report?.target_month_name || 'September'} {formData.target_year}
              </span>
            </div>

            {/* Horizontal Timing Cards */}
            {(() => {
              const activeYearForecast = report?.five_year_roadmap?.find(r => r.year === formData.target_year) || report?.five_year_roadmap?.[0];
              const displayPY = activeYearForecast?.personal_year_number ?? '—';
              const displayPM = activeDayEnergy?.personal_month_number ?? currentDays[0]?.personal_month_number ?? '—';
              const displayPD = activeDayEnergy?.personal_date_number ?? '—';

              return (
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div 
                    onClick={() => {
                      if (typeof displayPY === 'number' && NUMBER_ARCHETYPE_DETAILS[displayPY]) {
                        const numInfo = NUMBER_ARCHETYPE_DETAILS[displayPY];
                        // Mirror backend digital_root: (n - 1) % 9 + 1, with 0 -> 0 fallback for empty fields
                        const computeDr = (raw: string, fallback: boolean) => {
                          const n = parseInt(String(raw || '0'));
                          if (isNaN(n) || n === 0) return fallback ? 0 : 0;
                          return (n - 1) % 9 + 1;
                        };
                        const dRoot = computeDr(formData.day, !!formData.day);
                        const mRoot = computeDr(formData.month, !!formData.month);
                        const yRoot = computeDr(String(formData.target_year || '2026'), false) || 9;
                        const rawSum = dRoot + mRoot + yRoot;
                        const pyRoot = rawSum > 0 ? (rawSum - 1) % 9 + 1 : 0;
                        setInspectedNumber({
                          title: `Personal Year ${displayPY} (${formData.target_year})`,
                          badge: 'Annual Life Epicycle',
                          number: displayPY,
                          planet: numInfo.planet,
                          icon: numInfo.icon,
                          formula: report?.calculation_audit?.personal_year_formula || `Day Root (${dRoot}) + Month Root (${mRoot}) + Year Root ${formData.target_year} (${yRoot}) = ${rawSum} -> Personal Year ${pyRoot}`,
                          explanation: 'Personal Year (PY) represents the dominant overarching energy and life-chapter focus for the entire 365-day solar period.',
                          meaning: numInfo.meaning,
                          actionDirective: numInfo.advice,
                          warningNotice: numInfo.warning
                        });
                      }
                    }}
                    className="p-3 bg-slate-50 hover:bg-slate-100/80 dark:bg-slate-950/60 dark:hover:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-xl space-y-1 cursor-pointer transition-all hover:scale-[1.02] shadow-sm group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-500 uppercase font-bold">Personal Year (PY)</span>
                      <span className="text-[9px] text-amber-600 dark:text-amber-400 group-hover:underline">ℹ️ Detail</span>
                    </div>
                    <span className="text-3xl font-black text-slate-900 dark:text-white font-mono">
                      {displayPY}
                    </span>
                    <span className="text-[10px] text-slate-400 block font-mono">{formData.target_year}</span>
                  </div>

                  <div 
                    onClick={() => {
                      if (typeof displayPM === 'number' && NUMBER_ARCHETYPE_DETAILS[displayPM]) {
                        const numInfo = NUMBER_ARCHETYPE_DETAILS[displayPM];
                        const tMonth = formData.target_month || 9;
                        const pyNum = typeof displayPY === 'number' ? displayPY : 1;
                        // Mirror backend digital_root: reduce sum to single digit
                        const pmRoot = (pyNum + tMonth - 1) % 9 + 1;
                        setInspectedNumber({
                          title: `Personal Month ${displayPM} (${report?.target_month_name || 'September'} ${formData.target_year})`,
                          badge: 'Monthly Timing Layer',
                          number: displayPM,
                          planet: numInfo.planet,
                          icon: numInfo.icon,
                          formula: report?.calculation_audit?.personal_month_formula || `Personal Year (${pyNum}) + Calendar Month (${tMonth}) = ${pmRoot} -> Personal Month ${displayPM}`,
                          explanation: `Personal Month (PM) fine-tunes your Personal Year theme for the specific 30-day window of ${report?.target_month_name}.`,
                          meaning: numInfo.meaning,
                          actionDirective: numInfo.advice,
                          warningNotice: numInfo.warning
                        });
                      }
                    }}
                    className="p-3 bg-slate-50 hover:bg-slate-100/80 dark:bg-slate-950/60 dark:hover:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-xl space-y-1 cursor-pointer transition-all hover:scale-[1.02] shadow-sm group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-500 uppercase font-bold">Personal Month (PM)</span>
                      <span className="text-[9px] text-amber-600 dark:text-amber-400 group-hover:underline">ℹ️ Detail</span>
                    </div>
                    <span className="text-3xl font-black text-slate-900 dark:text-white font-mono">
                      {displayPM}
                    </span>
                    <span className="text-[10px] text-slate-400 block font-mono">{report?.target_month_name || 'September'}</span>
                  </div>

                  <div 
                    onClick={() => {
                      if (typeof displayPD === 'number' && NUMBER_ARCHETYPE_DETAILS[displayPD]) {
                        const numInfo = NUMBER_ARCHETYPE_DETAILS[displayPD];
                        const dayData = activeDayEnergy;
                        const pdRaw = displayPM + selectedDayInspector;
                        const pdCalc = dayData?.calculation_formula || `Personal Month (${displayPM}) + Day ${selectedDayInspector} = ${pdRaw} -> Personal Day ${((pdRaw - 1) % 9) + 1}`;
                        const formula = dayData?.calculation_formula || pdCalc;
                        setInspectedNumber({
                          title: `Personal Day ${displayPD} (${selectedDayInspector} ${report?.target_month_name} ${formData.target_year})`,
                          badge: dayData?.is_peak_date ? '✨ Peak Gateway Day' : 'Daily Timing Pulse',
                          number: displayPD,
                          planet: numInfo.planet,
                          icon: numInfo.icon,
                          formula: formula,
                          explanation: `Personal Day (PD) governs the immediate emotional, cognitive, and commercial flow of this specific 24-hour day.`,
                          meaning: numInfo.meaning,
                          actionDirective: numInfo.advice,
                          warningNotice: numInfo.warning
                        });
                      }
                    }}
                    className="p-3 bg-amber-50 hover:bg-amber-100/80 dark:bg-amber-500/10 dark:hover:bg-amber-500/20 border border-amber-300 dark:border-amber-500/30 rounded-xl space-y-1 cursor-pointer transition-all hover:scale-[1.02] shadow-sm group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-amber-700 dark:text-amber-400 uppercase font-bold">
                        Personal Day (PD)
                      </span>
                      <span className="text-[9px] text-amber-700 dark:text-amber-300 group-hover:underline">ℹ️ Detail</span>
                    </div>
                    <span className="text-3xl font-black text-amber-800 dark:text-amber-300 font-mono">
                      {displayPD}
                    </span>
                    <span className="text-[10px] text-amber-700 dark:text-amber-400 block font-mono">
                      {selectedDayInspector} {report?.target_month_name?.slice(0, 3)} {formData.target_year}
                    </span>
                  </div>
                </div>
              );
            })()}

            {/* Interactive Date Selector / Inspector */}
            <div className="p-3.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  <CalendarIcon /> Select Any Day in {report?.target_month_name || 'September'}:
                </span>
                <span className="text-[11px] font-mono text-amber-700 dark:text-amber-400 font-bold">
                  {activeDayEnergy?.day_of_week}, {selectedDayInspector} {report?.target_month_name}
                </span>
              </div>

              {/* Horizontal Date Picker Slider / Grid */}
              <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
                {currentDays.map(d => (
                  <button
                    key={d.date}
                    onClick={() => setSelectedDayInspector(d.date)}
                    className={`shrink-0 w-8 h-9 rounded-lg text-xs font-mono flex flex-col items-center justify-center transition-all ${
                      selectedDayInspector === d.date
                        ? 'bg-amber-500 text-slate-950 font-black shadow-sm scale-105'
                        : d.is_peak_date
                        ? 'bg-amber-100 dark:bg-amber-500/20 text-amber-900 dark:text-amber-300 border border-amber-300 dark:border-amber-500/40'
                        : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:border-amber-300'
                    }`}
                  >
                    <span className="text-[9px] font-normal leading-none">{d.day_of_week.slice(0, 2)}</span>
                    <span className="font-bold leading-none mt-0.5">{d.date}</span>
                  </button>
                ))}
              </div>

              {/* Exact Formula for Selected Date */}
              {(() => {
                const selDate = selectedDayInspector;
                const selDateRoot = ((selDate - 1) % 9) + 1;
                const pmVal = activeDayEnergy?.personal_month_number ?? currentDays[0]?.personal_month_number ?? 1;
                const rawSum = pmVal + selDateRoot;
                const pdVal = activeDayEnergy?.personal_date_number ?? (((rawSum - 1) % 9) + 1);

                return (
                  <div className="text-[11px] font-mono bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 flex justify-between items-center">
                    <span>
                      <strong>Calculation:</strong> {isPaidUser ? (
                        activeDayEnergy?.calculation_formula || `Personal Month (${pmVal}) + Day ${selDate} (Root: ${selDateRoot}) = ${rawSum} -> Personal Day ${pdVal}`
                      ) : (
                        <span className="text-amber-700 dark:text-amber-400 font-sans font-semibold">
                          Direct Result: Personal Day {pdVal} (🔒 Formula in Pro)
                        </span>
                      )}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[10px] font-bold text-slate-700 dark:text-slate-300">
                      {activeDayEnergy?.category_icon} {activeDayEnergy?.dominant_category}
                    </span>
                  </div>
                );
              })()}
            </div>
          </div>

          {/* 🧮 3×3 VEDIC NUMBER GRID (ANK CHAKRA) */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <GridIcon />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">3×3 Vedic Number Grid (Ank Chakra)</h3>
              </div>
              <span className="text-xs text-slate-500">Distribution across Mental, Will & Action planes</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center">
              {/* The 3x3 Visual Grid */}
              <div className="sm:col-span-5 grid grid-cols-3 gap-2 p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl">
                {[
                  { num: '4', label: 'Mental', color: 'text-sky-700 dark:text-sky-300' },
                  { num: '9', label: 'Mental', color: 'text-rose-700 dark:text-rose-300' },
                  { num: '2', label: 'Mental', color: 'text-amber-700 dark:text-amber-300' },
                  { num: '3', label: 'Will', color: 'text-amber-700 dark:text-amber-400' },
                  { num: '5', label: 'Will', color: 'text-emerald-700 dark:text-emerald-300' },
                  { num: '7', label: 'Will', color: 'text-purple-700 dark:text-purple-300' },
                  { num: '8', label: 'Action', color: 'text-indigo-700 dark:text-indigo-300' },
                  { num: '1', label: 'Action', color: 'text-cyan-700 dark:text-cyan-300' },
                  { num: '6', label: 'Action', color: 'text-pink-700 dark:text-pink-300' },
                ].map(cell => {
                  const count = report?.calculation_audit?.loshu_grid?.[cell.num] || 0;
                  const isPresent = count > 0;
                  return (
                    <div
                      key={cell.num}
                      className={`h-16 rounded-lg border flex flex-col items-center justify-center p-1 transition-all ${
                        isPresent
                          ? 'bg-white dark:bg-slate-900 border-amber-300 dark:border-amber-500/40 shadow-sm'
                          : 'bg-slate-100/40 dark:bg-slate-950/40 border-slate-200 dark:border-slate-900 opacity-40'
                      }`}
                    >
                      <span className={`text-lg font-bold font-mono ${isPresent ? cell.color : 'text-slate-400'}`}>
                        {cell.num}
                      </span>
                      <span className="text-[9px] font-mono text-slate-500">
                        {isPresent ? `${cell.num.repeat(count)} (${count}x)` : '—'}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Planes Analysis */}
              <div className="sm:col-span-7 space-y-2 text-xs">
                <div className="p-2.5 bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800 rounded-lg">
                  <span className="font-bold text-sky-700 dark:text-sky-400 block text-[11px]">Top Row (4-9-2): Mental Plane</span>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400">
                    Digits: {['4', '9', '2'].filter(d => (report?.calculation_audit?.loshu_grid?.[d] || 0) > 0).join(', ') || 'None'}. Memory and intellectual analysis.
                  </p>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800 rounded-lg">
                  <span className="font-bold text-emerald-700 dark:text-emerald-400 block text-[11px]">Middle Row (3-5-7): Will & Emotion Plane</span>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400">
                    Digits: {['3', '5', '7'].filter(d => (report?.calculation_audit?.loshu_grid?.[d] || 0) > 0).join(', ') || 'None'}. Intuition, resilience and drive.
                  </p>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800 rounded-lg">
                  <span className="font-bold text-amber-700 dark:text-amber-400 block text-[11px]">Bottom Row (8-1-6): Practical / Action Plane</span>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400">
                    Digits: {['8', '1', '6'].filter(d => (report?.calculation_audit?.loshu_grid?.[d] || 0) > 0).join(', ') || 'None'}. Execution and material stability.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* 🌱 MISSING NUMBERS: BEHAVIORAL ACTIVATION */}
          {report?.missing_numbers_activation && report.missing_numbers_activation.length > 0 && (
            <div className="bg-white dark:bg-slate-900 border border-amber-200/80 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm space-y-3">
              <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-2.5">
                <div className="flex items-center gap-2">
                  <span className="text-base">🌱</span>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    Missing Numbers: Behavioral Activation & Balancing
                  </h3>
                </div>
                <span className="text-[10px] font-mono text-amber-800 dark:text-amber-300 bg-amber-100 dark:bg-amber-500/10 px-2 py-0.5 rounded-full font-bold">
                  {report.missing_numbers_activation.length} Dormant Faculties
                </span>
              </div>
              <p className="text-[11px] text-slate-600 dark:text-slate-400">
                In Meena's method, missing numbers are <strong>dormant faculties</strong> activated through <strong>daily behavioral action</strong>:
              </p>
              <div className="grid grid-cols-1 gap-2.5 pt-1">
                {report.missing_numbers_activation.map(item => (
                  <div key={item.number} className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl space-y-1">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-md bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 font-bold font-mono text-xs flex items-center justify-center">
                          #{item.number}
                        </span>
                        <span className="text-xs font-bold text-slate-900 dark:text-white">{item.planetary_ruler}</span>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">{item.dormant_quality}</span>
                    </div>
                    <div className="text-[11px] text-slate-700 dark:text-slate-300 pt-0.5">
                      <strong className="text-cyan-700 dark:text-cyan-400">🛠️ Action: </strong>
                      {item.behavioral_activation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 🔢 SYNCHRONICITY SCANNER */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-cyan-100 dark:bg-cyan-500/20 text-cyan-700 dark:text-cyan-400 rounded-lg">
                  <EyeIcon />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    Seeing Repeated Numbers like 1111, 222, 555?
                  </h3>
                  <p className="text-[11px] text-slate-500">Enter any repeating sequence to decode subconscious timing alerts.</p>
                </div>
              </div>
              <form
                onSubmit={e => {
                  e.preventDefault();
                  if (numberSequence.trim()) scanSynchronicity(numberSequence.trim());
                }}
                className="flex items-center gap-2 w-full sm:w-auto"
              >
                <input
                  type="text"
                  placeholder="e.g. 1111, 222, 555"
                  value={numberSequence}
                  onChange={e => {
                    const val = e.target.value;
                    setNumberSequence(val);
                    if (syncResult) {
                      setSyncResult(null);
                    }
                  }}
                  className="bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-900 dark:text-white w-full sm:w-36 focus:outline-none font-mono"
                />
                <button
                  type="submit"
                  disabled={syncLoading || !numberSequence.trim()}
                  className="px-3.5 py-1.5 bg-gradient-to-r from-cyan-600 to-cyan-500 text-white font-bold rounded-lg text-xs transition-all shadow disabled:opacity-50 whitespace-nowrap"
                >
                  {syncLoading ? 'Decoding...' : '🚀 Decode'}
                </button>
              </form>
            </div>

            {/* Sync Result Display */}
            {syncResult && (
              <div className="p-4 bg-slate-50 dark:bg-slate-950 border border-cyan-200 dark:border-cyan-500/30 rounded-xl space-y-2 text-xs animate-fadeIn">
                <div className="flex justify-between items-center font-bold">
                  <span className="font-mono text-sm text-cyan-800 dark:text-cyan-300">Sequence: {syncResult.sequence}</span>
                  <span className={syncResult.is_favorable ? 'text-emerald-600' : 'text-rose-600'}>
                    {syncResult.signal_status}
                  </span>
                </div>
                <p className="text-slate-700 dark:text-slate-300">{syncResult.subconscious_signal}</p>
                <div className="p-2.5 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                  <strong className="text-cyan-700 dark:text-cyan-400">Action: </strong>
                  {syncResult.actionable_directive}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ================= RIGHT COLUMN ================= */}
        <div className="lg:col-span-6 space-y-6">

          {/* 🏛️ CARD: 4 LIFE CHAPTERS & PINNACLES */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 text-xs font-bold flex items-center justify-center font-mono">
                  🏛️
                </span>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">4 Life Chapters (Pinnacles & Life Milestones)</h3>
                  <span className="text-[11px] text-slate-500">Age-based evolutionary phases via the 36 - Destiny formula</span>
                </div>
              </div>
              <span className="text-[10px] font-mono text-purple-700 dark:text-purple-300 bg-purple-100 dark:bg-purple-900/30 px-2 py-0.5 rounded-full font-bold">
                4 Major Eras
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {report.life_chapters?.map(chapter => {
                const pNum = chapter.pinnacle_number;
                const numInfo = NUMBER_ARCHETYPE_DETAILS[pNum] || NUMBER_ARCHETYPE_DETAILS[1];
                const cNum = chapter.challenge_number;
                const cInfo = NUMBER_ARCHETYPE_DETAILS[cNum];

                let formulaStr = '';
                if (chapter.chapter_index === 1) {
                  formulaStr = report.calculation_audit?.pinnacle_p1_formula || 'Month Root + Day Root (Duration: 36 - Destiny Number)';
                } else if (chapter.chapter_index === 2) {
                  formulaStr = report.calculation_audit?.pinnacle_p2_formula || 'Day Root + Year Root (Duration: 9 Years)';
                } else if (chapter.chapter_index === 3) {
                  formulaStr = report.calculation_audit?.pinnacle_p3_formula || 'Pinnacle 1 + Pinnacle 2 (Duration: 9 Years)';
                } else {
                  formulaStr = report.calculation_audit?.pinnacle_p4_formula || 'Month Root + Year Root (Duration: Lifetime 50+)';
                }

                return (
                  <div
                    key={chapter.chapter_index}
                    onClick={() => {
                      setInspectedNumber({
                        title: `Chapter ${chapter.chapter_index}: ${chapter.chapter_title}`,
                        badge: `${chapter.age_span} • Pinnacle #${pNum}`,
                        number: pNum,
                        planet: numInfo.planet,
                        icon: numInfo.icon,
                        formula: formulaStr,
                        explanation: chapter.description,
                        meaning: `यह आपके जीवन का ${chapter.chapter_index}वां कालखंड (${chapter.age_span}) है, जो ${numInfo.planet} की ऊर्जा द्वारा संचालित है। ${numInfo.meaning}`,
                        actionDirective: chapter.key_advice || numInfo.advice,
                        warningNotice: `इस कालखंड की आंतरिक चुनौती (Challenge #${cNum}): ${cInfo?.warning || 'धैर्य और अनुशासन बनाए रखें।'}`
                      });
                    }}
                    className="p-3.5 bg-slate-50 hover:bg-purple-50/50 dark:bg-slate-950 dark:hover:bg-purple-950/20 border border-slate-200/80 hover:border-purple-300 dark:border-slate-800 dark:hover:border-purple-800 rounded-xl space-y-2 flex flex-col justify-between cursor-pointer transition-all hover:scale-[1.01] shadow-sm group"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-mono">
                            Chapter {chapter.chapter_index} • {chapter.age_span}
                          </span>
                          <span className="text-[9px] text-purple-600 dark:text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity">
                            ℹ️ Detail
                          </span>
                        </div>
                        <h4 className="text-xs font-extrabold text-slate-900 dark:text-white mt-0.5 group-hover:text-purple-700 dark:group-hover:text-purple-300 transition-colors">
                          {chapter.chapter_title}
                        </h4>
                      </div>
                      <span className="w-7 h-7 rounded-lg bg-purple-100 dark:bg-purple-900/50 text-purple-800 dark:text-purple-300 font-mono font-black text-sm flex items-center justify-center group-hover:scale-110 transition-transform">
                        #{chapter.pinnacle_number}
                      </span>
                    </div>

                    <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
                      {chapter.description}
                    </p>

                    <div className="pt-1.5 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center text-[10px] font-mono">
                      <span className="text-slate-500">Lesson / Test:</span>
                      <span className="font-bold text-amber-700 dark:text-amber-400">
                        Challenge #{chapter.challenge_number}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 🛍️ CARD: ACTIVITY FINDER & MONTHLY TIMING GUIDE */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 text-xs font-bold flex items-center justify-center font-mono">
                  🛍️
                </span>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">Activity Finder & Strategy Guide</h3>
                  <span className="text-[11px] text-slate-500">Best dates in {report?.target_month_name || 'September'} {formData.target_year} for real-world tasks</span>
                </div>
              </div>
            </div>

            {/* Interactive Category Selector Pills */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {[
                { id: 'shopping_deals', label: '🛍️ Shopping & Deals', num: 5 },
                { id: 'luxury_beauty', label: '👗 Luxury & Style', num: 6 },
                { id: 'career_interview', label: '💼 Career & Pitch', num: '1/8' },
                { id: 'property_asset', label: '🏠 Property & Deals', num: '4/8' },
                { id: 'vehicle_travel', label: '🚗 Travel & Vehicle', num: '5/9' },
                { id: 'restraint_silence', label: '🧘 Restraint & Silence', num: 7 },
              ].map(cat => (
                <button
                  key={cat.id}
                  onClick={() => findActivity(cat.id)}
                  className={`p-2 rounded-xl text-left border transition-all ${
                    selectedActivity === cat.id
                      ? 'bg-amber-50 dark:bg-amber-500/10 border-amber-400 dark:border-amber-500/40 shadow-sm'
                      : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 hover:border-amber-300'
                  }`}
                >
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200 block">{cat.label}</span>
                  <span className="text-[10px] text-slate-500 font-mono">Energy: #{cat.num}</span>
                </button>
              ))}
            </div>

            {/* Active Recommendation Output Box */}
            {activityResult && (
              <div className="p-4 bg-gradient-to-br from-amber-50/70 dark:from-amber-950/20 to-slate-50 dark:to-slate-900 border border-amber-200 dark:border-amber-500/30 rounded-xl space-y-2 animate-fadeIn">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-amber-900 dark:text-amber-300">
                    Recommended Dates in {report?.target_month_name || 'September'}:
                  </span>
                  <div className="flex gap-1 flex-wrap">
                    {activityResult.recommended_dates?.map(d => (
                      <span key={d} className="px-2 py-0.5 bg-amber-500 text-slate-950 font-black rounded-lg text-xs font-mono shadow-sm">
                        {d} {report?.target_month_name?.slice(0, 3)}
                      </span>
                    ))}
                  </div>
                </div>
                <p className="text-xs text-slate-700 dark:text-slate-300 font-medium">
                  {activityResult.reasoning}
                </p>
                <div className="text-[11px] text-slate-800 dark:text-slate-200 pt-1 border-t border-amber-200/60 dark:border-amber-500/20">
                  <strong className="text-amber-800 dark:text-amber-400">💡 Strategy: </strong>
                  {activityResult.actionable_advice}
                </div>
              </div>
            )}

            {/* Full Activity Reference Table */}
            <div className="space-y-2 pt-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-mono">
                Monthly Activity Matrix
              </span>
              <div className="space-y-2">
                {report.activity_guide?.map((rec, i) => (
                  <div key={i} className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-900 dark:text-white">{rec.activity}</span>
                      <div className="flex gap-1">
                        {rec.best_dates?.slice(0, 5).map(d => (
                          <span key={d} className="px-1.5 py-0.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[10px] font-bold font-mono rounded text-amber-700 dark:text-amber-400">
                            {d}
                          </span>
                        ))}
                      </div>
                    </div>
                    <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-tight">
                      {rec.practical_advice}
                    </p>
                  </div>
                ))}
              </div>
            </div>

          </div>
          
          {/* Card 6: Planetary & Archetypal Principles Mapping Table */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-slate-100 dark:border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold flex items-center justify-center font-mono">
                  6
                </span>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Planetary & Mahāvidyā Mapping</h3>
              </div>
              <button
                onClick={() => setShowRelevanceModal(true)}
                className="flex items-center gap-1 text-[11px] text-amber-700 dark:text-amber-400 hover:text-amber-900 dark:hover:text-amber-200 font-semibold underline decoration-amber-400/60 underline-offset-2 transition-all cursor-pointer"
                title="Click to understand the connection between Numbers, Planets & Mahāvidyās"
              >
                <span>🔗 Why Mahāvidyās with Planets & Numbers?</span>
              </button>
            </div>

            {/* Clean Table with Free vs Pro Tiering */}
            {isPaidUser ? (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 dark:bg-slate-950/70 text-[11px] font-bold text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3 font-mono">Number</th>
                      <th className="py-2.5 px-3">Planet (Graha)</th>
                      <th className="py-2.5 px-3">Mahāvidyā</th>
                      <th className="py-2.5 px-3">Core Principle</th>
                      <th className="py-2.5 px-2 text-right">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-[11px]">
                    {PLANETARY_MAPPING.map(row => (
                      <tr
                        key={row.num}
                        onClick={() => setSelectedArchetype(row)}
                        className="hover:bg-amber-50/70 dark:hover:bg-amber-500/10 cursor-pointer transition-colors group"
                        title="Click to explore principle & reflection"
                      >
                        <td className="py-2.5 px-3 font-bold text-slate-900 dark:text-white group-hover:text-amber-700 dark:group-hover:text-amber-400">
                          {row.num}
                        </td>
                        <td className="py-2.5 px-3 text-slate-800 dark:text-slate-200 font-sans">
                          {row.symbol ? `${row.symbol} ` : ''}{row.planet}
                        </td>
                        <td className="py-2.5 px-3 text-amber-900 dark:text-amber-300 font-sans font-bold underline decoration-amber-300/60 underline-offset-2">
                          {row.archetype}
                        </td>
                        <td className="py-2.5 px-3 text-slate-600 dark:text-slate-400 font-sans">
                          {row.principle}
                        </td>
                        <td className="py-2.5 px-2 text-right text-[10px] font-sans text-amber-700 dark:text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity font-semibold">
                          Explore →
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              /* Free User Direct Output View (Without Mahāvidyā Suggestions) */
              <div className="space-y-3">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-50 dark:bg-slate-950/70 text-[11px] font-bold text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                      <tr>
                        <th className="py-2 px-3 font-mono">Number</th>
                        <th className="py-2 px-3">Planet (Graha)</th>
                        <th className="py-2 px-3">Standard Output</th>
                        <th className="py-2 px-3 text-right">Mahāvidyā Suggestion</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-[11px]">
                      {PLANETARY_MAPPING.map(row => (
                        <tr key={row.num} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                          <td className="py-2 px-3 font-bold text-slate-900 dark:text-white">{row.num}</td>
                          <td className="py-2 px-3 text-slate-800 dark:text-slate-200 font-sans">
                            {row.symbol ? `${row.symbol} ` : ''}{row.planet}
                          </td>
                          <td className="py-2 px-3 text-slate-600 dark:text-slate-400 font-sans">
                            Direct Planetary Output
                          </td>
                          <td className="py-2 px-3 text-right">
                            <span className="text-[10px] font-sans text-slate-400 italic">
                              🔒 Pro Only
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="p-4 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-300 dark:border-amber-500/30 rounded-xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                  <div className="space-y-0.5">
                    <h4 className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                      <span>🔒</span> Unlock Deep Mahāvidyā Archetypal Alignment
                    </h4>
                    <p className="text-[11px] text-slate-600 dark:text-slate-400">
                      Free accounts see standard numbers. Upgrade to unlock the 10 Mahāvidyā psychological reflections, audio formulas & custom timing directives.
                    </p>
                  </div>
                  <Link
                    href="/pricing"
                    className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow shrink-0 inline-block text-center"
                  >
                    ⭐ Upgrade to Pro
                  </Link>
                </div>
              </div>
            )}

            {/* 🌟 Simple, Reflective Mahāvidyā & Planetary Principle Modal */}
            {selectedArchetype && (
              <div
                className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn"
                onClick={() => setSelectedArchetype(null)}
              >
                <div
                  className="bg-white dark:bg-slate-900 border border-amber-200 dark:border-amber-500/30 rounded-2xl max-w-lg w-full p-6 sm:p-7 space-y-5 shadow-2xl relative"
                  onClick={e => e.stopPropagation()}
                >
                  {/* Modal Header */}
                  <div className="flex justify-between items-start border-b border-slate-100 dark:border-slate-800 pb-3">
                    <div className="flex items-center gap-3">
                      <span className="w-10 h-10 rounded-xl bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 font-black font-mono text-lg flex items-center justify-center border border-amber-300 dark:border-amber-500/40">
                        #{selectedArchetype.num}
                      </span>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                            {selectedArchetype.archetype} — {selectedArchetype.planet}
                          </h3>
                        </div>
                        <span className="text-xs text-amber-700 dark:text-amber-400 font-semibold">
                          Core Principle: {selectedArchetype.principle}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => setSelectedArchetype(null)}
                      className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-all font-bold text-sm"
                    >
                      ✕
                    </button>
                  </div>

                  {/* Gentle Story & Reflection */}
                  <div className="space-y-3 text-slate-700 dark:text-slate-300 text-sm leading-relaxed">
                    {selectedArchetype.storyLines.map((line, idx) => (
                      <p key={idx} className={idx === selectedArchetype.storyLines.length - 1 ? 'font-medium text-slate-900 dark:text-white' : ''}>
                        {line}
                      </p>
                    ))}
                  </div>

                  {/* Daily Alignment Takeaway */}
                  <div className="p-4 bg-amber-50/80 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30 rounded-xl space-y-1">
                    <p className="text-xs sm:text-sm font-semibold text-amber-950 dark:text-amber-200 leading-snug">
                      ✨ {selectedArchetype.takeaway}
                    </p>
                    <span className="text-[11px] text-amber-800/80 dark:text-amber-300/80 block pt-0.5">
                      It will help you align with this energy in daily life.
                    </span>
                  </div>

                  {/* Modal Footer */}
                  <div className="pt-1 flex justify-end">
                    <button
                      onClick={() => setSelectedArchetype(null)}
                      className="px-5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow"
                    >
                      Got it, close
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

                      {/* 🌟 Relevance of Mahāvidyās, Planets & Numbers Modal */}
            {showRelevanceModal && (
              <div
                className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn"
                onClick={() => setShowRelevanceModal(false)}
              >
                <div
                  className="bg-white dark:bg-slate-900 border border-amber-200 dark:border-amber-500/30 rounded-2xl max-w-xl w-full p-6 sm:p-7 space-y-5 shadow-2xl relative max-h-[90vh] overflow-y-auto"
                  onClick={e => e.stopPropagation()}
                >
                  {/* Header */}
                  <div className="flex justify-between items-start border-b border-slate-100 dark:border-slate-800 pb-3">
                    <div>
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                        <span>✨</span> The Relevance of Mahāvidyās with Planets & Numbers
                      </h3>
                      <span className="text-xs text-slate-500">Bridging Sound Vibrations, Psychology, and Archetypal Wisdom</span>
                    </div>
                    <button
                      onClick={() => setShowRelevanceModal(false)}
                      className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-all font-bold text-sm"
                    >
                      ✕
                    </button>
                  </div>

                  {/* Body Content */}
                  <div className="space-y-4 text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                    <p>
                      In modern numerology, people often ask: <em>"Why are ancient Mahāvidyās mapped to our birth numbers and planets?"</em>
                    </p>

                    {/* The 3-Tier Layer Explanation */}
                    <div className="space-y-2.5 pt-1">
                      <div className="p-3 bg-amber-50/70 dark:bg-amber-500/10 border border-amber-200/80 dark:border-amber-500/30 rounded-xl space-y-1">
                        <strong className="text-amber-900 dark:text-amber-300 font-bold block text-xs">
                          1. The Number (The Rhythm & Vibration)
                        </strong>
                        <p className="text-[12px] text-slate-600 dark:text-slate-400">
                          The numbers (0 to 9) represent the quantitative vibration—the exact timing cycle, day roots, and mathematical pulses in your daily life.
                        </p>
                      </div>

                      <div className="p-3 bg-sky-50/70 dark:bg-sky-500/10 border border-sky-200/80 dark:border-sky-500/30 rounded-xl space-y-1">
                        <strong className="text-sky-900 dark:text-sky-300 font-bold block text-xs">
                          2. The Planet / Graha (The Psychological Lens)
                        </strong>
                        <p className="text-[12px] text-slate-600 dark:text-slate-400">
                          Planets act as cognitive lenses. For example, Sun gives you an urge to lead, Moon creates emotional sensitivity, and Mercury drives commercial quickness.
                        </p>
                      </div>

                      <div className="p-3 bg-emerald-50/70 dark:bg-emerald-500/10 border border-emerald-200/80 dark:border-emerald-500/30 rounded-xl space-y-1">
                        <strong className="text-emerald-900 dark:text-emerald-300 font-bold block text-xs">
                          3. The Mahāvidyā (The Archetypal Mastery & Solution)
                        </strong>
                        <p className="text-[12px] text-slate-600 dark:text-slate-400">
                          Mahāvidyās are the 10 foundational states of cosmic intelligence. While a planet shows your <em>automatic tendency or shadow</em>, the Mahāvidyā provides the <em>wisdom to master and balance it</em>.
                        </p>
                      </div>
                    </div>

                    {/* Simple Musical Analogy */}
                    <div className="p-3.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-xs space-y-1">
                      <span className="font-bold text-slate-900 dark:text-white block">🎵 A Simple Relatable Analogy:</span>
                      <p className="italic text-slate-600 dark:text-slate-400">
                        "Think of life like playing a musical instrument: The <strong>Number</strong> is the tempo (speed), the <strong>Planet</strong> is the musical note you play, and the <strong>Mahāvidyā</strong> is the inner poise and mastery of the musician that turns noise into beautiful harmony."
                      </p>
                    </div>

                    <p>
                      When you know the Mahāvidyā principle behind your numbers, you stop fighting against life's timing. You understand when to take initiative (Tārā), when to listen (Tripurasundarī), when to remain still (Bagalāmukhī), and when to let the old dissolve (Kālī).
                    </p>
                  </div>

                  {/* Footer */}
                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={() => setShowRelevanceModal(false)}
                      className="px-5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow"
                    >
                      Understood, close
                    </button>
                  </div>
                </div>
              </div>
            )}

                      {/* 🌟 Upgrade Prompt Modal */}
            {showUpgradeModal && (
              <div
                className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn"
                onClick={() => setShowUpgradeModal(false)}
              >
                <div
                  className="bg-white dark:bg-slate-900 border border-amber-200 dark:border-amber-500/30 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl text-center"
                  onClick={e => e.stopPropagation()}
                >
                  <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 flex items-center justify-center text-2xl mx-auto border border-amber-300 dark:border-amber-500/40">
                    ⭐
                  </div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    Unlock Pro Numerology Reports & Formulas
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    Get full access to step-by-step Chaldean letter calculations, 10 Mahāvidyā psychological archetypes, and deep behavioral remediation for missing numbers.
                  </p>
                  <div className="flex gap-2 justify-center pt-2">
                    <button
                      onClick={() => setShowUpgradeModal(false)}
                      className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold rounded-xl text-xs hover:bg-slate-200"
                    >
                      Maybe Later
                    </button>
                    <Link
                      href="/pricing"
                      onClick={() => setShowUpgradeModal(false)}
                      className="px-5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow inline-block"
                    >
                      Unlock Pro Access
                    </Link>
                  </div>
                </div>
              </div>
            )}

          {/* Card 8: Life Chapters (Pinnacles & Challenges) */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold flex items-center justify-center font-mono">
                  8
                </span>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Life Chapters</h3>
              </div>
              <span className="text-xs text-slate-500 font-mono">Pinnacle Transition (36 - Destiny)</span>
            </div>

            {/* Chapters List */}
            <div className="space-y-3">
              {report.life_chapters && report.life_chapters.length > 0 ? (
                report.life_chapters.map((ch, idx) => {
                  const icons = ['🚩', '🧘', '❤️', '👑'];
                  return (
                    <div
                      key={idx}
                      className="p-3.5 bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800 rounded-xl flex items-start gap-3"
                    >
                      <span className="text-xl shrink-0 mt-0.5">{icons[idx] || '✨'}</span>
                      <div className="space-y-1 flex-1">
                        <div className="flex justify-between items-baseline">
                          <span className="text-xs font-extrabold text-slate-900 dark:text-white font-mono">
                            {ch.age_span}
                          </span>
                          <span className="text-[10px] font-bold text-amber-700 dark:text-amber-400 font-mono">
                            Pinnacle {ch.pinnacle_number} • Challenge {ch.challenge_number}
                          </span>
                        </div>
                        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">{ch.chapter_title}</h4>
                        <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">{ch.description}</p>
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-xs text-slate-500">No life chapters calculated for this profile.</p>
              )}
            </div>
          </div>

          {/* 📅 12-MONTH ANNUAL CALENDAR FORECAST (WITH DROPDOWN) */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-slate-100 dark:border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <CalendarIcon />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  12-Month Calendar Forecast for {formData.target_year}
                </h3>
              </div>
              
              {/* Dropdown Month Selector */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Select Month:</span>
                <select
                  value={formData.target_month}
                  onChange={e => {
                    const m = parseInt(e.target.value);
                    setFormData({ ...formData, target_month: m });
                    fetchReport(m);
                  }}
                  className="bg-slate-50 dark:bg-slate-950 border border-amber-300 dark:border-amber-500/40 rounded-lg px-2.5 py-1 text-xs font-bold font-mono text-slate-900 dark:text-white focus:outline-none"
                >
                  {report.all_twelve_months?.map(m => (
                    <option key={m.month_index} value={m.month_index}>
                      {m.month_name} (PM {m.personal_month_number})
                    </option>
                  )) || (
                    <option value={formData.target_month}>Month {formData.target_month}</option>
                  )}
                </select>
              </div>
            </div>

            {/* Selected Month Highlight Card */}
            <div className="p-4 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-300/80 dark:border-amber-500/40 rounded-xl space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-extrabold text-amber-900 dark:text-amber-300">
                  {report.target_month_name} {formData.target_year} (Personal Month {report.all_twelve_months?.[report.target_month_index - 1]?.personal_month_number ?? report.target_month_index})
                </span>
                <span className="px-2.5 py-0.5 rounded-full bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 text-xs font-mono font-bold">
                  Peak Launch Dates: {report.peak_launch_dates?.length ? report.peak_launch_dates.join(', ') : 'None'}
                </span>
              </div>
              <h4 className="text-xs font-bold text-slate-900 dark:text-white">{report.active_month_theme}</h4>
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">{report.active_month_guidance}</p>
            </div>

            {/* 12-Month Quick Tabs Bar */}
            <div className="grid grid-cols-4 sm:grid-cols-6 gap-1.5 pt-1">
              {report.all_twelve_months?.map(m => (
                <button
                  key={m.month_index}
                  onClick={() => {
                    setFormData({ ...formData, target_month: m.month_index });
                    fetchReport(m.month_index);
                  }}
                  className={`p-2 rounded-lg text-center border transition-all ${
                    formData.target_month === m.month_index
                      ? 'bg-amber-500 text-slate-950 border-amber-600 font-bold shadow-sm'
                      : 'bg-slate-50 dark:bg-slate-950 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-800 hover:border-amber-300'
                  }`}
                >
                  <span className="text-[10px] uppercase block leading-none">{m.month_name.slice(0, 3)}</span>
                  <span className="text-xs font-mono font-bold block mt-1">PM {m.personal_month_number}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 🛡️ CONSTRUCTIVE GROWTH BLINDSPOTS */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-3">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span>🛡️</span> Constructive Growth Blindspots (Shadow Balance)
              </h3>
              <span className="text-xs text-slate-500 font-mono">Root • Destiny • Challenge</span>
            </div>

            <div className="space-y-3">
              {report.growth_blindspots?.map((b, idx) => (
                <div
                  key={idx}
                  className="p-3.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl space-y-1.5"
                >
                  <span className="text-xs font-bold text-rose-800 dark:text-rose-400 block">{b.blindspot_title}</span>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">{b.tendency_description}</p>
                  <div className="text-[11px] text-slate-800 dark:text-slate-200 pt-1 font-medium border-t border-slate-200 dark:border-slate-800">
                    <strong className="text-amber-700 dark:text-amber-400 font-semibold">🛠️ Correction: </strong>
                    {b.corrective_action}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 🧠 2GB BANDWIDTH SIMULATOR */}
          <div className="bg-gradient-to-br from-indigo-50/70 dark:from-indigo-950/30 via-white dark:via-slate-900 to-white dark:to-slate-900 border border-indigo-200/80 dark:border-indigo-500/30 rounded-2xl p-5 sm:p-6 shadow-sm space-y-3">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <HardDriveIcon />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">The 2GB Mental Storage Protocol</h3>
              </div>
              <button
                onClick={() => setIsStorageCleared(!isStorageCleared)}
                className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition-all shadow"
              >
                {isStorageCleared ? '↺ Reset' : '🧹 Clear Storage'}
              </button>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              When your subconscious is full of old resentment loops, there is 0MB space for timing opportunities.
            </p>
            <div className="p-3 bg-white dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 font-mono text-xs flex justify-between">
              <span>Bandwidth:</span>
              <span className={isStorageCleared ? 'text-emerald-600 font-bold' : 'text-amber-700 font-bold'}>
                {isStorageCleared ? '1.85 GB Free (Clean Receiver)' : '1.9 GB Full (Worry Loops)'}
              </span>
            </div>
          </div>

        </div>
      </div>
      )}

      {/* Active Chart Selector Modal */}
      
      {/* 🌟 HIDDEN PASSION EXPLORER MODAL (ALL 1-9 NUMBERS) */}
      {showHiddenPassionModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-purple-50/50 dark:bg-purple-950/20">
              <div className="flex items-center gap-2.5">
                <span className="w-8 h-8 rounded-xl bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 font-bold flex items-center justify-center text-base">
                  🔥
                </span>
                <div>
                  <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                    Hidden Passion Archetypes (अंक 1 से 9)
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    नाम में सबसे अधिक दोहराया जाने वाला अंक = आपकी आंतरिक स्वाभाविक शक्ति व जुनून
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowHiddenPassionModal(false)}
                className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 font-bold flex items-center justify-center transition-all"
              >
                ✕
              </button>
            </div>

            {/* Numbers 1-9 Tab Navigation */}
            <div className="p-3 bg-slate-50 dark:bg-slate-950/60 border-b border-slate-200 dark:border-slate-800 overflow-x-auto">
              <div className="flex gap-1.5 min-w-max">
                {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => {
                  const detail = HIDDEN_PASSION_GUIDE[num];
                  const isSelected = activeHiddenPassionTab === num;
                  return (
                    <button
                      key={num}
                      onClick={() => setActiveHiddenPassionTab(num)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold font-mono flex items-center gap-1.5 transition-all ${
                        isSelected
                          ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                          : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:border-purple-300'
                      }`}
                    >
                      <span>{detail.icon}</span>
                      <span>#{num}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Active Number Details Content */}
            <div className="p-6 overflow-y-auto space-y-4 text-sm flex-1">
              {(() => {
                const info = HIDDEN_PASSION_GUIDE[activeHiddenPassionTab];
                return (
                  <div className="space-y-4 animate-fadeIn">
                    
                    {/* Header Banner */}
                    <div className="p-4 bg-gradient-to-br from-purple-50 dark:from-purple-950/40 to-slate-50 dark:to-slate-900 border border-purple-200/80 dark:border-purple-500/30 rounded-2xl flex items-center justify-between">
                      <div>
                        <span className="text-xs font-bold text-purple-700 dark:text-purple-400 uppercase tracking-wider block">
                          {info.planet}
                        </span>
                        <h4 className="text-lg font-black text-slate-900 dark:text-white mt-0.5">
                          {info.hindiTitle}
                        </h4>
                      </div>
                      <span className="text-3xl">{info.icon}</span>
                    </div>

                    {/* Core Drive & Natural Superpower */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="p-3.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl space-y-1">
                        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                          🎯 आंतरिक प्रेरणा (Core Drive)
                        </span>
                        <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                          {info.coreDrive}
                        </p>
                      </div>

                      <div className="p-3.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl space-y-1">
                        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                          ⚡ प्राकृतिक प्रतिभा (Natural Talent)
                        </span>
                        <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                          {info.superpower}
                        </p>
                      </div>
                    </div>

                    {/* Repetition Law Meter */}
                    <div className="p-4 bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200/80 dark:border-emerald-500/30 rounded-xl space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-emerald-800 dark:text-emerald-400 flex items-center gap-1.5">
                          <span>🔄</span> दोहराव का नियम (Law of Repetition Tiers)
                        </span>
                        <span className="text-[10px] font-mono font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-900/50 px-2 py-0.5 rounded-full">
                          3x = 100% Peak Potential
                        </span>
                      </div>
                      <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-mono">
                        {info.repetitionRule}
                      </p>
                    </div>

                    {/* Shadow Side & Overdrive Warning */}
                    <div className="p-4 bg-rose-50/60 dark:bg-rose-950/20 border border-rose-200/80 dark:border-rose-500/30 rounded-xl space-y-1.5">
                      <span className="text-xs font-bold text-rose-800 dark:text-rose-400 flex items-center gap-1.5">
                        <span>⚠️</span> अति व शैडो साइड (4x+ Repetition Caution)
                      </span>
                      <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                        {info.shadowWarning}
                      </p>
                    </div>

                  </div>
                );
              })()}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-100 dark:border-slate-800 flex justify-end bg-slate-50/50 dark:bg-slate-950/50">
              <button
                onClick={() => setShowHiddenPassionModal(false)}
                className="px-5 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold transition-all shadow-md"
              >
                Close Guide
              </button>
            </div>

          </div>
        </div>
      )}

      
      {/* 🔍 UNIVERSAL NUMBER CALCULATION & MEANING INSPECTOR MODAL */}
      {inspectedNumber && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl max-w-xl w-full flex flex-col shadow-2xl overflow-hidden animate-scaleUp">
            
            {/* Header */}
            <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-gradient-to-r from-amber-50/60 dark:from-amber-950/20 to-slate-50 dark:to-slate-900">
              <div className="flex items-center gap-3">
                <span className="w-10 h-10 rounded-2xl bg-amber-500 text-slate-950 font-black flex items-center justify-center text-lg font-mono shadow-md">
                  {inspectedNumber.number}
                </span>
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400 font-mono">
                    {inspectedNumber.badge} • {inspectedNumber.planet}
                  </span>
                  <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                    {inspectedNumber.title}
                  </h3>
                </div>
              </div>
              <button
                onClick={() => setInspectedNumber(null)}
                className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 font-bold flex items-center justify-center transition-all"
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4 text-xs overflow-y-auto max-h-[75vh]">
              
              {/* Formula & Step-by-Step Calculation */}
              <div className="p-3.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block font-mono">
                  📐 Step-by-Step Calculation (गणितीय सूत्र)
                </span>
                <p className="text-xs font-mono font-bold text-amber-900 dark:text-amber-300">
                  {inspectedNumber.formula}
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 pt-0.5">
                  {inspectedNumber.explanation}
                </p>
              </div>

              {/* Core Meaning & Epicycle Life Stage */}
              <div className="p-4 bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-200/70 dark:border-indigo-500/30 rounded-2xl space-y-1.5">
                <span className="text-[11px] font-bold text-indigo-800 dark:text-indigo-400 flex items-center gap-1.5 uppercase tracking-wider">
                  <span>{inspectedNumber.icon}</span> अंक का अर्थ व जीवन प्रभाव (Core Meaning)
                </span>
                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                  {inspectedNumber.meaning}
                </p>
              </div>

              {/* Actionable Directive (क्या करें) */}
              <div className="p-3.5 bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200/80 dark:border-emerald-500/30 rounded-xl space-y-1">
                <span className="text-[11px] font-bold text-emerald-800 dark:text-emerald-400 flex items-center gap-1">
                  <span>✅</span> व्यावहारिक निर्देश (Actionable Guidance)
                </span>
                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                  {inspectedNumber.actionDirective}
                </p>
              </div>

              {/* Warning / Pitfall to Avoid (किससे बचें) */}
              {inspectedNumber.warningNotice && (
                <div className="p-3.5 bg-rose-50/60 dark:bg-rose-950/20 border border-rose-200/80 dark:border-rose-500/30 rounded-xl space-y-1">
                  <span className="text-[11px] font-bold text-rose-800 dark:text-rose-400 flex items-center gap-1">
                    <span>⚠️</span> सावधानी (Pitfall to Avoid)
                  </span>
                  <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                    {inspectedNumber.warningNotice}
                  </p>
                </div>
              )}

            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-100 dark:border-slate-800 flex justify-end bg-slate-50/50 dark:bg-slate-950/50">
              <button
                onClick={() => setInspectedNumber(null)}
                className="px-5 py-2 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-950 rounded-xl text-xs font-bold transition-all shadow-sm"
              >
                Close Details
              </button>
            </div>

          </div>
        </div>
      )}

      <ActiveChartSelectorModal
        isOpen={activeChartModalOpen}
        onClose={() => setActiveChartModalOpen(false)}
      />
    </div>
  );
}
