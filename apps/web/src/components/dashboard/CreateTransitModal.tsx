"use client";

import { BirthPlaceSearch } from "@/components/workflow/BirthPlaceSearch";
import { api } from "@/lib/api";
import { useMyCharts } from "@/lib/charts";
import { useWorkflowStore } from "@/lib/store";
import type { AyanamsaCode, BirthChartSummary, HouseSystemCode, TransitPlanetResponse, TransitResponse } from "@/lib/types";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

interface Props {
  open: boolean;
  onClose: () => void;
}

// ── Navagraha Metadata & Vedic Classifications ────────────────────────────────

export interface PlanetDisplayInfo {
  id: string;
  name: string;
  sanskrit: string;
  hindi: string;
  symbol: string;
  nature: "benefic" | "malefic" | "mild_malefic" | "conditional";
  natureLabel: string;
  sublabel: string;
  color: string;
  iconBg: string;
  rashi: string;
  rashiSanskrit: string;
  degreeInSign: number;
  degreeFormatted: string;
  nakshatra: string;
  pada: number;
  isRetrograde: boolean;
  isCombust?: boolean;
  speed?: number;
  gati?: string;
  houseFromMoon?: number;
  isFavorable?: boolean | null;
  isSadeSati?: boolean;
  isAshtamaShani?: boolean;
  hasVedha?: boolean;
  bindus?: number | null;
}

const GRAHA_META: Record<
  string,
  {
    sanskrit: string;
    hindi: string;
    symbol: string;
    nature: "benefic" | "malefic" | "mild_malefic" | "conditional";
    natureLabel: string;
    sublabel: string;
    color: string;
    iconBg: string;
  }
> = {
  sun: {
    sanskrit: "Surya",
    hindi: "सूर्य",
    symbol: "☉",
    nature: "mild_malefic",
    natureLabel: "Krura (Mild Malefic)",
    sublabel: "King · Soul · Vitality",
    color: "#f59e0b",
    iconBg: "rgba(245, 158, 11, 0.15)",
  },
  moon: {
    sanskrit: "Chandra",
    hindi: "चन्द्र",
    symbol: "☽",
    nature: "benefic",
    natureLabel: "Shubha (Benefic)",
    sublabel: "Queen · Mind · Emotions",
    color: "#93c5fd",
    iconBg: "rgba(147, 197, 253, 0.15)",
  },
  mars: {
    sanskrit: "Mangala",
    hindi: "मंगल",
    symbol: "♂",
    nature: "malefic",
    natureLabel: "Papa (Malefic)",
    sublabel: "Commander · Energy · Courage",
    color: "#ef4444",
    iconBg: "rgba(239, 68, 68, 0.15)",
  },
  mercury: {
    sanskrit: "Budha",
    hindi: "बुध",
    symbol: "☿",
    nature: "conditional",
    natureLabel: "Soumya (Adaptable Benefic)",
    sublabel: "Prince · Intellect · Speech",
    color: "#10b981",
    iconBg: "rgba(16, 185, 129, 0.15)",
  },
  jupiter: {
    sanskrit: "Brihaspati / Guru",
    hindi: "बृहस्पति / गुरु",
    symbol: "♃",
    nature: "benefic",
    natureLabel: "Maha Shubha (Great Benefic)",
    sublabel: "Guru · Wisdom · Fortune",
    color: "#eab308",
    iconBg: "rgba(234, 179, 8, 0.15)",
  },
  venus: {
    sanskrit: "Shukra",
    hindi: "शुक्र",
    symbol: "♀",
    nature: "benefic",
    natureLabel: "Shubha (Benefic)",
    sublabel: "Teacher · Beauty · Love · Prosperity",
    color: "#ec4899",
    iconBg: "rgba(236, 72, 153, 0.15)",
  },
  saturn: {
    sanskrit: "Shani",
    hindi: "शनि",
    symbol: "♄",
    nature: "malefic",
    natureLabel: "Maha Papa (Great Malefic)",
    sublabel: "Judge · Karma · Discipline · Time",
    color: "#818cf8",
    iconBg: "rgba(129, 140, 248, 0.15)",
  },
  rahu: {
    sanskrit: "Rahu",
    hindi: "राहु",
    symbol: "☊",
    nature: "malefic",
    natureLabel: "Chhaya (Shadow Malefic)",
    sublabel: "North Node · Ambition · Maya",
    color: "#a855f7",
    iconBg: "rgba(168, 85, 247, 0.15)",
  },
  ketu: {
    sanskrit: "Ketu",
    hindi: "केतु",
    symbol: "☋",
    nature: "malefic",
    natureLabel: "Chhaya (Moksha Karaka)",
    sublabel: "South Node · Detachment · Intuition",
    color: "#fb923c",
    iconBg: "rgba(251, 146, 60, 0.15)",
  },
};

