"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useCurrentUser } from "@/lib/auth";
import { researchProjectsApi, snapshotsApi, researchExportApi, researchModeApi } from "@/lib/research";
import type { ResearchProject, ResearchSnapshot, ResearchMode, QueryLogEntry } from "@/lib/research";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, Input } from "@/components/ui";

/** Real backend action codes (apps/api/services/research_middleware.py
 * _get_action()) translated to short human sentences — mirrors the same
 * lookup in components/dashboard/DashboardOverview.tsx. Anything not in
 * this map falls back to the raw action string with underscores replaced
 * by spaces, so a newly-added backend action still renders legibly. */
const ACTION_LABELS: Record<string, string> = {
  workflow_analyze: "Ran a full chart analysis",
  snapshot_compare: "Compared two snapshots",
  snapshot_capture: "Captured a research snapshot",
  project_create: "Created a research project",
  research_query: "Ran a research query",
  hypothesis_generate: "Generated AI hypotheses",
  export: "Exported research data",
  chart_compare: "Compared charts",
  enhanced_qa: "Asked an enhanced Q&A question",
  hypothesis_validate: "Reviewed a hypothesis",
  research_mode_toggle: "Toggled Research Mode",
  query_log_view: "Viewed activity logs",
  research_action: "Research action",
};

function actionLabel(action: string): string {
  return ACTION_LABELS[action] ?? action.replace(/_/g, " ");
}

/** response_summary is "{status} {path}" — pull just the status code out
 * to render a small ok/error dot instead of the raw string. */
function logStatusOk(log: QueryLogEntry): boolean {
  const code = parseInt(log.response_summary.split(" ")[0] ?? "", 10);
  return !Number.isNaN(code) && code < 400;
}

