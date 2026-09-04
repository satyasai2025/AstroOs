"use client";

import React, { useState, useMemo } from "react";

// --- Comprehensive Datasets ---

interface ProfessionItem {
  id: string;
  title: string;
  category: string;
  planets: string[];
  primaryCusps: string[];
  favorableHouses: string;
  detrimentalHouses: string;
  description: string;
  kpFormula: string;
}

interface DiseaseItem {
  id: string;
  name: string;
  category: string;
  planets: string[];
  primaryCusps: string[];
  affectedHouses: string;
  symptoms: string;
  kpFormula: string;
  remedy: string;
}

interface TermItem {
  term: string;
  category: string;
  definition: string;
  kpSignificance: string;
}

const PROFESSIONS: ProfessionItem[] = [
  {
    id: "med-surg",
    title: "Surgeon / Medical Specialist",
    category: "Healthcare & Medicine",
    planets: ["Mars", "Sun", "Jupiter", "Ketu"],
    primaryCusps: ["10th Cusp", "6th Cusp", "8th Cusp"],
    favorableHouses: "2, 6, 8, 10, 11",
    detrimentalHouses: "5, 12",
    description: "Involves surgery, emergency operations, and clinical diagnosis.",
    kpFormula: "10th or 6th CSL in star of Mars (Cuts/Instruments) and Ketu, strongly signifying House 8 (Surgery) + Houses 2, 6, 11 (Earning & Service).",
  },
  {
    id: "med-phys",
    title: "Physician / Pharmacist",
    category: "Healthcare & Medicine",
    planets: ["Sun", "Jupiter", "Mercury"],
    primaryCusps: ["10th Cusp", "6th Cusp"],
    favorableHouses: "2, 6, 10, 11",
    detrimentalHouses: "5, 8, 12",
    description: "General medicine, pharmaceuticals, biochemistry, and patient healing.",
    kpFormula: "10th CSL in star of Sun (Vitality) or Jupiter (Healing) connected to Mercury (Chemistry/Medicine) signifying 2, 6, 10, 11.",
  },
  {
    id: "it-soft",
    title: "Software Engineer / AI Developer",
    category: "Technology & Engineering",
    planets: ["Mercury", "Rahu", "Mars", "Saturn"],
    primaryCusps: ["10th Cusp", "3rd Cusp", "11th Cusp"],
    favorableHouses: "2, 3, 6, 10, 11",
    detrimentalHouses: "5, 8",
    description: "Software architecture, coding, algorithms, cloud computing, and AI.",
    kpFormula: "10th CSL in star of Mercury (Logic/Coding) or Rahu (Cloud/Electronics) linked with 3rd (Computers) and 11th (Tech networks).",
  },
  {
    id: "fin-ca",
    title: "Chartered Accountant / Investment Banker",
    category: "Finance & Banking",
    planets: ["Jupiter", "Mercury", "Venus"],
    primaryCusps: ["10th Cusp", "2nd Cusp", "11th Cusp"],
    favorableHouses: "2, 5, 6, 10, 11",
    detrimentalHouses: "8, 12",
    description: "Auditing, taxation, investment portfolio management, and corporate finance.",
    kpFormula: "10th CSL in star of Jupiter (Wealth) or Mercury (Calculations) strongly signifying House 2 (Accumulation) + House 11 (Gains).",
  },
  {
    id: "law-judge",
    title: "Judge / Senior Advocate / Legal Counsel",
    category: "Law & Judiciary",
    planets: ["Jupiter", "Saturn", "Mars", "Mercury"],
    primaryCusps: ["10th Cusp", "6th Cusp", "9th Cusp"],
    favorableHouses: "2, 6, 9, 10, 11",
    detrimentalHouses: "8, 12",
    description: "Judicial administration, corporate law, litigation, and constitutional debate.",
    kpFormula: "10th CSL in star of Jupiter (Justice) and Saturn (Discipline) linked to 6th (Disputes/Courts) and 9th (Law).",
  },
  {
    id: "govt-ias",
    title: "Civil Services / Diplomat (IAS / IPS / IFS)",
    category: "Government & Administration",
    planets: ["Sun", "Mars", "Jupiter"],
    primaryCusps: ["10th Cusp", "9th Cusp", "1st Cusp"],
    favorableHouses: "1, 6, 9, 10, 11",
    detrimentalHouses: "5, 8, 12",
    description: "Top administrative authority, public policy execution, and law enforcement.",
    kpFormula: "10th CSL in star of Sun (Government Authority) and Mars (Administration), signifying Houses 1, 6, 10, 11 with no sub-lord negation.",
  },
  {
    id: "real-estate",
    title: "Real Estate Developer / Builder",
    category: "Construction & Property",
    planets: ["Mars", "Saturn", "Venus"],
    primaryCusps: ["10th Cusp", "4th Cusp"],
    favorableHouses: "2, 4, 10, 11, 12",
    detrimentalHouses: "3, 6",
    description: "Infrastructure development, land acquisition, commercial construction.",
    kpFormula: "10th CSL in star of Mars (Land/Bhoomi) or Saturn (Structure) linked to 4th (Property) and 11th (Large profits).",
  },
  {
    id: "stock-trader",
    title: "Stock Market Trader / Speculator",
    category: "Trading & Speculation",
    planets: ["Mercury", "Rahu", "Venus", "Moon"],
    primaryCusps: ["10th Cusp", "5th Cusp", "11th Cusp"],
    favorableHouses: "2, 5, 11",
    detrimentalHouses: "6, 8, 12",
    description: "Equities, derivatives trading, commodity arbitrage, and algorithmic trading.",
    kpFormula: "10th CSL in star of Mercury or Rahu strongly signifying 5th (Speculation) and 11th (Fulfillment), backed by 2nd house.",
  },
];

