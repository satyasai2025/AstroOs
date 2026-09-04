"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { SouthIndianChart } from "@/components/charts/SouthIndianChart";
import { api } from "@/lib/api";

// --- Domain Interfaces ---
interface PlanetRow {
  planet: string;
  sign: string;
  degree_str: string;
  degree_float: number;
  nakshatra: string;
  pada: number;
  sign_lord: string;
  star_lord: string;
  sub_lord: string;
  sub_sub_lord: string;
  house_number: number;
}

interface HouseCuspRow {
  house: number;
  sign: string;
  degree_str: string;
  degree_float: number;
  nakshatra: string;
  pada: number;
  sign_lord: string;
  star_lord: string;
  sub_lord: string;
  sub_sub_lord: string;
}

interface RulingPlanetItem {
  point_name: string;
  sign_lord: string;
  star_lord: string;
  sub_lord: string;
  sub_sub_lord: string;
}

interface ArabicPartItem {
  name: string;
  category: string;
  formula_used: string;
  is_day_formula: boolean;
  sidereal_longitude: number;
  rashi: string;
  rashi_degree_str: string;
  sign_lord: string;
  star_lord: string;
  sub_lord: string;
  sub_sub_lord: string;
  description: string;
}

interface KeyEvidence {
  factor: string;
  indication: "Positive" | "Very Positive" | "Neutral" | "Slight Negative" | "Negative";
  explanation: string;
  weight: number;
}

interface RelevantHouse {
  house: number;
  sign: string;
  lord: string;
  strength: "Strong" | "Average" | "Weak";
  note: string;
}

interface TimingIndication {
  likely_window: string;
  dasha_mahadasha: string;
  antardasha: string;
  transit_support: string;
  moon_cycle: string;
}

interface SupportingRule {
  rule_id: string;
  rule_principle: string;
  reference: string;
  triggered: "Yes" | "Partially" | "No";
  weight: number;
}

interface ContradictionAlert {
  title: string;
  description: string;
  advice: string;
}

export interface HoraryFormData {
  name: string;
  gender: "Male" | "Female" | "Unknown";
  horaryNumber: number | null;
  horarySystem: "kp_249" | "kp_2193";
  isTimeChart: boolean;
  date: string;
  time: string;
  place: string;
  timezone: string;
  latitude: number;
  longitude: number;
  gmt: number;
  dst: number;
  question: string;
}

export type TabType =
  | "Overview"
  | "Chart"
  | "Significators"
  | "Houses"
  | "Ruling & Moon"
  | "Timing & Timeline"
  | "AI Astrologer";

const TABS: TabType[] = [
  "Overview",
  "Chart",
  "Significators",
  "Houses",
  "Ruling & Moon",
  "Timing & Timeline",
  "AI Astrologer",
];

function computeUtcIsoString(
  dateStr: string,
  timeStr: string,
  gmtOffsetHours: number = 5.5,
  dstHours: number = 0
): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const timeParts = timeStr.split(":");
  const hours = Number(timeParts[0]) || 0;
  const minutes = Number(timeParts[1]) || 0;
  const seconds = Number(timeParts[2]) || 0;

  const totalOffsetMinutes = (gmtOffsetHours + dstHours) * 60;
  const localUtcMs = Date.UTC(y!, m! - 1, d!, hours, minutes, seconds);
  const actualUtcMs = localUtcMs - totalOffsetMinutes * 60 * 1000;
  return new Date(actualUtcMs).toISOString();
}

function detectQueryCategory(q: string): string {
  const lower = q.toLowerCase();
  if (/job|career|promotion|work|business|interview|selection|exam|boss|company|hire/i.test(lower)) return "Career & Job";
  if (/marriage|love|spouse|partner|relationship|wedding|bride|groom/i.test(lower)) return "Marriage & Love";
  if (/wealth|money|loan|property|buy|house|flat|finance|recovery|cash|payment/i.test(lower)) return "Wealth & Property";
  if (/travel|visa|abroad|foreign|flight|passport|relocation|immigrat/i.test(lower)) return "Travel & Visa";
  if (/health|disease|surgery|recovery|doctor|hospital|sick|cure/i.test(lower)) return "Health & Medical";
  if (/court|legal|lawsuit|case|dispute|police|judge/i.test(lower)) return "Litigation & Legal";
  return "General Inquiry";
}

function formatQueryDateTime(dateStr: string, timeStr: string, tz: string = "Asia/Kolkata"): string {
  try {
    return `${dateStr} ${timeStr} (${tz})`;
  } catch {
    return `${dateStr}, ${timeStr}`;
  }
}

