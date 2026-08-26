"use client";

import { useMemo, useState } from "react";
import { Card } from "@/components/ui";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import { api } from "@/lib/api";
import { MultiDashaConfluenceStudio } from "@/components/research/MultiDashaConfluenceStudio";
import type {
  WorkflowAnalysisResponse,
  WorkflowAnalysisRequest,
  DashaTreeResponse,
} from "@/lib/types";

interface SystemComparison {
  system: string;
  label: string;
  loading: boolean;
  error: string | null;
  tree: DashaTreeResponse | null;
}

const SUPPORTED_SYSTEMS: { id: string; label: string; category: string }[] = [
  { id: "vimshottari", label: "Vimshottari (120y)", category: "Nakshatra" },
  { id: "yogini", label: "Yogini (36y)", category: "Nakshatra" },
  { id: "ashtottari", label: "Ashtottari (108y)", category: "Nakshatra" },
  { id: "chara", label: "Chara Dasha", category: "Jaimini Sign" },
  { id: "kalachakra", label: "Kalachakra (100y)", category: "Nakshatra" },
  { id: "narayana", label: "Narayana Dasha", category: "Jaimini Sign" },
];

/**
 * Multi-Dasha Convergence Tab
 * Enables multi-system comparison (Vimshottari, Yogini, Chara, Ashtottari, etc.)
 * showing current active periods across systems and highlighting confluence.
 */
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

  // Primary active system (from result)
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

  // Compare active periods across loaded systems
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
      <Card>
        <h4
          className="mb-2 text-xs font-semibold uppercase tracking-wide"
          style={{ color: "var(--text-tertiary)" }}
        >
          Select Systems to Compare against {primaryDasha.system}
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
                className="rounded-lg px-3 py-1.5 text-xs font-medium transition"
                style={{
                  backgroundColor: isPrimary
                    ? "var(--accent)"
                    : isSelected
                    ? "var(--bg-card-hover, rgba(255,255,255,0.08))"
                    : "transparent",
                  color: isPrimary
                    ? "var(--accent-text)"
                    : isSelected
                    ? "var(--text-primary)"
                    : "var(--text-secondary)",
                  border: "1px solid var(--border-primary)",
                  opacity: isPrimary ? 0.9 : 1,
                  cursor: isPrimary ? "default" : "pointer",
                }}
              >
                {sys.label} {isPrimary ? "(Active)" : isSelected ? "✓" : "+"}
                {isLoading && " …"}
              </button>
            );
          })}
        </div>
      </Card>

      {/* ── Active Period Confluence Matrix ────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {comparisons.map((comp) => {
          const md = comp.activeChain[0] ?? null;
          const ad = comp.activeChain[1] ?? null;
          const errorMsg = errors[comp.systemId];

          return (
            <Card key={comp.systemId}>
              <div className="flex items-center justify-between border-b pb-2 mb-3" style={{ borderColor: "var(--border-primary)" }}>
                <div>
                  <h4
                    className="text-sm font-bold capitalize"
                    style={{ color: "var(--accent)" }}
                  >
                    {comp.label}
                  </h4>
                  <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                    {comp.category}
                  </p>
                </div>
                {comp.tree && (
                  <span
                    className="text-[10px] font-medium"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Trigger: {comp.tree.trigger_planet}
                  </span>
                )}
              </div>

              {comp.tree ? (
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span style={{ color: "var(--text-secondary)" }}>Active Mahadasha:</span>
                    <strong style={{ color: "var(--text-primary)" }}>
                      {md ? `${md.lord} (${md.start_date} → ${md.end_date})` : "—"}
                    </strong>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span style={{ color: "var(--text-secondary)" }}>Active Antardasha:</span>
                    <strong style={{ color: "var(--text-primary)" }}>
                      {ad ? `${ad.lord} (${ad.start_date} → ${ad.end_date})` : "—"}
                    </strong>
                  </div>
                </div>
              ) : errorMsg ? (
                <p className="text-xs" style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>
                  {errorMsg}
                </p>
              ) : (
                <div className="py-4 text-center">
                  <button
                    type="button"
                    onClick={() => fetchSystemTree(comp.systemId)}
                    className="rounded-md px-3 py-1.5 text-xs font-semibold"
                    style={{
                      background: "var(--accent)",
                      color: "var(--accent-text)",
                    }}
                  >
                    Load {comp.label} Tree
                  </button>
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* ── Polymodal Multi-Dasha Confluence Studio ────────────────────────── */}
      <MultiDashaConfluenceStudio />

      {/* ── Multi-Dasha Synthesis Note ────────────────────────────────────── */}
      <Card>
        <h4
          className="mb-1 text-xs font-semibold uppercase tracking-wide"
          style={{ color: "var(--text-tertiary)" }}
        >
          Multi-Dasha Convergence Principle
        </h4>
        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
          When multiple independent dasha systems (e.g. Nakshatra-based Vimshottari alongside Sign-based Jaimini Chara Dasha) concurrently activate the same house, lord, or significator, the confidence of event manifestation rises significantly.
        </p>
      </Card>
    </div>
  );
}
