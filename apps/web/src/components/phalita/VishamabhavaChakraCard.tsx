'use client';


import React, { useState } from "react";
import { CanonicalHouseSpan } from "@/lib/phalitaApi";
import { Compass, Sparkles, ShieldCheck, AlertCircle } from "./Icons";
import { useTheme } from "@/components/layout/ThemeProvider";

interface Props {
  lagnaMadhyaDeg: number;
  madhyaLagnaDeg: number;
  houses: CanonicalHouseSpan[];
}

const HOUSE_SIGNIFICANCE: Record<number, { title: string; sanskrit: string; karaka: string; description: string; bphsRule: string }> = {
  1: { title: "Tanu Bhava (Self & Vitality)", sanskrit: "तनु भाव", karaka: "Sun", description: "Governs physical constitution, general health, vitality, personality, temperament, longevity, and overall life orientation.", bphsRule: "Anchor of the entire horoscope; determines physical resilience and foundational destiny." },
  2: { title: "Dhana Bhava (Wealth & Speech)", sanskrit: "धन भाव", karaka: "Jupiter", description: "Governs accumulated liquid wealth, family assets, speech, oral expression, right eye, food habits, and ancestral lineage.", bphsRule: "Primary Dhana-sthana; sustained prosperity and credibility of spoken words." },
  3: { title: "Sahaja Bhava (Courage & Media)", sanskrit: "सहज भाव", karaka: "Mars", description: "Governs younger siblings, manual skills, boldness, communication, media, writing, short journeys, and self-effort (Upachaya).", bphsRule: "Parakrama-sthana; removes hesitation and compounds rewards through direct personal initiative." },
  4: { title: "Sukha Bhava (Home & Comfort)", sanskrit: "सुख भाव", karaka: "Moon", description: "Governs mother, real estate, vehicles, inner contentment, ancestral land, domestic peace, education, and heart health.", bphsRule: "Foundational Kendra; emotional stability and worldly shelter." },
  5: { title: "Putra Bhava (Creativity & Fortune)", sanskrit: "पुत्र भाव", karaka: "Jupiter", description: "Governs intellect, children, creative genius, speculative gains, purva-punya (past merit), mantras, and strategic foresight.", bphsRule: "Supreme Trikona; manifestation of divine grace and intellectual clarity." },
  6: { title: "Ari Bhava (Debts & Overcoming)", sanskrit: "अरि भाव", karaka: "Mars / Saturn", description: "Governs enemies, debts, daily labor, litigation, competitive resilience, and health management routines.", bphsRule: "Powerful Upachaya; converts struggle and discipline into ultimate competitive victory." },
  7: { title: "Yuvati Bhava (Partnerships)", sanskrit: "युवति भाव", karaka: "Venus", description: "Governs spouse, marriage, business joint ventures, public alliances, commercial agreements, and foreign relations.", bphsRule: "Direct mirror Kendra; success achieved through diplomacy and contractual trust." },
  8: { title: "Randhra Bhava (Transformation)", sanskrit: "रन्ध्र भाव", karaka: "Saturn", description: "Governs longevity, deep research, unearned wealth, inheritance, insurance, secret knowledge, and profound psychological rebirth.", bphsRule: "Moksha/Ayur-sthana; structural shedding that paves the way for higher wisdom." },
  9: { title: "Dharma Bhava (Fortune & Wisdom)", sanskrit: "धर्म भाव", karaka: "Jupiter", description: "Governs guru, father, pilgrimage, higher philosophy, spiritual ethics, international travels, and divine fortune (Bhagya).", bphsRule: "Greatest Trikona; effortless removal of obstacles through virtuous karma." },
  10: { title: "Karma Bhava (Career & Authority)", sanskrit: "कर्म भाव", karaka: "Sun / Mercury", description: "Governs vocation, executive appointments, government recognition, social standing, fame, leadership, and worldly achievements.", bphsRule: "Apex of the sky (Midheaven); maximum worldly power and public legacy." },
  11: { title: "Labha Bhava (Massive Gains)", sanskrit: "लाभ भाव", karaka: "Jupiter", description: "Governs financial cashflow, fulfillment of desires, influential networks, elder siblings, and lucrative commercial windfalls.", bphsRule: "Greatest Upachaya; monetizes the achievements of the 10th house." },
  12: { title: "Vyaya Bhava (Liberation & Solitude)", sanskrit: "व्यय भाव", karaka: "Saturn / Ketu", description: "Governs foreign lands, spiritual retreat, subconscious healing, meditation, charitable expenses, and final liberation (Moksha).", bphsRule: "Closing chapter of the cycle; releases old karma and recharges the soul." },
};

