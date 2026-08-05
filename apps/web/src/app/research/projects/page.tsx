"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useCurrentUser } from "@/lib/auth";
import { researchProjectsApi, snapshotsApi, researchExportApi, researchModeApi } from "@/lib/research";
import type { ResearchProject, ResearchSnapshot, ResearchMode } from "@/lib/research";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, Input } from "@/components/ui";

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

  async function handleToggleResearchMode() {
    try {
      const mode = await researchModeApi.set(!researchMode?.enabled);
      setResearchMode(mode);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to toggle research mode.");
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
            <div className="flex items-center gap-3">
              {/* Research Mode Toggle */}
              <button
                type="button"
                onClick={handleToggleResearchMode}
                className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                  researchMode?.enabled
                    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                    : "border-gray-700 bg-transparent text-gray-400 hover:bg-white/5"
                }`}
                aria-label={`Research mode is ${researchMode?.enabled ? "on" : "off"}. Click to toggle.`}
              >
                <span className={`inline-block h-2 w-2 rounded-full ${researchMode?.enabled ? "bg-emerald-400" : "bg-gray-500"}`} />
                Research Mode {researchMode?.enabled ? "ON" : "OFF"}
              </button>

              <Button size="sm" onClick={() => setShowForm(!showForm)}>
                {showForm ? "Cancel" : "+ New Project"}
              </Button>
            </div>
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

          {/* Query logs section (when research mode is on) */}
          {researchMode?.enabled && researchMode.total_logged_queries > 0 && (
            <details className="group mt-8">
              <summary className="cursor-pointer text-sm font-medium text-gray-400">
                Research Mode Active — {researchMode.total_logged_queries} query
                {researchMode.total_logged_queries !== 1 ? "s" : ""} logged
              </summary>
              <div className="mt-2">
                <button
                  type="button"
                  onClick={() => router.push("/research/projects")}
                  className="text-xs text-cyan-400 underline"
                >
                  View query logs
                </button>
              </div>
            </details>
          )}
        </div>
      )}
    </AppShell>
  );
}
