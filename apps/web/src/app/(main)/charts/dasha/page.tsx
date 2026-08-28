"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useWorkflowStore } from "@/lib/store";
import { useMyCharts, useActiveChart } from "@/lib/charts";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { ActiveChartSelectorModal } from "@/components/layout/ActiveChartSelectorModal";
import { DashaSystemSwitcher } from "@/components/charts/DashaSystemSwitcher";
import { DashaHeroCard, LEVEL_CONFIG } from "@/components/charts/DashaHeroCard";
import { DashaTimeline } from "@/components/charts/DashaTimeline";
import { DashaTreeExplorer } from "@/components/charts/DashaTreeExplorer";
import { DashaActivationMatrix } from "@/components/charts/DashaActivationMatrix";
import { DashaTransitConfluence } from "@/components/charts/DashaTransitConfluence";
import { VedhaAnalysisPanel } from "@/components/charts/VedhaAnalysisPanel";
import { MultiDashaConvergenceTab } from "@/components/charts/MultiDashaConvergenceTab";
import { DashaExportPanel } from "@/components/charts/DashaExportPanel";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import type { WorkflowAnalysisRequest } from "@/lib/types";

export const dynamic = "force-dynamic";

export type DashaWorkspaceTab =
  | "dashboard"
  | "systems"
  | "timeline"
  | "tree"
  | "activation"
  | "transit"
  | "convergence"
  | "reports";

const WORKSPACE_TABS: { key: DashaWorkspaceTab; label: string; icon: string; description: string }[] = [
  {
    key: "dashboard",
    label: "Dashboard",
    icon: "⊞",
    description: "Overview & Quick View • Active Mahadasha & Antardasha gauges and planetary chain",
  },
  {
    key: "systems",
    label: "Dasha Systems",
    icon: "⚙",
    description: "Select & Switch • Multi-engine computation layer (Vimshottari, Shoola, Narayana, Chara, etc.)",
  },
  {
    key: "timeline",
    label: "Timeline",
    icon: "⏱",
    description: "Interactive Multi-Dasha Timeline • D3 timeline with zoom, pan, and life event markers",
  },
  {
    key: "tree",
    label: "Dasha Tree",
    icon: "🌳",
    description: "Hierarchical Explorer • Nested 5-tier period drilldown (MD → AD → PD → SD → PR)",
  },
  {
    key: "activation",
    label: "Analysis Panel",
    icon: "⚡",
    description: "Period Analysis • Activated houses, planetary karakatvas, and yoga triggers",
  },
  {
    key: "transit",
    label: "Event Timing",
    icon: "◎",
    description: "Correlations & Events • Active lords live transit status, Gochar, and Vedha obstruction",
  },
  {
    key: "convergence",
    label: "Convergence",
    icon: "✦",
    description: "Multi-Dasha Convergence • Cross-system consensus across Vimshottari, Yogini, Chara, Narayana",
  },
  {
    key: "reports",
    label: "Reports",
    icon: "⎙",
    description: "Export & Print • Generate structured PDF, Excel, and CSV research reports",
  },
];

const KEY_FLOWS = [
  { step: 1, text: "User selects Dasha System" },
  { step: 2, text: "System loads timeline" },
  { step: 3, text: "User clicks a period" },
  { step: 4, text: "Hierarchy loads" },
  { step: 5, text: "Analysis generated" },
  { step: 6, text: "Transits correlated" },
  { step: 7, text: "Reports & Export" },
];

function formatBirthDatetime(iso: string | undefined): string {
  if (!iso) return "15 Aug 1990, 10:30 AM IST";
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-US", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return iso;
  }
}

function DashaWorkspaceContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);
  const setResult = useWorkflowStore((s) => s.setResult);

  const analyze = useAnalyzeWorkflow();
  const { data: myChartsData, isLoading: loadingCharts } = useMyCharts();
  const { activeSummary } = useActiveChart();

  const [selectorModalOpen, setSelectorModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<DashaWorkspaceTab>("dashboard");
  const [autoLoadAttempted, setAutoLoadAttempted] = useState(false);

  // Sync tab from query params if present
  useEffect(() => {
    const tabParam = searchParams.get("tab") as DashaWorkspaceTab | null;
    if (tabParam && WORKSPACE_TABS.some((t) => t.key === tabParam)) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  // Auto-load active/default chart if store is empty
  useEffect(() => {
    if (result || autoLoadAttempted || loadingCharts) return;
    setAutoLoadAttempted(true);

    const activeId =
      typeof window !== "undefined"
        ? localStorage.getItem("astroos_last_viewed_chart_id")
        : null;
    const target =
      (activeId ? myChartsData?.charts?.find((c) => c.id === activeId) : null) ??
      myChartsData?.charts?.find((c) => c.is_default) ??
      myChartsData?.charts?.[0];

    if (target) {
      const req: WorkflowAnalysisRequest = {
        birth_datetime_utc: target.birth_datetime_utc,
        latitude: target.birth_latitude,
        longitude: target.birth_longitude,
        ayanamsa: (target.ayanamsa as WorkflowAnalysisRequest["ayanamsa"]) || "lahiri",
        house_system: (target.house_system as WorkflowAnalysisRequest["house_system"]) || "placidus",
        dasha_system: "vimshottari",
        include_vargas: true,
        subject_name: target.subject_name,
        place_name: target.place_name,
        persist: false,
        chart_id: target.id,
      };
      analyze.mutate(req, {
        onSuccess: (data) => setResult(data, req),
      });
    }
  }, [result, autoLoadAttempted, loadingCharts, myChartsData, analyze, setResult]);

  const changeTab = (tab: DashaWorkspaceTab) => {
    setActiveTab(tab);
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", tab);
    router.replace(`/charts/dasha?${params.toString()}`, { scroll: false });
  };

  if (!result || !result.dasha) {
    return (
      <div className="container mx-auto max-w-7xl px-4 py-12">
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-12 text-center shadow-sm">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-amber-400 border-t-transparent" />
          <h2 className="text-base font-bold text-slate-100">
            {analyze.isPending ? "Computing Dasha Orchestration…" : "Loading Chart Workspace…"}
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Initializing Multi-Dasha Engines, Unified Timeline, and planetary hierarchy.
          </p>
        </div>
      </div>
    );
  }

  const dasha = result.dasha;

  return (
    <div className="container mx-auto max-w-7xl space-y-5 px-4 py-5">
      {/* ── Active Chart Bar ───────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/90 p-3 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 text-sm">
            {(activeSummary?.subject_name ?? request?.subject_name ?? "C")[0].toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-100">
                AstroOS — Dasha Module Architecture
              </h1>
              <span className="rounded-md bg-slate-800 px-2 py-0.5 text-[11px] font-semibold text-slate-300 border border-slate-700">
                {activeSummary?.subject_name ?? request?.subject_name ?? "Saved Chart"}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {formatBirthDatetime(activeSummary?.birth_datetime_utc ?? request?.birth_datetime_utc)}
              {(activeSummary?.place_name ?? request?.place_name) &&
                ` · ${activeSummary?.place_name ?? request?.place_name}`}
              {" · Ayanamsa: "}{request?.ayanamsa?.toUpperCase() ?? "LAHIRI"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setSelectorModalOpen(true)}
            className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 border border-slate-700 hover:bg-slate-700 transition"
          >
            Switch Chart
          </button>
          <Link
            href="/charts"
            className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-slate-200 border border-slate-800 transition"
          >
            Back to Overview
          </Link>
        </div>
      </div>

      {/* ── CLIENT LAYER Navigation Tabs Bar ────────────────────────────── */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-1.5 shadow-sm">
        <div
          className="flex flex-wrap gap-1"
          role="tablist"
          aria-label="AstroOS Dasha Architecture Modules"
        >
          {WORKSPACE_TABS.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => changeTab(tab.key)}
                className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                  isActive
                    ? "bg-amber-400 text-slate-900 shadow-xs"
                    : "text-slate-400 hover:bg-slate-800/80 hover:text-slate-200"
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Module Tab Content Views ────────────────────────────────────── */}
      {activeTab === "dashboard" && (
        <div className="space-y-5">
          <DashaHeroCard dasha={dasha} />
          <DashaSystemSwitcher
            current={dasha.system}
            birthParams={
              request
                ? {
                    birth_datetime_utc: request.birth_datetime_utc,
                    latitude: request.latitude,
                    longitude: request.longitude,
                    ayanamsa: request.ayanamsa,
                    house_system: request.house_system,
                  }
                : undefined
            }
            onChange={(nextDasha) => setResult({ ...result, dasha: nextDasha }, request!)}
            layout="compact"
          />
          <DashaTimeline dasha={dasha} />
        </div>
      )}

      {activeTab === "systems" && (
        <div className="space-y-5">
          <DashaSystemSwitcher
            current={dasha.system}
            birthParams={
              request
                ? {
                    birth_datetime_utc: request.birth_datetime_utc,
                    latitude: request.latitude,
                    longitude: request.longitude,
                    ayanamsa: request.ayanamsa,
                    house_system: request.house_system,
                  }
                : undefined
            }
            onChange={(nextDasha) => setResult({ ...result, dasha: nextDasha }, request!)}
            layout="grid"
          />
        </div>
      )}

      {activeTab === "timeline" && (
        <div className="space-y-5">
          <DashaTimeline dasha={dasha} />
        </div>
      )}

      {activeTab === "tree" && (
        <div className="space-y-5">
          <DashaTreeExplorer dasha={dasha} />
        </div>
      )}

      {activeTab === "activation" && (
        <div className="space-y-5">
          <DashaActivationMatrix result={result} />
        </div>
      )}

      {activeTab === "transit" && (
        <div className="space-y-5">
          <DashaTransitConfluence result={result} />
          <VedhaAnalysisPanel
            transits={result.transits}
            dashaChain={getCurrentDashaChain(dasha.mahadashas)}
          />
        </div>
      )}

      {activeTab === "convergence" && (
        <div className="space-y-5">
          <MultiDashaConvergenceTab result={result} request={request} />
        </div>
      )}

      {activeTab === "reports" && (
        <div className="space-y-5">
          <DashaExportPanel dasha={dasha} />
        </div>
      )}

      {/* ── Footer: Hierarchy Levels Legend & Key Flows ─────────────────── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.4fr_1fr] pt-2">
        {/* DASHA HIERARCHY LEVELS LEGEND */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-sm">
          <div className="mb-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              DASHA HIERARCHY LEVELS
            </h4>
            <p className="text-[11px] text-slate-400">
              Recursive planetary time partitions from Mahadasha down to Prana sub-lord
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {Object.entries(LEVEL_CONFIG).map(([lvl, cfg]) => (
              <div
                key={lvl}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1 text-xs font-semibold border ${cfg.bg} ${cfg.border}`}
              >
                <span>{cfg.label}</span>
                <span className="rounded bg-slate-800/80 px-1 py-0.5 text-[10px] font-mono font-normal">
                  ({cfg.short})
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* KEY FLOWS GUIDE */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-sm">
          <div className="mb-2.5 flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              KEY FLOWS (1 → 7)
            </h4>
            <span className="text-[10px] font-mono text-slate-400">Pipeline Sequence</span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-300">
            {KEY_FLOWS.map((flow, i) => (
              <div key={flow.step} className="flex items-center gap-1.5">
                <span className="flex h-4 w-4 items-center justify-center rounded-full bg-slate-800 text-[10px] font-bold text-amber-400 border border-slate-700">
                  {flow.step}
                </span>
                <span className="text-[11px] text-slate-300">{flow.text}</span>
                {i < KEY_FLOWS.length - 1 && <span className="text-slate-600 text-xs">→</span>}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Active Chart Switcher Modal ─────────────────────────────────── */}
      <ActiveChartSelectorModal
        isOpen={selectorModalOpen}
        onClose={() => setSelectorModalOpen(false)}
      />
    </div>
  );
}

export default function DashaPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto max-w-7xl px-4 py-12 text-center text-sm text-slate-400">
          Loading Dasha Workspace…
        </div>
      }
    >
      <DashaWorkspaceContent />
    </Suspense>
  );
}


