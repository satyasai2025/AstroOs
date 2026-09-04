'use client';

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Globe,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  BarChart3,
  Download,
  Calendar,
  Sparkles,
  Layers,
  Compass,
} from "@/components/phalita/Icons";

// ─── 1. Benchmark Datasets ───────────────────────────────────────────────────

interface RainfallAuditRow {
  year: number;
  actualRainfall: string;
  actualNumeric: number;
  category: "EXCESS_FLOOD" | "SEVERE_DROUGHT";
  ardraDate: string;
  dominantNadi: string;
  predRainfallPct: string;
  predIntensity: string;
  waterGrahas: string;
  fireGrahas: string;
  result: "MATCH" | "DIVERGENCE";
}

const HISTORICAL_RAINFALL_ROWS: RainfallAuditRow[] = [
  { year: 1917, actualRainfall: "+23.0%", actualNumeric: 23.0, category: "EXCESS_FLOOD", ardraDate: "1917-06-22", dominantNadi: "JALA", predRainfallPct: "75.0%", predIntensity: "TORRENTIAL", waterGrahas: "MOON, SATURN, RAHU, VENUS", fireGrahas: "JUPITER", result: "MATCH" },
  { year: 1956, actualRainfall: "+25.0%", actualNumeric: 25.0, category: "EXCESS_FLOOD", ardraDate: "1956-06-21", dominantNadi: "VAYU", predRainfallPct: "75.0%", predIntensity: "TORRENTIAL", waterGrahas: "MOON, JUPITER, SATURN, RAHU", fireGrahas: "None", result: "MATCH" },
  { year: 1961, actualRainfall: "+22.0%", actualNumeric: 22.0, category: "EXCESS_FLOOD", ardraDate: "1961-06-22", dominantNadi: "SAUMYA", predRainfallPct: "55.0%", predIntensity: "MODERATE_SHOWERS", waterGrahas: "MARS, RAHU, SATURN", fireGrahas: "JUPITER", result: "MATCH" },
  { year: 1975, actualRainfall: "+15.2%", actualNumeric: 15.2, category: "EXCESS_FLOOD", ardraDate: "1975-06-22", dominantNadi: "CHANDA", predRainfallPct: "65.0%", predIntensity: "MODERATE_SHOWERS", waterGrahas: "MOON, VENUS, RAHU, SATURN", fireGrahas: "MARS, JUPITER, KETU", result: "MATCH" },
  { year: 1983, actualRainfall: "+13.0%", actualNumeric: 13.0, category: "EXCESS_FLOOD", ardraDate: "1983-06-22", dominantNadi: "DAHANA", predRainfallPct: "52.5%", predIntensity: "SCANTY", waterGrahas: "VENUS, KETU, MOON, JUPITER", fireGrahas: "MARS, SATURN, RAHU", result: "MATCH" },
  { year: 1988, actualRainfall: "+19.4%", actualNumeric: 19.4, category: "EXCESS_FLOOD", ardraDate: "1988-06-21", dominantNadi: "DAHANA", predRainfallPct: "52.5%", predIntensity: "SCANTY", waterGrahas: "SATURN, MOON, KETU", fireGrahas: "SUN, MERCURY, VENUS, JUPITER", result: "MATCH" },
  { year: 1994, actualRainfall: "+10.5%", actualNumeric: 10.5, category: "EXCESS_FLOOD", ardraDate: "1994-06-22", dominantNadi: "SAUMYA", predRainfallPct: "60.0%", predIntensity: "MODERATE_SHOWERS", waterGrahas: "MOON, VENUS, RAHU", fireGrahas: "MARS, KETU", result: "MATCH" },
  { year: 2019, actualRainfall: "+10.0%", actualNumeric: 10.0, category: "EXCESS_FLOOD", ardraDate: "2019-06-22", dominantNadi: "NEERA", predRainfallPct: "85.0%", predIntensity: "HEAVY_DOWNPOUR", waterGrahas: "JUPITER, SATURN, KETU, MARS, MERCURY, RAHU", fireGrahas: "MOON", result: "MATCH" },
  { year: 2020, actualRainfall: "+8.7%", actualNumeric: 8.7, category: "EXCESS_FLOOD", ardraDate: "2020-06-21", dominantNadi: "NEERA", predRainfallPct: "55.0%", predIntensity: "MODERATE_SHOWERS", waterGrahas: "KETU, MERCURY, JUPITER, SATURN", fireGrahas: "SUN, RAHU", result: "MATCH" },
  { year: 1970, actualRainfall: "+11.3%", actualNumeric: 11.3, category: "EXCESS_FLOOD", ardraDate: "1970-06-22", dominantNadi: "VAYU", predRainfallPct: "57.5%", predIntensity: "MODERATE_SHOWERS", waterGrahas: "KETU, VENUS", fireGrahas: "MOON, JUPITER", result: "MATCH" },
  { year: 1877, actualRainfall: "-28.0%", actualNumeric: -28.0, category: "SEVERE_DROUGHT", ardraDate: "1877-06-21", dominantNadi: "VAYU", predRainfallPct: "70.0%", predIntensity: "MODERATE_SHOWERS", waterGrahas: "JUPITER, KETU, VENUS", fireGrahas: "None", result: "DIVERGENCE" },
  { year: 1899, actualRainfall: "-26.2%", actualNumeric: -26.2, category: "SEVERE_DROUGHT", ardraDate: "1899-06-22", dominantNadi: "SAUMYA", predRainfallPct: "67.5%", predIntensity: "MODERATE_SHOWERS", waterGrahas: "MOON, MARS, SATURN, RAHU", fireGrahas: "None", result: "DIVERGENCE" },
  { year: 1918, actualRainfall: "-24.9%", actualNumeric: -24.9, category: "SEVERE_DROUGHT", ardraDate: "1918-06-22", dominantNadi: "DAHANA", predRainfallPct: "67.5%", predIntensity: "MODERATE_SHOWERS", waterGrahas: "SATURN, RAHU, MOON, MARS", fireGrahas: "MERCURY, JUPITER, KETU, VENUS", result: "DIVERGENCE" },
  { year: 1965, actualRainfall: "-18.0%", actualNumeric: -18.0, category: "SEVERE_DROUGHT", ardraDate: "1965-06-21", dominantNadi: "VAYU", predRainfallPct: "52.5%", predIntensity: "SCANTY", waterGrahas: "KETU, MARS, VENUS", fireGrahas: "SUN", result: "DIVERGENCE" },
  { year: 1972, actualRainfall: "-23.9%", actualNumeric: -23.9, category: "SEVERE_DROUGHT", ardraDate: "1972-06-21", dominantNadi: "NEERA", predRainfallPct: "80.0%", predIntensity: "HEAVY_DOWNPOUR", waterGrahas: "JUPITER, KETU, MARS, MERCURY, RAHU", fireGrahas: "VENUS", result: "DIVERGENCE" },
  { year: 1979, actualRainfall: "-19.0%", actualNumeric: -19.0, category: "SEVERE_DROUGHT", ardraDate: "1979-06-22", dominantNadi: "VAYU", predRainfallPct: "65.0%", predIntensity: "MODERATE_SHOWERS", waterGrahas: "JUPITER, SATURN, RAHU, MERCURY", fireGrahas: "MARS", result: "DIVERGENCE" },
  { year: 1987, actualRainfall: "-19.4%", actualNumeric: -19.4, category: "SEVERE_DROUGHT", ardraDate: "1987-06-22", dominantNadi: "CHANDA", predRainfallPct: "52.5%", predIntensity: "SCANTY", waterGrahas: "SATURN, MARS, MERCURY", fireGrahas: "JUPITER, RAHU", result: "DIVERGENCE" },
  { year: 2002, actualRainfall: "-19.2%", actualNumeric: -19.2, category: "SEVERE_DROUGHT", ardraDate: "2002-06-22", dominantNadi: "VAYU", predRainfallPct: "77.5%", predIntensity: "TORRENTIAL", waterGrahas: "KETU, MOON, VENUS, MARS, JUPITER", fireGrahas: "SATURN", result: "DIVERGENCE" },
  { year: 2009, actualRainfall: "-21.8%", actualNumeric: -21.8, category: "SEVERE_DROUGHT", ardraDate: "2009-06-21", dominantNadi: "VAYU", predRainfallPct: "40.0%", predIntensity: "SCANTY", waterGrahas: "SATURN, KETU", fireGrahas: "SUN, JUPITER", result: "MATCH" },
  { year: 2014, actualRainfall: "-12.0%", actualNumeric: -12.0, category: "SEVERE_DROUGHT", ardraDate: "2014-06-22", dominantNadi: "CHANDA", predRainfallPct: "47.5%", predIntensity: "SCANTY", waterGrahas: "JUPITER, SATURN", fireGrahas: "MERCURY, RAHU, MOON, VENUS, KETU", result: "MATCH" },
];

