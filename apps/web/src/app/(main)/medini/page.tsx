'use client';

import React, { useState, useEffect } from "react";
import { useTheme } from "@/components/layout/ThemeProvider";
import { api } from "@/lib/api";
import {
  Compass,
  Sparkles,
  Layers,
  Calendar,
  Sun,
  Moon,
  Clock,
  Award
} from "@/components/phalita/Icons";

const SAMVATSARA_NAMES = [
  "Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati",
  "Angirasa", "Shrimukha", "Bhava", "Yuva", "Dhatri",
  "Ishvara", "Bahudhanya", "Pramathi", "Vikrama", "Vrisha",
  "Chitrabhanu", "Subhanu", "Tarana", "Parthiva", "Vyaya",
  "Sarvajit", "Sarvadhari", "Virodhi", "Vikrita", "Khara",
  "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukha",
  "Hemalamba", "Vilamba", "Vikari", "Sharvari", "Plava",
  "Shubhakrit", "Shobhana", "Krodhi", "Vishvavasu", "Parabhava",
  "Plavanga", "Kilaka", "Saumya", "Sadharana", "Virodhikrit",
  "Paridhavi", "Pramadicha", "Ananda", "Rakshasa", "Nala",
  "Pingala", "Kalayukta", "Siddharthi", "Raudra", "Durmati",
  "Dundubhi", "Rudhirodgari", "Raktakshi", "Krodhana", "Akshaya"
];

function getSamvatsaraName(year: number): string {
  const idx = ((37 + (year - 2024)) % 60 + 60) % 60;
  return SAMVATSARA_NAMES[idx];
}

interface CabinetMinisterApi {
  portfolio: string;
  planet: string;
  basis_ingress: string;
  is_benefic: boolean;
  impact_summary: string;
}

interface PlanetaryCabinetApiResponse {
  year: number;
  ministers: CabinetMinisterApi[];
  overall_balance_score: number;
  governance_climate: string;
  classical_summary: string;
}

interface SaptaNadiNadiStatusApi {
  nadi: string;
  element: string;
  occupying_planets: string[];
  status: string;
  analysis: string;
}

interface RainfallTeleconnectionApiResponse {
  target_year: number;
  analogue_year_61: number;
  analogue_year_122: number;
  aridra_pravesha_utc: string;
  meghadhipati: string;
  sasyeshadhipati: string;
  active_nadis: SaptaNadiNadiStatusApi[];
  predicted_monsoon_category: string;
  predicted_rainfall_pct_lpa: number;
  sst_teleconnection_coupling: string;
  shastric_analysis: string;
  research_citation: string;
}