const DISEASES: DiseaseItem[] = [
  {
    id: "cardio",
    name: "Cardiovascular & Hypertension",
    category: "Heart & Circulation",
    planets: ["Sun", "Mars"],
    primaryCusps: ["6th Cusp", "5th Cusp"],
    affectedHouses: "5, 6, 8, 12",
    symptoms: "High blood pressure, arterial blockages, arrhythmia, cardiac stress.",
    kpFormula: "6th CSL in star of Sun (Heart) in Leo or 5th house signifying 6th (Disease), 8th (Crisis), and 12th (Hospitalization).",
    remedy: "Surya Gayatri mantra, avoiding excessive salt/pitta foods, copper vessel water.",
  },
  {
    id: "diab",
    name: "Diabetes Mellitus & Pancreatic Issues",
    category: "Metabolism & Endocrine",
    planets: ["Venus", "Jupiter", "Moon"],
    primaryCusps: ["6th Cusp"],
    affectedHouses: "6, 8",
    symptoms: "Insulin resistance, high blood glucose, metabolic sluggishness.",
    kpFormula: "6th CSL in star of Venus (Sugar/Pancreas) or Jupiter (Liver metabolism) signifying 6, 8 in watery/earthy rashis.",
    remedy: "Regulating sugar intake, Pranayama, Moon/Venus calming practices.",
  },
];

const TERMS: TermItem[] = [
  {
    term: "Cuspal Sub-Lord (CSL)",
    category: "Core KP Concept",
    definition: "The ruler of the 249th subdivision of a house cusp longitude. It acts as the final decision maker for house fructification.",
    kpSignificance: "Decides IF an event promised by the house will actually happen.",
  },
  {
    term: "Star Lord (SL)",
    category: "Core KP Concept",
    definition: "The Nakshatra lord occupied by a planet or house cusp.",
    kpSignificance: "Determines WHAT results/houses a planet actually offers.",
  },
  {
    term: "Sub-Lord (SLD)",
    category: "Core KP Concept",
    definition: "The 249th subdivision ruler occupied by a planet.",
    kpSignificance: "Determines whether the results indicated by the Star Lord are Favorable or Unfavorable.",
  },
  {
    term: "Ruling Planets (RP)",
    category: "Time Gatekeeping",
    definition: "The 5 celestial rulers at the moment of query/birth: Day Lord, Moon Sign Lord, Moon Star Lord, Lagna Sign Lord, Lagna Star Lord.",
    kpSignificance: "Acts as the infallible cosmic verification filter for birth time rectification and prashna timing.",
  },
  {
    term: "Fruitful Cusps (2, 5, 11)",
    category: "KP Event Rules",
    definition: "Houses representing expansion, progeny, addition of family, and desire fulfillment.",
    kpSignificance: "Vital for child birth, marriage fruition, and Rule of Origin rectification.",
  },
];

