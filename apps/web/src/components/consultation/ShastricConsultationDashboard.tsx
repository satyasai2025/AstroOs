"use client";

import React, { useState } from "react";
const Icon = ({ path, className }: { path: string; className?: string }) => (
  <svg className={className || "w-4 h-4"} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d={path} />
  </svg>
);

const Sparkles = ({ className }: { className?: string }) => <Icon path="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" className={className} />;
const Compass = ({ className }: { className?: string }) => <Icon path="m16.2 7.8-2 6.3-6.4 2 2-6.3z M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z" className={className} />;
const ShieldAlert = ({ className }: { className?: string }) => <Icon path="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z M12 8v4 M12 16h.01" className={className} />;
const ShieldCheck = ({ className }: { className?: string }) => <Icon path="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z m-3-10 2 2 4-4" className={className} />;
const Calendar = ({ className }: { className?: string }) => <Icon path="M8 2v4 M16 2v4 M3 10h18 M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" className={className} />;
const Layers = ({ className }: { className?: string }) => <Icon path="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.9a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z M2 12l10 4.5 10-4.5 M2 17l10 4.5 10-4.5" className={className} />;
const Globe = ({ className }: { className?: string }) => <Icon path="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M2 12h20 M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" className={className} />;
const ChevronRight = ({ className }: { className?: string }) => <Icon path="m9 18 6-6-6-6" className={className} />;
const TrendingUp = ({ className }: { className?: string }) => <Icon path="m22 7-8.5 8.5-5-5L2 17 M16 7h6v6" className={className} />;
const Award = ({ className }: { className?: string }) => <Icon path="m15.4 17.6 3.6 4.4-4-1-4 1 3.6-4.4 M12 15a7 7 0 1 0 0-14 7 7 0 0 0 0 14z" className={className} />;
const Zap = ({ className }: { className?: string }) => <Icon path="M13 2 3 14h9l-1 8 10-12h-9l1-8z" className={className} />;
const Info = ({ className }: { className?: string }) => <Icon path="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 16v-4 M12 8h.01" className={className} />;
const Clock = ({ className }: { className?: string }) => <Icon path="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 6v6l4 2" className={className} />;
const MapPin = ({ className }: { className?: string }) => <Icon path="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z M12 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4z" className={className} />;
const User = ({ className }: { className?: string }) => <Icon path="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2 M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" className={className} />;

interface DecisionWindow {
  window_start: string;
  window_end: string;
  mahadasha: string;
  antardasha: string;
  probability: number;
  decision_tier: "PRATYAKSHA_PHALA" | "SUSHUPTA_BEEJA" | "ALPA_PHALA" | "SAMANYA_KAL";
  confidence_level: string;
  verdict: string;
  explanation_hi: string;
  explanation_en: string;
  sav_10th_bindus: number;
  double_transit: boolean;
  amatyakaraka: string;
}

interface ConsultationData {
  status: string;
  native_name: string;
  domain: string;
  scan_horizon: string;
  timeline_summary: {
    total_windows_scanned: number;
    pratyaksha_events_count: number;
    latent_potential_count: number;
    transient_triggers_count: number;
  };
  bhrigu_bindu: {
    degree_absolute: number;
    rashi: string;
    rashi_degree: number;
    nakshatra: string;
    pada: number;
    house_from_lagna: number;
    transit_date: string;
    activation_status: string;
    destiny_impact_score: number;
    planets_conjunct: string[];
    planets_aspecting: string[];
  };
  sarvato_bhadra_chakra: {
    janma_nakshatra: string;
    overall_transit_shield: string;
    sbc_composite_score: number;
    nadi_afflictions: Record<
      string,
      {
        nakshatra: string;
        status: string;
        benefics: string[];
        malefics: string[];
      }
    >;
  };
  decision_timeline: DecisionWindow[];
}

