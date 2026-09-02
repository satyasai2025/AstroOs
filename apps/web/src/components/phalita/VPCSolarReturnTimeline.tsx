'use client';

import React, { useState, useMemo } from "react";
import { useTheme } from "@/components/layout/ThemeProvider";
import { VPCSolarReturnReport } from "@/lib/phalitaApi";
import { Calendar, Clock, Milestone, Sparkles, ChevronDown, ChevronUp } from "./Icons";
import { DiamondChart } from "./DiamondChart";
import {
  VargaChartData,
  VargaPlacement,
  RASHI_NAMES,
  RASHI_LORDS,
  getPlanetDignity,
  DEFAULT_D1_LONGITUDES,
} from "@/lib/vargaCalculator";

interface Props {
  vpcReport: VPCSolarReturnReport;
  availableYears?: number[];
  selectedYear: number;
  onSelectYear: (year: number) => void;
  locationName?: string;
  timezoneText?: string;
  onEditLocation?: () => void;
}

const RASHI_LIST_LOWER = [
  "aries", "taurus", "gemini", "cancer",
  "leo", "virgo", "libra", "scorpio",
  "sagittarius", "capricorn", "aquarius", "pisces"
];

const MUNTHA_FOCUS_MAP: Record<number, { focus: string; strength: string; color: string; desc: string }> = {
  1: { focus: "Self-Reinvention, Vitality & Leadership", strength: "Very Strong", color: "text-emerald-500", desc: "New beginnings, personal charisma, and taking direct initiative." },
  2: { focus: "Wealth Accumulation & Family Assets", strength: "High", color: "text-emerald-500", desc: "Liquid cashflow growth, family assets consolidation, and valued speech." },
  3: { focus: "Enterprise, Bold Initiatives & Media", strength: "Strong", color: "text-teal-500", desc: "Courage, writing/media projects, short travels, and self-effort gains." },
  4: { focus: "Home, Real Estate & Emotional Peace", strength: "High (Kendra)", color: "text-cyan-500", desc: "Property investments, domestic happiness, homeland stability, and mother's blessing." },
  5: { focus: "Intellect, Creative Genius & Purva-Punya", strength: "Supreme (Trikona)", color: "text-amber-500", desc: "Strategic brilliance, speculative success, mentorship, and creative fulfillment." },
  6: { focus: "Competitive Victory & Service Mastery", strength: "Dynamic (Upachaya)", color: "text-blue-500", desc: "Overcoming adversaries, debt clearance, competitive discipline, and health resilience." },
  7: { focus: "Public Partnerships & Commercial Contracts", strength: "High (Kendra)", color: "text-indigo-500", desc: "Joint ventures, marital milestones, commercial pacts, and bilateral expansion." },
  8: { focus: "Deep Transformation & Unlocking Stuck Assets", strength: "Intense / Transformative", color: "text-purple-500", desc: "Research, resolving legacy bottlenecks, unearned wealth, and architectural restructuring." },
  9: { focus: "Divine Fortune, Wisdom & Global Expansion", strength: "Supreme (Trikona)", color: "text-emerald-500", desc: "Bhagya manifestation, pilgrimage, higher education, guru blessings, and international travels." },
  10: { focus: "Career Elevation, Executive Status & Authority", strength: "Supreme (Kendra)", color: "text-cyan-400", desc: "Promotions, public prestige, administrative influence, and worldly accomplishments." },
  11: { focus: "Massive Gains, Network Windfalls & Desires", strength: "High (Upachaya)", color: "text-emerald-400", desc: "Multi-channel cashflow, realization of major ambitions, and elite networking." },
  12: { focus: "Overseas Horizons, Solitude & Subconscious Growth", strength: "Reflective / Spiritual", color: "text-rose-400", desc: "International projects, meditation, charitable expenses, and spiritual elevation." },
};

