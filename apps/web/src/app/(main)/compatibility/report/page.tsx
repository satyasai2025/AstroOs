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
import { useWorkflowStore } from "@/lib/store";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

export const dynamic = "force-dynamic";

type RelationshipType = "marriage" | "business" | "friendship" | "parent_child";

const RELATIONSHIP_CONFIG: Record<
  RelationshipType,
  { label: string; subLabel: string; accent: string; accentSoft: string; accentBorder: string; icon: string }
> = {
  marriage: {
    label: "Marriage Compatibility",
    subLabel: "Vedic Ashtakoota · Dosha · Best Bet 58",
    accent: "var(--obsidian-accent-tertiary, #a855f7)",
    accentSoft: "rgba(168,85,247,0.08)",
    accentBorder: "rgba(168,85,247,0.25)",
    icon: "M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8Z",
  },
  business: {
    label: "Business Partnership",
    subLabel: "Vedic Ashtakoota · Dosha · Synastry",
    accent: "var(--obsidian-accent-secondary, #06b6d4)",
    accentSoft: "rgba(6,182,212,0.08)",
    accentBorder: "rgba(6,182,212,0.25)",
    icon: "M20 7H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2zM2 17h20M2 7l10-4 10 4",
  },
  friendship: {
    label: "Friendship Compatibility",
    subLabel: "Vedic Ashtakoota · Dosha · Synastry",
    accent: "#10b981",
    accentSoft: "rgba(16,185,129,0.08)",
    accentBorder: "rgba(16,185,129,0.25)",
    icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
  },
  parent_child: {
    label: "Parent–Child Synastry",
    subLabel: "Vedic Ashtakoota · Dosha · Synastry",
    accent: "#f59e0b",
    accentSoft: "rgba(245,158,11,0.08)",
    accentBorder: "rgba(245,158,11,0.25)",
    icon: "M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11",
  },
};

const STATUS_COLORS: Record<string, string> = {
  Excellent: "#10b981",
  Good:      "#f59e0b",
  Average:   "#f59e0b",
  Poor:      "#ef4444",
};

function statusColor(status: string) {
  return STATUS_COLORS[status] ?? "var(--obsidian-text-muted)";
}