interface MultiIngressRow {
  year: number;
  actualRainfall: string;
  groundTruth: "EXCESS" | "DROUGHT";
  confluenceScore: number;
  predictedCategory: string;
  chaitra: number;
  meshaMeru: number;
  ardra: number;
  saptaNadi: number;
  result: "CORRECT" | "DIVERGENT";
  split: "OUT_OF_SAMPLE (1961-2020)" | "CALIBRATION (1877-1960)";
}

const MULTI_INGRESS_ROWS: MultiIngressRow[] = [
  { year: 1961, actualRainfall: "+22.0%", groundTruth: "EXCESS", confluenceScore: 0.37, predictedCategory: "EXCESS_FLOOD", chaitra: 0.35, meshaMeru: 0.6, ardra: 0.3, saptaNadi: 0.2, result: "CORRECT", split: "OUT_OF_SAMPLE (1961-2020)" },
  { year: 1965, actualRainfall: "-18.0%", groundTruth: "DROUGHT", confluenceScore: 0.205, predictedCategory: "NORMAL_BOUNTIFUL", chaitra: 0.35, meshaMeru: -0.2, ardra: 0.3, saptaNadi: 0.45, result: "DIVERGENT", split: "OUT_OF_SAMPLE (1961-2020)" },
  { year: 1972, actualRainfall: "-23.9%", groundTruth: "DROUGHT", confluenceScore: 0.4, predictedCategory: "EXCESS_FLOOD", chaitra: 0.35, meshaMeru: 0.2, ardra: 0.3, saptaNadi: 0.7, result: "DIVERGENT", split: "OUT_OF_SAMPLE (1961-2020)" },
  { year: 1975, actualRainfall: "+15.2%", groundTruth: "EXCESS", confluenceScore: 0.265, predictedCategory: "EXCESS_FLOOD", chaitra: 0.35, meshaMeru: 0.6, ardra: -0.3, saptaNadi: 0.25, result: "CORRECT", split: "OUT_OF_SAMPLE (1961-2020)" },
  { year: 1987, actualRainfall: "-19.4%", groundTruth: "DROUGHT", confluenceScore: 0.2, predictedCategory: "NORMAL_BOUNTIFUL", chaitra: -0.35, meshaMeru: 0.6, ardra: 0.3, saptaNadi: 0.1, result: "DIVERGENT", split: "OUT_OF_SAMPLE (1961-2020)" },
  { year: 1988, actualRainfall: "+19.4%", groundTruth: "EXCESS", confluenceScore: 0.095, predictedCategory: "NORMAL_BOUNTIFUL", chaitra: -0.35, meshaMeru: 0.6, ardra: -0.3, saptaNadi: 0.15, result: "CORRECT", split: "OUT_OF_SAMPLE (1961-2020)" },
  { year: 1994, actualRainfall: "+10.5%", groundTruth: "EXCESS", confluenceScore: 0.205, predictedCategory: "NORMAL_BOUNTIFUL", chaitra: 0.35, meshaMeru: 0.0, ardra: 0.3, saptaNadi: 0.25, result: "CORRECT", split: "OUT_OF_SAMPLE (1961-2020)" },
  { year: 2002, actualRainfall: "-19.2%", groundTruth: "DROUGHT", confluenceScore: 0.085, predictedCategory: "NORMAL_BOUNTIFUL", chaitra: 0.35, meshaMeru: -0.2, ardra: -0.3, saptaNadi: 0.45, result: "DIVERGENT", split: "OUT_OF_SAMPLE (1961-2020)" },
  { year: 2009, actualRainfall: "-21.8%", groundTruth: "DROUGHT", confluenceScore: -0.07, predictedCategory: "MODERATE_DEFICIENT", chaitra: -0.35, meshaMeru: 0.2, ardra: -0.3, saptaNadi: 0.0, result: "CORRECT", split: "OUT_OF_SAMPLE (1961-2020)" },
  { year: 2019, actualRainfall: "+10.0%", groundTruth: "EXCESS", confluenceScore: 0.37, predictedCategory: "EXCESS_FLOOD", chaitra: 0.35, meshaMeru: 0.4, ardra: -0.3, saptaNadi: 0.8, result: "CORRECT", split: "OUT_OF_SAMPLE (1961-2020)" },
  { year: 1877, actualRainfall: "-28.0%", groundTruth: "DROUGHT", confluenceScore: 0.385, predictedCategory: "EXCESS_FLOOD", chaitra: 0.35, meshaMeru: 0.6, ardra: 0.3, saptaNadi: 0.25, result: "DIVERGENT", split: "CALIBRATION (1877-1960)" },
  { year: 1899, actualRainfall: "-26.2%", groundTruth: "DROUGHT", confluenceScore: 0.155, predictedCategory: "NORMAL_BOUNTIFUL", chaitra: -0.35, meshaMeru: 0.4, ardra: -0.3, saptaNadi: 0.55, result: "DIVERGENT", split: "CALIBRATION (1877-1960)" },
  { year: 1917, actualRainfall: "+23.0%", groundTruth: "EXCESS", confluenceScore: 0.35, predictedCategory: "EXCESS_FLOOD", chaitra: -0.35, meshaMeru: 0.6, ardra: 0.3, saptaNadi: 0.6, result: "CORRECT", split: "CALIBRATION (1877-1960)" },
  { year: 1918, actualRainfall: "-24.9%", groundTruth: "DROUGHT", confluenceScore: 0.14, predictedCategory: "NORMAL_BOUNTIFUL", chaitra: -0.35, meshaMeru: 0.6, ardra: 0.3, saptaNadi: -0.1, result: "DIVERGENT", split: "CALIBRATION (1877-1960)" },
  { year: 1920, actualRainfall: "-15.8%", groundTruth: "DROUGHT", confluenceScore: 0.35, predictedCategory: "EXCESS_FLOOD", chaitra: -0.35, meshaMeru: 0.6, ardra: 0.3, saptaNadi: 0.6, result: "DIVERGENT", split: "CALIBRATION (1877-1960)" },
  { year: 1933, actualRainfall: "+14.5%", groundTruth: "EXCESS", confluenceScore: 0.32, predictedCategory: "EXCESS_FLOOD", chaitra: -0.35, meshaMeru: 0.4, ardra: 0.3, saptaNadi: 0.7, result: "CORRECT", split: "CALIBRATION (1877-1960)" },
  { year: 1942, actualRainfall: "+13.8%", groundTruth: "EXCESS", confluenceScore: 0.265, predictedCategory: "EXCESS_FLOOD", chaitra: 0.35, meshaMeru: 0.6, ardra: -0.3, saptaNadi: 0.25, result: "CORRECT", split: "CALIBRATION (1877-1960)" },
  { year: 1951, actualRainfall: "-18.7%", groundTruth: "DROUGHT", confluenceScore: 0.28, predictedCategory: "EXCESS_FLOOD", chaitra: 0.35, meshaMeru: 0.6, ardra: 0.3, saptaNadi: -0.1, result: "DIVERGENT", split: "CALIBRATION (1877-1960)" },
  { year: 1956, actualRainfall: "+25.0%", groundTruth: "EXCESS", confluenceScore: 0.46, predictedCategory: "EXCESS_FLOOD", chaitra: 0.35, meshaMeru: 0.4, ardra: 0.3, saptaNadi: 0.7, result: "CORRECT", split: "CALIBRATION (1877-1960)" },
  { year: 1959, actualRainfall: "+10.4%", groundTruth: "EXCESS", confluenceScore: 0.43, predictedCategory: "EXCESS_FLOOD", chaitra: 0.35, meshaMeru: 0.0, ardra: 0.3, saptaNadi: 1.0, result: "CORRECT", split: "CALIBRATION (1877-1960)" },
];

