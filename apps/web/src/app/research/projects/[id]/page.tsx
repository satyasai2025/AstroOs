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

interface ExtendedSnapshot extends ResearchSnapshot {
  _extended?: {
    chart_summary?: string;
    yogas_present?: number;
  };
}

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

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center" role="status">
        <span
          className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-t-transparent"
          style={{ borderColor: "var(--accent)", borderTopColor: "transparent" }}
        />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex flex-col items-center gap-4 py-20">
        <p style={{ color: "var(--text-secondary)" }}>Project not found.</p>
        <button
          type="button"
          onClick={() => router.push("/research/projects")}
          className="btn-primary text-xs px-4 py-1.5"
        >
          Back to Projects
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back link */}
      <button
        type="button"
        onClick={() => router.push("/research/projects")}
        className="text-xs transition-colors"
        style={{ color: "var(--accent)" }}
      >
        &larr; Back to Projects
      </button>

      {error && (
        <div
          className="rounded-lg border px-4 py-3 text-sm"
          style={{
            borderColor: "rgba(239, 68, 68, 0.3)",
            backgroundColor: "rgba(239, 68, 68, 0.1)",
            color: "#fca5a5",
          }}
          role="alert"
        >
          {error}
          <button
            type="button"
            onClick={() => setError(null)}
            className="ml-2 underline"
            aria-label="Dismiss error"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Project header */}
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {editing ? (
            <div className="space-y-3">
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="w-full rounded-lg border px-3 py-2 text-lg font-bold outline-none transition-colors"
                style={{
                  borderColor: "var(--border-primary)",
                  backgroundColor: "var(--bg-input)",
                  color: "var(--text-primary)",
                }}
              />
              <textarea
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                rows={3}
                className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
                style={{
                  borderColor: "var(--border-primary)",
                  backgroundColor: "var(--bg-input)",
                  color: "var(--text-primary)",
                }}
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
                  onClick={() => setEditing(false)}
                  className="rounded-lg border px-4 py-1.5 text-xs"
                  style={{
                    borderColor: "var(--border-primary)",
                    color: "var(--text-secondary)",
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
                {project.title}
              </h1>
              <div className="mt-1 flex items-center gap-3">
                <span
                  className="rounded-full px-2 py-0.5 text-xs uppercase tracking-wide"
                  style={{
                    backgroundColor:
                      project.status === "active"
                        ? "rgba(34, 197, 94, 0.15)"
                        : "rgba(100, 116, 139, 0.15)",
                    color: project.status === "active" ? "#22c55e" : "var(--text-muted)",
                  }}
                >
                  {project.status}
                </span>
                {project.description && (
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                    {project.description}
                  </p>
                )}
              </div>
            </>
          )}
        </div>

        <div className="flex items-center gap-2 ml-4 flex-shrink-0">
          {!editing && (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="rounded-lg px-3 py-1.5 text-xs"
              style={{
                border: "1px solid var(--border-primary)",
                color: "var(--text-secondary)",
              }}
            >
              Edit
            </button>
          )}
          <button
            type="button"
            onClick={() => handleExport("csv")}
            className="rounded-lg px-3 py-1.5 text-xs"
            style={{
              border: "1px solid var(--border-primary)",
              color: "var(--text-secondary)",
            }}
          >
            Export CSV
          </button>
          <button
            type="button"
            onClick={() => handleExport("json")}
            className="rounded-lg px-3 py-1.5 text-xs"
            style={{
              border: "1px solid var(--border-primary)",
              color: "var(--text-secondary)",
            }}
          >
            Export JSON
          </button>
        </div>
      </div>

      {/* Snapshot Comparison */}
      <div
        className="rounded-xl border p-4"
        style={{
          borderColor: "var(--border-primary)",
          backgroundColor: "var(--bg-card)",
        }}
      >
        <h2 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Snapshot Comparison
        </h2>

        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[200px]">
            <label
              htmlFor="compare-a"
              className="mb-1 block text-xs"
              style={{ color: "var(--text-secondary)" }}
            >
              Snapshot A
            </label>
            <select
              id="compare-a"
              value={compareA}
              onChange={(e) => setCompareA(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-xs outline-none"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-input)",
                color: "var(--text-primary)",
              }}
            >
              <option value="">Select a snapshot...</option>
              {snapshots.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label || s.id.slice(0, 8)} — {new Date(s.captured_at).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1 min-w-[200px]">
            <label
              htmlFor="compare-b"
              className="mb-1 block text-xs"
              style={{ color: "var(--text-secondary)" }}
            >
              Snapshot B
            </label>
            <select
              id="compare-b"
              value={compareB}
              onChange={(e) => setCompareB(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-xs outline-none"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-input)",
                color: "var(--text-primary)",
              }}
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
            className="rounded-lg bg-amber-600 px-4 py-2 text-xs font-semibold text-white hover:bg-amber-500 disabled:opacity-40 transition-colors"
          >
            {comparing ? "Comparing..." : "Compare"}
          </button>
        </div>

        {/* Comparison Results */}
        {comparison && (
          <div className="mt-4 space-y-4">
            <div
              className="rounded-lg border p-3"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-secondary)",
              }}
            >
              <div className="flex items-center justify-between">
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  <span className="font-medium" style={{ color: "var(--text-primary)" }}>
                    {comparison.matching_fields.length}
                  </span>{" "}
                  matching fields
                </p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  <span className="font-medium" style={{ color: "var(--text-primary)" }}>
                    {comparison.differing_fields.length}
                  </span>{" "}
                  differing fields
                </p>
              </div>
            </div>

            {/* Matching fields */}
            {comparison.matching_fields.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                  Matching Fields
                </p>
                <div className="flex flex-wrap gap-2">
                  {comparison.matching_fields.map((f) => (
                    <span
                      key={f}
                      className="rounded-full px-2 py-0.5 text-xs"
                      style={{
                        backgroundColor: "rgba(34, 197, 94, 0.1)",
                        color: "#22c55e",
                      }}
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Differing fields */}
            {comparison.differing_fields.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                  Differing Fields
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b" style={{ borderColor: "var(--border-primary)" }}>
                        <th className="py-2 pr-3 font-medium" style={{ color: "var(--text-muted)" }}>
                          Field
                        </th>
                        <th className="py-2 pr-3 font-medium" style={{ color: "var(--text-muted)" }}>
                          Snapshot A
                        </th>
                        <th className="py-2 font-medium" style={{ color: "var(--text-muted)" }}>
                          Snapshot B
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.differing_fields.map((diff) => (
                        <tr
                          key={diff.field}
                          className="border-b"
                          style={{ borderColor: "var(--border-primary)" }}
                        >
                          <td
                            className="py-2 pr-3 font-medium"
                            style={{ color: "var(--text-primary)" }}
                          >
                            {diff.field}
                          </td>
                          <td
                            className="py-2 pr-3"
                            style={{ color: "var(--text-secondary)" }}
                          >
                            {String(diff.value_a ?? "—")}
                          </td>
                          <td
                            className="py-2"
                            style={{ color: "var(--text-secondary)" }}
                          >
                            {String(diff.value_b ?? "—")}
                          </td>
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
      <div
        className="rounded-xl border p-4"
        style={{
          borderColor: "var(--border-primary)",
          backgroundColor: "var(--bg-card)",
        }}
      >
        <h2 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Snapshots ({snapshots.length})
        </h2>

        {snapshots.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            No snapshots captured yet. Run a workflow analysis with this project selected to create snapshots.
          </p>
        ) : (
          <div className="space-y-2">
            {snapshots.map((snap) => (
              <div
                key={snap.id}
                className="flex items-center justify-between rounded-lg border p-3"
                style={{
                  borderColor: "var(--border-primary)",
                  backgroundColor: "var(--bg-secondary)",
                }}
              >
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {snap.label || `Snapshot ${snap.id.slice(0, 8)}`}
                  </p>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Chart: {snap.chart_id.slice(0, 8)}... |{" "}
                    Captured: {new Date(snap.captured_at).toLocaleString()} | v{snap.snapshot_version}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setCompareA(snap.id);
                      setCompareB("");
                    }}
                    className="rounded-lg px-2 py-1 text-xs"
                    style={{
                      border: "1px solid var(--border-primary)",
                      color: "var(--text-secondary)",
                    }}
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
                    className="rounded-lg px-2 py-1 text-xs"
                    style={{
                      border: "1px solid rgba(239, 68, 68, 0.3)",
                      color: "#fca5a5",
                    }}
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
        <div
          className="rounded-xl border p-4"
          style={{
            borderColor: "var(--border-primary)",
            backgroundColor: "var(--bg-card)",
          }}
        >
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              Hypothesis Validations ({validations.length})
            </h2>
            <button
              type="button"
              onClick={() => router.push("/research/hypotheses")}
              className="text-xs underline"
              style={{ color: "var(--accent)" }}
            >
              View All
            </button>
          </div>

          <div className="space-y-2">
            {validations.slice(0, 5).map((v) => (
              <div
                key={v.id}
                className="flex items-center justify-between rounded-lg border p-3"
                style={{
                  borderColor: "var(--border-primary)",
                  backgroundColor: "var(--bg-secondary)",
                }}
              >
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {v.title}
                  </p>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    {v.hypothesis_id} | {v.domain} | {v.ai_generated ? "AI-generated" : "Manual"}
                  </p>
                </div>
                <span
                  className="rounded-full px-2 py-0.5 text-xs uppercase"
                  style={{
                    backgroundColor:
                      v.status === "confirmed"
                        ? "rgba(34, 197, 94, 0.15)"
                        : v.status === "rejected"
                          ? "rgba(239, 68, 68, 0.15)"
                          : "rgba(251, 191, 36, 0.15)",
                    color:
                      v.status === "confirmed"
                        ? "#22c55e"
                        : v.status === "rejected"
                          ? "#fca5a5"
                          : "#fbbf24",
                  }}
                >
                  {v.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
