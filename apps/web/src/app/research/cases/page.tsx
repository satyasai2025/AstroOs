"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import Link from "next/link";
import { Badge, Button, Card, KpiCard, ResizablePanels, SearchInput, Select, Table, TreeView, type SelectOption, type TableColumn, type TreeNode } from "@/components/ui";
import { AppShell } from "@/components/layout/AppShell";
import { researchCasesApi } from "@/lib/researchCases";
import { formatEventTitle } from "@/lib/astro";
import { useEventTypeTree, useUpdateEventType, type EventTypeNode } from "@/lib/research";
import type { LifeEventDetail, ResearchCaseDetail, ResearchCaseSummary, ResearchCaseBatchImport, ResearchCaseBatchValidation, ResearchCaseImportResponse, ResearchCasePayload } from "@/lib/types";
import { EventDetailBody, EventTimelineChart } from "@/components/research/EventTimelineChart";
import { LifeEventCard } from "@/components/research/LifeEventCard";
import { GuidedHelpTour, type TourStep } from "@/components/ui/GuidedHelpTour";

const CASE_DATABANK_TOUR_STEPS: TourStep[] = [
  {
    targetSelector: '[data-tour="case-import"]',
    title: "Step 1 of 4: Import Case Dataset",
    description: "Use the Bulk Import wizard to upload CSV case datasets (Rodden Rating AA verified charts with natal coordinates and life events).",
    actionText: "Click '📤 Bulk Import' to open the import wizard.",
  },
  {
    targetSelector: '[data-tour="case-blocks"]',
    title: "Step 2 of 4: Chart & Case Block Workspace",
    description: "Dock and view interactive life event timelines, planetary positions (D1, D9, D10), and KP horary snapshots inline in the VS Code-style studio.",
    actionText: "Select any case from the navigator to view details.",
  },
  {
    targetSelector: '[data-tour="case-filters"]',
    title: "Step 3 of 4: Master Dataset Filters",
    description: "Search across 8,000+ verified research cases, filter by verification status, and organize dataset collections.",
    actionText: "Use search and filters to query the databank.",
  },
  {
    targetSelector: '[data-tour="case-finish"]',
    title: "Step 4 of 4 (Submit): Finish & Export Findings",
    description: "Export research datasets, tag event categories, or jump directly into the Pattern Discovery Studio to mine empirical rules.",
    actionText: "Click '✨ Pattern Discovery' to analyze mined patterns.",
  },
];