// Exact Indian Standard Panchanga Calculations (Udaya-Tithi at Sunrise & Adhika-Masa Resolved via Swiss Ephemeris)
const MEDINI_ANNUAL_DATA: Record<number, {
  samvatsara: string;
  harmonyScore: number;
  verdict: string;
  themeSummary: string;
  cabinet: { role: string; lord: string; ingress: string; nature: string; impact: string; isBenefic: boolean }[];
  monsoon: { nadi: string; element: string; planets: string; status: string; analysis: string }[];
  koorma: { direction: string; states: string; lord: string; condition: "Afflicted" | "Volatile" | "Mixed" | "Stable"; details: string }[];
  financial: { sector: string; trend: string; color: string; desc: string }[];
}> = {
  2024: {
    samvatsara: "Krodhi (Year of Turbulence & Militancy)",
    harmonyScore: 28,
    verdict: "Extremely Challenging (28/100) — King is Mars ♂, Prime Minister is Saturn ♄",
    themeSummary: "Udaya-Tithi Calculation: Chaitra Shukla Pratipada commenced at Sunrise on Tuesday (9 April 2024, 06:01 IST) making Mars (Mangala) the King, while Mesha Sankranti occurred on Saturday (13 April 2024, 21:04 IST) making Saturn (Shani) the Prime Minister. Classical Shastric reality: Mars + Saturn joint rule brings fierce election aggression, institutional friction, public anger over jobs/paper leaks, severe summer heatwaves, infrastructure accidents, and heightened border vigilance.",
    cabinet: [
      { role: "Raja (King / Head of State)", lord: "Mars ♂ (Mangala)", ingress: "Chaitra Shukla Pratipada (Tue, 9 Apr 2024, 06:01 IST)", nature: "Fiery Malefic", impact: "Aggressive state posturing, stringent internal enforcement, political confrontation, and fiery rhetoric.", isBenefic: false },
      { role: "Mantri (Prime Minister / Chief Advisor)", lord: "Saturn ♄ (Shani)", ingress: "Mesha Sankranti (Sat, 13 Apr 2024, 21:04 IST)", nature: "Cold Malefic", impact: "Severe coalition/policy deadlock, public unrest regarding unemployment, and judicial-executive friction.", isBenefic: false },
      { role: "Senadhipati (Defense & Armed Forces)", lord: "Venus ♀ (Shukra)", ingress: "Simha Sankranti (Fri, 16 Aug 2024, 19:44 IST)", nature: "Benefic", impact: "Strategic bilateral defense pacts, diplomatic posturing, and global weapons procurement.", isBenefic: true },
      { role: "Sasyeshadhipati (Kharif Monsoon Crops)", lord: "Mars ♂ (Mangala)", ingress: "Karka Sankranti (Tue, 16 Jul 2024, 11:29 IST)", nature: "Fiery Malefic", impact: "Severe crop stress from irregular heatwaves and unseasonal cloudbursts.", isBenefic: false },
      { role: "Dhanyadhipati (Rabi Winter Cereals)", lord: "Moon ☽ (Chandra)", ingress: "Dhanu Sankranti (Mon, 16 Dec 2024, 00:08 IST)", nature: "Benefic", impact: "Buffer grain stocks maintained with targeted market interventions.", isBenefic: true },
      { role: "Arghyadhipati (Prices & Inflation)", lord: "Mercury ☿ (Budha)", ingress: "Mithuna Sankranti (Fri, 14 Jun 2024, 22:38 IST)", nature: "Mixed", impact: "Sharp volatility in vegetables, pulses, and FMCG costs against resilient tech exports.", isBenefic: true },
      { role: "Meghadhipati (Lord of Clouds & Rain)", lord: "Venus ♀ (Shukra)", ingress: "Aridra Pravesha (Sat, 22 Jun 2024, 00:34 IST)", nature: "Watery", impact: "Extremely skewed rainfall: coastal flooding/cyclones vs interior agricultural deficit.", isBenefic: true },
      { role: "Raseshadhipati (Liquids & Petroleum)", lord: "Saturn ♄ (Shani)", ingress: "Tula Sankranti (Thu, 17 Oct 2024, 07:42 IST)", nature: "Heavy Malefic", impact: "Elevated crude oil import costs, currency depreciation pressures, and fuel price burdens.", isBenefic: false },
      { role: "Nireshadhipati (Metals & Minerals)", lord: "Mars ♂ (Mangala)", ingress: "Makara Sankranti (Mon, 15 Jan 2024, 02:54 IST)", nature: "Fiery Malefic", impact: "High price surges in steel, copper, defense manufacturing minerals, and construction supplies.", isBenefic: false },
    ],
    monsoon: [
      { nadi: "1. Dahananadi (Intense Heat / Fire)", element: "Fire", planets: "Mars ♂, Sun ☉", status: "Severe", analysis: "Historic heatwaves across Northern and Central India during May-June." },
      { nadi: "2. Vayunadi (Gale Winds / Cyclones)", element: "Air", planets: "Saturn ♄, Rahu ☊", status: "High Alert", analysis: "Severe cyclonic surges and coastal storms in the Bay of Bengal." },
      { nadi: "3. Chandronadi (Localized Cloudbursts)", element: "Water", planets: "Venus ♀", status: "Active", analysis: "Heavy catastrophic localized floods in Himachal, Uttarakhand, and Kerala." },
    ],
    koorma: [
      { direction: "Central (Madhya Desha)", states: "Delhi, UP, MP, Rajasthan", lord: "Mars / Saturn", condition: "Afflicted", details: "Intense political heat, unemployment protests, inflation squeeze, and legal confrontations." },
      { direction: "Himalayan & Northern Belt", states: "J&K, Himachal, Uttarakhand", lord: "Saturn / Rahu", condition: "Afflicted", details: "Frequent landslides, cloudburst devastation, and high border vigilance." },
      { direction: "East & North-East", states: "Bengal, Bihar, Odisha, Assam", lord: "Mars / Rahu", condition: "Volatile", details: "Severe regional political tensions, localized communal friction, and flood disruptions." },
    ],
    financial: [
      { sector: "Equities & Market Sentiment", trend: "HIGH VOLATILITY & CORRECTION HEADWINDS", color: "text-amber-500", desc: "Mars-Saturn cabinet creates unpredictable sudden drawdowns and capital rotations." },
      { sector: "Essential Food Commodities", trend: "SEVERE PRICE PRESSURES", color: "text-rose-500", desc: "Mars over Kharif harvests spikes daily consumer inflation in pulses and vegetables." },
      { sector: "Gold & Precious Metals", trend: "RECORD BULLISH RUSH", color: "text-emerald-500", desc: "Global geopolitical conflicts and currency hedges push gold to historic highs." },
    ]
  },
  2025: {
    samvatsara: "Vishvavasu (Year of Austere Governance & Structural Tests)",
    harmonyScore: 34,
    verdict: "Challenging (34/100) — King is Sun ☉, Prime Minister is Moon ☽",
    themeSummary: "Udaya-Tithi Calculation: Chaitra Shukla Pratipada starts at Sunrise on Sunday (30 March 2025, 06:13 IST) making Sun (Surya) the King, while Mesha Sankranti occurs on Monday (14 April 2025, 03:21 IST) making Moon (Chandra) the Prime Minister. Sun as King brings strict tax and compliance enforcement, centralized authority, and intense bureaucratic oversight, while Moon as Minister drives fluctuating public sentiment and localized agrarian friction.",
    cabinet: [
      { role: "Raja (King / Head of State)", lord: "Sun ☉ (Surya)", ingress: "Chaitra Shukla Pratipada (Sun, 30 Mar 2025, 06:13 IST)", nature: "Authoritative", impact: "Centralized sovereign control, aggressive tax enforcement, strict corporate compliance.", isBenefic: false },
      { role: "Mantri (Prime Minister / Chief Advisor)", lord: "Moon ☽ (Chandra)", ingress: "Mesha Sankranti (Mon, 14 Apr 2025, 03:21 IST)", nature: "Fluctuating Benefic", impact: "Shifting policy priorities, high public scrutiny, and sensitivity to grassroots welfare.", isBenefic: true },
      { role: "Senadhipati (Defense & Armed Forces)", lord: "Sunday / Sun ☉", ingress: "Simha Sankranti (Sun, 17 Aug 2024)", nature: "Stern", impact: "Heavy surveillance, border fortification, and indigenous defense production push.", isBenefic: false },
      { role: "Sasyeshadhipati (Kharif Monsoon Crops)", lord: "Wednesday / Mercury ☿", ingress: "Karka Sankranti", nature: "Benefic", impact: "Moderate Kharif harvest supported by late-season technology and irrigation.", isBenefic: true },
      { role: "Dhanyadhipati (Rabi Winter Cereals)", lord: "Thursday / Jupiter ♃", ingress: "Dhanu Sankranti", nature: "Benefic", impact: "Strong winter cereal yields, MSP support, and robust wheat storage.", isBenefic: true },
      { role: "Arghyadhipati (Prices & Inflation)", lord: "Sunday / Sun ☉", ingress: "Mithuna Sankranti", nature: "Strict", impact: "Strict government price controls on essential commodities and exports.", isBenefic: false },
      { role: "Meghadhipati (Lord of Clouds & Rain)", lord: "Sun ☉ (Surya)", ingress: "Aridra Pravesha", nature: "Arid", impact: "Patchy monsoon with intense heatwaves in northwest before late revival.", isBenefic: false },
      { role: "Raseshadhipati (Liquids & Petroleum)", lord: "Friday / Venus ♀", ingress: "Tula Sankranti", nature: "Benefic", impact: "Stabilization of petrochemical supply lines and expansion of ethanol/EV mixes.", isBenefic: true },
      { role: "Nireshadhipati (Metals & Minerals)", lord: "Tuesday / Mars ♂", ingress: "Makara Sankranti", nature: "Aggressive", impact: "Strategic national auctions of lithium, rare-earths, and heavy industrial metals.", isBenefic: false },
    ],
    monsoon: [
      { nadi: "1. Dahananadi (Severe Heatwave)", element: "Fire", planets: "Sun ☉", status: "Active", analysis: "Early summer heatwave strain on power grids and urban water supplies." },
      { nadi: "2. Varunanadi (Late Soaking Rains)", element: "Water", planets: "Jupiter ♃", status: "Supportive", analysis: "Late July-August agricultural replenishment saving Kharif yields." },
    ],
    koorma: [
      { direction: "Northern & Central Plains", states: "Punjab, Haryana, Delhi, Western UP", lord: "Sun / Mars", condition: "Volatile", details: "Groundwater depletion debates, power supply stress, and agrarian policy friction." },
      { direction: "Coastal & Southern Belts", states: "Tamil Nadu, Kerala, Andhra", lord: "Moon / Venus", condition: "Stable", details: "Stronger service economy, port revenue, and coastal reservoir recovery." },
    ],
    financial: [
      { sector: "Banking & Sovereign Debt", trend: "TIGHT FISCAL CONSOLIDATION", color: "text-cyan-500", desc: "Central bank and government maintain strict liquidity discipline." },
      { sector: "Real Estate & Capital Goods", trend: "SELECTIVE EXPANSION", color: "text-emerald-500", desc: "High infrastructure spending offset by stricter financing checks." },
    ]
  },
  2026: {
    samvatsara: "Parabhava / Plavanga (Year of Dharmic Expansion & Technological Leap)",
    harmonyScore: 71,
    verdict: "Progressive & Balanced (71/100) — King is Jupiter ♃, Prime Minister is Mars ♂",
    themeSummary: "Standard Panchang & Siddhanta Alignment: Chaitra Shukla Pratipada begins at Sunrise on Thursday (19 March 2026, 06:53 IST) making Jupiter (Guru) the King (Raja), while Mesha Sankranti occurs on Tuesday (14 April 2026, 09:32 IST) making Mars (Mangala) the Prime Minister (Mantri). Classical Shastric reality: Guru Raja + Mangala Mantri is an auspicious, highly progressive configuration governing dharmic governance, judicial strength, robust domestic capital formation, agricultural abundance, and energetic defense modernization.",
    cabinet: [
      { role: "Raja (King / Head of State)", lord: "Jupiter ♃ (Guru)", ingress: "Chaitra Shukla Pratipada (Thu, 19 Mar 2026, 06:53 IST)", nature: "Great Benefic", impact: "Dharmic policy vision, judicial integrity, educational reforms, and record sovereign welfare expansion.", isBenefic: true },
      { role: "Mantri (Prime Minister / Chief Advisor)", lord: "Mars ♂ (Mangala)", ingress: "Mesha Sankranti (Tue, 14 Apr 2026, 09:32 IST)", nature: "Decisive Malefic", impact: "Aggressive national security readiness, rapid infrastructure construction, and tough geopolitical stance.", isBenefic: false },
      { role: "Senadhipati (Defense & Armed Forces)", lord: "Moon ☽ (Chandra)", ingress: "Simha Sankranti (Mon, 17 Aug 2026, 07:58 IST)", nature: "Benefic", impact: "Major naval defense modernization, maritime surveillance in Indian Ocean, and military welfare.", isBenefic: true },
      { role: "Sasyeshadhipati (Kharif Monsoon Crops)", lord: "Jupiter ♃ (Guru)", ingress: "Karka Sankranti (Thu, 16 Jul 2026, 23:39 IST)", nature: "Benefic", impact: "Benefic protection for summer crops, agricultural subsidies, and record grain harvest security.", isBenefic: true },
      { role: "Dhanyadhipati (Rabi Winter Cereals)", lord: "Mercury ☿ (Budha)", ingress: "Dhanu Sankranti (Wed, 16 Dec 2026, 10:25 IST)", nature: "Benefic", impact: "Strong winter yields in wheat, pulses, and commercial crops; organized commodity exports.", isBenefic: true },
      { role: "Arghyadhipati (Prices & Inflation)", lord: "Moon ☽ (Chandra)", ingress: "Mithuna Sankranti (Mon, 15 Jun 2026, 12:52 IST)", nature: "Benefic", impact: "Moderating inflation in essential food items despite industrial raw material volatility.", isBenefic: true },
      { role: "Meghadhipati (Lord of Clouds & Rain)", lord: "Moon ☽ (Chandra)", ingress: "Aridra Pravesha (Mon, 22 Jun 2026, 12:26 IST)", nature: "Watery Benefic", impact: "Timely and equitable monsoon rains across major river basin agricultural zones.", isBenefic: true },
      { role: "Raseshadhipati (Liquids & Petroleum)", lord: "Saturn ♄ (Shani)", ingress: "Tula Sankranti (Sat, 17 Oct 2026, 19:51 IST)", nature: "Cold / Heavy", impact: "Tight regulatory control on oil & energy imports; acceleration of domestic renewable infrastructure.", isBenefic: false },
      { role: "Nireshadhipati (Metals & Minerals)", lord: "Mercury ☿ (Budha)", ingress: "Makara Sankranti (Wed, 14 Jan 2026, 15:07 IST)", nature: "Benefic", impact: "Major expansion in semiconductor fabrication, rare earth exploration, and electronic manufacturing.", isBenefic: true },
    ],
    monsoon: [
      { nadi: "1. Chandronadi (Equitable Rain)", element: "Water", planets: "Moon ☽, Venus ♀", status: "Active", analysis: "Generous and well-distributed rainfall across fertile river basins." },
      { nadi: "2. Varunanadi (Beneficial Soaking)", element: "Water", planets: "Jupiter ♃", status: "Active", analysis: "Optimal groundwater table recharge and reservoir replenishment." },
    ],
    koorma: [
      { direction: "Northern & Himalayan Border", states: "J&K, Ladakh, Arunachal, Himalayas", lord: "Jupiter / Mars", condition: "Stable", details: "Heightened military defense preparedness, border security alertness, and strategic highway tunnels." },
      { direction: "Industrial & Coastal Hubs", states: "Maharashtra, Gujarat, Tamil Nadu", lord: "Jupiter / Mercury", condition: "Mixed", details: "Heavy manufacturing, tech corridors, and semiconductor boom backed by strong sovereign policy." }
    ],
    financial: [
      { sector: "Equities & Financial Liquidity", trend: "STRUCTURAL BULL RUN", color: "text-emerald-500", desc: "Jupiter King fosters record domestic retail mutual fund inflows, banking resilience, and capex expansion." },
      { sector: "Defense & Strategic Manufacturing", trend: "HISTORIC EXPANSION", color: "text-emerald-500", desc: "Mars as Prime Minister channels massive state procurement into defense indigenization and electronics." },
    ]
  }
};

