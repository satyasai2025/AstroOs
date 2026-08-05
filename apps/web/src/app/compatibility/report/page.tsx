"use client";

import {
  bestBetApi,
  compatibilityApi,
  exportApi,
  marriageTimingApi,
  sadhuPadhdhatiApi,
  type BestBetCompatibilityResponse,
  type CompatibilityResponse,
  type MarriageTimingResponse,
  type SadhuPadhdhatiResponse,
  type TransitScanYear,
} from "@/lib/research";
import { AppShell } from "@/components/layout/AppShell";
import { useWorkflowStore } from "@/lib/store";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

type RelationshipType = "marriage" | "business" | "friendship" | "parent_child";

const RELATIONSHIP_LABELS: Record<RelationshipType, string> = {
  marriage: "Marriage Compatibility",
  business: "Business Partnership",
  friendship: "Friendship Compatibility",
  parent_child: "Parent–Child Synastry",
};

const STATUS_COLORS: Record<string, string> = {
  Excellent: "text-emerald-400",
  Good: "text-amber-400",
  Average: "text-amber-400",
  Poor: "text-red-400",
};

const STATUS_BAR_COLORS: Record<string, string> = {
  Excellent: "bg-emerald-500",
  Good: "bg-amber-500",
  Average: "bg-amber-500",
  Poor: "bg-red-500",
};

function statusColor(status: string): string {
  return STATUS_COLORS[status] ?? "text-slate-400";
}

function statusBarColor(status: string): string {
  return STATUS_BAR_COLORS[status] ?? "bg-slate-500";
}

function fmtScore(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

// Radar geometry — one axis per koota
const RADAR_CENTER = 100;
const RADAR_RADIUS = 72;

function radarPoint(index: number, count: number, pct: number): [number, number] {
  const angle = (-90 + (360 / count) * index) * (Math.PI / 180);
  const r = (RADAR_RADIUS * Math.max(0, Math.min(100, pct))) / 100;
  return [RADAR_CENTER + r * Math.cos(angle), RADAR_CENTER + r * Math.sin(angle)];
}

function radarPolygon(values: number[]): string {
  return values.map((v, i) => radarPoint(i, values.length, v).join(",")).join(" ");
}

// Marriage timing status colors (from backend: probable, delayed, not_indicated)
const TIMING_STATUS_COLORS: Record<string, string> = {
  probable: "text-emerald-400",
  delayed: "text-amber-400",
  not_indicated: "text-slate-400",
};

const TIMING_BAR_COLORS: Record<string, string> = {
  probable: "bg-emerald-500",
  delayed: "bg-amber-500",
  not_indicated: "bg-slate-600",
};

const TIMING_LABELS: Record<string, string> = {
  probable: "✅ Probable Marriage Year",
  delayed: "🟠 Delayed / Obstructed",
  not_indicated: "⚪ Not Indicated",
};

const TIMING_FILL_PCT: Record<string, number> = {
  probable: 100,
  delayed: 60,
  not_indicated: 20,
};

type TabKey = "overview" | "ashtakoota" | "doshas" | "timeline" | "recommendations" | "bestbet";

const TABS: { key: TabKey; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "ashtakoota", label: "Ashtakoota" },
  { key: "doshas", label: "Doshas" },
  { key: "timeline", label: "Timeline" },
  { key: "bestbet", label: "Best Bet 58" },
  { key: "recommendations", label: "Recommendations" },
];

