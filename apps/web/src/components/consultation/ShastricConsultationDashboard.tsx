"use client";

import React, { useState, useEffect, useRef } from "react";
import { SudarshanaChakraWheel, SudarshanaData } from "./SudarshanaChakraWheel";
import { VargaBreakdownCard, VargaFusionData } from "./VargaBreakdownCard";
import { DecisionTimelineCard, DecisionTimelineWindow } from "./DecisionTimelineCard";
import { ConsultationErrorBoundary } from "./ErrorBoundary";
import { exportConsultationDossierPdf } from "./ConsultationPdfDossier";
import { ShastricHelpGuide } from "./ShastricHelpGuide";
import { PlainEnglishStoryView, ExecutiveLifeStoryData } from "./PlainEnglishStoryView";
import { ResearchWorkbenchTab } from "./ResearchWorkbenchTab";
import { LiveSkyTransitClock } from "./LiveSkyTransitClock";
import { ProfessionalArchetypeCard, ProfessionalArchetypesData } from "./ProfessionalArchetypeCard";
import { ShastricChatOracle } from "./ShastricChatOracle";
import { ChartInputModal, ChartFormData } from "./ChartInputModal";
import { SaptaNadiModal } from "./SaptaNadiModal";
import { useTheme } from "@/components/layout/ThemeProvider";
import { useWorkflowStore } from "@/lib/store";
import { api } from "@/lib/api";

const Icon = ({ path, className }: { path: string; className?: string }) => (
  <svg className={className || "w-4 h-4"} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d={path} />
  </svg>
);

const Sparkles = ({ className }: { className?: string }) => <Icon path="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" className={className} />;
const Compass = ({ className }: { className?: string }) => <Icon path="m16.2 7.8-2 6.3-6.4 2 2-6.3z M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z" className={className} />;
const ShieldAlert = ({ className }: { className?: string }) => <Icon path="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z M12 8v4 M12 16h.01" className={className} />;
const Calendar = ({ className }: { className?: string }) => <Icon path="M8 2v4 M16 2v4 M3 10h18 M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" className={className} />;
const Layers = ({ className }: { className?: string }) => <Icon path="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.9a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z M2 12l10 4.5 10-4.5 M2 17l10 4.5 10-4.5" className={className} />;
const Zap = ({ className }: { className?: string }) => <Icon path="M13 2 3 14h9l-1 8 10-12h-9l1-8z" className={className} />;
const SearchIcon = ({ className }: { className?: string }) => <Icon path="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" className={className} />;