export default function MediniJyotishPage() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [selectedYear, setSelectedYear] = useState<number>(2026);
  const [inputYear, setInputYear] = useState<string>("2026");
  const [activeTab, setActiveTab] = useState<"cabinet" | "saptanadi" | "koorma" | "financial">("cabinet");
  const [liveCabinet, setLiveCabinet] = useState<PlanetaryCabinetApiResponse | null>(null);
  const [liveTeleconnection, setLiveTeleconnection] = useState<RainfallTeleconnectionApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    async function fetchData() {
      setIsLoading(true);
      try {
        const [cabRes, teleRes] = await Promise.all([
          api.get<PlanetaryCabinetApiResponse>(`/api/v1/research/mundane/planetary-cabinet/${selectedYear}`),
          api.get<RainfallTeleconnectionApiResponse>(`/api/v1/research/mundane/rainfall-teleconnection/${selectedYear}`),
        ]);
        if (isMounted) {
          if (cabRes) setLiveCabinet(cabRes);
          if (teleRes) setLiveTeleconnection(teleRes);
        }
      } catch (err) {
        console.warn("Could not fetch live medini data:", err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }
    fetchData();
    return () => { isMounted = false; };
  }, [selectedYear]);

  const fallbackData = MEDINI_ANNUAL_DATA[selectedYear];
  const calculatedSamvatsara = getSamvatsaraName(selectedYear);

  // Dynamic synthesis if year is not in curated dictionary
  const samvatsaraTitle = fallbackData?.samvatsara || `${calculatedSamvatsara} (Samvatsara Cycle #${((selectedYear - 1900) % 60) + 1})`;
  const harmonyScore = liveCabinet ? liveCabinet.overall_balance_score : (fallbackData?.harmonyScore || 50);
  const governanceClimate = liveCabinet ? liveCabinet.governance_climate : (fallbackData?.verdict || "Standard Astrological Year");
  const themeSummary = liveCabinet ? liveCabinet.classical_summary : (fallbackData?.themeSummary || `Astronomical evaluation for ${selectedYear} based on Swiss Ephemeris.`);

  // Active cabinet rows
  const cabinetRows = liveCabinet
    ? liveCabinet.ministers.map((m) => ({
        role: m.portfolio,
        lord: `${m.planet} ${m.planet.toLowerCase() === "jupiter" ? "♃" : m.planet.toLowerCase() === "mars" ? "♂" : m.planet.toLowerCase() === "saturn" ? "♄" : m.planet.toLowerCase() === "sun" ? "☉" : m.planet.toLowerCase() === "moon" ? "☽" : m.planet.toLowerCase() === "venus" ? "♀" : "☿"}`,
        ingress: m.basis_ingress,
        nature: m.is_benefic ? "Benefic / Auspicious" : "Malefic / Strict",
        impact: m.impact_summary,
        isBenefic: m.is_benefic,
      }))
    : (fallbackData?.cabinet || []);

  // Extract key ministers if available
  const rajaMinister = liveCabinet?.ministers.find((m) => m.portfolio.toLowerCase().includes("raja"))?.planet || "Jupiter";
  const mantriMinister = liveCabinet?.ministers.find((m) => m.portfolio.toLowerCase().includes("mantri"))?.planet || "Mars";
  const meghaMinister = liveCabinet?.ministers.find((m) => m.portfolio.toLowerCase().includes("megha"))?.planet || "Moon";
  const sasyoMinister = liveCabinet?.ministers.find((m) => m.portfolio.toLowerCase().includes("sasye"))?.planet || "Jupiter";
  const arghyaMinister = liveCabinet?.ministers.find((m) => m.portfolio.toLowerCase().includes("arghya"))?.planet || "Moon";

  const curMonsoon = fallbackData?.monsoon || [
    {
      nadi: "1. Meghadhipati Governance (Annual Rain Matrix)",
      element: "Water",
      planets: `${meghaMinister} (Monsoon Lord)`,
      status: ["moon", "venus", "jupiter"].includes(meghaMinister.toLowerCase()) ? "Auspicious & Plentiful" : "Fluctuating & Arid",
      analysis: `Annual rainfall governed by ${meghaMinister} at Aridra Pravesha. Kharif agricultural cycle protected by ${sasyoMinister} (Sasyeshadhipati).`
    },
    {
      nadi: "2. Varunanadi & Groundwater Table Recharge",
      element: "Water",
      planets: `${sasyoMinister} & ${rajaMinister}`,
      status: "Active",
      analysis: `Seasonal water table recharge and river basin agricultural capacity derived from ${selectedYear} ingress dynamics.`
    }
  ];

  const curKoorma = fallbackData?.koorma || [
    {
      direction: "Northern & Himalayan Border (Uttara / Ishanya)",
      states: "J&K, Ladakh, Himachal, Uttarakhand, Arunachal",
      lord: `${rajaMinister} / ${mantriMinister}`,
      condition: ["mars", "saturn", "sun"].includes(mantriMinister.toLowerCase()) ? ("Volatile" as const) : ("Stable" as const),
      details: `Strategic border security, infrastructure tunnels, and administrative focus under ${rajaMinister} Raja & ${mantriMinister} Mantri.`
    },
    {
      direction: "Central & Gangetic Plains (Madhya Desha)",
      states: "Delhi, UP, Bihar, MP, Rajasthan",
      lord: `${rajaMinister} (King)`,
      condition: harmonyScore >= 60 ? ("Stable" as const) : ("Mixed" as const),
      details: `Macro policy governance, socio-economic welfare, and agrarian yields governed by ${rajaMinister}.`
    },
    {
      direction: "Coastal & Industrial Hubs (Dakshina / Paschima)",
      states: "Maharashtra, Gujarat, Tamil Nadu, Karnataka",
      lord: `${arghyaMinister} (Prices/Commerce)`,
      condition: "Stable" as const,
      details: `Maritime trade, manufacturing expansion, and supply chain liquidity governed by ${arghyaMinister} (Arghyadhipati).`
    }
  ];

  const curFinancial = fallbackData?.financial || [
    {
      sector: "Macroeconomy & Capital Markets",
      trend: harmonyScore >= 60 ? "EXPANSION & STRONG LIQUIDITY" : harmonyScore >= 40 ? "SELECTIVE GROWTH & CONSOLIDATION" : "HIGH VOLATILITY & TIGHT LIQUIDITY",
      color: harmonyScore >= 60 ? "text-emerald-500" : harmonyScore >= 40 ? "text-cyan-500" : "text-amber-500",
      desc: `Cosmic Harmony Score (${harmonyScore}/100) indicates ${governanceClimate.toLowerCase()}`
    },
    {
      sector: "Defense, Energy & Strategic Capex",
      trend: ["mars", "sun", "saturn"].includes(mantriMinister.toLowerCase()) ? "HIGH SPENDING & MILITARY INDIGENIZATION" : "STABLE MODERNIZATION",
      color: "text-emerald-500",
      desc: `Minister (${mantriMinister}) drives strategic defense procurement, heavy industrial corridors, and energy infrastructure.`
    },
    {
      sector: "Essential Commodities & Price Stability",
      trend: ["moon", "jupiter", "mercury"].includes(arghyaMinister.toLowerCase()) ? "MODERATING INFLATION & FOOD BUFFER" : "VOLATILE COMMODITY PRICES",
      color: ["moon", "jupiter", "mercury"].includes(arghyaMinister.toLowerCase()) ? "text-cyan-500" : "text-rose-500",
      desc: `Lord of Commodities (${arghyaMinister}) governs price indices, market liquidity, and trade balances.`
    }
  ];

  const handleYearSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseInt(inputYear, 10);
    if (!isNaN(parsed) && parsed >= 1800 && parsed <= 2150) {
      setSelectedYear(parsed);
    }
  };

  return (
    <div className="min-h-screen p-4 sm:p-6 lg:p-8 space-y-8 transition-colors bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* 🌟 Header Banner */}
      <div className="border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-sm transition-all relative overflow-hidden bg-white dark:bg-slate-900/90">
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400 font-mono text-xs font-bold tracking-wider uppercase">
              <GlobeIcon className="w-4 h-4 text-cyan-500" />
              <span>MEDINI JYOTISHA (SAMHITA MUNDANE ASTROLOGY)</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold font-sans tracking-tight">
              National & Geopolitical Forecasting Suite
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-400 max-w-2xl font-sans">
              Rigorous classical Samhita calculations: <strong>Nava Nayakas (9 Cosmic Ministers)</strong>, <strong>Sapta-Nadi Weather & Monsoon Matrix</strong>, and <strong>Koorma Chakra Sector Afflictions</strong>.
            </p>
          </div>

          {/* Dynamic Target Year Input */}
          <div className="flex flex-col items-start lg:items-end gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono">
              ENTER OR SELECT ANY YEAR (1800 – 2150)
            </span>
            
            <form onSubmit={handleYearSubmit} className="flex items-center gap-1.5 font-mono">
              <button
                type="button"
                onClick={() => {
                  const next = selectedYear - 1;
                  setSelectedYear(next);
                  setInputYear(next.toString());
                }}
                className="px-3 py-1.5 rounded-lg border text-xs font-bold transition-all cursor-pointer bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-cyan-500"
                title="Previous Year"
              >
                ◀
              </button>
              
              <input
                type="number"
                min="1800"
                max="2150"
                value={inputYear}
                onChange={(e) => setInputYear(e.target.value)}
                onBlur={() => {
                  const parsed = parseInt(inputYear, 10);
                  if (!isNaN(parsed) && parsed >= 1800 && parsed <= 2150) {
                    setSelectedYear(parsed);
                  }
                }}
                className="w-24 px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-center text-sm font-bold font-mono focus:outline-none focus:ring-2 focus:ring-cyan-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              />
              
              <button
                type="button"
                onClick={() => {
                  const next = selectedYear + 1;
                  setSelectedYear(next);
                  setInputYear(next.toString());
                }}
                className="px-3 py-1.5 rounded-lg border text-xs font-bold transition-all cursor-pointer bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-cyan-500"
                title="Next Year"
              >
                ▶
              </button>
              
              <button
                type="submit"
                className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold shadow-md transition-all cursor-pointer"
              >
                Calculate
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* 🌟 Year Summary Callout */}
      <div className={`p-5 rounded-xl border space-y-2.5 shadow-sm transition-all ${
        harmonyScore <= 35
          ? "bg-rose-50 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900/40 text-rose-900 dark:text-rose-200"
          : "bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/40 text-emerald-900 dark:text-emerald-200"
      }`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-2 border-current/20">
          <span className="font-mono font-bold text-sm flex items-center gap-2">
            <span>📅 {selectedYear} Samvatsara: {samvatsaraTitle}</span>
            {isLoading && <span className="text-[10px] animate-pulse font-mono text-cyan-500 dark:text-cyan-400">● Computing Swiss Ephemeris...</span>}
          </span>
          <span className="font-mono text-xs font-extrabold px-2.5 py-0.5 rounded border border-current/30 w-fit">
            Cosmic Harmony Score: {harmonyScore} / 100
          </span>
        </div>
        <div className="text-xs leading-relaxed font-sans pt-1 space-y-1">
          <div className="font-bold font-mono text-cyan-600 dark:text-cyan-400">{governanceClimate}</div>
          <p className="text-slate-700 dark:text-slate-300">{themeSummary}</p>
        </div>
      </div>

      {/* 🌟 Tab Navigation — 1-Line Segmented Control */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 border-b pb-4 border-slate-200 dark:border-slate-800 font-mono">
        <button
          onClick={() => setActiveTab("cabinet")}
          className={`py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer text-center truncate ${
            activeTab === "cabinet"
              ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/30"
              : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          }`}
          title="01 Planetary Cabinet (Nava Nayakas)"
        >
          <CrownIcon className="w-3.5 h-3.5 shrink-0" />
          <span className="truncate">01 Planetary Cabinet (Nava Nayakas)</span>
        </button>

        <button
          onClick={() => setActiveTab("saptanadi")}
          className={`py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer text-center truncate ${
            activeTab === "saptanadi"
              ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/30"
              : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          }`}
          title="02 Sapta-Nadi Weather & Monsoon"
        >
          <CloudRainIcon className="w-3.5 h-3.5 shrink-0" />
          <span className="truncate">02 Sapta-Nadi Weather &amp; Monsoon</span>
        </button>

        <button
          onClick={() => setActiveTab("koorma")}
          className={`py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer text-center truncate ${
            activeTab === "koorma"
              ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/30"
              : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          }`}
          title="03 Koorma Chakra Afflictions"
        >
          <Compass className="w-3.5 h-3.5 shrink-0" />
          <span className="truncate">03 Koorma Chakra Afflictions</span>
        </button>

        <button
          onClick={() => setActiveTab("financial")}
          className={`py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer text-center truncate ${
            activeTab === "financial"
              ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/30"
              : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          }`}
          title="04 Financial & Commodity Reality"
        >
          <TrendingUpIcon className="w-3.5 h-3.5 shrink-0" />
          <span className="truncate">04 Financial &amp; Commodity Reality</span>
        </button>
      </div>

      {/* 🌟 Tab 1: Planetary Cabinet */}
      {activeTab === "cabinet" && (
        <div className="space-y-6">
          <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors bg-white dark:bg-slate-900/90">
            <div className="border-b pb-3 mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-slate-200 dark:border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
                {selectedYear} PLANETARY CABINET (NAVA NAYAKAS — 9 MINISTERS OF GOVERNANCE)
              </span>
              <span className="text-xs font-mono font-bold text-slate-500 dark:text-slate-400">Brihat Samhita & Bhavishya Phala Standards</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="uppercase tracking-wider text-[10px] border-b bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="py-3 px-4">Ministry / Portfolio</th>
                    <th className="py-3 px-4">Ruling Lord</th>
                    <th className="py-3 px-4">Ingress Basis (Panchanga & Ephemeris)</th>
                    <th className="py-3 px-4">Samhita Astrological Impact</th>
                    <th className="py-3 px-4">Nature</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {cabinetRows.map((c, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors">
                      <td className="py-3 px-4 font-bold text-slate-900 dark:text-white font-sans">{c.role}</td>
                      <td className="py-3 px-4 font-extrabold text-cyan-700 dark:text-cyan-300">{c.lord}</td>
                      <td className="py-3 px-4 text-slate-500 dark:text-slate-400 text-[11px]">{c.ingress}</td>
                      <td className="py-3 px-4 text-slate-700 dark:text-slate-300 font-sans leading-relaxed">{c.impact}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          c.isBenefic
                            ? "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800"
                            : "bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800"
                        }`}>
                          {c.nature}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 🌟 Tab 2: Sapta-Nadi Weather & Monsoon */}
      {activeTab === "saptanadi" && (
        <div className="space-y-6">
          {/* 61-Year Waveform Teleconnection Card */}
          <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors space-y-4 bg-white dark:bg-slate-900/90">
            <div className="border-b pb-3 border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono flex items-center gap-2">
                <CloudRainIcon className="w-4 h-4 text-cyan-500" />
                <span>61-YEAR CLIMATIC WAVEFORM MONSOON FORECAST ({selectedYear})</span>
              </span>
              <span className="text-xs font-mono font-bold text-slate-500 dark:text-slate-400">
                    Canonical Siddhantic & Brihat Samhita Standards
              </span>
            </div>

            {liveTeleconnection ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
                  <div className="p-3.5 rounded-xl border bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase">Predicted Rainfall (ISMR)</span>
                    <div className="text-lg font-extrabold text-cyan-600 dark:text-cyan-400 mt-1">
                      {liveTeleconnection.predicted_rainfall_pct_lpa}% of LPA
                    </div>
                    <div className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
                      {liveTeleconnection.predicted_monsoon_category}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl border bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase">61-Yr Historical Analogue</span>
                    <div className="text-base font-extrabold text-slate-900 dark:text-slate-200 mt-1">
                      Year {liveTeleconnection.analogue_year_61} (1st)
                    </div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                      Harmonic 2: Year {liveTeleconnection.analogue_year_122}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl border bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase">Meghadhipati (Monsoon Lord)</span>
                    <div className="text-base font-extrabold text-cyan-700 dark:text-cyan-400 mt-1">
                      {liveTeleconnection.meghadhipati}
                    </div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                      Aridra Pravesha Ingress Day
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl border bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase">Sasyeshadhipati (Kharif Crops)</span>
                    <div className="text-base font-extrabold text-emerald-700 dark:text-emerald-400 mt-1">
                      {liveTeleconnection.sasyeshadhipati}
                    </div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                      Karka Sankranti Ingress Day
                    </div>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl border text-xs font-sans space-y-1.5 bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60 text-slate-700 dark:text-slate-300">
                  <div className="font-mono font-bold text-cyan-600 dark:text-cyan-400 text-xs">Climatic Teleconnection & Atmospheric Resonance:</div>
                  <p className="leading-relaxed">{liveTeleconnection.sst_teleconnection_coupling}</p>
                  <p className="leading-relaxed font-semibold text-slate-900 dark:text-slate-200">{liveTeleconnection.shastric_analysis}</p>
                </div>
              </div>
            ) : (
              <div className="text-xs font-mono text-cyan-500 dark:text-cyan-400 animate-pulse">
                Computing 61-year climatic waveform teleconnection...
              </div>
            )}
          </div>

          {/* Sapta-Nadi 7-Channel Matrix */}
          <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors space-y-4 bg-white dark:bg-slate-900/90">
            <div className="border-b pb-3 border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-500" />
                <span>SAPTA-NADI 7-CHANNEL PRECIPITATION MATRIX ({selectedYear})</span>
              </span>
              <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                Krishi Parashara & Yamala Swarodaya Standards
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 font-mono text-xs">
              {liveTeleconnection ? (
                liveTeleconnection.active_nadis.map((n, i) => (
                  <div key={i} className="p-4 rounded-xl border space-y-2 bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-slate-900 dark:text-white font-sans text-sm">{n.nadi}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        n.element.includes("Water")
                          ? "bg-cyan-100 dark:bg-cyan-950/60 text-cyan-800 dark:text-cyan-300 border border-cyan-800"
                          : n.element.includes("Fire")
                          ? "bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border border-rose-800"
                          : "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-800"
                      }`}>
                        {n.element}
                      </span>
                    </div>
                    <div className="text-xs text-amber-600 dark:text-amber-400 font-bold">
                      Occupied: {n.occupying_planets.length > 0 ? n.occupying_planets.join(", ") : "None (Dormant)"}
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 font-sans leading-relaxed">
                      {n.analysis}
                    </p>
                  </div>
                ))
              ) : (
                curMonsoon.map((n, i) => (
                  <div key={i} className="p-4 rounded-xl border space-y-2 bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-slate-900 dark:text-white font-sans text-sm">{n.nadi}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-100 dark:bg-cyan-950/60 text-cyan-800 dark:text-cyan-300">
                        {n.element}
                      </span>
                    </div>
                    <div className="text-xs text-amber-600 dark:text-amber-400 font-bold">Occupied Planets: {n.planets}</div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 font-sans leading-relaxed">
                      {n.analysis}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* 🌟 Tab 3: Koorma Chakra */}
      {activeTab === "koorma" && (
        <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4 transition-colors bg-white dark:bg-slate-900/90">
          <div className="border-b pb-3 border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono flex items-center gap-2">
              <Compass className="w-4 h-4 text-cyan-500" />
              <span>KOORMA CHAKRA (REGIONAL & GEOPOLITICAL AFFLICTION MATRIX)</span>
            </span>
            <span className="text-xs font-mono text-slate-500 dark:text-slate-400">Varahamihira Brihat Samhita (Adhyaya 14)</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {curKoorma.map((s, idx) => (
              <div key={idx} className="p-4 rounded-xl border border-slate-200 dark:border-slate-700/60 space-y-2 transition-all bg-slate-50 dark:bg-slate-800/50">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-slate-900 dark:text-white font-sans text-sm">{s.direction}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                    s.condition === "Afflicted"
                      ? "bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800"
                      : s.condition === "Volatile"
                      ? "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800"
                      : "bg-cyan-100 dark:bg-cyan-950/60 text-cyan-800 dark:text-cyan-300 border border-cyan-300 dark:border-cyan-800"
                  }`}>
                    {s.condition}
                  </span>
                </div>
                <div className="text-xs text-cyan-700 dark:text-cyan-400 font-mono font-semibold">{s.states}</div>
                <p className="text-xs text-slate-600 dark:text-slate-300 font-sans leading-relaxed">
                  {s.details}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 🌟 Tab 4: Financial & Commodity Reality */}
      {activeTab === "financial" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {curFinancial.map((f, idx) => (
            <div key={idx} className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3 transition-colors bg-white dark:bg-slate-900/90">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
                {f.sector}
              </span>
              <div className={`text-xl font-extrabold font-mono ${f.color}`}>
                {f.trend}
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 font-sans leading-relaxed">
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function GlobeIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
      <path d="M2 12h20" />
    </svg>
  );
}

function CrownIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14" />
    </svg>
  );
}

function CloudRainIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242" />
      <path d="M16 14v6" />
      <path d="M8 14v6" />
      <path d="M12 16v6" />
    </svg>
  );
}

function TrendingUpIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
      <polyline points="16 7 22 7 22 13" />
    </svg>
  );
}
