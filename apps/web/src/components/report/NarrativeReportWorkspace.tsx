"use client";

import { useState, useEffect } from "react";
import {
  generateNarrativeReport,
  generateComparativeNarrativeReport,
  exportReportDocument,
  type FullStructuredAstrologicalReportResponse,
} from "@/lib/narrativeReports";

interface Props {
  mode?: "single" | "comparative";
  chartData?: Record<string, unknown>;
  chartBData?: Record<string, unknown>;
  subjectName?: string;
  subjectBName?: string;
}

const SAMPLE_DEFAULT_CHART_A = {
  birth_datetime_utc: "2026-08-20T12:00:00Z",
  latitude: 28.6139,
  longitude: 77.2090,
  planets: [
    { planet: "Jupiter", house_number: 1, rashi: "Cancer", sidereal_longitude: 104.5 },
    { planet: "Moon", house_number: 11, rashi: "Taurus", nakshatra: "Rohini", sidereal_longitude: 45.2 },
    { planet: "Sun", house_number: 10, rashi: "Aries", sidereal_longitude: 15.8 },
    { planet: "Mercury", house_number: 10, rashi: "Aries", sidereal_longitude: 22.4 },
    { planet: "Mars", house_number: 7, rashi: "Capricorn", sidereal_longitude: 284.1 },
    { planet: "Venus", house_number: 9, rashi: "Pisces", sidereal_longitude: 348.0 },
    { planet: "Saturn", house_number: 4, rashi: "Libra", sidereal_longitude: 198.3 },
    { planet: "Rahu", house_number: 11, rashi: "Taurus", sidereal_longitude: 54.0 },
    { planet: "Ketu", house_number: 5, rashi: "Scorpio", sidereal_longitude: 234.0 },
  ],
  houses: [
    { house_number: 1, rashi: "Cancer", longitude: 95.0 },
    { house_number: 10, rashi: "Aries", longitude: 5.0 },
  ],
  vargas: {
    D9: {
      planets: [
        { planet: "Jupiter", rashi: "Cancer" },
        { planet: "Moon", rashi: "Taurus" },
      ],
    },
  },
  yogas: [
    { name: "Gajakesari Yoga", category: "Raja", source: "BPHS Ch. 36", strength: 0.9, description: "Jupiter in Kendra from Moon creates enduring wisdom." },
    { name: "Hamsa Yoga", category: "Mahapurusha", source: "Saravali Ch. 35", strength: 0.95, description: "Jupiter exalted in Kendra bestows leadership and integrity." },
  ],
};

const SAMPLE_DEFAULT_CHART_B = {
  birth_datetime_utc: "2026-08-20T12:00:00Z",
  latitude: 19.0760,
  longitude: 72.8777,
  planets: [
    { planet: "Moon", house_number: 9, rashi: "Virgo", nakshatra: "Hasta", sidereal_longitude: 165.0 },
    { planet: "Sun", house_number: 11, rashi: "Scorpio", sidereal_longitude: 225.0 },
    { planet: "Jupiter", house_number: 5, rashi: "Taurus", sidereal_longitude: 48.0 },
  ],
  houses: [
    { house_number: 1, rashi: "Capricorn", longitude: 275.0 },
  ],
};

