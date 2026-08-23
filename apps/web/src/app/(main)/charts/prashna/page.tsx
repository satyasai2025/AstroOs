"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { HoraryDataEntryModal, type HoraryFormData } from "@/components/prashna/HoraryDataEntryModal";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
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

const CATALOG_ARABIC_PARTS = [
  { name: "Spirit", category: "Classical Core", day_formula: "Asc + Sun - Moon", night_formula: "Asc + Moon - Sun", description: "Soul, intellect, conscious intention, and spiritual essence." },
  { name: "Fortuna", category: "Classical Core", day_formula: "Asc + Moon - Sun", night_formula: "Asc + Sun - Moon", description: "Physical prosperity, material circumstances, health, and luck." },
  { name: "Surgery", category: "Medical & Health", day_formula: "Asc + Saturn - Mars", night_formula: "Asc + Mars - Saturn", description: "Surgical procedures, incisions, and sharp medical interventions." },
  { name: "Abundance in Home", category: "Domestic & Real Estate", day_formula: "Asc + Sun - Moon", night_formula: "Asc + Sun - Moon", description: "Domestic prosperity, comfort, peace, and household abundance." },
  { name: "Accomplishment", category: "Career & Success", day_formula: "Asc + Sun - Jupiter", night_formula: "Asc + Jupiter - Sun", description: "Successful completion, mastery, and professional attainment." },
  { name: "Activity", category: "Enterprise & Energy", day_formula: "Asc + Mars - Venus", night_formula: "Asc + Venus - Mars", description: "Energetic initiative, active pursuit, and physical enterprise." },
  { name: "Administrators", category: "Governance & Power", day_formula: "Asc + Mars - Mercury", night_formula: "Asc + Mercury - Mars", description: "Administrative authority, managerial executives, and civil officers." },
  { name: "Advancement", category: "Career & Success", day_formula: "Asc + Sun - Saturn", night_formula: "Asc + Saturn - Sun", description: "Promotion, status elevation, career rank rise, and social elevation." },
  { name: "Agriculture", category: "Domestic & Real Estate", day_formula: "Asc + Saturn - Venus", night_formula: "Asc + Venus - Saturn", description: "Land cultivation, farming yield, harvest, and estate produce." },
  { name: "Allegiance", category: "Social & Relations", day_formula: "Asc + Saturn - Sun", night_formula: "Asc + Sun - Saturn", description: "Loyalty, oaths, fidelity, trustworthy partnerships, and devotion." },
  { name: "Aloofness", category: "Social & Relations", day_formula: "Asc + Moon - Mars", night_formula: "Asc + Mars - Moon", description: "Detachment, solitude, emotional reserve, and contemplative distance." },
  { name: "Anareta I", category: "Medical & Health", day_formula: "Asc + Moon - Asc Lord", night_formula: "Asc + Asc Lord - Moon", description: "Severe vulnerability point, vital crisis, and critical health risk." },
  { name: "Anareta II", category: "Medical & Health", day_formula: "Asc + Mars - Moon", night_formula: "Asc + Moon - Mars", description: "Secondary life-taking index, accidents, and sudden physical crises." },
  { name: "Ancestors", category: "Lineage & Family", day_formula: "Asc + Mars - Saturn", night_formula: "Asc + Saturn - Mars", description: "Paternal ancestors, ancestral legacy, ancestral karma, and blessings." },
  { name: "Ancestors & Kin", category: "Lineage & Family", day_formula: "Asc + Saturn - Jupiter", night_formula: "Asc + Jupiter - Saturn", description: "Extended kinship relations, family inheritance, and roots." },
  { name: "Appreciation", category: "Social & Relations", day_formula: "Asc + Venus - Sun", night_formula: "Asc + Sun - Venus", description: "Public goodwill, recognition, esteem, gratitude, and affectionate regard." },
  { name: "Aptness", category: "Intellect & Talent", day_formula: "Asc + Mercury - Jupiter", night_formula: "Asc + Jupiter - Mercury", description: "Inherent aptitude, sharp learning capacity, and skillful application." },
  { name: "Acquaintances", category: "Social & Relations", day_formula: "Asc + Sun - Mercury", night_formula: "Asc + Mercury - Sun", description: "High-standing contacts, VIP associates, aristocratic patrons, and mentors." },
  { name: "Armies & Police", category: "Governance & Power", day_formula: "Asc + Saturn - Mars", night_formula: "Asc + Mars - Saturn", description: "Armed forces, defense, law enforcement, policing, and security." },
  { name: "Art", category: "Intellect & Talent", day_formula: "Asc + Venus - Mercury", night_formula: "Asc + Mercury - Venus", description: "Artistic creations, aesthetics, design, poetry, drama, and music." },
  { name: "Astrology & Occult", category: "Intellect & Talent", day_formula: "Asc + Mercury - Rahu", night_formula: "Asc + Rahu - Mercury", description: "Astrological intuition, divination, esoteric science, and occult research." },
  { name: "Boldness & Courage", category: "Enterprise & Energy", day_formula: "Asc + Moon - Mars", night_formula: "Asc + Mars - Moon", description: "Valor, fearlessness, enterprise in competition, and daring action." },
  { name: "Business & Commerce", category: "Wealth & Finance", day_formula: "Asc + Mercury - Sun", night_formula: "Asc + Sun - Mercury", description: "Mercantile transactions, trading profit, business agreements, and retail." },
  { name: "Career Success", category: "Career & Success", day_formula: "Asc + Moon - Saturn", night_formula: "Asc + Saturn - Moon", description: "Vocation, professional renown, occupational stability, and livelihood." },
  { name: "Children", category: "Lineage & Family", day_formula: "Asc + Saturn - Jupiter", night_formula: "Asc + Jupiter - Saturn", description: "Progeny, conception, child-birth, relations with offspring, and succession." },
  { name: "Chronic Illness", category: "Medical & Health", day_formula: "Asc + Mars - Saturn", night_formula: "Asc + Saturn - Mars", description: "Protracted ailments, constitutional weaknesses, and lingering disorders." },
  { name: "Commerce & Goods", category: "Wealth & Finance", day_formula: "Asc + Sun - Mercury", night_formula: "Asc + Mercury - Sun", description: "Trading commodities, merchandise inventory, shipping, and exchange." },
  { name: "Debt & Obligations", category: "Wealth & Finance", day_formula: "Asc + Saturn - Mercury", night_formula: "Asc + Mercury - Saturn", description: "Loans, credit agreements, debts, borrowing conditions, and repayment." },
  { name: "Defeat & Loss", category: "Crisis & Conflict", day_formula: "Asc + Sun - Mars", night_formula: "Asc + Mars - Sun", description: "Adversity in contests, setbacks, courtroom losses, and competition hurdles." },
  { name: "Fame & Celebrity", category: "Career & Success", day_formula: "Asc + Jupiter - Sun", night_formula: "Asc + Sun - Jupiter", description: "Public renown, high reputation, widespread honor, and standing." },
  { name: "Father", category: "Lineage & Family", day_formula: "Asc + Sun - Saturn", night_formula: "Asc + Saturn - Sun", description: "Paternal fortune, father's longevity, paternal inheritance, and guidance." },
  { name: "Mother", category: "Lineage & Family", day_formula: "Asc + Moon - Venus", night_formula: "Asc + Venus - Moon", description: "Maternal wellbeing, mother's longevity, nurturance, and affection." },
  { name: "Marriage (Men)", category: "Marriage & Partnership", day_formula: "Asc + Venus - Saturn", night_formula: "Asc + Saturn - Venus", description: "Spouse attraction, wedding timing, partnership harmony, and bliss." },
  { name: "Marriage (Women)", category: "Marriage & Partnership", day_formula: "Asc + Saturn - Venus", night_formula: "Asc + Venus - Saturn", description: "Nuptials, husband profile, marriage suitability, and partnership." },
  { name: "Lawsuits & Disputes", category: "Crisis & Conflict", day_formula: "Asc + Mercury - Mars", night_formula: "Asc + Mars - Mercury", description: "Judicial hearings, disputes, courtroom advocacy, and settlements." },
  { name: "Lost Property", category: "Crisis & Conflict", day_formula: "Asc + Mars - Moon", night_formula: "Asc + Moon - Mars", description: "Misplaced items, stolen goods, recovery potential, and directional clues." },
  { name: "Travel & Relocation", category: "Travel & Exploration", day_formula: "Asc + Jupiter - Mercury", night_formula: "Asc + Mercury - Jupiter", description: "Long-distance travel, foreign relocation, pilgrimages, and overseas." },
  { name: "Treasure & Windfall", category: "Wealth & Finance", day_formula: "Asc + Moon - Mars", night_formula: "Asc + Mars - Moon", description: "Windfalls, hidden treasures, unearned gains, and sudden assets." },
  { name: "Victory & Triumph", category: "Crisis & Conflict", day_formula: "Asc + Jupiter - Mars", night_formula: "Asc + Mars - Jupiter", description: "Overcoming rivals, triumphant conclusion, negotiations, and conquest." },
  { name: "Wisdom & Higher Ed", category: "Intellect & Talent", day_formula: "Asc + Sun - Saturn", night_formula: "Asc + Saturn - Sun", description: "Philosophical insights, university scholarship, and research intellect." },
];