const PRESET_CHARTS = [
  {
    name: "Narendra Modi",
    dob: "1950-09-17",
    time: "11:00",
    lat: 23.7833,
    lon: 72.6333,
    startYear: 2012,
    endYear: 2025,
    targetDate: "2014-05-16",
  },
  {
    name: "Indira Gandhi",
    dob: "1917-11-19",
    time: "23:11",
    lat: 25.45,
    lon: 81.85,
    startYear: 1965,
    endYear: 1985,
    targetDate: "1966-01-24",
  },
  {
    name: "Donald Trump",
    dob: "1946-06-14",
    time: "10:54",
    lat: 40.69,
    lon: -73.8,
    startYear: 2012,
    endYear: 2025,
    targetDate: "2016-11-08",
  },
  {
    name: "Amitabh Bachchan",
    dob: "1942-10-11",
    time: "16:00",
    lat: 25.45,
    lon: 81.85,
    startYear: 1970,
    endYear: 1990,
    targetDate: "1975-08-15",
  },
];

export function ShastricConsultationDashboard() {
  const [name, setName] = useState("Narendra Modi");
  const [dob, setDob] = useState("1950-09-17");
  const [tob, setTob] = useState("11:00");
  const [lat, setLat] = useState(23.7833);
  const [lon, setLon] = useState(72.6333);
  const [startYear, setStartYear] = useState(2012);
  const [endYear, setEndYear] = useState(2025);
  const [targetDate, setTargetDate] = useState("2014-05-16");
  const [domain, setDomain] = useState("career");
  const [lang, setLang] = useState<"hi" | "en">("hi");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ConsultationData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runConsultation = async () => {
    setLoading(true);
    setError(null);
    try {
      const birthIso = `${dob}T${tob}:00+00:00`;
      const res = await fetch("/api/v1/phalita/consultation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          birth_date_iso: birthIso,
          latitude: Number(lat),
          longitude: Number(lon),
          native_name: name,
          scan_start_year: Number(startYear),
          scan_end_year: Number(endYear),
          domain: domain,
          evaluation_target_date_iso: targetDate,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to generate consultation.");
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (p: (typeof PRESET_CHARTS)[0]) => {
    setName(p.name);
    setDob(p.dob);
    setTob(p.time);
    setLat(p.lat);
    setLon(p.lon);
    setStartYear(p.startYear);
    setEndYear(p.endYear);
    setTargetDate(p.targetDate);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-6 h-6 text-amber-400" />
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-amber-200 via-amber-400 to-orange-400 bg-clip-text text-transparent">
              AstroOS Shastric Consultation Engine
            </h1>
          </div>
          <p className="text-sm text-slate-400">
            Supervisory Self-Adaptive Governor + Bhrigu Bindu + 28-Nakshatra Sarvato-Bhadra Chakra
          </p>
        </div>

        {/* Language Toggle */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg p-1">
          <button
            onClick={() => setLang("hi")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition ${
              lang === "hi" ? "bg-amber-500 text-slate-950 shadow" : "text-slate-400 hover:text-white"
            }`}
          >
            🇮🇳 Hindi (हिन्दी)
          </button>
          <button
            onClick={() => setLang("en")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition ${
              lang === "en" ? "bg-amber-500 text-slate-950 shadow" : "text-slate-400 hover:text-white"
            }`}
          >
            🇬🇧 English
          </button>
        </div>
      </div>

      {/* Main Grid: Form + Results */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Input Form & Presets */}
        <div className="lg:col-span-4 space-y-6">
          {/* Preset Buttons */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Award className="w-4 h-4 text-amber-400" /> Celebrated Case Studies
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {PRESET_CHARTS.map((p) => (
                <button
                  key={p.name}
                  onClick={() => loadPreset(p)}
                  className={`px-3 py-2 text-xs font-medium rounded-lg border text-left transition ${
                    name === p.name
                      ? "bg-amber-500/10 border-amber-500/50 text-amber-300"
                      : "bg-slate-950/50 border-slate-800 text-slate-300 hover:border-slate-700"
                  }`}
                >
                  {p.name}
                </button>
              ))}
            </div>
          </div>

          {/* Form */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <User className="w-4 h-4 text-cyan-400" /> Native Parameters
            </h3>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Native Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Date of Birth</label>
                <input
                  type="date"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Time (UTC)</label>
                <input
                  type="time"
                  value={tob}
                  onChange={(e) => setTob(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={lat}
                  onChange={(e) => setLat(parseFloat(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={lon}
                  onChange={(e) => setLon(parseFloat(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="border-t border-slate-800 pt-3">
              <h4 className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-2">
                <Calendar className="w-3.5 h-3.5 text-amber-400" /> Life Scan Horizon
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Start Year</label>
                  <input
                    type="number"
                    value={startYear}
                    onChange={(e) => setStartYear(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">End Year</label>
                  <input
                    type="number"
                    value={endYear}
                    onChange={(e) => setEndYear(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Target Evaluation Date (Transit Trigger)</label>
              <input
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
              />
            </div>

            <button
              onClick={runConsultation}
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-slate-950 font-bold rounded-lg shadow-lg flex items-center justify-center gap-2 transition disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  Synthesizing Shastric Vectors...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 fill-slate-950" /> Run Consultation Scan
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Output Report */}
        <div className="lg:col-span-8 space-y-6">
          {error && (
            <div className="bg-rose-950/40 border border-rose-800 text-rose-300 p-4 rounded-xl flex items-center gap-3">
              <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!result && !loading && !error && (
            <div className="bg-slate-900/40 border border-slate-800 border-dashed rounded-xl p-12 text-center text-slate-500 space-y-3">
              <Compass className="w-12 h-12 text-slate-600 mx-auto animate-pulse" />
              <h3 className="text-base font-semibold text-slate-300">Ready to Scan Life Timeline</h3>
              <p className="text-xs max-w-md mx-auto">
                Select a celebrated case study or enter birth parameters on the left and click "Run Consultation Scan".
              </p>
            </div>
          )}

          {result && (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-emerald-950/20 border border-emerald-800/40 rounded-xl p-3">
                  <div className="text-xs text-emerald-400 font-semibold">Pratyaksha Phala</div>
                  <div className="text-2xl font-bold text-emerald-300">
                    {result.timeline_summary.pratyaksha_events_count}
                  </div>
                  <div className="text-[10px] text-slate-400">Landmark Events</div>
                </div>

                <div className="bg-blue-950/20 border border-blue-800/40 rounded-xl p-3">
                  <div className="text-xs text-blue-400 font-semibold">Sushupta Beeja</div>
                  <div className="text-2xl font-bold text-blue-300">
                    {result.timeline_summary.latent_potential_count}
                  </div>
                  <div className="text-[10px] text-slate-400">Latent Potential</div>
                </div>

                <div className="bg-amber-950/20 border border-amber-800/40 rounded-xl p-3">
                  <div className="text-xs text-amber-400 font-semibold">Alpa Phala</div>
                  <div className="text-2xl font-bold text-amber-300">
                    {result.timeline_summary.transient_triggers_count}
                  </div>
                  <div className="text-[10px] text-slate-400">Minor Triggers</div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-3">
                  <div className="text-xs text-slate-400 font-semibold">SBC Transit Shield</div>
                  <div className="text-sm font-bold text-cyan-300 mt-1">
                    {result.sarvato_bhadra_chakra.overall_transit_shield}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Score: {result.sarvato_bhadra_chakra.sbc_composite_score}
                  </div>
                </div>
              </div>

              {/* Bhrigu Bindu & SBC Panel */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Bhrigu Bindu */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                      <Sparkles className="w-4 h-4" /> Bhrigu Bindu (Destiny Trigger)
                    </h4>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        result.bhrigu_bindu.activation_status === "BENEFIC_TRIGGER"
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                          : result.bhrigu_bindu.activation_status === "MALEFIC_TRIGGER"
                          ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {result.bhrigu_bindu.activation_status}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-500">Sign & Degree</div>
                      <div className="font-semibold text-white">
                        {result.bhrigu_bindu.rashi} {result.bhrigu_bindu.rashi_degree}°
                      </div>
                    </div>
                    <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-500">Nakshatra</div>
                      <div className="font-semibold text-white">
                        {result.bhrigu_bindu.nakshatra} (P{result.bhrigu_bindu.pada})
                      </div>
                    </div>
                    <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-500">House</div>
                      <div className="font-semibold text-white">H{result.bhrigu_bindu.house_from_lagna}</div>
                    </div>
                  </div>

                  <div className="text-xs text-slate-400 space-y-1">
                    <div>
                      <span className="text-slate-500">Conjunct: </span>
                      {result.bhrigu_bindu.planets_conjunct?.length
                        ? result.bhrigu_bindu.planets_conjunct.join(", ")
                        : "None"}
                    </div>
                    <div>
                      <span className="text-slate-500">Aspecting: </span>
                      {result.bhrigu_bindu.planets_aspecting?.length
                        ? result.bhrigu_bindu.planets_aspecting.join(", ")
                        : "None"}
                    </div>
                  </div>
                </div>

                {/* Sarvato-Bhadra Chakra Nadi Vedhas */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
                      <Layers className="w-4 h-4" /> SBC Nadi Vedha Status
                    </h4>
                    <span className="text-[10px] text-slate-400">
                      Janma: {result.sarvato_bhadra_chakra.janma_nakshatra}
                    </span>
                  </div>

                  <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                    {Object.entries(result.sarvato_bhadra_chakra.nadi_afflictions).map(([key, val]) => (
                      <div
                        key={key}
                        className="flex items-center justify-between text-xs bg-slate-950 px-2.5 py-1.5 rounded-lg border border-slate-800/80"
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[10px] text-slate-400 font-bold">{key}</span>
                          <span className="text-slate-300 font-medium">{val.nakshatra}</span>
                        </div>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            val.status === "BENEFIC_AFFIRMATION"
                              ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800/60"
                              : val.status === "CRUEL_AFFLICTION"
                              ? "bg-rose-950/60 text-rose-300 border border-rose-800/60"
                              : "text-slate-500"
                          }`}
                        >
                          {val.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* 4-Tier Decision Timeline */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-400" /> Life Consultation Timeline ({result.scan_horizon})
                </h3>

                <div className="space-y-3">
                  {result.decision_timeline.map((win, idx) => {
                    const isPratyaksha = win.decision_tier === "PRATYAKSHA_PHALA";
                    const isSushupta = win.decision_tier === "SUSHUPTA_BEEJA";
                    const isAlpa = win.decision_tier === "ALPA_PHALA";

                    return (
                      <div
                        key={idx}
                        className={`p-4 rounded-xl border transition ${
                          isPratyaksha
                            ? "bg-emerald-950/20 border-emerald-800/60 shadow-lg shadow-emerald-950/20"
                            : isSushupta
                            ? "bg-blue-950/20 border-blue-800/50"
                            : isAlpa
                            ? "bg-amber-950/10 border-amber-800/30"
                            : "bg-slate-950/40 border-slate-800/80 text-slate-400"
                        }`}
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                                isPratyaksha
                                  ? "bg-emerald-500 text-slate-950 font-extrabold"
                                  : isSushupta
                                  ? "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                                  : isAlpa
                                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                                  : "bg-slate-800 text-slate-400"
                              }`}
                            >
                              {win.decision_tier}
                            </span>
                            <span className="font-mono text-sm font-bold text-white">
                              {win.mahadasha} - {win.antardasha}
                            </span>
                          </div>

                          <div className="flex items-center gap-3 text-xs text-slate-400">
                            <span>
                              {win.window_start} to {win.window_end}
                            </span>
                            <span className="font-semibold text-cyan-400">10H SAV: {win.sav_10th_bindus}</span>
                          </div>
                        </div>

                        {/* Explanation */}
                        <p className="text-xs text-slate-300 leading-relaxed mt-2">
                          {lang === "hi" ? win.explanation_hi : win.explanation_en}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