// ── Inline Sub-Tool Panel 1: Bulk Import ──
function InlineBulkImportPanel({ onClose }: { onClose: () => void }) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [step, setStep] = useState<"upload" | "map" | "preview" | "import">("upload");
  const [fileName, setFileName] = useState<string | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [rows, setRows] = useState<string[][]>([]);
  const [mapping, setMapping] = useState<Record<string, string | null>>({});
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    setFileName(file.name);
    try {
      const text = await file.text();
      const lines = text.replace(/\r\n/g, "\n").split("\n").filter((l) => l.trim());
      if (lines.length === 0) throw new Error("CSV file is empty.");
      const h = lines[0].split(",").map((s) => s.trim().replace(/^"|"$/g, ""));
      setHeaders(h);
      setRows(lines.slice(1).map((l) => l.split(",").map((s) => s.trim().replace(/^"|"$/g, ""))));
      setStep("map");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to parse CSV.");
    }
  };

  return (
    <div className="p-4 bg-white dark:bg-slate-900 border border-cyan-500/30 rounded-xl shadow-lg space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
        <h3 className="font-extrabold text-cyan-600 dark:text-cyan-400 uppercase tracking-wide flex items-center gap-2">
          <span>📤 Bulk Case Import Wizard</span>
          {fileName && <span className="text-[11px] text-slate-500">({fileName})</span>}
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 font-bold px-2 py-0.5 text-xs rounded bg-slate-100 dark:bg-slate-800"
        >
          ✕ Close Panel
        </button>
      </div>

      {error && <p className="text-rose-500 font-bold">{error}</p>}

      {step === "upload" && (
        <div
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-cyan-500 p-6 rounded-xl text-center cursor-pointer transition"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleFile(file);
            }}
          />
          <p className="text-sm font-bold text-slate-700 dark:text-slate-300">Drag &amp; Drop CSV File or Click to Browse</p>
          <p className="text-[10px] text-slate-500 mt-1">Supports name, gender, dob, tob, place, latitude, longitude columns</p>
        </div>
      )}

      {step === "map" && (
        <div className="space-y-3">
          <p className="text-slate-700 dark:text-slate-300 font-bold">Detected {rows.length} rows. Confirm CSV column mapping:</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {["name", "gender", "dob", "place", "latitude", "longitude"].map((f) => (
              <div key={f} className="p-2 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                <span className="block text-[10px] uppercase font-bold text-slate-500">{f}</span>
                <select
                  value={mapping[f] ?? ""}
                  onChange={(e) => setMapping((prev) => ({ ...prev, [f]: e.target.value || null }))}
                  className="w-full text-xs bg-transparent border-none outline-none font-bold text-slate-900 dark:text-slate-100"
                >
                  <option value="">— unmapped —</option>
                  {headers.map((h) => (
                    <option key={h} value={h}>{h}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="secondary" onClick={() => setStep("upload")}>Reset</Button>
            <Button size="sm" variant="primary" onClick={() => setStep("import")}>Import {rows.length} Cases</Button>
          </div>
        </div>
      )}

      {step === "import" && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-center space-y-2">
          <p className="font-bold text-sm">🎉 Ready to import {rows.length} cases to Research Databank!</p>
          <div className="flex justify-center gap-2 pt-1">
            <Link href="/research/cases/bulk-import" className="px-3 py-1 bg-cyan-500 text-white rounded font-bold text-xs">
              Open Full Import Wizard ↗
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Inline Sub-Tool Panel 2: Event Types ──
function InlineEventTypesPanel({ onClose }: { onClose: () => void }) {
  const { data, isLoading } = useEventTypeTree();
  const [search, setSearch] = useState("");
  const eventTypes = data?.event_types ?? [];

  return (
    <div className="p-4 bg-white dark:bg-slate-900 border border-cyan-500/30 rounded-xl shadow-lg space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
        <h3 className="font-extrabold text-cyan-600 dark:text-cyan-400 uppercase tracking-wide flex items-center gap-2">
          <span>🏷️ Event Types Taxonomy Studio</span>
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 font-bold px-2 py-0.5 text-xs rounded bg-slate-100 dark:bg-slate-800"
        >
          ✕ Close Panel
        </button>
      </div>

      <div className="flex items-center justify-between gap-3">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍 Filter taxonomy (e.g. Marriage, Promotion, Accident)..."
          className="w-full rounded-lg px-3 py-1.5 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 outline-none"
        />
        <Link href="/research/event-types" className="shrink-0 text-cyan-600 dark:text-cyan-400 font-bold hover:underline">
          Full Taxonomy ↗
        </Link>
      </div>

      {isLoading ? (
        <p className="text-slate-400 text-center py-4">Loading taxonomy tree...</p>
      ) : (
        <div className="max-h-48 overflow-y-auto custom-scrollbar p-2 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
          {eventTypes.slice(0, 8).map((et) => (
            <div key={et.id} className="flex items-center justify-between p-1.5 rounded hover:bg-slate-200 dark:hover:bg-slate-800">
              <span className="font-bold text-slate-900 dark:text-slate-100">{et.name}</span>
              <span className="text-[10px] text-slate-400">{et.path}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Inline Sub-Tool Panel 3: Datasets ──
function InlineDatasetsPanel({ onClose }: { onClose: () => void }) {
  const DATASETS = [
    { id: "ds-1", name: "Marriage Timing Dataset", charts: 12431, size: "1.2 GB", status: "ready" },
    { id: "ds-2", name: "Career Success Cohort", charts: 8320, size: "740 MB", status: "ready" },
    { id: "ds-3", name: "Sade Sati Life Events", charts: 4110, size: "410 MB", status: "processing" },
  ];

  return (
    <div className="p-4 bg-white dark:bg-slate-900 border border-cyan-500/30 rounded-xl shadow-lg space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
        <h3 className="font-extrabold text-cyan-600 dark:text-cyan-400 uppercase tracking-wide flex items-center gap-2">
          <span>🗄️ Research Datasets Catalog</span>
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 font-bold px-2 py-0.5 text-xs rounded bg-slate-100 dark:bg-slate-800"
        >
          ✕ Close Panel
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-500 uppercase">
              <th className="py-1 px-2">Dataset</th>
              <th className="py-1 px-2">Charts</th>
              <th className="py-1 px-2">Size</th>
              <th className="py-1 px-2">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {DATASETS.map((d) => (
              <tr key={d.id}>
                <td className="py-2 px-2 font-bold text-slate-900 dark:text-slate-100">{d.name}</td>
                <td className="py-2 px-2 text-slate-600 dark:text-slate-400">{d.charts.toLocaleString()}</td>
                <td className="py-2 px-2 text-slate-600 dark:text-slate-400">{d.size}</td>
                <td className="py-2 px-2 font-bold text-emerald-600 dark:text-emerald-400">{d.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="text-right pt-1">
        <Link href="/research/datasets" className="text-cyan-600 dark:text-cyan-400 font-bold hover:underline">
          Manage All Datasets ↗
        </Link>
      </div>
    </div>
  );
}

// ── Inline Sub-Tool Panel 4: Life Events Verification Queue ──
function InlineEventsPanel({ onClose }: { onClose: () => void }) {
  const EVENTS = [
    { id: "ev-1", chartSubject: "Ravi Kumar", eventTitle: "Marriage", eventDate: "2019-11-14", ruleMatched: "7th Lord conjunct Venus" },
    { id: "ev-2", chartSubject: "Priya Sharma", eventTitle: "Career Promotion", eventDate: "2022-03-02", ruleMatched: "10th Lord in Kendra" },
  ];

  return (
    <div className="p-4 bg-white dark:bg-slate-900 border border-cyan-500/30 rounded-xl shadow-lg space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
        <h3 className="font-extrabold text-cyan-600 dark:text-cyan-400 uppercase tracking-wide flex items-center gap-2">
          <span>📅 Life Events Verification Queue</span>
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 font-bold px-2 py-0.5 text-xs rounded bg-slate-100 dark:bg-slate-800"
        >
          ✕ Close Panel
        </button>
      </div>

      <div className="space-y-2">
        {EVENTS.map((e) => (
          <div key={e.id} className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <div>
              <p className="font-bold text-slate-900 dark:text-slate-100">{e.chartSubject} · {e.eventTitle}</p>
              <p className="text-[10px] text-slate-500">{e.eventDate} · {e.ruleMatched}</p>
            </div>
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold text-[10px]">Verified</span>
          </div>
        ))}
      </div>
      <div className="text-right pt-1">
        <Link href="/research/events" className="text-cyan-600 dark:text-cyan-400 font-bold hover:underline">
          Full Events Queue ↗
        </Link>
      </div>
    </div>
  );
}

export default function ResearchCasesListPage() {
  const [cases, setCases] = useState<ResearchCaseSummary[]>([]);
  const [totalCases, setTotalCases] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<ResearchCaseDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [selectedEvent, setSelectedEvent] = useState<LifeEventDetail | null>(null);

  // Studio Dockable Active Tool State
  const [activeTool, setActiveTool] = useState<"bulk-import" | "event-types" | "datasets" | "events" | null>(null);
  const [isTourOpen, setIsTourOpen] = useState(false);

  // Debounced server-side search — with 8,000+ cases now imported, the
  // backend only ever returns one page (default 200) so client-side
  // filtering over that page alone would silently miss almost everything
  // outside it. This mirrors what the backend's `total` count fix is
  // for: the case list badge previously showed len(page) (always <=200)
  // instead of the real total, which is what looked "fake" once the
  // count stopped matching the actual imported number.
  useEffect(() => {
    setLoading(true);
    const handle = setTimeout(() => {
      researchCasesApi
        .list({ search: searchTerm.trim() || undefined, limit: 200 })
        .then((data) => {
          setCases(data.cases);
          setTotalCases(data.total);
          if (data.cases.length > 0 && !selectedCaseId) {
            setSelectedCaseId(data.cases[0].research_case_id);
          }
        })
        .catch((err) => setError(err instanceof Error ? err.message : "Failed to load research cases."))
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(handle);
  }, [searchTerm]);

  useEffect(() => {
    if (!selectedCaseId) return;
    let cancelled = false;
    setDetailLoading(true);
    setSelectedEvent(null);
    researchCasesApi
      .getDetail(selectedCaseId)
      .then((detailData) => {
        if (!cancelled) {
          setSelectedDetail(detailData);
          if (detailData.life_events && detailData.life_events.length > 0) {
            setSelectedEvent(detailData.life_events[0]);
          }
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSelectedDetail(null);
          setSelectedEvent(null);
        }
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedCaseId]);

  // Search now happens server-side (see the debounced effect above, which
  // re-fetches on searchTerm change) — only status stays a client-side
  // filter over the current page, since it's a cheap enum check.
  const filteredCases = cases.filter((c) => {
    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "passed" && c.validation_status === "passed") ||
      (statusFilter === "pending" && c.validation_status !== "passed");

    return matchesStatus;
  });

  return (
    <AppShell sectionColor="--section-research">
      <div className="space-y-3 pb-6">
        {/* ── Top Header ── */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-200 dark:border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">🧪</span>
              <h1 className="text-xl font-extrabold text-slate-900 dark:text-slate-100">
                Research Case Databank Studio
              </h1>
            </div>
            <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400 font-mono">
              Explore verified research cases, analyze interactive life event timelines, and inspect planetary snapshots inline.
            </p>
          </div>

          {/* IDE Action Tool Tabs */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={() => setIsTourOpen(true)}
              className="px-2.5 py-1 rounded-lg text-xs font-bold font-mono transition cursor-pointer flex items-center gap-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30"
            >
              <span>❓ Guided Tour</span>
            </button>

            <button
              type="button"
              data-tour="case-import"
              onClick={() => setActiveTool((prev) => (prev === "bulk-import" ? null : "bulk-import"))}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold font-mono transition cursor-pointer flex items-center gap-1.5 ${
                activeTool === "bulk-import"
                  ? "bg-cyan-500 text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              <span>📤 Bulk Import</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTool((prev) => (prev === "event-types" ? null : "event-types"))}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold font-mono transition cursor-pointer flex items-center gap-1.5 ${
                activeTool === "event-types"
                  ? "bg-cyan-500 text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              <span>🏷️ Event Types</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTool((prev) => (prev === "datasets" ? null : "datasets"))}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold font-mono transition cursor-pointer flex items-center gap-1.5 ${
                activeTool === "datasets"
                  ? "bg-cyan-500 text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              <span>🗄️ Datasets</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTool((prev) => (prev === "events" ? null : "events"))}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold font-mono transition cursor-pointer flex items-center gap-1.5 ${
                activeTool === "events"
                  ? "bg-cyan-500 text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              <span>📅 Life Events</span>
            </button>

            <span data-tour="case-finish">
              <Button href="/research/patterns" variant="primary" size="sm">
                ✨ Pattern Discovery
              </Button>
            </span>
          </div>
        </div>

        {/* ── Dockable Resizable Tool Block ── */}
        {activeTool === "bulk-import" && <InlineBulkImportPanel onClose={() => setActiveTool(null)} />}
        {activeTool === "event-types" && <InlineEventTypesPanel onClose={() => setActiveTool(null)} />}
        {activeTool === "datasets" && <InlineDatasetsPanel onClose={() => setActiveTool(null)} />}
        {activeTool === "events" && <InlineEventsPanel onClose={() => setActiveTool(null)} />}

        {error && (
          <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/40 text-xs text-rose-700 dark:text-rose-300 font-mono">
            {error}
          </div>
        )}

        {/* ── IDE 3-Pane Resizable Workspace (NO POPUPS) ── */}
        <ResizablePanels data-tour="case-blocks" defaultSizes={[0.26, 0.44, 0.30]} className="min-h-[640px]">
          {/* PANE 1: Case Navigator (Left) */}
          <div data-tour="case-filters" className="flex flex-col gap-3 pr-2 h-full">
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-2.5">
              {/* Search */}
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="🔍 Search name or ID..."
                className="w-full rounded-lg px-3 py-1.5 text-xs bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 outline-none focus:border-cyan-500 transition"
              />

              {/* Filters */}
              <div className="flex items-center justify-between text-[11px] font-mono">
                <div className="flex gap-1">
                  {(["all", "passed", "pending"] as const).map((st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => setStatusFilter(st)}
                      className={`px-2 py-0.5 rounded font-bold uppercase tracking-wider transition cursor-pointer ${
                        statusFilter === st
                          ? "bg-cyan-500 text-white"
                          : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
                <span className="text-slate-500 dark:text-slate-400 font-bold">
                  {totalCases.toLocaleString()}
                </span>
              </div>
              {totalCases > cases.length && (
                <p className="text-[10px] text-slate-400">
                  Showing {cases.length.toLocaleString()} of {totalCases.toLocaleString()} — search to narrow.
                </p>
              )}
            </div>

            {/* Cases List */}
            <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar max-h-[600px]">
              {loading ? (
                <div className="p-6 text-center text-xs text-slate-400 font-mono">
                  Loading cases…
                </div>
              ) : filteredCases.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500 dark:text-slate-400 font-mono">
                  No cases found.
                </div>
              ) : (
                filteredCases.map((c) => {
                  const isSelected = selectedCaseId === c.research_case_id;
                  return (
                    <div
                      key={c.research_case_id}
                      onClick={() => setSelectedCaseId(c.research_case_id)}
                      className={`p-3 rounded-xl border transition cursor-pointer ${
                        isSelected
                          ? "bg-cyan-500/10 dark:bg-cyan-950/60 border-cyan-500 text-slate-900 dark:text-slate-100 shadow-sm"
                          : "bg-white dark:bg-slate-900/90 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:border-slate-400 dark:hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <h4 className="text-xs font-extrabold text-slate-900 dark:text-slate-100 truncate">
                          {c.person_name || c.research_case_id}
                        </h4>
                        <Badge
                          tone={c.validation_status === "passed" ? "cyan" : "neutral"}
                          className="text-[10px] uppercase font-mono shrink-0"
                        >
                          {c.validation_status}
                        </Badge>
                      </div>

                      <div className="mt-1.5 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                        <span>Born: {c.dob || "—"}</span>
                        <span>{c.total_events} events</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* PANE 2: Timeline & Events List (Middle) */}
          <div className="px-2 h-full flex flex-col space-y-3">
            {detailLoading ? (
              <div className="h-full min-h-[400px] flex items-center justify-center p-8 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-400 font-mono">
                Loading case timeline details…
              </div>
            ) : selectedDetail ? (
              <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm space-y-4 flex-1 overflow-y-auto custom-scrollbar">
                {/* Case Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
                  <div>
                    <h2 className="text-sm font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                      <span>👤 {selectedDetail.person_name || selectedDetail.research_case_id}</span>
                      <span className="text-[11px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 font-mono font-bold">
                        {selectedDetail.research_case_id}
                      </span>
                    </h2>
                    <p className="mt-0.5 text-[11px] text-slate-600 dark:text-slate-400 font-mono">
                      Born: {selectedDetail.dob} {selectedDetail.gender ? `· ${selectedDetail.gender}` : ""} · Verified Events: {selectedDetail.life_events.length}
                    </p>
                  </div>
                  <Link
                    href={`/research/cases/${encodeURIComponent(selectedDetail.research_case_id)}`}
                    className="text-[11px] font-extrabold text-cyan-600 dark:text-cyan-400 hover:underline font-mono"
                  >
                    Full View →
                  </Link>
                </div>

                {(() => {
                  const dates = selectedDetail.life_events.map((e) => e.event_date);
                  const allSameDate = dates.length > 1 && dates.every((d) => d === dates[0]);
                  return (
                    <>
                      {!allSameDate && (
                        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800/80">
                          <div className="flex items-center justify-between mb-2">
                            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 font-mono">
                              Life Event Timeline
                            </h3>
                            <span className="text-[10px] text-cyan-600 dark:text-cyan-400 font-mono font-bold">
                              Click any node to inspect right pane
                            </span>
                          </div>
                          <EventTimelineChart
                            events={selectedDetail.life_events}
                            selectedEventId={selectedEvent?.id}
                            onSelectEvent={(ev) => setSelectedEvent(ev)}
                          />
                        </div>
                      )}
                      {allSameDate && (
                        <p className="text-[11px] text-slate-400 dark:text-slate-500">
                          Every event below shares the same birth-date fallback — the source
                          data doesn&apos;t carry a distinct date per event, so no timeline
                          chart is shown here.
                        </p>
                      )}

                      <div className="space-y-2">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 font-mono flex items-center justify-between">
                          <span>Life Events ({selectedDetail.life_events.length})</span>
                          <span className="text-[10px] text-slate-400 font-normal">showing max 5 · scroll for more</span>
                        </h3>
                        <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
                          {selectedDetail.life_events.map((ev, idx) => (
                            <button
                              key={ev.id || idx}
                              type="button"
                              onClick={() => setSelectedEvent(ev)}
                              className={`text-left transition rounded-lg ${
                                (selectedEvent?.id) === (ev.id)
                                  ? "ring-2 ring-cyan-500"
                                  : ""
                              }`}
                            >
                              <LifeEventCard event={ev} sharedFallbackDate={allSameDate} />
                            </button>
                          ))}
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>
            ) : (
              <div className="h-full min-h-[400px] flex items-center justify-center p-8 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-500 dark:text-slate-400 font-mono">
                Select a research case from the left panel.
              </div>
            )}
          </div>

          {/* PANE 3: Event Astrological Positions Inspector (Right - NO POPUP) */}
          <div className="pl-2 h-full flex flex-col">
            <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex-1 overflow-y-auto custom-scrollbar space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 font-mono flex items-center gap-1.5">
                  <span>⚡ Astrological Positions &amp; Snapshot Inspector</span>
                </h3>
                {selectedEvent && (
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-mono font-bold">
                    Active Inspection
                  </span>
                )}
              </div>

              {selectedEvent ? (
                <div className="space-y-4">
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-1">
                    <div className="text-xs font-extrabold text-cyan-600 dark:text-cyan-400 tracking-wide font-mono">
                      {formatEventTitle(selectedEvent.description || selectedEvent.event_type || selectedEvent.category)}
                    </div>
                  </div>

                  {/* Inline Astrological Detail Body (NO POPUP!) */}
                  <EventDetailBody event={selectedEvent} />
                </div>
              ) : (
                <div className="h-full min-h-[320px] flex flex-col items-center justify-center text-center p-6 text-xs text-slate-500 dark:text-slate-400 font-mono space-y-2">
                  <span className="text-2xl">🔍</span>
                  <p>Click any timeline node or event row in the middle panel to inspect its full planetary snapshot, active yogas &amp; dasha periods inline here.</p>
                </div>
              )}
            </div>
          </div>
        </ResizablePanels>
      </div>

      <GuidedHelpTour
        steps={CASE_DATABANK_TOUR_STEPS}
        isOpen={isTourOpen}
        onClose={() => setIsTourOpen(false)}
        tourId="cases"
      />
    </AppShell>
  );
}