const PLANET_KARAKAS: Record<string, string> = {
  Sun: "Soul, Vitality, Government, Father, Authority, Leadership, Gold.",
  Moon: "Mind, Mother, Emotions, Public Relations, Fluids, Travel, Creativity.",
  Mars: "Energy, Courage, Real Estate, Engineering, Surgery, Disputes, Brother.",
  Mercury: "Intelligence, Logic, Mathematics, Software, Communication, Business, Accounts.",
  Jupiter: "Wisdom, Finance, Higher Learning, Guru, Law, Children, Prosperity.",
  Venus: "Luxury, Arts, Marriage, Vehicles, Aesthetics, Banking, Romance.",
  Saturn: "Discipline, Labour, Hard Work, Longevity, Mines, Chronic Matters, Judiciary.",
  Rahu: "Innovation, Foreign Connections, AI, Cloud Technology, Unconventional Success, Speculation.",
  Ketu: "Spirituality, Occult, Research, Surgery, Precision Instruments, Liberation.",
};

const HOUSE_SIGNIFICATIONS: Record<number, string> = {
  1: "Self, Physical Appearance, Vitality, Natural Temperament, Longevity.",
  2: "Wealth Accumulation, Speech, Family Assets, Liquid Finance, Food.",
  3: "Courage, Short Travel, Communication, Siblings, IT Hardware/Software, Writing.",
  4: "Mother, Vehicles, Fixed Properties, Formal Education, Domestic Peace.",
  5: "Children, Intellect, Speculation, Creativity, Romance, Mantras.",
  6: "Service, Employment, Competition, Debts, Disease, Litigation, Victory.",
  7: "Spouse, Legal Partnership, Public Dealings, Foreign Trade, Open Opponents.",
  8: "Longevity, Sudden Unexpected Gains/Losses, Research, Surgery, Legacies.",
  9: "Father, Higher Philosophy, Guru, Long Distance Travel, Fortune, Law.",
  10: "Career, Public Stature, Profession, Leadership Karma, Government Honour.",
  11: "Fulfillment of Desires, Large Profits, Elder Siblings, Professional Network.",
  12: "Expenditure, Foreign Settlement, Hospitalization, Subconscious, Moksha.",
};