interface SeasonalRow {
  year: number;
  actualRainfall: string;
  groundTruth: "DROUGHT" | "EXCESS";
  earlySeason: number;
  midSeason: number;
  rollingConfluence: number;
  breakDetected: boolean;
  predictedCategory: string;
  result: "CORRECT" | "DIVERGENT";
}

const SEASONAL_ROWS: SeasonalRow[] = [
  { year: 1901, actualRainfall: "-16.0%", groundTruth: "DROUGHT", earlySeason: 0.433, midSeason: 1.0, rollingConfluence: 0.773, breakDetected: false, predictedCategory: "EXCESS_FLOOD", result: "DIVERGENT" },
  { year: 1904, actualRainfall: "-12.4%", groundTruth: "DROUGHT", earlySeason: -0.87, midSeason: 0.5, rollingConfluence: -0.048, breakDetected: false, predictedCategory: "MODERATE_DEFICIENT", result: "CORRECT" },
  { year: 1905, actualRainfall: "-16.3%", groundTruth: "DROUGHT", earlySeason: -0.235, midSeason: 0.64, rollingConfluence: 0.29, breakDetected: false, predictedCategory: "EXCESS_FLOOD", result: "DIVERGENT" },
  { year: 1911, actualRainfall: "-14.6%", groundTruth: "DROUGHT", earlySeason: -0.397, midSeason: 0.01, rollingConfluence: -0.153, breakDetected: false, predictedCategory: "SEVERE_DROUGHT", result: "CORRECT" },
  { year: 1974, actualRainfall: "-12.1%", groundTruth: "DROUGHT", earlySeason: -0.37, midSeason: 0.46, rollingConfluence: 0.128, breakDetected: false, predictedCategory: "NORMAL_BOUNTIFUL", result: "DIVERGENT" },
  { year: 2018, actualRainfall: "-9.1%", groundTruth: "DROUGHT", earlySeason: -0.21, midSeason: 0.78, rollingConfluence: 0.384, breakDetected: false, predictedCategory: "EXCESS_FLOOD", result: "DIVERGENT" },
  { year: 1916, actualRainfall: "+12.3%", groundTruth: "EXCESS", earlySeason: -0.145, midSeason: 0.61, rollingConfluence: 0.308, breakDetected: false, predictedCategory: "EXCESS_FLOOD", result: "CORRECT" },
  { year: 1938, actualRainfall: "+10.2%", groundTruth: "EXCESS", earlySeason: -0.575, midSeason: 0.07, rollingConfluence: -0.188, breakDetected: false, predictedCategory: "SEVERE_DROUGHT", result: "DIVERGENT" },
  { year: 1947, actualRainfall: "+11.0%", groundTruth: "EXCESS", earlySeason: 0.152, midSeason: 0.67, rollingConfluence: 0.463, breakDetected: false, predictedCategory: "EXCESS_FLOOD", result: "CORRECT" },
  { year: 1964, actualRainfall: "+10.5%", groundTruth: "EXCESS", earlySeason: -0.562, midSeason: 0.14, rollingConfluence: -0.141, breakDetected: false, predictedCategory: "MODERATE_DEFICIENT", result: "DIVERGENT" },
  { year: 1990, actualRainfall: "+10.0%", groundTruth: "EXCESS", earlySeason: -0.395, midSeason: 0.34, rollingConfluence: 0.046, breakDetected: false, predictedCategory: "MODERATE_DEFICIENT", result: "DIVERGENT" },
  { year: 2013, actualRainfall: "+5.6%", groundTruth: "EXCESS", earlySeason: -0.082, midSeason: 0.68, rollingConfluence: 0.375, breakDetected: false, predictedCategory: "EXCESS_FLOOD", result: "CORRECT" },
];

