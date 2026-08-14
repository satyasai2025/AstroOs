"use client";

import { useCallback, useEffect, useState } from "react";
import { Button, Card, Input, Select, type SelectOption } from "@/components/ui";
import { api } from "@/lib/api";
import { ResearchPatternsShell } from "@/components/research/ResearchPatternsShell";
import { useFullReport } from "@/lib/workflow";
import type { AyanamsaCode, HouseSystemCode, FullReportResponse } from "@/lib/types";
import { ChartPanel } from "@/components/workflow/panels/ChartPanel";
import { VargaPanel } from "@/components/workflow/panels/VargaPanel";
import { DashaPanel } from "@/components/workflow/panels/DashaPanel";
import { YogaPanel } from "@/components/workflow/panels/YogaPanel";
import { StrengthPanel } from "@/components/workflow/panels/StrengthPanel";
import { TransitPanel } from "@/components/workflow/panels/TransitPanel";
import { RulesPanel } from "@/components/workflow/panels/RulesPanel";
import { KnowledgePanel } from "@/components/workflow/panels/KnowledgePanel";
import { VerificationPanel } from "@/components/workflow/panels/VerificationPanel";
import { ReportPanel } from "@/components/workflow/panels/ReportPanel";
import { KPSnapshot } from "@/components/kp/KPSnapshot";
import { KPCuspMatrix } from "@/components/kp/KPCuspMatrix";
import { KPPlanetPortfolio } from "@/components/kp/KPPlanetPortfolio";
import { KPSignificatorMatrix } from "@/components/kp/KPSignificatorMatrix";
import { KPRulingPlanets } from "@/components/kp/KPRulingPlanets";
import { KPEventExplorer } from "@/components/kp/KPEventExplorer";
import { KPTimingEngine } from "@/components/kp/KPTimingEngine";
import { KPSpecialFactors } from "@/components/kp/KPSpecialFactors";
import { KPReasoningChain } from "@/components/kp/KPReasoningChain";

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

export default function ReportsFullPage() {
  // ── Form fields ──────────────────────────────────────────────────────────
  const [selectedChartId, setSelectedChartId] = useState<string>("");
  const [subjectName, setSubjectName] = useState("");
  const [title, setTitle] = useState("Complete Astrology Report");
  const [birthDate, setBirthDate] = useState("");
  const [birthTime, setBirthTime] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [ayanamsa, setAyanamsa] = useState<AyanamsaCode>("lahiri");
  const [houseSystem, setHouseSystem] = useState<HouseSystemCode>("W");
  const [includeKp, setIncludeKp] = useState(true);

  // ── Saved charts state ──────────────────────────────────────────────────
  const [savedCharts, setSavedCharts] = useState<any[]>([]);
  const [loadingCharts, setLoadingCharts] = useState(true);

  // ── API state ────────────────────────────────────────────────────────────
  const fullReport = useFullReport();
  const [result, setResult] = useState<FullReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load saved charts on mount
  const loadSavedCharts = useCallback(async () => {
    try {
      setLoadingCharts(true);
      const data = await api.get<{ charts: any[]; total: number }>("/api/v1/horoscope/my-charts?limit=50&offset=0");
      setSavedCharts(data.charts || []);
      if (data.charts && data.charts.length > 0) {
        populateFromChart(data.charts[0]);
      }
    } catch {
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

  // Submit: build the FullReportRequest and POST to /api/v1/report/full
  const handleGenerate = useCallback(async () => {
    setError(null);
    setResult(null);

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

    try {
      const resp = await fullReport.mutateAsync({
        birth_datetime_utc: birthDatetimeUtc,
        latitude: lat,
        longitude: lng,
        ayanamsa,
        house_system: houseSystem,
        dasha_system: "vimshottari",
        include_vargas: true,
        include_kp: includeKp,
        title: title || "Complete Astrology Report",
        subject_name: subjectName || "Unnamed",
        generated_by: "AstroOS Web Reports",
      });
      setResult(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate the full report.");
    }
  }, [birthDate, birthTime, latitude, longitude, ayanamsa, houseSystem, title, subjectName, includeKp, fullReport]);

  return (
    <ResearchPatternsShell
      title="Full Report"
      subtitle="Complete astrology report — the full analysis pipeline plus KP analysis on one printable page."
    >
      <div className="no-print" style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
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
            <label style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>
              <input
                type="checkbox"
                checked={includeKp}
                onChange={(e) => setIncludeKp(e.target.checked)}
              />
              Include KP Analysis
            </label>
          </div>
        </Card>

        {/* ── Actions ─────────────────────────────────────────────────────── */}
        <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "center", flexWrap: "wrap" }}>
          <Button
            variant="gold"
            size="lg"
            disabled={fullReport.isPending}
            onClick={handleGenerate}
          >
            {fullReport.isPending ? "Generating…" : "Generate Full Report"}
          </Button>
          {result && (
            <Button variant="ghost" size="lg" onClick={() => window.print()}>
              Print / Save as PDF
            </Button>
          )}
        </div>
      </div>

      {/* ── Report body (printable) ───────────────────────────────────────── */}
      {result && <FullReportBody report={result} />}
    </ResearchPatternsShell>
  );
}

/**
 * Renders the full report as a continuous scroll of the existing workflow
 * panels followed by the KP analysis panels — everything the frontend
 * already knows how to render, fed directly from the backend's composed
 * response. The interactive form carries the no-print class so only the
 * report content prints.
 */
function FullReportBody({ report }: { report: FullReportResponse }) {
  const kp = report.kp_analysis;

  return (
    <div className="print-area" style={{ marginTop: "var(--space-4)" }}>
      <div className="glass-card p-5" style={{ marginBottom: "var(--space-4)" }}>
        <h1 style={{ fontSize: "var(--text-xl)", fontWeight: "var(--weight-bold)", margin: 0 }}>
          {report.title}
        </h1>
        <p style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", marginTop: "var(--space-1)" }}>
          Subject: {report.subject_name} · Generated{" "}
          {new Date(report.generated_at).toUTCString()}
        </p>
      </div>

      <div className="space-y-4">
        <ChartPanel chart={report.chart} />
        <VargaPanel vargas={report.vargas} />
        <DashaPanel dasha={report.dasha} />
        <YogaPanel yogas={report.yogas} />
        <StrengthPanel shadbala={report.shadbala} ashtakavarga={report.ashtakavarga} />
        <TransitPanel transits={report.transits} />
        <RulesPanel ruleResults={report.rule_results} />
        <KnowledgePanel citations={report.knowledge_citations} />
        <VerificationPanel verification={report.verification} />
        <ReportPanel report={report.report} benchmark={report.benchmark} />

        {kp && (
          <>
            <div className="glass-card p-5">
              <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
                KP Analysis
              </h2>
            </div>
            <KPSnapshot
              cusps={kp.cusps}
              profiles={kp.planet_profiles}
              rulingPlanets={kp.ruling_planets}
              eventPromises={kp.event_promises}
              timing={kp.timing}
            />
            <KPCuspMatrix cusps={kp.cusps} />
            <KPPlanetPortfolio profiles={kp.planet_profiles} />
            <KPSignificatorMatrix houses={kp.house_significators} />
            <KPRulingPlanets rulingPlanets={kp.ruling_planets} houseSignificators={kp.house_significators} />
            <KPEventExplorer eventPromises={kp.event_promises} />
            <KPTimingEngine timing={kp.timing} />
            <KPSpecialFactors factors={kp.special_factors} />
            <KPReasoningChain evidence={kp.evidence} />
          </>
        )}
      </div>
    </div>
  );
}
