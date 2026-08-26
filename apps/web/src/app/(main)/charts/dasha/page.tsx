"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useWorkflowStore } from "@/lib/store";
import { useMyCharts, useActiveChart } from "@/lib/charts";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { ActiveChartSelectorModal } from "@/components/layout/ActiveChartSelectorModal";
import { DashaSystemSwitcher } from "@/components/charts/DashaSystemSwitcher";
import { DashaHeroCard } from "@/components/charts/DashaHeroCard";
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
  | "tree"
  | "activation"
  | "transit"
  | "convergence"
  | "reports";

const WORKSPACE_TABS: { key: DashaWorkspaceTab; label: string; description: string }[] = [
  { key: "tree", label: "Tree", description: "Mahadasha hierarchy, interactive timeline, and deep periods tree" },
  { key: "activation", label: "Activation", description: "Activated houses, karakatvas, and triggered yogas" },
  { key: "transit", label: "Dasha × Transit", description: "Active lords live transit status and double-transit correlation" },
  { key: "convergence", label: "Multi-Dasha Convergence", description: "Cross-system agreement between Vimshottari, Yogini, Chara, etc." },
  { key: "reports", label: "Export & Reports", description: "Download and print structured Dasha reports" },
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
  const [activeTab, setActiveTab] = useState<DashaWorkspaceTab>("tree");
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
      <div className="container mx-auto max-w-7xl px-4 py-8">
        <div
          className="rounded-xl border p-12 text-center"
          style={{
            borderColor: "var(--border-primary)",
            background: "var(--bg-card)",
          }}
        >
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent" />
          <h2
            className="text-base font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            {analyze.isPending ? "Computing Dasha Analysis…" : "Loading Chart Data…"}
          </h2>
          <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
            Preparing timing cycles and planetary period hierarchy.
          </p>
        </div>
      </div>
    );
  }

  const dasha = result.dasha;

  return (
    <div className="container mx-auto max-w-7xl space-y-6 px-4 py-6">
      {/* ── Active Chart Bar ───────────────────────────────────────────── */}
      <div
        className="flex flex-wrap items-center justify-between gap-3 rounded-xl p-3"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-primary)",
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-lg font-bold"
            style={{
              background: "var(--accent)",
              color: "var(--accent-text)",
            }}
          >
            {(activeSummary?.subject_name ?? request?.subject_name ?? "C")[0].toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1
                className="text-base font-bold"
                style={{ color: "var(--text-primary)" }}
              >
                Dasha Deep Dive
              </h1>
              <span
                className="rounded-md px-2 py-0.5 text-[10px] font-semibold"
                style={{
                  background: "var(--bg-card-hover, rgba(255,255,255,0.06))",
                  border: "1px solid var(--border-primary)",
                  color: "var(--accent)",
                }}
              >
                {activeSummary?.subject_name ?? request?.subject_name ?? "Saved Chart"}
              </span>
            </div>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
              {formatBirthDatetime(activeSummary?.birth_datetime_utc ?? request?.birth_datetime_utc)}
              {(activeSummary?.place_name ?? request?.place_name) &&
                ` · ${activeSummary?.place_name ?? request?.place_name}`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setSelectorModalOpen(true)}
            className="rounded-lg px-3 py-1.5 text-xs font-semibold transition"
            style={{
              background: "var(--bg-card-hover, rgba(255,255,255,0.08))",
              border: "1px solid var(--border-primary)",
              color: "var(--text-primary)",
            }}
          >
            Switch Chart
          </button>
          <Link
            href="/charts"
            className="rounded-lg px-3 py-1.5 text-xs font-medium transition"
            style={{
              color: "var(--text-secondary)",
            }}
          >
            Back to Overview
          </Link>
        </div>
      </div>

      {/* ── Dasha Hero Card ─────────────────────────────────────────────── */}
      <DashaHeroCard dasha={dasha} />

      {/* ── Dasha System Switcher ──────────────────────────────────────── */}
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
      />

      {/* ── Workspace 4-Tab Navigation Bar ──────────────────────────────── */}
      <div>
        <div
          className="flex flex-wrap gap-1 border-b pb-2"
          style={{ borderColor: "var(--border-primary)" }}
          role="tablist"
          aria-label="Dasha Deep Dive Workspace Tabs"
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
                className="rounded-lg px-4 py-2 text-xs font-semibold transition"
                style={{
                  backgroundColor: isActive ? "var(--accent)" : "transparent",
                  color: isActive ? "var(--accent-text)" : "var(--text-secondary)",
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
        <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
          {WORKSPACE_TABS.find((t) => t.key === activeTab)?.description}
        </p>
      </div>

      {/* ── Tab Content Views ───────────────────────────────────────────── */}
      {activeTab === "tree" && (
        <div className="space-y-6">
          <DashaTimeline dasha={dasha} />
          <DashaTreeExplorer dasha={dasha} />
        </div>
      )}

      {activeTab === "activation" && (
        <DashaActivationMatrix result={result} />
      )}

      {activeTab === "transit" && (
        <div className="space-y-6">
          <DashaTransitConfluence result={result} />
          <VedhaAnalysisPanel
            transits={result.transits}
            dashaChain={getCurrentDashaChain(dasha.mahadashas)}
          />
        </div>
      )}

      {activeTab === "convergence" && (
        <MultiDashaConvergenceTab result={result} request={request} />
      )}

      {activeTab === "reports" && (
        <DashaExportPanel dasha={dasha} />
      )}

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
        <div className="container mx-auto max-w-7xl px-4 py-8 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
          Loading Dasha Workspace…
        </div>
      }
    >
      <DashaWorkspaceContent />
    </Suspense>
  );
}