export const VPCSolarReturnTimeline: React.FC<Props> = ({
  vpcReport,
  availableYears,
  selectedYear,
  onSelectYear,
  locationName = "New Delhi, India",
  timezoneText = "UTC +05:30",
  onEditLocation,
}) => {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [showNarrative, setShowNarrative] = useState(false);

  // Dynamic 5-year pill window
  const yearPills = useMemo(() => {
    if (availableYears && availableYears.length > 0) return availableYears;
    return [selectedYear - 2, selectedYear - 1, selectedYear, selectedYear + 1, selectedYear + 2];
  }, [availableYears, selectedYear]);

  // Exact Solar Return Moment
  const vpcDt = new Date(vpcReport.vpc_datetime_utc || Date.now());
  const formattedDate = vpcDt.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
  const formattedTime = vpcDt.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

  // Muntha & Varshaphal Extracted Calculated Data
  const muntha = vpcReport.muntha;
  const munthaHouse = muntha?.house_number ?? (vpcReport.scd_annual_house || 10);
  const munthaRashi = muntha?.rashi
    ? muntha.rashi.charAt(0).toUpperCase() + muntha.rashi.slice(1).toLowerCase()
    : RASHI_NAMES[(munthaHouse - 1) % 12];
  const munthaLord = muntha?.lord || RASHI_LORDS[RASHI_NAMES.indexOf(munthaRashi)] || "Saturn";

  const yearLord = vpcReport.year_lord?.selected || "Mercury";
  const yearLordMethod = vpcReport.year_lord?.selection_method || "Panchadhikari";

  const munthaInfo = MUNTHA_FOCUS_MAP[munthaHouse] || MUNTHA_FOCUS_MAP[10];

  // Dynamic Sun Longitude
  const sunLongitudeFormatted = useMemo(() => {
    if (vpcReport.sun_longitude_deg != null) {
      const lon = (vpcReport.sun_longitude_deg % 360 + 360) % 360;
      const signIdx = Math.floor(lon / 30);
      const degInSign = lon % 30;
      const d = Math.floor(degInSign);
      const m = Math.floor((degInSign - d) * 60);
      return `${String(d).padStart(2, "0")}° ${String(m).padStart(2, "0")}' ${RASHI_NAMES[signIdx]}`;
    }
    return "13° 05' Gemini";
  }, [vpcReport.sun_longitude_deg]);

  // Annual Outlook Score (Calculated Dynamically from Muntha House, Kendra/Trikona, Year Lord)
  const { outlookScore, outlookCategory, outlookDesc } = useMemo(() => {
    let score = 52;
    if ([1, 4, 7, 10].includes(munthaHouse)) score += 26;
    else if ([5, 9].includes(munthaHouse)) score += 28;
    else if ([3, 11].includes(munthaHouse)) score += 20;
    else if (munthaHouse === 2) score += 16;
    else score -= 4; // Dusthana (6, 8, 12)

    // Year Lord bonus
    if (["Jupiter", "Venus", "Mercury", "Sun"].includes(yearLord)) score += 6;
    else score += 4;

    const clamped = Math.min(94, Math.max(54, score));
    let cat = "Positive Year";
    let desc = "Favorable for steady growth through structured effort.";
    if (clamped >= 80) {
      cat = "Exceptional Year";
      desc = "Highly auspicious for major breakthroughs, elevation and success.";
    } else if (clamped >= 70) {
      cat = "Highly Favorable";
      desc = "Strong planetary support for ambitious initiatives.";
    } else if (clamped < 60) {
      cat = "Dynamic / Transformative";
      desc = "Strategic focus and patience required to resolve underlying bottlenecks.";
    }

    return { outlookScore: clamped, outlookCategory: cat, outlookDesc: desc };
  }, [munthaHouse, yearLord]);

  // 🌟 Live Solar Return Diamond Chart Construction with Muntha Badge
  const vpcChartData: VargaChartData = useMemo(() => {
    const varshaAsc = vpcReport.varsha_ascendant;
    const ascRashiLower = (varshaAsc?.rashi || "gemini").toLowerCase();
    const ascRashiIdx = RASHI_LIST_LOWER.indexOf(ascRashiLower);
    const ascRashiNum = ascRashiIdx >= 0 ? ascRashiIdx + 1 : 3;

    const houses: Record<number, { rashiNumber: number; planets: VargaPlacement[] }> = {};
    for (let h = 1; h <= 12; h++) {
      const rashiNum = ((ascRashiNum - 1 + (h - 1)) % 12) + 1;
      houses[h] = { rashiNumber: rashiNum, planets: [] };
    }

    const vimshopakaPlanets: VargaPlacement[] = [];
    let totalScore = 0;

    const varshaPlanets = vpcReport.varsha_planets || [];
    for (const p of varshaPlanets) {
      const pRashiLower = p.rashi.toLowerCase();
      const pRashiIdx = RASHI_LIST_LOWER.indexOf(pRashiLower);
      const pRashiNum = pRashiIdx >= 0 ? pRashiIdx + 1 : 1;
      const houseNum = p.house_number || (((pRashiNum - ascRashiNum + 12) % 12) + 1);
      const dignityInfo = getPlanetDignity(p.planet, pRashiNum);
      const baseGlyph = DEFAULT_D1_LONGITUDES[p.planet]?.glyph || p.planet.slice(0, 2);
      const glyph = `${baseGlyph}${p.is_retrograde ? " (R)" : ""}`;

      const placement: VargaPlacement = {
        planet: p.planet,
        glyph,
        rashiNumber: pRashiNum,
        rashiName: RASHI_NAMES[pRashiNum - 1],
        rashiDeg: p.rashi_degree || 0,
        houseNumber: houseNum,
        dignity: p.dignity || dignityInfo.dignity,
        score: dignityInfo.score,
        status: dignityInfo.status,
        color: dignityInfo.color,
        textCol: dignityInfo.textCol,
        isRetro: p.is_retrograde,
      };

      if (houses[houseNum]) {
        houses[houseNum].planets.push(placement);
      }
      vimshopakaPlanets.push(placement);
      totalScore += dignityInfo.score;
    }

    // Add Muntha as a highlighted badge inside its active house
    if (munthaHouse && houses[munthaHouse]) {
      houses[munthaHouse].planets.push({
        planet: "Muntha",
        glyph: "🎯 Mun",
        rashiNumber: houses[munthaHouse].rashiNumber,
        rashiName: RASHI_NAMES[houses[munthaHouse].rashiNumber - 1],
        rashiDeg: 0,
        houseNumber: munthaHouse,
        dignity: "Annual Focus",
        score: 18.0,
        status: "Strong",
        color: "bg-cyan-500",
        textCol: "text-cyan-400 font-bold",
      });
    }

    const avgScore = vimshopakaPlanets.length ? totalScore / vimshopakaPlanets.length : 14;
    const potentialScore = Math.min(96, Math.max(58, Math.round((avgScore / 20) * 100)));

    const centerRashis = {
      h1: houses[1].rashiNumber,
      h4: houses[4].rashiNumber,
      h7: houses[7].rashiNumber,
      h10: houses[10].rashiNumber,
    };

    return {
      vargaCode: "VPC",
      vargaName: `Solar Return ${selectedYear}`,
      domain: `Tajika Varsha Chart (Age ${vpcReport.completed_years || (selectedYear - 1971)})`,
      weight: 20,
      ascendantRashi: ascRashiNum,
      ascendantName: RASHI_NAMES[ascRashiNum - 1],
      centerRashis,
      houses,
      indicators: {
        ascendant: `${RASHI_NAMES[ascRashiNum - 1]} (${ascRashiNum})`,
        lord: RASHI_LORDS[ascRashiNum - 1],
        tenthHouse: `${RASHI_NAMES[houses[10].rashiNumber - 1]} (${houses[10].rashiNumber})`,
        ak: yearLord,
        weight: 20,
        activation: "High",
      },
      signalMetrics: [
        { label: "Annual Momentum", score: 17.5, max: 20 },
        { label: "Muntha Alignment", score: [1, 4, 7, 10, 5, 9, 11].includes(munthaHouse) ? 18.2 : 13.6, max: 20 },
        { label: "Year Lord Dignity", score: 16.4, max: 20 },
        { label: "Quarterly Stability", score: 15.8, max: 20 },
        { label: "Dhana Inflow Potential", score: 17.0, max: 20 },
      ],
      potentialScore,
      vimshopakaPlanets,
    };
  }, [vpcReport, selectedYear, munthaHouse, yearLord]);

  // 🌟 Dynamic 5 Yearly Themes based on Muntha House & Year Lord
  const dynamicThemes = useMemo(() => {
    return [
      {
        title: "Primary Karma",
        desc: munthaInfo.focus,
        icon: "🎯",
      },
      {
        title: "Year Lord (Varshēsha)",
        desc: `${yearLord} governs annual governance and protective armor via ${yearLordMethod.replace(/_/g, " ")}.`,
        icon: "👑",
      },
      {
        title: "Muntha Territory",
        desc: `Lands in House H${munthaHouse} (${munthaRashi}), energized by its lord ${munthaLord}.`,
        icon: "🏛️",
      },
      {
        title: "Financial Direction",
        desc: [2, 11, 5].includes(munthaHouse)
          ? "High wealth accumulation and lucrative cashflow windfalls."
          : "Steady financial stability through structured management.",
        icon: "💰",
      },
      {
        title: "Strategic Guidance",
        desc: [6, 8, 12].includes(munthaHouse)
          ? "Deep foundation building, patience with transformation, and solving backend bottlenecks."
          : "Execute bold initiatives with confident public presence and clear milestone tracking.",
        icon: "🌿",
      },
    ];
  }, [munthaInfo, munthaHouse, munthaRashi, munthaLord, yearLord, yearLordMethod]);

  return (
    <div className="space-y-6">
      {/* Top Row: VPC Configuration (Left), VPC Diamond Chart (Mid), Muntha + Outlook (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: VPC Solar Return Details & Year Selector */}
        <div className="lg:col-span-4 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4 transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-cyan-500" />
              VPC SOLAR RETURN (VARSHAPHAL)
            </span>
          </div>

          {/* Select Target Year Stepper & Pills */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono block">
                SELECT TARGET YEAR
              </span>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min="1900"
                  max="2100"
                  value={selectedYear}
                  onChange={(e) => onSelectYear(Number(e.target.value))}
                  aria-label="Target Solar Return Year"
                  className="w-20 text-xs font-extrabold font-mono text-cyan-800 dark:text-cyan-200 rounded border border-slate-300 dark:border-slate-700 px-2 py-0.5 focus:outline-none bg-slate-50 dark:bg-slate-800"
                />
                <button
                  type="button"
                  onClick={() => onSelectYear(new Date().getFullYear())}
                  className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-cyan-500"
                >
                  Current
                </button>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs">
              <button
                onClick={() => onSelectYear(selectedYear - 1)}
                className="px-2 py-1 rounded-lg border text-xs cursor-pointer transition-all bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
                title="Previous Solar Return Year"
              >
                &lt;
              </button>
              {yearPills.map((yr) => (
                <button
                  key={yr}
                  onClick={() => onSelectYear(yr)}
                  className={`px-3 py-1 rounded-lg border transition-all cursor-pointer font-bold ${
                    selectedYear === yr
                      ? "bg-cyan-500 text-slate-950 border-cyan-400 shadow-sm scale-105"
                      : "bg-slate-50 dark:bg-slate-800/60 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-cyan-500"
                  }`}
                >
                  {yr}
                </button>
              ))}
              <button
                onClick={() => onSelectYear(selectedYear + 1)}
                className="px-2 py-1 rounded-lg border text-xs cursor-pointer transition-all bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
                title="Next Solar Return Year"
              >
                &gt;
              </button>
            </div>
          </div>

          {/* Solar Return Metadata Details */}
          <div className="pt-2 border-t border-slate-200 dark:border-slate-800 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono block">
              SOLAR RETURN DETAILS
            </span>

            <div className="divide-y divide-slate-200 dark:divide-slate-800 text-xs font-mono">
              <div className="py-1.5 flex justify-between">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Date</span>
                <span className="font-bold text-slate-900 dark:text-white">{formattedDate}</span>
              </div>
              <div className="py-1.5 flex justify-between">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Exact Moment (UTC)</span>
                <span className="font-bold text-cyan-600 dark:text-cyan-300">{formattedTime} UTC</span>
              </div>
              <div className="py-1.5 flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Location</span>
                <div className="flex items-center gap-1.5">
                  <span className="text-slate-700 dark:text-slate-200 font-semibold">{locationName}</span>
                  {onEditLocation && (
                    <button
                      type="button"
                      onClick={onEditLocation}
                      className="px-1.5 py-0.5 rounded text-[10px] font-bold font-mono bg-cyan-100 dark:bg-cyan-950 text-cyan-700 dark:text-cyan-300 border border-cyan-300 dark:border-cyan-800 hover:bg-cyan-200 dark:hover:bg-cyan-900 cursor-pointer flex items-center gap-0.5 transition"
                      title="Edit Birth or Solar Return Location"
                    >
                      <span>✏️</span>
                      <span>Change</span>
                    </button>
                  )}
                </div>
              </div>
              <div className="py-1.5 flex justify-between">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Timezone</span>
                <span className="text-slate-700 dark:text-slate-300">{timezoneText}</span>
              </div>
              <div className="py-1.5 flex justify-between">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Sun Longitude</span>
                <span className="text-amber-500 font-bold">{sunLongitudeFormatted}</span>
              </div>
              <div className="py-1.5 flex justify-between">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Calculated Age</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                  {vpcReport.completed_years} Completed Years
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Middle: VPC Solar Return Diamond Chart */}
        <div className={`lg:col-span-5 border rounded-xl p-5 shadow-xl flex flex-col items-center justify-between transition-colors ${
          isDark ? "bg-[#0b1424] border-[#17263c] text-slate-100" : "bg-white border-slate-200 text-slate-900"
        }`}>
          <div className={`w-full flex items-center justify-between border-b pb-3 mb-4 ${isDark ? "border-[#17263c]" : "border-slate-200"}`}>
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono flex items-center gap-1.5">
              <span>🏛️ VARSHA PRAVESHA CHART ({selectedYear})</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-100 dark:bg-cyan-950 text-cyan-700 dark:text-cyan-300 border border-cyan-300 dark:border-cyan-800 font-bold">
              🎯 Muntha in H{munthaHouse}
            </span>
          </div>

          <DiamondChart vargaData={vpcChartData} />
        </div>

        {/* Right: Muntha Analysis + Annual Outlook Meter */}
        <div className="lg:col-span-3 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between space-y-4 transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          <div className="space-y-3">
            <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
                Muntha Analysis ({selectedYear})
              </span>
            </div>

            <div className="divide-y divide-slate-200 dark:divide-slate-800 text-xs font-mono">
              <div className="py-1.5 flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Muntha House</span>
                <span className="font-bold text-cyan-700 dark:text-cyan-300">
                  House H{munthaHouse} ({munthaRashi})
                </span>
              </div>
              <div className="py-1.5 flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Muntha Lord</span>
                <span className="font-bold text-indigo-700 dark:text-indigo-300">{munthaLord}</span>
              </div>
              <div className="py-1.5 flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Annual Focus</span>
                <span className="text-slate-700 dark:text-slate-200 text-right font-medium max-w-[150px] truncate" title={munthaInfo.focus}>
                  {munthaInfo.focus}
                </span>
              </div>
              <div className="py-1.5 flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Yearly Lord (Varshēsha)</span>
                <span className="font-bold text-emerald-700 dark:text-emerald-300">{yearLord}</span>
              </div>
              <div className="py-1.5 flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400 font-sans">Focus Strength</span>
                <span className={`font-bold ${munthaInfo.color}`}>{munthaInfo.strength}</span>
              </div>
            </div>
          </div>

          {/* Annual Outlook Circular Meter */}
          <div className="p-4 border rounded-xl flex flex-col items-center text-center bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono mb-2">
              ANNUAL OUTLOOK
            </span>
            <div className="relative w-20 h-20 flex items-center justify-center">
              <svg viewBox="0 0 36 36" className="w-full h-full text-teal-500 -rotate-90">
                <path
                  className="text-slate-200 dark:text-slate-800"
                  strokeWidth="3.5"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className="text-teal-500"
                  strokeDasharray={`${outlookScore}, 100`}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div className="absolute text-center">
                <span className="text-base font-extrabold text-slate-900 dark:text-white font-mono">
                  {outlookScore}%
                </span>
              </div>
            </div>
            <span className="text-xs font-bold text-teal-700 dark:text-teal-300 font-sans mt-2">
              {outlookCategory}
            </span>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">{outlookDesc}</span>
          </div>
        </div>
      </div>

      {/* Bottom Row: 5 Yearly Themes & Forecast Cards */}
      <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4 transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
          <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
            YEARLY THEMES & FORECAST ({selectedYear})
          </span>

          <button
            onClick={() => setShowNarrative(!showNarrative)}
            className="text-xs text-cyan-600 dark:text-cyan-400 hover:underline flex items-center gap-1 cursor-pointer font-mono font-semibold"
          >
            {showNarrative ? "▲ Collapse Narrative" : "▼ Expand Full Narrative Reading"}
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {dynamicThemes.map((t, idx) => (
            <div key={idx} className="p-3.5 border rounded-xl space-y-1.5 bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60">
              <div className="text-xs font-bold text-cyan-800 dark:text-cyan-200 font-mono flex items-center gap-1.5">
                <span>{t.icon}</span>
                <span>{t.title}</span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 font-sans leading-relaxed">
                {t.desc}
              </p>
            </div>
          ))}
        </div>

        {/* Expandable Deep Shastric Narrative */}
        {showNarrative && (
          <div className="p-5 border rounded-xl space-y-5 pt-4 text-xs leading-relaxed font-sans transition-all bg-cyan-50/40 dark:bg-cyan-950/20 border-cyan-200 dark:border-cyan-900/40 text-slate-800 dark:text-slate-200">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-3 border-cyan-500/20">
              <h4 className="font-bold text-sm text-cyan-800 dark:text-cyan-200 font-mono flex items-center gap-2">
                <span>🏛️ Tajika Varshaphal Shastric Synthesis for Year {selectedYear}</span>
              </h4>
              <span className="text-[10px] px-2.5 py-0.5 rounded font-mono font-bold bg-cyan-100 dark:bg-cyan-950 text-cyan-800 dark:text-cyan-200 border border-cyan-300 dark:border-cyan-800 w-fit">
                Tajik Neelakanthi Standard
              </span>
            </div>

            {/* 1. Core Meaning in Simple English (Table Format) */}
            <div className="space-y-2.5">
              <div className="font-bold text-xs uppercase tracking-wider text-cyan-800 dark:text-cyan-300 font-mono">
                1. 🧠 Core Meaning in Simple English
              </div>

              <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
                <table className="w-full text-left text-xs font-sans">
                  <thead className="uppercase tracking-wider text-[10px] border-b bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700">
                    <tr>
                      <th className="py-2.5 px-4 font-mono font-bold w-1/3">Tajika Principle</th>
                      <th className="py-2.5 px-4 font-mono font-bold">What It Means for You in {selectedYear}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-900">
                    <tr>
                      <td className="py-3 px-4 font-bold text-cyan-700 dark:text-cyan-300 font-mono">
                        Muntha in House H{munthaHouse} ({munthaRashi})
                      </td>
                      <td className="py-3 px-4 text-slate-700 dark:text-slate-300 leading-relaxed">
                        <strong className="text-slate-900 dark:text-white block mb-0.5">
                          {munthaInfo.focus}:
                        </strong>
                        {munthaInfo.desc} In this solar return year (Age {vpcReport.completed_years}), your consciousness and major events will center around the {munthaHouse}th house themes.
                      </td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                        Year Lord (Varshēsha: {yearLord})
                      </td>
                      <td className="py-3 px-4 text-slate-700 dark:text-slate-300 leading-relaxed">
                        <strong className="text-slate-900 dark:text-white block mb-0.5">
                          Panchadhikari Selected: {yearLord}
                        </strong>
                        Selected via {yearLordMethod.replace(/_/g, " ")}. The Year Lord acts as the supreme custodian of the year, steering the timing of events and turning initial friction into sustained progress.
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* 2. Astrological Nuance & Context */}
            <div className={`p-4 rounded-xl border space-y-1.5 ${
              isDark ? "bg-amber-950/20 border-amber-800/40 text-amber-200" : "bg-amber-50 border-amber-300 text-amber-900"
            }`}>
              <div className="font-bold font-mono text-xs flex items-center gap-1.5">
                <span>⚠️ Astrological Nuance: House H{munthaHouse} Activation</span>
              </div>
              <p className="text-[11px] leading-relaxed">
                In classical Tajik Shastra (<em>Tajik Neelakanthi</em>), when Muntha occupies House {munthaHouse} governed by {munthaLord}, it highlights the specific karmic axis that must be prioritized during the 12 solar months of {selectedYear}.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