export default function CompatibilityReportPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const openCreateModal = useWorkflowStore((s) => s.openCreateModal);

  const checkAnotherCompatibility = () => {
    openCreateModal("compatibility");
    router.push("/dashboard");
  };

  const [report, setReport] = useState<CompatibilityResponse | null>(null);
  const [bestBetReport, setBestBetReport] = useState<BestBetCompatibilityResponse | null>(null);
  const [timingData, setTimingData] = useState<MarriageTimingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");

  // Sadhu Padhdhati — 2nd, selectable marriage-timing method (compared
  // against the Jupiter/Saturn transit scan above via timingMethod).
  const [timingMethod, setTimingMethod] = useState<"transit" | "sadhu">("transit");
  const [sadhuGenderA, setSadhuGenderA] = useState<"male" | "female">("male");
  const [sadhuGenderB, setSadhuGenderB] = useState<"male" | "female">("female");
  const [sadhuA, setSadhuA] = useState<SadhuPadhdhatiResponse | null>(null);
  const [sadhuB, setSadhuB] = useState<SadhuPadhdhatiResponse | null>(null);
  const [sadhuLoading, setSadhuLoading] = useState(false);
  const [sadhuError, setSadhuError] = useState<string | null>(null);

  const relationshipType = (searchParams.get("relationship_type") as RelationshipType) || "marriage";
  const nameA = searchParams.get("subject_name_a") || "Person A";
  const nameB = searchParams.get("subject_name_b") || "Person B";

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        setError(null);

        const birthDatetimeA = searchParams.get("birth_datetime_utc_a");
        const latitudeA = searchParams.get("latitude_a");
        const longitudeA = searchParams.get("longitude_a");
        const birthDatetimeB = searchParams.get("birth_datetime_utc_b");
        const latitudeB = searchParams.get("latitude_b");
        const longitudeB = searchParams.get("longitude_b");

        const ayanamsa = searchParams.get("ayanamsa") || "lahiri";
        const houseSystem = searchParams.get("house_system") || "W";

        if (!birthDatetimeA || !latitudeA || !longitudeA || !birthDatetimeB || !latitudeB || !longitudeB) {
          throw new Error("Missing required birth data parameters");
        }

        const response = await compatibilityApi.analyze({
          birth_datetime_utc_a: birthDatetimeA,
          latitude_a: parseFloat(latitudeA),
          longitude_a: parseFloat(longitudeA),
          subject_name_a: nameA,
          birth_datetime_utc_b: birthDatetimeB,
          latitude_b: parseFloat(latitudeB),
          longitude_b: parseFloat(longitudeB),
          subject_name_b: nameB,
          relationship_type: relationshipType,
          ayanamsa,
          house_system: houseSystem,
        });

        setReport(response);

        // Fetch marriage timing for Person A when relationship type is marriage
        // (Jupiter/Saturn transit scanner — real backend endpoint)
        if (relationshipType === "marriage") {
          try {
            const timing = await marriageTimingApi.scan({
              birth_datetime_utc: birthDatetimeA,
              latitude: parseFloat(latitudeA),
              longitude: parseFloat(longitudeA),
              subject_name: nameA,
              scan_start_age: 20,
              scan_end_age: 50,
              ayanamsa,
              house_system: houseSystem,
            });
            setTimingData(timing);
          } catch (timingErr) {
            // Marriage timing is optional — don't fail the whole report if it errors
            console.warn("Marriage timing scan failed:", timingErr);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to generate compatibility report");
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [searchParams, nameA, nameB, relationshipType]);

  // Fetch Best Bet report for marriage relationship type
  useEffect(() => {
    const fetchBestBet = async () => {
      if (relationshipType !== "marriage" || !report) return;
      try {
        const birthDatetimeA = searchParams.get("birth_datetime_utc_a");
        const latitudeA = searchParams.get("latitude_a");
        const longitudeA = searchParams.get("longitude_a");
        const birthDatetimeB = searchParams.get("birth_datetime_utc_b");
        const latitudeB = searchParams.get("latitude_b");
        const longitudeB = searchParams.get("longitude_b");
        const ayanamsa = searchParams.get("ayanamsa") || "lahiri";
        const houseSystem = searchParams.get("house_system") || "W";

        if (!birthDatetimeA || !latitudeA || !longitudeA || !birthDatetimeB || !latitudeB || !longitudeB) return;

        const res = await bestBetApi.analyze({
          birth_datetime_utc_a: birthDatetimeA,
          latitude_a: parseFloat(latitudeA),
          longitude_a: parseFloat(longitudeA),
          subject_name_a: nameA,
          birth_datetime_utc_b: birthDatetimeB,
          latitude_b: parseFloat(latitudeB),
          longitude_b: parseFloat(longitudeB),
          subject_name_b: nameB,
          ayanamsa,
          house_system: houseSystem,
        });
        setBestBetReport(res);
      } catch (err) {
        console.warn("Best Bet scan failed:", err);
      }
    };

    fetchBestBet();
  }, [relationshipType, report, searchParams, nameA, nameB]);

  // Filter to only show years where Jupiter activates Venus (probable or delayed)
  const activeTimingWindows: TransitScanYear[] = timingData
    ? timingData.scan_results.filter((r) => r.status !== "not_indicated")
    : [];

  const runSadhuPadhdhati = async () => {
    if (relationshipType !== "marriage" || sadhuLoading) return;
    const birthDatetimeA = searchParams.get("birth_datetime_utc_a");
    const latitudeA = searchParams.get("latitude_a");
    const longitudeA = searchParams.get("longitude_a");
    const birthDatetimeB = searchParams.get("birth_datetime_utc_b");
    const latitudeB = searchParams.get("latitude_b");
    const longitudeB = searchParams.get("longitude_b");
    const ayanamsa = searchParams.get("ayanamsa") || "lahiri";
    const houseSystem = searchParams.get("house_system") || "W";

    if (!birthDatetimeA || !latitudeA || !longitudeA || !birthDatetimeB || !latitudeB || !longitudeB) {
      setSadhuError("Missing required birth data parameters");
      return;
    }

    setSadhuLoading(true);
    setSadhuError(null);
    try {
      const [resultA, resultB] = await Promise.all([
        sadhuPadhdhatiApi.analyze({
          birth_datetime_utc: birthDatetimeA,
          latitude: parseFloat(latitudeA),
          longitude: parseFloat(longitudeA),
          subject_name: nameA,
          gender: sadhuGenderA,
          ayanamsa,
          house_system: houseSystem,
        }),
        sadhuPadhdhatiApi.analyze({
          birth_datetime_utc: birthDatetimeB,
          latitude: parseFloat(latitudeB),
          longitude: parseFloat(longitudeB),
          subject_name: nameB,
          gender: sadhuGenderB,
          ayanamsa,
          house_system: houseSystem,
        }),
      ]);
      setSadhuA(resultA);
      setSadhuB(resultB);
    } catch (err) {
      setSadhuError(err instanceof Error ? err.message : "Sadhu Padhdhati analysis failed");
    } finally {
      setSadhuLoading(false);
    }
  };

  const handleExport = async (format: "json" | "markdown" | "html") => {
    if (!report || exporting) return;
    try {
      setExporting(true);
      const birthDatetimeA = searchParams.get("birth_datetime_utc_a");
      const latitudeA = searchParams.get("latitude_a");
      const longitudeA = searchParams.get("longitude_a");
      const birthDatetimeB = searchParams.get("birth_datetime_utc_b");
      const latitudeB = searchParams.get("latitude_b");
      const longitudeB = searchParams.get("longitude_b");
      const ayanamsa = searchParams.get("ayanamsa") || "lahiri";
      const houseSystem = searchParams.get("house_system") || "W";

      if (!birthDatetimeA || !latitudeA || !longitudeA || !birthDatetimeB || !latitudeB || !longitudeB) {
        throw new Error("Missing required birth data for export");
      }

      const res = await exportApi.compatibility({
        birth_datetime_utc_a: birthDatetimeA,
        latitude_a: parseFloat(latitudeA),
        longitude_a: parseFloat(longitudeA),
        subject_name_a: nameA,
        birth_datetime_utc_b: birthDatetimeB,
        latitude_b: parseFloat(latitudeB),
        longitude_b: parseFloat(longitudeB),
        subject_name_b: nameB,
        relationship_type: relationshipType,
        ayanamsa,
        house_system: houseSystem,
        format,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Export failed with HTTP ${res.status}`);
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `compatibility-report-${nameA}-${nameB}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed:", err);
      alert(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExporting(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      alert("Report link copied to clipboard!");
    } catch {
      alert("Failed to copy link");
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ backgroundColor: "#0b0f19" }}>
        <div className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-2 border-purple-500/30 border-t-purple-500" />
          <p className="text-sm text-slate-400">Analyzing compatibility...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ backgroundColor: "#0b0f19" }}>
        <div className="max-w-md rounded-2xl border border-red-500/30 bg-red-950/20 p-6">
          <h2 className="mb-2 text-xl font-bold text-red-400">Analysis Error</h2>
          <p className="text-sm text-red-300">{error}</p>
          <button
            onClick={() => router.push("/dashboard")}
            className="mt-4 rounded-lg border border-white/10 px-4 py-2 text-xs font-bold text-slate-300 hover:bg-white/5"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!report) return null;

  const radarAxes = report.kootas.map((k) => ({
    label: k.name,
    value: report.radar_values[k.name] ?? (k.obtained_score / k.max_score) * 100,
  }));
  const radarN = radarAxes.length;

  return (
    <AppShell sectionColor="--section-analysis">
      <div className="min-h-screen" style={{ backgroundColor: "#0b0f19" }}>
        {/* Top Navigation Bar */}
        <div className="sticky top-0 z-40 border-b border-white/10 bg-black/40 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push("/dashboard")}
              className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
              Back to Dashboard
            </button>
            <button
              onClick={checkAnotherCompatibility}
              className="flex items-center gap-2 rounded-lg border border-purple-500/30 bg-purple-500/10 px-3 py-1.5 text-xs font-bold text-purple-300 transition hover:bg-purple-500/20"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8Z" />
              </svg>
              Check Another Compatibility
            </button>
          </div>
            <div className="flex items-center gap-2">
            <button
              onClick={() => handleExport("html")}
              disabled={exporting}
              className="rounded-lg border border-white/10 px-3 py-1.5 text-xs font-bold text-slate-300 transition hover:bg-white/5 disabled:opacity-50"
            >
              📄 {exporting ? "Exporting..." : "Export"}
            </button>
            <button
              onClick={handlePrint}
              className="rounded-lg border border-white/10 px-3 py-1.5 text-xs font-bold text-slate-300 transition hover:bg-white/5"
            >
              🖨 Print
            </button>
            <button
              onClick={handleShare}
              className="rounded-lg border border-white/10 px-3 py-1.5 text-xs font-bold text-slate-300 transition hover:bg-white/5"
            >
              🔗 Share
            </button>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-6 py-8">
        {/* Hero Section */}
        <div className="mb-8 overflow-hidden rounded-2xl border border-purple-500/20 bg-gradient-to-br from-purple-950/30 to-slate-900/50 p-8">
          <div className="flex flex-col items-center gap-6 md:flex-row md:items-center md:justify-between">
            <div className="text-center md:text-left">
              <p className="mb-2 text-xs font-bold uppercase tracking-wider text-purple-400">
                {RELATIONSHIP_LABELS[relationshipType]}
              </p>
              <h1 className="text-3xl font-black text-white">
                {report.subject_name_a} <span className="text-pink-400">❤</span> {report.subject_name_b}
              </h1>
              <p className="mt-2 text-sm text-slate-400">
                {relationshipType === "marriage" ? "Marriage Compatibility Analysis" : relationshipType === "business" ? "Business Partnership Analysis" : relationshipType === "friendship" ? "Friendship Compatibility Analysis" : "Parent–Child Synastry Analysis"}
              </p>
            </div>

            {/* Large Score Gauge */}
            <div className="relative flex h-32 w-32 items-center justify-center rounded-full border-4 border-purple-500/60 bg-purple-500/10 shadow-lg shadow-purple-500/20">
              <div className="text-center">
                <div className="text-3xl font-black text-white">{Math.round(report.compatibility_percentage)}%</div>
                <div className="text-[10px] font-bold uppercase text-purple-300">{report.verdict}</div>
              </div>
            </div>
          </div>

          {/* Quick Summary Tags */}
          <div className="mt-6 flex flex-wrap gap-2 border-t border-white/10 pt-6">
            {report.kootas.slice(0, 6).map((k) => (
              <span
                key={k.name}
                className={`rounded-full border px-3 py-1 text-[11px] font-semibold ${k.status === "Excellent" ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400" : k.status === "Good" ? "border-amber-500/30 bg-amber-500/10 text-amber-400" : k.status === "Poor" ? "border-red-500/30 bg-red-500/10 text-red-400" : "border-white/10 bg-white/5 text-slate-400"}`}
              >
                {k.status === "Excellent" ? "🟢" : k.status === "Good" ? "🟡" : k.status === "Poor" ? "🔴" : "⚪"} {k.name}
              </span>
            ))}
          </div>
        </div>

        {/* Main Layout: Content + Sticky Sidebar */}
        <div className="flex gap-6">
          {/* Main Content */}
          <div className="flex-1 space-y-6">
            {/* Tabs */}
            <div className="flex border-b border-white/10">
              {TABS.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setActiveTab(t.key)}
                  className={`px-4 py-3 text-xs font-semibold transition ${activeTab === t.key ? "border-b-2 border-purple-500 text-purple-400" : "border-b-2 border-transparent text-slate-400 hover:text-slate-200"}`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Overview Tab */}
            {activeTab === "overview" && (
              <div className="space-y-6">
                {/* Person Comparison Card */}
                <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                  <h2 className="mb-4 text-sm font-bold text-white">Person Comparison</h2>
                  <div className="grid grid-cols-3 items-center gap-4">
                    {/* Person A */}
                    <div className="rounded-xl border border-purple-500/30 bg-purple-950/10 p-4 text-center">
                      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-purple-500/20 text-lg font-bold text-purple-400">
                        {report.subject_name_a.charAt(0).toUpperCase()}
                      </div>
                      <p className="text-sm font-bold text-white">{report.subject_name_a}</p>
                      <p className="mt-1 text-[10px] text-slate-400">Person A</p>
                    </div>

                    {/* VS */}
                    <div className="text-center">
                      <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-black/40 text-xs font-black text-pink-400">
                        VS
                      </div>
                    </div>

                    {/* Person B */}
                    <div className="rounded-xl border border-blue-500/30 bg-blue-950/10 p-4 text-center">
                      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/20 text-lg font-bold text-blue-400">
                        {report.subject_name_b.charAt(0).toUpperCase()}
                      </div>
                      <p className="text-sm font-bold text-white">{report.subject_name_b}</p>
                      <p className="mt-1 text-[10px] text-slate-400">Person B</p>
                    </div>
                  </div>
                </div>

                {/* Score Dashboard + Radar Chart */}
                <div className="grid grid-cols-2 gap-6">
                  {/* Score Cards */}
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                    <h2 className="mb-4 text-sm font-bold text-white">Score Dashboard</h2>
                    <div className="space-y-3">
                      {/* Overall Score */}
                      <div className="rounded-xl border border-purple-500/20 bg-purple-950/20 p-4">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-purple-300">Overall Match</span>
                          <span className="text-lg font-black text-white">{Math.round(report.compatibility_percentage)}%</span>
                        </div>
                        <div className="mt-2 h-2 overflow-hidden rounded-full bg-black/40">
                          <div className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500" style={{ width: `${report.compatibility_percentage}%` }} />
                        </div>
                      </div>

                      {/* Individual Koota Scores */}
                      {report.kootas.map((k) => {
                        const pct = (k.obtained_score / k.max_score) * 100;
                        return (
                          <div key={k.name} className="rounded-lg border border-white/10 bg-black/30 p-3">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-medium text-slate-300">{k.name}</span>
                              <span className="text-xs font-bold text-white">
                                {fmtScore(k.obtained_score)} / {fmtScore(k.max_score)}
                              </span>
                            </div>
                            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-black/40">
                              <div className={`h-full rounded-full ${statusBarColor(k.status)}`} style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Radar Chart */}
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                    <h2 className="mb-4 text-sm font-bold text-white">Compatibility Radar</h2>
                    <div className="flex items-center justify-center">
                      <svg width="240" height="240" viewBox="0 0 200 200" className="overflow-visible">
                        {[100, 66, 33].map((ring) => (
                          <polygon
                            key={ring}
                            points={radarPolygon(radarAxes.map(() => ring))}
                            fill="none"
                            stroke="rgba(255,255,255,0.1)"
                            strokeWidth="1"
                          />
                        ))}
                        {radarAxes.map((a, i) => {
                          const [x, y] = radarPoint(i, radarN, 100);
                          return <line key={a.label} x1={RADAR_CENTER} y1={RADAR_CENTER} x2={x} y2={y} stroke="rgba(255,255,255,0.1)" />;
                        })}
                        <polygon
                          points={radarPolygon(radarAxes.map((a) => a.value))}
                          fill="rgba(168,85,247,0.3)"
                          stroke="#a855f7"
                          strokeWidth="2"
                        />
                        {radarAxes.map((a, i) => {
                          const [x, y] = radarPoint(i, radarN, 122);
                          const anchor = x > RADAR_CENTER + 2 ? "start" : x < RADAR_CENTER - 2 ? "end" : "middle";
                          return (
                            <text key={a.label} x={x} y={y} textAnchor={anchor} dominantBaseline="middle" fill="#cbd5e1" fontSize="8">
                              {a.label}
                            </text>
                          );
                        })}
                      </svg>
                    </div>
                  </div>
                </div>

                {/* Strengths & Challenges */}
                <div className="grid grid-cols-2 gap-6">
                  {report.strengths.length > 0 && (
                    <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/10 p-6">
                      <h2 className="mb-3 text-sm font-bold text-emerald-400">✔ Strengths</h2>
                      <ul className="space-y-2">
                        {report.strengths.map((s, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                            <span className="mt-0.5 text-emerald-400">✓</span>
                            <span>{s}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {report.challenges.length > 0 && (
                    <div className="rounded-2xl border border-amber-500/20 bg-amber-950/10 p-6">
                      <h2 className="mb-3 text-sm font-bold text-amber-400">⚠ Challenges</h2>
                      <ul className="space-y-2">
                        {report.challenges.map((c, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                            <span className="mt-0.5 text-amber-400">⚠</span>
                            <span>{c}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Ashtakoota Tab */}
            {activeTab === "ashtakoota" && (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                <h2 className="mb-4 text-sm font-bold text-white">Ashtakoota Matching (36 Points)</h2>
                <div className="space-y-3">
                  {report.kootas.map((k, i) => {
                    const pct = (k.obtained_score / k.max_score) * 100;
                    return (
                      <div key={k.name} className="rounded-xl border border-white/10 bg-black/30 p-4">
                        <div className="mb-2 flex items-center justify-between">
                          <div>
                            <span className="text-xs font-bold text-slate-200">
                              {i + 1}. {k.name}
                            </span>
                            <p className="mt-0.5 text-[10px] text-slate-500">{k.description}</p>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-bold text-white">
                              {fmtScore(k.obtained_score)} / {fmtScore(k.max_score)}
                            </div>
                            <div className={`text-[10px] font-semibold ${statusColor(k.status)}`}>
                              {k.status === "Poor" ? "✕" : "✓"} {k.status}
                            </div>
                          </div>
                        </div>
                        {/* Progress Bar */}
                        <div className="h-2 overflow-hidden rounded-full bg-black/40">
                          <div className={`h-full rounded-full ${statusBarColor(k.status)}`} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}

                  {/* Total Score */}
                  <div className="flex items-center justify-between rounded-xl border border-purple-500/30 bg-purple-950/20 p-4">
                    <span className="text-sm font-bold text-white">Total Score</span>
                    <span className="text-lg font-black text-purple-400">
                      {fmtScore(report.total_score)} / {fmtScore(report.max_total_score)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Doshas Tab */}
            {activeTab === "doshas" && (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                <h2 className="mb-4 text-sm font-bold text-white">Dosha Analysis</h2>
                {report.doshas.length === 0 ? (
                  <p className="text-xs text-slate-400">No doshas detected.</p>
                ) : (
                  <div className="space-y-3">
                    {report.doshas.map((d) => (
                      <div
                        key={d.name}
                        className={`rounded-xl border p-4 ${d.has_dosha ? (d.severity === "Severe" ? "border-red-500/30 bg-red-950/20" : d.severity === "Partial" ? "border-amber-500/30 bg-amber-950/20" : "border-white/10 bg-black/30") : "border-emerald-500/30 bg-emerald-950/10"}`}
                      >
                        <div className="mb-1 flex items-center justify-between">
                          <h3 className="text-xs font-bold text-white">{d.name}</h3>
                          <span
                            className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${d.has_dosha ? (d.severity === "Severe" ? "bg-red-500/20 text-red-400" : d.severity === "Partial" ? "bg-amber-500/20 text-amber-400" : "bg-slate-500/20 text-slate-400") : "bg-emerald-500/20 text-emerald-400"}`}
                          >
                            {d.has_dosha ? `${d.severity} Dosha ⚠` : "No Dosha ✓"}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400">{d.description}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Timeline Tab — Jupiter/Saturn Marriage Timing */}
            {activeTab === "timeline" && (
              <div className="space-y-6">
                {/* Timing method selector — compare Jupiter/Saturn transit vs Sadhu Padhdhati */}
                <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-black/30 p-1.5">
                  <button
                    onClick={() => setTimingMethod("transit")}
                    className={`flex-1 rounded-lg px-3 py-2 text-xs font-bold transition ${
                      timingMethod === "transit" ? "bg-cyan-500/20 text-cyan-300" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    🪐 Jupiter / Saturn Transit
                  </button>
                  <button
                    onClick={() => setTimingMethod("sadhu")}
                    className={`flex-1 rounded-lg px-3 py-2 text-xs font-bold transition ${
                      timingMethod === "sadhu" ? "bg-cyan-500/20 text-cyan-300" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    🕉 Sadhu Padhdhati
                  </button>
                </div>

                {timingMethod === "transit" && (
                <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                  <div className="mb-4 flex items-center gap-2">
                    <span className="text-lg">🪐</span>
                    <div>
                      <h2 className="text-sm font-bold text-white">Jupiter / Saturn Transit Scanner</h2>
                      <p className="text-[11px] text-slate-400">
                        Marriage timing windows for {nameA} — Jupiter activation of natal Venus with Saturn obstruction filter
                      </p>
                    </div>
                  </div>

                  {timingData ? (
                    <>
                      {/* Natal Venus Info */}
                      <div className="mb-4 grid grid-cols-3 gap-3">
                        <div className="rounded-lg border border-purple-500/20 bg-purple-950/20 p-3 text-center">
                          <p className="text-[10px] text-slate-400">Natal Venus Sign</p>
                          <p className="text-sm font-bold text-purple-400">{timingData.natal_venus_rashi}</p>
                        </div>
                        <div className="rounded-lg border border-blue-500/20 bg-blue-950/20 p-3 text-center">
                          <p className="text-[10px] text-slate-400">7th House Cusp</p>
                          <p className="text-sm font-bold text-blue-400">{timingData.natal_seventh_cusp_rashi}</p>
                        </div>
                        <div className="rounded-lg border border-emerald-500/20 bg-emerald-950/20 p-3 text-center">
                          <p className="text-[10px] text-slate-400">Scan Range</p>
                          <p className="text-sm font-bold text-emerald-400">
                            Age {timingData.scan_start_age}–{timingData.scan_end_age}
                          </p>
                        </div>
                      </div>

                      {/* Summary Stats */}
                      <div className="mb-4 flex gap-3">
                        <div className="flex-1 rounded-lg border border-emerald-500/30 bg-emerald-950/20 p-3 text-center">
                          <p className="text-2xl font-black text-emerald-400">{timingData.probable_windows}</p>
                          <p className="text-[10px] text-slate-400">Probable Windows</p>
                        </div>
                        <div className="flex-1 rounded-lg border border-amber-500/30 bg-amber-950/20 p-3 text-center">
                          <p className="text-2xl font-black text-amber-400">{timingData.delayed_windows}</p>
                          <p className="text-[10px] text-slate-400">Delayed Windows</p>
                        </div>
                        <div className="flex-1 rounded-lg border border-white/10 bg-black/30 p-3 text-center">
                          <p className="text-2xl font-black text-slate-400">{timingData.total_years_scanned}</p>
                          <p className="text-[10px] text-slate-400">Years Scanned</p>
                        </div>
                      </div>

                      {/* Active Timing Windows */}
                      {activeTimingWindows.length > 0 ? (
                        <div className="space-y-3">
                          <p className="text-xs font-bold text-white">Marriage Timing Windows (Jupiter activates Venus)</p>
                          {activeTimingWindows.map((w) => (
                            <div key={w.year} className="rounded-xl border border-white/10 bg-black/30 p-4">
                              <div className="mb-2 flex items-center justify-between">
                                <div>
                                  <span className="text-sm font-bold text-white">{w.year}</span>
                                  <span className="ml-2 text-[10px] text-slate-400">Age {w.age_at_year.toFixed(0)}</span>
                                </div>
                                <span className={`text-xs font-bold ${TIMING_STATUS_COLORS[w.status]}`}>
                                  {TIMING_LABELS[w.status]}
                                </span>
                              </div>

                              {/* Jupiter/Saturn positions */}
                              <div className="mb-2 grid grid-cols-2 gap-2 text-[10px]">
                                <div className="rounded bg-purple-950/20 px-2 py-1">
                                  <span className="text-purple-400">Jupiter:</span>{" "}
                                  <span className="text-slate-300">{w.jupiter_rashi}</span>
                                </div>
                                <div className="rounded bg-blue-950/20 px-2 py-1">
                                  <span className="text-blue-400">Saturn:</span>{" "}
                                  <span className="text-slate-300">{w.saturn_rashi}</span>
                                </div>
                              </div>

                              {/* Aspect details */}
                              {w.aspect_details.length > 0 && (
                                <p className="mb-1 text-[11px] text-emerald-300">
                                  ✓ {w.aspect_details.join("; ")}
                                </p>
                              )}
                              {w.saturn_obstruction_details.length > 0 && (
                                <p className="mb-1 text-[11px] text-amber-300">
                                  ⚠ {w.saturn_obstruction_details.join("; ")}
                                </p>
                              )}

                              {/* Progress Bar */}
                              <div className="mt-2 h-2 overflow-hidden rounded-full bg-black/40">
                                <div
                                  className={`h-full rounded-full ${TIMING_BAR_COLORS[w.status]}`}
                                  style={{ width: `${TIMING_FILL_PCT[w.status] ?? 20}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="rounded-lg border border-white/10 bg-black/30 p-4 text-center">
                          <p className="text-xs text-slate-400">
                            No marriage timing windows found in the scanned age range.
                            This doesn't mean marriage won't happen — the transit scanner only checks
                            Jupiter/Venus activations.
                          </p>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 px-3 py-2 text-[11px] text-amber-300">
                      {relationshipType === "marriage"
                        ? "⚠ Marriage timing scan could not be loaded. The backend endpoint may be unavailable."
                        : "ℹ Marriage timing scanner is only available for Marriage relationship type. Switch to Marriage to see Jupiter/Saturn transit windows."}
                    </div>
                  )}
                </div>
                )}

                {timingMethod === "sadhu" && (
                <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                  <div className="mb-4 flex items-center gap-2">
                    <span className="text-lg">🕉</span>
                    <div>
                      <h2 className="text-sm font-bold text-white">Sadhu Padhdhati (Sudarshana Chakra Prism)</h2>
                      <p className="text-[11px] text-slate-400">
                        Alternate marriage-timing method for both {nameA} and {nameB} — compare its predicted year against the Jupiter/Saturn scan above.
                      </p>
                    </div>
                  </div>

                  {relationshipType !== "marriage" ? (
                    <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 px-3 py-2 text-[11px] text-amber-300">
                      ℹ Sadhu Padhdhati is only available for Marriage relationship type.
                    </div>
                  ) : (
                    <>
                      {/* Gender inputs — required by the method's age-base table, not tracked elsewhere in this flow */}
                      <div className="mb-4 grid grid-cols-2 gap-3">
                        <div className="rounded-lg border border-white/10 bg-black/30 p-3">
                          <label className="mb-1 block text-[10px] text-slate-400">{nameA}&apos;s Gender</label>
                          <select
                            value={sadhuGenderA}
                            onChange={(e) => setSadhuGenderA(e.target.value as "male" | "female")}
                            className="w-full rounded bg-black/40 px-2 py-1.5 text-xs text-white outline-none"
                          >
                            <option value="male">Male</option>
                            <option value="female">Female</option>
                          </select>
                        </div>
                        <div className="rounded-lg border border-white/10 bg-black/30 p-3">
                          <label className="mb-1 block text-[10px] text-slate-400">{nameB}&apos;s Gender</label>
                          <select
                            value={sadhuGenderB}
                            onChange={(e) => setSadhuGenderB(e.target.value as "male" | "female")}
                            className="w-full rounded bg-black/40 px-2 py-1.5 text-xs text-white outline-none"
                          >
                            <option value="male">Male</option>
                            <option value="female">Female</option>
                          </select>
                        </div>
                      </div>

                      <button
                        onClick={runSadhuPadhdhati}
                        disabled={sadhuLoading}
                        className="mb-4 w-full rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-2 text-xs font-bold text-cyan-300 transition hover:bg-cyan-500/20 disabled:opacity-50"
                      >
                        {sadhuLoading ? "Computing…" : "Run Sadhu Padhdhati Analysis"}
                      </button>

                      {sadhuError && (
                        <div className="mb-4 rounded-lg border border-red-500/30 bg-red-950/20 px-3 py-2 text-[11px] text-red-300">
                          {sadhuError}
                        </div>
                      )}

                      {sadhuA && sadhuB && (
                        <div className="grid grid-cols-2 gap-4">
                          {[
                            { label: nameA, result: sadhuA },
                            { label: nameB, result: sadhuB },
                          ].map(({ label, result }) => (
                            <div key={label} className="rounded-xl border border-white/10 bg-black/30 p-4">
                              <p className="mb-2 text-xs font-bold text-white">{label}</p>
                              <div className="mb-3 text-center">
                                <p className="text-3xl font-black text-cyan-400">{result.predicted_year}</p>
                                <p className="text-[10px] text-slate-400">
                                  Predicted window {result.window_start}–{result.window_end}
                                </p>
                              </div>
                              <div className="space-y-1 text-[10px] text-slate-400">
                                <div className="flex justify-between">
                                  <span>Net Delay (years from birth)</span>
                                  <span className="text-slate-300">{result.net_delay}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>D1 chart delay</span>
                                  <span className="text-slate-300">
                                    {result.d1.delay.toFixed(1)} (EF {result.d1.escalation_factor}, RF {result.d1.reducing_factor})
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span>D9 chart delay</span>
                                  <span className="text-slate-300">
                                    {result.d9.delay.toFixed(1)} (EF {result.d9.escalation_factor}, RF {result.d9.reducing_factor})
                                  </span>
                                </div>
                                {result.alphabet_class && (
                                  <div className="flex justify-between">
                                    <span>Alphabet Class / Destiny Factor</span>
                                    <span className="text-slate-300">
                                      {result.alphabet_class} / {result.destiny_factor}
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      <p className="mt-4 text-[10px] text-slate-500">
                        Escalation Factor (EF) is computed from classical aspect/conjunction/parivartana
                        rules; Reducing Factor (RF) is an automated approximation of a column the source
                        method leaves to manual astrologer judgment. Treat the predicted year as an
                        estimate to compare against the Jupiter/Saturn scan, not a certainty.
                      </p>
                    </>
                  )}
                </div>
                )}
              </div>
            )}

            {/* Best Bet 58-Point Tab */}
            {activeTab === "bestbet" && (
              <div className="space-y-6">
                <div className="rounded-2xl border border-purple-500/20 bg-purple-950/10 p-6">
                  <h2 className="mb-4 text-sm font-bold text-purple-300">Best Bet 58-Point Marriage Matching</h2>
                  <p className="mb-4 text-xs text-slate-400">
                    Comprehensive compatibility analysis using the Best Bet method (Jai Shaker):
                    Practical (36), Karmic (12), Future (10) — total 58 points.
                  </p>

                  {relationshipType !== "marriage" ? (
                    <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 px-3 py-2 text-[11px] text-amber-300">
                      ℹ Best Bet scoring is specifically designed for marriage matching. Switch to Marriage relationship type to see full analysis.
                    </div>
                  ) : bestBetReport ? (
                    <>
                      {/* Overall Score */}
                      <div className="mb-6 flex items-center justify-between rounded-xl border border-purple-500/30 bg-purple-950/20 p-5">
                        <div>
                          <p className="text-xs text-slate-400">Overall Score</p>
                          <p className="text-3xl font-black text-white">
                            {bestBetReport.total_score} / {bestBetReport.max_score}
                          </p>
                          <p className="text-xs text-slate-400">{bestBetReport.verdict}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-4xl font-black text-purple-400">{bestBetReport.percentage}%</p>
                          <p className="text-xs text-purple-300">{bestBetReport.status}</p>
                        </div>
                      </div>

                      {/* Group Scores */}
                      <div className="mb-6 grid grid-cols-3 gap-3">
                        <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-4 text-center">
                          <p className="text-[10px] text-slate-400">Practical</p>
                          <p className="text-lg font-black text-emerald-400">
                            {bestBetReport.practical_score}/{bestBetReport.practical_max}
                          </p>
                          <p className="text-[10px] text-slate-400">Spiritual, Psych, Physical</p>
                        </div>
                        <div className="rounded-xl border border-amber-500/20 bg-amber-950/20 p-4 text-center">
                          <p className="text-[10px] text-slate-400">Karmic</p>
                          <p className="text-lg font-black text-amber-400">
                            {bestBetReport.karmic_score}/{bestBetReport.karmic_max}
                          </p>
                          <p className="text-[10px] text-slate-400">Mars Dosha, Karmic Pattern</p>
                        </div>
                        <div className="rounded-xl border border-blue-500/20 bg-blue-950/20 p-4 text-center">
                          <p className="text-[10px] text-slate-400">Future</p>
                          <p className="text-lg font-black text-blue-400">
                            {bestBetReport.future_score}/{bestBetReport.future_max}
                          </p>
                          <p className="text-[10px] text-slate-400">Dasha, Mutual Planets</p>
                        </div>
                      </div>

                      {/* Sub-factors */}
                      <div className="mb-6">
                        <h3 className="mb-3 text-xs font-bold text-white">Detailed Breakdown</h3>
                        <div className="space-y-2">
                          {bestBetReport.sub_factors.map((f) => {
                            const pct = (f.score / f.max) * 100;
                            const color = pct >= 70 ? "bg-emerald-500" : pct >= 40 ? "bg-amber-500" : "bg-red-500";
                            return (
                              <div key={f.name} className="rounded-lg border border-white/10 bg-black/30 p-3">
                                <div className="mb-1 flex items-center justify-between">
                                  <span className="text-xs font-medium text-slate-300">{f.name}</span>
                                  <span className="text-xs font-bold text-white">
                                    {Number.isInteger(f.score) ? f.score : f.score.toFixed(1)} / {f.max}
                                  </span>
                                </div>
                                <p className="mb-1.5 text-[10px] text-slate-500">{f.description}</p>
                                <div className="h-1.5 overflow-hidden rounded-full bg-black/40">
                                  <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Strengths & Challenges */}
                      <div className="grid grid-cols-2 gap-4">
                        {bestBetReport.strengths.length > 0 && (
                          <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/10 p-4">
                            <h3 className="mb-2 text-xs font-bold text-emerald-400">✔ Strengths</h3>
                            <ul className="space-y-1">
                              {bestBetReport.strengths.map((s, i) => (
                                <li key={i} className="text-[11px] text-slate-300">• {s}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {bestBetReport.challenges.length > 0 && (
                          <div className="rounded-xl border border-amber-500/20 bg-amber-950/10 p-4">
                            <h3 className="mb-2 text-xs font-bold text-amber-400">⚠ Challenges</h3>
                            <ul className="space-y-1">
                              {bestBetReport.challenges.map((c, i) => (
                                <li key={i} className="text-[11px] text-slate-300">• {c}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="rounded-lg border border-white/10 bg-black/30 p-4 text-center">
                      <p className="text-xs text-slate-400">Loading Best Bet analysis...</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Recommendations Tab */}
            {activeTab === "recommendations" && (
              <div className="rounded-2xl border border-purple-500/20 bg-purple-950/10 p-6">
                <h2 className="mb-4 text-sm font-bold text-purple-300">✨ AI Recommendations</h2>
                <ul className="space-y-3">
                  {report.recommendations.map((r, i) => (
                    <li key={i} className="flex items-start gap-3 rounded-lg border border-white/10 bg-black/20 p-3 text-xs text-slate-300">
                      <span className="mt-0.5 text-purple-400">→</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Sticky Right Sidebar */}
          <div className="sticky top-20 hidden h-fit w-72 flex-col gap-4 lg:flex">
            {/* Overall Score Card */}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5 text-center">
              <p className="mb-3 text-xs font-bold text-slate-400">Overall Compatibility</p>
              <div className="relative mx-auto flex h-24 w-24 items-center justify-center rounded-full border-4 border-pink-500/80 bg-pink-500/10">
                <span className="text-2xl font-black text-white">{Math.round(report.compatibility_percentage)}%</span>
              </div>
              <p className="mt-3 text-sm font-bold text-pink-400">{report.verdict}</p>
              <p className="mt-1 text-[10px] text-slate-400">
                {report.subject_name_a} & {report.subject_name_b}
              </p>
              <div className="mt-4 grid grid-cols-2 gap-2 border-t border-white/10 pt-4 text-[11px]">
                <div className="rounded-lg bg-black/40 p-2">
                  <p className="text-slate-400">Ashtakoota</p>
                  <p className="text-sm font-bold text-white">
                    {fmtScore(report.total_score)} / {fmtScore(report.max_total_score)}
                  </p>
                </div>
                <div className="rounded-lg bg-black/40 p-2">
                  <p className="text-slate-400">Match Index</p>
                  <p className="text-sm font-bold text-white">{Math.round(report.compatibility_percentage)} / 100</p>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <p className="mb-3 text-xs font-bold text-white">Quick Stats</p>
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Relationship Type</span>
                  <span className="font-semibold text-slate-200">{RELATIONSHIP_LABELS[relationshipType]}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Kootas Analyzed</span>
                  <span className="font-semibold text-slate-200">{report.kootas.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Doshas Checked</span>
                  <span className="font-semibold text-slate-200">{report.doshas.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Strengths</span>
                  <span className="font-semibold text-emerald-400">{report.strengths.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Challenges</span>
                  <span className="font-semibold text-amber-400">{report.challenges.length}</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <p className="mb-3 text-xs font-bold text-white">Actions</p>
              <div className="space-y-2">
                <button
                  onClick={() => handleExport("html")}
                  disabled={exporting}
                  className="w-full rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-slate-300 transition hover:bg-white/5 disabled:opacity-50"
                >
                  📄 {exporting ? "Exporting..." : "Export Report"}
                </button>
                <button
                  onClick={handlePrint}
                  className="w-full rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-slate-300 transition hover:bg-white/5"
                >
                  🖨 Print Report
                </button>
                <button
                  onClick={handleShare}
                  className="w-full rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-slate-300 transition hover:bg-white/5"
                >
                  🔗 Share Link
                </button>
                <button
                  onClick={() => router.push("/dashboard")}
                  className="w-full rounded-lg border border-purple-500/30 bg-purple-500/10 px-3 py-2 text-xs font-bold text-purple-300 transition hover:bg-purple-500/20"
                >
                  ← Back to Dashboard
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </AppShell>
  );
}