interface AuditMetricCardProps {
  label: string;
  value: string;
  sublabel: string;
  icon: React.ReactNode;
  variant?: "default" | "emerald" | "rose" | "cyan";
}

function AuditMetricCard({ label, value, sublabel, icon, variant = "default" }: AuditMetricCardProps) {
  const styles = {
    default: {
      border: "border-slate-800",
      gradient: "from-slate-900/90 to-slate-950/90",
      valColor: "text-white",
      subColor: "text-slate-400",
      labelColor: "text-slate-400",
    },
    emerald: {
      border: "border-emerald-900/40",
      gradient: "from-emerald-950/30 to-slate-950/90",
      valColor: "text-emerald-400",
      subColor: "text-emerald-400/80",
      labelColor: "text-emerald-400",
    },
    rose: {
      border: "border-rose-900/40",
      gradient: "from-rose-950/30 to-slate-950/90",
      valColor: "text-rose-400",
      subColor: "text-rose-400/80",
      labelColor: "text-rose-400",
    },
    cyan: {
      border: "border-cyan-900/40",
      gradient: "from-cyan-950/30 to-slate-950/90",
      valColor: "text-cyan-400",
      subColor: "text-cyan-300/80",
      labelColor: "text-cyan-400",
    },
  }[variant];

  return (
    <div className={`p-5 rounded-2xl border ${styles.border} bg-gradient-to-b ${styles.gradient} backdrop-blur-md shadow-xl transition-all hover:scale-[1.01]`}>
      <div className="flex items-center justify-between">
        <span className={`text-xs uppercase font-bold ${styles.labelColor}`}>{label}</span>
        {icon}
      </div>
      <div className={`text-3xl font-extrabold ${styles.valColor} mt-2`}>{value}</div>
      <div className={`text-xs ${styles.subColor} mt-1`}>{sublabel}</div>
    </div>
  );
}

