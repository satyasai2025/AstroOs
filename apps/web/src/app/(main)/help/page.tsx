"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { Card, Icon, type IconName } from "@/components/ui";

interface FeatureGuide {
  id: string;
  title: string;
  category: "core" | "predictive" | "technical" | "life" | "research" | "settings";
  categoryLabel: string;
  route: string;
  icon: IconName;
  tagline: string;
  whatIsIt: string;
  howToUse: string[];
  keyInputs: string[];
  howToInterpret: string[];
  proTip?: string;
}

const FEATURE_GUIDES: FeatureGuide[] = [
  // ── 1. CORE CHARTS ──
  {
    id: "birth-chart",
    title: "Interactive Kundli & Birth Chart",
    category: "core",
    categoryLabel: "Core Charts",
    route: "/charts/birth",
    icon: "compass",
    tagline: "North & South Indian interactive Kundli with planetary degrees and aspects.",
    whatIsIt:
      "The foundation of Vedic horoscope analysis. Generates the Rashi (D-1) birth chart, Bhava Chalit chart, exact planetary degrees, retrograde (R) status, combustion (C), dignity (exalted/debilitated), and house ownerships.",
    howToUse: [
      "Click '+ Quick Action' in the top header or sidebar and select 'New Natal Chart'.",
      "Enter Native Name, Birth Date, Exact Time, and City/Coordinates (with Timezone).",
      "Switch between North Indian (Diamond) and South Indian (Box) formats using the layout toggle.",
      "Hover or click any planet/house to inspect aspect rays, nakshatra lords, and sub-divisions.",
    ],
    keyInputs: ["Birth Date & Time", "Latitude & Longitude", "Ayanamsa (Default: Lahiri / Chitra Paksha)"],
    howToInterpret: [
      "Lagna (Ascendant): Represents the physical body, general vitality, temperament, and life direction.",
      "Planets in Kendras (1, 4, 7, 10) & Trikonas (1, 5, 9): Strong pillars providing strength and auspicious results.",
      "Dusthanas (6, 8, 12): Houses of obstacles, transformation, hidden matters, and spiritual liberation.",
    ],
    proTip: "Use the 'Active Chart Selector' in the top navigation bar to quickly switch between saved charts without leaving your current analysis.",
  },
  {
    id: "divisional-charts",
    title: "Divisional Charts (Shodashvarga D-1 to D-60)",
    category: "core",
    categoryLabel: "Core Charts",
    route: "/charts?view=divisional",
    icon: "grid",
    tagline: "Micro-harmonic division charts for specific life areas (D-9, D-10, D-7, etc.).",
    whatIsIt:
      "Classical Vedic astrology divides each 30° zodiac sign into harmonic sub-charts to assess specific life areas. Parasara defines 16 core divisional charts (Shodashvarga).",
    howToUse: [
      "Select an active chart, then navigate to Divisional Charts.",
      "Use the varga selector tab to switch between D-9 (Navamsha), D-10 (Dashamsha), D-7 (Saptamsha), D-12 (Dwadashamsha), D-60 (Shashtiamsha), etc.",
      "Compare planet placements between the D-1 Rashi chart and the selected divisional chart.",
    ],
    keyInputs: ["Varga Chart Type (D-1 to D-60)", "High-accuracy birth time (critical for D-60)."],
    howToInterpret: [
      "D-9 Navamsha: Confirms true planetary strength, spouse characteristics, post-marriage life, and inner destiny (Bhagya). Vargottama planets (same sign in D-1 & D-9) give exceptionally strong results.",
      "D-10 Dashamsha: Career peak, profession status, executive authority, and public achievements.",
      "D-7 Saptamsha: Children, creative output, and lineage continuation.",
    ],
    proTip: "If a planet is debilitated in D-1 but exalted in D-9, it indicates Neecha Bhanga and eventual rise through perseverance.",
  },
  {
    id: "chart-compare",
    title: "Chart Comparison & Synastry",
    category: "core",
    categoryLabel: "Core Charts",
    route: "/charts/compare",
    icon: "layers",
    tagline: "Side-by-side multi-chart comparison, Venn diagrams, and planetary difference metrics.",
    whatIsIt:
      "A dual-workspace environment allowing astrologers to place two or more natal charts side-by-side to compare planetary placements, aspects, strengths, and mutual synastry.",
    howToUse: [
      "Click 'Select Primary Chart' and 'Select Secondary Chart' from your saved library.",
      "Switch between 'Side-by-Side Grid', 'Overlay Mode', 'Radar Strength Comparison', and 'Venn Aspects'.",
      "Export the comparison summary as PDF, JSON, or CSV for client reports.",
    ],
    keyInputs: ["Two or more saved charts from Chart Library."],
    howToInterpret: [
      "Overlay Aspects: Mutual trines (1/5/9) between two charts foster natural harmony and shared values.",
      "Oppositions (1/7): Indicate strong attraction but require compromise and balance.",
      "Mutual 6/8 (Shadashtaka): Points of friction, health friction, or misunderstandings.",
    ],
    proTip: "Use the 'Difference Highlight' filter to instantly reveal planets sharing the same nakshatra or sign across both charts.",
  },
  {
    id: "chart-rectification",
    title: "Birth Time Rectification",
    category: "core",
    categoryLabel: "Core Charts",
    route: "/charts/rectify",
    icon: "clock",
    tagline: "Lagna boundary sensitivity, Upagrahas, and micro-interval verification.",
    whatIsIt:
      "A tool to verify and fine-tune birth times when exact birth records are uncertain. Analyzes how sensitive the Ascendant, Navamsha Lagna, and sub-lords are to minute shifts in birth time.",
    howToUse: [
      "Load the client chart in the Rectification module.",
      "Adjust the slider by +/- 1 to 15 minutes to observe where Lagna, D-9 Navamsha Lagna, or KP Sub-Lord changes.",
      "Cross-verify the timing with past major life milestones (e.g. marriage date, first job).",
    ],
    keyInputs: ["Approximate birth time", "Known past life events for validation."],
    howToInterpret: [
      "Ascendant Degree Boundary: If Lagna is at 29°58' or 0°02', a 1-minute shift alters the entire house structure.",
      "D-9 Lagna shifts every ~13 minutes on average; D-60 shifts every ~2 minutes.",
    ],
  },

  // ── 2. PREDICTIVE & TIMING ──
  {
    id: "dasha-analysis",
    title: "Vimshottari Dasha Explorer",
    category: "predictive",
    categoryLabel: "Predictive & Timing",
    route: "/charts?view=dasha",
    icon: "clock",
    tagline: "120-year multi-tier planetary period tree (Maha, Antar, Pratyantar, Sookshma).",
    whatIsIt:
      "The primary timing mechanism in Parashari Vedic Astrology. Calculates the 120-year Vimshottari Dasha cycles based on the Moon's natal nakshatra degree at birth.",
    howToUse: [
      "Open Dasha view for any chart.",
      "Click into any Mahadasha (e.g. Jupiter) to expand its Antardashas (sub-periods).",
      "Click deeper to view Pratyantardasha (level 3) and Sookshma Dasha (level 4) with start and end dates.",
      "Review the active period highlighted with the live countdown badge.",
    ],
    keyInputs: ["Birth Time", "Ayanamsa selection", "Moon longitude at birth."],
    howToInterpret: [
      "Mahadasha Lord: Sets the general theme, environment, and overarching focus of life for 6-20 years.",
      "Antardasha Lord: Triggers concrete events by activating its house lordship, placement, and natal aspects.",
      "Favorable Period: When Dasha Lord and Antardasha Lord are in Kendra/Trikona from each other (1-5-9 or 1-4-7-10).",
    ],
    proTip: "Check the Tara Bala of the running Dasha Lord relative to your Janma Nakshatra to confirm whether its results will be smooth (Sampat/Kshema) or challenging (Vipat/Naidhana).",
  },
  {
    id: "transit-analysis",
    title: "Gochara / Planetary Transits",
    category: "predictive",
    categoryLabel: "Predictive & Timing",
    route: "/charts?view=timeline",
    icon: "orbit",
    tagline: "Live real-time planetary movements superimposed on your natal chart.",
    whatIsIt:
      "Tracks real-time planetary positions across the zodiac and superimposes them onto the natal houses and natal planets to identify active triggers, Sade Sati, Jupiter returns, and nodal eclipses.",
    howToUse: [
      "Select an active chart and open Transit Analysis.",
      "Use the date picker or transit slider to jump forward or backward in time.",
      "Inspect the 'Sade Sati & Dhaiya' status card for Saturn's transit over the 12th, 1st, and 2nd from natal Moon.",
      "View live benefic Jupiter transits over 2nd, 5th, 7th, 9th, 11th from Moon.",
    ],
    keyInputs: ["Target transit date & time", "Base natal chart."],
    howToInterpret: [
      "Transits only deliver what the running Dasha promises. A good transit during an unfavorable Dasha gives mild relief, whereas a good transit during a favorable Dasha delivers peak success.",
      "Ashtakavarga BAV bindus in the transiting house determine the final delivery of results (28+ SAV points indicate smooth transit).",
    ],
  },
  {
    id: "sarvatobhadra-chakra",
    title: "Sarvatobhadra Chakra (SBC)",
    category: "predictive",
    categoryLabel: "Predictive & Timing",
    route: "/charts/sbc",
    icon: "grid",
    tagline: "Classical 9x9 astrological grid with 28 Nakshatras & multi-directional Vedha rays.",
    whatIsIt:
      "A classical, high-level research grid described in Saravali and Narapati Jayacharya. 28 Nakshatras (including Abhijit) are mapped around the border. Planets cast Front (Direct), Left, and Right Vedha (piercing rays) depending on their direct/retrograde speed.",
    howToUse: [
      "Select your Janma Nakshatra (or any other reference star) from the dropdown.",
      "Click any border cell on the 9x9 grid to highlight its three Vedha rays (Green=Front, Blue=Left, Red=Right).",
      "Inspect the Vedha Result panel to see if any transiting Benefic (Jupiter, Venus, Mercury) or Malefic (Saturn, Mars, Rahu, Ketu, Sun) is casting a ray on your star.",
      "Run date-range scans to find exact dates when benefic Vedha hits occur.",
    ],
    keyInputs: ["Reference Nakshatra (Janma, Karma, Adhana, etc.)", "Transit Date."],
    howToInterpret: [
      "Benefic Vedha on Janma Nakshatra: Financial gain, auspicious events, health recovery, and success.",
      "Malefic Vedha on Janma/Karma Nakshatra: Obstacles, delays, mental distress, or sudden health watchouts.",
      "Empty Vedha: Neutral day with normal routine.",
    ],
  },
  {
    id: "tarabala-module",
    title: "Navatara / Tarabala Matrix",
    category: "predictive",
    categoryLabel: "Predictive & Timing",
    route: "/charts/tarabala",
    icon: "star",
    tagline: "9-fold Tara categories (Janma, Sampat, Vipat...) with Dasha convergence.",
    whatIsIt:
      "Calculates the relative strength and compatibility between the Moon's natal nakshatra and other transiting planets or Dasha lords divided into 9 repeating Tara cycles.",
    howToUse: [
      "Enter your Janma Nakshatra and optional Lagna Nakshatra.",
      "Add your active dasha chain (e.g. 'jupiter,saturn,mercury') to unlock multi-tier convergence scoring.",
      "Review the Special Points Table (Janma, Karma, Samudayika, Sanghatika, Jaati, Naidhana, Desa, Abhisheka, etc.).",
    ],
    keyInputs: ["Janma Nakshatra", "Active Dasha Lord chain", "Transit positions."],
    howToInterpret: [
      "Favorable Taras (5): Sampat (Wealth - 2nd), Kshema (Well-being - 4th), Sadhaka (Success - 6th), Mitra (Friend - 8th), Paramamitra (Best Friend - 9th).",
      "Unfavorable Taras (4): Janma (Self/Strain - 1st), Vipat (Danger/Loss - 3rd), Pratyari (Obstacles - 5th), Naidhana/Vadha (Destruction - 7th).",
      "Convergence Count: When Mahadasha + Antardasha + Transit lords are simultaneously in favorable Taras, high-impact success occurs.",
    ],
  },
  {
    id: "shadbala-strengths",
    title: "Shadbala & Planetary Strengths",
    category: "predictive",
    categoryLabel: "Predictive & Timing",
    route: "/charts?view=strength",
    icon: "bar",
    tagline: "6-fold planetary strength calculation (Sthana, Dig, Kaala, Chesta, Naisargika, Drik).",
    whatIsIt:
      "Calculates the classical Shadbala requirement for each of the 7 major planets in Rupas and Virupas to determine their capacity to yield results.",
    howToUse: [
      "Open Shadbala view for the active chart.",
      "Inspect the strength bar chart comparing each planet's total Shadbala against its minimum required threshold (Shadbala Ratio > 1.0).",
      "Break down the sub-components: Sthana Bala (Positional), Dig Bala (Directional), Kaala Bala (Temporal), Chesta Bala (Motional), Naisargika Bala (Natural), and Drik Bala (Aspectual).",
    ],
    keyInputs: ["Birth Time", "Sunrise/Sunset for Kaala Bala", "Planetary Speeds for Chesta Bala."],
    howToInterpret: [
      "Ratio >= 1.0: Planet has sufficient strength to manifest its promise during its Dasha.",
      "Dig Bala (Directional Strength): Jupiter/Mercury strong in 1st house; Sun/Mars strong in 10th; Saturn in 7th; Moon/Venus in 4th.",
      "Ishta Phala vs Kashta Phala: Ishta Phala indicates benefic manifestation capacity; Kashta Phala indicates challenges.",
    ],
  },

  // ── 3. TECHNICAL SYSTEMS ──
  {
    id: "kp-system",
    title: "KP System (Krishnamurti Paddhati)",
    category: "technical",
    categoryLabel: "Technical Systems",
    route: "/charts?view=kp",
    icon: "target",
    tagline: "Placidus house cusps, Sign-Star-Sub lords, and 4-fold house significators.",
    whatIsIt:
      "A precision astrological system pioneered by Prof. K.S. Krishnamurti that subdivides each nakshatra into 9 unequal sub-divisions ('Sub-Lords') to predict events with pinpoint accuracy.",
    howToUse: [
      "Open KP Analysis view.",
      "Inspect the 12 House Cusps table showing Cusp degree, Sign Lord, Star Lord, and Cusp Sub-Lord (CSL).",
      "Review the Planetary Signification table (Levels A, B, C, D) to find which houses each planet signifies.",
      "Check the Ruling Planets (RPs) panel for real-time verification.",
    ],
    keyInputs: ["KP Ayanamsa (Krishnamurti)", "Placidus House System", "High-precision birth time."],
    howToInterpret: [
      "Golden Rule of KP: The Star Lord of a planet shows the matter/house involved, but the Sub-Lord determines whether the result will be positive or negative.",
      "For Marriage: 7th Cusp Sub-Lord must signify houses 2, 7, or 11 (and not purely 1, 6, 10).",
      "For Career: 10th CSL must signify 2, 6, 10, or 11.",
    ],
    proTip: "KP Cuspal Sub-Lord is the final verdict giver in Krishnamurti Paddhati. Never rely on sign placement alone.",
  },
  {
    id: "prashna-horary",
    title: "Prashna (Horary) & Arabic Parts",
    category: "technical",
    categoryLabel: "Technical Systems",
    route: "/charts/prashna",
    icon: "sparkle",
    tagline: "Horary question charts using KP 1-249 seeds and classical Arabic Sahams.",
    whatIsIt:
      "Used when a client asks a specific question at a specific moment, or when birth time is completely unknown. Supports KP Horary number seeding (1-249) and Arabic Parts calculation (Saham of Fortune, Spirit, Marriage, Trade, etc.).",
    howToUse: [
      "Navigate to Prashna module.",
      "Enter the question text and select a KP Horary Number between 1 and 249 provided by the querent.",
      "Set the current query location and click 'Calculate Prashna Chart'.",
      "Inspect the Ruling Planets, Moon's Star/Sub Lord, and relevant house cusps.",
    ],
    keyInputs: ["Horary Seed Number (1-249)", "Current query timestamp and GPS coordinates."],
    howToInterpret: [
      "Moon's Position: The nakshatra and sub-lord of the Moon reveals the true underlying question in the querent's mind.",
      "If the Ascendant Sub-Lord is in retrograde or signifies house 12/8, the inquiry may face cancellations or reversals.",
      "Arabic Parts (Sahams): Fortunate Sahams conjunct benefics in Kendra indicate fruitful outcomes.",
    ],
  },
  {
    id: "jaimini-system",
    title: "Jaimini Astrology & Chara Karakas",
    category: "technical",
    categoryLabel: "Technical Systems",
    route: "/charts?view=jaimini",
    icon: "book",
    tagline: "7/8 Chara Karakas (Atmakaraka, Amatyakaraka), Karakamsha, and Arudha Padas.",
    whatIsIt:
      "The classical system of Maharishi Jaimini based on movable significators (Chara Karakas determined by planetary degrees in sign) and Rashi Dashas (Chara Dasha, Sthira Dasha).",
    howToUse: [
      "Open Jaimini Analysis view.",
      "Inspect the 7/8 Chara Karakas table: AK (Atmakaraka - highest degree), AmK (Amatyakaraka - career), BK (Bhratru), MK (Matru), PK (Putra), GK (Gnati), DK (Darakaraka - lowest degree / spouse).",
      "Check Karakamsha Lagna (sign occupied by AK in D-9 Navamsha) and Arudha Lagna (AL) / Upapada Lagna (UL).",
    ],
    keyInputs: ["Planetary Longitudes within Signs."],
    howToInterpret: [
      "Atmakaraka (AK): Represents the soul's primary spiritual lesson and core identity in this incarnation.",
      "Amatyakaraka (AmK): Shows the nature of professional role, finances, and advisors.",
      "Darakaraka (DK): Depicts spouse characteristics and business partnerships.",
      "Arudha Lagna (AL): Public image, perception, and worldly standing.",
    ],
  },
  {
    id: "yogas-ashtakavarga",
    title: "Yogas & Ashtakavarga",
    category: "technical",
    categoryLabel: "Technical Systems",
    route: "/charts?view=yogas",
    icon: "star",
    tagline: "Classical planetary combinations & 337-point Ashtakavarga distribution.",
    whatIsIt:
      "Automated detection of hundreds of classical Yogas (Gajakesari, Pancha Mahapurusha, Budhaditya, Neechabhanga, Viparita Raja Yogas) alongside Bhinnashtakavarga (BAV) and Sarvashtakavarga (SAV) matrix.",
    howToUse: [
      "Open Yogas view to inspect all active combinations categorized by Raja, Dhana, Nabhasa, and Arishta Yogas.",
      "Switch to Ashtakavarga tab to see the 12-house bindu count (out of 337 total).",
      "Houses with 28+ SAV points denote areas of strength, support, and ease during transits.",
    ],
    keyInputs: ["Planetary coordinates", "House alignments."],
    howToInterpret: [
      "Raja Yogas (Trine Lord + Kendra Lord conjunction/mutual aspect): Bestows power, reputation, and authority.",
      "Dhana Yogas (2nd, 5th, 9th, 11th lord connections): Bestows sustained wealth creation.",
      "SAV Points: 11th house points > 10th house points indicates income exceeds effort (high prosperity).",
    ],
  },

  // ── 4. LIFE DOMAINS & PREDICTIONS ──
  {
    id: "marriage-compatibility",
    title: "Marriage & Relationship Compatibility",
    category: "life",
    categoryLabel: "Life Domains",
    route: "/life/marriage",
    icon: "heart",
    tagline: "Ashtakoota 36-point Guna Milan, Manglik Dosha, and 7th House / D-9 analysis.",
    whatIsIt:
      "Full Vedic relationship compatibility analysis combining the traditional 36-point Guna Milan (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi) with Mangal Dosha check and synastry overlays.",
    howToUse: [
      "Select Boy/Partner 1 Chart and Girl/Partner 2 Chart.",
      "Review the total score out of 36 (Minimum recommended: 18 points).",
      "Inspect critical dosha warnings: Nadi Dosha (8 points) and Bhakoot Dosha (7 points) with cancellation rules.",
      "Review the Kuja / Mangal Dosha assessment for both partners.",
    ],
    keyInputs: ["Two natal birth charts."],
    howToInterpret: [
      "28+ points: Excellent match with deep mental, physical, and spiritual harmony.",
      "18–27 points: Good match with balanced compatibility.",
      "< 18 points: Below threshold; check if Jupiter aspects 7th house or D-9 cancels afflictions before concluding.",
    ],
  },
  {
    id: "career-wealth",
    title: "Career, Profession & Wealth",
    category: "life",
    categoryLabel: "Life Domains",
    route: "/life/career",
    icon: "briefcase",
    tagline: "10th house, D-10 Dashamsha, Indu Lagna, and Dhana Yogas.",
    whatIsIt:
      "Dedicated analysis of career trajectory, vocation, business vs employment, authority, government honors, and wealth accumulation potentials.",
    howToUse: [
      "Open Career module with an active chart.",
      "Review the 10th house Lord, planets in 10th, and dispositor strength in D-10 (Dashamsha).",
      "Inspect the Wealth (Dhana) indicators: 2nd house (Accumulated Wealth), 11th house (Gains), and Indu Lagna.",
    ],
    keyInputs: ["Natal chart", "Accurate birth time for D-10."],
    howToInterpret: [
      "Sun/Mars strong in 10th: Executive leadership, administration, government, entrepreneurship.",
      "Mercury/Jupiter in 10th/2nd: Finance, consulting, analytics, communication, and teaching.",
      "Venus/Rahu: Creative arts, media, technology, international business.",
    ],
  },
  {
    id: "health-wellness",
    title: "Health & Medical Astrology",
    category: "life",
    categoryLabel: "Life Domains",
    route: "/life/health",
    icon: "health",
    tagline: "6th, 8th, 12th houses, Maraka/Badhaka lords, and organ correlations.",
    whatIsIt:
      "Analyzes physical constitution (Ayurvedic Dosha: Vata, Pitta, Kapha), chronic vulnerability zones, and timing of health strains using 6th house (diseases), 8th house (longevity/transformation), and Maraka houses (2, 7).",
    howToUse: [
      "Load the active chart into Health analysis.",
      "Inspect the Ayurvedic dosha balance chart.",
      "Review the vulnerable body parts mapped to afflicted rashis and nakshatras.",
    ],
    keyInputs: ["Natal Chart."],
    howToInterpret: [
      "Afflicted Sun/Lagna Lord: Low vitality, immunity watchout.",
      "Afflicted Moon: Anxiety, sleep disruptions, psychosomatic sensitivities.",
      "Saturn/Mars conjunctions: Joint, blood, or inflammatory tendencies.",
    ],
  },
  {
    id: "life-timeline",
    title: "Life Events & Prediction Timeline",
    category: "life",
    categoryLabel: "Life Domains",
    route: "/life/timeline",
    icon: "calendar",
    tagline: "Chronological visualization of Dasha shifts, key transits, and milestone windows.",
    whatIsIt:
      "Integrates Dasha periods, major Saturn/Jupiter/Rahu transits, and 300+ classical event formulas into a single continuous interactive timeline from birth to 100 years.",
    howToUse: [
      "Select an active chart and open Life Timeline.",
      "Scroll horizontally across the chronological timeline to view past and future milestone windows.",
      "Filter by domain: Career, Marriage, Children, Property, Foreign Travel, Spirituality.",
    ],
    keyInputs: ["Natal Chart."],
    howToInterpret: [
      "High Confluence Windows: Dates where a favorable Mahadasha, supportive Antardasha, and double-transit (Saturn + Jupiter aspecting the event house) align indicate inevitable milestone fulfillment.",
    ],
  },

  // ── 5. VEDIC RESEARCH & KNOWLEDGE BASE ──
  {
    id: "classical-knowledge",
    title: "Classical Knowledge Base (BPHS & Saravali)",
    category: "research",
    categoryLabel: "Vedic Research",
    route: "/knowledge",
    icon: "book",
    tagline: "Direct search & citation of Brihat Parashara Hora Shastra, Saravali, and classical texts.",
    whatIsIt:
      "A searchable digital library of authentic classical Vedic texts including Brihat Parashara Hora Shastra (BPHS), Saravali, Phaladeepika, and Jaimini Sutras with Sanskrit shlokas and English translations.",
    howToUse: [
      "Navigate to Knowledge Base.",
      "Use the search bar to query specific combinations, e.g., 'Jupiter in 10th house' or 'Gajakesari Yoga'.",
      "Read shlokas with verified chapter and verse citations.",
    ],
    keyInputs: ["Keyword or planet/house combination."],
    howToInterpret: [
      "Classical texts provide foundational baseline archetypes. Always synthesize shlokas with contemporary context, country-time-person (Desha-Kaala-Paatra), and overall chart strength.",
    ],
  },
  {
    id: "research-explorer",
    title: "Research Tools & Multi-Chart Cohorts",
    category: "research",
    categoryLabel: "Vedic Research",
    route: "/research/projects",
    icon: "search",
    tagline: "Empirical astrological research, reverse chart search, and rule validation on datasets.",
    whatIsIt:
      "Designed for serious researchers and astrologers. Create research cohorts (e.g. 500 medical doctors, 200 civil servants), run reverse searches to find charts matching complex planetary criteria, and statistically validate predictive rules.",
    howToUse: [
      "Create a research project under Research Explorer.",
      "Import a batch CSV dataset of birth data with verified life events.",
      "Use the Query Builder to test hypotheses (e.g. 'Percentage of charts with Sun-Mercury in 10th in medical cohort').",
      "Review statistical validation accuracy curves and confidence scores.",
    ],
    keyInputs: ["Cohort datasets", "Custom astrological query formulas."],
    howToInterpret: [
      "Helps separate verified astrological principles from folklore through statistical statistical validation.",
    ],
  },
  {
    id: "knowledge-graph",
    title: "Interactive Astrological Knowledge Graph",
    category: "research",
    categoryLabel: "Vedic Research",
    route: "/knowledge-graph",
    icon: "network",
    tagline: "Visual relationship network connecting planets, rashis, houses, and karakatvas.",
    whatIsIt:
      "A graph visualization engine that maps every astrological entity (Grahas, Rashis, Bhavas, Nakshatras, Karakas) and their intricate Vedic relationships (ownership, exaltation, friendship, natural significations).",
    howToUse: [
      "Open Knowledge Graph Explorer.",
      "Click any node (e.g. 'Mars' or '10th House') to reveal all interconnected entities and classical rule links.",
      "Use zoom and pan to explore the web of Vedic astrological connections.",
    ],
    keyInputs: ["Interactive graph explorer."],
    howToInterpret: [
      "Visualizes multi-hop dispositor chains and how energy flows between different house rulers in a horoscope.",
    ],
  },
  {
    id: "pdf-reports",
    title: "Printable PDF Reports & Report Templates Directory",
    category: "research",
    categoryLabel: "Vedic Research & Reports",
    route: "/reports/pdf",
    icon: "document",
    tagline: "Publication-ready PDF & HTML report generation with active backend Jinja2 templates directory.",
    whatIsIt:
      "Generates publication-grade PDF and HTML horoscope reports complete with multi-varga matrices, Gajakesari & Raja Yogas, Vimshottari Dasha sequences, and Sarvatobhadra Chakra (SBC) Vedha analysis. Also displays the active backend report templates directory (horoscope.html, base.html).",
    howToUse: [
      "Navigate to Reports → PDF Reports (/reports/pdf) from the main menu.",
      "Select a saved chart from your library or click '✨ Auto-fill Demo Sample Chart' for instant testing.",
      "Customize Native Name, Report Title, Ayanamsha (Lahiri, KP, Raman), and House System (Placidus, Whole Sign).",
      "Click 'Download Printable PDF Report' to generate and download a standalone high-resolution PDF document.",
      "Inspect the 'Active Report Templates Directory' section to view active report templates loaded on the server.",
    ],
    keyInputs: ["Saved Chart or Birth Date/Time, Coordinates, Ayanamsha, House System"],
    howToInterpret: [
      "Produces a print-ready document with birth chart graphics, planetary dignity tables, active yoga strength scores, dasha periods, and SBC protective/malefic ray breakdowns.",
    ],
    proTip: "Developers can add custom HTML/CSS Jinja2 report templates to apps/api/templates/reports/ which will automatically appear as 'Active ✓' in the Report Templates Directory.",
  },
];