function fmtScore(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

// Radar geometry
const RC = 100;
const RR = 72;
function radarPoint(i: number, n: number, pct: number): [number, number] {
  const a = (-90 + (360 / n) * i) * (Math.PI / 180);
  const r = RR * Math.max(0, Math.min(100, pct)) / 100;
  return [RC + r * Math.cos(a), RC + r * Math.sin(a)];
}
function radarPolygon(vals: number[]): string {
  return vals.map((v, i) => radarPoint(i, vals.length, v).join(",")).join(" ");
}

const TIMING_BAR: Record<string, string> = {
  probable:     "bg-emerald-500",
  delayed:      "bg-amber-500",
  not_indicated:"bg-slate-600",
};
const TIMING_FILL: Record<string, number> = {
  probable: 100,
  delayed: 60,
  not_indicated: 20,
};
const TIMING_LABEL: Record<string, string> = {
  probable:      "Probable",
  delayed:       "Delayed / Obstructed",
  not_indicated: "Not Indicated",
};
const TIMING_COLOR: Record<string, string> = {
  probable:      "#10b981",
  delayed:       "#f59e0b",
  not_indicated: "var(--obsidian-text-muted)",
};

// Tabs differ by relationship type
function getTabsForType(rel: RelationshipType) {
  const base = [
    { key: "overview",         label: "Overview" },
    { key: "ashtakoota",       label: "Ashtakoota" },
    { key: "doshas",           label: "Doshas" },
    { key: "recommendations",  label: "Recommendations" },
  ];
  if (rel === "marriage") {
    return [
      ...base.slice(0, 3),
      { key: "timeline", label: "Timing" },
      { key: "bestbet",  label: "Best Bet 58" },
      base[3],
    ];
  }
  return base;
}

type TabKey = "overview" | "ashtakoota" | "doshas" | "timeline" | "bestbet" | "recommendations";

/* ─────────────────────────────────────────── */
/*  Shared card wrapper                        */
/* ─────────────────────────────────────────── */
function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-xl border p-5 ${className}`}
      style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
    >
      {children}
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="mb-4 text-sm font-bold" style={{ color: "var(--text-primary)" }}>
      {children}
    </h2>
  );
}

/* ─────────────────────────────────────────── */
/*  Score bar                                  */
/* ─────────────────────────────────────────── */
function ScoreBar({ pct, color }: { pct: number; color: string }) {
  return (
    <div className="mt-1.5 h-1.5 overflow-hidden rounded-full" style={{ backgroundColor: "var(--bg-primary)" }}>
      <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  );
}

/* ─────────────────────────────────────────── */
/*  Main page component                        */
/* ─────────────────────────────────────────── */
function CompatibilityReportPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const openCreateModal = useWorkflowStore((s) => s.openCreateModal);

  const [report, setReport] = useState<CompatibilityResponse | null>(null);
  const [bestBetReport, setBestBetReport] = useState<BestBetCompatibilityResponse | null>(null);
  const [timingData, setTimingData] = useState<MarriageTimingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [shareStatus, setShareStatus] = useState<"idle" | "copied" | "failed">("idle");

  // Sadhu Padhdhati (marriage only)
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
  const relConfig = RELATIONSHIP_CONFIG[relationshipType];
  const TABS = getTabsForType(relationshipType);

  /* ── Fetch main report ── */
  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        setError(null);
        const bdA = searchParams.get("birth_datetime_utc_a");
        const latA = searchParams.get("latitude_a");
        const lonA = searchParams.get("longitude_a");
        const bdB = searchParams.get("birth_datetime_utc_b");
        const latB = searchParams.get("latitude_b");
        const lonB = searchParams.get("longitude_b");
        const ayanamsa = searchParams.get("ayanamsa") || "lahiri";
        const houseSystem = searchParams.get("house_system") || "W";
        if (!bdA || !latA || !lonA || !bdB || !latB || !lonB)
          throw new Error("Missing required birth data parameters");

        const res = await compatibilityApi.analyze({
          birth_datetime_utc_a: bdA, latitude_a: parseFloat(latA), longitude_a: parseFloat(lonA), subject_name_a: nameA,
          birth_datetime_utc_b: bdB, latitude_b: parseFloat(latB), longitude_b: parseFloat(lonB), subject_name_b: nameB,
          relationship_type: relationshipType, ayanamsa, house_system: houseSystem,
        });
        setReport(res);

        if (relationshipType === "marriage") {
          try {
            const t = await marriageTimingApi.scan({
              birth_datetime_utc: bdA, latitude: parseFloat(latA), longitude: parseFloat(lonA),
              subject_name: nameA, scan_start_age: 20, scan_end_age: 50, ayanamsa, house_system: houseSystem,
            });
            setTimingData(t);
          } catch { /* optional — don't block */ }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to generate compatibility report");
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [searchParams, nameA, nameB, relationshipType]);

  /* ── Fetch Best Bet (marriage only) ── */
  useEffect(() => {
    if (relationshipType !== "marriage" || !report) return;
    const fetchBestBet = async () => {
      const bdA = searchParams.get("birth_datetime_utc_a");
      const latA = searchParams.get("latitude_a");
      const lonA = searchParams.get("longitude_a");
      const bdB = searchParams.get("birth_datetime_utc_b");
      const latB = searchParams.get("latitude_b");
      const lonB = searchParams.get("longitude_b");
      const ayanamsa = searchParams.get("ayanamsa") || "lahiri";
      const houseSystem = searchParams.get("house_system") || "W";
      if (!bdA || !latA || !lonA || !bdB || !latB || !lonB) return;
      try {
        const res = await bestBetApi.analyze({
          birth_datetime_utc_a: bdA, latitude_a: parseFloat(latA), longitude_a: parseFloat(lonA), subject_name_a: nameA,
          birth_datetime_utc_b: bdB, latitude_b: parseFloat(latB), longitude_b: parseFloat(lonB), subject_name_b: nameB,
          ayanamsa, house_system: houseSystem,
        });
        setBestBetReport(res);
      } catch { /* optional */ }
    };
    fetchBestBet();
  }, [relationshipType, report, searchParams, nameA, nameB]);

  const activeTimingWindows: TransitScanYear[] = timingData
    ? timingData.scan_results.filter((r) => r.status !== "not_indicated")
    : [];

  const runSadhuPadhdhati = async () => {
    if (sadhuLoading) return;
    const bdA = searchParams.get("birth_datetime_utc_a");
    const latA = searchParams.get("latitude_a");
    const lonA = searchParams.get("longitude_a");
    const bdB = searchParams.get("birth_datetime_utc_b");
    const latB = searchParams.get("latitude_b");
    const lonB = searchParams.get("longitude_b");
    const ayanamsa = searchParams.get("ayanamsa") || "lahiri";
    const houseSystem = searchParams.get("house_system") || "W";
    if (!bdA || !latA || !lonA || !bdB || !latB || !lonB) { setSadhuError("Missing birth data"); return; }
    setSadhuLoading(true); setSadhuError(null);
    try {
      const [rA, rB] = await Promise.all([
        sadhuPadhdhatiApi.analyze({ birth_datetime_utc: bdA, latitude: parseFloat(latA), longitude: parseFloat(lonA), subject_name: nameA, gender: sadhuGenderA, ayanamsa, house_system: houseSystem }),
        sadhuPadhdhatiApi.analyze({ birth_datetime_utc: bdB, latitude: parseFloat(latB), longitude: parseFloat(lonB), subject_name: nameB, gender: sadhuGenderB, ayanamsa, house_system: houseSystem }),
      ]);
      setSadhuA(rA); setSadhuB(rB);
    } catch (e) {
      setSadhuError(e instanceof Error ? e.message : "Sadhu Padhdhati analysis failed");
    } finally { setSadhuLoading(false); }
  };

  const handleExport = async (format: "json" | "markdown" | "html") => {
    if (!report || exporting) return;
    setExporting(true);
    try {
      const bdA = searchParams.get("birth_datetime_utc_a")!;
      const latA = searchParams.get("latitude_a")!;
      const lonA = searchParams.get("longitude_a")!;
      const bdB = searchParams.get("birth_datetime_utc_b")!;
      const latB = searchParams.get("latitude_b")!;
      const lonB = searchParams.get("longitude_b")!;
      const ayanamsa = searchParams.get("ayanamsa") || "lahiri";
      const houseSystem = searchParams.get("house_system") || "W";
      const res = await exportApi.compatibility({
        birth_datetime_utc_a: bdA, latitude_a: parseFloat(latA), longitude_a: parseFloat(lonA), subject_name_a: nameA,
        birth_datetime_utc_b: bdB, latitude_b: parseFloat(latB), longitude_b: parseFloat(lonB), subject_name_b: nameB,
        relationship_type: relationshipType, ayanamsa, house_system: houseSystem, format,
      });
      if (!res.ok) throw new Error(`Export failed with HTTP ${res.status}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `compatibility-${nameA}-${nameB}.${format}`;
      document.body.appendChild(a); a.click();
      document.body.removeChild(a); window.URL.revokeObjectURL(url);
    } catch (e) { alert(e instanceof Error ? e.message : "Export failed"); }
    finally { setExporting(false); }
  };

  const handleShare = async () => {
    const url = window.location.href;
    let copied = false;
    if (navigator.clipboard?.writeText) {
      try { await navigator.clipboard.writeText(url); copied = true; } catch { copied = false; }
    }
    if (!copied) {
      try {
        const t = document.createElement("textarea");
        t.value = url; t.style.cssText = "position:fixed;opacity:0";
        document.body.appendChild(t); t.focus(); t.select();
        copied = document.execCommand("copy");
        document.body.removeChild(t);
      } catch { copied = false; }
    }
    setShareStatus(copied ? "copied" : "failed");
    setTimeout(() => setShareStatus("idle"), 2500);
  };

  /* ── Loading / Error states ── */
  if (loading) {
    return (
      <div className="flex min-h-dvh items-center justify-center" style={{ backgroundColor: "var(--bg-primary)" }}>
        <div className="text-center">
          <div
            className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-2"
            style={{ borderColor: "var(--border-primary)", borderTopColor: relConfig.accent }}
          />
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            Analyzing {relConfig.label.toLowerCase()}…
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-dvh items-center justify-center" style={{ backgroundColor: "var(--bg-primary)" }}>
        <div
          className="max-w-md rounded-xl border p-6"
          style={{ borderColor: "rgba(239,68,68,0.3)", backgroundColor: "rgba(239,68,68,0.05)" }}
        >
          <h2 className="mb-2 text-base font-bold text-red-400">Analysis Error</h2>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{error}</p>
          <button
            onClick={() => router.push("/dashboard")}
            className="mt-4 rounded-lg border px-4 py-2 text-xs font-semibold transition hover:opacity-80"
            style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}
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
  const overallPct = Math.round(report.compatibility_percentage);

  return (
    <div className="min-h-dvh" style={{ backgroundColor: "var(--bg-primary)" }}>

      {/* ── Top Navigation Bar ── */}
      <div
        className="sticky top-0 z-40 border-b backdrop-blur-md"
        style={{
          borderColor: "var(--border-primary)",
          backgroundColor: "var(--bg-card)",
          backdropFilter: "blur(12px)",
        }}
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
          {/* Left: back + check another */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push("/dashboard")}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition hover:opacity-80"
              style={{ color: "var(--text-secondary)" }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
              Dashboard
            </button>
            <span style={{ color: "var(--border-primary)" }}>|</span>
            <button
              onClick={() => openCreateModal("compatibility")}
              className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition hover:opacity-80"
              style={{
                borderColor: relConfig.accentBorder,
                backgroundColor: relConfig.accentSoft,
                color: relConfig.accent,
              }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d={relConfig.icon} />
              </svg>
              New Compatibility
            </button>
          </div>

          {/* Center: title */}
          <div className="hidden text-center md:block">
            <p className="text-[11px] font-bold uppercase tracking-widest" style={{ color: relConfig.accent }}>
              {relConfig.label}
            </p>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              {nameA} · {nameB}
            </p>
          </div>

          {/* Right: actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleExport("html")}
              disabled={exporting}
              className="rounded-lg border px-3 py-1.5 text-xs font-medium transition hover:opacity-80 disabled:opacity-40"
              style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}
            >
              {exporting ? "Exporting…" : "Export"}
            </button>
            <button
              onClick={() => window.print()}
              className="rounded-lg border px-3 py-1.5 text-xs font-medium transition hover:opacity-80"
              style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}
            >
              Print
            </button>
            <button
              onClick={handleShare}
              className="rounded-lg border px-3 py-1.5 text-xs font-semibold transition hover:opacity-80"
              style={{
                borderColor: shareStatus === "copied" ? "rgba(16,185,129,0.4)" : "var(--border-primary)",
                backgroundColor: shareStatus === "copied" ? "rgba(16,185,129,0.08)" : "transparent",
                color: shareStatus === "copied" ? "#10b981" : shareStatus === "failed" ? "#ef4444" : "var(--text-secondary)",
              }}
            >
              {shareStatus === "copied" ? "Link Copied" : shareStatus === "failed" ? "Copy Failed" : "Share"}
            </button>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-6 py-6">

        {/* ── Hero Card ── */}
        <div
          className="mb-6 overflow-hidden rounded-xl border p-6"
          style={{ borderColor: relConfig.accentBorder, backgroundColor: relConfig.accentSoft }}
        >
          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            {/* Names + type */}
            <div>
              <p className="mb-1 text-[11px] font-bold uppercase tracking-widest" style={{ color: relConfig.accent }}>
                {relConfig.label}
              </p>
              <h1 className="text-2xl font-black" style={{ color: "var(--text-primary)" }}>
                {report.subject_name_a}
                <span className="mx-3 font-normal" style={{ color: relConfig.accent }}>·</span>
                {report.subject_name_b}
              </h1>
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                {relConfig.subLabel}
              </p>
            </div>

            {/* Score ring */}
            <div className="flex items-center gap-5">
              <div
                className="relative flex h-24 w-24 flex-shrink-0 items-center justify-center rounded-full"
                style={{
                  border: `3px solid ${relConfig.accent}`,
                  backgroundColor: relConfig.accentSoft,
                }}
              >
                <div className="text-center">
                  <div className="text-2xl font-black" style={{ color: "var(--text-primary)" }}>{overallPct}%</div>
                  <div className="text-[9px] font-bold uppercase tracking-wider" style={{ color: relConfig.accent }}>
                    {report.verdict}
                  </div>
                </div>
              </div>
              <div className="hidden sm:block">
                <p className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
                  Ashtakoota Score
                </p>
                <p className="text-xl font-black" style={{ color: "var(--text-primary)" }}>
                  {fmtScore(report.total_score)}<span className="text-sm font-normal" style={{ color: "var(--text-muted)" }}> / {fmtScore(report.max_total_score)}</span>
                </p>
                <p className="mt-1 text-[11px]" style={{ color: "var(--text-muted)" }}>
                  {report.kootas.length} kootas analyzed
                </p>
              </div>
            </div>
          </div>

          {/* Quick status pills */}
          <div className="mt-5 flex flex-wrap gap-2 border-t pt-4" style={{ borderColor: relConfig.accentBorder }}>
            {report.kootas.slice(0, 6).map((k) => (
              <span
                key={k.name}
                className="rounded-full border px-3 py-0.5 text-[11px] font-semibold"
                style={{
                  borderColor: `${statusColor(k.status)}33`,
                  backgroundColor: `${statusColor(k.status)}0d`,
                  color: statusColor(k.status),
                }}
              >
                {k.name} · {fmtScore(k.obtained_score)}/{fmtScore(k.max_score)}
              </span>
            ))}
          </div>
        </div>

        {/* ── Main Layout ── */}
        <div className="flex gap-5">

          {/* ── Tab Content ── */}
          <div className="flex-1 min-w-0">

            {/* Tab bar */}
            <div
              className="mb-4 flex overflow-x-auto rounded-lg border"
              style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
            >
              {TABS.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setActiveTab(t.key as TabKey)}
                  className="flex-shrink-0 px-4 py-2.5 text-xs font-semibold transition"
                  style={{
                    color: activeTab === t.key ? relConfig.accent : "var(--text-muted)",
                    borderBottom: activeTab === t.key ? `2px solid ${relConfig.accent}` : "2px solid transparent",
                  }}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* ── Overview Tab ── */}
            {activeTab === "overview" && (
              <div className="space-y-4">
                {/* Person cards */}
                <Card>
                  <SectionTitle>People</SectionTitle>
                  <div className="grid grid-cols-3 items-center gap-4">
                    <div
                      className="rounded-lg border p-4 text-center"
                      style={{ borderColor: relConfig.accentBorder, backgroundColor: relConfig.accentSoft }}
                    >
                      <div
                        className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold"
                        style={{ backgroundColor: relConfig.accentSoft, color: relConfig.accent, border: `1px solid ${relConfig.accentBorder}` }}
                      >
                        {report.subject_name_a.charAt(0).toUpperCase()}
                      </div>
                      <p className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>{report.subject_name_a}</p>
                      <p className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>
                        {relationshipType === "marriage" ? "Bride / Groom" : relationshipType === "business" ? "Partner A" : "Person A"}
                      </p>
                    </div>
                    <div className="flex items-center justify-center">
                      <div
                        className="flex h-9 w-9 items-center justify-center rounded-full border text-[11px] font-black"
                        style={{ borderColor: "var(--border-primary)", color: relConfig.accent, backgroundColor: relConfig.accentSoft }}
                      >
                        VS
                      </div>
                    </div>
                    <div
                      className="rounded-lg border p-4 text-center"
                      style={{ borderColor: "rgba(6,182,212,0.25)", backgroundColor: "rgba(6,182,212,0.05)" }}
                    >
                      <div
                        className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold"
                        style={{ backgroundColor: "rgba(6,182,212,0.1)", color: "#06b6d4", border: "1px solid rgba(6,182,212,0.3)" }}
                      >
                        {report.subject_name_b.charAt(0).toUpperCase()}
                      </div>
                      <p className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>{report.subject_name_b}</p>
                      <p className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>
                        {relationshipType === "marriage" ? "Bride / Groom" : relationshipType === "business" ? "Partner B" : "Person B"}
                      </p>
                    </div>
                  </div>
                </Card>

                {/* Score dashboard + Radar */}
                <div className="grid grid-cols-2 gap-4">
                  <Card>
                    <SectionTitle>Score Breakdown</SectionTitle>
                    <div className="space-y-2">
                      {/* Overall */}
                      <div
                        className="rounded-lg border p-3"
                        style={{ borderColor: relConfig.accentBorder, backgroundColor: relConfig.accentSoft }}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold" style={{ color: relConfig.accent }}>Overall Match</span>
                          <span className="text-lg font-black" style={{ color: "var(--text-primary)" }}>{overallPct}%</span>
                        </div>
                        <div className="mt-2 h-2 overflow-hidden rounded-full" style={{ backgroundColor: "var(--bg-primary)" }}>
                          <div className="h-full rounded-full transition-all" style={{ width: `${overallPct}%`, backgroundColor: relConfig.accent }} />
                        </div>
                      </div>
                      {/* Per koota */}
                      {report.kootas.map((k) => {
                        const pct = (k.obtained_score / k.max_score) * 100;
                        const sc = statusColor(k.status);
                        return (
                          <div key={k.name} className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>{k.name}</span>
                              <span className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                                {fmtScore(k.obtained_score)} / {fmtScore(k.max_score)}
                              </span>
                            </div>
                            <ScoreBar pct={pct} color={sc} />
                          </div>
                        );
                      })}
                    </div>
                  </Card>

                  {/* Radar */}
                  <Card>
                    <SectionTitle>Compatibility Radar</SectionTitle>
                    <div className="flex items-center justify-center">
                      <svg width="240" height="240" viewBox="0 0 200 200" className="overflow-visible">
                        {[100, 66, 33].map((ring) => (
                          <polygon key={ring} points={radarPolygon(radarAxes.map(() => ring))}
                            fill="none" stroke="var(--border-primary)" strokeWidth="1" />
                        ))}
                        {radarAxes.map((a, i) => {
                          const [x, y] = radarPoint(i, radarN, 100);
                          return <line key={a.label} x1={RC} y1={RC} x2={x} y2={y} stroke="var(--border-primary)" />;
                        })}
                        <polygon
                          points={radarPolygon(radarAxes.map((a) => a.value))}
                          fill={relConfig.accentSoft.replace("0.08", "0.25")}
                          stroke={relConfig.accent}
                          strokeWidth="2"
                        />
                        {radarAxes.map((a, i) => {
                          const [x, y] = radarPoint(i, radarN, 122);
                          const anchor = x > RC + 2 ? "start" : x < RC - 2 ? "end" : "middle";
                          return (
                            <text key={a.label} x={x} y={y} textAnchor={anchor}
                              dominantBaseline="middle" fill="var(--text-muted)" fontSize="7.5">
                              {a.label}
                            </text>
                          );
                        })}
                      </svg>
                    </div>
                  </Card>
                </div>

                {/* Strengths & Challenges */}
                {(report.strengths.length > 0 || report.challenges.length > 0) && (
                  <div className="grid grid-cols-2 gap-4">
                    {report.strengths.length > 0 && (
                      <Card>
                        <h2 className="mb-3 text-sm font-bold" style={{ color: "#10b981" }}>Strengths</h2>
                        <ul className="space-y-2">
                          {report.strengths.map((s, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
                              <span style={{ color: "#10b981", marginTop: 1 }}>✓</span><span>{s}</span>
                            </li>
                          ))}
                        </ul>
                      </Card>
                    )}
                    {report.challenges.length > 0 && (
                      <Card>
                        <h2 className="mb-3 text-sm font-bold" style={{ color: "#f59e0b" }}>Challenges</h2>
                        <ul className="space-y-2">
                          {report.challenges.map((c, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
                              <span style={{ color: "#f59e0b", marginTop: 1 }}>!</span><span>{c}</span>
                            </li>
                          ))}
                        </ul>
                      </Card>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ── Ashtakoota Tab ── */}
            {activeTab === "ashtakoota" && (
              <Card>
                <SectionTitle>Ashtakoota Matching — 36 Points</SectionTitle>
                <div className="space-y-3">
                  {report.kootas.map((k, i) => {
                    const pct = (k.obtained_score / k.max_score) * 100;
                    const sc = statusColor(k.status);
                    return (
                      <div key={k.name} className="rounded-lg border p-4" style={{ borderColor: "var(--border-primary)" }}>
                        <div className="mb-2 flex items-start justify-between gap-2">
                          <div>
                            <span className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                              {i + 1}. {k.name}
                            </span>
                            <p className="mt-0.5 text-[10px]" style={{ color: "var(--text-muted)" }}>{k.description}</p>
                          </div>
                          <div className="flex-shrink-0 text-right">
                            <div className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                              {fmtScore(k.obtained_score)} / {fmtScore(k.max_score)}
                            </div>
                            <div className="text-[10px] font-semibold" style={{ color: sc }}>{k.status}</div>
                          </div>
                        </div>
                        <ScoreBar pct={pct} color={sc} />
                      </div>
                    );
                  })}
                  {/* Total */}
                  <div
                    className="flex items-center justify-between rounded-lg border p-4"
                    style={{ borderColor: relConfig.accentBorder, backgroundColor: relConfig.accentSoft }}
                  >
                    <span className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>Total Score</span>
                    <span className="text-lg font-black" style={{ color: relConfig.accent }}>
                      {fmtScore(report.total_score)} / {fmtScore(report.max_total_score)}
                    </span>
                  </div>
                </div>
              </Card>
            )}

            {/* ── Doshas Tab ── */}
            {activeTab === "doshas" && (
              <Card>
                <SectionTitle>Dosha Analysis</SectionTitle>
                {report.doshas.length === 0 ? (
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>No doshas detected for this pairing.</p>
                ) : (
                  <div className="space-y-3">
                    {report.doshas.map((d) => {
                      const borderCol = d.has_dosha
                        ? d.severity === "Severe" ? "rgba(239,68,68,0.3)" : "rgba(245,158,11,0.3)"
                        : "rgba(16,185,129,0.3)";
                      const bgCol = d.has_dosha
                        ? d.severity === "Severe" ? "rgba(239,68,68,0.06)" : "rgba(245,158,11,0.06)"
                        : "rgba(16,185,129,0.05)";
                      const badgeCol = d.has_dosha
                        ? d.severity === "Severe" ? "#ef4444" : "#f59e0b"
                        : "#10b981";
                      return (
                        <div key={d.name} className="rounded-lg border p-4"
                          style={{ borderColor: borderCol, backgroundColor: bgCol }}>
                          <div className="mb-1 flex items-center justify-between">
                            <h3 className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>{d.name}</h3>
                            <span
                              className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                              style={{ backgroundColor: `${badgeCol}1a`, color: badgeCol }}
                            >
                              {d.has_dosha ? `${d.severity} Dosha` : "No Dosha"}
                            </span>
                          </div>
                          <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>{d.description}</p>
                        </div>
                      );
                    })}
                  </div>
                )}
              </Card>
            )}

            {/* ── Timeline Tab (marriage only) ── */}
            {activeTab === "timeline" && (
              <div className="space-y-4">
                {/* Method selector */}
                <div
                  className="flex gap-1 rounded-lg border p-1"
                  style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
                >
                  {[
                    { key: "transit", label: "Jupiter / Saturn Transit" },
                    { key: "sadhu", label: "Sadhu Padhdhati" },
                  ].map((m) => (
                    <button
                      key={m.key}
                      onClick={() => setTimingMethod(m.key as "transit" | "sadhu")}
                      className="flex-1 rounded-md px-3 py-2 text-xs font-semibold transition"
                      style={{
                        backgroundColor: timingMethod === m.key ? relConfig.accentSoft : "transparent",
                        color: timingMethod === m.key ? relConfig.accent : "var(--text-muted)",
                        border: timingMethod === m.key ? `1px solid ${relConfig.accentBorder}` : "1px solid transparent",
                      }}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>

                {/* Transit method */}
                {timingMethod === "transit" && (
                  <Card>
                    <div className="mb-4">
                      <h2 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>Jupiter / Saturn Transit Scanner</h2>
                      <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                        Marriage timing windows for {nameA} — Jupiter activation of natal Venus with Saturn obstruction filter
                      </p>
                    </div>
                    {timingData ? (
                      <>
                        <div className="mb-4 grid grid-cols-3 gap-3">
                          {[
                            { label: "Natal Venus Sign", value: timingData.natal_venus_rashi, color: relConfig.accent },
                            { label: "7th House Cusp", value: timingData.natal_seventh_cusp_rashi, color: "#06b6d4" },
                            { label: "Scan Range", value: `Age ${timingData.scan_start_age}–${timingData.scan_end_age}`, color: "#10b981" },
                          ].map((stat) => (
                            <div key={stat.label} className="rounded-lg border p-3 text-center"
                              style={{ borderColor: `${stat.color}33`, backgroundColor: `${stat.color}0d` }}>
                              <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>{stat.label}</p>
                              <p className="mt-1 text-sm font-bold" style={{ color: stat.color }}>{stat.value}</p>
                            </div>
                          ))}
                        </div>
                        <div className="mb-4 grid grid-cols-3 gap-3">
                          {[
                            { label: "Probable Windows", value: timingData.probable_windows, color: "#10b981" },
                            { label: "Delayed Windows",  value: timingData.delayed_windows,  color: "#f59e0b" },
                            { label: "Years Scanned",   value: timingData.total_years_scanned, color: "var(--text-muted)" },
                          ].map((s) => (
                            <div key={s.label} className="rounded-lg border p-3 text-center"
                              style={{ borderColor: "var(--border-primary)" }}>
                              <p className="text-2xl font-black" style={{ color: s.color }}>{s.value}</p>
                              <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>{s.label}</p>
                            </div>
                          ))}
                        </div>

                        {activeTimingWindows.length > 0 ? (
                          <div className="space-y-3">
                            <p className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                              Active Marriage Timing Windows
                            </p>
                            {activeTimingWindows.map((w) => (
                              <div key={w.year} className="rounded-lg border p-4"
                                style={{ borderColor: "var(--border-primary)" }}>
                                <div className="mb-2 flex items-center justify-between">
                                  <div>
                                    <span className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>{w.year}</span>
                                    <span className="ml-2 text-[10px]" style={{ color: "var(--text-muted)" }}>Age {w.age_at_year.toFixed(0)}</span>
                                  </div>
                                  <span className="text-xs font-bold" style={{ color: TIMING_COLOR[w.status] }}>
                                    {TIMING_LABEL[w.status]}
                                  </span>
                                </div>
                                <div className="mb-2 grid grid-cols-2 gap-2 text-[10px]">
                                  <div className="rounded px-2 py-1" style={{ backgroundColor: "var(--bg-primary)" }}>
                                    <span style={{ color: relConfig.accent }}>Jupiter: </span>
                                    <span style={{ color: "var(--text-secondary)" }}>{w.jupiter_rashi}</span>
                                  </div>
                                  <div className="rounded px-2 py-1" style={{ backgroundColor: "var(--bg-primary)" }}>
                                    <span style={{ color: "#06b6d4" }}>Saturn: </span>
                                    <span style={{ color: "var(--text-secondary)" }}>{w.saturn_rashi}</span>
                                  </div>
                                </div>
                                {w.aspect_details.length > 0 && (
                                  <p className="mb-1 text-[11px]" style={{ color: "#10b981" }}>
                                    ✓ {w.aspect_details.join("; ")}
                                  </p>
                                )}
                                {w.saturn_obstruction_details.length > 0 && (
                                  <p className="mb-1 text-[11px]" style={{ color: "#f59e0b" }}>
                                    ! {w.saturn_obstruction_details.join("; ")}
                                  </p>
                                )}
                                <div className="mt-2 h-1.5 overflow-hidden rounded-full" style={{ backgroundColor: "var(--bg-primary)" }}>
                                  <div className={`h-full rounded-full ${TIMING_BAR[w.status]}`}
                                    style={{ width: `${TIMING_FILL[w.status] ?? 20}%` }} />
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="rounded-lg border p-4 text-center" style={{ borderColor: "var(--border-primary)" }}>
                            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                              No active marriage timing windows found in the scanned age range. The transit scanner checks Jupiter/Venus activations only.
                            </p>
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="rounded-lg border px-3 py-2 text-[11px]"
                        style={{ borderColor: "rgba(245,158,11,0.3)", backgroundColor: "rgba(245,158,11,0.06)", color: "#f59e0b" }}>
                        Marriage timing scan could not be loaded. The backend endpoint may be unavailable.
                      </div>
                    )}
                  </Card>
                )}

                {/* Sadhu Padhdhati method */}
                {timingMethod === "sadhu" && (
                  <Card>
                    <div className="mb-4">
                      <h2 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>Sadhu Padhdhati (Sudarshana Chakra)</h2>
                      <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                        Alternate marriage-timing method — compare predicted year against the Jupiter/Saturn scan.
                      </p>
                    </div>
                    <div className="mb-4 grid grid-cols-2 gap-3">
                      {[
                        { name: nameA, gender: sadhuGenderA, setGender: setSadhuGenderA },
                        { name: nameB, gender: sadhuGenderB, setGender: setSadhuGenderB },
                      ].map((p) => (
                        <div key={p.name} className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
                          <label className="mb-1 block text-[10px]" style={{ color: "var(--text-muted)" }}>{p.name}'s Gender</label>
                          <select
                            value={p.gender}
                            onChange={(e) => p.setGender(e.target.value as "male" | "female")}
                            className="obsidian-input w-full text-xs"
                          >
                            <option value="male">Male</option>
                            <option value="female">Female</option>
                          </select>
                        </div>
                      ))}
                    </div>
                    <button
                      onClick={runSadhuPadhdhati}
                      disabled={sadhuLoading}
                      className="mb-4 w-full rounded-lg border px-3 py-2 text-xs font-semibold transition hover:opacity-80 disabled:opacity-50"
                      style={{ borderColor: relConfig.accentBorder, backgroundColor: relConfig.accentSoft, color: relConfig.accent }}
                    >
                      {sadhuLoading ? "Computing…" : "Run Sadhu Padhdhati Analysis"}
                    </button>
                    {sadhuError && (
                      <div className="mb-4 rounded-lg border px-3 py-2 text-[11px]"
                        style={{ borderColor: "rgba(239,68,68,0.3)", color: "#ef4444" }}>{sadhuError}</div>
                    )}
                    {sadhuA && sadhuB && (
                      <div className="grid grid-cols-2 gap-4">
                        {[{ label: nameA, result: sadhuA }, { label: nameB, result: sadhuB }].map(({ label, result }) => (
                          <div key={label} className="rounded-lg border p-4" style={{ borderColor: "var(--border-primary)" }}>
                            <p className="mb-2 text-xs font-bold" style={{ color: "var(--text-primary)" }}>{label}</p>
                            <div className="mb-3 text-center">
                              <p className="text-3xl font-black" style={{ color: relConfig.accent }}>{result.predicted_year}</p>
                              <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                                Window {result.window_start}–{result.window_end}
                              </p>
                            </div>
                            <div className="space-y-1 text-[10px]" style={{ color: "var(--text-muted)" }}>
                              <div className="flex justify-between">
                                <span>Net Delay (years)</span>
                                <span style={{ color: "var(--text-secondary)" }}>{result.net_delay}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>D1 delay</span>
                                <span style={{ color: "var(--text-secondary)" }}>
                                  {result.d1.delay.toFixed(1)} (EF {result.d1.escalation_factor}, RF {result.d1.reducing_factor})
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span>D9 delay</span>
                                <span style={{ color: "var(--text-secondary)" }}>
                                  {result.d9.delay.toFixed(1)} (EF {result.d9.escalation_factor}, RF {result.d9.reducing_factor})
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    <p className="mt-4 text-[10px]" style={{ color: "var(--text-muted)" }}>
                      Escalation Factor (EF) is computed from classical aspect/conjunction/parivartana rules; Reducing Factor (RF)
                      is an approximation. Treat predicted year as an estimate alongside the Jupiter/Saturn scan.
                    </p>
                  </Card>
                )}
              </div>
            )}

            {/* ── Best Bet 58 Tab (marriage only) ── */}
            {activeTab === "bestbet" && (
              <div className="space-y-4">
                <Card>
                  <SectionTitle>Best Bet 58-Point Marriage Matching</SectionTitle>
                  <p className="mb-4 text-xs" style={{ color: "var(--text-muted)" }}>
                    Comprehensive analysis using the Best Bet method (Jai Shaker): Practical (36) · Karmic (12) · Future (10) — total 58 points.
                  </p>
                  {bestBetReport ? (
                    <>
                      {/* Overall */}
                      <div
                        className="mb-5 flex items-center justify-between rounded-lg border p-5"
                        style={{ borderColor: relConfig.accentBorder, backgroundColor: relConfig.accentSoft }}
                      >
                        <div>
                          <p className="text-xs" style={{ color: "var(--text-muted)" }}>Overall Score</p>
                          <p className="text-2xl font-black" style={{ color: "var(--text-primary)" }}>
                            {bestBetReport.total_score} / {bestBetReport.max_score}
                          </p>
                          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{bestBetReport.verdict}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-4xl font-black" style={{ color: relConfig.accent }}>{bestBetReport.percentage}%</p>
                          <p className="text-xs" style={{ color: "var(--text-muted)" }}>{bestBetReport.status}</p>
                        </div>
                      </div>

                      {/* Group scores */}
                      <div className="mb-5 grid grid-cols-3 gap-3">
                        {[
                          { label: "Practical", value: `${bestBetReport.practical_score}/${bestBetReport.practical_max}`, sub: "Spiritual · Psych · Physical", color: "#10b981" },
                          { label: "Karmic",    value: `${bestBetReport.karmic_score}/${bestBetReport.karmic_max}`,    sub: "Mars Dosha · Pattern",        color: "#f59e0b" },
                          { label: "Future",    value: `${bestBetReport.future_score}/${bestBetReport.future_max}`,    sub: "Dasha · Mutual Planets",      color: "#06b6d4" },
                        ].map((g) => (
                          <div key={g.label} className="rounded-lg border p-4 text-center"
                            style={{ borderColor: `${g.color}33`, backgroundColor: `${g.color}0d` }}>
                            <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>{g.label}</p>
                            <p className="text-lg font-black" style={{ color: g.color }}>{g.value}</p>
                            <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>{g.sub}</p>
                          </div>
                        ))}
                      </div>

                      {/* Sub-factors */}
                      <div className="mb-5">
                        <h3 className="mb-3 text-xs font-bold" style={{ color: "var(--text-primary)" }}>Detailed Breakdown</h3>
                        <div className="space-y-2">
                          {bestBetReport.sub_factors.map((f) => {
                            const pct = (f.score / f.max) * 100;
                            const col = pct >= 70 ? "#10b981" : pct >= 40 ? "#f59e0b" : "#ef4444";
                            return (
                              <div key={f.name} className="rounded-lg border p-3"
                                style={{ borderColor: "var(--border-primary)" }}>
                                <div className="mb-1 flex items-center justify-between">
                                  <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>{f.name}</span>
                                  <span className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                                    {Number.isInteger(f.score) ? f.score : f.score.toFixed(1)} / {f.max}
                                  </span>
                                </div>
                                <p className="mb-1.5 text-[10px]" style={{ color: "var(--text-muted)" }}>{f.description}</p>
                                <ScoreBar pct={pct} color={col} />
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Strengths + challenges */}
                      <div className="grid grid-cols-2 gap-4">
                        {bestBetReport.strengths.length > 0 && (
                          <div className="rounded-lg border p-4"
                            style={{ borderColor: "rgba(16,185,129,0.25)", backgroundColor: "rgba(16,185,129,0.05)" }}>
                            <h3 className="mb-2 text-xs font-bold" style={{ color: "#10b981" }}>Strengths</h3>
                            <ul className="space-y-1">
                              {bestBetReport.strengths.map((s, i) => (
                                <li key={i} className="text-[11px]" style={{ color: "var(--text-secondary)" }}>• {s}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {bestBetReport.challenges.length > 0 && (
                          <div className="rounded-lg border p-4"
                            style={{ borderColor: "rgba(245,158,11,0.25)", backgroundColor: "rgba(245,158,11,0.05)" }}>
                            <h3 className="mb-2 text-xs font-bold" style={{ color: "#f59e0b" }}>Challenges</h3>
                            <ul className="space-y-1">
                              {bestBetReport.challenges.map((c, i) => (
                                <li key={i} className="text-[11px]" style={{ color: "var(--text-secondary)" }}>• {c}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="rounded-lg border p-4 text-center" style={{ borderColor: "var(--border-primary)" }}>
                      <div className="mx-auto mb-2 h-5 w-5 animate-spin rounded-full border-2"
                        style={{ borderColor: "var(--border-primary)", borderTopColor: relConfig.accent }} />
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>Loading Best Bet analysis…</p>
                    </div>
                  )}
                </Card>
              </div>
            )}

            {/* ── Recommendations Tab ── */}
            {activeTab === "recommendations" && (
              <Card>
                <SectionTitle>Recommendations</SectionTitle>
                {report.recommendations.length === 0 ? (
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>No specific recommendations for this pairing.</p>
                ) : (
                  <ul className="space-y-3">
                    {report.recommendations.map((r, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-3 rounded-lg border p-3 text-xs"
                        style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}
                      >
                        <span className="mt-0.5 flex-shrink-0 font-bold" style={{ color: relConfig.accent }}>{i + 1}.</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            )}
          </div>

          {/* ── Sticky Right Sidebar ── */}
          <div className="sticky top-20 hidden h-fit w-64 flex-col gap-4 lg:flex">

            {/* Score card */}
            <Card className="text-center">
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                {relConfig.label}
              </p>
              <div
                className="relative mx-auto flex h-20 w-20 items-center justify-center rounded-full"
                style={{ border: `3px solid ${relConfig.accent}`, backgroundColor: relConfig.accentSoft }}
              >
                <div>
                  <div className="text-xl font-black" style={{ color: "var(--text-primary)" }}>{overallPct}%</div>
                </div>
              </div>
              <p className="mt-3 text-sm font-bold" style={{ color: relConfig.accent }}>{report.verdict}</p>
              <p className="mt-0.5 text-[10px]" style={{ color: "var(--text-muted)" }}>
                {report.subject_name_a} · {report.subject_name_b}
              </p>
              <div className="mt-3 grid grid-cols-2 gap-2 border-t pt-3 text-[11px]"
                style={{ borderColor: "var(--border-primary)" }}>
                <div className="rounded-lg p-2" style={{ backgroundColor: "var(--bg-primary)" }}>
                  <p style={{ color: "var(--text-muted)" }}>Ashtakoota</p>
                  <p className="font-bold" style={{ color: "var(--text-primary)" }}>
                    {fmtScore(report.total_score)}/{fmtScore(report.max_total_score)}
                  </p>
                </div>
                <div className="rounded-lg p-2" style={{ backgroundColor: "var(--bg-primary)" }}>
                  <p style={{ color: "var(--text-muted)" }}>Match %</p>
                  <p className="font-bold" style={{ color: "var(--text-primary)" }}>{overallPct}/100</p>
                </div>
              </div>
            </Card>

            {/* Quick stats */}
            <Card>
              <p className="mb-3 text-xs font-bold" style={{ color: "var(--text-primary)" }}>Analysis Summary</p>
              <div className="space-y-2 text-xs">
                {[
                  { label: "Relationship",   value: relConfig.label },
                  { label: "Kootas",         value: String(report.kootas.length) },
                  { label: "Doshas Checked", value: String(report.doshas.length) },
                  { label: "Strengths",      value: String(report.strengths.length),   color: "#10b981" },
                  { label: "Challenges",     value: String(report.challenges.length),   color: "#f59e0b" },
                ].map((s) => (
                  <div key={s.label} className="flex items-center justify-between">
                    <span style={{ color: "var(--text-muted)" }}>{s.label}</span>
                    <span className="font-semibold" style={{ color: s.color ?? "var(--text-secondary)" }}>{s.value}</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Actions */}
            <Card>
              <p className="mb-3 text-xs font-bold" style={{ color: "var(--text-primary)" }}>Actions</p>
              <div className="space-y-2">
                <button
                  onClick={() => handleExport("html")}
                  disabled={exporting}
                  className="w-full rounded-lg border px-3 py-2 text-xs font-semibold transition hover:opacity-80 disabled:opacity-40"
                  style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}
                >
                  {exporting ? "Exporting…" : "Export Report"}
                </button>
                <button
                  onClick={() => window.print()}
                  className="w-full rounded-lg border px-3 py-2 text-xs font-semibold transition hover:opacity-80"
                  style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}
                >
                  Print Report
                </button>
                <button
                  onClick={handleShare}
                  className="w-full rounded-lg border px-3 py-2 text-xs font-semibold transition hover:opacity-80"
                  style={{
                    borderColor: shareStatus === "copied" ? "rgba(16,185,129,0.4)" : "var(--border-primary)",
                    backgroundColor: shareStatus === "copied" ? "rgba(16,185,129,0.08)" : "transparent",
                    color: shareStatus === "copied" ? "#10b981" : "var(--text-secondary)",
                  }}
                >
                  {shareStatus === "copied" ? "Link Copied!" : "Share Link"}
                </button>
                <button
                  onClick={() => openCreateModal("compatibility")}
                  className="w-full rounded-lg border px-3 py-2 text-xs font-semibold transition hover:opacity-80"
                  style={{ borderColor: relConfig.accentBorder, backgroundColor: relConfig.accentSoft, color: relConfig.accent }}
                >
                  New Compatibility
                </button>
                <button
                  onClick={() => router.push("/dashboard")}
                  className="w-full rounded-lg border px-3 py-2 text-xs font-semibold transition hover:opacity-80"
                  style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}
                >
                  ← Dashboard
                </button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CompatibilityReportPage() {
  return (
    <Suspense fallback={null}>
      <CompatibilityReportPageContent />
    </Suspense>
  );
}