export default function PrashnaPage() {
  const [activeTab, setActiveTab] = useState<TabType>("Overview");
  const [chartStyle, setChartStyle] = useState<"north" | "south">("north");
  const [hasCalculated, setHasCalculated] = useState(false);
  const [loading, setLoading] = useState(false);

  const now = new Date();
  const defaultDate = now.toISOString().split("T")[0]!;
  const defaultTime = now.toTimeString().split(" ")[0]!;

  const [formData, setFormData] = useState<HoraryFormData>({
    name: "Querent",
    gender: "Male",
    horaryNumber: 1,
    horarySystem: "kp_249",
    isTimeChart: true,
    date: defaultDate,
    time: defaultTime,
    place: "Pune, Maharashtra, India",
    timezone: "Asia/Kolkata",
    latitude: 18.5204,
    longitude: 73.8567,
    gmt: 5.5,
    dst: 0,
    question: "",
  });

  // Computed State
  const [planets, setPlanets] = useState<PlanetRow[]>([]);
  const [cusps, setCusps] = useState<HouseCuspRow[]>([]);
  const [arabicParts, setArabicParts] = useState<ArabicPartItem[]>([]);
  const [rpEntries, setRpEntries] = useState<RulingPlanetItem[]>([]);
  const [evidence, setEvidence] = useState<KeyEvidence[]>([]);
  const [relevantHouses, setRelevantHouses] = useState<RelevantHouse[]>([]);
  const [timing, setTiming] = useState<TimingIndication | null>(null);
  const [supportingRules, setSupportingRules] = useState<SupportingRule[]>([]);
  const [contradictions, setContradictions] = useState<ContradictionAlert[]>([]);
  const [conclusions, setConclusions] = useState<string[]>([]);
  const [summaryText, setSummaryText] = useState<string>("");
  const [confidence, setConfidence] = useState(88);
  const [verdict, setVerdict] = useState<"YES" | "NO" | "MIXED">("YES");
  const [ascendantSign, setAscendantSign] = useState("Libra");
  const [ascendantDegreeStr, setAscendantDegreeStr] = useState("29° 08' 26\"");
  const [dayLord, setDayLord] = useState<string>("Saturn");
  const [horaLord, setHoraLord] = useState<string>("Jupiter");

  // "Here & Now" button handler
  const handleHereAndNow = () => {
    const d = new Date();
    setFormData((prev) => ({
      ...prev,
      date: d.toISOString().split("T")[0]!,
      time: d.toTimeString().split(" ")[0]!,
      isTimeChart: true,
      horaryNumber: null,
    }));
  };

  // Random seed generator
  const handleRandomSeed = () => {
    const max = formData.horarySystem === "kp_2193" ? 2193 : 249;
    const rnd = Math.floor(Math.random() * max) + 1;
    setFormData((prev) => ({
      ...prev,
      horaryNumber: rnd,
      isTimeChart: false,
    }));
  };

  // Calculate Horary Analysis
  const handleCalculate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!formData.question.trim()) return;

    setLoading(true);
    try {
      const utcIso = computeUtcIsoString(
        formData.date,
        formData.time,
        formData.gmt,
        formData.dst
      );

      const payload = {
        name: formData.name || "Querent",
        gender: formData.gender,
        question: formData.question.trim(),
        moment_utc: utcIso,
        latitude: formData.latitude,
        longitude: formData.longitude,
        place_name: formData.place,
        timezone_offset: formData.gmt,
        horary_number: formData.isTimeChart ? null : Number(formData.horaryNumber),
        horary_system: formData.horarySystem,
        ayanamsa: "lahiri",
      };

      const res = await api.post<any>("/api/v1/prashna/calculate", payload);

      if (res) {
        setPlanets(res.planets || []);
        setCusps(res.cusps || []);
        setArabicParts(res.arabic_parts || []);
        setRpEntries(res.ruling_planets_ct?.entries || res.ruling_planets_rt?.entries || []);
        setEvidence(res.judgement?.key_evidences || []);
        setRelevantHouses(res.judgement?.relevant_houses || []);
        setTiming(res.judgement?.timing || null);
        setSupportingRules(res.judgement?.supporting_rules || []);
        setContradictions(res.judgement?.contradictions || []);
        setConclusions(res.judgement?.conclusions || []);
        setSummaryText(res.judgement?.summary || "");
        setConfidence(res.judgement?.confidence_percentage ?? 88);
        setVerdict(res.judgement?.verdict || "YES");

        if (res.ruling_planets_ct) {
          setDayLord(res.ruling_planets_ct.day_lord?.toUpperCase() || "SATURN");
          setHoraLord(res.ruling_planets_ct.hora_lord?.toUpperCase() || "JUPITER");
        }

        if (res.cusps && res.cusps.length > 0) {
          setAscendantSign(res.cusps[0].sign);
          setAscendantDegreeStr(res.cusps[0].degree_str);
        }
        setHasCalculated(true);
        setActiveTab("Overview");
      }
    } catch (err) {
      console.error("Prashna calculation error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Chart Planets for North/South Indian Chart
  const chartPlanets = useMemo(() => {
    return planets.map((p) => ({
      planet: p.planet,
      rashi: p.sign,
      house_number: p.house_number,
      rashi_degree: p.degree_float,
    }));
  }, [planets]);

  const moonPlanet = useMemo(() => {
    return planets.find((p) => p.planet.toLowerCase() === "moon");
  }, [planets]);

  const jupiterPlanet = useMemo(() => {
    return planets.find((p) => p.planet.toLowerCase() === "jupiter");
  }, [planets]);

  const saturnPlanet = useMemo(() => {
    return planets.find((p) => p.planet.toLowerCase() === "saturn");
  }, [planets]);

  const queryCategory = useMemo(() => {
    return detectQueryCategory(formData.question);
  }, [formData.question]);

  const indicationText = verdict === "YES" ? "Favorable" : verdict === "NO" ? "Unfavorable" : "Mixed Outcome";
  const indicationColor = verdict === "YES" ? "#10b981" : verdict === "NO" ? "#ef4444" : "#f59e0b";

  return (
    <div
      className="min-h-screen p-4 md:p-6"
      style={{ backgroundColor: "var(--bg-primary)", color: "var(--text-primary)" }}
    >
      <div className="max-w-6xl mx-auto space-y-6">

        {/* ── STATE 1: SIMPLE CLEAN ENTRY FORM ── */}
        {!hasCalculated ? (
          <div className="max-w-2xl mx-auto py-6">
            <div
              className="obsidian-card rounded-2xl border p-6 md:p-8 shadow-2xl space-y-6"
              style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
            >
              {/* Form Header */}
              <div className="flex items-center justify-between border-b pb-4" style={{ borderColor: "var(--border-primary)" }}>
                <div>
                  <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                    Horary / Time Chart Data Entry
                  </h2>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Vedic &amp; KP Prashna Analysis with Ruling Planets, Hora &amp; Transit
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleHereAndNow}
                  className="rounded-xl border px-3 py-1.5 text-xs font-bold text-cyan-400 border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20 transition flex items-center gap-1.5 cursor-pointer"
                >
                  <span>⚡ Here &amp; Now</span>
                </button>
              </div>

              <form onSubmit={handleCalculate} className="space-y-4">
                {/* Question Input */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                    <span className="text-cyan-400 mr-1">*</span>Prashna Question:
                  </label>
                  <textarea
                    id="prashna-question"
                    rows={2}
                    required
                    value={formData.question}
                    onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                    placeholder="e.g. Will I get this job? / Will the visa be approved?"
                    className="obsidian-input w-full text-sm"
                  />
                  {/* Quick Category Chips */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {[
                      { label: "💼 Job Selection", q: "Will I get selected for this job / promotion?" },
                      { label: "💍 Marriage", q: "Will our marriage take place smoothly?" },
                      { label: "✈️ Visa / Travel", q: "Will my foreign visa application be approved?" },
                      { label: "🏠 Buy Property", q: "Will I purchase the property successfully?" },
                      { label: "⚖️ Court Case", q: "Will the court case be decided in my favor?" },
                    ].map((item) => (
                      <button
                        key={item.label}
                        type="button"
                        onClick={() => setFormData({ ...formData, question: item.q })}
                        className="rounded-md border px-2 py-0.5 text-[10px] font-medium transition hover:border-cyan-500/40 hover:text-cyan-300 cursor-pointer"
                        style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Name & Gender */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                      Name (Optional):
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Querent name"
                      className="obsidian-input w-full text-xs"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                      Gender:
                    </label>
                    <div className="flex items-center gap-4 pt-2">
                      {(["Male", "Female", "Unknown"] as const).map((g) => (
                        <label key={g} className="inline-flex items-center cursor-pointer gap-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                          <input
                            type="radio"
                            name="gender"
                            value={g}
                            checked={formData.gender === g}
                            onChange={() => setFormData({ ...formData, gender: g })}
                            className="accent-cyan-400"
                          />
                          <span>{g}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Horary Seed Mode */}
                <div className="space-y-2 pt-2 border-t" style={{ borderColor: "var(--border-primary)" }}>
                  <label className="block text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                    Horary Seed:
                  </label>
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      type="number"
                      min={1}
                      max={formData.horarySystem === "kp_2193" ? 2193 : 249}
                      value={formData.horaryNumber ?? ""}
                      onChange={(e) => setFormData({ ...formData, horaryNumber: parseInt(e.target.value) || 1, isTimeChart: false })}
                      placeholder={formData.horarySystem === "kp_2193" ? "1-2193" : "1-249"}
                      className="obsidian-input w-24 text-xs font-mono font-bold text-cyan-400"
                    />
                    <button
                      type="button"
                      onClick={handleRandomSeed}
                      className="rounded-lg border px-3 py-1.5 text-xs font-bold transition hover:bg-cyan-500/10 cursor-pointer"
                      style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}
                    >
                      🎲 Random
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormData({ ...formData, horarySystem: "kp_249", isTimeChart: false, horaryNumber: formData.horaryNumber || 1 })}
                      className={`rounded-lg border px-3 py-1.5 text-xs font-bold transition cursor-pointer ${
                        !formData.isTimeChart && formData.horarySystem === "kp_249"
                          ? "border-cyan-500 bg-cyan-500/20 text-cyan-300"
                          : ""
                      }`}
                      style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}
                    >
                      1–249
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormData({ ...formData, horarySystem: "kp_2193", isTimeChart: false, horaryNumber: formData.horaryNumber || 1 })}
                      className={`rounded-lg border px-3 py-1.5 text-xs font-bold transition cursor-pointer ${
                        !formData.isTimeChart && formData.horarySystem === "kp_2193"
                          ? "border-cyan-500 bg-cyan-500/20 text-cyan-300"
                          : ""
                      }`}
                      style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}
                    >
                      1–2193
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormData({ ...formData, isTimeChart: true, horaryNumber: null })}
                      className={`rounded-lg border px-3.5 py-1.5 text-xs font-bold transition cursor-pointer ${
                        formData.isTimeChart
                          ? "border-cyan-400 bg-cyan-500/20 text-cyan-300"
                          : ""
                      }`}
                      style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}
                    >
                      ⏱️ Time Chart (Now)
                    </button>
                  </div>
                </div>

                {/* Date & Time Custom Entry */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                      <span className="text-cyan-400 mr-1">*</span>Date:
                    </label>
                    <input
                      id="prashna-date"
                      type="date"
                      required
                      value={formData.date}
                      onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                      className="obsidian-input w-full text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                      <span className="text-cyan-400 mr-1">*</span>Time:
                    </label>
                    <input
                      id="prashna-time"
                      type="time"
                      step="1"
                      required
                      value={formData.time}
                      onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                      className="obsidian-input w-full text-xs"
                    />
                  </div>
                </div>

                {/* Place & Timezone */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                      <span className="text-cyan-400 mr-1">*</span>Place:
                    </label>
                    <input
                      id="prashna-place"
                      type="text"
                      required
                      value={formData.place}
                      onChange={(e) => setFormData({ ...formData, place: e.target.value })}
                      placeholder="City, State, Country"
                      className="obsidian-input w-full text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                      <span className="text-cyan-400 mr-1">*</span>Timezone:
                    </label>
                    <select
                      value={formData.timezone}
                      onChange={(e) => {
                        const tz = e.target.value;
                        const gmt = tz === "Asia/Kolkata" ? 5.5 : tz === "UTC" ? 0 : 5.5;
                        setFormData({ ...formData, timezone: tz, gmt });
                      }}
                      className="obsidian-input w-full text-xs"
                    >
                      <option value="Asia/Kolkata">Asia/Kolkata (IST, UTC+05:30)</option>
                      <option value="UTC">UTC (UTC+00:00)</option>
                      <option value="America/New_York">America/New_York (EST, UTC-05:00)</option>
                      <option value="Europe/London">Europe/London (GMT, UTC+00:00)</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                  <div>
                    <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>Lat (N/S)</span>
                    <input
                      type="number"
                      step="any"
                      value={formData.latitude}
                      onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) || 0 })}
                      className="obsidian-input text-xs w-full font-mono"
                    />
                  </div>
                  <div>
                    <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>Lng (E/W)</span>
                    <input
                      type="number"
                      step="any"
                      value={formData.longitude}
                      onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) || 0 })}
                      className="obsidian-input text-xs w-full font-mono"
                    />
                  </div>
                  <div>
                    <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>GMT Offset</span>
                    <input
                      type="number"
                      step="any"
                      value={formData.gmt}
                      onChange={(e) => setFormData({ ...formData, gmt: parseFloat(e.target.value) || 5.5 })}
                      className="obsidian-input text-xs w-full font-mono"
                    />
                  </div>
                  <div>
                    <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>DST</span>
                    <input
                      type="number"
                      step="any"
                      value={formData.dst}
                      onChange={(e) => setFormData({ ...formData, dst: parseFloat(e.target.value) || 0 })}
                      className="obsidian-input text-xs w-full font-mono"
                    />
                  </div>
                </div>

                {/* Submit Action */}
                <div className="pt-4 border-t" style={{ borderColor: "var(--border-primary)" }}>
                  <button
                    type="submit"
                    disabled={loading || !formData.question.trim()}
                    className="w-full rounded-xl py-3 px-6 text-sm font-bold shadow-lg transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                    style={{
                      backgroundColor: "var(--obsidian-accent-secondary, #06b6d4)",
                      color: "#000",
                    }}
                  >
                    {loading ? (
                      <>
                        <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-t-transparent border-black" />
                        <span>Calculating Canonical Prashna Facts…</span>
                      </>
                    ) : (
                      <span>Cast Prashna Chart &amp; Reveal Verdict →</span>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : (
          /* ── STATE 2: COMPLETE PRASHNA ANALYSIS REPORT (Full Astrological Engine) ── */
          <div
            className="obsidian-card rounded-2xl border shadow-2xl overflow-hidden"
            style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
          >
            {/* 1. Header Banner */}
            <div className="p-6 border-b space-y-3" style={{ borderColor: "var(--border-primary)" }}>
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => {
                    setHasCalculated(false);
                    setFormData((prev) => ({ ...prev, question: "" }));
                  }}
                  className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:underline cursor-pointer"
                >
                  <span>← Prashna Analysis</span>
                </button>
                <div className="flex items-center gap-2">
                  <span
                    className="rounded-full px-3 py-0.5 text-xs font-bold border"
                    style={{
                      backgroundColor: "rgba(6,182,212,0.12)",
                      borderColor: "rgba(6,182,212,0.3)",
                      color: "#06b6d4",
                    }}
                  >
                    Canonical Astrological Engine • KP Placidus • Swiss Ephemeris
                  </span>
                </div>
              </div>

              <div>
                <h1 className="text-xl md:text-2xl font-bold tracking-tight" style={{ color: "var(--text-primary)" }}>
                  &ldquo;{formData.question}&rdquo;
                </h1>
                <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                  Asked: {formatQueryDateTime(formData.date, formData.time, formData.timezone)} • {formData.place} • <strong className="text-cyan-400">Vara: {dayLord}</strong> • <strong className="text-amber-400">Hora: {horaLord}</strong>
                </p>
              </div>
            </div>

            {/* 2. Top 4 Metric KPI Cards */}
            <div className="p-6 border-b" style={{ borderColor: "var(--border-primary)" }}>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {/* Card 1: QUESTION */}
                <div
                  className="rounded-xl border p-4"
                  style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
                >
                  <span className="text-[10px] block uppercase font-bold tracking-wider" style={{ color: "var(--text-muted)" }}>
                    QUESTION
                  </span>
                  <p className="text-sm font-bold mt-1 text-cyan-400">
                    {queryCategory}
                  </p>
                </div>

                {/* Card 2: ASCENDANT */}
                <div
                  className="rounded-xl border p-4"
                  style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
                >
                  <span className="text-[10px] block uppercase font-bold tracking-wider" style={{ color: "var(--text-muted)" }}>
                    ASCENDANT (LAGNA)
                  </span>
                  <p className="text-sm font-bold mt-1" style={{ color: "var(--text-primary)" }}>
                    {ascendantSign} <span className="text-xs font-normal font-mono" style={{ color: "var(--text-muted)" }}>({ascendantDegreeStr})</span>
                  </p>
                </div>

                {/* Card 3: MOON & HORA */}
                <div
                  className="rounded-xl border p-4"
                  style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
                >
                  <span className="text-[10px] block uppercase font-bold tracking-wider" style={{ color: "var(--text-muted)" }}>
                    MOON &amp; HORA
                  </span>
                  <p className="text-sm font-bold mt-1 text-amber-400">
                    {moonPlanet?.sign || "Scorpio"} <span className="text-xs font-normal" style={{ color: "var(--text-muted)" }}>({horaLord} Hora)</span>
                  </p>
                </div>

                {/* Card 4: INDICATION */}
                <div
                  className="rounded-xl border p-4"
                  style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
                >
                  <span className="text-[10px] block uppercase font-bold tracking-wider" style={{ color: "var(--text-muted)" }}>
                    INDICATION
                  </span>
                  <p className="text-sm font-bold mt-1 flex items-center gap-1.5" style={{ color: indicationColor }}>
                    <span>{verdict === "YES" ? "✓" : verdict === "NO" ? "✕" : "⚠️"}</span>
                    <span>{indicationText}</span>
                  </p>
                </div>
              </div>
            </div>

            {/* 3. Tab Navigation Bar (7 Required Tabs) */}
            <div className="px-6 border-b flex items-center gap-2 overflow-x-auto" style={{ borderColor: "var(--border-primary)" }}>
              {TABS.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setActiveTab(tab)}
                  className="px-4 py-3 text-xs font-bold border-b-2 transition whitespace-nowrap cursor-pointer"
                  style={{
                    borderColor: activeTab === tab ? "var(--obsidian-accent-secondary, #06b6d4)" : "transparent",
                    color: activeTab === tab ? "#06b6d4" : "var(--text-secondary)",
                  }}
                >
                  {tab === "Ruling & Moon" ? "👑 Ruling & Moon" : tab === "Timing & Timeline" ? "⏳ Timing & Timeline" : tab === "AI Astrologer" ? "✨ AI Astrologer" : tab}
                </button>
              ))}
            </div>

            {/* 4. Tab Body Content */}
            <div className="p-6 space-y-6">

              {/* ── TAB 1: OVERVIEW ── */}
              {activeTab === "Overview" && (
                <div className="space-y-6">
                  {/* Top Split: Rashi Chart (Left) + Prashna Verdict (Right) */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
                    {/* Left: RASHI CHART */}
                    <div
                      className="rounded-2xl border p-5 flex flex-col items-center justify-between relative space-y-3"
                      style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
                    >
                      <div className="w-full flex items-center justify-between px-2">
                        <span className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                          Rashi Chart (D1)
                        </span>
                        <div className="flex items-center gap-1 rounded-lg border p-0.5" style={{ borderColor: "var(--border-primary)" }}>
                          <button
                            type="button"
                            onClick={() => setChartStyle("north")}
                            className="px-2 py-0.5 text-[10px] font-bold rounded cursor-pointer"
                            style={{
                              backgroundColor: chartStyle === "north" ? "rgba(6,182,212,0.2)" : "transparent",
                              color: chartStyle === "north" ? "#06b6d4" : "var(--text-muted)",
                            }}
                          >
                            North
                          </button>
                          <button
                            type="button"
                            onClick={() => setChartStyle("south")}
                            className="px-2 py-0.5 text-[10px] font-bold rounded cursor-pointer"
                            style={{
                              backgroundColor: chartStyle === "south" ? "rgba(6,182,212,0.2)" : "transparent",
                              color: chartStyle === "south" ? "#06b6d4" : "var(--text-muted)",
                            }}
                          >
                            South
                          </button>
                        </div>
                      </div>

                      <div className="flex justify-center items-center py-2 w-full">
                        {chartStyle === "north" ? (
                          <NorthIndianChart
                            title="Horary D1"
                            ascendant={{ rashi: ascendantSign }}
                            planets={chartPlanets}
                            size={280}
                          />
                        ) : (
                          <SouthIndianChart
                            title="Horary D1"
                            ascendant={{ rashi: ascendantSign }}
                            planets={chartPlanets}
                            size={280}
                          />
                        )}
                      </div>
                    </div>

                    {/* Right: PRASHNA VERDICT */}
                    <div
                      className="rounded-2xl border p-6 flex flex-col justify-between space-y-4"
                      style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
                    >
                      <div>
                        <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
                          <h2 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                            PRASHNA VERDICT
                          </h2>
                          <span className="text-xs font-bold font-mono" style={{ color: indicationColor }}>
                            {confidence}% Confidence
                          </span>
                        </div>

                        <div className="mt-4 space-y-2">
                          <div className="flex items-center gap-2">
                            <span className="text-lg font-bold" style={{ color: indicationColor }}>
                              {verdict === "YES" ? "✓" : verdict === "NO" ? "✕" : "⚠️"}
                            </span>
                            <span className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
                              {verdict === "YES" ? "Positive indication for outcome" : verdict === "NO" ? "Negative indication for outcome" : "Mixed / Conditional indication"}
                            </span>
                          </div>
                          <p className="text-xs leading-relaxed pl-6" style={{ color: "var(--text-secondary)" }}>
                            {summaryText || `Based on Cuspal Sub-Lord (CSL) significations, Ruling Planets (RP), Hora Lord (${horaLord}), and Moon's strength for ${queryCategory}.`}
                          </p>
                        </div>

                        {/* Key Factors */}
                        <div className="mt-4 pt-3 border-t space-y-2" style={{ borderColor: "var(--border-primary)" }}>
                          <p className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>Key factors:</p>
                          <ul className="space-y-1.5 text-xs pl-2" style={{ color: "var(--text-secondary)" }}>
                            {evidence.slice(0, 3).map((e, idx) => (
                              <li key={idx} className="flex items-start gap-2">
                                <span className="text-cyan-400 font-bold">•</span>
                                <span><strong>{e.factor}:</strong> {e.explanation}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      {/* Clean Timeline Mini Strip */}
                      <div
                        className="rounded-xl border p-3 text-xs flex items-center justify-between"
                        style={{ borderColor: "rgba(6,182,212,0.3)", backgroundColor: "rgba(6,182,212,0.08)" }}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-cyan-400 font-bold">⏱️ Timing Horizon:</span>
                          <span className="font-mono text-cyan-300 font-bold">{timing?.likely_window || "Aug 2026 – Nov 2026"}</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setActiveTab("Timing & Timeline")}
                          className="text-[11px] font-bold text-cyan-400 hover:underline cursor-pointer"
                        >
                          View Full Timeline →
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Middle: SIGNIFICATOR CHAIN */}
                  <div
                    className="rounded-2xl border p-6 space-y-4"
                    style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
                  >
                    <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                      SIGNIFICATOR CHAIN
                    </h3>

                    {/* Flow Diagram */}
                    <div className="flex flex-wrap items-center gap-2 md:gap-3 text-xs font-semibold py-2">
                      <div className="rounded-xl border px-3.5 py-2" style={{ borderColor: "rgba(6,182,212,0.4)", backgroundColor: "rgba(6,182,212,0.15)", color: "#06b6d4" }}>
                        <span className="block text-[10px] font-normal" style={{ color: "var(--text-muted)" }}>Query</span>
                        <span>{queryCategory}</span>
                      </div>
                      <span style={{ color: "var(--text-muted)" }}>──►</span>

                      <div className="rounded-xl border px-3.5 py-2" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}>
                        <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>Primary House</span>
                        <span>{relevantHouses.length > 0 ? `House ${relevantHouses.map(h => h.house).slice(0, 2).join(" & ")}` : "House 10 & 11"}</span>
                      </div>
                      <span style={{ color: "var(--text-muted)" }}>──►</span>

                      <div className="rounded-xl border px-3.5 py-2" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}>
                        <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>CSL Lord</span>
                        <span className="text-emerald-400">{cusps.find((c) => c.house === 10)?.sub_lord || cusps[0]?.sub_lord || "Venus"}</span>
                      </div>
                      <span style={{ color: "var(--text-muted)" }}>──►</span>

                      <div className="rounded-xl border px-3.5 py-2" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}>
                        <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>Hora &amp; RP</span>
                        <span className="text-amber-400">{horaLord}</span>
                      </div>
                      <span style={{ color: "var(--text-muted)" }}>──►</span>

                      <div className="rounded-xl border px-3.5 py-2" style={{ borderColor: "rgba(16,185,129,0.4)", backgroundColor: "rgba(16,185,129,0.15)", color: indicationColor }}>
                        <span className="block text-[10px] font-normal">Result</span>
                        <span>{indicationText}</span>
                      </div>
                    </div>
                  </div>

                  {/* Bottom: Evidence & Rules Triggered */}
                  <div
                    className="rounded-2xl border p-6 space-y-4"
                    style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
                  >
                    <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                          Evidence &amp; Classical Rules Triggered
                        </h3>
                        <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                          Weighted breakdown of primary promises vs minor procedural delays
                        </p>
                      </div>
                      <div className="flex items-center gap-2 text-xs font-mono">
                        <span className="rounded px-2 py-0.5 border text-emerald-400 border-emerald-500/30 bg-emerald-500/10 font-bold">
                          Net Confidence: {confidence}%
                        </span>
                      </div>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="border-b font-semibold text-[11px]" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                          <tr>
                            <th className="py-2.5 px-3">Rule / Factor</th>
                            <th className="py-2.5 px-3">Astrological Principle</th>
                            <th className="py-2.5 px-3">Status</th>
                            <th className="py-2.5 px-3 text-right">Factor Weight / Impact</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                          {supportingRules.map((r) => (
                            <tr key={r.rule_id} className="hover:bg-white/[0.02] transition">
                              <td className="py-2.5 px-3 font-mono font-bold text-cyan-400">{r.rule_id}</td>
                              <td className="py-2.5 px-3" style={{ color: "var(--text-primary)" }}>{r.rule_principle}</td>
                              <td className="py-2.5 px-3">
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                                  ✓ {r.triggered === "Yes" ? "Strongly Supports" : "Partially"}
                                </span>
                              </td>
                              <td className="py-2.5 px-3 text-right font-bold text-emerald-400">
                                +{r.weight}% (Major Support)
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* ── TAB 2: CHART ── */}
              {activeTab === "Chart" && (
                <div className="space-y-6">
                  <div className="flex justify-center p-4">
                    {chartStyle === "north" ? (
                      <NorthIndianChart
                        title="Horary D1"
                        ascendant={{ rashi: ascendantSign }}
                        planets={chartPlanets}
                        size={360}
                      />
                    ) : (
                      <SouthIndianChart
                        title="Horary D1"
                        ascendant={{ rashi: ascendantSign }}
                        planets={chartPlanets}
                        size={360}
                      />
                    )}
                  </div>
                </div>
              )}

              {/* ── TAB 3: SIGNIFICATORS ── */}
              {activeTab === "Significators" && (
                <div className="space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                    KP 4-Fold Planetary Significators Table
                  </h3>
                  <div className="overflow-x-auto rounded-xl border" style={{ borderColor: "var(--border-primary)" }}>
                    <table className="w-full text-left text-xs">
                      <thead className="border-b font-semibold text-[11px]" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)", color: "var(--text-muted)" }}>
                        <tr>
                          <th className="py-2.5 px-3">Planet</th>
                          <th className="py-2.5 px-3">Sign</th>
                          <th className="py-2.5 px-3">Degree</th>
                          <th className="py-2.5 px-3">Nakshatra</th>
                          <th className="py-2.5 px-3">Sign Lord</th>
                          <th className="py-2.5 px-3">Star Lord</th>
                          <th className="py-2.5 px-3">Sub Lord</th>
                          <th className="py-2.5 px-3">House</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                        {planets.map((p) => (
                          <tr key={p.planet} className="hover:bg-white/[0.02] transition">
                            <td className="py-2 px-3 font-bold" style={{ color: "var(--text-primary)" }}>{p.planet}</td>
                            <td className="py-2 px-3 font-semibold text-cyan-400">{p.sign}</td>
                            <td className="py-2 px-3 font-mono">{p.degree_str}</td>
                            <td className="py-2 px-3 text-amber-400">{p.nakshatra} (P{p.pada})</td>
                            <td className="py-2 px-3">{p.sign_lord}</td>
                            <td className="py-2 px-3 text-amber-400">{p.star_lord}</td>
                            <td className="py-2 px-3 font-bold text-emerald-400">{p.sub_lord}</td>
                            <td className="py-2 px-3 font-bold">H{p.house_number}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* ── TAB 4: HOUSES ── */}
              {activeTab === "Houses" && (
                <div className="space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                    12 Cuspal Sub-Lords (CSL) &amp; House Alignment
                  </h3>
                  <div className="overflow-x-auto rounded-xl border" style={{ borderColor: "var(--border-primary)" }}>
                    <table className="w-full text-left text-xs">
                      <thead className="border-b font-semibold text-[11px]" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)", color: "var(--text-muted)" }}>
                        <tr>
                          <th className="py-2.5 px-3">House</th>
                          <th className="py-2.5 px-3">Sign</th>
                          <th className="py-2.5 px-3">Cusp Longitude</th>
                          <th className="py-2.5 px-3">Nakshatra</th>
                          <th className="py-2.5 px-3">Sign Lord</th>
                          <th className="py-2.5 px-3">Star Lord</th>
                          <th className="py-2.5 px-3">Sub Lord (CSL)</th>
                          <th className="py-2.5 px-3">Sub-Sub Lord</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                        {cusps.map((c) => (
                          <tr key={c.house} className="hover:bg-white/[0.02] transition">
                            <td className="py-2 px-3 font-bold text-cyan-400">House {c.house}</td>
                            <td className="py-2 px-3 font-semibold">{c.sign}</td>
                            <td className="py-2 px-3 font-mono">{c.degree_str}</td>
                            <td className="py-2 px-3 text-amber-400">{c.nakshatra} (P{c.pada})</td>
                            <td className="py-2 px-3">{c.sign_lord}</td>
                            <td className="py-2 px-3 text-amber-400">{c.star_lord}</td>
                            <td className="py-2 px-3 font-bold text-emerald-400">{c.sub_lord}</td>
                            <td className="py-2 px-3" style={{ color: "var(--text-muted)" }}>{c.sub_sub_lord}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* ── TAB 5: RULING & MOON ── */}
              {activeTab === "Ruling & Moon" && (
                <div className="space-y-6">
                  {/* Hora & Day Lord Summary */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="rounded-xl border p-4 space-y-1" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}>
                      <span className="text-[10px] block uppercase font-bold text-cyan-400">Vara Lord (Day Lord)</span>
                      <p className="text-base font-bold" style={{ color: "var(--text-primary)" }}>{dayLord}</p>
                      <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>Ruling deity for the diurnal solar cycle</p>
                    </div>

                    <div className="rounded-xl border p-4 space-y-1" style={{ borderColor: "rgba(245,158,11,0.4)", backgroundColor: "rgba(245,158,11,0.1)" }}>
                      <span className="text-[10px] block uppercase font-bold text-amber-400">Hora Lord (Active Planetary Hour)</span>
                      <p className="text-base font-bold text-amber-300">{horaLord}</p>
                      <p className="text-[11px]" style={{ color: "var(--text-secondary)" }}>Directly governs the psychological intent of query</p>
                    </div>

                    <div className="rounded-xl border p-4 space-y-1" style={{ borderColor: "rgba(16,185,129,0.4)", backgroundColor: "rgba(16,185,129,0.1)" }}>
                      <span className="text-[10px] block uppercase font-bold text-emerald-400">Moon Condition</span>
                      <p className="text-base font-bold text-emerald-300">{moonPlanet?.sign || "Scorpio"} ({moonPlanet?.nakshatra})</p>
                      <p className="text-[11px]" style={{ color: "var(--text-secondary)" }}>{timing?.moon_cycle || "Waxing Shukla Paksha"}</p>
                    </div>
                  </div>

                  {/* 5-Fold Ruling Planets Matrix */}
                  <div className="rounded-2xl border p-6 space-y-4" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}>
                    <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                      5-Fold Krishnamurti Ruling Planets (RP) Hierarchy
                    </h3>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="border-b font-semibold text-[11px]" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                          <tr>
                            <th className="py-2.5 px-3">RP Factor</th>
                            <th className="py-2.5 px-3">Sign Lord (Rashi)</th>
                            <th className="py-2.5 px-3">Star Lord (Nakshatra)</th>
                            <th className="py-2.5 px-3">Sub Lord (CSL)</th>
                            <th className="py-2.5 px-3">Sub-Sub Lord</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                          {rpEntries.map((e, idx) => (
                            <tr key={idx} className="hover:bg-white/[0.02]">
                              <td className="py-2.5 px-3 font-bold text-cyan-400">{e.point_name}</td>
                              <td className="py-2.5 px-3 font-bold" style={{ color: "var(--text-primary)" }}>{e.sign_lord}</td>
                              <td className="py-2.5 px-3 text-amber-400">{e.star_lord}</td>
                              <td className="py-2.5 px-3 text-emerald-400 font-bold">{e.sub_lord}</td>
                              <td className="py-2.5 px-3" style={{ color: "var(--text-muted)" }}>{e.sub_sub_lord}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* ── TAB 6: TIMING & TIMELINE ── */}
              {activeTab === "Timing & Timeline" && (
                <div className="space-y-6">
                  {/* Event Horizon Timeline Visualizer */}
                  <div className="rounded-2xl border p-6 space-y-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}>
                    <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                        <span>⏳</span> Fructification Timeline &amp; Transit Milestone Tracker
                      </h3>
                      <span className="text-xs font-mono font-bold text-emerald-400">
                        {timing?.likely_window || "Aug 2026 – Nov 2026"}
                      </span>
                    </div>

                    {/* Timeline Stages Bar */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Stage 1 */}
                      <div className="rounded-xl border p-4 space-y-2" style={{ borderColor: "rgba(6,182,212,0.4)", backgroundColor: "rgba(6,182,212,0.08)" }}>
                        <div className="flex items-center justify-between text-xs font-bold text-cyan-300">
                          <span>STAGE 1: Immediate Trigger</span>
                          <span>Days 1–14</span>
                        </div>
                        <p className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
                          Moon Transit over CSL &amp; Hora Activation
                        </p>
                        <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                          Moon passes through trigger signs, contacting query significator cusps to catalyze response.
                        </p>
                      </div>

                      {/* Stage 2 */}
                      <div className="rounded-xl border p-4 space-y-2" style={{ borderColor: "rgba(245,158,11,0.4)", backgroundColor: "rgba(245,158,11,0.08)" }}>
                        <div className="flex items-center justify-between text-xs font-bold text-amber-300">
                          <span>STAGE 2: Operating Dasha Window</span>
                          <span>Weeks 2–8</span>
                        </div>
                        <p className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
                          {timing?.antardasha || "Mercury Antardasha"} Active
                        </p>
                        <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                          Operating Vimshottari period connects with key bhavas to facilitate outcome.
                        </p>
                      </div>

                      {/* Stage 3 */}
                      <div className="rounded-xl border p-4 space-y-2" style={{ borderColor: "rgba(16,185,129,0.4)", backgroundColor: "rgba(16,185,129,0.08)" }}>
                        <div className="flex items-center justify-between text-xs font-bold text-emerald-300">
                          <span>STAGE 3: Major Transit Support</span>
                          <span>Months 2–4</span>
                        </div>
                        <p className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
                          Jupiter Transit Support
                        </p>
                        <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                          {timing?.transit_support || "Jupiter direct transit cements expansion and stability."}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Dasha Periods Breakdown */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="rounded-xl border p-4 space-y-2" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}>
                      <h4 className="text-xs font-bold uppercase text-cyan-400">Vimshottari Dasha at Query Moment</h4>
                      <div className="space-y-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                        <p><strong style={{ color: "var(--text-primary)" }}>Mahadasha:</strong> {timing?.dasha_mahadasha || "Mercury Mahadasha"}</p>
                        <p><strong style={{ color: "var(--text-primary)" }}>Antardasha:</strong> {timing?.antardasha || "Saturn Antardasha"}</p>
                      </div>
                    </div>

                    <div className="rounded-xl border p-4 space-y-2" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}>
                      <h4 className="text-xs font-bold uppercase text-amber-400">Transit (Gochara) Status</h4>
                      <div className="space-y-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                        <p><strong style={{ color: "var(--text-primary)" }}>Transit Support:</strong> {timing?.transit_support || "Favorable"}</p>
                        <p><strong style={{ color: "var(--text-primary)" }}>Moon Cycle:</strong> {timing?.moon_cycle || "Waxing Shukla Paksha"}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ── TAB 7: AI ASTROLOGER ── */}
              {activeTab === "AI Astrologer" && (
                <div className="space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                    AI Astrologer Deep Interpretation
                  </h3>
                  <div className="rounded-2xl border p-6 space-y-4 text-xs leading-relaxed" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)", color: "var(--text-secondary)" }}>
                    <div
                      className="rounded-xl border p-3 font-bold"
                      style={{
                        borderColor: indicationColor + "40",
                        backgroundColor: indicationColor + "15",
                        color: indicationColor,
                      }}
                    >
                      Astrological Summary: {indicationText} ({confidence}% Confidence)
                    </div>
                    <p>
                      {summaryText || `The Prashna Lagna ${ascendantSign} (${ascendantDegreeStr}), operating Day Lord (${dayLord}), and the 10th Cuspal Sub-Lord demonstrate strong synergy. Benefic alignment promises positive fruition within the ${timing?.likely_window || "Aug 2026 – Nov 2026"} window.`}
                    </p>
                    <div className="space-y-2 pt-2 border-t" style={{ borderColor: "var(--border-primary)" }}>
                      <p className="font-bold text-cyan-400">Actionable Guidance &amp; Conclusions:</p>
                      <ul className="list-disc pl-5 space-y-1">
                        {conclusions.length > 0 ? (
                          conclusions.map((c, i) => <li key={i}>{c}</li>)
                        ) : (
                          <>
                            <li>Maintain positive initiative and direct communication with key decision makers.</li>
                            <li>Follow through with thorough verification during the timing window.</li>
                            <li>Favorable event fruition expected around {timing?.likely_window || "Aug 2026 – Nov 2026"}.</li>
                          </>
                        )}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

            </div>
          </div>
        )}
      </div>
    </div>
  );
}