export function NarrativeReportWorkspace({
  mode = "single",
  chartData,
  chartBData,
  subjectName = "Primary Native",
  subjectBName = "Partner / Event Snapshot",
}: Props) {
  const [report, setReport] = useState<FullStructuredAstrologicalReportResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSectionId, setActiveSectionId] = useState<string>("summary");
  const [exportingFormat, setExportingFormat] = useState<string | null>(null);

  useEffect(() => {
    async function loadReport() {
      try {
        setLoading(true);
        setError(null);
        let res: FullStructuredAstrologicalReportResponse;

        if (mode === "comparative") {
          res = await generateComparativeNarrativeReport({
            chart_a: chartData || SAMPLE_DEFAULT_CHART_A,
            chart_b: chartBData || SAMPLE_DEFAULT_CHART_B,
            chart_a_name: subjectName,
            chart_b_name: subjectBName,
          });
        } else {
          res = await generateNarrativeReport({
            chart: chartData || SAMPLE_DEFAULT_CHART_A,
            subject_name: subjectName,
            report_title: "AstroOS Comprehensive Astrological Synthesis",
          });
        }
        setReport(res);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to generate narrative report.");
      } finally {
        setLoading(false);
      }
    }
    loadReport();
  }, [mode, chartData, chartBData, subjectName, subjectBName]);

  const handleExport = async (format: "pdf" | "html" | "csv" | "json") => {
    if (!report) return;
    try {
      setExportingFormat(format);
      const res = await exportReportDocument({
        report: report as unknown as Record<string, unknown>,
        export_format: format,
      });

      if (format === "html" || format === "csv" || format === "json") {
        const blob = new Blob([res.content_base64_or_text], { type: res.mime_type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = res.filename;
        a.click();
        URL.revokeObjectURL(url);
      } else if (format === "pdf") {
        // Trigger browser printable window with pre-styled content
        const printWindow = window.open("", "_blank");
        if (printWindow) {
          const decodedHtml = atob(res.content_base64_or_text);
          printWindow.document.write(decodedHtml);
          printWindow.document.close();
          setTimeout(() => {
            printWindow.print();
          }, 500);
        }
      }
    } catch (err: unknown) {
      alert(`Export failed: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setExportingFormat(null);
    }
  };

  return (
    <div className="space-y-6" data-testid="narrative-report-workspace">
      {/* 1. Report Master Header & Action Toolbar */}
      <div className="p-6 rounded-2xl border glass-card border-zinc-800 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              {mode === "comparative" ? "COMPARATIVE SYNASTRY REPORT" : "STRUCTURED 9-SECTION REPORT"}
            </span>
            <span className="text-xs text-zinc-400">• Deterministic Synthesis</span>
          </div>
          <h1 className="text-2xl font-bold text-zinc-100 mt-2">
            {report?.report_title || "AstroOS Technical Astrological Report"}
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            Native: <strong className="text-zinc-200">{report?.subject_name || subjectName}</strong> • Generated: {report?.generated_at_iso || "Live"} • Swiss Ephemeris Standard
          </p>
        </div>

        {/* One-Click Export Toolbar */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => handleExport("pdf")}
            disabled={!report || exportingFormat !== null}
            data-testid="export-pdf-btn"
            className="px-3.5 py-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-xs font-semibold text-zinc-200 transition flex items-center gap-1.5 shadow-sm"
          >
            <span>📄</span> {exportingFormat === "pdf" ? "Exporting…" : "Export PDF"}
          </button>
          <button
            onClick={() => handleExport("html")}
            disabled={!report || exportingFormat !== null}
            data-testid="export-html-btn"
            className="px-3.5 py-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-xs font-semibold text-zinc-200 transition flex items-center gap-1.5 shadow-sm"
          >
            <span>🌐</span> {exportingFormat === "html" ? "Exporting…" : "Export HTML"}
          </button>
          <button
            onClick={() => handleExport("csv")}
            disabled={!report || exportingFormat !== null}
            data-testid="export-csv-btn"
            className="px-3.5 py-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-xs font-semibold text-zinc-200 transition flex items-center gap-1.5 shadow-sm"
          >
            <span>📊</span> {exportingFormat === "csv" ? "Exporting…" : "Export CSV"}
          </button>
          <button
            onClick={() => handleExport("json")}
            disabled={!report || exportingFormat !== null}
            data-testid="export-json-btn"
            className="px-3.5 py-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-xs font-semibold text-zinc-200 transition flex items-center gap-1.5 shadow-sm"
          >
            <span>💾</span> {exportingFormat === "json" ? "Exporting…" : "Export JSON"}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-xs text-zinc-400">Synthesizing 9-Section Narrative Astrological Report…</div>
      ) : error ? (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-300">{error}</div>
      ) : report ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Sticky Section Navigation */}
          <div className="lg:col-span-3 space-y-2">
            <div className="p-3 rounded-xl bg-zinc-900/80 border border-zinc-800 sticky top-4 space-y-1">
              <div className="text-[10px] uppercase font-bold text-zinc-400 px-2 py-1 tracking-wider">
                Report Sections ({report.sections.length})
              </div>
              {report.sections.map((sec) => (
                <button
                  key={sec.section_type}
                  onClick={() => {
                    setActiveSectionId(sec.section_type);
                    document.getElementById(`section-${sec.section_type}`)?.scrollIntoView({ behavior: "smooth" });
                  }}
                  className={`w-full text-left px-2.5 py-2 rounded-lg text-xs font-medium transition flex items-center justify-between ${
                    activeSectionId === sec.section_type
                      ? "bg-cyan-500 text-zinc-950 font-bold"
                      : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200"
                  }`}
                >
                  <span className="truncate">{sec.title}</span>
                  <span className="text-[10px] font-mono opacity-60">›</span>
                </button>
              ))}
            </div>
          </div>

          {/* Right Column: Master Report Flow */}
          <div className="lg:col-span-9 space-y-6">
            {/* Multi-Varga Dignity Matrix Card */}
            <div className="p-5 rounded-2xl border glass-card border-zinc-800 space-y-4">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                <div>
                  <h2 className="text-base font-bold text-zinc-100">Multi-Varga Dignity Spectrum</h2>
                  <p className="text-xs text-zinc-400">Rashi (D1), Navamsha (D9), Dashamsha (D10), and Saptamsha (D7)</p>
                </div>
                <span className="text-xs font-mono text-emerald-400 bg-emerald-950/40 px-2.5 py-1 rounded-full border border-emerald-500/30">
                  {report.multi_varga_matrix.filter((m) => m.is_vargottama).length} Vargottama Planets
                </span>
              </div>

              <div className="border rounded-xl overflow-hidden border-zinc-800 overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-zinc-900 text-zinc-400 border-b border-zinc-800 text-[10px] uppercase">
                    <tr>
                      <th className="p-2.5">Planet</th>
                      <th className="p-2.5">D1 Rashi</th>
                      <th className="p-2.5">D9 Navamsha</th>
                      <th className="p-2.5">D10 Dashamsha</th>
                      <th className="p-2.5">D7 Saptamsha</th>
                      <th className="p-2.5">Vargottama</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
                    {report.multi_varga_matrix.map((v) => (
                      <tr key={v.planet} className="hover:bg-zinc-900/40">
                        <td className="p-2.5 font-bold text-zinc-100">{v.planet}</td>
                        <td className="p-2.5 font-mono text-[11px]">{v.d1_rashi} ({v.d1_dignity})</td>
                        <td className="p-2.5 font-mono text-[11px]">{v.d9_rashi} ({v.d9_dignity})</td>
                        <td className="p-2.5 font-mono text-[11px]">{v.d10_rashi} ({v.d10_dignity})</td>
                        <td className="p-2.5 font-mono text-[11px]">{v.d7_rashi} ({v.d7_dignity})</td>
                        <td className="p-2.5">
                          {v.is_vargottama ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              VARGOTTAMA
                            </span>
                          ) : (
                            <span className="text-zinc-400 text-[11px]">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Comparative Findings Card (if available) */}
            {report.comparative_analysis && (
              <div className="p-5 rounded-2xl border glass-card border-violet-500/30 bg-violet-950/20 space-y-4" data-testid="comparative-analysis-panel">
                <div className="flex items-center justify-between border-b border-violet-500/30 pb-3">
                  <div>
                    <span className="text-[10px] font-mono text-violet-400 uppercase font-bold">SYNASTRY &amp; COMPARATIVE METRICS</span>
                    <h2 className="text-base font-bold text-zinc-100">
                      {report.comparative_analysis.chart_a_name} vs {report.comparative_analysis.chart_b_name}
                    </h2>
                  </div>
                  {report.comparative_analysis.ashtakoota_guna_score && (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-violet-500/20 text-violet-300 border border-violet-500/30 font-mono">
                      Guna Score: {report.comparative_analysis.ashtakoota_guna_score} / 36.0
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-zinc-900/80 border border-zinc-800 space-y-1">
                    <span className="text-[10px] uppercase text-zinc-400">Lagna Axis Relationship</span>
                    <div className="font-semibold text-zinc-200">{report.comparative_analysis.lagna_relationship}</div>
                  </div>
                  <div className="p-3 rounded-xl bg-zinc-900/80 border border-zinc-800 space-y-1">
                    <span className="text-[10px] uppercase text-zinc-400">Lunar Axis Relationship</span>
                    <div className="font-semibold text-zinc-200">{report.comparative_analysis.moon_relationship}</div>
                  </div>
                </div>

                <p className="text-xs text-zinc-300 leading-relaxed font-medium">
                  {report.comparative_analysis.comparative_summary}
                </p>
              </div>
            )}

            {/* Render 9 Standardized Report Sections */}
            {report.sections.map((sec) => (
              <div
                key={sec.section_type}
                id={`section-${sec.section_type}`}
                className="p-5 rounded-2xl border glass-card border-zinc-800 space-y-4"
              >
                <div className="border-b border-zinc-800 pb-3">
                  <h2 className="text-base font-bold text-zinc-100">{sec.title}</h2>
                  <p className="text-xs text-zinc-400">{sec.subtitle}</p>
                </div>

                {/* Narrative Paragraphs */}
                <div className="space-y-4 text-xs text-zinc-300 leading-relaxed">
                  {sec.paragraphs.map((p, idx) => (
                    <div key={idx} className="space-y-1.5 bg-zinc-900/40 p-3.5 rounded-xl border border-zinc-800/60">
                      <h2 className="text-xs font-bold text-cyan-300">{p.heading}</h2>
                      <p className="text-zinc-300 leading-relaxed">{p.content_text}</p>
                      {p.referenced_evidence_ids.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 pt-1.5">
                          <span className="text-[10px] text-zinc-400">Referenced Evidence:</span>
                          {p.referenced_evidence_ids.map((id) => (
                            <span
                              key={id}
                              className="font-mono text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-cyan-400 border border-zinc-700"
                            >
                              {id}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Technical Evidence Table */}
                {sec.evidence_table.length > 0 && (
                  <div className="space-y-2 pt-2">
                    <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">
                      Technical Evidence Data Items ({sec.evidence_table.length})
                    </div>
                    <div className="border rounded-xl overflow-hidden border-zinc-800/80 overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-zinc-900/90 text-zinc-400 border-b border-zinc-800 text-[10px] uppercase">
                          <tr>
                            <th className="p-2">Evidence ID</th>
                            <th className="p-2">Category</th>
                            <th className="p-2">Parameter</th>
                            <th className="p-2">Computed Value</th>
                            <th className="p-2">Classical Source</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
                          {sec.evidence_table.map((e) => (
                            <tr key={e.evidence_id} className="hover:bg-zinc-900/40">
                              <td className="p-2 font-mono text-[11px] text-cyan-400 font-semibold">{e.evidence_id}</td>
                              <td className="p-2 text-zinc-400 text-[11px]">{e.category}</td>
                              <td className="p-2 font-medium text-zinc-200">{e.parameter_name}</td>
                              <td className="p-2 text-zinc-300 font-mono text-[11px]">{e.computed_value}</td>
                              <td className="p-2 text-zinc-400 text-[11px]">{e.classical_reference || "-"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
