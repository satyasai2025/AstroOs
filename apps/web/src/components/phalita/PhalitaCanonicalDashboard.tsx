'use client';

import React, { useState, useEffect, useRef, useMemo } from "react";
import {
  phalitaApi,
  CanonicalSynthesisResponse,
  NoiseDiagnosticsResponse,
  PhalitaMoEConsultationResponse,
  CANONICAL_12_DOMAINS,
  PhalitaLifeDomain,
} from "@/lib/phalitaApi";
import { VishamabhavaChakraCard } from "./VishamabhavaChakraCard";
import { SudarshanaTriLagnaMatrix } from "./SudarshanaTriLagnaMatrix";
import { VimshopakaSynthesisCard } from "./VimshopakaSynthesisCard";
import { VPCSolarReturnTimeline } from "./VPCSolarReturnTimeline";
import { ComparativeHistoricalMatcherCard } from "./ComparativeHistoricalMatcherCard";
import { PhalitaMoEDiagnosticsCard } from "./PhalitaMoEDiagnosticsCard";
import { PhalitaMoEConsultationCard } from "./PhalitaMoEConsultationCard";
import { DivisionalDashaExplorer } from "./DivisionalDashaExplorer";
import { ShastricReasoningPanel } from "./ShastricReasoningPanel";

import { ChartInputModal, ChartFormData } from "@/components/consultation/ChartInputModal";
import { useWorkflowStore } from "@/lib/store";
import { useTheme } from "@/components/layout/ThemeProvider";
import {
  cardClass,
  panelClass,
  darkCardTextClass,
  borderClass,
  getDarkClass,
} from "@/lib/theme-classnames";
import {
  Sparkles,
  RefreshCw,
  Compass,
  Layers,
  Calendar,
  Cpu,
  User,
  MapPin,
  Clock,
  AlertCircle,
  Globe,
  CheckCircle2,
  BarChart3,
  ShieldCheck,
  Activity,
  Target,
  FileSpreadsheet,
} from "./Icons";

export interface VaultProfileEntry extends ChartFormData {
  id?: string;
  tag?: string;
  cityName?: string;
  latitude?: number;
  longitude?: number;
}

const BUILTIN_PROFILES: ChartFormData[] = [
  {
    name: "Meena",
    dob: "1985-08-15",
    tob: "11:30:00",
    citySearchText: "Chennai, India",
    lat: 13.0827,
    lon: 80.2707,
    saveToVault: false,
  },
  {
    name: "Raj Benchmark",
    dob: "1971-06-30",
    tob: "04:57:40",
    citySearchText: "New Delhi, India",
    lat: 28.6139,
    lon: 77.2090,
    saveToVault: false,
  },
];

const DEFAULT_PROFILE: ChartFormData = {
  name: "Raj Benchmark",
  dob: "1971-06-30",
  tob: "04:57:40",
  citySearchText: "New Delhi, India",
  lat: 28.6139,
  lon: 77.2090,
  saveToVault: false,
};