export interface ChartProfile {
  id: string;
  name: string;
  dob: string;
  tob: string;
  cityName: string;
  latitude: number;
  longitude: number;
  tag?: string;
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
  varga_fusion?: VargaFusionData;
  sapta_nadi_chakra?: {
    dominant_nadi: string;
    cyclone_risk_score: number;
    flood_risk_score: number;
    weather_summary: string;
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
  arudha_padas?: {
    AL: { house: number; rashi: string; name: string };
    UL: { house: number; rashi: string; name: string };
    A10: { house: number; rashi: string; name: string };
    all_padas: Record<string, { house: number; rashi: string }>;
  };
  triple_dasha_confluence?: {
    confluence_level: string;
    confluence_score: number;
    is_infallible_landmark: boolean;
    vimshottari_md: string;
    vimshottari_ad: string;
    scd_active_house: number;
    chara_dasha_rashi: string;
    synthesis_hi: string;
    synthesis_en: string;
  };
  executive_story?: ExecutiveLifeStoryData;
  professional_archetypes?: ProfessionalArchetypesData;
  sudarshana_chakra?: SudarshanaData;
  decision_timeline: DecisionTimelineWindow[];
}

export function ShastricConsultationDashboard() {
  const { theme, toggle: toggleTheme } = useTheme();

  // Active Profile State (Universal Active Chart)
  const [name, setName] = useState("");
  const [dob, setDob] = useState("");
  const [tob, setTob] = useState("12:00");
  const [lat, setLat] = useState(0);
  const [lon, setLon] = useState(0);
  const [citySearchText, setCitySearchText] = useState("");

  // Consultation Parameters State (Max 3-Year Precision Window)
  const currentYear = new Date().getFullYear();
  const [startYear, setStartYear] = useState(currentYear);
  const [endYear, setEndYear] = useState(currentYear + 2);
  const [targetDate, setTargetDate] = useState(new Date().toISOString().slice(0, 10));
  const [domain, setDomain] = useState("career");
  const [lang, setLang] = useState<"hi" | "en">("en");

  // View & UI State
  const [activeViewTab, setActiveViewTab] = useState<
    "story" | "timeline" | "archetypes" | "oracle" | "research" | "livesky" | "sudarshana" | "varga" | "triggers" | "guide" | "all"
  >("story");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ConsultationData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savedVaultProfiles, setSavedVaultProfiles] = useState<ChartProfile[]>([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Search & Modal State
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isNadiModalOpen, setIsNadiModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const searchContainerRef = useRef<HTMLDivElement>(null);

  const storeRequest = useWorkflowStore((s) => s.request);
  const storeResult = useWorkflowStore((s) => s.result);

  useEffect(() => {
    if (storeRequest) {
      const dtStr = storeRequest.birth_datetime_utc || "";
      if (dtStr) {
        setDob(dtStr.slice(0, 10));
        setTob(dtStr.slice(11, 16) || "12:00");
      }
      if (typeof storeRequest.latitude === "number") setLat(storeRequest.latitude);
      if (typeof storeRequest.longitude === "number") setLon(storeRequest.longitude);
      setName("Active Native");
    }
  }, [storeRequest]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("astroos_saved_charts");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setSavedVaultProfiles(parsed);
        }
      }
    } catch {
      // ignore
    }
  }, []);

  // Handle outside click to close search dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setIsSearchOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelectProfile = (p: ChartProfile) => {
    setName(p.name);
    setDob(p.dob);
    setTob(p.tob || "12:00");
    setLat(Number(p.latitude) || 0);
    setLon(Number(p.longitude) || 0);
    setCitySearchText(p.cityName || "Custom Location");

    const birthYear = parseInt(p.dob.slice(0, 4)) || 1990;
    setStartYear(Math.max(1900, birthYear + 15));
    setEndYear(Math.min(2100, birthYear + 35));

    setIsSearchOpen(false);
    setSearchQuery("");
  };

  const handleModalSubmit = (data: ChartFormData) => {
    setName(data.name);
    setDob(data.dob);
    setTob(data.tob);
    setLat(data.lat);
    setLon(data.lon);
    setCitySearchText(data.citySearchText);

    const birthYear = parseInt(data.dob.slice(0, 4)) || 1990;
    setStartYear(Math.max(1900, birthYear + 15));
    setEndYear(Math.min(2100, birthYear + 35));

    if (data.saveToVault) {
      const newProfile: ChartProfile = {
        id: "chart-" + Date.now(),
        name: data.name,
        dob: data.dob,
        tob: data.tob,
        cityName: data.citySearchText,
        latitude: data.lat,
        longitude: data.lon,
        tag: "Saved Vault",
      };
      const updated = [newProfile, ...savedVaultProfiles.filter((p) => p.name !== data.name)];
      setSavedVaultProfiles(updated);
      try {
        localStorage.setItem("astroos_saved_charts", JSON.stringify(updated));
      } catch {
        // ignore
      }
    }
  };

  const runConsultation = async () => {
    setLoading(true);
    setError(null);
    try {
      if (lat < -90 || lat > 90) {
        throw new Error("Latitude must be between -90.0 and +90.0 degrees.");
      }
      if (lon < -180 || lon > 180) {
        throw new Error("Longitude must be between -180.0 and +180.0 degrees.");
      }
      if (endYear < startYear) {
        throw new Error("Scan End Year must be greater than or equal to Start Year.");
      }
      if (!dob) {
        throw new Error("Date of Birth is required.");
      }

      // Determine timezone offset string (e.g. +05:30 for India)
      let tzOffset = "+05:30";
      if (lon < -30 && lon > -150) {
        tzOffset = "-05:00";
      } else if (lon >= -30 && lon <= 45) {
        tzOffset = "+01:00";
      } else if (lon > 45 && lon <= 95) {
        tzOffset = "+05:30";
      } else if (lon > 95 && lon <= 130) {
        tzOffset = "+08:00";
      }

      const birthIso = `${dob}T${tob || "12:00"}:00${tzOffset}`;
      const data = await api.post<ConsultationData>("/api/v1/phalita/consultation", {
        birth_date_iso: birthIso,
        latitude: Number(lat),
        longitude: Number(lon),
        native_name: name.trim() || "Native Profile",
        scan_start_year: Number(startYear),
        scan_end_year: Number(endYear),
        domain: domain,
        evaluation_target_date_iso: targetDate || undefined,
      });

      setResult(data);
      setActiveViewTab("story");
    } catch (err: any) {
      setError(err.message || "Failed to generate consultation.");
    } finally {
      setLoading(false);
    }
  };

  // User's authentic saved profiles
  const allProfiles = savedVaultProfiles.map((p) => ({ ...p, tag: p.tag || "Saved Vault" }));

  const filteredProfiles = allProfiles.filter((p) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      p.name.toLowerCase().includes(q) ||
      (p.cityName && p.cityName.toLowerCase().includes(q)) ||
      (p.tag && p.tag.toLowerCase().includes(q))
    );
  });

  return (
    <div className="min-h-screen transition-colors duration-200 p-4 md:p-8 bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* Chart Input Popup Modal */}
      <ChartInputModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleModalSubmit}
        initialData={{
          name: modalMode === "edit" ? name : "",
          dob: modalMode === "edit" ? dob : "",
          tob: modalMode === "edit" ? tob : "12:00",
          citySearchText: modalMode === "edit" ? citySearchText : "",
          lat: modalMode === "edit" ? lat : 0,
          lon: modalMode === "edit" ? lon : 0,
        }}
        theme={theme}
        title={modalMode === "edit" ? "Edit Native Parameters" : "Create New Chart Profile"}
      />

      {/* Sapta Nadi Deep Knowledge Modal */}
      <SaptaNadiModal
        isOpen={isNadiModalOpen}
        onClose={() => setIsNadiModalOpen(false)}
        dominantNadi={result?.sapta_nadi_chakra?.dominant_nadi || "Vata"}
        lang={lang}
      />

      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b pb-4 border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-6 h-6 text-amber-500" />
            <h1 className="text-2xl md:text-3xl font-black text-slate-900 dark:bg-gradient-to-r dark:from-amber-200 dark:via-amber-400 dark:to-orange-400 dark:bg-clip-text dark:text-transparent">
              AstroOS Shastric Consultation Engine
            </h1>
          </div>
          <p className="text-xs md:text-sm text-slate-600 dark:text-slate-400 font-medium">
            Supervisory 4-Tier Governor • Sudarshana Chakra Tri-Lagna Wheel • Varga Fusion • 28-SBC Vedhas
          </p>
        </div>

        {/* Actions & Theme Toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className="px-3.5 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-sm border bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-amber-700 dark:text-amber-300 hover:bg-amber-50 dark:hover:bg-slate-800"
            title="Toggle Light / Dark Theme"
          >
            <span>{theme === "light" ? "☀️ Light Mode" : "🌙 Dark Mode"}</span>
          </button>

          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="px-3 py-2 border rounded-xl text-xs font-semibold transition flex items-center gap-1.5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 shadow-sm"
            title={isSidebarCollapsed ? "Show Input Controls" : "Expand Results Fullscreen"}
          >
            <span>{isSidebarCollapsed ? "⇲" : "⇱"}</span>
            <span className="hidden sm:inline">
              {isSidebarCollapsed ? "Show Controls" : "Full Width"}
            </span>
          </button>

          {result && (
            <button
              onClick={() => exportConsultationDossierPdf(result, lang)}
              className="px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-slate-950 font-black rounded-xl text-xs shadow-lg flex items-center gap-1.5 transition transform hover:scale-[1.02]"
            >
              <span>📄</span>
              <span>Download PDF Dossier</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: Left Controls & Right Visualizations */}
      <div className="max-w-[1600px] mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Fast Search, Active Profile & Scan Scope */}
        {!isSidebarCollapsed && (
          <div className="lg:col-span-4 space-y-4">
            {/* 1. Fast Profile Search & "+ New Chart" Bar */}
            <div
              ref={searchContainerRef}
              className="border rounded-2xl p-4 shadow-sm space-y-3 relative bg-white dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100"
            >
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 text-amber-600 dark:text-amber-500">
                  <SearchIcon className="w-3.5 h-3.5" /> Search / Switch Chart
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setModalMode("create");
                    setIsModalOpen(true);
                  }}
                  className="px-2.5 py-1 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-slate-950 text-xs font-bold rounded-lg shadow transition transform hover:scale-105 flex items-center gap-1"
                >
                  <span>+</span>
                  <span>New Chart</span>
                </button>
              </div>

              {/* Search input with live dropdown */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search saved client/native profile..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setIsSearchOpen(true);
                  }}
                  onFocus={() => setIsSearchOpen(true)}
                  className="w-full border rounded-xl px-3 py-2 text-xs focus:border-amber-500 focus:outline-none transition bg-slate-50 dark:bg-slate-950 border-slate-300 dark:border-slate-800 text-slate-900 dark:text-white"
                />

                {isSearchOpen && (
                  <div
                    className="absolute left-0 right-0 z-30 mt-1 max-h-60 overflow-y-auto rounded-xl border shadow-2xl bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
                  >
                    {filteredProfiles.length > 0 ? (
                      <div className="p-1 space-y-1">
                        {filteredProfiles.map((p) => (
                          <button
                            key={p.id}
                            type="button"
                            onClick={() => handleSelectProfile(p)}
                            className={`w-full px-3 py-2 text-left rounded-lg text-xs flex items-center justify-between transition ${
                              name === p.name
                                ? "bg-amber-50 dark:bg-amber-500/20 text-amber-900 dark:text-amber-200 font-bold"
                                : "hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200"
                            }`}
                          >
                            <div className="truncate pr-2">
                              <span className="font-semibold">{p.name}</span>
                              <span className="text-[10px] text-slate-500 block truncate">
                                {p.dob} • {p.cityName}
                              </span>
                            </div>
                            <span className="text-[9px] px-1.5 py-0.5 rounded font-bold whitespace-nowrap bg-cyan-100 dark:bg-cyan-500/15 text-cyan-800 dark:text-cyan-400">
                              📂 Vault
                            </span>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="p-4 text-center text-xs text-slate-500">
                        No saved profiles. Click <strong>+ New Chart</strong> to create one.
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* 2. Active Native Profile Summary Card */}
            <div
              className="border rounded-2xl p-4 shadow-sm space-y-2.5 transition bg-gradient-to-br from-amber-50/80 via-white to-white dark:from-slate-900 dark:via-slate-900 dark:to-slate-950 border-amber-200 dark:border-amber-500/30 text-slate-900 dark:text-white"
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                  <span>👤</span> Active Native Profile
                </span>
                <button
                  type="button"
                  onClick={() => {
                    setModalMode(name ? "edit" : "create");
                    setIsModalOpen(true);
                  }}
                  className="text-xs font-bold text-cyan-700 dark:text-cyan-400 hover:underline flex items-center gap-1 cursor-pointer"
                  title="Set birth parameters in popup modal"
                >
                  <span>✏️</span> {name ? "Edit" : "Set Chart"}
                </button>
              </div>

              {name ? (
                <div>
                  <h3 className="text-base font-black truncate text-slate-900 dark:text-white">{name}</h3>
                  <div className="text-xs text-slate-600 dark:text-slate-300 flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-0.5 font-medium">
                    <span>📅 {dob}</span>
                    <span>⏰ {tob}</span>
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5 flex items-center gap-1 font-medium">
                    <span>📍</span>
                    <span className="truncate">{citySearchText || "Custom Location"}</span>
                  </div>
                </div>
              ) : (
                <div className="py-2 text-xs text-slate-500 dark:text-slate-400">
                  <span>No chart loaded. Click </span>
                  <button
                    onClick={() => {
                      setModalMode("create");
                      setIsModalOpen(true);
                    }}
                    className="font-bold text-amber-600 dark:text-amber-400 underline cursor-pointer"
                  >
                    + Set Chart Details
                  </button>
                  <span> to begin.</span>
                </div>
              )}
            </div>

            {/* 3. Consultation Scan Controls */}
            <div
              className="border rounded-2xl p-5 shadow-xl space-y-4 bg-white dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100"
            >
              <div>
                <label className="block text-xs mb-1 font-semibold text-slate-700 dark:text-slate-300">
                  Consultation Domain
                </label>
                <select
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:border-amber-500 focus:outline-none bg-slate-50 dark:bg-slate-950 border-slate-300 dark:border-slate-800 text-slate-900 dark:text-slate-200 font-medium"
                >
                  <option value="career">Career & Authority (10th House / D10)</option>
                  <option value="wealth">Wealth & Property (2nd & 11th Houses / D4)</option>
                  <option value="marriage">Marriage & Relationships (7th House / D9)</option>
                  <option value="health">Vitality & Health (1st & 6th Houses / D6)</option>
                </select>
              </div>

              <div className="border-t pt-3 border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-xs font-semibold flex items-center gap-1.5 text-slate-800 dark:text-slate-300">
                    <Calendar className="w-3.5 h-3.5 text-amber-500" /> Focus Horizon (Max 3 Years)
                  </h4>
                  <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10 px-1.5 py-0.5 rounded">
                    {Math.max(1, (endYear || startYear) - (startYear || currentYear) + 1)} Year Focus
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs mb-1 font-semibold text-slate-700 dark:text-slate-300">Start Year</label>
                    <input
                      type="number"
                      placeholder="e.g. 2026"
                      value={isNaN(startYear) || startYear === 0 ? "" : startYear}
                      onChange={(e) => {
                        const val = e.target.value;
                        const s = val === "" ? (0 as any) : parseInt(val) || 0;
                        setStartYear(s);
                        if (s > 0 && endYear > 0 && endYear > s + 2) {
                          setEndYear(s + 2);
                        }
                      }}
                      className="w-full border rounded-lg px-3 py-2 text-sm focus:border-amber-500 focus:outline-none bg-slate-50 dark:bg-slate-950 border-slate-300 dark:border-slate-800 text-slate-900 dark:text-white font-medium"
                    />
                  </div>
                  <div>
                    <label className="block text-xs mb-1 font-semibold text-slate-700 dark:text-slate-300">End Year (Max +2)</label>
                    <input
                      type="number"
                      placeholder="e.g. 2028"
                      value={isNaN(endYear) || endYear === 0 ? "" : endYear}
                      onChange={(e) => {
                        const val = e.target.value;
                        const parsed = val === "" ? (0 as any) : parseInt(val) || 0;
                        if (startYear > 0 && parsed > startYear + 2) {
                          setEndYear(startYear + 2);
                        } else {
                          setEndYear(parsed);
                        }
                      }}
                      className="w-full border rounded-lg px-3 py-2 text-sm focus:border-amber-500 focus:outline-none bg-slate-50 dark:bg-slate-950 border-slate-300 dark:border-slate-800 text-slate-900 dark:text-white font-medium"
                    />
                  </div>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1.5 leading-tight">
                  🎯 Scanning max 3 consecutive years keeps onscreen data concise and avoids clutter.
                </p>
              </div>

              <div>
                <label className="block text-xs mb-1 font-semibold text-slate-700 dark:text-slate-300">
                  Target Evaluation Date (Transit & SBC Trigger)
                </label>
                <input
                  type="date"
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:border-amber-500 focus:outline-none bg-slate-50 dark:bg-slate-950 border-slate-300 dark:border-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <button
                onClick={runConsultation}
                disabled={loading}
                className="w-full py-3.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-slate-950 font-black rounded-xl shadow-lg flex items-center justify-center gap-2 transition disabled:opacity-50 transform hover:scale-[1.01]"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    <span>Synthesizing Shastric Engine...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 fill-slate-950" />
                    <span>Run Complete Consultation Scan</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Right Column: Output Dashboards & Visualizations */}
        <div className={`${isSidebarCollapsed ? "lg:col-span-12" : "lg:col-span-8"} space-y-6`}>
          {error && (
            <div className="bg-rose-50 dark:bg-rose-950/40 border border-rose-300 dark:border-rose-800 text-rose-800 dark:text-rose-300 p-4 rounded-2xl flex items-center gap-3">
              <ShieldAlert className="w-5 h-5 text-rose-500 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Standalone tabs accessible before running consultation */}
          {activeViewTab === "research" && (
            <ConsultationErrorBoundary fallbackTitle="Research Workbench Error">
              <ResearchWorkbenchTab />
            </ConsultationErrorBoundary>
          )}

          {activeViewTab === "guide" && (
            <ConsultationErrorBoundary fallbackTitle="Help Guide Error">
              <ShastricHelpGuide lang={lang} />
            </ConsultationErrorBoundary>
          )}

          {/* Clean Ready State */}
          {!result && !loading && !error && activeViewTab !== "research" && activeViewTab !== "guide" && (
            <div
              className="border border-dashed rounded-2xl p-12 text-center space-y-4 bg-white dark:bg-slate-900/40 border-slate-300 dark:border-slate-800 text-slate-600 dark:text-slate-400 shadow-sm"
            >
              <Compass className="w-12 h-12 text-amber-500 mx-auto animate-pulse" />
              <div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-200">
                  Ready for Shastric Life Scan
                </h3>
                <p className="text-xs max-w-md mx-auto mt-1 leading-relaxed text-slate-600 dark:text-slate-400">
                  Active Profile: <strong className="text-slate-900 dark:text-amber-400">{name}</strong> ({dob} • {citySearchText || "Custom Location"})
                </p>
              </div>
              <div className="pt-2 flex flex-wrap items-center justify-center gap-3">
                <button
                  type="button"
                  onClick={runConsultation}
                  disabled={loading}
                  className="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-slate-950 font-black rounded-xl text-xs shadow-lg transition flex items-center gap-1.5"
                >
                  <Zap className="w-4 h-4 fill-slate-950" />
                  <span>Run Scan for {name}</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setModalMode("create");
                    setIsModalOpen(true);
                  }}
                  className="px-4 py-2.5 rounded-xl text-xs font-bold border transition bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 shadow-sm"
                >
                  <span>+ Create Different Chart</span>
                </button>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-6">
              {/* Top Summary Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-emerald-50 dark:bg-emerald-950/25 border border-emerald-200 dark:border-emerald-800/50 rounded-2xl p-3.5 shadow-sm">
                  <div className="text-xs text-emerald-800 dark:text-emerald-400 font-bold">Pratyaksha Phala</div>
                  <div className="text-2xl font-black text-emerald-700 dark:text-emerald-300 mt-0.5">
                    {result.timeline_summary.pratyaksha_events_count}
                  </div>
                  <div className="text-[10px] text-emerald-700 dark:text-slate-400 font-medium">Landmark Manifestations</div>
                </div>

                <div className="bg-blue-50 dark:bg-blue-950/25 border border-blue-200 dark:border-blue-800/50 rounded-2xl p-3.5 shadow-sm">
                  <div className="text-xs text-blue-800 dark:text-blue-400 font-bold">Sushupta Beeja</div>
                  <div className="text-2xl font-black text-blue-700 dark:text-blue-300 mt-0.5">
                    {result.timeline_summary.latent_potential_count}
                  </div>
                  <div className="text-[10px] text-blue-700 dark:text-slate-400 font-medium">Latent Potential Windows</div>
                </div>

                <div className="bg-amber-50 dark:bg-amber-950/25 border border-amber-200 dark:border-amber-800/50 rounded-2xl p-3.5 shadow-sm">
                  <div className="text-xs text-amber-800 dark:text-amber-400 font-bold">Alpa Phala</div>
                  <div className="text-2xl font-black text-amber-700 dark:text-amber-300 mt-0.5">
                    {result.timeline_summary.transient_triggers_count}
                  </div>
                  <div className="text-[10px] text-amber-700 dark:text-slate-400 font-medium">Minor Transient Triggers</div>
                </div>

                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-3.5 shadow-sm">
                  <div className="text-xs text-slate-600 dark:text-slate-400 font-bold">SBC Transit Shield</div>
                  <div className="text-sm font-black text-cyan-700 dark:text-cyan-300 mt-1">
                    {result.sarvato_bhadra_chakra.overall_transit_shield}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    SBC Score: {result.sarvato_bhadra_chakra.sbc_composite_score}
                  </div>
                </div>
              </div>

              {/* Triple-Dasha Confluence Synthesis Card */}
              {result.triple_dasha_confluence && (
                <div className="bg-gradient-to-r from-purple-50 via-amber-50 to-white dark:from-purple-950/40 dark:via-amber-950/25 dark:to-slate-950 border border-purple-200 dark:border-purple-800/50 rounded-2xl p-4 shadow-md space-y-2">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">🌟</span>
                      <h3 className="text-sm font-bold text-purple-900 dark:bg-gradient-to-r dark:from-amber-300 dark:to-purple-300 dark:bg-clip-text dark:text-transparent">
                        Triple-Dasha Confluence (Triveni Sangam)
                      </h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-purple-900 dark:text-purple-300 bg-purple-100 dark:bg-purple-950 px-2 py-0.5 rounded-lg border border-purple-300 dark:border-purple-800">
                        Jaimini: {result.triple_dasha_confluence.chara_dasha_rashi}
                      </span>
                      <span className="text-xs font-black px-2.5 py-0.5 rounded-lg bg-amber-400 text-slate-950 shadow-sm">
                        {result.triple_dasha_confluence.confluence_level === "TRIPLE_CONFLUENCE"
                          ? "100% Infallible"
                          : result.triple_dasha_confluence.confluence_level}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                    {result.triple_dasha_confluence.synthesis_en || result.triple_dasha_confluence.synthesis_hi}
                  </p>
                </div>
              )}

              {/* Sapta-Nadi Weather & Energy Banner */}
              {result.sapta_nadi_chakra && (
                <div className="bg-gradient-to-r from-cyan-500/10 via-white to-cyan-500/5 dark:from-cyan-950/40 dark:via-slate-900/80 dark:to-cyan-950/20 border border-cyan-200 dark:border-cyan-800/60 rounded-2xl p-3 px-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs shadow-sm">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl">🌊</span>
                    <div>
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {lang === "hi" ? "सप्त-नाड़ी प्रवाह (Sapta-Nadi):" : "Sapta-Nadi Celestial Channel:"}{" "}
                        <strong className="text-cyan-700 dark:text-cyan-300 font-bold">
                          {result.sapta_nadi_chakra.dominant_nadi} Nadi
                        </strong>
                      </span>
                      <span className="hidden md:inline ml-2 text-slate-500 dark:text-slate-400 text-[11px]">
                        {lang === "hi"
                          ? "(व्यक्तिगत जैविक, मानसिक व स्वास्थ्य ऊर्जा)"
                          : "(Personal Biological, Mental & Energy Dynamics)"}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsNadiModalOpen(true)}
                    className="px-3.5 py-1.5 bg-cyan-600 hover:bg-cyan-700 text-white font-bold rounded-xl text-xs transition shadow-sm flex items-center gap-1.5 cursor-pointer whitespace-nowrap"
                  >
                    <span>{lang === "hi" ? "विस्तृत प्रभाव समझें" : "Explore Nadi Impact"}</span>
                    <span>🔍</span>
                  </button>
                </div>
              )}

              {/* Visualization Mode View Tabs */}
              <div className="flex items-center gap-2 border-b pb-2 overflow-x-auto text-xs border-slate-200 dark:border-slate-800">
                <button
                  onClick={() => setActiveViewTab("story")}
                  className={`px-3.5 py-2 rounded-xl font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                    activeViewTab === "story"
                      ? "bg-amber-500 text-slate-950 shadow-md font-black"
                      : "text-slate-700 dark:text-slate-400 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-transparent hover:bg-slate-50 dark:hover:text-white shadow-sm"
                  }`}
                >
                  <span>📖</span>
                  <span>Plain English Story</span>
                </button>

                <button
                  onClick={() => setActiveViewTab("timeline")}
                  className={`px-3.5 py-2 rounded-xl font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                    activeViewTab === "timeline"
                      ? "bg-amber-500 text-slate-950 shadow-md font-black"
                      : "text-slate-700 dark:text-slate-400 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-transparent hover:bg-slate-50 dark:hover:text-white shadow-sm"
                  }`}
                >
                  <span>⚖️</span>
                  <span>4-Tier Decision Timeline</span>
                </button>

                <button
                  onClick={() => setActiveViewTab("archetypes")}
                  className={`px-3.5 py-2 rounded-xl font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                    activeViewTab === "archetypes"
                      ? "bg-amber-500 text-slate-950 shadow-md font-black"
                      : "text-slate-700 dark:text-slate-400 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-transparent hover:bg-slate-50 dark:hover:text-white shadow-sm"
                  }`}
                >
                  <span>👑</span>
                  <span>Career Archetypes</span>
                </button>

                <button
                  onClick={() => setActiveViewTab("oracle")}
                  className={`px-3.5 py-2 rounded-xl font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                    activeViewTab === "oracle"
                      ? "bg-gradient-to-r from-purple-500 to-amber-400 text-slate-950 shadow-md font-black"
                      : "text-purple-800 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800/40 hover:bg-purple-100 shadow-sm"
                  }`}
                >
                  <span>🔮</span>
                  <span>Shastric AI Copilot</span>
                </button>

                <button
                  onClick={() => setActiveViewTab("research")}
                  className={`px-3.5 py-2 rounded-xl font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                    activeViewTab === "research"
                      ? "bg-cyan-500 text-slate-950 shadow-md font-black"
                      : "text-slate-700 dark:text-slate-400 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-transparent hover:bg-slate-50 dark:hover:text-white shadow-sm"
                  }`}
                >
                  <span>🔬</span>
                  <span>Empirical Research</span>
                </button>

                <button
                  onClick={() => setActiveViewTab("livesky")}
                  className={`px-3.5 py-2 rounded-xl font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                    activeViewTab === "livesky"
                      ? "bg-amber-500 text-slate-950 shadow-md font-black"
                      : "text-slate-700 dark:text-slate-400 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-transparent hover:bg-slate-50 dark:hover:text-white shadow-sm"
                  }`}
                >
                  <span>🪐</span>
                  <span>Live Sky Transit Clock</span>
                </button>

                <button
                  onClick={() => setActiveViewTab("sudarshana")}
                  className={`px-3.5 py-2 rounded-xl font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                    activeViewTab === "sudarshana"
                      ? "bg-amber-500 text-slate-950 shadow-md font-black"
                      : "text-slate-700 dark:text-slate-400 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-transparent hover:bg-slate-50 dark:hover:text-white shadow-sm"
                  }`}
                >
                  <span>☸️</span>
                  <span>Sudarshana 3-Ring Wheel</span>
                </button>

                <button
                  onClick={() => setActiveViewTab("varga")}
                  className={`px-3.5 py-2 rounded-xl font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                    activeViewTab === "varga"
                      ? "bg-amber-500 text-slate-950 shadow-md font-black"
                      : "text-slate-700 dark:text-slate-400 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-transparent hover:bg-slate-50 dark:hover:text-white shadow-sm"
                  }`}
                >
                  <span>✨</span>
                  <span>Varga Fusion & Bhāvottama</span>
                </button>

                <button
                  onClick={() => setActiveViewTab("triggers")}
                  className={`px-3.5 py-2 rounded-xl font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                    activeViewTab === "triggers"
                      ? "bg-amber-500 text-slate-950 shadow-md font-black"
                      : "text-slate-700 dark:text-slate-400 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-transparent hover:bg-slate-50 dark:hover:text-white shadow-sm"
                  }`}
                >
                  <span>🎯</span>
                  <span>Transit Triggers (BB & SBC)</span>
                </button>

                <button
                  onClick={() => setActiveViewTab("all")}
                  className={`px-3.5 py-2 rounded-xl font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                    activeViewTab === "all"
                      ? "bg-gradient-to-r from-amber-400 to-orange-400 text-slate-950 shadow-md font-black"
                      : "text-slate-700 dark:text-slate-400 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-transparent hover:bg-slate-50 dark:hover:text-white shadow-sm"
                  }`}
                >
                  <span>📜</span>
                  <span>Complete Scholar Suite</span>
                </button>

                <button
                  onClick={() => setActiveViewTab("guide")}
                  className={`px-3.5 py-2 rounded-xl font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
                    activeViewTab === "guide"
                      ? "bg-purple-500 text-slate-950 shadow-md font-black"
                      : "text-slate-700 dark:text-slate-400 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-transparent hover:bg-slate-50 dark:hover:text-white shadow-sm"
                  }`}
                >
                  <span>❓</span>
                  <span>User Help Guide</span>
                </button>
              </div>

              {/* View 1: Executive Plain English Story Mode */}
              {(activeViewTab === "story" || activeViewTab === "all") && result.executive_story && (
                <ConsultationErrorBoundary fallbackTitle="Executive Story Error">
                  <PlainEnglishStoryView story={result.executive_story} lang={lang} />
                </ConsultationErrorBoundary>
              )}

              {/* View 2: Empirical Research Discovery Workbench */}
              {activeViewTab === "research" && (
                <ConsultationErrorBoundary fallbackTitle="Research Workbench Error">
                  <ResearchWorkbenchTab />
                </ConsultationErrorBoundary>
              )}

              {/* View 3: Live Sky Celestial Ephemeris Transit Clock */}
              {activeViewTab === "livesky" && (
                <ConsultationErrorBoundary fallbackTitle="Live Sky Ephemeris Error">
                  <LiveSkyTransitClock
                    nativeName={result.native_name}
                    natalLagnaRashi={result.sudarshana_chakra?.lagna_rashi}
                  />
                </ConsultationErrorBoundary>
              )}

              {/* View 4: Plain Shastric Help Guide */}
              {activeViewTab === "guide" && (
                <ConsultationErrorBoundary fallbackTitle="Help Guide Error">
                  <ShastricHelpGuide lang={lang} />
                </ConsultationErrorBoundary>
              )}

              {/* View 5: 4-Tier Decision Timeline */}
              {(activeViewTab === "timeline" || activeViewTab === "all") && (
                <ConsultationErrorBoundary fallbackTitle="Timeline Rendering Error">
                  <DecisionTimelineCard
                    timeline={result.decision_timeline}
                    scanHorizon={result.scan_horizon}
                    lang={lang}
                  />
                </ConsultationErrorBoundary>
              )}

              {/* View 6: Professional Archetypes & Wealth/Authority Discovery */}
              {(activeViewTab === "archetypes" || activeViewTab === "all") && result.professional_archetypes && (
                <ConsultationErrorBoundary fallbackTitle="Professional Archetype Error">
                  <ProfessionalArchetypeCard
                    data={result.professional_archetypes}
                    lang={lang}
                  />
                </ConsultationErrorBoundary>
              )}

              {/* View 7: Shastric Interactive Copilot */}
              {(activeViewTab === "oracle" || activeViewTab === "all") && (
                <ConsultationErrorBoundary fallbackTitle="Shastric Chat Copilot Error">
                  <ShastricChatOracle
                    timelineWindows={result.decision_timeline || []}
                    nativeName={name}
                    birthDateIso={dob ? `${dob}T${tob || "12:00"}:00+00:00` : undefined}
                    latitude={lat}
                    longitude={lon}
                    lang={lang}
                  />
                </ConsultationErrorBoundary>
              )}

              {/* View 8: Sudarshana Chakra 3-Ring Concentric Wheel */}
              {(activeViewTab === "sudarshana" || activeViewTab === "all") && result.sudarshana_chakra && (
                <ConsultationErrorBoundary fallbackTitle="Sudarshana Chakra Wheel Error">
                  <SudarshanaChakraWheel
                    data={result.sudarshana_chakra}
                    lang={lang}
                  />
                </ConsultationErrorBoundary>
              )}

              {/* View 9: Varga Fusion & Bhāvottama Breakdown */}
              {(activeViewTab === "varga" || activeViewTab === "all") && result.varga_fusion && (
                <ConsultationErrorBoundary fallbackTitle="Varga Fusion Engine Error">
                  <VargaBreakdownCard
                    data={result.varga_fusion}
                    lang={lang}
                  />
                </ConsultationErrorBoundary>
              )}

              {/* View 10: Transit Triggers (Bhrigu Bindu & SBC Nadi Vedha) */}
              {(activeViewTab === "triggers" || activeViewTab === "all") && (
                <ConsultationErrorBoundary fallbackTitle="Transit Triggers Error">
                  <div className="space-y-6">
                    {/* Bhrigu Bindu & SBC Side-by-Side */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Bhrigu Bindu Card */}
                      <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 space-y-3 shadow-sm text-slate-900 dark:text-slate-100">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider flex items-center gap-2">
                            <Sparkles className="w-4 h-4" /> Bhrigu Bindu (Destiny Trigger)
                          </h4>
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                              result.bhrigu_bindu.activation_status === "BENEFIC_TRIGGER"
                                ? "bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40"
                                : result.bhrigu_bindu.activation_status === "MALEFIC_TRIGGER"
                                ? "bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-500/40"
                                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                            }`}
                          >
                            {result.bhrigu_bindu.activation_status}
                          </span>
                        </div>

                        <div className="grid grid-cols-3 gap-2 text-center text-xs">
                          <div className="bg-slate-50 dark:bg-slate-950 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800">
                            <div className="text-[10px] text-slate-500">Sign & Degree</div>
                            <div className="font-bold text-slate-900 dark:text-white text-xs mt-0.5">
                              {result.bhrigu_bindu.rashi} {result.bhrigu_bindu.rashi_degree}°
                            </div>
                          </div>
                          <div className="bg-slate-50 dark:bg-slate-950 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800">
                            <div className="text-[10px] text-slate-500">Nakshatra</div>
                            <div className="font-bold text-slate-900 dark:text-white text-xs mt-0.5">
                              {result.bhrigu_bindu.nakshatra} (P{result.bhrigu_bindu.pada})
                            </div>
                          </div>
                          <div className="bg-slate-50 dark:bg-slate-950 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800">
                            <div className="text-[10px] text-slate-500">Bhava</div>
                            <div className="font-bold text-slate-900 dark:text-white text-xs mt-0.5">H{result.bhrigu_bindu.house_from_lagna}</div>
                          </div>
                        </div>

                        <div className="text-xs text-slate-600 dark:text-slate-400 space-y-1.5 pt-1">
                          <div>
                            <span className="text-slate-500">Conjunct (Transit): </span>
                            <span className="text-slate-900 dark:text-slate-200 font-semibold">
                              {result.bhrigu_bindu.planets_conjunct?.length
                                ? result.bhrigu_bindu.planets_conjunct.join(", ")
                                : "None"}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500">Aspecting (Transit): </span>
                            <span className="text-slate-900 dark:text-slate-200 font-semibold">
                              {result.bhrigu_bindu.planets_aspecting?.length
                                ? result.bhrigu_bindu.planets_aspecting.join(", ")
                                : "None"}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Sarvato-Bhadra Chakra Nadi Vedhas */}
                      <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 space-y-3 shadow-sm text-slate-900 dark:text-slate-100">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-cyan-700 dark:text-cyan-400 uppercase tracking-wider flex items-center gap-2">
                            <Layers className="w-4 h-4" /> 28-Nakshatra SBC Vedha Shield
                          </h4>
                          <span className="text-[10px] text-slate-500 dark:text-slate-400">
                            Janma: <strong className="text-slate-900 dark:text-white">{result.sarvato_bhadra_chakra.janma_nakshatra}</strong>
                          </span>
                        </div>

                        <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
                          {Object.entries(result.sarvato_bhadra_chakra.nadi_afflictions).map(([key, val]) => (
                            <div
                              key={key}
                              className="flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-950 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800/80"
                            >
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-[10px] text-slate-500 dark:text-slate-400 font-bold">{key}</span>
                                <span className="text-slate-800 dark:text-slate-200 font-semibold">{val.nakshatra}</span>
                              </div>
                              <span
                                className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                  val.status === "BENEFIC_AFFIRMATION"
                                    ? "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800/60"
                                    : val.status === "CRUEL_AFFLICTION"
                                    ? "bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800/60"
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

                    {/* Arudha Padas Row */}
                    {result.arudha_padas && (
                      <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 space-y-3 shadow-sm text-slate-900 dark:text-slate-100">
                        <h4 className="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider flex items-center gap-2">
                          <Layers className="w-4 h-4" /> Jaimini & Parashari Arudha Padas (Manifested Worldly Status)
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                          <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-center">
                            <span className="text-[10px] text-amber-700 dark:text-amber-400 font-bold uppercase block">AL (Arudha Lagna)</span>
                            <div className="font-black text-slate-900 dark:text-white text-sm mt-0.5">
                              {result.arudha_padas.AL.rashi} (H{result.arudha_padas.AL.house})
                            </div>
                            <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Worldly Means & External Persona</div>
                          </div>

                          <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-center">
                            <span className="text-[10px] text-purple-700 dark:text-purple-400 font-bold uppercase block">UL (Upapada Lagna)</span>
                            <div className="font-black text-slate-900 dark:text-white text-sm mt-0.5">
                              {result.arudha_padas.UL.rashi} (H{result.arudha_padas.UL.house})
                            </div>
                            <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Marriage, Partner & Sustenance</div>
                          </div>

                          <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-center">
                            <span className="text-[10px] text-emerald-700 dark:text-emerald-400 font-bold uppercase block">A10 (Rajya Pada)</span>
                            <div className="font-black text-slate-900 dark:text-white text-sm mt-0.5">
                              {result.arudha_padas.A10.rashi} (H{result.arudha_padas.A10.house})
                            </div>
                            <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Executive Authority & Career Rank</div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </ConsultationErrorBoundary>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
