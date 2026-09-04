"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useCurrentUser } from "@/lib/auth";
import {
  researchProjectsApi,
  snapshotsApi,
  researchExportApi,
  hypothesisValidationApi,
} from "@/lib/research";
import type {
  ResearchProject,
  ResearchSnapshot,
  SnapshotComparisonResponse,
  HypothesisValidation,
} from "@/lib/research";
import { AppShell } from "@/components/layout/AppShell";

interface ExtendedSnapshot extends ResearchSnapshot {
  _extended?: {
    chart_summary?: string;
    yogas_present?: number;
  };
}

const VALIDATION_BADGE_CLASS: Record<string, string> = {
  confirmed: "bg-emerald-500/15 text-emerald-400",
  rejected: "bg-red-500/15 text-red-300",
};

export default function ResearchProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const { data: user } = useCurrentUser();

  const [project, setProject] = useState<ResearchProject | null>(null);
  const [snapshots, setSnapshots] = useState<ExtendedSnapshot[]>([]);
  const [validations, setValidations] = useState<HypothesisValidation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Snapshot compare
  const [compareA, setCompareA] = useState<string>("");
  const [compareB, setCompareB] = useState<string>("");
  const [comparison, setComparison] = useState<SnapshotComparisonResponse | null>(null);
  const [comparing, setComparing] = useState(false);

  // Edit mode
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [proj, snapData, validData] = await Promise.all([
        researchProjectsApi.get(projectId),
        snapshotsApi.list(projectId),
        hypothesisValidationApi.list({ project_id: projectId }),
      ]);
      setProject(proj);
      setSnapshots(snapData.snapshots);
      setValidations(validData.validations);
      setEditTitle(proj.title);
      setEditDescription(proj.description || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project.");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleUpdateProject() {
    if (!project || !editTitle.trim()) return;
    try {
      await researchProjectsApi.update(projectId, {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
      });
      setEditing(false);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update project.");
    }
  }

  async function handleCompare() {
    if (!compareA || !compareB) return;
    if (compareA === compareB) {
      setError("Please select two different snapshots to compare.");
      return;
    }
    setComparing(true);
    setError(null);
    try {
      const result = await snapshotsApi.compare(compareA, compareB);
      setComparison(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed.");
    } finally {
      setComparing(false);
    }
  }

  async function handleExport(format: "csv" | "json") {
    try {
      const blob = await researchExportApi.export(projectId, format, true);
      const url = URL.createObjectURL(blob);
      const a = window.document.createElement("a");
      a.href = url;
      a.download = `research-export-${projectId.slice(0, 8)}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.");
    }
  }

  return (
    <AppShell sectionColor="--section-research">
      {loading ? (
        <div className="flex min-h-[60vh] items-center justify-center" role="status">
          <span className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
        </div>
      ) : !project ? (
        <div className="flex flex-col items-center gap-4 py-20">
          <p className="text-gray-400">Project not found.</p>
          <button
            type="button"
            onClick={() => router.push("/research/projects")}
            className="btn-primary text-xs px-4 py-1.5"
          >
            Back to Projects
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Back link */}
          <button
            type="button"
            onClick={() => router.push("/research/projects")}
            className="text-xs text-cyan-400 transition-colors"
          >
            &larr; Back to Projects
          </button>

          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300" role="alert">
              {error}
              <button type="button" onClick={() => setError(null)} className="ml-2 underline" aria-label="Dismiss error">
                Dismiss
              </button>
            </div>
          )}

          {/* Project header */}
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              {editing ? (
                <div className="space-y-3">
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-lg font-bold text-slate-900 dark:text-slate-100 outline-none transition-colors focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <textarea
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    rows={3}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 outline-none transition-colors focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={handleUpdateProject}
                      disabled={!editTitle.trim()}
                      className="rounded-lg bg-amber-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-amber-500 disabled:opacity-40"
                    >
                      Save
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setEditTitle(project.title);
                        setEditDescription(project.description || "");
                        setEditing(false);
                      }}
                      className="rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 px-4 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">{project.title}</h1>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                    {project.description || "No description provided."}
                  </p>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  project.status === "active" ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-500/20 text-slate-400"
                }`}
              >
                {project.status.replace("_", " ")}
              </span>
              {!editing && (
                <button
                  type="button"
                  onClick={() => setEditing(true)}
                  className="rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 px-3 py-1 text-xs text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                >
                  Edit
                </button>
              )}
            </div>
          </div>

          {/* Snapshot Comparator */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Compare Snapshots</h2>
            <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400">
              Select two snapshots to compare dataset size and hypothesis statuses.
            </p>

            <div className="mt-3 flex flex-wrap items-end gap-3">
              <div className="min-w-[200px] flex-1">
                <label htmlFor="compare-a" className="mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Snapshot A
                </label>
                <select
                  id="compare-a"
                  value={compareA}
                  onChange={(e) => setCompareA(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select a snapshot...</option>
                  {snapshots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.label || s.id.slice(0, 8)} — {new Date(s.captured_at).toLocaleDateString()}
                    </option>
                  ))}
                </select>
              </div>

              <div className="min-w-[200px] flex-1">
                <label htmlFor="compare-b" className="mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Snapshot B
                </label>
                <select
                  id="compare-b"
                  value={compareB}
                  onChange={(e) => setCompareB(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Select a snapshot...</option>
                  {snapshots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.label || s.id.slice(0, 8)} — {new Date(s.captured_at).toLocaleDateString()}
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="button"
                onClick={handleCompare}
                disabled={!compareA || !compareB || comparing}
                className="rounded-lg bg-amber-600 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-amber-500 disabled:opacity-40"
              >
                {comparing ? "Comparing..." : "Compare"}
              </button>
            </div>

            {/* Comparison Results */}
            {comparison && (
              <div className="mt-4 space-y-4">
                <div className="rounded-lg border border-gray-700 bg-black/30 p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-gray-500">
                      <span className="font-medium text-gray-100">{comparison.matching_fields.length}</span> matching fields
                    </p>
                    <p className="text-xs text-gray-500">
                      <span className="font-medium text-gray-100">{comparison.differing_fields.length}</span> differing fields
                    </p>
                  </div>
                </div>

                {/* Matching fields */}
                {comparison.matching_fields.length > 0 && (
                  <div>
                    <p className="mb-2 text-xs font-medium text-gray-500">Matching Fields</p>
                    <div className="flex flex-wrap gap-2">
                      {comparison.matching_fields.map((f) => (
                        <span key={f} className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Differing fields */}
                {comparison.differing_fields.length > 0 && (
                  <div>
                    <p className="mb-2 text-xs font-medium text-gray-500">Differing Fields</p>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-gray-800">
                            <th className="py-2 pr-3 font-medium text-gray-500">Field</th>
                            <th className="py-2 pr-3 font-medium text-gray-500">Snapshot A</th>
                            <th className="py-2 font-medium text-gray-500">Snapshot B</th>
                          </tr>
                        </thead>
                        <tbody>
                          {comparison.differing_fields.map((diff) => (
                            <tr key={diff.field} className="border-b border-gray-800">
                              <td className="py-2 pr-3 font-medium text-gray-100">{diff.field}</td>
                              <td className="py-2 pr-3 text-gray-400">{String(diff.value_a ?? "—")}</td>
                              <td className="py-2 text-gray-400">{String(diff.value_b ?? "—")}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Snapshots list */}
          <div className="rounded-xl border border-gray-700 bg-white/5 p-4">
            <h2 className="mb-3 text-sm font-semibold text-gray-100">Snapshots ({snapshots.length})</h2>

            {snapshots.length === 0 ? (
              <p className="text-xs text-gray-500">
                No snapshots captured yet. Run a workflow analysis with this project selected to create snapshots.
              </p>
            ) : (
              <div className="space-y-2">
                {snapshots.map((snap) => (
                  <div key={snap.id} className="flex items-center justify-between rounded-lg border border-gray-700 bg-black/30 p-3">
                    <div>
                      <p className="text-sm font-medium text-gray-100">
                        {snap.label || `Snapshot ${snap.id.slice(0, 8)}`}
                      </p>
                      <p className="text-xs text-gray-500">
                        Chart: {snap.chart_id.slice(0, 8)}... | Captured: {new Date(snap.captured_at).toLocaleString()} | v{snap.snapshot_version}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setCompareA(snap.id);
                          setCompareB("");
                        }}
                        className="rounded-lg border border-gray-700 px-2 py-1 text-xs text-gray-400"
                      >
                        Compare
                      </button>
                      <button
                        type="button"
                        onClick={async () => {
                          try {
                            await snapshotsApi.delete(snap.id);
                            await loadData();
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Failed to delete snapshot.");
                          }
                        }}
                        className="rounded-lg border border-red-500/30 px-2 py-1 text-xs text-red-300"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Hypothesis Validations */}
          {validations.length > 0 && (
            <div className="rounded-xl border border-gray-700 bg-white/5 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-100">Hypothesis Validations ({validations.length})</h2>
                <button
                  type="button"
                  onClick={() => router.push("/research/hypotheses")}
                  className="text-xs text-cyan-400 underline"
                >
                  View All
                </button>
              </div>

              <div className="space-y-2">
                {validations.slice(0, 5).map((v) => (
                  <div key={v.id} className="flex items-center justify-between rounded-lg border border-gray-700 bg-black/30 p-3">
                    <div>
                      <p className="text-sm font-medium text-gray-100">{v.title}</p>
                      <p className="text-xs text-gray-500">
                        {v.hypothesis_id} | {v.domain} | {v.ai_generated ? "AI-generated" : "Manual"}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs uppercase ${
                        VALIDATION_BADGE_CLASS[v.status] ?? "bg-amber-500/15 text-amber-400"
                      }`}
                    >
                      {v.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