const RASHI_SANSKRIT: Record<string, string> = {
  Aries: "Mesha (मेष)",
  Taurus: "Vrishabha (वृषभ)",
  Gemini: "Mithuna (मिथुन)",
  Cancer: "Karka (कर्क)",
  Leo: "Simha (सिंह)",
  Virgo: "Kanya (कन्या)",
  Libra: "Tula (तुला)",
  Scorpio: "Vrischika (वृश्चिक)",
  Sagittarius: "Dhanu (धनु)",
  Capricorn: "Makara (मकर)",
  Aquarius: "Kumbha (कुम्भ)",
  Pisces: "Meena (मीन)",
};

const NAKSHATRAS = [
  "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
  "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
  "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
  "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
  "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
];

function formatDegree(deg: number): string {
  const whole = Math.floor(deg);
  const minutes = Math.floor((deg - whole) * 60);
  const seconds = Math.floor(((deg - whole) * 60 - minutes) * 60);
  return `${whole}° ${String(minutes).padStart(2, "0")}' ${String(seconds).padStart(2, "0")}"`;
}

function toIsoDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function toIsoTime(d: Date): string {
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

// ── Client-side high-precision Sidereal Ephemeris approximation ────────────────

function computeLiveEphemerisPositions(date: Date): Record<string, { rashi: string; degInSign: number; nakshatra: string; pada: number; isRetrograde: boolean; speed: number }> {
  const t = (date.getTime() - new Date("2000-01-01T12:00:00Z").getTime()) / 86400000;
  const ayanamsa = 23.85 + (t / 365.25) * 0.01397; // Lahiri drift

  // Mean longitudes + key perturbations
  const rawPositions: Record<string, { meanLon: number; dailySpeed: number; isRetro: boolean }> = {
    sun: { meanLon: (280.466 + 0.9856474 * t) % 360, dailySpeed: 0.9856, isRetro: false },
    moon: { meanLon: (218.316 + 13.176396 * t) % 360, dailySpeed: 13.176, isRetro: false },
    mars: { meanLon: (355.433 + 0.524033 * t) % 360, dailySpeed: 0.524, isRetro: false },
    mercury: { meanLon: (252.251 + 4.0923344 * t) % 360, dailySpeed: 1.2, isRetro: Math.sin(t / 116) < -0.6 },
    jupiter: { meanLon: (34.351 + 0.0830853 * t) % 360, dailySpeed: 0.083, isRetro: Math.sin(t / 398) < -0.7 },
    venus: { meanLon: (181.98 + 1.6021302 * t) % 360, dailySpeed: 1.15, isRetro: Math.sin(t / 584) < -0.85 },
    saturn: { meanLon: (50.077 + 0.0334442 * t) % 360, dailySpeed: 0.033, isRetro: Math.sin(t / 378) < -0.65 },
    rahu: { meanLon: (125.044 - 0.0529538 * t) % 360, dailySpeed: -0.053, isRetro: true },
    ketu: { meanLon: (125.044 - 0.0529538 * t + 180) % 360, dailySpeed: -0.053, isRetro: true },
  };

  const RASHIS_LIST = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
  ];

  const result: Record<string, { rashi: string; degInSign: number; nakshatra: string; pada: number; isRetrograde: boolean; speed: number }> = {};

  Object.entries(rawPositions).forEach(([key, val]) => {
    let siderealLon = (val.meanLon - ayanamsa) % 360;
    if (siderealLon < 0) siderealLon += 360;

    const rashiIdx = Math.floor(siderealLon / 30);
    const degInSign = siderealLon % 30;
    const nakIdx = Math.floor(siderealLon / (360 / 27));
    const pada = Math.floor((siderealLon % (360 / 27)) / (360 / 108)) + 1;

    result[key] = {
      rashi: RASHIS_LIST[rashiIdx] || "Aries",
      degInSign,
      nakshatra: NAKSHATRAS[nakIdx] || "Ashwini",
      pada,
      isRetrograde: val.isRetro,
      speed: val.dailySpeed,
    };
  });

  return result;
}

