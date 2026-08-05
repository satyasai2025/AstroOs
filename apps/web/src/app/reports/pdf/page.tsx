"use client";

import { useCallback, useEffect, useState } from "react";
import { Button, Card, Input, Select, type SelectOption } from "@/components/ui";
import { api, tokenStore } from "@/lib/api";
import { ResearchPatternsShell } from "@/components/research/ResearchPatternsShell";
import type { AyanamsaCode, HouseSystemCode } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

const AYANAMSA_OPTIONS: SelectOption[] = [
  { value: "lahiri", label: "Lahiri (default)" },
  { value: "kp", label: "Krishnamitra (KP)" },
  { value: "raman", label: "Raman" },
  { value: "yukteshwar", label: "Yukteshwar" },
  { value: "fagan_bradley", label: "Fagan/Bradley" },
  { value: "true_chitra", label: "True Chitra" },
];

const HOUSE_SYSTEM_OPTIONS: SelectOption[] = [
  { value: "W", label: "W — Whole Sign" },
  { value: "P", label: "P — Placidus" },
  { value: "K", label: "K — Koch" },
  { value: "E", label: "E — Equal" },
];

export default function ReportsPdfPage() {
  // ── Form fields ──────────────────────────────────────────────────────────
  const [selectedChartId, setSelectedChartId] = useState<string>("");
  const [subjectName, setSubjectName] = useState("");
  const [title, setTitle] = useState("AstroOS Chart Report");
  const [birthDate, setBirthDate] = useState("");
  const [birthTime, setBirthTime] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [ayanamsa, setAyanamsa] = useState<AyanamsaCode>("lahiri");
  const [houseSystem, setHouseSystem] = useState<HouseSystemCode>("W");

  // ── Saved charts state ──────────────────────────────────────────────────
  const [savedCharts, setSavedCharts] = useState<any[]>([]);
  const [loadingCharts, setLoadingCharts] = useState(true);

  // ── API state ────────────────────────────────────────────────────────────
  const [templates, setTemplates] = useState<string[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load available report templates on mount (GET /api/v1/report/templates)
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
      // Auto-select first chart if available
      if (data.charts && data.charts.length > 0) {
        const firstChart = data.charts[0];
        setSelectedChartId(firstChart.id);
        populateFromChart(firstChart);
      }
    } catch (err) {
      // User might not be logged in - that's okay
      setSavedCharts([]);
    } finally {
      setLoadingCharts(false);
    }
  }, []);

  useEffect(() => {
    void loadSavedCharts();
  }, [loadSavedCharts]);

  // Populate form fields from a saved chart
  const populateFromChart = (chart: any) => {
    setSubjectName(chart.subject_name || "");
    const birthDt = new Date(chart.birth_datetime_utc);
    setBirthDate(birthDt.toISOString().split("T")[0]);
    setBirthTime(birthDt.toISOString().split("T")[1].slice(0, 5));
    setLatitude(chart.birth_latitude?.toString() || "");
    setLongitude(chart.birth_longitude?.toString() || "");
    setAyanamsa((chart.ayanamsa as AyanamsaCode) || "lahiri");
    setHouseSystem((chart.house_system as HouseSystemCode) || "W");
  };

  // Handle saved chart selection
  const handleChartSelect = useCallback((chartId: string) => {
    setSelectedChartId(chartId);
    const chart = savedCharts.find((c) => c.id === chartId);
    if (chart) {
      populateFromChart(chart);
    }
  }, [savedCharts]);

  // Submit: build the ChartReportRequest and POST to /api/v1/report/chart/pdf.
  // The endpoint returns binary PDF (application/pdf), so we use a raw fetch
  // with the bearer token from tokenStore rather than api.post (which
  // JSON-parses the body).
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

    // The API field is birth_datetime_utc — we treat the entered local time
    // as UTC (the user is responsible for offsetting beforehand). It must be
    // timezone-aware, so we append the "Z" suffix.
    const birthDatetimeUtc = `${birthDate}T${birthTime}Z`;

    const body = {
      birth_datetime_utc: birthDatetimeUtc,
      latitude: lat,
      longitude: lng,
      ayanamsa,
      house_system: houseSystem,
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
      a.download = `${title || "report"}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate PDF report.");
    } finally {
      setGenerating(false);
    }
  }, [birthDate, birthTime, latitude, longitude, ayanamsa, houseSystem, title, subjectName]);

  return (
    <ResearchPatternsShell
      title="Reports"
      subtitle="Generate printable chart reports as PDF."
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        {error && (
          <Card glow="gold">
            <p style={{ color: "var(--danger-400)", margin: 0 }}>{error}</p>
          </Card>
        )}

        {/* ── Birth data form ────────────────────────────────────────────── */}
        <Card padding="var(--space-4)">
          <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
            Birth Data
          </h2>
          <div style={{ marginBottom: "var(--space-4)" }}>
            <label style={{ display: "block", fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)", marginBottom: "var(--space-2)", color: "var(--text-secondary)" }}>
              Load from Saved Chart
            </label>
            {loadingCharts ? (
              <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Loading saved charts…</span>
            ) : savedCharts.length > 0 ? (
              <Select
                value={selectedChartId}
                onChange={handleChartSelect}
                options={savedCharts.map((c) => ({
                  value: c.id,
                  label: `${c.subject_name} · ${new Date(c.birth_datetime_utc).toLocaleDateString()} · ${c.place_name || "Unknown place"}`,
                }))}
                placeholder="Select a saved chart…"
              />
            ) : (
              <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                No saved charts found. Enter birth details manually below or save a chart first from the Dashboard.
              </span>
            )}
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "var(--space-3)",
            }}
          >
            <Input
              label="Subject Name"
              placeholder="e.g. Alex"
              value={subjectName}
              onChange={setSubjectName}
            />
            <Input
              label="Report Title"
              placeholder="e.g. Career Analysis"
              value={title}
              onChange={setTitle}
            />
            <Input
              label="Birth Date"
              type="date"
              value={birthDate}
              onChange={setBirthDate}
              required
            />
            <Input
              label="Birth Time (UTC)"
              type="time"
              value={birthTime}
              onChange={setBirthTime}
              required
            />
            <Input
              label="Latitude"
              type="number"
              placeholder="e.g. 28.6139"
              value={latitude}
              onChange={setLatitude}
              hint="Between -90 and 90"
            />
            <Input
              label="Longitude"
              type="number"
              placeholder="e.g. 77.2090"
              value={longitude}
              onChange={setLongitude}
              hint="Between -180 and 180"
            />
            <div style={{ width: "100%" }}>
              <Select
                label="Ayanamsa"
                options={AYANAMSA_OPTIONS}
                value={ayanamsa}
                onChange={(v) => setAyanamsa(v as AyanamsaCode)}
              />
            </div>
            <div style={{ width: "100%" }}>
              <Select
                label="House System"
                options={HOUSE_SYSTEM_OPTIONS}
                value={houseSystem}
                onChange={(v) => setHouseSystem(v as HouseSystemCode)}
              />
            </div>
          </div>
        </Card>

        {/* ── Actions ─────────────────────────────────────────────────────── */}
        <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "center" }}>
          <Button
            variant="gold"
            size="lg"
            disabled={generating || loadingTemplates}
            onClick={handleGeneratePdf}
          >
            {generating ? "Generating…" : "Download PDF Report"}
          </Button>
        </div>

        {/* ── Available templates (informational) ─────────────────────────── */}
        <Card padding="var(--space-4)">
          <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
            Available Report Templates
          </h2>
          {loadingTemplates ? (
            <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>Loading templates…</p>
          ) : templates.length === 0 ? (
            <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>No templates found.</p>
          ) : (
            <ul style={{ margin: 0, paddingLeft: 20, fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>
              {templates.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </ResearchPatternsShell>
  );
}