export default function PrashnaPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [topChartTab, setTopChartTab] = useState<"Chart" | "Details" | "Panchanga" | "KP Snapshot" | "Aspects">("Chart");
  const [subTab, setSubTab] = useState<"Bas" | "Sig" | "Asp" | "Arb">("Arb");

  const [formData, setFormData] = useState<HoraryFormData>({
    name: "Kunal Bhagia",
    gender: "Male",
    horaryNumber: 14,
    horarySystem: "kp_249",
    isTimeChart: false,
    date: "2026-08-22",
    time: "12:22:00",
    place: "Pune, Maharashtra, India",
    latitude: 18.5204,
    longitude: 73.8567,
    gmt: 5.5,
    dst: 0,
    question: "Will I get selected for this job?",
  });

  // Arabic Parts Filters & Catalog State
  const [arbSearch, setArbSearch] = useState("");
  const [filterSgL, setFilterSgL] = useState("Show All");
  const [filterStL, setFilterStL] = useState("Show All");
  const [filterSL, setFilterSL] = useState("Show All");
  const [filterSSL, setFilterSSL] = useState("Show All");
  const [expandedParts, setExpandedParts] = useState<Record<string, boolean>>({
    Fortuna: true,
    Surgery: true,
    "Abundance in the Home": true,
  });

  const [catalogSearch, setCatalogSearch] = useState("");
  const [catalogCategory, setCatalogCategory] = useState("Show All");
  const [showArbGuideModal, setShowArbGuideModal] = useState(false);

  // AI Drawer State
  const [isAiDrawerOpen, setIsAiDrawerOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Computed State
  const [planets, setPlanets] = useState<PlanetRow[]>([]);
  const [cusps, setCusps] = useState<HouseCuspRow[]>([]);
  const [arabicParts, setArabicParts] = useState<ArabicPartItem[]>([]);
  const [rpCt, setRpCt] = useState<RulingPlanetItem[]>([]);
  const [rpRt, setRpRt] = useState<RulingPlanetItem[]>([]);
  const [evidence, setEvidence] = useState<KeyEvidence[]>([]);
  const [relevantHouses, setRelevantHouses] = useState<RelevantHouse[]>([]);
  const [timing, setTiming] = useState<TimingIndication | null>(null);
  const [supportingRules, setSupportingRules] = useState<SupportingRule[]>([]);
  const [contradictions, setContradictions] = useState<ContradictionAlert[]>([]);
  const [confidence, setConfidence] = useState(88);
  const [verdict, setVerdict] = useState<"YES" | "NO" | "MIXED">("YES");
  const [ascendantSign, setAscendantSign] = useState("Aries");
  const [ascendantDegreeStr, setAscendantDegreeStr] = useState("00° 00' 00\"");

  // Fetch / Compute Horary from Backend API
  const calculateHorary = async (data: HoraryFormData) => {
    setLoading(true);
    try {
      const dt = new Date(`${data.date}T${data.time}Z`).toISOString();
      const payload = {
        name: data.name,
        gender: data.gender,
        question: data.question,
        moment_utc: dt,
        latitude: data.latitude,
        longitude: data.longitude,
        place_name: data.place,
        timezone_offset: data.gmt,
        horary_number: data.isTimeChart ? null : Number(data.horaryNumber),
        horary_system: data.horarySystem,
        ayanamsa: "lahiri",
      };

      const res = await api.post<any>("/api/v1/prashna/calculate", payload);

      if (res) {
        setPlanets(res.planets || []);
        setCusps(res.cusps || []);
        setArabicParts(res.arabic_parts || []);
        setRpCt(res.ruling_planets_ct?.entries || []);
        setRpRt(res.ruling_planets_rt?.entries || []);
        setEvidence(res.judgement?.key_evidences || []);
        setRelevantHouses(res.judgement?.relevant_houses || []);
        setTiming(res.judgement?.timing || null);
        setSupportingRules(res.judgement?.supporting_rules || []);
        setContradictions(res.judgement?.contradictions || []);
        setConfidence(res.judgement?.confidence_percentage || 85);
        setVerdict(res.judgement?.verdict || "YES");

        if (res.cusps && res.cusps.length > 0) {
          setAscendantSign(res.cusps[0].sign);
          setAscendantDegreeStr(res.cusps[0].degree_str);
        }
      }
    } catch (err) {
      console.warn("Prashna calculation:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    calculateHorary(formData);
  }, []);

  const handleModalSubmit = (newData: HoraryFormData) => {
    setFormData(newData);
    setIsModalOpen(false);
    calculateHorary(newData);
  };

  const togglePart = (name: string) => {
    setExpandedParts((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  // Convert planets for NorthIndianChart component
  const chartPlanets = useMemo(() => {
    return planets.map((p) => ({
      planet: p.planet,
      rashi: p.sign,
      house_number: p.house_number,
      rashi_degree: p.degree_float,
    }));
  }, [planets]);

  // Filtered Arabic Parts
  const filteredArabicParts = useMemo(() => {
    return arabicParts.filter((p) => {
      if (arbSearch && !p.name.toLowerCase().includes(arbSearch.toLowerCase()) && !p.category.toLowerCase().includes(arbSearch.toLowerCase())) {
        return false;
      }
      if (filterSgL !== "Show All" && p.sign_lord.toLowerCase() !== filterSgL.toLowerCase()) return false;
      if (filterStL !== "Show All" && p.star_lord.toLowerCase() !== filterStL.toLowerCase()) return false;
      if (filterSL !== "Show All" && p.sub_lord.toLowerCase() !== filterSL.toLowerCase()) return false;
      if (filterSSL !== "Show All" && p.sub_sub_lord.toLowerCase() !== filterSSL.toLowerCase()) return false;
      return true;
    });
  }, [arabicParts, arbSearch, filterSgL, filterStL, filterSL, filterSSL]);

  // Filtered Catalog Arabic Parts (40 Sahams)
  const filteredCatalogArabicParts = useMemo(() => {
    return CATALOG_ARABIC_PARTS.filter((p) => {
      const matchesSearch =
        catalogSearch === "" ||
        p.name.toLowerCase().includes(catalogSearch.toLowerCase()) ||
        p.category.toLowerCase().includes(catalogSearch.toLowerCase()) ||
        p.day_formula.toLowerCase().includes(catalogSearch.toLowerCase()) ||
        p.night_formula.toLowerCase().includes(catalogSearch.toLowerCase()) ||
        p.description.toLowerCase().includes(catalogSearch.toLowerCase());
      const matchesCat =
        catalogCategory === "Show All" || p.category === catalogCategory;
      return matchesSearch && matchesCat;
    });
  }, [catalogSearch, catalogCategory]);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 p-4 md:p-6 space-y-6">
      {/* ── Top Header & Breadcrumb ── */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <span>Prashna (Horary) &amp; Event Combinations</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/15 text-cyan-900 dark:text-cyan-300 border border-cyan-600/30 font-semibold">
              KP Horary 1–249 · 1–2193
            </span>
            {loading && (
              <span className="text-xs animate-pulse font-mono text-amber-800 dark:text-amber-300">
                ⚡ Calculating...
              </span>
            )}
          </h1>
          <nav aria-label="Breadcrumb" className="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-1.5 mt-1">
            <Link href="/" className="hover:text-slate-900 dark:hover:text-slate-200">Home</Link>
            <span>›</span>
            <Link href="/charts" className="hover:text-slate-900 dark:hover:text-slate-200">Charts</Link>
            <span>›</span>
            <span className="text-cyan-800 dark:text-cyan-300 font-semibold">Prashna (Horary)</span>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-1.5 rounded-xl bg-cyan-700 hover:bg-cyan-800 text-white px-4 py-2 text-xs font-semibold shadow-sm transition"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 20h9" />
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
            </svg>
            <span>+ New Horary Query</span>
          </button>
          <button
            type="button"
            onClick={() => setIsAiDrawerOpen(true)}
            className="flex items-center gap-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3.5 py-2 text-xs font-semibold text-slate-800 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
          >
            <span>✨ AI Astrologer</span>
          </button>
        </div>
      </div>

      {/* ── Top Grid: Section 1 & 2 (Left) + Chart & Tables (Right) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (4 cols): 1. Prashna Input & 2. Horary Judgement */}
        <div className="lg:col-span-4 space-y-6">
          {/* Section 1: PRASHNA INPUT */}
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                1. Prashna Input
              </h2>
              <button
                type="button"
                onClick={() => setIsModalOpen(true)}
                className="text-xs font-semibold text-cyan-800 dark:text-cyan-300 hover:underline"
              >
                Edit Details
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-600 dark:text-slate-400 block text-[11px]">Question</span>
                <div className="mt-1 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/70 p-3 text-slate-900 dark:text-slate-100 font-medium leading-relaxed">
                  &ldquo;{formData.question}&rdquo;
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-slate-600 dark:text-slate-400 text-[11px] block">Date</span>
                  <div className="mt-1 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 px-2.5 py-1.5 text-slate-800 dark:text-slate-200 font-mono">
                    {formData.date}
                  </div>
                </div>
                <div>
                  <span className="text-slate-600 dark:text-slate-400 text-[11px] block">Time</span>
                  <div className="mt-1 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 px-2.5 py-1.5 text-slate-800 dark:text-slate-200 font-mono">
                    {formData.time}
                  </div>
                </div>
              </div>

              <div>
                <span className="text-slate-600 dark:text-slate-400 text-[11px] block">Location</span>
                <div className="mt-1 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 px-2.5 py-1.5 text-slate-800 dark:text-slate-200">
                  {formData.place}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-slate-600 dark:text-slate-400 text-[11px] block">Timezone</span>
                  <div className="mt-1 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 px-2.5 py-1.5 text-slate-800 dark:text-slate-200">
                    Asia/Kolkata (+05:30)
                  </div>
                </div>
                <div>
                  <span className="text-slate-600 dark:text-slate-400 text-[11px] block">Horary Number</span>
                  <div className="mt-1 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 px-2.5 py-1.5 text-cyan-800 dark:text-cyan-300 font-bold font-mono">
                    {formData.isTimeChart ? "Time Chart" : `#${formData.horaryNumber} (${formData.horarySystem})`}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: HORARY JUDGEMENT */}
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm text-center space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
              2. Horary Judgement
            </h2>

            <div className="flex justify-center">
              <div
                className="px-6 py-1.5 rounded-full text-base font-extrabold tracking-wider inline-flex items-center gap-2"
                style={{
                  background: verdict === "YES" ? "rgba(6, 95, 70, 0.15)" : verdict === "NO" ? "rgba(159, 18, 57, 0.15)" : "rgba(180, 83, 9, 0.15)",
                  color: verdict === "YES" ? "#065f46" : verdict === "NO" ? "#9f1239" : "#92400e",
                  border: `1px solid ${verdict === "YES" ? "rgba(6, 95, 70, 0.4)" : verdict === "NO" ? "rgba(159, 18, 57, 0.4)" : "rgba(180, 83, 9, 0.4)"}`,
                }}
              >
                <span className="w-2.5 h-2.5 rounded-full animate-pulse" style={{ background: "currentColor" }}></span>
                <span>VERDICT: {verdict}</span>
              </div>
            </div>

            {/* Radial Gauge */}
            <div className="relative flex flex-col items-center justify-center pt-2">
              <svg className="w-40 h-40 transform -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="transparent"
                  stroke="currentColor"
                  strokeWidth="8"
                  className="text-slate-200 dark:text-slate-800"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="transparent"
                  stroke={confidence >= 65 ? "#047857" : "#b45309"}
                  strokeWidth="8"
                  strokeDasharray="251.2"
                  strokeDashoffset={251.2 * (1 - (confidence / 100) * 0.75)}
                  strokeLinecap="round"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100">{confidence}%</span>
                <p className="text-[10px] text-slate-600 dark:text-slate-400 uppercase tracking-wide">Confidence</p>
              </div>
            </div>

            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-600/30 text-emerald-800 dark:text-emerald-300 text-xs font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 dark:bg-emerald-400 animate-pulse"></span>
              {confidence >= 75 ? "Strong Indication" : "Moderate Indication"}
            </div>
          </div>
        </div>

        {/* Right Column (8 cols): Chart + Sub-Tabs Panel */}
        <div className="lg:col-span-8 space-y-6">
          {/* Top Kundli Chart & Info Card */}
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm space-y-4">
            {/* Chart Sub Tabs */}
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div className="flex items-center space-x-1 sm:space-x-2">
                {(["Chart", "Details", "Panchanga", "KP Snapshot", "Aspects"] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setTopChartTab(tab)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                      topChartTab === tab
                        ? "bg-cyan-700 text-white shadow-sm"
                        : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              <div className="text-xs font-medium text-slate-800 dark:text-slate-200">
                Prashna Lagna: <span className="text-cyan-800 dark:text-cyan-300 font-bold font-mono">{ascendantSign} {ascendantDegreeStr}</span>
              </div>
            </div>

            {/* TAB CONTENT: 1. CHART VIEW (Using Official NorthIndianChart) */}
            {topChartTab === "Chart" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
                <div className="flex justify-center p-2">
                  <div className="relative rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2 shadow-sm flex items-center justify-center">
                    <NorthIndianChart
                      title="Horary D1"
                      ascendant={{ rashi: ascendantSign }}
                      planets={chartPlanets}
                      size={280}
                    />
                  </div>
                </div>

                {/* Quick Summary Meta Pills */}
                <div className="space-y-3">
                  <p className="text-xs uppercase font-bold tracking-wider text-slate-600 dark:text-slate-400">Planetary Summary</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5">
                      <span className="text-[10px] text-slate-600 dark:text-slate-400 block">Prashna Lagna</span>
                      <span className="font-bold text-cyan-800 dark:text-cyan-300 font-mono">{ascendantSign} {ascendantDegreeStr}</span>
                    </div>
                    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5">
                      <span className="text-[10px] text-slate-600 dark:text-slate-400 block">Moon Position</span>
                      <span className="font-bold text-slate-800 dark:text-slate-200 font-mono">
                        {planets.find((p) => p.planet.toLowerCase() === "moon")?.sign || "Cancer"} {planets.find((p) => p.planet.toLowerCase() === "moon")?.degree_str || ""}
                      </span>
                    </div>
                    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5">
                      <span className="text-[10px] text-slate-600 dark:text-slate-400 block">Sun Position</span>
                      <span className="font-bold text-amber-800 dark:text-amber-300 font-mono">
                        {planets.find((p) => p.planet.toLowerCase() === "sun")?.sign || "Leo"} {planets.find((p) => p.planet.toLowerCase() === "sun")?.degree_str || ""}
                      </span>
                    </div>
                    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5">
                      <span className="text-[10px] text-slate-600 dark:text-slate-400 block">Timing Window</span>
                      <span className="font-bold text-emerald-800 dark:text-emerald-300 font-mono">{timing?.likely_window || "Aug 2026 – Nov 2026"}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB CONTENT: 2. DETAILS VIEW */}
            {topChartTab === "Details" && (
              <div className="space-y-3 text-xs">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-3">
                    <span className="text-[10px] text-slate-600 dark:text-slate-400 block uppercase">Query Location</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200 mt-0.5 block">{formData.place}</span>
                    <span className="text-[11px] text-slate-600 dark:text-slate-400 font-mono">{formData.latitude.toFixed(4)}° N, {formData.longitude.toFixed(4)}° E</span>
                  </div>
                  <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-3">
                    <span className="text-[10px] text-slate-600 dark:text-slate-400 block uppercase">Horary Seed Model</span>
                    <span className="font-bold text-cyan-800 dark:text-cyan-300 mt-0.5 block">{formData.isTimeChart ? "Time Chart" : `#${formData.horaryNumber} (${formData.horarySystem})`}</span>
                    <span className="text-[11px] text-slate-600 dark:text-slate-400">Ayanamsa: Lahiri (Chitra Paksha)</span>
                  </div>
                  <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-3">
                    <span className="text-[10px] text-slate-600 dark:text-slate-400 block uppercase">Calculated Lagna</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200 mt-0.5 block font-mono">{ascendantSign} {ascendantDegreeStr}</span>
                    <span className="text-[11px] text-slate-600 dark:text-slate-400">House System: Placidus / KP</span>
                  </div>
                </div>
              </div>
            )}

            {/* TAB CONTENT: 3. PANCHANGA VIEW */}
            {topChartTab === "Panchanga" && (
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 text-xs text-center">
                <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5">
                  <span className="text-[10px] text-slate-600 dark:text-slate-400 block uppercase">Vara (Day)</span>
                  <span className="font-bold text-cyan-800 dark:text-cyan-300 mt-1 block">Saturn (Shani)</span>
                </div>
                <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5">
                  <span className="text-[10px] text-slate-600 dark:text-slate-400 block uppercase">Tithi</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200 mt-1 block">Shukla Navami</span>
                </div>
                <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5">
                  <span className="text-[10px] text-slate-600 dark:text-slate-400 block uppercase">Nakshatra</span>
                  <span className="font-bold text-amber-800 dark:text-amber-300 mt-1 block">Pushya (Pada 4)</span>
                </div>
                <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5">
                  <span className="text-[10px] text-slate-600 dark:text-slate-400 block uppercase">Yoga</span>
                  <span className="font-bold text-emerald-800 dark:text-emerald-300 mt-1 block">Indra Yoga</span>
                </div>
                <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5">
                  <span className="text-[10px] text-slate-600 dark:text-slate-400 block uppercase">Karana</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200 mt-1 block">Balava Karana</span>
                </div>
              </div>
            )}

            {/* TAB CONTENT: 4. KP SNAPSHOT */}
            {topChartTab === "KP Snapshot" && (
              <div className="space-y-2 text-xs">
                <p className="text-slate-600 dark:text-slate-400 text-[11px] mb-2 font-medium">
                  Core Cuspal Sub-Lord (CSL) and Star Lord significations for primary inquiry houses:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 font-mono">
                  {cusps.filter((c) => [1, 6, 7, 10, 11].includes(c.house)).map((c) => (
                    <div key={c.house} className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5">
                      <div className="flex justify-between font-bold text-slate-900 dark:text-slate-100 font-sans">
                        <span>Cusp {c.house} ({c.sign})</span>
                        <span className="text-cyan-800 dark:text-cyan-300 font-mono">CSL: {c.sub_lord}</span>
                      </div>
                      <div className="mt-1 text-[11px] text-slate-600 dark:text-slate-400">
                        <span>StL: {c.star_lord} · SSL: {c.sub_sub_lord}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB CONTENT: 5. ASPECTS */}
            {topChartTab === "Aspects" && (
              <div className="space-y-2 text-xs text-slate-800 dark:text-slate-200 p-1">
                <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-3 space-y-1.5">
                  <div className="flex items-center gap-2 font-semibold text-emerald-800 dark:text-emerald-300">
                    <span>✓</span>
                    <span>Jupiter Benefic Trine on Moon (120° Auspicious Aspect)</span>
                  </div>
                  <p className="text-slate-600 dark:text-slate-400 pl-4">
                    Jupiter in Taurus casts a harmonious 9th drishti onto Moon in Pushya nakshatra, providing protection, credibility, and authority approval.
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-3 space-y-1.5">
                  <div className="flex items-center gap-2 font-semibold text-amber-800 dark:text-amber-300">
                    <span>⚠️</span>
                    <span>Saturn Aspect on 7th House (Procedural Scrutiny)</span>
                  </div>
                  <p className="text-slate-600 dark:text-slate-400 pl-4">
                    Saturn from Pisces aspects the 7th house (negotiations / appointment decisions), indicating patience and thorough technical verification needed.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Sub-Tabs Full Width Workspace Panel: Bas / Sig / Asp / Arb ── */}
      <div className="w-full rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
          <div className="flex items-center space-x-1.5">
                {(["Bas", "Sig", "Asp", "Arb"] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setSubTab(tab)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                      subTab === tab
                        ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100"
                    }`}
                  >
                    {tab === "Arb" ? "Arb (Arabic Parts)" : tab}
                  </button>
                ))}
              </div>
              <span className="text-xs text-slate-600 dark:text-slate-400 font-mono">
                {arabicParts.length} Parts Loaded
              </span>
            </div>

            {/* TAB: ARB (Arabic Parts Explorer) */}
            {subTab === "Arb" && (
              <div className="space-y-5">
                {/* Feature Summary Pills (Brought up to Top) */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs text-center font-sans">
                  <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5 shadow-2xs">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block uppercase font-bold">Catalog Scope</span>
                    <span className="font-extrabold text-cyan-800 dark:text-cyan-300 mt-0.5 block text-xs">✨ 40 Classical Sahams</span>
                  </div>
                  <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5 shadow-2xs">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block uppercase font-bold">Formula Mode</span>
                    <span className="font-extrabold text-amber-800 dark:text-amber-300 mt-0.5 block text-xs">☀️ Day / 🌙 Night Altitude</span>
                  </div>
                  <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5 shadow-2xs">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block uppercase font-bold">KP Precision</span>
                    <span className="font-extrabold text-emerald-800 dark:text-emerald-300 mt-0.5 block text-xs">🪐 4-Tier Sub-Lord Subdivisions</span>
                  </div>
                  <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-2.5 shadow-2xs">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block uppercase font-bold">Horary Outcome</span>
                    <span className="font-extrabold text-slate-800 dark:text-slate-200 mt-0.5 block text-xs">🎯 Objective Event Fructification</span>
                  </div>
                </div>

                {/* Main 2-Column Responsive Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
                  {/* LEFT COLUMN (7 cols): Calculated Sahams in Chart */}
                  <div className="lg:col-span-7 space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                        <span>📊</span> Calculated Sahams (Current Chart)
                      </h3>
                      <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                        {filteredArabicParts.length} / {arabicParts.length} Parts
                      </span>
                    </div>

                    {/* Search and Filters */}
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5 text-xs">
                      <input
                        type="text"
                        aria-label="Search Sahams and Lots"
                        placeholder="Search Saham..."
                        value={arbSearch}
                        onChange={(e) => setArbSearch(e.target.value)}
                        className="col-span-2 sm:col-span-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-2 py-1 text-xs text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:border-cyan-500 focus:outline-none"
                      />
                      <select
                        aria-label="Filter by Sign Lord"
                        value={filterSgL}
                        onChange={(e) => setFilterSgL(e.target.value)}
                        className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-1.5 py-1 text-xs text-slate-800 dark:text-slate-200 focus:border-cyan-500 focus:outline-none"
                      >
                        <option value="Show All">All SgL</option>
                        {["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"].map((p) => (
                          <option key={p} value={p}>{p}</option>
                        ))}
                      </select>
                      <select
                        aria-label="Filter by Star Lord"
                        value={filterStL}
                        onChange={(e) => setFilterStL(e.target.value)}
                        className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-1.5 py-1 text-xs text-slate-800 dark:text-slate-200 focus:border-cyan-500 focus:outline-none"
                      >
                        <option value="Show All">All StL</option>
                        {["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"].map((p) => (
                          <option key={p} value={p}>{p}</option>
                        ))}
                      </select>
                      <select
                        aria-label="Filter by Sub Lord"
                        value={filterSL}
                        onChange={(e) => setFilterSL(e.target.value)}
                        className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-1.5 py-1 text-xs text-slate-800 dark:text-slate-200 focus:border-cyan-500 focus:outline-none"
                      >
                        <option value="Show All">All SL</option>
                        {["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"].map((p) => (
                          <option key={p} value={p}>{p}</option>
                        ))}
                      </select>
                      <select
                        aria-label="Filter by Sub-Sub Lord"
                        value={filterSSL}
                        onChange={(e) => setFilterSSL(e.target.value)}
                        className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-1.5 py-1 text-xs text-slate-800 dark:text-slate-200 focus:border-cyan-500 focus:outline-none"
                      >
                        <option value="Show All">All SSL</option>
                        {["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"].map((p) => (
                          <option key={p} value={p}>{p}</option>
                        ))}
                      </select>
                    </div>

                    {/* Computed Sahams Table */}
                    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 max-h-[460px]">
                      <table className="w-full text-left text-xs">
                        <thead className="sticky top-0 bg-slate-100 dark:bg-slate-950 text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800 font-semibold z-10">
                          <tr>
                            <th className="py-2 px-2.5">Name</th>
                            <th className="py-2 px-2">Sgn</th>
                            <th className="py-2 px-2">Deg</th>
                            <th className="py-2 px-2">SgL</th>
                            <th className="py-2 px-2">StL</th>
                            <th className="py-2 px-2">SL</th>
                            <th className="py-2 px-2">SSL</th>
                            <th className="py-2 px-2">Formula</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-800 dark:text-slate-200 font-mono text-[11px]">
                          {filteredArabicParts.map((p) => (
                            <tr key={p.name} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                              <td className="py-2 px-2.5 font-bold text-slate-900 dark:text-slate-100 font-sans">
                                <button
                                  type="button"
                                  onClick={() => togglePart(p.name)}
                                  className="text-left hover:text-cyan-800 dark:hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
                                >
                                  <span>{expandedParts[p.name] ? "▾" : "▸"}</span>
                                  <span>{p.name}</span>
                                </button>
                                {expandedParts[p.name] && (
                                  <p className="mt-0.5 text-[10px] text-slate-600 dark:text-slate-400 font-normal font-sans leading-tight">
                                    {p.description}
                                  </p>
                                )}
                              </td>
                              <td className="py-2 px-2 text-cyan-800 dark:text-cyan-300 font-bold">{p.rashi}</td>
                              <td className="py-2 px-2">{p.rashi_degree_str}</td>
                              <td className="py-2 px-2 text-slate-700 dark:text-slate-300">{p.sign_lord.slice(0, 2)}</td>
                              <td className="py-2 px-2 text-amber-800 dark:text-amber-300 font-semibold">{p.star_lord.slice(0, 2)}</td>
                              <td className="py-2 px-2 text-rose-800 dark:text-rose-300 font-bold">{p.sub_lord.slice(0, 2)}</td>
                              <td className="py-2 px-2 text-emerald-800 dark:text-emerald-300 font-semibold">{p.sub_sub_lord.slice(0, 2)}</td>
                              <td className="py-2 px-2 text-[10px] text-slate-500 dark:text-slate-400 whitespace-nowrap">{p.formula_used}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Bottom-Left Info (i) Guide Button */}
                    <div className="pt-1 flex items-center justify-between">
                      <button
                        type="button"
                        onClick={() => setShowArbGuideModal(true)}
                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border border-cyan-500/30 bg-cyan-500/10 text-cyan-800 dark:text-cyan-300 text-xs font-bold hover:bg-cyan-500/20 transition cursor-pointer shadow-xs"
                      >
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-cyan-500/20 text-cyan-400 text-xs font-black">i</span>
                        <span>Arabic Parts Calculation &amp; KP Guide</span>
                      </button>
                      <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">
                        Click <strong className="text-cyan-400">i</strong> for Day/Night formulas &amp; KP rules
                      </span>
                    </div>
                  </div>

                  {/* RIGHT COLUMN (5 cols): Available Arabic Parts Catalog (40 Sahams Reference Table) */}
                  <div className="lg:col-span-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                        <span>📚</span> Available Arabic Parts Catalog (40 Sahams)
                      </h3>
                      <span className="text-xs font-bold text-cyan-800 dark:text-cyan-300">
                        {filteredCatalogArabicParts.length} / 40 Registered
                      </span>
                    </div>

                    {/* Catalog Search & Category Filter */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                      <input
                        type="text"
                        placeholder="Search 40 Saham formulas..."
                        value={catalogSearch}
                        onChange={(e) => setCatalogSearch(e.target.value)}
                        className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-2.5 py-1 text-xs text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:border-cyan-500 focus:outline-none"
                      />
                      <select
                        value={catalogCategory}
                        aria-label="Filter Catalog Category"
                        onChange={(e) => setCatalogCategory(e.target.value)}
                        className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-2 py-1 text-xs text-slate-800 dark:text-slate-200 focus:border-cyan-500 focus:outline-none"
                      >
                        <option value="Show All">All Categories</option>
                        <option value="Classical Core">Classical Core</option>
                        <option value="Career & Success">Career &amp; Success</option>
                        <option value="Wealth & Finance">Wealth &amp; Finance</option>
                        <option value="Medical & Health">Medical &amp; Health</option>
                        <option value="Marriage & Partnership">Marriage &amp; Partnership</option>
                        <option value="Lineage & Family">Lineage &amp; Family</option>
                        <option value="Crisis & Conflict">Crisis &amp; Conflict</option>
                        <option value="Intellect & Talent">Intellect &amp; Talent</option>
                        <option value="Travel & Exploration">Travel &amp; Exploration</option>
                        <option value="Domestic & Real Estate">Domestic &amp; Real Estate</option>
                        <option value="Governance & Power">Governance &amp; Power</option>
                        <option value="Social & Relations">Social &amp; Relations</option>
                        <option value="Enterprise & Energy">Enterprise &amp; Energy</option>
                      </select>
                    </div>

                    {/* 40 Classical Sahams Catalog Reference Table */}
                    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 max-h-[460px]">
                      <table className="w-full text-left text-xs">
                        <thead className="sticky top-0 bg-slate-100 dark:bg-slate-950 text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800 font-semibold z-10">
                          <tr>
                            <th className="py-2 px-2.5">Saham / Category</th>
                            <th className="py-2 px-2">☀️ Day Formula</th>
                            <th className="py-2 px-2">🌙 Night Formula</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-800 dark:text-slate-200">
                          {filteredCatalogArabicParts.map((item) => (
                            <tr key={item.name} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                              <td className="py-2 px-2.5">
                                <div className="font-extrabold text-slate-900 dark:text-slate-100">{item.name}</div>
                                <span className="inline-block mt-0.5 px-1.5 py-0.2 text-[9px] font-bold rounded bg-cyan-100 text-cyan-900 border border-cyan-600/30 dark:bg-cyan-950/60 dark:text-cyan-300">
                                  {item.category}
                                </span>
                                <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-tight mt-0.5">
                                  {item.description}
                                </p>
                              </td>
                              <td className="py-2 px-2 font-mono text-[11px] font-bold text-amber-800 dark:text-amber-300 whitespace-nowrap">
                                {item.day_formula}
                              </td>
                              <td className="py-2 px-2 font-mono text-[11px] font-bold text-cyan-800 dark:text-cyan-300 whitespace-nowrap">
                                {item.night_formula}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB: BAS (Basic Planetary Positions & Cusps) */}
            {subTab === "Bas" && (
              <div className="space-y-4">
                <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-50 dark:bg-slate-950/80 text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800 font-semibold">
                      <tr>
                        <th className="py-2 px-3">Pln</th>
                        <th className="py-2 px-3">Sgn</th>
                        <th className="py-2 px-3">Deg</th>
                        <th className="py-2 px-3">Nak</th>
                        <th className="py-2 px-3">SgL</th>
                        <th className="py-2 px-3">StL</th>
                        <th className="py-2 px-3">SL</th>
                        <th className="py-2 px-3">SSL</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-800 dark:text-slate-200">
                      {planets.map((p) => (
                        <tr key={p.planet} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                          <td className="py-2 px-3 font-semibold text-slate-900 dark:text-slate-100 font-sans">{p.planet}</td>
                          <td className="py-2 px-3 text-cyan-800 dark:text-cyan-300 font-semibold">{p.sign}</td>
                          <td className="py-2 px-3">{p.degree_str}</td>
                          <td className="py-2 px-3">{p.nakshatra} ({p.pada})</td>
                          <td className="py-2 px-3 text-slate-700 dark:text-slate-300">{p.sign_lord.slice(0, 2)}</td>
                          <td className="py-2 px-3 text-amber-800 dark:text-amber-300 font-semibold">{p.star_lord.slice(0, 2)}</td>
                          <td className="py-2 px-3 text-rose-800 dark:text-rose-300 font-bold">{p.sub_lord.slice(0, 2)}</td>
                          <td className="py-2 px-3 text-emerald-800 dark:text-emerald-300 font-semibold">{p.sub_sub_lord.slice(0, 2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB: SIG (4-Fold Significators Matrix) */}
            {subTab === "Sig" && (
              <div className="space-y-3">
                <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-50 dark:bg-slate-950/80 text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800 font-semibold">
                      <tr>
                        <th className="py-2 px-3">House</th>
                        <th className="py-2 px-3">Level A (Star of Occ)</th>
                        <th className="py-2 px-3">Level B (Occupant)</th>
                        <th className="py-2 px-3">Level C (Star of Lord)</th>
                        <th className="py-2 px-3">Level D (Lord)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-800 dark:text-slate-200">
                      {cusps.map((c) => {
                        const occupants = planets.filter((p) => p.house_number === c.house).map((p) => p.planet);
                        return (
                          <tr key={c.house} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                            <td className="py-2 px-3 font-semibold text-slate-900 dark:text-slate-100 font-sans">House {c.house}</td>
                            <td className="py-2 px-3 text-emerald-800 dark:text-emerald-300 font-semibold">{occupants.length > 0 ? `${occupants.join(", ")} (Star)` : "—"}</td>
                            <td className="py-2 px-3 text-cyan-800 dark:text-cyan-300 font-semibold">{occupants.join(", ") || "—"}</td>
                            <td className="py-2 px-3 text-amber-800 dark:text-amber-300 font-semibold">{c.star_lord}</td>
                            <td className="py-2 px-3 text-slate-700 dark:text-slate-300">{c.sign_lord}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB: ASP (Aspects) */}
            {subTab === "Asp" && (
              <div className="space-y-3 p-2 text-xs text-slate-800 dark:text-slate-200">
                <p className="font-semibold text-slate-900 dark:text-slate-100">Planetary Drishti &amp; Aspects</p>
                <p>Benefic aspect from Jupiter on Lagna Lord Moon provides auspicious backing. Saturn aspect on 7th cusp indicates procedural scrutiny.</p>
              </div>
            )}
          </div>

      {/* ── Ruling Planets (RP) Dual Tables (CT & RT) ── */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
            Ruling Planets (RP) Analysis
          </h2>
          <span className="text-[11px] text-slate-600 dark:text-slate-400">
            CT: Casting Time · RT: Real Time
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* CT Table */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-3 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-cyan-800 dark:text-cyan-300">
              <span>CT (Casting Time Snapshot)</span>
              <span className="text-[10px] font-mono font-normal text-slate-600 dark:text-slate-400">HL: Sun · DL: Saturn</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="py-1">Point</th>
                    <th className="py-1">SgL</th>
                    <th className="py-1">StL</th>
                    <th className="py-1">SL</th>
                    <th className="py-1">SSL</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-800 dark:text-slate-200">
                  {rpCt.slice(0, 4).map((r) => (
                    <tr key={r.point_name}>
                      <td className="py-1.5 text-slate-900 dark:text-slate-200 font-sans">{r.point_name}</td>
                      <td className="py-1.5 text-slate-600 dark:text-slate-400">{r.sign_lord.slice(0, 2)}</td>
                      <td className="py-1.5 text-amber-800 dark:text-amber-300 font-semibold">{r.star_lord.slice(0, 2)}</td>
                      <td className="py-1.5 text-rose-800 dark:text-rose-300 font-bold">{r.sub_lord.slice(0, 2)}</td>
                      <td className="py-1.5 text-emerald-800 dark:text-emerald-300 font-semibold">{r.sub_sub_lord.slice(0, 2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* RT Table */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-3 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-emerald-800 dark:text-emerald-300">
              <span>RT (Real Time Snapshot)</span>
              <span className="text-[10px] font-mono font-normal text-slate-600 dark:text-slate-400">HL: Moon · DL: Saturn</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="py-1">Point</th>
                    <th className="py-1">SgL</th>
                    <th className="py-1">StL</th>
                    <th className="py-1">SL</th>
                    <th className="py-1">SSL</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-800 dark:text-slate-200">
                  {rpRt.slice(0, 4).map((r) => (
                    <tr key={r.point_name}>
                      <td className="py-1.5 text-slate-900 dark:text-slate-200 font-sans">{r.point_name}</td>
                      <td className="py-1.5 text-slate-600 dark:text-slate-400">{r.sign_lord.slice(0, 2)}</td>
                      <td className="py-1.5 text-amber-800 dark:text-amber-300 font-semibold">{r.star_lord.slice(0, 2)}</td>
                      <td className="py-1.5 text-rose-800 dark:text-rose-300 font-bold">{r.sub_lord.slice(0, 2)}</td>
                      <td className="py-1.5 text-emerald-800 dark:text-emerald-300 font-semibold">{r.sub_sub_lord.slice(0, 2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* ── Section 3: KEY EVIDENCE Table ── */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm space-y-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
          3. Key Evidence
        </h2>
        <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-950/80 text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800 font-semibold">
              <tr>
                <th className="py-2.5 px-3">Factor</th>
                <th className="py-2.5 px-3">Indication</th>
                <th className="py-2.5 px-3">Explanation</th>
                <th className="py-2.5 px-3">Weight</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-800 dark:text-slate-200">
              {evidence.map((e, idx) => (
                <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition">
                  <td className="py-2.5 px-3 font-semibold text-slate-900 dark:text-slate-200">{e.factor}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        e.indication.includes("Positive")
                          ? "bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-600/30"
                          : e.indication === "Neutral"
                          ? "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                          : "bg-rose-500/15 text-rose-800 dark:text-rose-300 border border-rose-600/30"
                      }`}
                    >
                      {e.indication}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">{e.explanation}</td>
                  <td className="py-2.5 px-3 font-mono">
                    <div className="flex items-center gap-2">
                      <span className={e.weight >= 0 ? "text-emerald-800 dark:text-emerald-300 font-bold" : "text-rose-800 dark:text-rose-300 font-bold"}>
                        {e.weight >= 0 ? `+${e.weight}%` : `${e.weight}%`}
                      </span>
                      <div className="w-16 h-1.5 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                        <div
                          className={`h-full ${e.weight >= 0 ? "bg-emerald-600" : "bg-rose-600"}`}
                          style={{ width: `${Math.min(Math.abs(e.weight) * 4, 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Middle Row (Sections 4, 5, 6): Relevant Houses, Timing, Conclusion ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Section 4: Relevant Houses & Lords */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm space-y-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
            4. Relevant Houses &amp; Lords
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 font-semibold">
                <tr>
                  <th className="py-1">House</th>
                  <th className="py-1">Sign</th>
                  <th className="py-1">Lord</th>
                  <th className="py-1">Strength</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-800 dark:text-slate-200">
                {relevantHouses.map((h) => (
                  <tr key={h.house}>
                    <td className="py-1.5 text-slate-900 dark:text-slate-200 font-sans">{h.house}</td>
                    <td className="py-1.5">{h.sign}</td>
                    <td className="py-1.5 text-cyan-800 dark:text-cyan-300 font-bold">{h.lord}</td>
                    <td className="py-1.5">
                      <span className={h.strength === "Strong" ? "text-emerald-800 dark:text-emerald-300 font-bold" : "text-amber-800 dark:text-amber-300 font-semibold"}>
                        {h.strength}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Section 5: Timing Indication */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm space-y-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
            5. Timing Indication
          </h2>
          {timing && (
            <div className="space-y-3 text-xs">
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/70 p-3">
                <span className="text-[10px] text-slate-600 dark:text-slate-400 uppercase tracking-wide block">Likely Timing Window</span>
                <span className="font-bold text-sm text-cyan-800 dark:text-cyan-300 font-mono">{timing.likely_window}</span>
              </div>
              <div className="space-y-1.5 text-slate-800 dark:text-slate-200">
                <p><span className="text-slate-600 dark:text-slate-400">Dasha:</span> {timing.dasha_mahadasha}</p>
                <p><span className="text-slate-600 dark:text-slate-400">Antardasha:</span> {timing.antardasha}</p>
                <p><span className="text-slate-600 dark:text-slate-400">Transit:</span> {timing.transit_support}</p>
                <p><span className="text-slate-600 dark:text-slate-400">Moon:</span> {timing.moon_cycle}</p>
              </div>
            </div>
          )}
        </div>

        {/* Section 6: Conclusion */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm space-y-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
            6. Conclusion
          </h2>
          <div className="space-y-2 text-xs text-slate-800 dark:text-slate-200">
            <div className="flex items-start gap-2">
              <span className="text-emerald-800 dark:text-emerald-300 font-bold">✓</span>
              <span>Strong Lagna and Lagna Lord</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-emerald-800 dark:text-emerald-300 font-bold">✓</span>
              <span>7th &amp; 10th lords support positive event outcome</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-emerald-800 dark:text-emerald-300 font-bold">✓</span>
              <span>Jupiter benefic aspect confirms patronage</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-amber-800 dark:text-amber-300 font-bold">✓</span>
              <span>Procedural scrutiny due to Saturn aspect</span>
            </div>
            <div className="mt-3 rounded-xl border border-emerald-600/30 bg-emerald-500/10 p-3 text-emerald-900 dark:text-emerald-300 font-semibold text-center">
              Result: {verdict} — Favorable Indications for inquiry.
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom Grid: Supporting Rules (7) & Contradictions (8) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section 7: Supporting Rules Triggered */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm space-y-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
            7. Supporting Rules Triggered
          </h2>
          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-950/80 text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800 font-semibold">
                <tr>
                  <th className="py-2 px-3">Rule ID</th>
                  <th className="py-2 px-3">Principle</th>
                  <th className="py-2 px-3">Source</th>
                  <th className="py-2 px-3">Triggered</th>
                  <th className="py-2 px-3">Weight</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-800 dark:text-slate-200">
                {supportingRules.map((r) => (
                  <tr key={r.rule_id}>
                    <td className="py-2 px-3 font-mono font-bold text-cyan-800 dark:text-cyan-300">{r.rule_id}</td>
                    <td className="py-2 px-3 text-slate-900 dark:text-slate-200">{r.rule_principle}</td>
                    <td className="py-2 px-3 italic text-slate-600 dark:text-slate-400">{r.reference}</td>
                    <td className="py-2 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-600/30">
                        {r.triggered}
                      </span>
                    </td>
                    <td className="py-2 px-3 font-mono font-bold text-emerald-800 dark:text-emerald-300">+{r.weight}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Section 8: Contradictions & Precautions */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm space-y-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
            8. Contradictions &amp; Precautions
          </h2>
          <div className="space-y-3 text-xs">
            {contradictions.map((c, idx) => (
              <div key={idx} className="rounded-xl border border-amber-300 dark:border-amber-500/30 bg-amber-50/50 dark:bg-amber-500/10 p-3 space-y-1">
                <div className="flex items-center gap-2 text-amber-900 dark:text-amber-200 font-bold">
                  <span>⚠️</span>
                  <span>{c.title}</span>
                </div>
                <p className="text-slate-800 dark:text-slate-200 pl-6">{c.description}</p>
                <p className="text-amber-950 dark:text-amber-200 pl-6 font-semibold">Advice: {c.advice}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Modal Dialog ── */}
      <HoraryDataEntryModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleModalSubmit}
        initialData={formData}
      />

      {/* ── AI Astrologer Drawer ── */}
      {isAiDrawerOpen && (
        <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl p-6 flex flex-col justify-between animate-in slide-in-from-right duration-200">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="text-xl">✨</span>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base">AI Astrologer Analysis</h3>
              </div>
              <button
                type="button"
                onClick={() => setIsAiDrawerOpen(false)}
                className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-800 dark:text-slate-200">
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 p-3">
                <span className="text-[10px] text-slate-600 dark:text-slate-400 block uppercase">Question Analyzed</span>
                <p className="font-bold text-slate-900 dark:text-slate-100 mt-1">&ldquo;{formData.question}&rdquo;</p>
              </div>

              <div className="rounded-xl border border-emerald-600/30 bg-emerald-500/10 p-3 text-emerald-900 dark:text-emerald-300">
                <span className="font-bold block text-sm">Verdict: {verdict} ({confidence}% Confidence)</span>
                <p className="mt-1 text-xs leading-relaxed text-slate-800 dark:text-slate-200">
                  The primary significators (Houses 10, 6, and 11) and the Lagna Lord Moon are strongly aligned. Jupiter&apos;s aspect brings favorable patronage and decision-maker support.
                </p>
              </div>

              <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 p-3 space-y-2">
                <span className="text-xs font-bold text-cyan-800 dark:text-cyan-300 block">Practical Guidance</span>
                <ul className="list-disc pl-4 space-y-1 text-slate-800 dark:text-slate-200">
                  <li>Focus strongly on technical interview preparation.</li>
                  <li>Anticipate slight procedural scrutiny due to Saturn&apos;s 7th house aspect.</li>
                  <li>Favorable timing window aligns around {timing?.likely_window || "Oct–Nov 2026"}.</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={() => setIsAiDrawerOpen(false)}
              className="w-full rounded-xl bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 py-2.5 text-xs font-semibold hover:opacity-90 transition"
            >
              Close Assistant
            </button>
          </div>
        </div>
      )}
      {/* ── Arabic Parts Calculation & KP Guide Modal ── */}
      {showArbGuideModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div
            className="relative w-full max-w-3xl max-h-[85vh] flex flex-col rounded-2xl border shadow-2xl overflow-hidden font-sans backdrop-blur-md"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
              <div className="flex items-center gap-2.5">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-100 text-cyan-900 border border-cyan-600/40 dark:bg-cyan-950/60 dark:text-cyan-300 font-bold text-sm">i</span>
                <div>
                  <h3 className="text-sm font-extrabold text-slate-900 dark:text-slate-100">Arabic Parts (Sahams) &amp; KP Rules Guide</h3>
                  <p className="text-[11px] text-slate-700 dark:text-slate-300 font-medium">Classical Hermetic / Tajika Formula Mechanics &amp; Event Promise</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowArbGuideModal(false)}
                className="flex h-7 w-7 items-center justify-center rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer font-bold text-xs"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 p-5 overflow-y-auto space-y-4 text-xs leading-relaxed">
              <div className="p-3.5 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-900 dark:text-amber-200 space-y-1">
                <h4 className="text-xs font-bold text-amber-700 dark:text-amber-300 flex items-center gap-1.5">
                  <span>☀️</span> Day vs 🌙 Night Formula Altitude Mechanics
                </h4>
                <p className="text-[11px] font-semibold leading-relaxed text-slate-800 dark:text-slate-200">
                  Arabic Parts (Lots / Sahams) calculate a sensitive longitudinal point by projecting the distance between two significators onto the Ascendant:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
                  <div className="p-2 rounded-lg border" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                    <strong className="text-amber-600 dark:text-amber-400 block font-sans text-xs font-extrabold">Day Birth (Sun above Horizon)</strong>
                    <code className="text-slate-900 dark:text-slate-100 font-bold">Formula: Asc + Planet_B - Planet_A</code>
                  </div>
                  <div className="p-2 rounded-lg border" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                    <strong className="text-cyan-600 dark:text-cyan-400 block font-sans text-xs font-extrabold">Night Birth (Sun below Horizon)</strong>
                    <code className="text-slate-900 dark:text-slate-100 font-bold">Formula: Asc + Planet_A - Planet_B</code>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">How to Interpret Arabic Parts in Prashna / Horary:</h4>
                <ul className="list-disc pl-5 space-y-1.5 text-slate-800 dark:text-slate-200 text-[11px] font-semibold">
                  <li>
                    <strong className="text-cyan-600 dark:text-cyan-400">KP Sub-Lord Fructification</strong>: Check the Sub Lord (SL) of the calculated Saham. If its Star Lord signifies the primary query houses (e.g. 2, 6, 10, 11 for career), the Saham guarantees a successful outcome.
                  </li>
                  <li>
                    <strong className="text-emerald-600 dark:text-emerald-400">Benefic Aspects on Saham Point</strong>: Conjunctions or trine aspects from Jupiter or Venus onto the Saham longitude bring swift, un-obstructed resolution.
                  </li>
                  <li>
                    <strong className="text-amber-600 dark:text-amber-400">Dasha Trigger Intersection</strong>: When the operating Antardasha lord transits over or rules the Saham&apos;s Star Lord, the event manifests within that transit window.
                  </li>
                </ul>
              </div>

              <div className="p-3 rounded-xl border text-[11px] text-slate-700 dark:text-slate-300 font-semibold" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                <strong className="text-amber-600 dark:text-amber-400 font-bold block mb-0.5">📚 Classical Reference Sources:</strong>
                Formulas derived from Al-Biruni&apos;s <em>Book of Instruction in the Elements of the Art of Astrology</em>, Neelakantha&apos;s <em>Tajika Neelakanthi (Sahamadhikara)</em>, and Prof. K.S. Krishnamurti&apos;s <em>KP Readers</em>.
              </div>
            </div>

            <div className="flex justify-end px-5 py-3 border-t" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
              <button
                type="button"
                onClick={() => setShowArbGuideModal(false)}
                className="px-4 py-1.5 rounded-xl text-xs font-bold bg-cyan-700 hover:bg-cyan-600 text-white transition cursor-pointer shadow-xs"
              >
                Close Guide
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