export default function ResearchProjectsPage() {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [snapshots, setSnapshots] = useState<Record<string, ResearchSnapshot[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");

  // New project form
  const [showForm, setShowForm] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");

  // Research mode
  const [researchMode, setResearchMode] = useState<ResearchMode | null>(null);

  // Query logs (fetched on demand when the disclosure below is opened)
  const [queryLogs, setQueryLogs] = useState<QueryLogEntry[] | null>(null);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logsError, setLogsError] = useState<string | null>(null);

  async function loadQueryLogs() {
    if (queryLogs !== null || logsLoading) return; // fetch once per page visit
    setLogsLoading(true);
    setLogsError(null);
    try {
      const data = await researchModeApi.listLogs({ limit: 20 });
      setQueryLogs(data.logs);
    } catch (err) {
      setLogsError(err instanceof Error ? err.message : "Failed to load query logs.");
    } finally {
      setLogsLoading(false);
    }
  }

  const loadProjects = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await researchProjectsApi.list(statusFilter || undefined);
      setProjects(data.projects);

      // Load snapshots for each project
      const snapMap: Record<string, ResearchSnapshot[]> = {};
      await Promise.all(
        data.projects.map(async (p) => {
          try {
            const snapData = await snapshotsApi.list(p.id);
            snapMap[p.id] = snapData.snapshots;
          } catch {
            snapMap[p.id] = [];
          }
        })
      );
      setSnapshots(snapMap);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects.");
    } finally {
      setLoading(false);
    }
  }, [user, statusFilter]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  // Load research mode
  useEffect(() => {
    researchModeApi.get().then(setResearchMode).catch(() => {});
  }, []);

  async function handleCreateProject(e: React.FormEvent) {
    e.preventDefault();
    if (!user || !newTitle.trim()) return;
    try {
      await researchProjectsApi.create({
        title: newTitle.trim(),
        description: newDescription.trim() || null,
      });
      setNewTitle("");
      setNewDescription("");
      setShowForm(false);
      await loadProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project.");
    }
  }

  async function handleDeleteProject(id: string) {
    if (!confirm("Delete this project and all its snapshots?")) return;
    try {
      await researchProjectsApi.delete(id);
      await loadProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete project.");
    }
  }

  async function handleArchiveProject(id: string) {
    try {
      await researchProjectsApi.update(id, { status: "archived" });
      await loadProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to archive project.");
    }
  }

  async function handleExport(projectId: string, format: "csv" | "json") {
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
      ) : (
        <div className="space-y-6">
          {/* Header */}
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-3xl font-bold">Research Projects</h1>
              <p className="mt-2 text-sm text-gray-400">
                Create and manage research projects, capture snapshots, compare versions, and export data.
              </p>
            </div>
            {/* Research Mode has one global control — the compact toggle
                in AppShell's header — rather than a second one here that
                would drift out of sync with it (each held independent
                fetched-on-mount state hitting the same backend flag). */}
            <Button size="sm" onClick={() => setShowForm(!showForm)}>
              {showForm ? "Cancel" : "+ New Project"}
            </Button>
          </div>

          {error && (
            <Card padding="0" className="px-4 py-3">
              <p className="text-sm text-red-400" role="alert">
                {error}
                <button type="button" onClick={() => setError(null)} className="ml-2 underline">
                  Dismiss
                </button>
              </p>
            </Card>
          )}

          {/* New Project Form */}
          {showForm && (
            <Card padding="0" className="p-5">
              <form onSubmit={handleCreateProject} className="space-y-3">
                <h3 className="text-sm font-semibold text-gray-100">New Research Project</h3>
                <Input
                  label="Title *"
                  value={newTitle}
                  onChange={setNewTitle}
                  required
                  placeholder="e.g. Sade Sati Correlation Study"
                />
                <div>
                  <label htmlFor="project-description" className="mb-1 block text-xs text-gray-400">
                    Description
                  </label>
                  <textarea
                    id="project-description"
                    value={newDescription}
                    onChange={(e) => setNewDescription(e.target.value)}
                    placeholder="Optional description of the research project..."
                    rows={3}
                    className="w-full rounded-lg border border-gray-700 bg-black/40 px-3 py-2 text-sm text-gray-100 outline-none transition-colors focus:border-cyan-400"
                  />
                </div>
                <Button type="submit" size="sm" disabled={!newTitle.trim()}>
                  Create Project
                </Button>
              </form>
            </Card>
          )}

          {/* Status Filter */}
          <div className="flex flex-wrap gap-2">
            {["", "active", "archived"].map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setStatusFilter(s)}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  statusFilter === s
                    ? "border-cyan-400 bg-cyan-400/10 text-cyan-300"
                    : "border-gray-700 bg-transparent text-gray-400 hover:bg-white/5"
                }`}
              >
                {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>

          {/* Projects List */}
          {projects.length === 0 ? (
            <Card padding="0" className="flex flex-col items-center justify-center py-16 px-4">
              <p className="text-sm text-gray-500">No research projects yet.</p>
              <p className="mt-1 text-xs text-gray-500">Create your first project to start tracking research.</p>
            </Card>
          ) : (
            <div className="space-y-4">
              {projects.map((project) => {
                const projectSnapshots = snapshots[project.id] || [];
                return (
                  <Card key={project.id} padding="0" className="p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="truncate text-base font-semibold text-gray-100">{project.title}</h3>
                          <Badge tone={project.status === "active" ? "success" : "neutral"}>{project.status}</Badge>
                        </div>
                        {project.description && (
                          <p className="mt-1 line-clamp-2 text-sm text-gray-400">{project.description}</p>
                        )}
                        <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-500">
                          <span>{projectSnapshots.length} snapshot{projectSnapshots.length !== 1 ? "s" : ""}</span>
                          <span>
                            Created: {project.created_at ? new Date(project.created_at).toLocaleDateString() : "—"}
                          </span>
                        </div>
                      </div>

                      <div className="flex flex-shrink-0 items-center gap-2">
                        <Button size="sm" onClick={() => router.push(`/research/projects/${project.id}`)} aria-label={`View details for ${project.title}`}>
                          View
                        </Button>
                        <Button variant="secondary" size="sm" onClick={() => handleExport(project.id, "csv")} aria-label={`Export ${project.title} as CSV`}>
                          CSV
                        </Button>
                        <Button variant="secondary" size="sm" onClick={() => handleExport(project.id, "json")} aria-label={`Export ${project.title} as JSON`}>
                          JSON
                        </Button>
                        {project.status === "active" && (
                          <Button variant="secondary" size="sm" onClick={() => handleArchiveProject(project.id)} aria-label={`Archive ${project.title}`}>
                            Archive
                          </Button>
                        )}
                        <Button variant="danger" size="sm" onClick={() => handleDeleteProject(project.id)} aria-label={`Delete ${project.title}`}>
                          Delete
                        </Button>
                      </div>
                    </div>

                    {/* Snapshot preview */}
                    {projectSnapshots.length > 0 && (
                      <div className="mt-3 border-t border-gray-800 pt-3">
                        <p className="mb-2 text-xs font-medium text-gray-500">Recent Snapshots</p>
                        <div className="flex flex-wrap gap-2">
                          {projectSnapshots.slice(0, 5).map((snap) => (
                            <Badge key={snap.id} tone="neutral">
                              {snap.label || snap.id.slice(0, 8)}
                            </Badge>
                          ))}
                          {projectSnapshots.length > 5 && (
                            <span className="rounded-full px-2 py-0.5 text-xs text-gray-500">
                              +{projectSnapshots.length - 5} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          )}

          {/* Query logs section (when research mode is on) — fetches and
              renders the real log entries inline on open, rather than
              linking to a page (this one) that doesn't have a log viewer. */}
          {researchMode?.enabled && researchMode.total_logged_queries > 0 && (
            <details className="group mt-8" onToggle={(e) => e.currentTarget.open && loadQueryLogs()}>
              <summary className="cursor-pointer text-sm font-medium text-gray-400">
                Research Mode Active — {researchMode.total_logged_queries} query
                {researchMode.total_logged_queries !== 1 ? "s" : ""} logged
              </summary>
              <div className="mt-3">
                {logsLoading && (
                  <p className="text-xs text-gray-500">Loading query logs…</p>
                )}
                {logsError && (
                  <p className="text-xs text-red-400" role="alert">{logsError}</p>
                )}
                {queryLogs && queryLogs.length === 0 && (
                  <p className="text-xs text-gray-500">No query logs recorded yet.</p>
                )}
                {queryLogs && queryLogs.length > 0 && (
                  <ul className="space-y-1.5">
                    {queryLogs.map((log) => {
                      const ok = logStatusOk(log);
                      return (
                        <li key={log.id} className="flex items-center gap-2.5 text-xs">
                          <span
                            className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full ${ok ? "bg-emerald-400" : "bg-red-400"}`}
                            aria-hidden="true"
                          />
                          <span className="text-gray-300">{actionLabel(log.action)}</span>
                          <span className="text-gray-600">·</span>
                          <span className="text-gray-500">{log.duration_ms}ms</span>
                          {log.created_at && (
                            <>
                              <span className="text-gray-600">·</span>
                              <span className="text-gray-500">{new Date(log.created_at).toLocaleString()}</span>
                            </>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </details>
          )}
        </div>
      )}
    </AppShell>
  );
}