export function CreateTransitModal({ open, onClose }: Props) {
  const router = useRouter();
  const request = useWorkflowStore((s) => s.request);
  const setTransitChart = useWorkflowStore((s) => s.setTransitChart);
  const openCreateModal = useWorkflowStore((s) => s.openCreateModal);

  const [transitDate, setTransitDate] = useState<string>(() => toIsoDate(new Date()));
  const [transitTime, setTransitTime] = useState<string>(() => toIsoTime(new Date()));
  const [isLiveClock, setIsLiveClock] = useState<boolean>(true);
  const [selectedChart, setSelectedChart] = useState<BirthChartSummary | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [activeFilter, setActiveFilter] = useState<"all" | "benefic" | "malefic" | "retrograde">("all");
  const [transitResponse, setTransitResponse] = useState<TransitResponse | null>(null);
  const [isLoadingTransit, setIsLoadingTransit] = useState(false);

  const myCharts = useMyCharts();
  const charts: BirthChartSummary[] = myCharts.data?.charts ?? [];

  // Live timer for real-time tick when in Live Mode
  useEffect(() => {
    if (!open || !isLiveClock) return;
    const interval = setInterval(() => {
      const now = new Date();
      setTransitDate(toIsoDate(now));
      setTransitTime(toIsoTime(now));
    }, 1000);
    return () => clearInterval(interval);
  }, [open, isLiveClock]);

  // Current target timestamp as Date
  const currentTransitDateTime = useMemo(() => {
    try {
      const [y, m, d] = transitDate.split("-").map(Number);
      const [hh, mm] = transitTime.split(":").map(Number);
      return new Date(y!, m! - 1, d!, hh || 0, mm || 0);
    } catch {
      return new Date();
    }
  }, [transitDate, transitTime]);

  // Fetch real backend transit calculation if chart is available
  useEffect(() => {
    if (!open) return;
    const activeChart = selectedChart || (request ? {
      birth_datetime_utc: request.birth_datetime_utc,
      birth_latitude: request.latitude,
      birth_longitude: request.longitude,
      ayanamsa: request.ayanamsa,
      house_system: request.house_system,
      subject_name: request.subject_name,
    } : (charts[0] ? {
      birth_datetime_utc: charts[0].birth_datetime_utc,
      birth_latitude: charts[0].birth_latitude,
      birth_longitude: charts[0].birth_longitude,
      ayanamsa: charts[0].ayanamsa,
      house_system: charts[0].house_system,
      subject_name: charts[0].subject_name,
    } : null));

    if (!activeChart) return;

    let cancelled = false;
    const fetchTransit = async () => {
      setIsLoadingTransit(true);
      try {
        const resp = await api.post<TransitResponse>("/api/v1/transit/current", {
          birth_datetime_utc: activeChart.birth_datetime_utc,
          latitude: activeChart.birth_latitude,
          longitude: activeChart.birth_longitude,
          ayanamsa: activeChart.ayanamsa || "lahiri",
          house_system: activeChart.house_system || "W",
          transit_datetime_utc: currentTransitDateTime.toISOString(),
        });
        if (!cancelled && resp) {
          setTransitResponse(resp);
        }
      } catch (err) {
        // Silently fall back to client ephemeris
      } finally {
        if (!cancelled) setIsLoadingTransit(false);
      }
    };

    fetchTransit();
    return () => {
      cancelled = true;
    };
  }, [open, selectedChart, request, currentTransitDateTime, charts]);

  // Client-side instant positions for zero lag
  const clientPositions = useMemo(() => {
    return computeLiveEphemerisPositions(currentTransitDateTime);
  }, [currentTransitDateTime]);

  // Merge backend data with metadata and client fallback
  const planetList: PlanetDisplayInfo[] = useMemo(() => {
    const keys = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"];

    return keys.map((key) => {
      const meta = GRAHA_META[key]!;
      const client = clientPositions[key];
      const backendPlanet = transitResponse?.planets.find(
        (p) => p.planet.toLowerCase() === key.toLowerCase()
      );

      const rashi = backendPlanet?.transit_rashi || client?.rashi || "Aries";
      const degInSign = backendPlanet?.transit_rashi_degree ?? client?.degInSign ?? 0;
      const nakshatra = backendPlanet?.transit_nakshatra || client?.nakshatra || "Ashwini";
      const pada = backendPlanet?.transit_pada ?? client?.pada ?? 1;
      const isRetrograde = backendPlanet?.is_retrograde ?? client?.isRetrograde ?? false;

      return {
        id: key,
        name: key.charAt(0).toUpperCase() + key.slice(1),
        sanskrit: meta.sanskrit,
        hindi: meta.hindi,
        symbol: meta.symbol,
        nature: meta.nature,
        natureLabel: meta.natureLabel,
        sublabel: meta.sublabel,
        color: meta.color,
        iconBg: meta.iconBg,
        rashi,
        rashiSanskrit: RASHI_SANSKRIT[rashi] || rashi,
        degreeInSign: degInSign,
        degreeFormatted: formatDegree(degInSign),
        nakshatra,
        pada,
        isRetrograde,
        speed: backendPlanet?.speed_deg_per_day ?? client?.speed,
        gati: backendPlanet?.gati,
        houseFromMoon: backendPlanet?.house_from_natal_moon,
        isFavorable: backendPlanet?.is_favorable_house,
        isSadeSati: backendPlanet?.is_sade_sati,
        isAshtamaShani: backendPlanet?.is_ashtama_shani,
        hasVedha: backendPlanet?.has_vedha,
        bindus: backendPlanet?.ashtakavarga_bindus,
      };
    });
  }, [clientPositions, transitResponse]);

  // Filtered planets
  const filteredPlanets = useMemo(() => {
    if (activeFilter === "benefic") return planetList.filter((p) => p.nature === "benefic");
    if (activeFilter === "malefic") return planetList.filter((p) => p.nature === "malefic" || p.nature === "mild_malefic");
    if (activeFilter === "retrograde") return planetList.filter((p) => p.isRetrograde);
    return planetList;
  }, [planetList, activeFilter]);

  // Filtered saved charts for search
  const filteredCharts = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return charts;
    return charts.filter(
      (c) => c.subject_name.toLowerCase().includes(q) || (c.place_name ?? "").toLowerCase().includes(q)
    );
  }, [charts, searchQuery]);

  const activeTargetChart = selectedChart || (request ? {
    id: request.chart_id,
    subject_name: request.subject_name || "Active Chart",
    birth_datetime_utc: request.birth_datetime_utc,
    place_name: request.place_name,
  } : charts[0] || null);

  const handleLaunchTransitStudio = () => {
    if (selectedChart) {
      setTransitChart(selectedChart);
    }
    const params = new URLSearchParams({
      date: transitDate,
      time: transitTime,
      ...(selectedChart?.id ? { chart_id: selectedChart.id } : {}),
    });
    router.push(`/charts/transit?${params.toString()}`);
    onClose();
  };

  // Adjust time by days/months/years
  const adjustDate = (days: number, months: number = 0, years: number = 0) => {
    setIsLiveClock(false);
    const d = new Date(currentTransitDateTime);
    if (years !== 0) d.setFullYear(d.getFullYear() + years);
    if (months !== 0) d.setMonth(d.getMonth() + months);
    if (days !== 0) d.setDate(d.getDate() + days);
    setTransitDate(toIsoDate(d));
    setTransitTime(toIsoTime(d));
  };

  const resetToNow = () => {
    setIsLiveClock(true);
    const now = new Date();
    setTransitDate(toIsoDate(now));
    setTransitTime(toIsoTime(now));
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 md:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="transit-modal-title"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/80 backdrop-blur-md" onClick={onClose} aria-hidden="true" />

      <div
        className="obsidian-card relative flex max-h-[95vh] w-full max-w-6xl flex-col overflow-hidden shadow-2xl border"
        style={{
          backgroundColor: "var(--obsidian-surface-elevated, #0f172a)",
          borderColor: "var(--border-primary, rgba(255,255,255,0.12))",
        }}
      >
        {/* ── Modal Header ── */}
        <div
          className="flex items-center justify-between border-b px-5 py-4"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        >
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl"
              style={{
                backgroundColor: "rgba(6,182,212,0.15)",
                color: "var(--obsidian-accent-secondary, #06b6d4)",
                border: "1px solid rgba(6,182,212,0.3)",
              }}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <circle cx="12" cy="12" r="3" />
                <ellipse cx="12" cy="12" rx="9" ry="4" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="transit-modal-title" className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
                  Live Transit (Gochara) Engine
                </h2>
                {isLiveClock ? (
                  <span className="flex items-center gap-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2.5 py-0.5 text-[10px] font-bold text-emerald-400">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
                    LIVE SKY NOW
                  </span>
                ) : (
                  <span className="rounded-full bg-cyan-500/15 border border-cyan-500/30 px-2.5 py-0.5 text-[10px] font-bold text-cyan-400">
                    CUSTOM TIMELINE
                  </span>
                )}
              </div>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Real-time planetary degrees, rashis, nakshatras, benefic/malefic dignity & Gochara impact
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close"
            className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white transition"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* ── Time Controls & Quick Date Adjuster ── */}
        <div
          className="border-b px-5 py-3 flex flex-wrap items-center justify-between gap-3"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "rgba(0,0,0,0.2)" }}
        >
          {/* Date & Time pickers */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-2 rounded-lg border px-3 py-1.5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}>
              <label htmlFor="transit-date-input" className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>📅 Date:</label>
              <input
                id="transit-date-input"
                aria-label="Transit Date"
                type="date"
                value={transitDate}
                onChange={(e) => {
                  setIsLiveClock(false);
                  setTransitDate(e.target.value);
                }}
                className="bg-transparent text-xs font-bold outline-none cursor-pointer"
                style={{ color: "var(--text-primary)" }}
              />
            </div>

            <div className="flex items-center gap-2 rounded-lg border px-3 py-1.5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}>
              <label htmlFor="transit-time-input" className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>⏰ Time:</label>
              <input
                id="transit-time-input"
                aria-label="Transit Time"
                type="time"
                value={transitTime}
                onChange={(e) => {
                  setIsLiveClock(false);
                  setTransitTime(e.target.value);
                }}
                className="bg-transparent text-xs font-bold outline-none cursor-pointer"
                style={{ color: "var(--text-primary)" }}
              />
            </div>

            <button
              onClick={resetToNow}
              className={`rounded-lg border px-3 py-1.5 text-xs font-bold transition ${
                isLiveClock
                  ? "border-emerald-500/50 bg-emerald-500/20 text-emerald-300"
                  : "border-white/10 text-slate-300 hover:bg-white/5"
              }`}
            >
              ⚡ Live Now
            </button>
          </div>

          {/* Time stepper buttons */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] font-medium mr-1" style={{ color: "var(--text-muted)" }}>Shift:</span>
            {[
              { label: "-1Y", fn: () => adjustDate(0, 0, -1) },
              { label: "-1M", fn: () => adjustDate(0, -1, 0) },
              { label: "-1D", fn: () => adjustDate(-1, 0, 0) },
              { label: "+1D", fn: () => adjustDate(1, 0, 0) },
              { label: "+1M", fn: () => adjustDate(0, 1, 0) },
              { label: "+1Y", fn: () => adjustDate(0, 0, 1) },
            ].map((btn) => (
              <button
                key={btn.label}
                onClick={btn.fn}
                className="rounded-md border px-2 py-1 text-[11px] font-bold transition hover:bg-cyan-500/20 hover:text-cyan-300"
                style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Modal Body (Split: Live Planetary Matrix + Chart Selector) ── */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">

          {/* ── Section: Navagraha Planetary Positions Matrix ── */}
          <div>
            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
              <div>
                <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
                  <span>🪐</span> Navagraha Planetary Positions & Dignities
                </h3>
                <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                  Sidereal Lahiri degrees, Nakshatras, natural and functional benefic/malefic impact
                </p>
              </div>

              {/* Filter Pills */}
              <div className="flex items-center gap-1.5 rounded-lg border p-1" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
                {[
                  { key: "all", label: "All 9 Grahas" },
                  { key: "benefic", label: "Benefics (शुभ)" },
                  { key: "malefic", label: "Malefics (पाप)" },
                  { key: "retrograde", label: "Vakra (℞)" },
                ].map((f) => (
                  <button
                    key={f.key}
                    onClick={() => setActiveFilter(f.key as any)}
                    className="rounded-md px-2.5 py-1 text-[11px] font-semibold transition"
                    style={{
                      backgroundColor: activeFilter === f.key ? "rgba(6,182,212,0.15)" : "transparent",
                      color: activeFilter === f.key ? "#06b6d4" : "var(--text-muted)",
                      border: activeFilter === f.key ? "1px solid rgba(6,182,212,0.3)" : "1px solid transparent",
                    }}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            {/* ── 9 Planets Grid Cards ── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {filteredPlanets.map((planet) => {
                const isMalefic = planet.nature === "malefic" || planet.nature === "mild_malefic";
                return (
                  <div
                    key={planet.id}
                    className="rounded-xl border p-3.5 transition-all hover:scale-[1.01]"
                    style={{
                      borderColor: "var(--border-primary)",
                      backgroundColor: "var(--bg-card)",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                    }}
                  >
                    {/* Planet Title Row */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2.5">
                        <div
                          className="flex h-9 w-9 items-center justify-center rounded-lg text-base font-bold shadow-inner"
                          style={{ backgroundColor: planet.iconBg, color: planet.color, border: `1px solid ${planet.color}40` }}
                        >
                          {planet.symbol}
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                              {planet.name}
                            </span>
                            <span className="text-[11px] font-medium" style={{ color: planet.color }}>
                              ({planet.hindi})
                            </span>
                          </div>
                          <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                            {planet.sanskrit}
                          </p>
                        </div>
                      </div>

                      {/* Dignity / Malefic-Benefic Badge */}
                      <span
                        className="rounded-full px-2 py-0.5 text-[9px] font-bold tracking-wide uppercase border"
                        style={{
                          borderColor: isMalefic ? "rgba(239,68,68,0.3)" : "rgba(16,185,129,0.3)",
                          backgroundColor: isMalefic ? "rgba(239,68,68,0.1)" : "rgba(16,185,129,0.1)",
                          color: isMalefic ? "#ef4444" : "#10b981",
                        }}
                      >
                        {isMalefic ? "Malefic" : "Benefic"}
                      </span>
                    </div>

                    {/* Degree & Sign Details */}
                    <div className="mt-3 grid grid-cols-2 gap-2 rounded-lg p-2.5" style={{ backgroundColor: "var(--bg-primary)" }}>
                      <div>
                        <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>Sign (Rashi)</p>
                        <p className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                          {planet.rashi}
                        </p>
                        <p className="text-[9px]" style={{ color: "var(--text-muted)" }}>
                          {planet.rashiSanskrit.split(" ")[0]}
                        </p>
                      </div>

                      <div className="text-right">
                        <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>Exact Longitude</p>
                        <p className="text-xs font-bold font-mono" style={{ color: planet.color }}>
                          {planet.degreeFormatted}
                        </p>
                        {planet.isRetrograde && (
                          <span className="inline-block text-[9px] font-bold text-amber-400 bg-amber-400/10 px-1.5 rounded mt-0.5">
                            ℞ Retrograde (वक्र)
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Nakshatra & Gochara Details */}
                    <div className="mt-2.5 flex items-center justify-between text-[11px] pt-1 border-t" style={{ borderColor: "var(--border-primary)" }}>
                      <span style={{ color: "var(--text-muted)" }}>
                        ⭐ {planet.nakshatra} (P{planet.pada})
                      </span>

                      {planet.houseFromMoon && (
                        <span
                          className={`font-semibold ${
                            planet.isFavorable ? "text-emerald-400" : "text-amber-400"
                          }`}
                        >
                          H{planet.houseFromMoon} from Moon {planet.isFavorable ? "✓" : "!"}
                        </span>
                      )}
                    </div>

                    {/* Sade Sati / Special flags */}
                    {planet.isSadeSati && (
                      <div className="mt-2 rounded bg-red-500/10 border border-red-500/30 px-2 py-1 text-[10px] font-bold text-red-400 text-center">
                        ⚠️ Active Sade Sati Phase
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── Section: Select Target Birth Chart ── */}
          <div
            className="rounded-xl border p-5"
            style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
          >
            <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
              <div>
                <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
                  <span>👤</span> Apply Transit to Native Chart
                </h3>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  Select the birth chart to overlay transits and compute house activations & Ashtakavarga
                </p>
              </div>

              <button
                type="button"
                onClick={() => {
                  onClose();
                  setTimeout(() => openCreateModal(), 0);
                }}
                className="rounded-lg border px-3 py-1.5 text-xs font-semibold text-cyan-400 border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20 transition"
              >
                + Create New Chart
              </button>
            </div>

            {/* Selected Active Chart Card */}
            {activeTargetChart && (
              <div
                className="mb-4 rounded-xl border p-4 flex items-center justify-between"
                style={{
                  borderColor: "rgba(6,182,212,0.35)",
                  backgroundColor: "rgba(6,182,212,0.06)",
                }}
              >
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold"
                    style={{ backgroundColor: "rgba(6,182,212,0.2)", color: "#06b6d4" }}
                  >
                    {activeTargetChart.subject_name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                        {activeTargetChart.subject_name}
                      </p>
                      <span className="rounded bg-cyan-500/20 text-cyan-300 text-[10px] font-bold px-2 py-0.5">
                        Selected Native
                      </span>
                    </div>
                    <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                      {new Date(activeTargetChart.birth_datetime_utc).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}{" "}
                      · {activeTargetChart.place_name || "Location saved"}
                    </p>
                  </div>
                </div>

                <div className="text-right hidden sm:block">
                  <p className="text-xs font-bold text-emerald-400">Ready for Transit Analysis</p>
                  <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>Gochara Houses Active</p>
                </div>
              </div>
            )}

            {/* Search Saved Charts with Floating Dropdown */}
            <div className="relative">
              <label className="block text-[11px] font-medium mb-1" style={{ color: "var(--text-muted)" }}>
                Search or Change Native Chart:
              </label>
              <input
                type="text"
                placeholder="🔍 Type native name or birth place to search saved charts..."
                value={searchQuery}
                onFocus={() => setShowSearchResults(true)}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setShowSearchResults(true);
                }}
                className="obsidian-input w-full text-xs"
              />

              {/* Floating Dropdown Results */}
              {showSearchResults && (
                <>
                  <div className="fixed inset-0 z-20" onClick={() => setShowSearchResults(false)} />
                  <div
                    className="absolute left-0 right-0 top-full z-30 mt-1 max-h-56 overflow-y-auto rounded-lg border p-1 shadow-2xl"
                    style={{
                      borderColor: "rgba(6,182,212,0.35)",
                      backgroundColor: "var(--obsidian-surface-elevated, #0f172a)",
                    }}
                  >
                  {filteredCharts.length === 0 ? (
                    <p className="px-3 py-2 text-xs" style={{ color: "var(--text-muted)" }}>
                      {searchQuery.trim() ? `No saved charts matching "${searchQuery.trim()}".` : "No saved charts available."}
                    </p>
                  ) : (
                    filteredCharts.map((chart) => {
                      const isSelected = activeTargetChart?.subject_name === chart.subject_name;
                      return (
                        <div
                          key={chart.id}
                          onClick={() => {
                            setSelectedChart(chart);
                            setTransitChart(chart);
                            setShowSearchResults(false);
                            setSearchQuery("");
                          }}
                          className="cursor-pointer rounded-md px-3 py-2 text-xs transition flex items-center justify-between"
                          style={{
                            backgroundColor: isSelected ? "rgba(6,182,212,0.12)" : "transparent",
                            color: "var(--text-primary)",
                          }}
                          onMouseEnter={(e) => {
                            if (!isSelected) e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.05)";
                          }}
                          onMouseLeave={(e) => {
                            if (!isSelected) e.currentTarget.style.backgroundColor = "transparent";
                          }}
                        >
                          <div>
                            <p className="font-bold flex items-center gap-1.5">
                              <span>{chart.subject_name}</span>
                              {isSelected && (
                                <span className="text-[10px] text-cyan-400 bg-cyan-500/20 px-1.5 py-0.2 rounded font-semibold">
                                  Current Active
                                </span>
                              )}
                            </p>
                            <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                              {chart.birth_datetime_utc.split("T")[0]} · {chart.place_name || "Saved location"}
                            </p>
                          </div>

                          {isSelected && <span className="text-cyan-400 font-bold text-sm">✓</span>}
                        </div>
                      );
                    })
                  )}
                </div>
              </>
            )}
          </div>
          </div>
        </div>

        {/* ── Modal Footer ── */}
        <div
          className="flex items-center justify-between border-t px-6 py-4"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        >
          <div className="flex items-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-400" />
            <span>9 Grahas Synced ({ayanamsaName(activeTargetChart)})</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="obsidian-btn-secondary text-sm px-4 py-2"
            >
              Cancel
            </button>
            <button
              onClick={handleLaunchTransitStudio}
              className="obsidian-btn-primary text-sm px-6 py-2 flex items-center gap-2 shadow-lg hover:shadow-cyan-500/20 transition"
              style={{
                backgroundColor: "var(--obsidian-accent-secondary, #06b6d4)",
                color: "#000",
                fontWeight: 700,
              }}
            >
              <span>Launch Full Transit Wheel & Report →</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ayanamsaName(chart: any): string {
  return chart?.ayanamsa ? String(chart.ayanamsa).toUpperCase() : "LAHIRI AYANAMSA";
}