const RASHI_META: { symbol: string; name: string; short: string }[] = [
  { symbol: "♈", name: "Aries", short: "Ari" },
  { symbol: "♉", name: "Taurus", short: "Tau" },
  { symbol: "♊", name: "Gemini", short: "Gem" },
  { symbol: "♋", name: "Cancer", short: "Can" },
  { symbol: "♌", name: "Leo", short: "Leo" },
  { symbol: "♍", name: "Virgo", short: "Vir" },
  { symbol: "♎", name: "Libra", short: "Lib" },
  { symbol: "♏", name: "Scorpio", short: "Sco" },
  { symbol: "♐", name: "Sagittarius", short: "Sag" },
  { symbol: "♑", name: "Capricorn", short: "Cap" },
  { symbol: "♒", name: "Aquarius", short: "Aqu" },
  { symbol: "♓", name: "Pisces", short: "Pis" },
];

export const VishamabhavaChakraCard: React.FC<Props> = ({
  lagnaMadhyaDeg,
  madhyaLagnaDeg,
  houses,
}) => {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [selectedHouse, setSelectedHouse] = useState<CanonicalHouseSpan | null>(null);

  const fmtRashiDMS = (deg: number) => {
    const norm = ((deg % 360) + 360) % 360;
    const signIdx = Math.floor(norm / 30);
    const rem = norm % 30;
    const d = Math.floor(rem);
    const m = Math.floor((rem - d) * 60);
    const meta = RASHI_META[signIdx] || { symbol: "", short: "" };
    return {
      symbol: meta.symbol,
      short: meta.short,
      formatted: `${meta.symbol} ${String(d).padStart(2, "0")}°${String(m).padStart(2, "0")}'`,
    };
  };

  const fmtSpan = (deg: number) => {
    const d = Math.floor(deg);
    const m = Math.floor((deg - d) * 60);
    return `${d}°${String(m).padStart(2, "0")}'`;
  };

  const size = 250;
  const center = size / 2;
  const radius = 110;
  const innerRadius = 52;

  const houseDetails = selectedHouse ? HOUSE_SIGNIFICANCE[selectedHouse.house_number] : null;

  return (
    <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors space-y-4 bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
      {/* Card Header */}
      <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono flex items-center gap-1.5">
            <Compass className="w-4 h-4 text-cyan-500" />
            VISHAMABHAVA CHAKRA (D1 UNEQUAL HOUSE CUSPS)
          </span>
          <span className="text-[11px] text-slate-400 cursor-pointer" title="Unequal Bhavachalita cusps based on Sripati method">
            ⓘ
          </span>
        </div>
      </div>

      {/* Visual Chakra Wheel + Data Table Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-center">
        {/* SVG Bhaavachalita Wheel */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center p-2.5 border rounded-xl shrink-0 bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60">
          <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
            {/* Outer & Inner Circles */}
            <circle
              cx={center}
              cy={center}
              r={radius}
              fill={isDark ? "#0f172a" : "#ffffff"}
              stroke={isDark ? "#334155" : "#cbd5e1"}
              strokeWidth="2"
            />
            <circle
              cx={center}
              cy={center}
              r={innerRadius}
              fill={isDark ? "#0f172a" : "#f1f5f9"}
              stroke={isDark ? "#00f0ff" : "#0284c7"}
              strokeOpacity="0.4"
              strokeWidth="1.5"
            />

            {/* Center Axis Label */}
            <text x={center} y={center - 3} textAnchor="middle" fill={isDark ? "#38bdf8" : "#0284c7"} fontSize="9" fontWeight="bold" fontFamily="monospace">
              BHAAVA
            </text>
            <text x={center} y={center + 9} textAnchor="middle" fill={isDark ? "#64748b" : "#64748b"} fontSize="7" fontFamily="monospace">
              CHALITA
            </text>

            {/* Unequal House Wedges */}
            {houses.map((h) => {
              const angleDeg = ((h.madhya - lagnaMadhyaDeg) * -1) + 180;
              const angleRad = (angleDeg * Math.PI) / 180;

              const x1 = center + innerRadius * Math.cos(angleRad);
              const y1 = center + innerRadius * Math.sin(angleRad);
              const x2 = center + radius * Math.cos(angleRad);
              const y2 = center + radius * Math.sin(angleRad);

              const textR = (radius + innerRadius) / 2;
              const tx = center + textR * Math.cos(angleRad);
              const ty = center + textR * Math.sin(angleRad);

              const isKendra = [1, 4, 7, 10].includes(h.house_number);
              const isSelected = selectedHouse?.house_number === h.house_number;

              return (
                <g
                  key={h.house_number}
                  className="cursor-pointer group"
                  onClick={() => setSelectedHouse(h)}
                >
                  <line
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke={isKendra ? (isDark ? "#00f0ff" : "#0284c7") : (isDark ? "#1e293b" : "#cbd5e1")}
                    strokeWidth={isKendra ? "1.8" : "1"}
                  />
                  <circle
                    cx={tx}
                    cy={ty}
                    r="8.5"
                    fill={isSelected ? (isDark ? "#00f0ff" : "#0284c7") : isKendra ? (isDark ? "#082f49" : "#e0f2fe") : (isDark ? "#070e1c" : "#ffffff")}
                    stroke={isSelected ? "#ffffff" : isKendra ? (isDark ? "#38bdf8" : "#0284c7") : (isDark ? "#334155" : "#94a3b8")}
                    strokeWidth="1"
                    className="group-hover:stroke-cyan-500 transition-colors"
                  />
                  <text
                    x={tx}
                    y={ty + 3}
                    textAnchor="middle"
                    fill={isSelected ? (isDark ? "#050b14" : "#ffffff") : isKendra ? (isDark ? "#38bdf8" : "#0369a1") : (isDark ? "#94a3b8" : "#475569")}
                    fontSize="8"
                    fontWeight="bold"
                    fontFamily="monospace"
                  >
                    {h.house_number}
                  </text>
                </g>
              );
            })}
          </svg>
          <div className="text-[10px] text-cyan-600 dark:text-cyan-400 font-mono text-center mt-1">
            Click any house wedge for details 🔍
          </div>
        </div>

        {/* 12 Unequal Houses Table */}
        <div className="lg:col-span-7 overflow-x-auto rounded-lg border border-slate-800/40">
          <table className="w-full text-left text-xs font-mono">
            <thead className={`uppercase tracking-wider text-[10px] border-b ${
              isDark ? "bg-[#070e1c] text-slate-400 border-[#17263c]" : "bg-slate-100 text-slate-600 border-slate-200"
            }`}>
              <tr>
                <th className="py-2 px-2 text-center">H</th>
                <th className="py-2 px-2">Start (Sandhi)</th>
                <th className="py-2 px-2">Madhya (Cusp)</th>
                <th className="py-2 px-2">End (Sandhi)</th>
                <th className="py-2 px-2 text-right">Span</th>
              </tr>
            </thead>
            <tbody className={`divide-y text-[11px] ${
              isDark ? "divide-[#17263c]/50 text-slate-200" : "divide-slate-200 text-slate-800"
            }`}>
              {houses.map((h) => {
                const span = h.total_span_deg || ((h.end_sandhi - h.start_sandhi + 360) % 360);
                const isSelected = selectedHouse?.house_number === h.house_number;
                const startFormatted = fmtRashiDMS(h.start_sandhi);
                const madhyaFormatted = fmtRashiDMS(h.madhya);
                const endFormatted = fmtRashiDMS(h.end_sandhi);

                return (
                  <tr
                    key={h.house_number}
                    onClick={() => setSelectedHouse(h)}
                    className={`cursor-pointer transition-colors ${
                      isDark
                        ? `hover:bg-cyan-950/20 ${isSelected ? 'bg-cyan-950/40 border-l-2 border-cyan-400' : ''}`
                        : `hover:bg-cyan-50 ${isSelected ? 'bg-cyan-100 border-l-2 border-cyan-600' : ''}`
                    }`}
                  >
                    <td className="py-1 px-2 font-bold text-center text-cyan-600 dark:text-cyan-300">
                      {h.house_number}
                    </td>
                    <td className="py-1 px-2 whitespace-nowrap text-slate-400 dark:text-slate-400">
                      {startFormatted.formatted}
                    </td>
                    <td className="py-1 px-2 whitespace-nowrap font-semibold text-slate-900 dark:text-white">
                      {madhyaFormatted.formatted}
                    </td>
                    <td className="py-1 px-2 whitespace-nowrap text-slate-400 dark:text-slate-400">
                      {endFormatted.formatted}
                    </td>
                    <td className="py-1 px-2 text-right whitespace-nowrap text-emerald-600 dark:text-emerald-400 font-semibold">
                      {fmtSpan(span || 27.5)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="text-[10px] text-slate-500 font-mono pt-1">
        Cusps calculated using Lagna Madhya &amp; Bhava Madhya (Unequal Houses via Sripati method)
      </div>

      {/* 🌟 FULL CENTERED HOUSE INSPECTOR MODAL POPUP */}
      {selectedHouse && houseDetails && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-lg rounded-2xl border border-cyan-500/40 shadow-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100">
            {/* Header */}
            <div className="flex justify-between items-start border-b border-slate-200 dark:border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono block">
                  House H{selectedHouse.house_number} • {houseDetails.sanskrit}
                </span>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-0.5">
                  {houseDetails.title}
                </h3>
                <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 font-mono block mt-0.5">
                  Karaka (Significator): {houseDetails.karaka}
                </span>
              </div>
              <button
                onClick={() => setSelectedHouse(null)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center font-bold text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Classical Significance Description */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2 text-xs leading-relaxed bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300">
              <div className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                <span>📖</span> Classical Parashari Significance:
              </div>
              <p>{houseDetails.description}</p>
              <div className="text-[11px] text-cyan-700 dark:text-cyan-400 font-medium pt-1 border-t border-slate-200 dark:border-slate-700/60">
                💡 <strong>Shastric Rule:</strong> {houseDetails.bphsRule}
              </div>
            </div>

            {/* Exact Sripati Cusp Boundaries */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono block">
                Exact Sripati Cusp Boundaries (Degrees & Arcminutes)
              </span>
              <div className="grid grid-cols-3 gap-2 text-center font-mono text-xs">
                <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 block">Start Sandhi</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{fmtRashiDMS(selectedHouse.start_sandhi).formatted}</span>
                </div>
                <div className="p-2.5 rounded-lg border border-cyan-500/40 bg-cyan-50 dark:bg-cyan-950/40">
                  <span className="text-[10px] text-cyan-700 dark:text-cyan-400 block">Bhava Madhya</span>
                  <span className="font-bold text-cyan-700 dark:text-cyan-300">{fmtRashiDMS(selectedHouse.madhya).formatted}</span>
                </div>
                <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 block">End Sandhi</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{fmtRashiDMS(selectedHouse.end_sandhi).formatted}</span>
                </div>
              </div>
            </div>

            {/* Close Button */}
            <button
              onClick={() => setSelectedHouse(null)}
              className="w-full py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs transition-all cursor-pointer shadow-md"
            >
              Done / Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
