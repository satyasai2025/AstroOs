"use client";

import { useCallback, useEffect, useState } from "react";
import { api, tokenStore } from "@/lib/api";
import { useWorkflowStore } from "@/lib/store";
import type { AyanamsaCode, HouseSystemCode, NodeTypeCode } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export const dynamic = "force-dynamic";

const AYANAMSA_OPTIONS = [
  { value: "lahiri", label: "Lahiri (default)" },
  { value: "kp", label: "Krishnamitra (KP)" },
  { value: "raman", label: "Raman" },
  { value: "yukteshwar", label: "Yukteshwar" },
  { value: "fagan_bradley", label: "Fagan / Bradley" },
  { value: "true_chitra", label: "True Chitra" },
  { value: "true_pushya", label: "True Pushya" },
];

const HOUSE_SYSTEM_OPTIONS = [
  { value: "W", label: "W — Whole Sign" },
  { value: "P", label: "P — Placidus" },
  { value: "K", label: "K — Koch" },
  { value: "E", label: "E — Equal" },
];

const NODE_TYPE_OPTIONS = [
  { value: "mean", label: "Mean Node (default)" },
  { value: "true", label: "True Node" },
];

export default function ReportsPdfPage() {
  const storeRequest = useWorkflowStore((s) => s.request);

  // ── Form fields ──────────────────────────────────────────────────────────
  const [selectedChartId, setSelectedChartId] = useState<string>("");
  const [subjectName, setSubjectName] = useState("");
  const [title, setTitle] = useState("AstroOS Chart Analysis Report");
  const [birthDate, setBirthDate] = useState("1995-01-01");
  const [birthTime, setBirthTime] = useState("12:00");
  const [latitude, setLatitude] = useState("28.6139");
  const [longitude, setLongitude] = useState("77.2090");
  const [ayanamsa, setAyanamsa] = useState<AyanamsaCode>("lahiri");
  const [houseSystem, setHouseSystem] = useState<HouseSystemCode>("P");
  const [nodeType, setNodeType] = useState<NodeTypeCode>("mean");

  // ── Saved charts state ──────────────────────────────────────────────────
  const [savedCharts, setSavedCharts] = useState<any[]>([]);
  const [loadingCharts, setLoadingCharts] = useState(true);

  // ── API state ────────────────────────────────────────────────────────────
  const [templates, setTemplates] = useState<string[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (storeRequest) {
      setSubjectName(storeRequest.subject_name || "");
      const birthDt = new Date(storeRequest.birth_datetime_utc);
      setBirthDate(birthDt.toISOString().split("T")[0]);
      setBirthTime(birthDt.toISOString().split("T")[1]?.slice(0, 5) || "12:00");
      setLatitude(storeRequest.latitude?.toString() || "28.6139");
      setLongitude(storeRequest.longitude?.toString() || "77.2090");
      setAyanamsa((storeRequest.ayanamsa as AyanamsaCode) || "lahiri");
      setHouseSystem((storeRequest.house_system as HouseSystemCode) || "P");
    }
  }, [storeRequest]);

  // Load available report templates on mount
  const loadTemplates = useCallback(async () => {
    try {
      setLoadingTemplates(true);
      setError(null);
      const data = await api.get<string[]>("/api/v1/report/templates");
      setTemplates(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load templates.");
    } finally {
      setLoadingTemplates(false);
    }
  }, []);

  useEffect(() => {
    void loadTemplates();
  }, [loadTemplates]);

  // Load saved charts on mount
  const loadSavedCharts = useCallback(async () => {
    try {
      setLoadingCharts(true);
      const data = await api.get<{ charts: any[]; total: number }>("/api/v1/horoscope/my-charts?limit=50&offset=0");
      setSavedCharts(data.charts || []);
      if (!storeRequest && data.charts && data.charts.length > 0) {
        const firstChart = data.charts[0];
        setSelectedChartId(firstChart.id);
        populateFromChart(firstChart);
      }
    } catch {
      setSavedCharts([]);
    } finally {
      setLoadingCharts(false);
    }
  }, [storeRequest]);

  useEffect(() => {
    void loadSavedCharts();
  }, [loadSavedCharts]);

  // Populate form fields from a saved chart
  const populateFromChart = (chart: any) => {
    setSubjectName(chart.subject_name || "");
    const birthDt = new Date(chart.birth_datetime_utc);
    setBirthDate(birthDt.toISOString().split("T")[0]);
    setBirthTime(birthDt.toISOString().split("T")[1].slice(0, 5));
    setLatitude(chart.birth_latitude?.toString() || "28.6139");
    setLongitude(chart.birth_longitude?.toString() || "77.2090");
    setAyanamsa((chart.ayanamsa as AyanamsaCode) || "lahiri");
    setHouseSystem((chart.house_system as HouseSystemCode) || "P");
  };

  // Handle saved chart selection
  const handleChartSelect = useCallback((chartId: string) => {
    setSelectedChartId(chartId);
    if (chartId === "demo") {
      setSubjectName("Arjun Sharma (Demo Chart)");
      setTitle("AstroOS Chart Analysis Report");
      setBirthDate("1995-01-01");
      setBirthTime("12:00");
      setLatitude("28.6139");
      setLongitude("77.2090");
      setAyanamsa("lahiri");
      setHouseSystem("P");
      return;
    }
    const chart = savedCharts.find((c) => c.id === chartId);
    if (chart) {
      populateFromChart(chart);
    }
  }, [savedCharts]);

  // Fill sample chart values
  const handleFillSample = () => {
    setSelectedChartId("demo");
    setSubjectName("Arjun Sharma (Demo Chart)");
    setTitle("AstroOS Chart Analysis Report");
    setBirthDate("1995-01-01");
    setBirthTime("12:00");
    setLatitude("28.6139");
    setLongitude("77.2090");
    setAyanamsa("lahiri");
    setHouseSystem("P");
  };

  // Submit & POST to /api/v1/report/chart/pdf
  const handleGeneratePdf = useCallback(async () => {
    setError(null);

    if (!birthDate || !birthTime) {
      setError("Please provide a birth date and time.");
      return;
    }
    const lat = parseFloat(latitude);
    const lng = parseFloat(longitude);
    if (Number.isNaN(lat) || lat < -90 || lat > 90) {
      setError("Latitude must be a number between -90 and 90.");
      return;
    }
    if (Number.isNaN(lng) || lng < -180 || lng > 180) {
      setError("Longitude must be a number between -180 and 180.");
      return;
    }

    const birthDatetimeUtc = `${birthDate}T${birthTime}Z`;

    const body = {
      birth_datetime_utc: birthDatetimeUtc,
      latitude: lat,
      longitude: lng,
      ayanamsa,
      house_system: houseSystem,
      node_type: nodeType,
      title: title || "Chart Analysis",
      subject_name: subjectName || "Unnamed",
      generated_by: "AstroOS Web Reports",
    };

    setGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/report/chart/pdf`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${tokenStore.getAccess() ?? ""}`,
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try {
          const errBody = await res.json();
          if (typeof errBody.detail === "string") detail = errBody.detail;
        } catch {
          /* ignore non-JSON error body */
        }
        throw new Error(detail);
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${title || "AstroOS_Report"}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate PDF report.");
    } finally {
      setGenerating(false);
    }
  }, [birthDate, birthTime, latitude, longitude, ayanamsa, houseSystem, nodeType, title, subjectName]);

  return (
    <div className="space-y-6">
      {/* ── Page Header ─────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4" style={{ borderColor: "var(--border-primary)" }}>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 font-bold shadow-inner">
            📄
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Printable PDF Reports
            </h1>
            <p className="text-xs text-slate-700 dark:text-slate-300 font-medium mt-0.5">
              Generate publication-grade PDF & HTML astrological reports with full Multi-Varga & Dasha breakdowns.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleFillSample}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-cyan-950/40 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-900/50 transition-all cursor-pointer shadow-sm self-start sm:self-auto"
        >
          <span>✨</span> Auto-fill Demo Sample Chart
        </button>
      </div>

      {/* ── Error Banner ────────────────────────────────────────────────────── */}
      {error && (
        <div className="p-4 rounded-xl border border-rose-500/40 bg-rose-950/30 text-rose-300 text-xs font-semibold flex items-center gap-2 shadow-sm">
          <span>⚠️</span> {error}
        </div>
      )}

      {/* ── Main Form Card ──────────────────────────────────────────────────── */}
      <div className="rounded-2xl border p-5 sm:p-6 shadow-xl space-y-6 backdrop-blur-sm" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <span>⚙️</span> Report Configuration & Birth Input
          </h2>
          <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-cyan-100 text-cyan-900 border border-cyan-600/40 dark:bg-cyan-950/50 dark:text-cyan-300">
            PDF & HTML Generator
          </span>
        </div>

        {/* 1. Saved Chart Select */}
        <div className="space-y-1.5">
          <label className="block text-xs font-bold text-slate-800 dark:text-slate-200">
            Select Saved Chart (or enter details manually)
          </label>
          {loadingCharts ? (
            <div className="text-xs text-slate-400 italic">Loading saved charts…</div>
          ) : (
            <select
              value={selectedChartId}
              onChange={(e) => handleChartSelect(e.target.value)}
              className="w-full rounded-xl border px-3 py-2 text-xs font-medium outline-none transition-all"
              style={{
                borderColor: "var(--border-primary)",
                background: "var(--bg-secondary)",
                color: "var(--text-primary)",
              }}
            >
              <option value="">-- Enter Birth Details Manually --</option>
              <option value="demo">★ Demo Sample: Arjun Sharma (New Delhi, India)</option>
              {savedCharts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.subject_name} · {new Date(c.birth_datetime_utc).toLocaleDateString()} · {c.place_name || "Unknown place"}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* 2. Grid Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="space-y-1">
            <label className="block text-xs font-bold text-slate-800 dark:text-slate-200">
              Subject Name
            </label>
            <input
              type="text"
              placeholder="e.g. Arjun Sharma"
              value={subjectName}
              onChange={(e) => setSubjectName(e.target.value)}
              className="w-full rounded-xl border px-3 py-2 text-xs outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-bold text-slate-800 dark:text-slate-200">
              Report Title
            </label>
            <input
              type="text"
              placeholder="e.g. Comprehensive Life Report"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-xl border px-3 py-2 text-xs outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-bold text-slate-800 dark:text-slate-200">
              Birth Date <span className="text-rose-400">*</span>
            </label>
            <input
              type="date"
              value={birthDate}
              onChange={(e) => setBirthDate(e.target.value)}
              className="w-full rounded-xl border px-3 py-2 text-xs outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-bold text-slate-800 dark:text-slate-200">
              Birth Time (UTC) <span className="text-rose-400">*</span>
            </label>
            <input
              type="time"
              value={birthTime}
              onChange={(e) => setBirthTime(e.target.value)}
              className="w-full rounded-xl border px-3 py-2 text-xs outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-bold text-slate-800 dark:text-slate-200">
              Latitude (-90 to 90)
            </label>
            <input
              type="number"
              step="any"
              placeholder="e.g. 28.6139"
              value={latitude}
              onChange={(e) => setLatitude(e.target.value)}
              className="w-full rounded-xl border px-3 py-2 text-xs outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-bold text-slate-800 dark:text-slate-200">
              Longitude (-180 to 180)
            </label>
            <input
              type="number"
              step="any"
              placeholder="e.g. 77.2090"
              value={longitude}
              onChange={(e) => setLongitude(e.target.value)}
              className="w-full rounded-xl border px-3 py-2 text-xs outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-bold text-slate-800 dark:text-slate-200">
              Ayanamsa
            </label>
            <select
              value={ayanamsa}
              onChange={(e) => setAyanamsa(e.target.value as AyanamsaCode)}
              className="w-full rounded-xl border px-3 py-2 text-xs outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            >
              {AYANAMSA_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-bold text-slate-800 dark:text-slate-200">
              House System
            </label>
            <select
              value={houseSystem}
              onChange={(e) => setHouseSystem(e.target.value as HouseSystemCode)}
              className="w-full rounded-xl border px-3 py-2 text-xs outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            >
              {HOUSE_SYSTEM_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-bold text-slate-800 dark:text-slate-200">
              Rahu/Ketu Node
            </label>
            <select
              value={nodeType}
              onChange={(e) => setNodeType(e.target.value as NodeTypeCode)}
              className="w-full rounded-xl border px-3 py-2 text-xs outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            >
              {NODE_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 3. Action Buttons */}
        <div className="pt-3 flex flex-wrap items-center gap-3 border-t" style={{ borderColor: "var(--border-primary)" }}>
          <button
            type="button"
            disabled={generating || loadingTemplates}
            onClick={handleGeneratePdf}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-xs font-extrabold bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white shadow-lg hover:shadow-cyan-500/25 transition-all cursor-pointer disabled:opacity-50"
          >
            <span>📥</span>
            {generating ? "Generating Printable PDF…" : "Download Printable PDF Report"}
          </button>
        </div>
      </div>

      {/* ── Available Templates Card ───────────────────────────────────────── */}
      <div className="rounded-2xl border p-5 sm:p-6 shadow-md space-y-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <span>📚</span> Active Report Templates Directory
        </h3>
        {loadingTemplates ? (
          <p className="text-xs text-slate-400 italic">Loading active template formats…</p>
        ) : templates.length === 0 ? (
          <p className="text-xs text-slate-400 italic">Default templates active (`horoscope.html`, `base.html`).</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {templates.map((t) => (
              <div key={t} className="p-3 rounded-xl border border-slate-700/50 bg-slate-900/60 text-xs flex items-center justify-between">
                <span className="font-semibold text-slate-200">{t}</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 border border-emerald-600/40 dark:bg-emerald-950/50 dark:text-emerald-300">
                  Active ✓
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
