"use client";

import React, { useState, useMemo } from "react";

export interface GrahaAlignment {
  point_name: string;
  rashi: string;
  house_from_lagna: number;
  house_from_moon: number;
  house_from_sun: number;
  tri_fold_auspiciousness: string;
  supporting_lagnas_count: number;
}

export interface SudarshanaData {
  lagna_rashi: string;
  moon_rashi: string;
  sun_rashi: string;
  tri_fold_harmony_score: number;
  current_scd: {
    age_years: number;
    active_house: number;
    primary_theme: string;
    significations: string[];
  };
  graha_alignments?: GrahaAlignment[];
}

interface SudarshanaChakraWheelProps {
  data: SudarshanaData;
  lang?: "hi" | "en";
}

const HOUSE_THEMES: Record<number, { en: string; hi: string; sigsEn: string[]; sigsHi: string[] }> = {
  1: { en: "Tanu Bhava (Deha / Identity & Vitality)", hi: "तनु भाव (शरीर, आत्म-सम्मान, जीवन शक्ति)", sigsEn: ["Self", "Vitality", "Appearance"], sigsHi: ["शरीर", "स्वास्थ्य", "आत्म-विश्वास"] },
  2: { en: "Dhana Bhava (Wealth & Family Assets)", hi: "धन भाव (संचित धन, परिवार, वाणी)", sigsEn: ["Liquid Wealth", "Family", "Speech"], sigsHi: ["धन संचय", "कुटुंब", "वाणी"] },
  3: { en: "Sahaja Bhava (Courage & Siblings)", hi: "सहज भाव (पराक्रम, अनुज, उद्यम)", sigsEn: ["Courage", "Short Journeys", "Siblings"], sigsHi: ["साहस", "उद्यम", "यात्रा"] },
  4: { en: "Sukha Bhava (Mother, Home & Vehicles)", hi: "सुख भाव (मातृ, गृह, वाहन, आंतरिक शांति)", sigsEn: ["Home", "Mother", "Conveyances"], sigsHi: ["गृह सुख", "माता", "भूमि-वाहन"] },
  5: { en: "Suta Bhava (Intellect, Children & Destiny)", hi: "सुत भाव (बुद्धि, संतान, पूर्व-पुण्य)", sigsEn: ["Intellect", "Progeny", "Creativity"], sigsHi: ["प्रज्ञा", "संतान", "मंत्र सिद्धि"] },
  6: { en: "Ripu Bhava (Obstacles, Health & Service)", hi: "रिपु भाव (शत्रु, रोग, ऋण, सेवा)", sigsEn: ["Health Struggles", "Debts", "Victory over foes"], sigsHi: ["रोग निवारण", "ऋण मुक्ति", "प्रतियोगिता"] },
  7: { en: "Kalatra Bhava (Partnerships & Marriage)", hi: "कलत्र भाव (विवाह, व्यापार, लोक-संबंध)", sigsEn: ["Spouse", "Business Alliances", "Foreign Travel"], sigsHi: ["जीवनसाथी", "साझेदारी", "सार्वजनिक छवि"] },
  8: { en: "Randhra Bhava (Transformation & Longevity)", hi: "रन्ध्र भाव (आयु, गुप्त विद्या, अप्रत्याशित परिवर्तन)", sigsEn: ["Longevity", "Occult", "Sudden Ups/Downs"], sigsHi: ["आयुष्य", "गुप्त ज्ञान", "कायाकल्प"] },
  9: { en: "Bhagya Bhava (Dharma, Fortune & Guru)", hi: "भाग्य भाव (धर्म, गुरु कृपा, उच्च भाग्य)", sigsEn: ["Higher Dharma", "Guru", "Divine Fortune"], sigsHi: ["धर्म", "गुरु आशीर्वाद", "तीर्थाटन"] },
  10: { en: "Karma Bhava (Career Authority & Prestige)", hi: "कर्म भाव (राजसत्ता, पदोन्नति, सामाजिक प्रतिष्ठा)", sigsEn: ["Profession", "Authority", "Public Status"], sigsHi: ["कर्म क्षेत्र", "अधिकार", "यश-कीर्ति"] },
  11: { en: "Labha Bhava (Gains, Network & Fulfilment)", hi: "लाभ भाव (आय, अभीष्ट सिद्धि, ज्येष्ठ भ्राता)", sigsEn: ["Great Gains", "Social Reach", "Goal Fruition"], sigsHi: ["प्रचुर लाभ", "मित्र मंडल", "मनोकामना पूर्ति"] },
  12: { en: "Vyaya Bhava (Liberation & Distant Horizons)", hi: "व्यय भाव (मोक्ष, विदेश वास, व्यय)", sigsEn: ["Foreign Settling", "Moksha", "Expenditures"], sigsHi: ["मोक्ष", "विदेश गमन", "त्याग"] },
};