const CATEGORIES = [
  { id: "all", label: "All Topics" },
  { id: "core", label: "Core Charts & Kundli" },
  { id: "predictive", label: "Predictive & Timing" },
  { id: "technical", label: "Technical Systems (KP/Jaimini)" },
  { id: "life", label: "Life Domains & Predictions" },
  { id: "research", label: "Vedic Research & Texts" },
];

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [expandedCard, setExpandedCard] = useState<string | null>("birth-chart");

  const filteredGuides = useMemo(() => {
    return FEATURE_GUIDES.filter((guide) => {
      const matchesCategory =
        selectedCategory === "all" || guide.category === selectedCategory;

      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        guide.title.toLowerCase().includes(q) ||
        guide.tagline.toLowerCase().includes(q) ||
        guide.whatIsIt.toLowerCase().includes(q) ||
        guide.categoryLabel.toLowerCase().includes(q);

      return matchesCategory && matchesSearch;
    });
  }, [searchQuery, selectedCategory]);

  return (
    <div className="mx-auto max-w-6xl space-y-8 px-2 py-4 sm:px-4">
      {/* ── Hero Header ── */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800 bg-gradient-to-br from-slate-900 via-slate-850 to-slate-950 p-6 sm:p-8 text-white shadow-xl">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-300">
            <span>ॐ</span>
            <span>AstroOS Platform Documentation &amp; User Manual</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl text-slate-100">
            How to Use <span className="text-cyan-400">AstroOS</span>
          </h1>
          <p className="text-sm leading-relaxed text-slate-300 sm:text-base">
            Complete user guide and classical interpretation manual for all core charts, predictive timing engines, KP &amp; Jaimini systems, and Vedic research tools.
          </p>

          {/* Search bar */}
          <div className="relative mt-4 max-w-xl">
            <input
              type="text"
              placeholder="Search features (e.g. Dasha, KP, SBC, Marriage, Rectification, Ashtakavarga)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-800/90 py-3 pl-10 pr-4 text-sm text-slate-100 placeholder-slate-400 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20"
            />
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
              <Icon name="search" style={{ width: 18, height: 18 }} />
            </div>
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-xs text-slate-400 hover:text-white"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── 3-Step Quick Start Guide ── */}
      <div className="space-y-3">
        <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Icon name="sparkle" style={{ width: 20, height: 20, color: "var(--accent)" }} />
          <span>Quick Start: 3 Steps to Full Horoscope Analysis</span>
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card className="flex flex-col justify-between p-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cyan-500 text-xs font-bold text-slate-950">
                  1
                </span>
                <h3 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                  Create or Select Chart
                </h3>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Click <strong>+ Quick Action</strong> or <strong>New Natal Chart</strong> in the top header. Enter birth date, exact time, and city. This sets your active chart session.
              </p>
            </div>
            <Link
              href="/dashboard"
              className="mt-3 inline-flex items-center text-xs font-semibold text-cyan-600 dark:text-cyan-400 hover:underline"
            >
              Open Dashboard &rarr;
            </Link>
          </Card>

          <Card className="flex flex-col justify-between p-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cyan-500 text-xs font-bold text-slate-950">
                  2
                </span>
                <h3 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                  Inspect Kundli &amp; D9
                </h3>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Explore the <strong>Interactive Kundli</strong>, verify <strong>D-9 Navamsha</strong> for true strength, and check <strong>Shadbala</strong> planetary power ratings.
              </p>
            </div>
            <Link
              href="/charts/birth"
              className="mt-3 inline-flex items-center text-xs font-semibold text-cyan-600 dark:text-cyan-400 hover:underline"
            >
              View Birth Chart &rarr;
            </Link>
          </Card>

          <Card className="flex flex-col justify-between p-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cyan-500 text-xs font-bold text-slate-950">
                  3
                </span>
                <h3 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                  Predict Timing
                </h3>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Drill down into <strong>Vimshottari Dasha</strong> periods, overlay live <strong>Transits</strong> (Gochara), and check <strong>Sarvatobhadra Chakra (SBC)</strong> for exact date triggers.
              </p>
            </div>
            <Link
              href="/charts?view=dasha"
              className="mt-3 inline-flex items-center text-xs font-semibold text-cyan-600 dark:text-cyan-400 hover:underline"
            >
              Explore Dasha &rarr;
            </Link>
          </Card>
        </div>
      </div>

      {/* ── Category Filter Tabs ── */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
        {CATEGORIES.map((cat) => {
          const active = selectedCategory === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => setSelectedCategory(cat.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                active
                  ? "bg-cyan-500 text-slate-950 font-bold shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* ── Feature Cards Accordion / List ── */}
      <div className="space-y-4">
        {filteredGuides.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 dark:border-slate-800 p-8 text-center">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              No features match your search query &quot;{searchQuery}&quot;.
            </p>
            <button
              type="button"
              onClick={() => {
                setSearchQuery("");
                setSelectedCategory("all");
              }}
              className="mt-2 text-xs font-semibold text-cyan-600 dark:text-cyan-400 hover:underline"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          filteredGuides.map((guide) => {
            const isExpanded = expandedCard === guide.id;
            return (
              <Card
                key={guide.id}
                className="overflow-hidden border border-slate-200 dark:border-slate-800 transition-all"
              >
                {/* Header clickable summary */}
                <div
                  onClick={() => setExpandedCard(isExpanded ? null : guide.id)}
                  className="flex cursor-pointer flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between hover:bg-slate-50 dark:hover:bg-slate-850/50 transition"
                >
                  <div className="flex items-start sm:items-center gap-3">
                    <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-600 dark:text-cyan-400">
                      <Icon name={guide.icon} style={{ width: 20, height: 20 }} />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">
                          {guide.title}
                        </h3>
                        <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">
                          {guide.categoryLabel}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                        {guide.tagline}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 self-end sm:self-auto">
                    <Link
                      href={guide.route}
                      onClick={(e) => e.stopPropagation()}
                      className="rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-2.5 py-1 text-xs font-semibold text-cyan-700 dark:text-cyan-400 hover:border-cyan-400 transition"
                    >
                      Open Tool &rarr;
                    </Link>
                    <span className="text-slate-400 text-xs">
                      {isExpanded ? "▲ Hide Details" : "▼ Expand Guide"}
                    </span>
                  </div>
                </div>

                {/* Expanded Detailed Instructions */}
                {isExpanded && (
                  <div className="border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/40 p-5 space-y-5 text-sm">
                    {/* What is it */}
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                        Overview &amp; Purpose
                      </h4>
                      <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">
                        {guide.whatIsIt}
                      </p>
                    </div>

                    <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                      {/* How to use */}
                      <div className="space-y-2 rounded-xl bg-white dark:bg-slate-850 p-4 border border-slate-200 dark:border-slate-800">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 flex items-center gap-1.5">
                          <Icon name="compass" style={{ width: 14, height: 14 }} />
                          <span>Step-by-Step Usage</span>
                        </h4>
                        <ol className="list-decimal list-inside space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                          {guide.howToUse.map((step, idx) => (
                            <li key={idx} className="leading-normal">
                              {step}
                            </li>
                          ))}
                        </ol>
                      </div>

                      {/* How to interpret */}
                      <div className="space-y-2 rounded-xl bg-white dark:bg-slate-850 p-4 border border-slate-200 dark:border-slate-800">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
                          <Icon name="star" style={{ width: 14, height: 14 }} />
                          <span>How to Interpret Results</span>
                        </h4>
                        <ul className="list-disc list-inside space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                          {guide.howToInterpret.map((item, idx) => (
                            <li key={idx} className="leading-normal">
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Inputs & Pro Tip */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2 text-xs border-t border-slate-200 dark:border-slate-800">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="font-semibold text-slate-600 dark:text-slate-400">
                          Key Inputs:
                        </span>
                        {guide.keyInputs.map((inp, idx) => (
                          <span
                            key={idx}
                            className="rounded bg-slate-200 dark:bg-slate-800 px-2 py-0.5 text-slate-700 dark:text-slate-300"
                          >
                            {inp}
                          </span>
                        ))}
                      </div>

                      {guide.proTip && (
                        <div className="w-full rounded-lg bg-cyan-500/10 border border-cyan-500/20 p-2.5 text-cyan-800 dark:text-cyan-300 text-xs">
                          <strong>💡 Pro Astrologer Tip:</strong> {guide.proTip}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </Card>
            );
          })
        )}
      </div>

      {/* ── Astrological Glossary & FAQ ── */}
      <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
        <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Icon name="book" style={{ width: 20, height: 20, color: "var(--accent)" }} />
          <span>Frequently Asked Astrological Questions (FAQ)</span>
        </h2>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card className="p-4 space-y-2">
            <h3 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
              Which Ayanamsa should I choose?
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              <strong>Lahiri (Chitra Paksha)</strong> is the official standard for classical Parashari astrology in India. If you practice <strong>KP System</strong>, select <strong>KP Ayanamsa</strong>. For Jaimini and specific research, Raman or True Chitra can be configured under Settings &rarr; Astrology.
            </p>
          </Card>

          <Card className="p-4 space-y-2">
            <h3 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
              Why do SBC or Tarabala show &quot;No benefic hit&quot;?
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Sarvatobhadra Chakra (SBC) and Tarabala check exact planetary rays at that specific instant. A neutral/empty result is completely normal. Use date-range scanning to find the exact days when benefic Vedha or favorable Tara convergence occurs.
            </p>
          </Card>

          <Card className="p-4 space-y-2">
            <h3 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
              How does D-9 Navamsha modify D-1 Rashi results?
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              The D-1 Rashi chart indicates the tree (potential), but the D-9 Navamsha chart indicates the fruit (manifestation). A planet that is exalted in D-1 but debilitated in D-9 struggles to sustain its promise, while a Vargottama planet gives consistently high results.
            </p>
          </Card>

          <Card className="p-4 space-y-2">
            <h3 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
              How do I export and share charts?
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              You can click the <strong>Share</strong> button in the top navigation bar to generate instant shareable links, or visit <strong>Reports &rarr; PDF Reports</strong> to download comprehensive multi-page client horoscope dossiers.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}
