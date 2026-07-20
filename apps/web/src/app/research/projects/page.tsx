"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useCurrentUser } from "@/lib/auth";
import { researchProjectsApi, snapshotsApi, researchExportApi, researchModeApi } from "@/lib/research";
import type { ResearchProject, ResearchSnapshot, ResearchMode } from "@/lib/research";

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
      const data = await researchProjectsApi.list(user.id, statusFilter || undefined);
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
        user_id: user.id,
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Research Projects
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Create and manage research projects, capture snapshots, compare versions, and export data.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Research Mode Toggle */}
          <button
            type="button"
            onClick={handleToggleResearchMode}
            className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
            style={{
              backgroundColor: researchMode?.enabled
                ? "rgba(34, 197, 94, 0.15)"
                : "var(--bg-card)",
              color: researchMode?.enabled ? "#22c55e" : "var(--text-secondary)",
              border: `1px solid ${
                researchMode?.enabled ? "rgba(34, 197, 94, 0.3)" : "var(--border-primary)"
              }`,
            }}
            aria-label={`Research mode is ${researchMode?.enabled ? "on" : "off"}. Click to toggle.`}
          >
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{
                backgroundColor: researchMode?.enabled ? "#22c55e" : "var(--text-muted)",
              }}
            />
            Research Mode {researchMode?.enabled ? "ON" : "OFF"}
          </button>

          <button
            type="button"
            onClick={() => setShowForm(!showForm)}
            className="btn-primary text-xs px-4 py-1.5"
          >
            {showForm ? "Cancel" : "+ New Project"}
          </button>
        </div>
      </div>

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

      {/* New Project Form */}
      {showForm && (
        <form
          onSubmit={handleCreateProject}
          className="rounded-xl border p-4 space-y-3"
          style={{
            borderColor: "var(--border-primary)",
            backgroundColor: "var(--bg-card)",
          }}
        >
          <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            New Research Project
          </h3>
          <div>
            <label
              htmlFor="project-title"
              className="mb-1 block text-xs"
              style={{ color: "var(--text-secondary)" }}
            >
              Title *
            </label>
            <input
              id="project-title"
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              required
              placeholder="e.g. Sade Sati Correlation Study"
              className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-input)",
                color: "var(--text-primary)",
              }}
            />
          </div>
          <div>
            <label
              htmlFor="project-description"
              className="mb-1 block text-xs"
              style={{ color: "var(--text-secondary)" }}
            >
              Description
            </label>
            <textarea
              id="project-description"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              placeholder="Optional description of the research project..."
              rows={3}
              className="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-input)",
                color: "var(--text-primary)",
              }}
            />
          </div>
          <button
            type="submit"
            disabled={!newTitle.trim()}
            className="rounded-lg bg-amber-600 px-4 py-2 text-xs font-semibold text-white hover:bg-amber-500 disabled:opacity-40 transition-colors"
          >
            Create Project
          </button>
        </form>
      )}

      {/* Status Filter */}
      <div className="flex flex-wrap gap-2">
        {["", "active", "archived"].map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setStatusFilter(s)}
            className="rounded-full px-3 py-1 text-xs font-medium transition-colors"
            style={{
              backgroundColor:
                statusFilter === s ? "var(--accent)" : "var(--bg-card)",
              color:
                statusFilter === s
                  ? "var(--accent-text)"
                  : "var(--text-secondary)",
              border: `1px solid ${
                statusFilter === s ? "var(--accent)" : "var(--border-primary)"
              }`,
            }}
          >
            {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Projects List */}
      {projects.length === 0 ? (
        <div
          className="flex flex-col items-center justify-center rounded-xl border py-16"
          style={{
            borderColor: "var(--border-primary)",
            backgroundColor: "var(--bg-card)",
          }}
        >
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            No research projects yet.
          </p>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Create your first project to start tracking research.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {projects.map((project) => {
            const projectSnapshots = snapshots[project.id] || [];
            return (
              <div
                key={project.id}
                className="rounded-xl border p-4 transition-colors hover:opacity-90"
                style={{
                  borderColor: "var(--border-primary)",
                  backgroundColor: "var(--bg-card)",
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3
                        className="text-base font-semibold truncate"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {project.title}
                      </h3>
                      <span
                        className="rounded-full px-2 py-0.5 text-xs uppercase tracking-wide"
                        style={{
                          backgroundColor:
                            project.status === "active"
                              ? "rgba(34, 197, 94, 0.15)"
                              : "rgba(100, 116, 139, 0.15)",
                          color:
                            project.status === "active" ? "#22c55e" : "var(--text-muted)",
                        }}
                      >
                        {project.status}
                      </span>
                    </div>
                    {project.description && (
                      <p
                        className="mt-1 text-sm line-clamp-2"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {project.description}
                      </p>
                    )}
                    <div className="mt-2 flex flex-wrap gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
                      <span>{projectSnapshots.length} snapshot{projectSnapshots.length !== 1 ? "s" : ""}</span>
                      <span>
                        Created:{" "}
                        {project.created_at
                          ? new Date(project.created_at).toLocaleDateString()
                          : "—"}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                    {/* View details */}
                    <button
                      type="button"
                      onClick={() => router.push(`/research/projects/${project.id}`)}
                      className="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
                      style={{
                        backgroundColor: "var(--accent)",
                        color: "var(--accent-text)",
                      }}
                      aria-label={`View details for ${project.title}`}
                    >
                      View
                    </button>

                    {/* Export CSV */}
                    <button
                      type="button"
                      onClick={() => handleExport(project.id, "csv")}
                      className="rounded-lg px-3 py-1.5 text-xs transition-colors"
                      style={{
                        border: "1px solid var(--border-primary)",
                        color: "var(--text-secondary)",
                      }}
                      aria-label={`Export ${project.title} as CSV`}
                    >
                      CSV
                    </button>

                    {/* Export JSON */}
                    <button
                      type="button"
                      onClick={() => handleExport(project.id, "json")}
                      className="rounded-lg px-3 py-1.5 text-xs transition-colors"
                      style={{
                        border: "1px solid var(--border-primary)",
                        color: "var(--text-secondary)",
                      }}
                      aria-label={`Export ${project.title} as JSON`}
                    >
                      JSON
                    </button>

                    {/* Archive */}
                    {project.status === "active" && (
                      <button
                        type="button"
                        onClick={() => handleArchiveProject(project.id)}
                        className="rounded-lg px-3 py-1.5 text-xs transition-colors"
                        style={{
                          border: "1px solid var(--border-primary)",
                          color: "var(--text-muted)",
                        }}
                        aria-label={`Archive ${project.title}`}
                      >
                        Archive
                      </button>
                    )}

                    {/* Delete */}
                    <button
                      type="button"
                      onClick={() => handleDeleteProject(project.id)}
                      className="rounded-lg px-3 py-1.5 text-xs transition-colors"
                      style={{
                        border: "1px solid rgba(239, 68, 68, 0.3)",
                        color: "#fca5a5",
                      }}
                      aria-label={`Delete ${project.title}`}
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {/* Snapshot preview */}
                {projectSnapshots.length > 0 && (
                  <div className="mt-3 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
                    <p className="mb-2 text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                      Recent Snapshots
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {projectSnapshots.slice(0, 5).map((snap) => (
                        <span
                          key={snap.id}
                          className="rounded-full px-2 py-0.5 text-xs"
                          style={{
                            backgroundColor: "var(--bg-secondary)",
                            color: "var(--text-secondary)",
                          }}
                        >
                          {snap.label || snap.id.slice(0, 8)}
                        </span>
                      ))}
                      {projectSnapshots.length > 5 && (
                        <span className="rounded-full px-2 py-0.5 text-xs" style={{ color: "var(--text-muted)" }}>
                          +{projectSnapshots.length - 5} more
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Query logs section (when research mode is on) */}
      {researchMode?.enabled && researchMode.total_logged_queries > 0 && (
        <details className="mt-8 group">
          <summary
            className="cursor-pointer text-sm font-medium"
            style={{ color: "var(--text-secondary)" }}
          >
            Research Mode Active — {researchMode.total_logged_queries} query
            {researchMode.total_logged_queries !== 1 ? "s" : ""} logged
          </summary>
          <div className="mt-2">
            <button
              type="button"
              onClick={() => router.push("/research/projects")}
              className="text-xs underline"
              style={{ color: "var(--accent)" }}
            >
              View query logs
            </button>
          </div>
        </details>
      )}
    </div>
  );
}
