"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { api } from "@/lib/api";
import { useCurrentUser } from "@/lib/auth";
import { Badge, Button, Card, Icon } from "@/components/ui";

interface GeneratedReport {
  id: string;
  subject_name: string;
  report_tier: "free_2page" | "pro_5page" | "research_dossier";
  export_format: "pdf" | "html" | "json";
  page_count: number;
  file_size_bytes: number;
  download_url: string;
  created_at: string;
}

export default function ReportsHubPage() {
  const { data: user } = useCurrentUser();
  const [reports, setReports] = useState<GeneratedReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [generatingTier, setGeneratingTier] = useState<string | null>(null);
  const [subjectName, setSubjectName] = useState("Natal Chart Analysis");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadReports() {
      setLoading(true);
      try {
        const res = await api.get<{ items: GeneratedReport[]; total: number }>(
          "/api/v1/reports/tiered/history"
        );
        setReports(res.items);
      } catch (err) {
        console.error("Failed to load reports", err);
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, []);

  const handleGenerate = async (tier: "free_2page" | "pro_5page" | "research_dossier") => {
    setGeneratingTier(tier);
    setErrorMessage(null);
    try {
      const res = await api.post<GeneratedReport>("/api/v1/reports/tiered/generate", {
        subject_name: subjectName,
        report_tier: tier,
        export_format: "pdf",
      });
      setReports((prev) => [res, ...prev]);
      window.open(res.download_url, "_blank");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to generate report.");
    } finally {
      setGeneratingTier(null);
    }
  };

  return (
    <AppShell>
      <div className="min-h-screen bg-slate-950 text-slate-100 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* ── Header ── */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-0.5 text-xs font-semibold text-cyan-400">
                <span>📄</span>
                <span>Narrative PDF Reports Studio</span>
              </div>
              <h1 className="text-2xl sm:text-4xl font-extrabold text-white mt-2">
                Astrological Reports &amp; Downloads
              </h1>
              <p className="text-xs sm:text-sm text-slate-400 mt-1">
                Generate high-resolution printable PDF narrative dossiers with Swiss Ephemeris calculations.
              </p>
            </div>
          </div>

          {errorMessage && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3.5 text-xs text-red-400">
              {errorMessage}
            </div>
          )}

          {/* ── Subject Input Bar ── */}
          <Card className="p-4 border border-slate-800 bg-slate-900/60">
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <label className="text-xs font-bold text-slate-300 whitespace-nowrap">
                Report Subject Name:
              </label>
              <input
                type="text"
                value={subjectName}
                onChange={(e) => setSubjectName(e.target.value)}
                placeholder="e.g. Swami Vivekananda Natal Chart"
                className="w-full sm:max-w-md rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:border-cyan-400 focus:outline-none"
              />
            </div>
          </Card>

          {/* ── 3 Tiered Report Cards ── */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Tier 1: Free 2-Page */}
            <Card className="p-6 border border-slate-800 bg-slate-900/60 flex flex-col justify-between space-y-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="rounded bg-slate-800 px-2.5 py-0.5 text-[10px] font-bold text-slate-300">
                    Free Community
                  </span>
                  <span className="text-xs text-slate-400">2 Pages</span>
                </div>
                <h3 className="text-lg font-bold text-white">Essential Natal Summary</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Clear 2-page overview with high-precision planetary coordinates, Panchanga, Lagna, and Rashi placements.
                </p>
                <ul className="space-y-1.5 text-xs text-slate-300 pt-2 border-t border-slate-800">
                  <li className="flex items-center gap-1.5">✓ Planetary Longitudes Table</li>
                  <li className="flex items-center gap-1.5">✓ Natal Panchanga Attributes</li>
                  <li className="flex items-center gap-1.5">✓ 12 Bhava (House) Sign Placements</li>
                </ul>
              </div>
              <button
                onClick={() => handleGenerate("free_2page")}
                disabled={generatingTier !== null}
                className="w-full rounded-xl bg-slate-800 hover:bg-slate-750 py-2.5 text-xs font-bold text-white transition border border-slate-700"
              >
                {generatingTier === "free_2page" ? "Generating..." : "Generate 2-Page PDF"}
              </button>
            </Card>

            {/* Tier 2: Pro 5-Page */}
            <Card className="p-6 border border-cyan-500/50 bg-slate-900/80 flex flex-col justify-between space-y-6 shadow-lg shadow-cyan-500/5">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-2.5 py-0.5 text-[10px] font-bold">
                    PRO Plan
                  </span>
                  <span className="text-xs text-cyan-400 font-bold">5 Pages</span>
                </div>
                <h3 className="text-lg font-bold text-white">Comprehensive Practitioner Report</h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Full 5-page dossier including D1/D9 visual harmonics, complete D1-D60 divisionals, Vimshottari dasha, and Shadbala rupas.
                </p>
                <ul className="space-y-1.5 text-xs text-slate-300 pt-2 border-t border-slate-800">
                  <li className="flex items-center gap-1.5">✓ D1 Rashi &amp; D9 Navamsha Analysis</li>
                  <li className="flex items-center gap-1.5">✓ Shodashavarga (D2–D60) Tables</li>
                  <li className="flex items-center gap-1.5">✓ 120-Year Vimshottari Timeline</li>
                  <li className="flex items-center gap-1.5">✓ 6-Fold Shadbala Strengths</li>
                  <li className="flex items-center gap-1.5">✓ Active Planetary Yogas Analysis</li>
                </ul>
              </div>
              <button
                onClick={() => handleGenerate("pro_5page")}
                disabled={generatingTier !== null}
                className="w-full rounded-xl bg-cyan-500 hover:bg-cyan-400 py-2.5 text-xs font-bold text-slate-950 transition shadow"
              >
                {generatingTier === "pro_5page" ? "Generating..." : "Generate 5-Page PRO PDF"}
              </button>
            </Card>

            {/* Tier 3: Research Dossier */}
            <Card className="p-6 border border-purple-500/50 bg-slate-900/80 flex flex-col justify-between space-y-6 shadow-lg shadow-purple-500/5">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2.5 py-0.5 text-[10px] font-bold">
                    RESEARCH Scholar
                  </span>
                  <span className="text-xs text-purple-400 font-bold">8+ Pages</span>
                </div>
                <h3 className="text-lg font-bold text-white">Empirical Research Dossier</h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Exhaustive research dossier with statistical cohort correlations, Bayes probability distributions, and classical BPHS citations.
                </p>
                <ul className="space-y-1.5 text-xs text-slate-300 pt-2 border-t border-slate-800">
                  <li className="flex items-center gap-1.5">✓ AstroDSL Custom Rule Evaluation</li>
                  <li className="flex items-center gap-1.5">✓ n=10,000 Cohort Significance</li>
                  <li className="flex items-center gap-1.5">✓ Classical Shastra Citations (BPHS)</li>
                  <li className="flex items-center gap-1.5">✓ Complete Knowledge Graph RAG</li>
                </ul>
              </div>
              <button
                onClick={() => handleGenerate("research_dossier")}
                disabled={generatingTier !== null}
                className="w-full rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 py-2.5 text-xs font-bold text-white transition shadow"
              >
                {generatingTier === "research_dossier" ? "Generating..." : "Generate Research Dossier"}
              </button>
            </Card>
          </div>

          {/* ── Generated Reports History Table ── */}
          <div className="space-y-4 pt-4">
            <h2 className="text-lg font-bold text-white">Generated Report History</h2>
            <Card className="p-0 overflow-hidden border border-slate-800 bg-slate-900/60">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                      <th className="py-3 px-4 font-semibold">Date</th>
                      <th className="py-3 px-4 font-semibold">Subject</th>
                      <th className="py-3 px-4 font-semibold">Report Tier</th>
                      <th className="py-3 px-4 font-semibold">Pages</th>
                      <th className="py-3 px-4 font-semibold text-right">Download</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {reports.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-slate-500">
                          No reports generated yet. Click above to generate your first PDF report.
                        </td>
                      </tr>
                    ) : (
                      reports.map((r) => (
                        <tr key={r.id} className="hover:bg-slate-800/30 transition">
                          <td className="py-3 px-4 text-slate-400">
                            {new Date(r.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4 font-semibold text-white">
                            {r.subject_name}
                          </td>
                          <td className="py-3 px-4 uppercase font-bold text-[11px] text-cyan-400">
                            {r.report_tier.replace("_", " ")}
                          </td>
                          <td className="py-3 px-4 text-slate-300">
                            {r.page_count} Pages
                          </td>
                          <td className="py-3 px-4 text-right">
                            <a
                              href={r.download_url}
                              target="_blank"
                              rel="noreferrer"
                              className="font-bold text-cyan-400 hover:text-cyan-300 underline"
                            >
                              Download PDF
                            </a>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
