"use client";

import { useMemo, useState } from "react";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import { api } from "@/lib/api";
import { MultiDashaConfluenceStudio } from "@/components/research/MultiDashaConfluenceStudio";
import type {
  WorkflowAnalysisResponse,
  WorkflowAnalysisRequest,
  DashaTreeResponse,
} from "@/lib/types";

const SUPPORTED_SYSTEMS: { id: string; label: string; category: string }[] = [
  { id: "vimshottari", label: "Vimshottari (120y)", category: "Nakshatra" },
  { id: "yogini", label: "Yogini (36y)", category: "Nakshatra" },
  { id: "ashtottari", label: "Ashtottari (108y)", category: "Nakshatra" },
  { id: "chara", label: "Chara Dasha", category: "Jaimini Sign" },
  { id: "kalachakra", label: "Kalachakra (100y)", category: "Nakshatra" },
  { id: "narayana", label: "Narayana Dasha", category: "Jaimini Sign" },
];

export function MultiDashaConvergenceTab({
  result,
  request,
}: {
  result: WorkflowAnalysisResponse;
  request?: WorkflowAnalysisRequest | null;
}) {
  const [selectedSystems, setSelectedSystems] = useState<string[]>([
    "yogini",
    "chara",
    "ashtottari",
  ]);
  const [loadedTrees, setLoadedTrees] = useState<Record<string, DashaTreeResponse>>({});
  const [loadingSystems, setLoadingSystems] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  const primaryDasha = result.dasha;
  const primaryChain = useMemo(
    () => getCurrentDashaChain(primaryDasha.mahadashas),
    [primaryDasha.mahadashas],
  );

  const fetchSystemTree = async (sysId: string) => {
    if (!request || loadedTrees[sysId] || loadingSystems[sysId]) return;

    setLoadingSystems((prev) => ({ ...prev, [sysId]: true }));
    setErrors((prev) => ({ ...prev, [sysId]: "" }));

    try {
      const data = await api.post<DashaTreeResponse>(`/api/v1/dasha/${sysId}`, {
        birth_datetime_utc: request.birth_datetime_utc,
        latitude: request.latitude,
        longitude: request.longitude,
        ayanamsa: request.ayanamsa,
        house_system: request.house_system,
        max_depth: 3,
      });
      setLoadedTrees((prev) => ({ ...prev, [sysId]: data }));
    } catch (err: any) {
      setErrors((prev) => ({
        ...prev,
        [sysId]: err.message || `Failed to fetch ${sysId} dasha tree`,
      }));
    } finally {
      setLoadingSystems((prev) => ({ ...prev, [sysId]: false }));
    }
  };

  const toggleSystem = (sysId: string) => {
    if (selectedSystems.includes(sysId)) {
      setSelectedSystems(selectedSystems.filter((s) => s !== sysId));
    } else {
      setSelectedSystems([...selectedSystems, sysId]);
      fetchSystemTree(sysId);
    }
  };

  const comparisons = useMemo(() => {
    const list: {
      systemId: string;
      label: string;
      category: string;
      tree: DashaTreeResponse | null;
      activeChain: ReturnType<typeof getCurrentDashaChain>;
    }[] = [
      {
        systemId: primaryDasha.system,
        label: primaryDasha.system,
        category: "Primary System",
        tree: primaryDasha,
        activeChain: primaryChain,
      },
    ];

    for (const sysId of selectedSystems) {
      const sysInfo = SUPPORTED_SYSTEMS.find((s) => s.id === sysId);
      const tree = loadedTrees[sysId] ?? null;
      const activeChain = tree ? getCurrentDashaChain(tree.mahadashas) : [];
      list.push({
        systemId: sysId,
        label: sysInfo?.label ?? sysId,
        category: sysInfo?.category ?? "Dasha",
        tree,
        activeChain,
      });
    }

    return list;
  }, [primaryDasha, primaryChain, selectedSystems, loadedTrees]);

  return (
    <div className="space-y-4">
      {/* ── System Selector Header ─────────────────────────────────────────── */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-sm">
        <h4 className="mb-2.5 text-xs font-bold uppercase tracking-wider text-slate-200">
          Compare Active Periods Across Dasha Systems (vs {primaryDasha.system.toUpperCase()})
        </h4>
        <div className="flex flex-wrap gap-2">
          {SUPPORTED_SYSTEMS.map((sys) => {
            const isPrimary = sys.id === primaryDasha.system.toLowerCase();
            const isSelected = selectedSystems.includes(sys.id);
            const isLoading = loadingSystems[sys.id];

            return (
              <button
                key={sys.id}
                type="button"
                disabled={isPrimary}
                onClick={() => toggleSystem(sys.id)}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                  isPrimary
                    ? "bg-amber-400 text-slate-900 shadow-xs cursor-default"
                    : isSelected
                    ? "bg-slate-800 text-slate-100 border border-slate-700"
                    : "bg-slate-900/80 text-slate-400 border border-slate-800 hover:bg-slate-800 hover:text-slate-200"
                }`}
              >
                {sys.label} {isPrimary ? "(Active)" : isSelected ? "✓" : "+"}
                {isLoading && " …"}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Active Period Confluence Matrix ────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {comparisons.map((comp) => {
          const md = comp.activeChain[0] ?? null;
          const ad = comp.activeChain[1] ?? null;
          const errorMsg = errors[comp.systemId];

          return (
            <div key={comp.systemId} className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                <div>
                  <h4 className="text-xs font-bold capitalize text-slate-100">
                    {comp.label}
                  </h4>
                  <p className="text-[10px] text-slate-400">
                    {comp.category}
                  </p>
                </div>
                {comp.tree && (
                  <span className="text-[11px] font-mono text-slate-400">
                    Trigger: <strong className="text-slate-200">{comp.tree.trigger_planet}</strong>
                  </span>
                )}
              </div>

              {comp.tree ? (
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Active Mahadasha:</span>
                    <strong className="text-slate-100 font-semibold">
                      {md ? `${md.lord} (${md.start_date} → ${md.end_date})` : "—"}
                    </strong>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Active Antardasha:</span>
                    <strong className="text-slate-100 font-semibold">
                      {ad ? `${ad.lord} (${ad.start_date} → ${ad.end_date})` : "—"}
                    </strong>
                  </div>
                </div>
              ) : errorMsg ? (
                <p className="text-xs text-rose-400">
                  {errorMsg}
                </p>
              ) : (
                <div className="py-3 text-center">
                  <button
                    type="button"
                    onClick={() => fetchSystemTree(comp.systemId)}
                    className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 border border-slate-700 hover:bg-slate-700 transition"
                  >
                    Load {comp.label} Tree
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── Polymodal Multi-Dasha Confluence Studio ────────────────────────── */}
      <MultiDashaConfluenceStudio />

      {/* ── Multi-Dasha Synthesis Note ────────────────────────────────────── */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-sm">
        <h4 className="mb-1 text-xs font-bold uppercase tracking-wider text-slate-200">
          Multi-Dasha Convergence Principle
        </h4>
        <p className="text-xs text-slate-400">
          When multiple independent dasha systems (e.g. Nakshatra-based Vimshottari alongside Sign-based Jaimini Chara Dasha) concurrently activate the same house, lord, or significator, the confidence of event manifestation rises significantly.
        </p>
      </div>
    </div>
  );
}