export function KPPredictiveAIToolkit() {
  const [activeTab, setActiveTab] = useState<"combi" | "prof" | "disease" | "terms">("combi");

  // Combination Finder State
  const [selectedPlanet, setSelectedPlanet] = useState<string>("Jupiter");
  const [selectedHouse, setSelectedHouse] = useState<number>(10);
  const [selectedSign, setSelectedSign] = useState<string>("Taurus");
  const [selectedNak, setSelectedNak] = useState<string>("Rohini (Moon)");

  // Search filters
  const [profSearch, setProfSearch] = useState<string>("");
  const [diseaseSearch, setDiseaseSearch] = useState<string>("");
  const [termSearch, setTermSearch] = useState<string>("");

  const filteredProfessions = useMemo(() => {
    return PROFESSIONS.filter(
      (p) =>
        p.title.toLowerCase().includes(profSearch.toLowerCase()) ||
        p.category.toLowerCase().includes(profSearch.toLowerCase()) ||
        p.description.toLowerCase().includes(profSearch.toLowerCase())
    );
  }, [profSearch]);

  const filteredDiseases = useMemo(() => {
    return DISEASES.filter(
      (d) =>
        d.name.toLowerCase().includes(diseaseSearch.toLowerCase()) ||
        d.category.toLowerCase().includes(diseaseSearch.toLowerCase()) ||
        d.symptoms.toLowerCase().includes(diseaseSearch.toLowerCase())
    );
  }, [diseaseSearch]);

  const filteredTerms = useMemo(() => {
    return TERMS.filter(
      (t) =>
        t.term.toLowerCase().includes(termSearch.toLowerCase()) ||
        t.definition.toLowerCase().includes(termSearch.toLowerCase()) ||
        t.category.toLowerCase().includes(termSearch.toLowerCase())
    );
  }, [termSearch]);

  return (
    <div className="w-full space-y-6 font-sans">
      {/* Top Banner & Header */}
      <div
        className="rounded-2xl border p-5 sm:p-6 shadow-xl backdrop-blur-sm"
        style={{
          borderColor: "var(--border-primary)",
          backgroundColor: "var(--bg-card)",
        }}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 text-xs font-bold uppercase tracking-wider mb-2">
              <span>✨ KP Predictive AI</span>
              <span>•</span>
              <span>Enterprise Rule Explorer</span>
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
              Predictive AI &amp; Combination Discovery Suite
            </h1>
            <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 font-medium mt-1 max-w-2xl">
              Cross-examine exact KP Cuspal Sub-Lord combinations, search career &amp; disease indicators, and evaluate planetary placements with classical precision.
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap gap-2 mt-5 pt-4 border-t" style={{ borderColor: "var(--border-primary)" }}>
          {[
            { id: "combi", label: "🔮 Combination Finder", badge: "Interactive" },
            { id: "prof", label: "💼 Profession Scanner", badge: "10th CSL" },
            { id: "disease", label: "🩺 Disease / Health Matrix", badge: "6th/8th CSL" },
            { id: "terms", label: "📖 KP Rules & Term Finder", badge: "Encyclopedia" },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === tab.id
                  ? "bg-cyan-100 text-cyan-900 border border-cyan-600/40 dark:bg-cyan-950/60 dark:text-cyan-300 shadow-sm"
                  : "border text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100"
              }`}
              style={{
                backgroundColor: activeTab === tab.id ? undefined : "var(--bg-secondary)",
                borderColor: activeTab === tab.id ? undefined : "var(--border-primary)",
              }}
            >
              <span>{tab.label}</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/40 text-slate-300 font-semibold">
                {tab.badge}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* --- TAB 1: COMBINATION FINDER --- */}
      {activeTab === "combi" && (
        <div className="space-y-6">
          {/* Query Bar */}
          <div
            className="rounded-2xl border p-5 shadow-md backdrop-blur-sm"
            style={{
              borderColor: "var(--border-primary)",
              backgroundColor: "var(--bg-card)",
            }}
          >
            <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-3">
              Configure 4-Tuple Combination
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5">Select Planet</label>
                <select
                  value={selectedPlanet}
                  onChange={(e) => setSelectedPlanet(e.target.value)}
                  className="w-full rounded-xl border px-3 py-2 text-xs font-semibold outline-none"
                  style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
                >
                  {Object.keys(PLANET_KARAKAS).map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5">Select House</label>
                <select
                  value={selectedHouse}
                  onChange={(e) => setSelectedHouse(Number(e.target.value))}
                  className="w-full rounded-xl border px-3 py-2 text-xs font-semibold outline-none"
                  style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((h) => (
                    <option key={h} value={h}>House {h}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5">Select Sign (Rashi)</label>
                <select
                  value={selectedSign}
                  onChange={(e) => setSelectedSign(e.target.value)}
                  className="w-full rounded-xl border px-3 py-2 text-xs font-semibold outline-none"
                  style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
                >
                  {[
                    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
                  ].map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-800 dark:text-slate-200 mb-1.5">Select Nakshatra</label>
                <select
                  value={selectedNak}
                  onChange={(e) => setSelectedNak(e.target.value)}
                  className="w-full rounded-xl border px-3 py-2 text-xs font-semibold outline-none"
                  style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
                >
                  {[
                    "Ashwini (Ketu)", "Bharani (Venus)", "Krittika (Sun)", "Rohini (Moon)",
                    "Mrigashira (Mars)", "Ardra (Rahu)", "Punarvasu (Jupiter)", "Pushya (Saturn)",
                    "Ashlesha (Mercury)", "Magha (Ketu)", "Purva Phalguni (Venus)", "Uttara Phalguni (Sun)",
                    "Hasta (Moon)", "Chitra (Mars)", "Swati (Rahu)", "Vishakha (Jupiter)",
                    "Anuradha (Saturn)", "Jyeshtha (Mercury)", "Mula (Ketu)", "Purva Ashadha (Venus)",
                    "Uttara Ashadha (Sun)", "Shravana (Moon)", "Dhanishta (Mars)", "Shatabhisha (Rahu)",
                    "Purva Bhadrapada (Jupiter)", "Uttara Bhadrapada (Saturn)", "Revati (Mercury)"
                  ].map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Quick Presets */}
            <div className="flex items-center gap-2 mt-4 pt-3 border-t text-xs" style={{ borderColor: "var(--border-primary)" }}>
              <span className="font-bold text-slate-800 dark:text-slate-200">Quick Presets:</span>
              {[
                { p: "Jupiter", h: 10, s: "Taurus", n: "Rohini (Moon)" },
                { p: "Mars", h: 6, s: "Capricorn", n: "Dhanishta (Mars)" },
                { p: "Sun", h: 10, s: "Aries", n: "Ashwini (Ketu)" },
                { p: "Mercury", h: 11, s: "Gemini", n: "Ardra (Rahu)" },
                { p: "Venus", h: 2, s: "Libra", n: "Chitra (Mars)" },
              ].map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setSelectedPlanet(preset.p);
                    setSelectedHouse(preset.h);
                    setSelectedSign(preset.s);
                    setSelectedNak(preset.n);
                  }}
                  className="px-2.5 py-1 rounded-lg border font-bold text-slate-800 dark:text-slate-200 hover:border-cyan-400 transition cursor-pointer"
                  style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}
                >
                  {preset.p} in {preset.h}th ({preset.s})
                </button>
              ))}
            </div>
          </div>

          {/* Results Display Card */}
          <div
            className="rounded-2xl border p-6 shadow-xl backdrop-blur-sm"
            style={{
              borderColor: "var(--border-primary)",
              backgroundColor: "var(--bg-card)",
            }}
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b pb-4 mb-5" style={{ borderColor: "var(--border-primary)" }}>
              <div>
                <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">
                  Synthesized Interpretation Result
                </span>
                <h3 className="text-xl font-extrabold text-slate-900 dark:text-slate-100 mt-0.5">
                  {selectedPlanet} in House {selectedHouse} · {selectedSign} ({selectedNak})
                </h3>
              </div>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-600/40 dark:bg-emerald-950/60 dark:text-emerald-300 text-xs font-bold shadow-xs">
                ✓ KP Verified Rule
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="p-4 rounded-xl border space-y-1" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <div className="text-[11px] font-bold text-cyan-400 uppercase">1. Planetary Karaka</div>
                <div className="text-xs text-slate-900 dark:text-slate-100 font-semibold">{PLANET_KARAKAS[selectedPlanet]}</div>
              </div>

              <div className="p-4 rounded-xl border space-y-1" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <div className="text-[11px] font-bold text-cyan-400 uppercase">2. House Governance</div>
                <div className="text-xs text-slate-900 dark:text-slate-100 font-semibold">{HOUSE_SIGNIFICATIONS[selectedHouse]}</div>
              </div>

              <div className="p-4 rounded-xl border space-y-1" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <div className="text-[11px] font-bold text-cyan-400 uppercase">3. Rashi Matrix ({selectedSign})</div>
                <div className="text-xs text-slate-900 dark:text-slate-100 font-semibold">
                  {selectedSign === "Taurus" || selectedSign === "Virgo" || selectedSign === "Capricorn"
                    ? "Earth Sign: Practical, material stability, wealth accumulation."
                    : selectedSign === "Aries" || selectedSign === "Leo" || selectedSign === "Sagittarius"
                    ? "Fire Sign: Executive power, dynamic initiative, leadership."
                    : selectedSign === "Gemini" || selectedSign === "Libra" || selectedSign === "Aquarius"
                    ? "Air Sign: Intellectual acumen, business strategy, networks."
                    : "Water Sign: Intuition, emotional intelligence, advisory depth."}
                </div>
              </div>

              <div className="p-4 rounded-xl border space-y-1" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <div className="text-[11px] font-bold text-cyan-400 uppercase">4. Star Lord Influence</div>
                <div className="text-xs text-slate-900 dark:text-slate-100 font-semibold">
                  Star channel: <strong className="text-cyan-400">{selectedNak.split(" ")[1] || selectedNak}</strong>. Dispatches planetary energy into the native's subconscious drives.
                </div>
              </div>
            </div>

            {/* Detailed KP Synthesis */}
            <div className="p-5 rounded-2xl border space-y-3 shadow-md" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
              <div className="text-xs font-bold text-amber-400 uppercase tracking-wider">
                🌟 KP Astrological Synthesis &amp; Real-World Prediction
              </div>
              <p className="text-xs sm:text-sm text-slate-900 dark:text-slate-100 leading-relaxed font-semibold m-0">
                When <strong>{selectedPlanet}</strong> occupies <strong>House {selectedHouse}</strong> in <strong>{selectedSign}</strong> in <strong>{selectedNak}</strong>, the native channels the expansive karakatwa of {selectedPlanet} into the active sphere of House {selectedHouse}. If the operating Dasha lord links with the Sub-Lord of this placement, the native experiences substantial breakthrough in material and professional objectives.
              </p>
              <div className="pt-2 flex items-center gap-4 text-xs font-bold text-slate-700 dark:text-slate-300">
                <span>Primary Favorable Links: <strong className="text-emerald-400">Houses 2, 6, 10, 11</strong></span>
                <span>•</span>
                <span>Fructification Trigger: <strong className="text-amber-400">Operating Dasha Lord Star Transit</strong></span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --- TAB 2: PROFESSION SCANNER --- */}
      {activeTab === "prof" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <input
              type="text"
              placeholder="Search profession (e.g. Doctor, Software, CA, Lawyer, Govt)..."
              value={profSearch}
              onChange={(e) => setProfSearch(e.target.value)}
              className="w-full sm:w-80 rounded-xl border px-3.5 py-2 text-xs font-semibold outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            />
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
              Showing <strong>{filteredProfessions.length}</strong> profession formulas
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredProfessions.map((prof) => (
              <div
                key={prof.id}
                className="rounded-2xl border p-5 space-y-3 transition-all backdrop-blur-sm shadow-md"
                style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-100 text-cyan-900 border border-cyan-600/40 dark:bg-cyan-950/60 dark:text-cyan-300 uppercase">
                      {prof.category}
                    </span>
                    <h4 className="text-base font-extrabold text-slate-900 dark:text-slate-100 mt-1">{prof.title}</h4>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-bold text-slate-700 dark:text-slate-300 block">Required Houses</span>
                    <span className="text-xs font-extrabold text-emerald-400">{prof.favorableHouses}</span>
                  </div>
                </div>

                <p className="text-xs font-medium text-slate-800 dark:text-slate-200 m-0">{prof.description}</p>

                <div className="p-3 rounded-xl border text-xs space-y-1.5" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                  <div className="text-slate-700 dark:text-slate-300 font-semibold">
                    Governing Planets: <strong className="text-cyan-400 font-bold">{prof.planets.join(", ")}</strong>
                  </div>
                  <div className="text-slate-900 dark:text-slate-100 font-semibold text-xs leading-relaxed">
                    <strong className="text-amber-400 font-bold">Formula:</strong> {prof.kpFormula}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* --- TAB 3: DISEASE / HEALTH MATRIX --- */}
      {activeTab === "disease" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <input
              type="text"
              placeholder="Search medical issue (e.g. Heart, Diabetes, Bone, Anxiety)..."
              value={diseaseSearch}
              onChange={(e) => setDiseaseSearch(e.target.value)}
              className="w-full sm:w-80 rounded-xl border px-3.5 py-2 text-xs font-semibold outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            />
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
              Showing <strong>{filteredDiseases.length}</strong> medical diagnostics
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredDiseases.map((d) => (
              <div
                key={d.id}
                className="rounded-2xl border p-5 space-y-3 transition-all backdrop-blur-sm shadow-md"
                style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-900 border border-rose-600/40 dark:bg-rose-950/60 dark:text-rose-300 uppercase">
                      {d.category}
                    </span>
                    <h4 className="text-base font-extrabold text-slate-900 dark:text-slate-100 mt-1">{d.name}</h4>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-bold text-slate-700 dark:text-slate-300 block">Vulnerability Cusp</span>
                    <span className="text-xs font-extrabold text-rose-400">{d.affectedHouses}</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl border text-xs space-y-1.5" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                  <div className="text-slate-700 dark:text-slate-300 font-semibold">
                    Afflicted Planets: <strong className="text-rose-400 font-bold">{d.planets.join(", ")}</strong>
                  </div>
                  <div className="text-slate-900 dark:text-slate-100 font-semibold text-xs leading-relaxed">
                    <strong className="text-amber-400 font-bold">KP Diagnosis:</strong> {d.kpFormula}
                  </div>
                  <div className="text-emerald-400 font-semibold text-xs pt-1">
                    <strong>Remedial Recommendation:</strong> {d.remedy}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* --- TAB 4: KP RULES & TERMS --- */}
      {activeTab === "terms" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <input
              type="text"
              placeholder="Search KP concept / terminology..."
              value={termSearch}
              onChange={(e) => setTermSearch(e.target.value)}
              className="w-full sm:w-80 rounded-xl border px-3.5 py-2 text-xs font-semibold outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            />
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
              Showing <strong>{filteredTerms.length}</strong> core principles
            </span>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {filteredTerms.map((t, idx) => (
              <div
                key={idx}
                className="rounded-2xl border p-4 space-y-1.5 shadow-md backdrop-blur-sm"
                style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}
              >
                <div className="flex items-center justify-between">
                  <h4 className="text-base font-extrabold text-slate-900 dark:text-slate-100 m-0">{t.term}</h4>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-100 text-cyan-900 border border-cyan-600/40 dark:bg-cyan-950/60 dark:text-cyan-300">
                    {t.category}
                  </span>
                </div>
                <p className="text-xs font-medium text-slate-800 dark:text-slate-200 m-0">{t.definition}</p>
                <div className="text-xs font-bold text-amber-400 pt-1">
                  <strong>KP Application:</strong> {t.kpSignificance}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