export default function MediniAuditDashboard() {
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<"rainfall" | "multi_ingress" | "seasonal" | "negative_results" | "live_verify">("rainfall");
  
  // Filter & Search
  const [filterRainfall, setFilterRainfall] = useState<"ALL" | "EXCESS_FLOOD" | "SEVERE_DROUGHT" | "MATCH" | "DIVERGENCE">("ALL");
  const [searchYear, setSearchYear] = useState<string>("");

  // Table Sort Config
  const [sortKey, setSortKey] = useState<keyof RainfallAuditRow>("year");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  // Live Kurma State
  const [liveKurma, setLiveKurma] = useState<any>(null);
  const [loadingKurma, setLoadingKurma] = useState<boolean>(true);

  useEffect(() => {
    setMounted(true);
    async function loadLiveVerification() {
      setLoadingKurma(true);
      try {
        const res = await fetch("http://localhost:8000/api/v1/kurma-chakra");
        if (res.ok) {
          const data = await res.json();
          setLiveKurma(data);
        }
      } catch (e) {
        console.warn("Could not load live kurma-chakra state for audit view:", e);
      } finally {
        setLoadingKurma(false);
      }
    }
    loadLiveVerification();
  }, []);

  const handleSort = (key: keyof RainfallAuditRow) => {
    if (sortKey === key) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  // Filtered & Sorted Rainfall Data
  const sortedRainfall = useMemo(() => {
    return [...HISTORICAL_RAINFALL_ROWS]
      .filter((r) => {
        if (searchYear && !r.year.toString().includes(searchYear.trim())) return false;
        if (filterRainfall === "ALL") return true;
        if (filterRainfall === "EXCESS_FLOOD") return r.category === "EXCESS_FLOOD";
        if (filterRainfall === "SEVERE_DROUGHT") return r.category === "SEVERE_DROUGHT";
        if (filterRainfall === "MATCH") return r.result === "MATCH";
        if (filterRainfall === "DIVERGENCE") return r.result === "DIVERGENCE";
        return true;
      })
      .sort((a, b) => {
        const valA = a[sortKey];
        const valB = b[sortKey];
        if (valA < valB) return sortDirection === "asc" ? -1 : 1;
        if (valA > valB) return sortDirection === "asc" ? 1 : -1;
        return 0;
      });
  }, [filterRainfall, searchYear, sortKey, sortDirection]);

  // Export CSV Function
  const handleExportCSV = (data: any[], filename: string) => {
    if (!data.length) return;
    const headers = Object.keys(data[0]);
    const csvRows = [
      headers.join(","),
      ...data.map((row) =>
        headers.map((h) => `"${String(row[h] ?? "").replace(/"/g, '""')}"`).join(",")
      ),
    ];
    const blob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${filename}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] space-y-6 pb-20 font-sans">
      {/* 🌌 1. Cosmic Observatory Header Hero */}
      <div className="relative overflow-hidden rounded-2xl border border-cyan-900/50 bg-gradient-to-br from-[var(--bg-card)] via-[#0a1428] to-[#0f1d3a] p-6 sm:p-8 shadow-2xl text-white">
        {/* Subtle grid background */}
        <div className="absolute inset-0 bg-[radial-gradient(#0284c7_1px,transparent_1px)] [background-size:20px_20px] opacity-10 pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs font-bold tracking-widest uppercase">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span>AstroOS Empirical Research &amp; Falsification Registry</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-300 via-sky-200 to-indigo-300 bg-clip-text text-transparent">
              Medini Jyotisha Audit Benchmarks
            </h1>
            <p className="text-sm text-slate-300 font-light max-w-3xl leading-relaxed">
              Historical validation, out-of-sample splits, and boundary falsification across <strong>150 years of IITM &amp; IMD instrumental ground-truth records (1877–2023)</strong>.
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/medini"
              className="px-4 py-2.5 rounded-xl border border-cyan-700/60 bg-cyan-950/40 hover:bg-cyan-900/60 text-cyan-200 text-xs font-mono font-semibold flex items-center gap-2 transition-all shadow-md hover:border-cyan-400"
            >
              <Globe className="w-4 h-4 text-cyan-400" />
              <span>Live Predictive Console</span>
            </Link>

            <button
              onClick={() => {
                const url = `http://localhost:8000/api/v1/excel/export-kurma`;
                window.open(url, "_blank");
              }}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-mono font-bold flex items-center gap-2 shadow-lg shadow-emerald-900/30 transition-all cursor-pointer"
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span>Export Excel Template</span>
            </button>
          </div>
        </div>

        {/* Isolation Alert */}
        <div className="mt-6 p-4 rounded-xl border border-amber-500/30 bg-amber-950/20 backdrop-blur-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 font-mono text-xs text-amber-200">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-amber-400 shrink-0" />
            <div>
              <span className="font-bold uppercase tracking-wider text-amber-300">Strict Research Isolation Contract: </span>
              <span className="text-amber-200/90">All macro Samhita weather rules are segregated in experimental research and never used for individual natal life guidance.</span>
            </div>
          </div>
          <span className="px-3 py-1 rounded-md bg-amber-500/20 border border-amber-400/30 font-bold uppercase tracking-widest text-[10px] text-amber-300 whitespace-nowrap">
            FROZEN EXPERIMENTAL
          </span>
        </div>
      </div>

      {/* 📊 2. Prominent Metric Dashboard Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
        <AuditMetricCard
          label="Total Benchmark Cohort"
          value="44 Years"
          sublabel="1877–2023 IITM/IMD Registry"
          icon={<Calendar className="w-4 h-4 text-cyan-400" />}
          variant="default"
        />

        <AuditMetricCard
          label="Excess / Flood Accuracy"
          value="10/10 (100%)"
          sublabel="Water Nadi Occupancy Sensitivity"
          icon={<TrendingUp className="w-4 h-4 text-emerald-400" />}
          variant="emerald"
        />

        <AuditMetricCard
          label="Severe Drought Accuracy"
          value="2/10 (20%)"
          sublabel="Early Snapshot Masking Vulnerability"
          icon={<AlertCircle className="w-4 h-4 text-rose-400" />}
          variant="rose"
        />

        <AuditMetricCard
          label="Multi-Ingress OOS Split"
          value="60.0%"
          sublabel="1961–2020 Untouched Test Cohort"
          icon={<BarChart3 className="w-4 h-4 text-cyan-400" />}
          variant="cyan"
        />
      </div>

      {/* 📈 3. Visual Interactive SVG Benchmark Accuracy Chart */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-md shadow-xl font-mono">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Empirical Accuracy &amp; Sensitivity Spectrum Comparison
            </h3>
            <p className="text-xs text-slate-400">Comparing classical snapshot accuracy across experimental phases</p>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5 text-emerald-400"><span className="w-2.5 h-2.5 rounded-sm bg-emerald-500"></span> Floods</span>
            <span className="flex items-center gap-1.5 text-rose-400"><span className="w-2.5 h-2.5 rounded-sm bg-rose-500"></span> Droughts</span>
            <span className="flex items-center gap-1.5 text-cyan-400"><span className="w-2.5 h-2.5 rounded-sm bg-cyan-500"></span> Overall</span>
          </div>
        </div>

        {/* SVG Responsive Chart */}
        <div className="w-full h-44 flex items-end justify-around gap-6 pt-6 pb-2 px-4 border-t border-slate-800">
          {/* Bar 1: Ardra Pravesha Floods */}
          <div className="flex flex-col items-center gap-2 h-full justify-end flex-1 max-w-[120px]">
            <span className="text-xs font-bold text-emerald-400">100%</span>
            <div className="w-full bg-emerald-500/80 rounded-t-lg transition-all" style={{ height: "100%" }}></div>
            <span className="text-[11px] text-slate-400 text-center">Ardra Floods</span>
          </div>

          {/* Bar 2: Ardra Pravesha Droughts */}
          <div className="flex flex-col items-center gap-2 h-full justify-end flex-1 max-w-[120px]">
            <span className="text-xs font-bold text-rose-400">20%</span>
            <div className="w-full bg-rose-500/80 rounded-t-lg transition-all" style={{ height: "20%" }}></div>
            <span className="text-[11px] text-slate-400 text-center">Ardra Droughts</span>
          </div>

          {/* Bar 3: Ardra Overall */}
          <div className="flex flex-col items-center gap-2 h-full justify-end flex-1 max-w-[120px]">
            <span className="text-xs font-bold text-cyan-400">60%</span>
            <div className="w-full bg-cyan-500/80 rounded-t-lg transition-all" style={{ height: "60%" }}></div>
            <span className="text-[11px] text-slate-400 text-center">Ardra Overall</span>
          </div>

          {/* Bar 4: Multi-Ingress OOS */}
          <div className="flex flex-col items-center gap-2 h-full justify-end flex-1 max-w-[120px]">
            <span className="text-xs font-bold text-cyan-400">60%</span>
            <div className="w-full bg-cyan-500/80 rounded-t-lg transition-all" style={{ height: "60%" }}></div>
            <span className="text-[11px] text-slate-400 text-center">Multi-Ingress OOS</span>
          </div>

          {/* Bar 5: 5-Stage Seasonal Dynamic */}
          <div className="flex flex-col items-center gap-2 h-full justify-end flex-1 max-w-[120px]">
            <span className="text-xs font-bold text-amber-400">41.7%</span>
            <div className="w-full bg-amber-500/80 rounded-t-lg transition-all" style={{ height: "41.7%" }}></div>
            <span className="text-[11px] text-slate-400 text-center">5-Stage Seasonal</span>
          </div>
        </div>
      </div>

      {/* 🧭 4. Glassmorphic Segmented Control Tab Navigation */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Desktop Pill Tabs */}
        <div className="hidden md:inline-flex bg-slate-900/90 backdrop-blur-md rounded-2xl p-1.5 border border-slate-800 shadow-xl">
          {[
            { id: "rainfall", label: "01 Historical Monsoon (20 Yrs)", icon: "🌧️" },
            { id: "multi_ingress", label: "02 Multi-Ingress OOS Split", icon: "🌐" },
            { id: "seasonal", label: "03 Seasonal 5-Stage Tracking", icon: "🔄" },
            { id: "negative_results", label: "04 Negative Results & Falsification", icon: "🔬" },
            { id: "live_verify", label: "05 Live API Sanity Audit", icon: "⚡" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2.5 rounded-xl text-xs font-mono font-bold transition-all cursor-pointer flex items-center gap-2 ${
                activeTab === tab.id
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-500/10"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Mobile Dropdown */}
        <div className="md:hidden w-full">
          <select
            value={activeTab}
            onChange={(e) => setActiveTab(e.target.value as any)}
            className="w-full bg-slate-900 border border-slate-700 text-cyan-300 font-mono text-xs rounded-xl p-3 focus:outline-none"
          >
            <option value="rainfall">🌧️ 01 Historical Monsoon (20 Yrs)</option>
            <option value="multi_ingress">🌐 02 Multi-Ingress OOS Split</option>
            <option value="seasonal">🔄 03 Seasonal 5-Stage Tracking</option>
            <option value="negative_results">🔬 04 Negative Results &amp; Falsification</option>
            <option value="live_verify">⚡ 05 Live API Sanity Audit</option>
          </select>
        </div>

        {/* Export dataset button */}
        <button
          onClick={() => {
            if (activeTab === "rainfall") handleExportCSV(HISTORICAL_RAINFALL_ROWS, "AstroOS_Medini_Rainfall_20Yrs");
            else if (activeTab === "multi_ingress") handleExportCSV(MULTI_INGRESS_ROWS, "AstroOS_Medini_MultiIngress_OOS");
            else if (activeTab === "seasonal") handleExportCSV(SEASONAL_ROWS, "AstroOS_Medini_Seasonal_Tracking");
            else alert("CSV export available on tabs 01, 02, and 03.");
          }}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs font-semibold flex items-center justify-center gap-2 border border-slate-700 transition-all cursor-pointer shrink-0"
        >
          <Download className="w-3.5 h-3.5 text-cyan-400" />
          <span>Export Tab as CSV</span>
        </button>
      </div>

      {/* 🌟 Tab 1: Historical Monsoon (20 Years) */}
      {activeTab === "rainfall" && (
        <div className="space-y-4">
          {/* Controls & Filter Toolbar */}
          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/80 backdrop-blur flex flex-col sm:flex-row items-center justify-between gap-3 font-mono text-xs">
            <div className="flex flex-wrap items-center gap-1.5 w-full sm:w-auto">
              <span className="text-slate-400 font-bold mr-1">FILTER:</span>
              {(["ALL", "EXCESS_FLOOD", "SEVERE_DROUGHT", "MATCH", "DIVERGENCE"] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setFilterRainfall(mode)}
                  className={`px-3 py-1.5 rounded-lg border transition-all cursor-pointer font-bold text-[11px] ${
                    filterRainfall === mode
                      ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/60"
                      : "bg-slate-800/60 border-slate-700 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {mode.replace("_", " ")}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <input
                type="text"
                placeholder="Search year (e.g. 1987)..."
                value={searchYear}
                onChange={(e) => setSearchYear(e.target.value)}
                className="w-full sm:w-48 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-950 text-white text-xs font-mono focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
              <span className="text-slate-400 font-bold whitespace-nowrap text-[11px]">
                {sortedRainfall.length} / {HISTORICAL_RAINFALL_ROWS.length} Yrs
              </span>
            </div>
          </div>

          {/* Sortable Interactive Table */}
          <div className="border border-slate-800 rounded-2xl overflow-hidden shadow-2xl bg-slate-900/60 backdrop-blur">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="uppercase text-[10px] tracking-wider border-b border-slate-800 bg-slate-950/80 text-slate-400 select-none">
                  <tr>
                    <th onClick={() => handleSort("year")} className="py-3.5 px-4 cursor-pointer hover:bg-slate-800 transition-colors">
                      Year {sortKey === "year" && (sortDirection === "asc" ? "▲" : "▼")}
                    </th>
                    <th onClick={() => handleSort("actualNumeric")} className="py-3.5 px-3 cursor-pointer hover:bg-slate-800 transition-colors">
                      Actual (IITM) {sortKey === "actualNumeric" && (sortDirection === "asc" ? "▲" : "▼")}
                    </th>
                    <th onClick={() => handleSort("category")} className="py-3.5 px-3 cursor-pointer hover:bg-slate-800 transition-colors">
                      Category {sortKey === "category" && (sortDirection === "asc" ? "▲" : "▼")}
                    </th>
                    <th className="py-3.5 px-3">Ardra Date</th>
                    <th onClick={() => handleSort("dominantNadi")} className="py-3.5 px-3 cursor-pointer hover:bg-slate-800 transition-colors">
                      Dominant Nadi {sortKey === "dominantNadi" && (sortDirection === "asc" ? "▲" : "▼")}
                    </th>
                    <th className="py-3.5 px-3">Pred Rainfall %</th>
                    <th className="py-3.5 px-3">Pred Intensity</th>
                    <th className="py-3.5 px-3">Water Grahas</th>
                    <th className="py-3.5 px-3">Fire Grahas</th>
                    <th onClick={() => handleSort("result")} className="py-3.5 px-4 text-center cursor-pointer hover:bg-slate-800 transition-colors">
                      Result {sortKey === "result" && (sortDirection === "asc" ? "▲" : "▼")}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {sortedRainfall.map((r) => (
                    <tr key={r.year} className={`hover:bg-cyan-950/20 transition-colors ${
                      r.result === "DIVERGENCE" ? "bg-rose-950/10" : ""
                    }`}>
                      <td className="py-3 px-4 font-bold text-cyan-300">{r.year}</td>
                      <td className={`py-3 px-3 font-bold ${r.actualNumeric > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {r.actualRainfall}
                      </td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          r.category === "EXCESS_FLOOD" ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                        }`}>
                          {r.category}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-slate-400">{r.ardraDate}</td>
                      <td className="py-3 px-3 font-semibold text-cyan-300">{r.dominantNadi}</td>
                      <td className="py-3 px-3 font-mono text-slate-200">{r.predRainfallPct}</td>
                      <td className="py-3 px-3 text-slate-400">{r.predIntensity}</td>
                      <td className="py-3 px-3 text-slate-300 text-[11px] max-w-[160px] truncate" title={r.waterGrahas}>
                        {r.waterGrahas}
                      </td>
                      <td className="py-3 px-3 text-slate-400 text-[11px] max-w-[130px] truncate" title={r.fireGrahas}>
                        {r.fireGrahas}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {r.result === "MATCH" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold text-[10px]">
                            <CheckCircle2 className="w-3 h-3" /> MATCH
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 font-bold text-[10px]">
                            <AlertCircle className="w-3 h-3" /> DIVERGENCE
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 🌟 Tab 2: Multi-Ingress OOS Split */}
      {activeTab === "multi_ingress" && (
        <div className="space-y-4 font-mono">
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur space-y-2 text-xs">
            <div className="font-bold text-cyan-400 uppercase tracking-wider">
              4-Pillar Synthesis Formula: Chaitra King + Mesha Meru World Chart + Ardra Pravesha + Sapta-Nadi
            </div>
            <p className="text-slate-300 leading-relaxed">
              Evaluating cross-pillar planetary war confluence across two distinct chronological splits: <strong>Calibration Split (1877–1960)</strong> and <strong>Untouched Out-of-Sample Test Split (1961–2020)</strong>.
            </p>
          </div>

          <div className="border border-slate-800 rounded-2xl overflow-hidden shadow-2xl bg-slate-900/60 backdrop-blur">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="uppercase text-[10px] tracking-wider border-b border-slate-800 bg-slate-950/80 text-slate-400">
                  <tr>
                    <th className="py-3.5 px-4">Year</th>
                    <th className="py-3.5 px-3">Split Cohort</th>
                    <th className="py-3.5 px-3">Actual (IITM)</th>
                    <th className="py-3.5 px-3">Ground Truth</th>
                    <th className="py-3.5 px-3">Confluence Score</th>
                    <th className="py-3.5 px-3">Predicted Category</th>
                    <th className="py-3.5 px-2 text-center">Chaitra</th>
                    <th className="py-3.5 px-2 text-center">Mesha (Meru)</th>
                    <th className="py-3.5 px-2 text-center">Ardra</th>
                    <th className="py-3.5 px-2 text-center">Sapta-Nadi</th>
                    <th className="py-3.5 px-4 text-center">Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {MULTI_INGRESS_ROWS.map((r) => (
                    <tr key={r.year} className={`hover:bg-cyan-950/20 transition-colors ${
                      r.result === "DIVERGENT" ? "bg-rose-950/10" : ""
                    }`}>
                      <td className="py-3 px-4 font-bold text-cyan-300">{r.year}</td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                          r.split.includes("OUT_OF_SAMPLE") ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30" : "bg-slate-800 text-slate-400"
                        }`}>
                          {r.split.includes("OUT_OF_SAMPLE") ? "OOS 1961-2020" : "CALIB 1877-1960"}
                        </span>
                      </td>
                      <td className={`py-3 px-3 font-bold ${r.actualRainfall.startsWith("+") ? "text-emerald-400" : "text-rose-400"}`}>
                        {r.actualRainfall}
                      </td>
                      <td className="py-3 px-3 font-bold">{r.groundTruth}</td>
                      <td className="py-3 px-3 font-bold text-cyan-300">{r.confluenceScore.toFixed(3)}</td>
                      <td className="py-3 px-3 text-slate-300">{r.predictedCategory}</td>
                      <td className="py-3 px-2 text-center text-slate-400">{r.chaitra}</td>
                      <td className="py-3 px-2 text-center text-slate-400">{r.meshaMeru}</td>
                      <td className="py-3 px-2 text-center text-slate-400">{r.ardra}</td>
                      <td className="py-3 px-2 text-center text-slate-400">{r.saptaNadi}</td>
                      <td className="py-3 px-4 text-center">
                        {r.result === "CORRECT" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold text-[10px]">
                            <CheckCircle2 className="w-3 h-3" /> CORRECT
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 font-bold text-[10px]">
                            <AlertCircle className="w-3 h-3" /> DIVERGENT
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 🌟 Tab 3: Seasonal 5-Stage Tracking */}
      {activeTab === "seasonal" && (
        <div className="space-y-4 font-mono">
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur space-y-2 text-xs">
            <div className="font-bold text-amber-400 uppercase tracking-wider">
              Prospective Dynamic Tracking: Chaitra $\rightarrow$ Mesha $\rightarrow$ Ardra $\rightarrow$ Karka (July) $\rightarrow$ Simha (August)
            </div>
            <p className="text-slate-300">
              Evaluated across 12 fresh independent historical years to detect mid-season monsoon breaks and sudden convective pauses.
            </p>
          </div>

          <div className="border border-slate-800 rounded-2xl overflow-hidden shadow-2xl bg-slate-900/60 backdrop-blur">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="uppercase text-[10px] tracking-wider border-b border-slate-800 bg-slate-950/80 text-slate-400">
                  <tr>
                    <th className="py-3.5 px-4">Year</th>
                    <th className="py-3.5 px-3">Actual</th>
                    <th className="py-3.5 px-3">Ground Truth</th>
                    <th className="py-3.5 px-3">Early Season (June)</th>
                    <th className="py-3.5 px-3">Mid-Season (July-Aug)</th>
                    <th className="py-3.5 px-3">Rolling Confluence</th>
                    <th className="py-3.5 px-3">Break Detected?</th>
                    <th className="py-3.5 px-3">Predicted Category</th>
                    <th className="py-3.5 px-4 text-center">Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {SEASONAL_ROWS.map((r) => (
                    <tr key={r.year} className={`hover:bg-cyan-950/20 transition-colors ${
                      r.result === "DIVERGENT" ? "bg-rose-950/10" : ""
                    }`}>
                      <td className="py-3 px-4 font-bold text-cyan-300">{r.year}</td>
                      <td className={`py-3 px-3 font-bold ${r.actualRainfall.startsWith("+") ? "text-emerald-400" : "text-rose-400"}`}>
                        {r.actualRainfall}
                      </td>
                      <td className="py-3 px-3 font-bold">{r.groundTruth}</td>
                      <td className="py-3 px-3 text-slate-400">{r.earlySeason}</td>
                      <td className="py-3 px-3 text-slate-400">{r.midSeason}</td>
                      <td className="py-3 px-3 font-bold text-cyan-300">{r.rollingConfluence}</td>
                      <td className="py-3 px-3">{r.breakDetected ? "YES" : "NO"}</td>
                      <td className="py-3 px-3 text-slate-300">{r.predictedCategory}</td>
                      <td className="py-3 px-4 text-center">
                        {r.result === "CORRECT" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold text-[10px]">
                            <CheckCircle2 className="w-3 h-3" /> CORRECT
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 font-bold text-[10px]">
                            <AlertCircle className="w-3 h-3" /> DIVERGENT
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 🌟 Tab 4: Negative Results Record & Shastric Boundary */}
      {activeTab === "negative_results" && (
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur shadow-2xl space-y-6 font-mono text-xs">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <span className="font-bold text-rose-400 uppercase tracking-wider text-sm">
              Negative-Results, Falsification &amp; Boundary Conditions
            </span>
            <span className="px-3 py-1 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/30 font-bold text-[10px]">
              CLASSIFIED: RESEARCH ISOLATED
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="space-y-2 p-5 rounded-xl bg-slate-950/80 border border-cyan-900/40">
              <div className="text-cyan-400 font-bold uppercase text-xs">Experiment 1: Single-Point Ingress</div>
              <p className="text-slate-400 leading-relaxed">
                Single Ardra Pravesha snapshot fails on landmark droughts (20% sensitivity). Early June moisture frequently masks late monsoon collapse.
              </p>
              <div className="text-emerald-400 font-bold pt-2 border-t border-slate-800">Result: 60.0% Overall (Asymmetric)</div>
            </div>

            <div className="space-y-2 p-5 rounded-xl bg-slate-950/80 border border-cyan-900/40">
              <div className="text-cyan-400 font-bold uppercase text-xs">Experiment 2: Multi-Ingress Confluence</div>
              <p className="text-slate-400 leading-relaxed">
                Mesha Meru chart + Chaitra King correctly models planetary war conditions and captures major shifts across the 1961–2020 split.
              </p>
              <div className="text-emerald-400 font-bold pt-2 border-t border-slate-800">Result: 60.0% Out-of-Sample Generalization</div>
            </div>

            <div className="space-y-2 p-5 rounded-xl bg-slate-950/80 border border-rose-900/40">
              <div className="text-rose-400 font-bold uppercase text-xs">Experiment 3: Prospective Seasonal Tracking</div>
              <p className="text-slate-400 leading-relaxed">
                Prospective seasonal dynamic tracking on fresh untouched years falls to 41.7%, confirming that pure celestial ingresses cannot act as local deterministic weather forecasts.
              </p>
              <div className="text-rose-400 font-bold pt-2 border-t border-slate-800">Conclusion: FORMALLY FALSIFIED AS STANDALONE FORECASTER</div>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-cyan-950/30 border border-cyan-800/40 text-slate-300 space-y-2">
            <div className="text-cyan-300 font-bold uppercase text-xs">Scientific Epistemological Implication</div>
            <p className="leading-relaxed text-slate-300">
              As articulated in the AstroOS core memory and canonical Siddhantic framework: Medini celestial calculations are macro planetary barometers (cosmic governance climate) rather than local atmospheric models. In contrast, natal astrology relies on exact birth time, Bhavachalita coordinates, and Vimshottari dasha promises.
            </p>
          </div>
        </div>
      )}

      {/* 🌟 Tab 5: Live API Sanity Audit */}
      {activeTab === "live_verify" && (
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur shadow-2xl space-y-5 font-mono text-xs">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <span className="font-bold text-cyan-400 uppercase tracking-wider text-sm">
              Live FastAPI Backend Sanity &amp; Udaya-Tithi Verifier
            </span>
            <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold text-[10px]">
              GET /api/v1/kurma-chakra
            </span>
          </div>

          {loadingKurma ? (
            <div className="space-y-4 py-4">
              <div className="h-10 bg-slate-800/60 animate-pulse rounded-xl" />
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => (
                  <div key={i} className="h-24 bg-slate-800/40 animate-pulse rounded-xl" />
                ))}
              </div>
            </div>
          ) : liveKurma ? (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <span className="text-slate-400">Evaluated Timestamp: </span>
                  <span className="text-cyan-300 font-bold">{liveKurma.evaluated_at}</span>
                </div>
                <div>
                  <span className="text-slate-400">Global Kurma Status: </span>
                  <span className="text-emerald-400 font-bold">{liveKurma.summary}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {liveKurma.sectors?.map((s: any) => (
                  <div key={s.direction} className={`p-4 rounded-xl border ${
                    s.is_afflicted ? "bg-rose-950/20 border-rose-800/40" : "bg-slate-950/80 border-slate-800"
                  }`}>
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="font-bold uppercase text-cyan-400">{s.direction}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        s.is_afflicted ? "bg-rose-500/20 text-rose-400 border border-rose-500/30" : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      }`}>
                        {s.severity}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-300 truncate">
                      Regions: {s.traditional_regions?.join(", ")}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1">
                      Malefics: {s.transiting_malefics?.join(", ") || "None"}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800/50 text-rose-300">
              Could not connect to FastAPI endpoint at http://localhost:8000/api/v1/kurma-chakra. Ensure backend is running.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