const PLANET_SYMBOLS: Record<string, { glyph: string; color: string; label: string }> = {
  SUN: { glyph: "☉", color: "#fb923c", label: "Sun" },
  MOON: { glyph: "☽", color: "#60a5fa", label: "Moon" },
  MARS: { glyph: "♂", color: "#f87171", label: "Mars" },
  MERCURY: { glyph: "☿", color: "#34d399", label: "Mercury" },
  JUPITER: { glyph: "♃", color: "#fbbf24", label: "Jupiter" },
  VENUS: { glyph: "♀", color: "#f472b6", label: "Venus" },
  SATURN: { glyph: "♄", color: "#a78bfa", label: "Saturn" },
  RAHU: { glyph: "☊", color: "#818cf8", label: "Rahu" },
  KETU: { glyph: "☋", color: "#c084fc", label: "Ketu" },
};

export function SudarshanaChakraWheel({ data, lang = "hi" }: SudarshanaChakraWheelProps) {
  const [selectedHouse, setSelectedHouse] = useState<number>(data.current_scd.active_house || 1);
  const [activeRingFilter, setActiveRingFilter] = useState<"ALL" | "LK" | "CK" | "SK">("ALL");

  const size = 520;
  const center = size / 2;
  
  // Radii for 3 concentric rings + central hub
  const r0 = 68;  // Central Hub radius
  const r1 = 122; // Inner Ring: Surya Kundali
  const r2 = 182; // Middle Ring: Chandra Kundali
  const r3 = 246; // Outer Ring: Lagna Kundali

  const activeHouse = data.current_scd.active_house;

  // Group planets by house for LK, CK, SK
  const planetsByHouse = useMemo(() => {
    const lkMap: Record<number, GrahaAlignment[]> = {};
    const ckMap: Record<number, GrahaAlignment[]> = {};
    const skMap: Record<number, GrahaAlignment[]> = {};
    for (let h = 1; h <= 12; h++) {
      lkMap[h] = [];
      ckMap[h] = [];
      skMap[h] = [];
    }
    if (data.graha_alignments) {
      for (const g of data.graha_alignments) {
        if (g.house_from_lagna >= 1 && g.house_from_lagna <= 12) lkMap[g.house_from_lagna].push(g);
        if (g.house_from_moon >= 1 && g.house_from_moon <= 12) ckMap[g.house_from_moon].push(g);
        if (g.house_from_sun >= 1 && g.house_from_sun <= 12) skMap[g.house_from_sun].push(g);
      }
    }
    return { lk: lkMap, ck: ckMap, sk: skMap };
  }, [data.graha_alignments]);

  // Polar to Cartesian conversion helper
  const polarToCartesian = (cx: number, cy: number, radius: number, angleInDegrees: number) => {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
    return {
      x: cx + radius * Math.cos(angleInRadians),
      y: cy + radius * Math.sin(angleInRadians),
    };
  };

  // Helper to create an SVG arc slice path
  const describeArc = (
    cx: number,
    cy: number,
    innerRadius: number,
    outerRadius: number,
    startAngle: number,
    endAngle: number
  ) => {
    const startOuter = polarToCartesian(cx, cy, outerRadius, startAngle);
    const endOuter = polarToCartesian(cx, cy, outerRadius, endAngle);
    const startInner = polarToCartesian(cx, cy, innerRadius, endAngle);
    const endInner = polarToCartesian(cx, cy, innerRadius, startAngle);

    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";

    return [
      "M", startOuter.x, startOuter.y,
      "A", outerRadius, outerRadius, 0, largeArcFlag, 1, endOuter.x, endOuter.y,
      "L", startInner.x, startInner.y,
      "A", innerRadius, innerRadius, 0, largeArcFlag, 0, endInner.x, endInner.y,
      "Z"
    ].join(" ");
  };

  // 12 houses spread across 360 degrees (30 deg each)
  const houseAngles = useMemo(() => {
    return Array.from({ length: 12 }, (_, i) => {
      const h = i + 1;
      const start = (h - 1) * 30 - 15;
      const end = (h - 1) * 30 + 15;
      const mid = (h - 1) * 30;
      return { house: h, start, end, mid };
    });
  }, []);

  const selectedTheme = HOUSE_THEMES[selectedHouse] || HOUSE_THEMES[1];
  const selectedPlanetsLK = planetsByHouse.lk[selectedHouse] || [];
  const selectedPlanetsCK = planetsByHouse.ck[selectedHouse] || [];
  const selectedPlanetsSK = planetsByHouse.sk[selectedHouse] || [];

  return (
    <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 md:p-6 shadow-xl space-y-6 text-slate-900 dark:text-slate-100">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping" />
            <h3 className="text-base md:text-lg font-bold text-slate-900 dark:bg-gradient-to-r dark:from-amber-200 dark:via-amber-400 dark:to-cyan-300 dark:bg-clip-text dark:text-transparent">
              {lang === "hi" ? "सुदर्शन चक्र त्रि-लग्न व्हील (Sudarshana Chakra)" : "Sudarshana Chakra Tri-Lagna Interactive Wheel"}
            </h3>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium">
            {lang === "hi"
              ? "लग्न (Deha), चन्द्र (Mind), सूर्य (Soul) का समन्वित 3-रिंग चक्र + वार्षिक SCD दशा प्रोग्रेशन"
              : "Synchronized 3-Ring Tri-Fold Framework (Lagna, Moon, Sun) + Annual SCD Progression"}
          </p>
        </div>

        {/* Ring Filter Pill Selector */}
        <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-950 p-1 rounded-xl border border-slate-200 dark:border-slate-800 text-xs">
          <button
            onClick={() => setActiveRingFilter("ALL")}
            className={`px-3 py-1 rounded-lg font-semibold transition ${
              activeRingFilter === "ALL"
                ? "bg-amber-500 text-slate-950 shadow"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            {lang === "hi" ? "त्रि-लग्न (All)" : "Tri-Lagna"}
          </button>
          <button
            onClick={() => setActiveRingFilter("LK")}
            className={`px-2.5 py-1 rounded-lg font-semibold transition ${
              activeRingFilter === "LK"
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            LK ({data.lagna_rashi})
          </button>
          <button
            onClick={() => setActiveRingFilter("CK")}
            className={`px-2.5 py-1 rounded-lg font-semibold transition ${
              activeRingFilter === "CK"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            CK ({data.moon_rashi})
          </button>
          <button
            onClick={() => setActiveRingFilter("SK")}
            className={`px-2.5 py-1 rounded-lg font-semibold transition ${
              activeRingFilter === "SK"
                ? "bg-orange-500/20 text-orange-300 border border-orange-500/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            SK ({data.sun_rashi})
          </button>
        </div>
      </div>

      {/* Main Interactive Grid: SVG Wheel + Selected House Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Left / Center: SVG Chakra Wheel */}
        <div className="lg:col-span-7 flex flex-col items-center justify-center relative">
          <svg
            viewBox={`0 0 ${size} ${size}`}
            className="w-full max-w-[460px] h-auto select-none overflow-visible"
          >
            <defs>
              <radialGradient id="hubGradient" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#1e1b4b" />
                <stop offset="70%" stopColor="#0f172a" />
                <stop offset="100%" stopColor="#020617" />
              </radialGradient>
            </defs>

            {/* Background concentric boundary circles */}
            <circle cx={center} cy={center} r={r3} fill="#030712" stroke="#1e293b" strokeWidth="1.5" />
            <circle cx={center} cy={center} r={r2} fill="#020617" stroke="#1e293b" strokeWidth="1.5" />
            <circle cx={center} cy={center} r={r1} fill="#0b0f19" stroke="#1e293b" strokeWidth="1.5" />

            {/* 12 House Sectors rendering */}
            {houseAngles.map(({ house, start, end, mid }) => {
              const isSelected = selectedHouse === house;
              const isActiveScd = activeHouse === house;

              // Outer Ring (LK) Slice
              const lkPath = describeArc(center, center, r2, r3, start, end);
              // Middle Ring (CK) Slice
              const ckPath = describeArc(center, center, r1, r2, start, end);
              // Inner Ring (SK) Slice
              const skPath = describeArc(center, center, r0, r1, start, end);

              // Coordinates for labels
              const labelPosLK = polarToCartesian(center, center, (r2 + r3) / 2, mid);
              const labelPosCK = polarToCartesian(center, center, (r1 + r2) / 2, mid);
              const labelPosSK = polarToCartesian(center, center, (r0 + r1) / 2, mid);

              const lkPlanets = planetsByHouse.lk[house] || [];
              const ckPlanets = planetsByHouse.ck[house] || [];
              const skPlanets = planetsByHouse.sk[house] || [];

              return (
                <g key={house} className="cursor-pointer group" onClick={() => setSelectedHouse(house)}>
                  {/* Outer Ring: Lagna Kundali (LK) */}
                  <path
                    d={lkPath}
                    fill={
                      isActiveScd
                        ? "rgba(245, 158, 11, 0.22)"
                        : isSelected
                        ? "rgba(56, 189, 248, 0.18)"
                        : activeRingFilter === "LK" || activeRingFilter === "ALL"
                        ? "#0f172a"
                        : "#090d16"
                    }
                    stroke={
                      isActiveScd
                        ? "#f59e0b"
                        : isSelected
                        ? "#38bdf8"
                        : "#1e293b"
                    }
                    strokeWidth={isActiveScd || isSelected ? "2" : "1"}
                    className="transition-colors duration-200 group-hover:fill-slate-800/80"
                  />

                  {/* Middle Ring: Chandra Kundali (CK) */}
                  <path
                    d={ckPath}
                    fill={
                      isActiveScd
                        ? "rgba(245, 158, 11, 0.18)"
                        : isSelected
                        ? "rgba(56, 189, 248, 0.14)"
                        : activeRingFilter === "CK" || activeRingFilter === "ALL"
                        ? "#0b1120"
                        : "#070a12"
                    }
                    stroke={
                      isActiveScd
                        ? "#f59e0b"
                        : isSelected
                        ? "#38bdf8"
                        : "#1e293b"
                    }
                    strokeWidth={isActiveScd || isSelected ? "2" : "1"}
                    className="transition-colors duration-200 group-hover:fill-slate-800/80"
                  />

                  {/* Inner Ring: Surya Kundali (SK) */}
                  <path
                    d={skPath}
                    fill={
                      isActiveScd
                        ? "rgba(245, 158, 11, 0.14)"
                        : isSelected
                        ? "rgba(56, 189, 248, 0.1)"
                        : activeRingFilter === "SK" || activeRingFilter === "ALL"
                        ? "#090d18"
                        : "#05070d"
                    }
                    stroke={
                      isActiveScd
                        ? "#f59e0b"
                        : isSelected
                        ? "#38bdf8"
                        : "#1e293b"
                    }
                    strokeWidth={isActiveScd || isSelected ? "2" : "1"}
                    className="transition-colors duration-200 group-hover:fill-slate-800/80"
                  />

                  {/* House Number & Planet Glyphs in LK Ring */}
                  <text
                    x={labelPosLK.x}
                    y={labelPosLK.y - 6}
                    textAnchor="middle"
                    dominantBaseline="central"
                    className={`text-[10px] font-bold ${
                      isActiveScd ? "fill-amber-300 font-extrabold" : isSelected ? "fill-cyan-300" : "fill-slate-400"
                    }`}
                  >
                    H{house}
                  </text>
                  {lkPlanets.length > 0 && (
                    <text
                      x={labelPosLK.x}
                      y={labelPosLK.y + 8}
                      textAnchor="middle"
                      dominantBaseline="central"
                      className="text-[9px] font-bold fill-amber-200"
                    >
                      {lkPlanets.map((p) => PLANET_SYMBOLS[p.point_name]?.glyph || p.point_name.slice(0, 2)).join(" ")}
                    </text>
                  )}

                  {/* Planet Glyphs in CK Ring */}
                  <text
                    x={labelPosCK.x}
                    y={labelPosCK.y - 4}
                    textAnchor="middle"
                    dominantBaseline="central"
                    className={`text-[9px] font-medium ${
                      isActiveScd ? "fill-amber-300" : "fill-cyan-400/80"
                    }`}
                  >
                    {ckPlanets.length > 0
                      ? ckPlanets.map((p) => PLANET_SYMBOLS[p.point_name]?.glyph || p.point_name.slice(0, 2)).join(" ")
                      : `·`}
                  </text>

                  {/* Planet Glyphs in SK Ring */}
                  <text
                    x={labelPosSK.x}
                    y={labelPosSK.y}
                    textAnchor="middle"
                    dominantBaseline="central"
                    className={`text-[9px] font-medium ${
                      isActiveScd ? "fill-amber-300" : "fill-orange-400/80"
                    }`}
                  >
                    {skPlanets.length > 0
                      ? skPlanets.map((p) => PLANET_SYMBOLS[p.point_name]?.glyph || p.point_name.slice(0, 2)).join(" ")
                      : `·`}
                  </text>
                </g>
              );
            })}

            {/* Central Core Hub */}
            <circle
              cx={center}
              cy={center}
              r={r0}
              fill="url(#hubGradient)"
              stroke="#f59e0b"
              strokeWidth="2"
            />

            <g className="pointer-events-none select-none text-center">
              <text
                x={center}
                y={center - 26}
                textAnchor="middle"
                className="text-[8px] font-bold uppercase tracking-widest fill-amber-400"
              >
                SCD DASHA
              </text>
              <text
                x={center}
                y={center - 10}
                textAnchor="middle"
                className="text-[14px] font-black fill-amber-300"
              >
                House {data.current_scd.active_house}
              </text>
              <text
                x={center}
                y={center + 8}
                textAnchor="middle"
                className="text-[9px] font-semibold fill-slate-300"
              >
                Age {data.current_scd.age_years} yrs
              </text>
              <text
                x={center}
                y={center + 24}
                textAnchor="middle"
                className="text-[8px] font-medium fill-emerald-400"
              >
                Harmony: {data.tri_fold_harmony_score}
              </text>
            </g>
          </svg>

          {/* Ring Guide Legend below SVG */}
          <div className="flex items-center justify-center gap-4 mt-3 text-[10px] text-slate-400">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-800 border border-amber-400" />
              <span>Outer: Lagna (LK)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-800 border border-cyan-400" />
              <span>Mid: Chandra (CK)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-800 border border-orange-400" />
              <span>Inner: Surya (SK)</span>
            </div>
          </div>
        </div>

        {/* Right: Selected Bhava Deep-Dive Inspector */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-4 space-y-3 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-bold text-amber-700 dark:text-amber-400 tracking-wider block">
                  {lang === "hi" ? "भाव निरीक्षण (Bhava Inspector)" : "Bhava Deep Dive"}
                </span>
                <h4 className="text-sm md:text-base font-bold text-slate-900 dark:text-white mt-0.5">
                  House {selectedHouse} — {lang === "hi" ? selectedTheme.hi : selectedTheme.en}
                </h4>
              </div>
              {activeHouse === selectedHouse && (
                <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-500/40">
                  Active SCD
                </span>
              )}
            </div>

            <div className="flex flex-wrap gap-1.5 pt-1">
              {(lang === "hi" ? selectedTheme.sigsHi : selectedTheme.sigsEn).map((sig, idx) => (
                <span
                  key={idx}
                  className="text-[10px] font-medium px-2 py-0.5 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 rounded-md border border-slate-200 dark:border-slate-800"
                >
                  ✦ {sig}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-4 space-y-3 shadow-sm">
            <h5 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center justify-between">
              <span>{lang === "hi" ? "त्रि-लग्न स्थित ग्रह" : "Tri-Lagna Occupying Grahas"}</span>
              <span className="text-[10px] text-slate-500 font-mono">House {selectedHouse}</span>
            </h5>

            <div className="space-y-2 text-xs">
              <div className="p-2.5 rounded-lg bg-white dark:bg-slate-900/70 border border-slate-200 dark:border-slate-800/80 shadow-sm">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-amber-700 dark:text-amber-400 font-bold text-[11px]">1. From Lagna (Deha / Tangible)</span>
                  <span className="text-slate-500 dark:text-slate-400 text-[10px]">{data.lagna_rashi} Base</span>
                </div>
                {selectedPlanetsLK.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {selectedPlanetsLK.map((p) => (
                      <span
                        key={p.point_name}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-50 dark:bg-slate-950 border border-amber-300 dark:border-amber-500/30 text-amber-900 dark:text-amber-200 text-[10px] font-semibold"
                      >
                        <span>{PLANET_SYMBOLS[p.point_name]?.glyph}</span>
                        <span>{p.point_name}</span>
                        <span className="text-[9px] text-slate-500 dark:text-slate-400">({p.rashi})</span>
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-[10px] text-slate-400 italic">No direct grahas situated</span>
                )}
              </div>

              <div className="p-2.5 rounded-lg bg-white dark:bg-slate-900/70 border border-slate-200 dark:border-slate-800/80 shadow-sm">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-cyan-700 dark:text-cyan-400 font-bold text-[11px]">2. From Chandra (Mind / Emotion)</span>
                  <span className="text-slate-500 dark:text-slate-400 text-[10px]">{data.moon_rashi} Base</span>
                </div>
                {selectedPlanetsCK.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {selectedPlanetsCK.map((p) => (
                      <span
                        key={p.point_name}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-cyan-50 dark:bg-slate-950 border border-cyan-300 dark:border-cyan-500/30 text-cyan-900 dark:text-cyan-200 text-[10px] font-semibold"
                      >
                        <span>{PLANET_SYMBOLS[p.point_name]?.glyph}</span>
                        <span>{p.point_name}</span>
                        <span className="text-[9px] text-slate-500 dark:text-slate-400">({p.rashi})</span>
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-[10px] text-slate-400 italic">No direct grahas situated</span>
                )}
              </div>

              <div className="p-2.5 rounded-lg bg-white dark:bg-slate-900/70 border border-slate-200 dark:border-slate-800/80 shadow-sm">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-orange-700 dark:text-orange-400 font-bold text-[11px]">3. From Surya (Soul / Authority)</span>
                  <span className="text-slate-500 dark:text-slate-400 text-[10px]">{data.sun_rashi} Base</span>
                </div>
                {selectedPlanetsSK.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {selectedPlanetsSK.map((p) => (
                      <span
                        key={p.point_name}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-orange-50 dark:bg-slate-950 border border-orange-300 dark:border-orange-500/30 text-orange-900 dark:text-orange-200 text-[10px] font-semibold"
                      >
                        <span>{PLANET_SYMBOLS[p.point_name]?.glyph}</span>
                        <span>{p.point_name}</span>
                        <span className="text-[9px] text-slate-500 dark:text-slate-400">({p.rashi})</span>
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-[10px] text-slate-400 italic">No direct grahas situated</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