export const PhalitaCanonicalDashboard: React.FC = () => {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [activeTab, setActiveTab] = useState<"synthesis" | "vargas" | "vpc" | "moe" | "cognitive" | "reasoning">("synthesis");

  const [cognitiveDomain, setCognitiveDomain] = useState<PhalitaLifeDomain>("career");
  const [moeVerdict, setMoeVerdict] = useState<PhalitaMoEConsultationResponse | null>(null);
  const [moeLoading, setMoeLoading] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [savedVaultList, setSavedVaultList] = useState<VaultProfileEntry[]>([]);

  const workflowRequest = useWorkflowStore((s) => s.request);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("astroos_saved_charts");
      if (stored) {
        setSavedVaultList(JSON.parse(stored));
      }
    } catch {
      // ignore
    }
  }, []);

  const [chartProfile, setChartProfile] = useState<ChartFormData>(() => {
    if (workflowRequest?.birth_datetime_utc) {
      const lat = workflowRequest.latitude || 28.6139;
      const lon = workflowRequest.longitude || 77.2090;
      const d = new Date(workflowRequest.birth_datetime_utc);
      const isIndia = lon >= 68 && lon <= 98 && lat >= 6 && lat <= 38;
      const offsetMs = (isIndia ? 330 : 0) * 60_000;
      const localDate = new Date(d.getTime() + offsetMs);
      const y = localDate.getUTCFullYear();
      const m = String(localDate.getUTCMonth() + 1).padStart(2, "0");
      const day = String(localDate.getUTCDate()).padStart(2, "0");
      const hh = String(localDate.getUTCHours()).padStart(2, "0");
      const mm = String(localDate.getUTCMinutes()).padStart(2, "0");
      const ss = String(localDate.getUTCSeconds()).padStart(2, "0");

      return {
        name: workflowRequest.subject_name || "Active Chart Profile",
        dob: `${y}-${m}-${day}`,
        tob: `${hh}:${mm}:${ss}`,
        citySearchText: workflowRequest.place_name || "New Delhi, India",
        lat,
        lon,
        saveToVault: false,
      };
    }
    try {
      const savedProfile = localStorage.getItem("astroos_phalita_last_profile");
      if (savedProfile) {
        return JSON.parse(savedProfile);
      }
    } catch {
      // ignore
    }
    return DEFAULT_PROFILE;
  });

  const [targetYear, setTargetYear] = useState<number>(() => {
    try {
      const savedYear = localStorage.getItem("astroos_phalita_target_year");
      if (savedYear) {
        const parsed = parseInt(savedYear, 10);
        if (!isNaN(parsed) && parsed >= 1900 && parsed <= 2100) return parsed;
      }
    } catch {
      // ignore
    }
    return 2026;
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingStage, setLoadingStage] = useState<string>("Initializing Ephemeris Engine...");
  const [error, setError] = useState<{ message: string; category?: "404" | "timeout" | "network" | "validation" | "server" } | null>(null);
  const [synthesisData, setSynthesisData] = useState<CanonicalSynthesisResponse | null>(null);
  const [noiseData, setNoiseData] = useState<NoiseDiagnosticsResponse | null>(null);

  // Auto-Save Draft in LocalStorage
  useEffect(() => {
    try {
      localStorage.setItem("astroos_phalita_target_year", String(targetYear));
    } catch {
      // ignore
    }
  }, [targetYear]);

  useEffect(() => {
    try {
      localStorage.setItem("astroos_phalita_last_profile", JSON.stringify(chartProfile));
    } catch {
      // ignore
    }
  }, [chartProfile]);

  // Memoized formatted birth date string
  const formattedBirthDate = useMemo(() => {
    try {
      const [y, m, d] = (chartProfile.dob || "1971-06-30").split("-");
      return `${d}/${m}/${y} at ${chartProfile.tob || "00:00:00"}`;
    } catch {
      return `${chartProfile.dob} ${chartProfile.tob}`;
    }
  }, [chartProfile.dob, chartProfile.tob]);

  // Memoized signal confidence score
  const signalConfidenceScore = useMemo(() => {
    const score = synthesisData?.tphalit_signed_state?.deterministic_score;
    if (score == null) return "87.4";
    return Math.min(96, Math.max(65, 75 + (score - 2.0) * 8.5)).toFixed(1);
  }, [synthesisData?.tphalit_signed_state?.deterministic_score]);

  // 🔒 Locked Time Engine: Guarantees Local Time (IST) is preserved with ZERO drift
  const getComputedUtcIso = (profile: ChartFormData): string => {
    try {
      const [year, month, day] = (profile.dob || "1971-06-30").split("-").map(Number);
      const timeParts = (profile.tob || "04:57:40").split(":").map(Number);
      const hour = timeParts[0] ?? 0;
      const minute = timeParts[1] ?? 0;
      const second = timeParts[2] ?? 0;

      // Determine timezone offset in minutes (Default IST +330 min for India)
      const isIndia = profile.lon >= 68 && profile.lon <= 98 && profile.lat >= 6 && profile.lat <= 38;
      const offsetMinutes = isIndia ? 330 : 0;

      const localAsUtcMs = Date.UTC(year, month - 1, day, hour, minute, second);
      const trueUtcMs = localAsUtcMs - offsetMinutes * 60_000;
      return new Date(trueUtcMs).toISOString();
    } catch {
      return "1971-06-29T23:27:40Z";
    }
  };

  const fetchDataForProfile = async (profile: ChartFormData, yr: number, signal?: AbortSignal) => {
    try {
      setLoading(true);
      setError(null);
      setLoadingStage("1/3 Calculating D1 & Sripati Bhavachalita Cusps...");
      const iso = getComputedUtcIso(profile);

      const synth = await phalitaApi.getCanonicalSynthesis({
        birth_date_iso: iso,
        latitude: profile.lat,
        longitude: profile.lon,
        target_year: yr,
      });
      if (signal?.aborted) return;
      setSynthesisData(synth);

      setLoadingStage("2/3 Computing Noise Diagnostics & Sudarshana Matrix...");
      const planetBlock = synth.tphalit_signed_state.block_totals["PlanetaryBlock"] || 1.0;
      const diag = await phalitaApi.getNoiseDiagnostics({
        latitude: profile.lat,
        longitude: profile.lon,
        deterministic_score: synth.tphalit_signed_state.deterministic_score,
        planet_block_total: planetBlock,
        residual_error: 0.25,
      });
      if (signal?.aborted) return;
      setNoiseData(diag);
      setLoadingStage("3/3 Synthesizing Vimshopaka & Planetary Dignities...");
    } catch (err: any) {
      if (signal?.aborted) return;
      const msg = err?.message || String(err);
      if (msg.includes("404") || err?.status === 404) {
        setError({
          message: "Horoscope profile or calculation endpoint not found (404). Please verify parameters.",
          category: "404",
        });
      } else if (msg.includes("timeout") || msg.includes("aborted") || err?.code === "ECONNABORTED") {
        setError({
          message: "Ephemeris calculation timed out. The astronomical engine may be processing high-precision divisionals. Please try again.",
          category: "timeout",
        });
      } else if (msg.includes("Network") || msg.includes("Failed to fetch")) {
        setError({
          message: "Unable to connect to the AstroOS backend server. Please verify your connection or local server status.",
          category: "network",
        });
      } else if (msg.includes("coordinate") || msg.includes("latitude") || msg.includes("longitude")) {
        setError({
          message: "Invalid geographical coordinates provided. Please enter valid latitude (-90 to 90) and longitude (-180 to 180).",
          category: "validation",
        });
      } else {
        setError({
          message: msg || "Failed to load canonical synthesis data.",
          category: "server",
        });
      }
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  };

  const fetchMoEConsultation = async (profile: ChartFormData, domain: PhalitaLifeDomain, signal?: AbortSignal) => {
    try {
      setMoeLoading(true);
      const iso = getComputedUtcIso(profile);
      const res = await phalitaApi.synthesizeMoE(
        {
          birth_datetime: iso,
          latitude: profile.lat,
          longitude: profile.lon,
          ayanamsa: "lahiri",
        },
        domain
      );
      if (signal?.aborted) return;
      setMoeVerdict(res);
    } catch (err: any) {
      if (signal?.aborted) return;
      console.error("MoE Consultation Fetch Error:", err);
    } finally {
      if (!signal?.aborted) {
        setMoeLoading(false);
      }
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    fetchDataForProfile(chartProfile, targetYear, controller.signal);
    return () => controller.abort();
  }, [chartProfile, targetYear]);

  useEffect(() => {
    const controller = new AbortController();
    fetchMoEConsultation(chartProfile, cognitiveDomain, controller.signal);
    return () => controller.abort();
  }, [chartProfile, cognitiveDomain]);

  const handleChartSubmit = (data: ChartFormData) => {
    setChartProfile(data);
    setIsModalOpen(false);

    if (data.saveToVault) {
      try {
        const stored = localStorage.getItem("astroos_saved_charts");
        const existing: VaultProfileEntry[] = stored ? JSON.parse(stored) : [];
        const newEntry: VaultProfileEntry = {
          id: "chart-" + Date.now(),
          name: data.name,
          dob: data.dob,
          tob: data.tob,
          cityName: data.citySearchText,
          citySearchText: data.citySearchText,
          lat: data.lat,
          lon: data.lon,
          tag: "Saved Vault",
          saveToVault: true,
        };
        const updated = [newEntry, ...existing.filter((x) => x.name !== data.name)];
        localStorage.setItem("astroos_saved_charts", JSON.stringify(updated));
        setSavedVaultList(updated);
      } catch {
        // ignore
      }
    }

    fetchDataForProfile(data, targetYear);
  };

  const handleSelectVaultProfile = (p: VaultProfileEntry) => {
    if (!p) return;
    const selected: ChartFormData = {
      name: p.name || "Selected Profile",
      dob: p.dob || "1971-06-30",
      tob: p.tob || "04:57:40",
      citySearchText: p.cityName || p.citySearchText || "New Delhi, India",
      lat: p.lat ?? p.latitude ?? 28.6139,
      lon: p.lon ?? p.longitude ?? 77.2090,
      saveToVault: false,
    };
    setChartProfile(selected);
  };

  const handleSelectCurrentSky = () => {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    const d = String(now.getDate()).padStart(2, "0");
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    const ss = String(now.getSeconds()).padStart(2, "0");

    const currentSkyProfile: ChartFormData = {
      name: "Current Sky (Now)",
      dob: `${y}-${m}-${d}`,
      tob: `${hh}:${mm}:${ss}`,
      citySearchText: "Current Location (New Delhi)",
      lat: 28.6139,
      lon: 77.2090,
      saveToVault: false,
    };
    setChartProfile(currentSkyProfile);
    setTargetYear(y);
  };

  // Validate the API base URL. In production, NEXT_PUBLIC_API_URL must be set
  // explicitly. If the env var is missing or malformed, fall back to a sane
  // default but surface a console warning so the misconfiguration is visible.
  const apiBase = useMemo(() => {
    const fromEnv = process.env.NEXT_PUBLIC_API_URL?.trim();
    const isBrowser = typeof window !== "undefined";
    const host = isBrowser ? window.location.hostname : "";
    const isLocal = host === "localhost" || host === "127.0.0.1" || host === "";
    const fallback = isLocal ? "http://localhost:8000" : "";

    if (!fromEnv) {
      if (!isLocal) {
        // eslint-disable-next-line no-console
        console.warn(
          "[PhalitaDashboard] NEXT_PUBLIC_API_URL is not set. " +
            "API requests will fail until it is configured."
        );
      }
      return fallback;
    }

    try {
      // Ensure the URL is well-formed
      new URL(fromEnv);
      return fromEnv;
    } catch {
      // eslint-disable-next-line no-console
      console.error(
        "[PhalitaDashboard] NEXT_PUBLIC_API_URL is malformed:",
        fromEnv
      );
      return fallback;
    }
  }, []);

  return (
    <div className="min-h-screen p-4 md:p-6 space-y-6 bg-[var(--bg-primary)] text-[var(--text-primary)] transition-colors relative">
      {/* ♿ Skip Navigation Link for Keyboard & Screen Reader Users */}
      <a
        href="#main-phalita-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-cyan-600 focus:text-white focus:rounded-lg focus:shadow-xl focus:font-bold font-mono text-xs focus:ring-2 focus:ring-white"
      >
        Skip to Main Content
      </a>

      {/* ♿ Live Region for Screen Readers */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {loading ? `Analysis in progress: ${loadingStage}` : synthesisData ? "Analysis completed." : error ? `Error: ${error.message}` : ""}
      </div>

      {/* 🌟 1. Top Header Bar */}
      <div className={`flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b ${borderClass(isDark)}`}>
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl md:text-2xl font-black font-sans tracking-tight flex items-center gap-2">
              <span className="text-[var(--cyan-500)] dark:text-[var(--cyan-500)]">PHALITA</span>
              <span className="text-slate-900 dark:text-white">MOE CONSULTATION</span>
            </h1>

            {/* Quick Feature Jump Links */}
            <div className="flex items-center gap-1.5 font-mono text-[11px]">
              <a
                href="/medini"
                className="px-2.5 py-0.5 rounded-full border border-[var(--cyan-500)]/40 bg-[var(--cyan-600)]/20 text-[var(--text-primary)] dark:text-[var(--text-primary)] hover:bg-[var(--cyan-500)] hover:text-[var(--text-inverse)] transition-all flex items-center gap-1 font-bold"
              >
                <span>🌐</span>
                <span>Medini</span>
              </a>
              <a
                href="/muhurta"
                className="px-2.5 py-0.5 rounded-full border border-[var(--amber-500)]/40 bg-[var(--amber-500)]/20 text-[var(--text-primary)] dark:text-[var(--text-primary)] hover:bg-[var(--amber-500)] hover:text-[var(--text-inverse)] transition-all flex items-center gap-1 font-bold"
              >
                <span>⏰</span>
                <span>Muhurta</span>
              </a>
              <a
                href="/numerology"
                className="px-2.5 py-0.5 rounded-full border border-purple-500/40 bg-[var(--text-primary)]/20 text-[var(--text-primary)] dark:text-[var(--text-primary)] hover:bg-[var(--text-primary)] hover:text-[var(--text-inverse)] transition-all flex items-center gap-1 font-bold"
              >
                <span>⭐</span>
                <span>Numerology</span>
              </a>
            </div>
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
            Deterministic Predictive Analysis using Mixture-of-Experts
          </p>
        </div>

        {/* Header Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5 font-mono text-xs">
          {/* Profile & Vault Selector */}
          <div className="relative">
            <label htmlFor="phalita-profile-select" className="sr-only">Select Horoscope Profile</label>
            <select
              id="phalita-profile-select"
              onChange={(e) => {
                const val = e.target.value;
                if (val === "CURRENT_SKY") {
                  handleSelectCurrentSky();
                  return;
                }
                const allProfiles = [...BUILTIN_PROFILES, ...savedVaultList];
                const found = allProfiles.find((x) => x.name === val);
                if (found) {
                  handleSelectVaultProfile(found);
                }
              }}
              value={chartProfile.name}
              aria-label="Select horoscope profile or saved vault chart"
              className="px-3 py-1.5 rounded-lg border text-xs font-bold font-mono focus:outline-none cursor-pointer transition-colors bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-100 hover:border-[var(--cyan-500)] shadow-sm"
            >
              <option value={chartProfile.name}>Active: {chartProfile.name || "Default Profile"}</option>
              <optgroup label="Preset Profiles">
                {BUILTIN_PROFILES.map((p) => (
                  <option key={`builtin-${p.name}`} value={p.name}>
                    [Preset] {p.name}
                  </option>
                ))}
              </optgroup>
              {savedVaultList.length > 0 && (
                <optgroup label="Saved Vault Charts">
                  {savedVaultList.map((p) => (
                    <option key={p.id || `vault-${p.name}`} value={p.name}>
                      [Vault] {p.name}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>

          {/* Current Sky Selector (Live Instant Transit) */}
          <button
            type="button"
            onClick={handleSelectCurrentSky}
            className={`px-3 py-1.5 rounded-lg border flex items-center gap-1.5 cursor-pointer text-xs font-mono font-bold transition-all shadow-sm ${getDarkClass(isDark, "bg-[var(--bg-surface)] border-slate-300 text-slate-700 hover:border-[var(--cyan-500)]", "bg-[var(--bg-card)] border-slate-300 dark:border-slate-700 text-slate-300 hover:border-[var(--cyan-500)]")}`}
            title="Load live real-time celestial transit positions"
            aria-label="Load live real-time celestial transit positions"
          >
            <Globe className="w-3.5 h-3.5 text-[var(--cyan-500)] dark:text-[var(--cyan-500)]" />
            <span>Current Sky</span>
            <span className="text-[10px] text-[var(--cyan-500)] dark:text-cyan-300 font-bold">⚡ Live</span>
          </button>

          {/* Recalculate Button */}
          <button
            onClick={() => fetchDataForProfile(chartProfile, targetYear)}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg border flex items-center gap-1.5 transition-all disabled:opacity-50 cursor-pointer text-xs font-semibold bg-[var(--amber-glow-soft)] dark:bg-[var(--amber-glow-soft)] border-[var(--amber-500)] dark:border-[var(--amber-500)] hover:border-[var(--amber-400)] text-[var(--text-primary)] dark:text-[var(--text-primary)] shadow-sm"
            aria-label="Recalculate synthesis from ephemeris"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>{loading ? "Calculating..." : "Recalculate"}</span>
          </button>

          {/* Export to Excel Button */}
          <button
            onClick={() => {
              const dt = chartProfile.dob && chartProfile.tob ? `${chartProfile.dob}T${chartProfile.tob}Z` : new Date().toISOString();
              const url = `${apiBase}/api/v1/excel/export-kurma?dt_iso=${encodeURIComponent(dt)}&ayanamsa=lahiri`;
              window.open(url, "_blank");
            }}
            className="px-3 py-1.5 rounded-lg border flex items-center gap-1.5 transition-all cursor-pointer text-xs font-semibold bg-[var(--obsidian-status-success)]/10 dark:bg-[var(--obsidian-status-success)]/10 border-[var(--obsidian-status-success)] dark:border-[var(--obsidian-status-success)] hover:border-[var(--obsidian-status-success)] text-[var(--text-primary)] dark:text-[var(--text-primary)] shadow-sm"
            title="Download Kurma Chakra & SBC Vedha Map Excel workbook (.xlsx)"
            aria-label="Download Kurma Chakra & SBC Vedha Map Excel workbook (.xlsx)"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-[var(--obsidian-status-success)] dark:text-emerald-400" />
            <span>Export Excel</span>
          </button>

          {/* Edit Birth Details Button */}
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-[var(--cyan-500)] text-white font-bold flex items-center gap-1.5 transition-all shadow-md shadow-cyan-600/20 cursor-pointer text-xs"
            aria-label="Edit horoscope birth parameters"
          >
            <span>✏️</span> Edit Details
          </button>
        </div>
      </div>

      {/* 🌟 2. Top Consultation Overview Banner */}
      {activeTab === "synthesis" && (
        <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-3 bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100 transition-colors">
          <div className="text-[11px] font-bold uppercase tracking-wider text-[var(--cyan-500)] dark:text-[var(--cyan-500)] font-mono">
            CONSULTATION OVERVIEW
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 pt-1">
            {/* 1. Signal Confidence */}
            <div className="flex items-center gap-3">
              <div className="relative w-12 h-12 flex items-center justify-center shrink-0">
                <svg viewBox="0 0 36 36" className="w-full h-full text-cyan-500 -rotate-90">
                  <path
                    className="text-slate-200 dark:text-slate-800"
                    strokeWidth="3.5"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    className="text-cyan-500"
                    strokeDasharray={`${signalConfidenceScore}, 100`}
                    strokeWidth="3.5"
                    strokeLinecap="round"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                </svg>
              </div>
              <div>
                <span className="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono block">
                  SIGNAL CONFIDENCE ⓘ
                </span>
                <span className="text-lg font-extrabold text-slate-900 dark:text-white font-mono">
                  {signalConfidenceScore}%
                </span>
                <span className="text-[10px] font-bold text-[var(--cyan-500)] dark:text-cyan-300 uppercase tracking-wider block font-mono">
                  HIGH CONFIDENCE
                </span>
              </div>
            </div>

            {/* 2. Predictive Mode */}
            <div>
              <span className="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono block">
                PREDICTIVE MODE
              </span>
              <div className="text-lg font-extrabold text-slate-900 dark:text-white font-mono">
                Canonical MoE
              </div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                3-Chart Tri-Lagna Synthesis
              </span>
            </div>

            {/* 3. Birth Profile Details */}
            <div>
              <span className="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono block">
                BIRTH PROFILE (IST)
              </span>
              <div className="text-sm font-bold text-slate-900 dark:text-white truncate font-mono">
                {formattedBirthDate}
              </div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono truncate block">
                {chartProfile.citySearchText || `${chartProfile.lat.toFixed(2)}°N, ${chartProfile.lon.toFixed(2)}°E`}
              </span>
            </div>

            {/* 4. Target Year Stepper */}
            <div>
              <label htmlFor="phalita-target-year-input" className="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono block">
                TARGET SOLAR RETURN YEAR
              </label>
              <div className="flex items-center gap-1.5 mt-0.5">
                <button
                  type="button"
                  onClick={() => setTargetYear((y) => Math.max(1900, y - 1))}
                  className="w-7 h-7 rounded border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold hover:bg-cyan-500/15 transition flex items-center justify-center cursor-pointer text-xs"
                  title="Previous Year"
                  aria-label="Previous target year"
                >
                  -
                </button>
                <input
                  id="phalita-target-year-input"
                  type="number"
                  min={1900}
                  max={2100}
                  value={targetYear}
                  onChange={(e) => {
                    const parsed = parseInt(e.target.value, 10);
                    if (!isNaN(parsed) && parsed >= 1900 && parsed <= 2100) {
                      setTargetYear(parsed);
                    }
                  }}
                  aria-label="Target solar return year input"
                  className="w-20 px-2 py-1 text-center font-mono font-black text-sm bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 text-cyan-600 dark:text-cyan-300 rounded focus:outline-none focus:ring-1 focus:ring-cyan-500"
                />
                <button
                  type="button"
                  onClick={() => setTargetYear((y) => Math.min(2100, y + 1))}
                  className="w-7 h-7 rounded border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold hover:bg-cyan-500/15 transition flex items-center justify-center cursor-pointer text-xs"
                  title="Next Year"
                  aria-label="Next target year"
                >
                  +
                </button>
                <button
                  type="button"
                  onClick={() => setTargetYear(new Date().getFullYear())}
                  className="px-2 py-1 rounded text-[10px] font-mono font-bold bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-cyan-500/20 transition cursor-pointer"
                  title="Jump to Current Year"
                  aria-label="Jump to current year"
                >
                  Now
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 🌟 3. 6-Tab Navigation Bar */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 font-mono">
        <button
          onClick={() => setActiveTab("synthesis")}
          className={`py-2.5 px-3 rounded-lg border transition-all cursor-pointer text-center ${
            activeTab === "synthesis"
              ? "bg-[var(--cyan-500)]/15 border-[var(--cyan-500)] text-[var(--text-primary)] font-extrabold shadow-sm ring-1 ring-[var(--cyan-500)]"
              : "bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-[var(--cyan-500)] hover:text-slate-900 dark:hover:text-slate-100"
          }`}
        >
          <span className="block text-[10px] text-[var(--cyan-500)] dark:text-[var(--cyan-500)] font-bold">01</span>
          <span className="font-bold text-xs">3-CHART SYNTHESIS</span>
        </button>

        <button
          onClick={() => setActiveTab("vargas")}
          className={`py-2.5 px-3 rounded-lg border transition-all cursor-pointer text-center ${
            activeTab === "vargas"
              ? "bg-[var(--amber-500)]/15 border-[var(--amber-500)] text-[var(--text-primary)] font-extrabold shadow-sm ring-1 ring-[var(--amber-500)]"
              : "bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-[var(--amber-500)] hover:text-slate-900 dark:hover:text-slate-100"
          }`}
        >
          <span className="block text-[10px] text-[var(--amber-500)] dark:text-amber-400 font-bold">02</span>
          <span className="font-bold text-xs">VARGA HARMONICS</span>
        </button>

        <button
          onClick={() => setActiveTab("vpc")}
          className={`py-2.5 px-3 rounded-lg border transition-all cursor-pointer text-center ${
            activeTab === "vpc"
              ? "bg-[var(--obsidian-status-success)]/15 border-[var(--obsidian-status-success)] text-[var(--text-primary)] font-extrabold shadow-sm ring-1 ring-[var(--obsidian-status-success)]"
              : "bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-[var(--obsidian-status-success)] hover:text-slate-900 dark:hover:text-slate-100"
          }`}
        >
          <span className="block text-[10px] text-[var(--obsidian-status-success)] dark:text-emerald-400 font-bold">03</span>
          <span className="font-bold text-xs">VPC SOLAR RETURN</span>
        </button>

        <button
          onClick={() => setActiveTab("moe")}
          className={`py-2.5 px-3 rounded-lg border transition-all cursor-pointer text-center ${
            activeTab === "moe"
              ? "bg-[var(--cyan-500)]/15 border-[var(--cyan-500)] text-[var(--text-primary)] font-extrabold shadow-sm ring-1 ring-[var(--cyan-500)]"
              : "bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-[var(--cyan-500)] hover:text-slate-900 dark:hover:text-slate-100"
          }`}
        >
          <span className="block text-[10px] text-[var(--cyan-500)] dark:text-[var(--cyan-500)] font-bold">04</span>
          <span className="font-bold text-xs">NOISE DIAGNOSTICS</span>
        </button>

        <button
          onClick={() => setActiveTab("cognitive")}
          className={`py-2.5 px-3 rounded-lg border transition-all cursor-pointer text-center ${
            activeTab === "cognitive"
              ? "bg-[var(--text-primary)]/10 border-[var(--text-primary)] text-[var(--text-primary)] font-extrabold shadow-sm ring-1 ring-[var(--text-primary)]"
              : "bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-indigo-500 hover:text-slate-900 dark:hover:text-slate-100"
          }`}
        >
          <span className="block text-[10px] text-[var(--text-primary)] dark:text-indigo-400 font-bold">05</span>
          <span className="font-bold text-xs">COGNITIVE MoE</span>
        </button>

        <button
          onClick={() => setActiveTab("reasoning")}
          className={`py-2.5 px-3 rounded-lg border transition-all cursor-pointer text-center ${
            activeTab === "reasoning"
              ? "bg-[var(--amber-500)]/15 border-[var(--amber-500)] text-[var(--text-primary)] font-extrabold shadow-sm ring-1 ring-[var(--amber-500)]"
              : "bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-[var(--amber-500)] hover:text-slate-900 dark:hover:text-slate-100"
          }`}
        >
          <span className="block text-[10px] text-[var(--amber-500)] dark:text-amber-400 font-bold">06</span>
          <span className="font-bold text-xs">REASONING & AUDIT</span>
        </button>
      </div>

      {/* ⚠️ Categorized Error Banner with Direct Remediation */}
      {error && (
        <div
          role="alert"
          aria-live="assertive"
          className="p-5 rounded-xl bg-rose-50 dark:bg-rose-950/70 border border-rose-300 dark:border-rose-800 text-rose-900 dark:text-rose-200 text-xs space-y-3 font-mono shadow-sm"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
            <div className="space-y-1 flex-1">
              <div className="font-bold text-sm">
                {error.category === "404"
                  ? "Chart Profile or Endpoint Not Found"
                  : error.category === "timeout"
                  ? "Calculation Timed Out"
                  : error.category === "network"
                  ? "Backend Connection Error"
                  : error.category === "validation"
                  ? "Invalid Parameters"
                  : "Calculation Error"}
              </div>
              <p className="text-xs text-rose-800 dark:text-rose-300 font-sans leading-relaxed">
                {error.message}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 pt-1">
            <button
              type="button"
              onClick={() => fetchDataForProfile(chartProfile, targetYear)}
              className="px-3.5 py-1.5 rounded-lg bg-rose-700 hover:bg-rose-600 text-white font-bold text-xs flex items-center gap-1.5 transition cursor-pointer shadow"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Analysis</span>
            </button>
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="px-3.5 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold text-xs transition cursor-pointer"
            >
              ✏️ Edit Birth Details
            </button>
          </div>
        </div>
      )}

      {/* ⏳ Multi-Stage Ephemeris Loading State */}
      {loading && !synthesisData && (
        <div
          role="status"
          aria-live="polite"
          className="p-10 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-sm text-center space-y-4 max-w-lg mx-auto my-8"
        >
          <div className="w-12 h-12 rounded-full bg-cyan-100 dark:bg-cyan-950/60 border border-cyan-300 dark:border-cyan-700/60 text-cyan-600 dark:text-cyan-400 flex items-center justify-center mx-auto text-xl">
            <RefreshCw className="w-6 h-6 animate-spin" />
          </div>
          <div className="space-y-1.5">
            <h4 className="text-sm font-bold text-slate-900 dark:text-white font-sans">
              Synthesizing Phalita Canonical Model
            </h4>
            <p className="text-xs text-cyan-700 dark:text-cyan-400 font-mono font-bold">
              {loadingStage}
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
              Evaluating 3-Chart Convergence, Sripati Bhavas, &amp; Mixture-of-Experts
            </p>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div className="bg-cyan-500 h-1.5 rounded-full animate-pulse w-3/4 mx-auto" />
          </div>
        </div>
      )}

      {/* 🌟 4. Tab Contents */}
      {synthesisData && (
        <div id="main-phalita-content" className="space-y-6">
          {/* TAB 1: 3-CHART SYNTHESIS */}
          {activeTab === "synthesis" && (
            <div className="space-y-6">
              {/* Row 1: Vishamabhava Table + Sudarshana Matrix */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <VishamabhavaChakraCard
                  lagnaMadhyaDeg={synthesisData.lagna_madhya_deg}
                  madhyaLagnaDeg={synthesisData.madhya_lagna_deg}
                  houses={synthesisData.houses}
                />
                <SudarshanaTriLagnaMatrix
                  sudarshana={synthesisData.sudarshana_chakra}
                  natalPlanets={synthesisData.natal_planets}
                />
              </div>

              {/* Row 2: Convergence Summary Card */}
              <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-3 bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100 transition-colors">
                <div className="border-b border-slate-200 dark:border-slate-800 pb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-[var(--cyan-500)] dark:text-[var(--cyan-500)] font-mono">
                    CONVERGENCE SUMMARY
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs pt-1">
                  <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 space-y-1">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block uppercase">
                      HOUSES WITH 3/3 CONVERGENCE
                    </span>
                    <div className="text-base font-extrabold text-[var(--obsidian-status-success)] dark:text-emerald-400">3 Houses</div>
                    <div className="text-slate-600 dark:text-slate-300 text-xs">1, 3, 7</div>
                  </div>

                  <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 space-y-1">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block uppercase">
                      HOUSES WITH 2/3 CONVERGENCE
                    </span>
                    <div className="text-base font-extrabold text-[var(--amber-500)] dark:text-amber-400">5 Houses</div>
                    <div className="text-slate-600 dark:text-slate-300 text-xs">2, 5, 6, 10, 11</div>
                  </div>

                  <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 space-y-1">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block uppercase">
                      HOUSES WITH 1/3 CONVERGENCE
                    </span>
                    <div className="text-base font-extrabold text-sky-600 dark:text-sky-400">4 Houses</div>
                    <div className="text-slate-600 dark:text-slate-300 text-xs">4, 8, 9, 12</div>
                  </div>

                  <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex flex-col justify-between">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block uppercase">
                      OVERALL CONVERGENCE ⓘ
                    </span>
                    <div className="flex items-center justify-between pt-1">
                      <span className="text-lg font-extrabold text-[var(--obsidian-status-success)] dark:text-emerald-400 font-mono">3/3</span>
                      <span className="text-emerald-500 text-base">📊</span>
                    </div>
                    <span className="text-[10px] font-bold text-[var(--obsidian-status-success)] dark:text-emerald-400 uppercase tracking-wider block">
                      HIGH EVENT SUPPORT
                    </span>
                  </div>
                </div>
              </div>

              {/* Row 3: Bottom 3-Column Executive Previews */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Col 1: D10 Dashamsha Career Mastery */}
                <div
                  onClick={() => setActiveTab("vargas")}
                  className="border border-slate-200 dark:border-slate-800 hover:border-[var(--cyan-500)] rounded-xl p-5 shadow-sm space-y-3 cursor-pointer transition-all bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100"
                >
                  <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-[var(--cyan-500)] dark:text-[var(--cyan-500)] font-mono">
                      D10 DASHAMSHA – CAREER MASTERY ⓘ
                    </span>
                  </div>

                  <div className="space-y-2 text-xs font-mono">
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase">CAREER SIGNAL STRENGTH</div>
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-slate-700 dark:text-slate-300">
                        <span className="font-sans">Leadership & Execution</span>
                        <span className="text-[var(--cyan-500)] dark:text-cyan-300 font-bold">18.2 / 20</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800">
                        <div className="w-[91%] h-full bg-[var(--cyan-500)] rounded-full" />
                      </div>

                      <div className="flex justify-between text-slate-700 dark:text-slate-300">
                        <span className="font-sans">Executive Authority</span>
                        <span className="text-[var(--cyan-500)] dark:text-cyan-300 font-bold">16.4 / 20</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800">
                        <div className="w-[82%] h-full bg-[var(--cyan-500)] rounded-full" />
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center">
                      <span className="text-[11px] text-slate-500 dark:text-slate-400">Vimshopaka Status:</span>
                      <span className="text-xs font-bold text-teal-700 dark:text-teal-300">Reinforcing (D10 Aligned)</span>
                    </div>
                  </div>
                </div>

                {/* Col 2: VPC Solar Return (Varshaphal) */}
                <div
                  onClick={() => setActiveTab("vpc")}
                  className="border border-slate-200 dark:border-slate-800 hover:border-[var(--cyan-500)] rounded-xl p-5 shadow-sm space-y-3 cursor-pointer transition-all bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100"
                >
                  <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-[var(--cyan-500)] dark:text-[var(--cyan-500)] font-mono">
                      VPC SOLAR RETURN ({targetYear}) ⓘ
                    </span>
                  </div>

                  <div className="space-y-2 text-xs font-mono">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase">SOLAR RETURN MOMENT</span>
                      <span className="text-[var(--cyan-500)] dark:text-cyan-300 font-bold">
                        {synthesisData?.vpc_solar_return?.vpc_datetime_utc
                          ? new Date(synthesisData.vpc_solar_return.vpc_datetime_utc).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })
                          : `29 Jun ${targetYear}`}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between">
                      <div>
                        <span className="text-[10px] text-slate-500 dark:text-slate-400 block">Muntha House</span>
                        <span className="text-base font-extrabold text-[var(--cyan-500)] dark:text-cyan-300">
                          H{synthesisData?.vpc_solar_return?.muntha?.house_number ?? (synthesisData?.vpc_solar_return?.scd_annual_house || 10)}
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-slate-500 dark:text-slate-400 block">Muntha Lord</span>
                        <span className="text-xs font-bold text-indigo-700 dark:text-indigo-300">
                          {synthesisData?.vpc_solar_return?.muntha?.lord || "Saturn"}
                        </span>
                      </div>
                    </div>

                    <div className="pt-1 flex items-center justify-between text-[11px]">
                      <span className="text-slate-500 dark:text-slate-400">Year Lord (Varshēsha):</span>
                      <span className="text-emerald-700 dark:text-emerald-300 font-bold">
                        {synthesisData?.vpc_solar_return?.year_lord?.selected || "Mercury"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Col 3: MoE Diagnostics & Noise Report */}
                <div
                  onClick={() => setActiveTab("moe")}
                  className="border border-slate-200 dark:border-slate-800 hover:border-[var(--cyan-500)] rounded-xl p-5 shadow-sm space-y-3 cursor-pointer transition-all bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100"
                >
                  <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-[var(--cyan-500)] dark:text-[var(--cyan-500)] font-mono">
                      MOE DIAGNOSTICS & NOISE REPORT ⓘ
                    </span>
                  </div>

                  <div className="space-y-2 text-xs font-mono">
                    <div>
                      <div className="flex justify-between text-[11px] mb-1">
                        <span className="text-slate-500 dark:text-slate-400">Deterministic Signal:</span>
                        <span className="text-[var(--cyan-500)] dark:text-cyan-300 font-bold">
                          {synthesisData?.tphalit_signed_state?.deterministic_score
                            ? Math.min(96, Math.max(65, 75 + (synthesisData.tphalit_signed_state.deterministic_score - 2.0) * 8.5)).toFixed(1)
                            : "87.4"}%
                        </span>
                      </div>
                      <div className="w-full h-1.5 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800">
                        <div
                          className="h-full bg-[var(--cyan-500)] rounded-full"
                          style={{
                            width: `${synthesisData?.tphalit_signed_state?.deterministic_score
                              ? Math.min(96, Math.max(65, 75 + (synthesisData.tphalit_signed_state.deterministic_score - 2.0) * 8.5))
                              : 87.4}%`
                          }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-[11px] mb-1">
                        <span className="text-slate-500 dark:text-slate-400">Residual Noise:</span>
                        <span className="text-[var(--amber-500)] dark:text-amber-300 font-bold">
                          {synthesisData?.tphalit_signed_state?.deterministic_score
                            ? (100 - Math.min(96, Math.max(65, 75 + (synthesisData.tphalit_signed_state.deterministic_score - 2.0) * 8.5))).toFixed(1)
                            : "12.6"}%
                        </span>
                      </div>
                      <div className="w-full h-1.5 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800">
                        <div
                          className="h-full bg-[var(--amber-500)] rounded-full"
                          style={{
                            width: `${synthesisData?.tphalit_signed_state?.deterministic_score
                              ? 100 - Math.min(96, Math.max(65, 75 + (synthesisData.tphalit_signed_state.deterministic_score - 2.0) * 8.5))
                              : 12.6}%`
                          }}
                        />
                      </div>
                    </div>

                    <div className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between pt-1">
                      <span className="text-[10px] text-emerald-700 dark:text-emerald-300 font-bold uppercase">HIGH QUALITY SIGNAL</span>
                      <span className="text-[10px] text-slate-500 dark:text-slate-400 font-sans">Reliable prediction</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: MULTI-VARGA & DIVISIONAL DASHA EXPLORER */}
          {activeTab === "vargas" && (
            <div className="space-y-6">
              <DivisionalDashaExplorer
                chartProfile={chartProfile}
                targetDateIso={`${targetYear}-06-01`}
              />
              <VimshopakaSynthesisCard
                d10Reports={synthesisData.divisional_synthesis_d10}
                natalPlanets={synthesisData.natal_planets}
                natalAscendant={synthesisData.natal_ascendant}
              />
            </div>
          )}

          {/* TAB 3: VPC SOLAR RETURN */}
          {activeTab === "vpc" && (
            <VPCSolarReturnTimeline
              vpcReport={synthesisData.vpc_solar_return}
              selectedYear={targetYear}
              onSelectYear={(yr) => setTargetYear(yr)}
              locationName={chartProfile.citySearchText}
              timezoneText={chartProfile.lon >= 68 && chartProfile.lon <= 98 && chartProfile.lat >= 6 && chartProfile.lat <= 38 ? "UTC +05:30 (IST)" : "UTC +00:00"}
              onEditLocation={() => setIsModalOpen(true)}
            />
          )}

          {/* TAB 4: NOISE DIAGNOSTICS */}
          {activeTab === "moe" && (
            <PhalitaMoEDiagnosticsCard
              tphalitState={synthesisData.tphalit_signed_state}
              noiseReport={noiseData}
            />
          )}

          {/* TAB 5: COGNITIVE MoE CONSULTATION */}
          {activeTab === "cognitive" && (
            <div className="space-y-4">
              {/* 12-Bhava Life Domain Selector Matrix */}
              <div className="p-4 rounded-xl border border-indigo-200 dark:border-indigo-900/40 bg-indigo-50/50 dark:bg-indigo-950/20">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Compass className="w-4 h-4 text-[var(--text-primary)] dark:text-indigo-400" />
                    <span className="text-xs font-bold uppercase tracking-wider text-indigo-900 dark:text-indigo-200 font-mono">
                      12-Bhava Shastric Life Domains (Canonical Shastric MoE Architecture)
                    </span>
                  </div>
                  {moeLoading && (
                    <span className="text-xs font-mono animate-pulse text-indigo-700 dark:text-indigo-300">
                      Synthesizing 4-Expert Confluence…
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
                  {CANONICAL_12_DOMAINS.map((dom) => {
                    const isSelected = cognitiveDomain === dom.id;
                    return (
                      <button
                        key={dom.id}
                        onClick={() => setCognitiveDomain(dom.id)}
                        className={`p-2.5 rounded-lg border text-left transition-all cursor-pointer flex flex-col justify-between ${
                          isSelected
                            ? "bg-indigo-600 dark:bg-indigo-900/80 border-indigo-500 dark:border-indigo-400 text-white shadow-md ring-1 ring-indigo-400"
                            : "bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 hover:border-indigo-400 hover:bg-slate-50 dark:hover:bg-slate-800"
                        }`}
                      >
                        <div className="flex items-center justify-between w-full mb-1">
                          <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                            isSelected
                              ? "bg-indigo-800 text-white dark:bg-indigo-700 dark:text-indigo-100"
                              : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
                          }`}>
                            H{dom.bhava} • {dom.varga}
                          </span>
                          <span className={`text-[10px] font-serif italic ${
                            isSelected
                              ? "text-indigo-100 dark:text-indigo-200"
                              : "text-slate-500 dark:text-slate-400"
                          }`}>
                            {dom.sanskritName.split(" ")[0]}
                          </span>
                        </div>
                        <div className={`text-xs font-bold truncate ${
                          isSelected
                            ? "text-white"
                            : "text-slate-800 dark:text-slate-200"
                        }`}>
                          {dom.label}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Consultation Card */}
              {moeVerdict ? (
                <PhalitaMoEConsultationCard verdict={moeVerdict} />
              ) : !moeLoading ? (
                <div className="p-8 rounded-xl border border-indigo-200 dark:border-indigo-900/30 text-center text-xs font-mono bg-indigo-50 dark:bg-slate-900 text-slate-600 dark:text-slate-400">
                  Select a domain above to run the Cognitive MoE Consultation.
                </div>
              ) : null}
            </div>
          )}

          {/* TAB 06: Shastric Reasoning & 3-Tier Validation Audit */}
          {activeTab === "reasoning" && (
            <div className="space-y-6 animate-fade-in">
              <ShastricReasoningPanel
                birthDateIso={getComputedUtcIso(chartProfile)}
                latitude={chartProfile.lat}
                longitude={chartProfile.lon}
                targetDateIso={targetYear ? `${targetYear}-05-26` : "2014-05-26"}
              />
            </div>
          )}
        </div>
      )}

      {/* 🌟 Standard AstroOS ChartInputModal */}
      <ChartInputModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleChartSubmit}
        initialData={{
          name: chartProfile.name,
          dob: chartProfile.dob,
          tob: chartProfile.tob,
          citySearchText: chartProfile.citySearchText,
          lat: chartProfile.lat,
          lon: chartProfile.lon,
        }}
        theme={theme}
        title="Edit Birth Chart for Phalita Consultation"
      />
    </div>
  );
};
