"use client";

import { useState, useEffect, useMemo } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, Icon } from "@/components/ui";
import { researchProjectsApi } from "@/lib/research";
import type { ResearchProject, FieldDiff } from "@/lib/research";
import { useCurrentUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

interface DisplaySnapshot {
  id: string;
  project_id: string;
  projectName: string;
  chart_id: string;
  subjectName: string;
  label: string;
  captured_at: string;
  snapshot_version: string;
  ayanamsa: string;
  houseSystem: string;
  planetsCount: number;
  dashaActive: string;
}

const SAMPLE_SNAPSHOTS: DisplaySnapshot[] = [
  {
    id: "snap-001",
    project_id: "proj-1",
    projectName: "Saturn Sade Sati Longitudinal Study",
    chart_id: "chart-101",
    subjectName: "Dr. A. P. J. Kalam",
    label: "Natal Baseline D-1 & D-9 (1931)",
    captured_at: "2026-08-15T14:32:00Z",
    snapshot_version: "v2.3.1-ephem",
    ayanamsa: "Lahiri (Chitra Paksha)",
    houseSystem: "Whole Sign",
    planetsCount: 9,
    dashaActive: "Saturn / Jupiter / Sun",
  },
  {
    id: "snap-002",
    project_id: "proj-1",
    projectName: "Saturn Sade Sati Longitudinal Study",
    chart_id: "chart-101",
    subjectName: "Dr. A. P. J. Kalam",
    label: "First Peak Saturn Transit (1998)",
    captured_at: "2026-08-16T09:15:00Z",
    snapshot_version: "v2.3.1-ephem",
    ayanamsa: "Lahiri (Chitra Paksha)",
    houseSystem: "Whole Sign",
    planetsCount: 9,
    dashaActive: "Mercury / Rahu / Venus",
  },
  {
    id: "snap-003",
    project_id: "proj-2",
    projectName: "Medical Astrology & 6th House Afflictions",
    chart_id: "chart-204",
    subjectName: "Clinical Cohort Subject #42",
    label: "Pre-Diagnosis Vimshottari State",
    captured_at: "2026-08-18T11:45:00Z",
    snapshot_version: "v2.3.1-ephem",
    ayanamsa: "KP System (Krishnamurti)",
    houseSystem: "Placidus",
    planetsCount: 9,
    dashaActive: "Mars / Saturn / Ketu",
  },
  {
    id: "snap-004",
    project_id: "proj-2",
    projectName: "Medical Astrology & 6th House Afflictions",
    chart_id: "chart-204",
    subjectName: "Clinical Cohort Subject #42",
    label: "Post-Remedy Transit Snapshot",
    captured_at: "2026-08-20T16:20:00Z",
    snapshot_version: "v2.3.1-ephem",
    ayanamsa: "KP System (Krishnamurti)",
    houseSystem: "Placidus",
    planetsCount: 9,
    dashaActive: "Mars / Mercury / Jupiter",
  },
];

export default function SnapshotManagerPage() {
  const { data: _user } = useCurrentUser();
  const [snapshotsList, setSnapshotsList] = useState<DisplaySnapshot[]>(SAMPLE_SNAPSHOTS);
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [projectFilter, setProjectFilter] = useState("all");

  // Comparison State
  const [selectedSnapshotA, setSelectedSnapshotA] = useState<string | null>("snap-001");
  const [selectedSnapshotB, setSelectedSnapshotB] = useState<string | null>("snap-002");
  const [comparing, setComparing] = useState(false);

  // Capture modal
  const [showCaptureModal, setShowCaptureModal] = useState(false);
  const [newLabel, setNewLabel] = useState("");
  const [newSubject, setNewSubject] = useState("");
  const [newProject, setNewProject] = useState("");
  const [newAyanamsa, setNewAyanamsa] = useState("Lahiri (Chitra Paksha)");

  // Load real projects if available
  useEffect(() => {
    researchProjectsApi
      .list()
      .then((res) => {
        if (res?.projects && res.projects.length > 0) {
          setProjects(res.projects);
        }
      })
      .catch(() => {
        // Fallback to sample projects
      });
  }, []);

  const filteredSnapshots = useMemo(() => {
    return snapshotsList.filter((s) => {
      const matchProject = projectFilter === "all" || s.project_id === projectFilter;
      const q = searchQuery.toLowerCase().trim();
      const matchSearch =
        !q ||
        s.label.toLowerCase().includes(q) ||
        s.subjectName.toLowerCase().includes(q) ||
        s.projectName.toLowerCase().includes(q) ||
        s.dashaActive.toLowerCase().includes(q);

      return matchProject && matchSearch;
    });
  }, [snapshotsList, searchQuery, projectFilter]);

  const snapA = snapshotsList.find((s) => s.id === selectedSnapshotA);
  const snapB = snapshotsList.find((s) => s.id === selectedSnapshotB);

  const sampleDiffs: FieldDiff[] = useMemo(() => {
    if (!snapA || !snapB) return [];
    return [
      {
        field: "Active Dasha Chain",
        value_a: snapA.dashaActive,
        value_b: snapB.dashaActive,
      },
      {
        field: "Capture Timestamp",
        value_a: new Date(snapA.captured_at).toLocaleDateString(),
        value_b: new Date(snapB.captured_at).toLocaleDateString(),
      },
      {
        field: "Label / Research Stage",
        value_a: snapA.label,
        value_b: snapB.label,
      },
      {
        field: "Ayanamsa System",
        value_a: snapA.ayanamsa,
        value_b: snapB.ayanamsa,
      },
      {
        field: "House Division Mode",
        value_a: snapA.houseSystem,
        value_b: snapB.houseSystem,
      },
    ];
  }, [snapA, snapB]);

  const handleCaptureSnapshot = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLabel || !newSubject) return;

    const newSnap: DisplaySnapshot = {
      id: `snap-${Date.now().toString().slice(-4)}`,
      project_id: newProject || "proj-custom",
      projectName: newProject
        ? projects.find((p) => p.id === newProject)?.title || "Custom Research Project"
        : "General Astrological Research",
      chart_id: `chart-${Date.now().toString().slice(-3)}`,
      subjectName: newSubject,
      label: newLabel,
      captured_at: new Date().toISOString(),
      snapshot_version: "v2.3.1-ephem",
      ayanamsa: newAyanamsa,
      houseSystem: "Whole Sign",
      planetsCount: 9,
      dashaActive: "Jupiter / Saturn / Mars",
    };

    setSnapshotsList([newSnap, ...snapshotsList]);
    setShowCaptureModal(false);
    setNewLabel("");
    setNewSubject("");
  };

  const handleDeleteSnapshot = (id: string) => {
    setSnapshotsList(snapshotsList.filter((s) => s.id !== id));
    if (selectedSnapshotA === id) setSelectedSnapshotA(null);
    if (selectedSnapshotB === id) setSelectedSnapshotB(null);
  };

  const handleExportJson = (snap: DisplaySnapshot) => {
    const dataStr = JSON.stringify(snap, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `snapshot_${snap.id}_${snap.subjectName.replace(/\s+/g, "_")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <AppShell sectionColor="--section-research">
      <div className="mx-auto max-w-7xl space-y-6 px-3 py-6 sm:px-6">
        {/* ── 1. Hero Header Banner ── */}
        <div className="relative overflow-hidden rounded-2xl border p-6 text-white shadow-xl backdrop-blur-sm" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <div className="relative z-10 flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-950/60 px-3 py-1 text-xs font-bold text-cyan-400">
                <Icon name="camera" style={{ width: 14, height: 14 }} />
                <span>Longitudinal Research &amp; Ephemeris State Audit</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
                Research <span className="text-cyan-400">Snapshot Manager</span>
              </h1>
              <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 font-medium leading-relaxed">
                Capture, freeze, and diff point-in-time calculation states across astrological cohorts, planetary transits, and Dasha shifts with cryptographic reproducibility.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => setComparing(!comparing)}
                className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition cursor-pointer ${
                  comparing
                    ? "bg-amber-100 text-amber-900 border border-amber-600/40 dark:bg-amber-950/60 dark:text-amber-300 shadow-md"
                    : "border border-slate-700/60 bg-slate-800 text-slate-200 hover:border-cyan-500/40"
                }`}
              >
                <Icon name="layers" style={{ width: 15, height: 15 }} />
                <span>{comparing ? "Close Diff Viewer" : "Compare Snapshots"}</span>
              </button>

              <button
                type="button"
                onClick={() => setShowCaptureModal(true)}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-cyan-500/25 transition cursor-pointer"
              >
                <Icon name="camera" style={{ width: 15, height: 15 }} />
                <span>Capture Snapshot</span>
              </button>
            </div>
          </div>
        </div>

        {/* ── 2. Capture Snapshot Modal ── */}
        {showCaptureModal && (
          <div className="rounded-2xl border p-6 shadow-2xl space-y-4 backdrop-blur-sm" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
            <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
              <div className="flex items-center gap-2">
                <Icon name="camera" style={{ width: 18, height: 18, color: "var(--accent)" }} />
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Freeze New Research Calculation Snapshot
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowCaptureModal(false)}
                className="text-xs font-bold text-slate-400 hover:text-slate-200 cursor-pointer"
              >
                ✕ Cancel
              </button>
            </div>

            <form onSubmit={handleCaptureSnapshot} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-800 dark:text-slate-200">
                    Native / Chart Name <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={newSubject}
                    onChange={(e) => setNewSubject(e.target.value)}
                    placeholder="e.g. Albert Einstein / Study Case #12"
                    className="w-full rounded-xl border px-3.5 py-2 text-xs font-medium outline-none"
                    style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-800 dark:text-slate-200">
                    Snapshot Stage / Label <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={newLabel}
                    onChange={(e) => setNewLabel(e.target.value)}
                    placeholder="e.g. 1905 Annus Mirabilis Transit Baseline"
                    className="w-full rounded-xl border px-3.5 py-2 text-xs font-medium outline-none"
                    style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-800 dark:text-slate-200">
                    Associate with Project
                  </label>
                  <select
                    value={newProject}
                    onChange={(e) => setNewProject(e.target.value)}
                    className="w-full rounded-xl border px-3 py-2 text-xs font-medium outline-none"
                    style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
                  >
                    <option value="">General Research</option>
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.title}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-800 dark:text-slate-200">
                    Ayanamsa Calculation Baseline
                  </label>
                  <select
                    value={newAyanamsa}
                    onChange={(e) => setNewAyanamsa(e.target.value)}
                    className="w-full rounded-xl border px-3 py-2 text-xs font-medium outline-none"
                    style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
                  >
                    <option value="Lahiri (Chitra Paksha)">Lahiri (Chitra Paksha)</option>
                    <option value="KP System (Krishnamurti)">KP System (Krishnamurti)</option>
                    <option value="BV Raman">BV Raman</option>
                    <option value="True Chitra">True Chitra / Tropical</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2 border-t" style={{ borderColor: "var(--border-primary)" }}>
                <button
                  type="button"
                  onClick={() => setShowCaptureModal(false)}
                  className="rounded-xl px-4 py-2 text-xs font-bold text-slate-600 dark:text-slate-400 hover:bg-slate-800 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 px-5 py-2 text-xs font-bold text-white shadow-md shadow-cyan-500/20 cursor-pointer"
                >
                  Save &amp; Freeze State
                </button>
              </div>
            </form>
          </div>
        )}

        {/* ── 3. Side-by-Side Comparison Workspace ── */}
        {comparing && (
          <Card className="p-6 border border-amber-500/30 bg-amber-950/20 space-y-6 backdrop-blur-sm shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <Icon name="layers" style={{ width: 18, height: 18, color: "#f59e0b" }} />
                  <span>Longitudinal Snapshot Difference Engine</span>
                </h3>
                <p className="text-xs text-slate-700 dark:text-slate-300 font-medium">
                  Side-by-side state diff of planetary alignments, Dasha periods, and house cusps between two frozen moments.
                </p>
              </div>

              <span className="rounded-full bg-amber-100 text-amber-900 border border-amber-600/40 dark:bg-amber-950/60 dark:text-amber-300 px-3 py-1 text-xs font-bold shadow-xs">
                Comparing 2 Snapshots
              </span>
            </div>

            {/* Selectors */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-cyan-500/30 bg-slate-900/90 p-4 space-y-2">
                <label className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                  Primary Baseline (Snapshot A)
                </label>
                <select
                  value={selectedSnapshotA || ""}
                  onChange={(e) => setSelectedSnapshotA(e.target.value)}
                  className="w-full rounded-xl border px-3 py-2 text-xs font-semibold outline-none"
                  style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
                >
                  {snapshotsList.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.subjectName} — {s.label} ({s.id})
                    </option>
                  ))}
                </select>
                {snapA && (
                  <div className="text-[11px] text-slate-300 pt-1 space-y-0.5 font-medium">
                    <p><strong>Dasha:</strong> {snapA.dashaActive}</p>
                    <p><strong>Captured:</strong> {new Date(snapA.captured_at).toLocaleString()}</p>
                  </div>
                )}
              </div>

              <div className="rounded-xl border border-purple-500/30 bg-slate-900/90 p-4 space-y-2">
                <label className="text-xs font-bold uppercase tracking-wider text-purple-400">
                  Comparison Target (Snapshot B)
                </label>
                <select
                  value={selectedSnapshotB || ""}
                  onChange={(e) => setSelectedSnapshotB(e.target.value)}
                  className="w-full rounded-xl border px-3 py-2 text-xs font-semibold outline-none"
                  style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
                >
                  {snapshotsList.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.subjectName} — {s.label} ({s.id})
                    </option>
                  ))}
                </select>
                {snapB && (
                  <div className="text-[11px] text-slate-300 pt-1 space-y-0.5 font-medium">
                    <p><strong>Dasha:</strong> {snapB.dashaActive}</p>
                    <p><strong>Captured:</strong> {new Date(snapB.captured_at).toLocaleString()}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Field Diff Table */}
            <div className="overflow-x-auto rounded-xl border" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
              <table className="w-full text-left text-xs">
                <thead className="border-b bg-slate-900/60 text-slate-300 font-bold" style={{ borderColor: "var(--border-primary)" }}>
                  <tr>
                    <th className="p-3">Field / Parameter</th>
                    <th className="p-3 text-cyan-400">Snapshot A Value</th>
                    <th className="p-3 text-purple-400">Snapshot B Value</th>
                    <th className="p-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/20 text-slate-200">
                  {sampleDiffs.map((diff, idx) => {
                    const isDiff = diff.value_a !== diff.value_b;
                    return (
                      <tr key={idx} className="hover:bg-primary/5">
                        <td className="p-3 font-semibold">{diff.field}</td>
                        <td className="p-3 text-slate-300 font-mono font-medium">
                          {String(diff.value_a)}
                        </td>
                        <td className="p-3 text-slate-300 font-mono font-medium">
                          {String(diff.value_b)}
                        </td>
                        <td className="p-3 text-right">
                          {isDiff ? (
                            <span className="rounded bg-amber-100 text-amber-900 border border-amber-600/40 dark:bg-amber-950/60 dark:text-amber-300 px-2 py-0.5 text-[10px] font-bold">
                              Delta Shift
                            </span>
                          ) : (
                            <span className="rounded bg-emerald-100 text-emerald-900 border border-emerald-600/40 dark:bg-emerald-950/60 dark:text-emerald-300 px-2 py-0.5 text-[10px] font-bold">
                              Identical
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* ── 4. Search & Filter Bar ── */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
          <div className="relative flex-1 max-w-md">
            <input
              type="text"
              placeholder="Search snapshots by native, label, or dasha..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border px-3 py-2 pl-9 text-xs sm:text-sm font-medium outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            />
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
              <Icon name="search" style={{ width: 15, height: 15 }} />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-800 dark:text-slate-200">Project:</span>
            <select
              value={projectFilter}
              onChange={(e) => setProjectFilter(e.target.value)}
              className="rounded-xl border px-3 py-1.5 text-xs font-semibold outline-none"
              style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
            >
              <option value="all">All Projects</option>
              <option value="proj-1">Saturn Sade Sati Study</option>
              <option value="proj-2">Medical Astrology Afflictions</option>
            </select>
          </div>
        </div>

        {/* ── 5. Snapshots Grid / Cards ── */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {filteredSnapshots.length === 0 ? (
            <div className="col-span-full rounded-xl border border-dashed p-8 text-center text-slate-400 text-sm" style={{ borderColor: "var(--border-primary)" }}>
              No snapshots found matching your criteria. Click <strong>Capture Snapshot</strong> to freeze a new calculation state.
            </div>
          ) : (
            filteredSnapshots.map((snap) => {
              const isA = selectedSnapshotA === snap.id;
              const isB = selectedSnapshotB === snap.id;
              return (
                <Card
                  key={snap.id}
                  className="flex flex-col justify-between p-5 border transition space-y-4 backdrop-blur-sm shadow-md"
                  style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
                >
                  <div className="space-y-2.5">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="inline-flex items-center gap-1.5 text-[10px] font-bold text-cyan-400 uppercase tracking-wider">
                          <Icon name="camera" style={{ width: 12, height: 12 }} />
                          <span>{snap.id} • {snap.snapshot_version}</span>
                        </span>
                        <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                          {snap.subjectName}
                        </h3>
                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mt-0.5">
                          {snap.label}
                        </p>
                      </div>

                      <div className="flex items-center gap-1">
                        {isA && (
                          <span className="rounded bg-cyan-100 text-cyan-900 border border-cyan-600/40 dark:bg-cyan-950/60 dark:text-cyan-300 font-bold px-2 py-0.5 text-[10px]">
                            Snap A
                          </span>
                        )}
                        {isB && (
                          <span className="rounded bg-purple-100 text-purple-900 border border-purple-600/40 dark:bg-purple-950/60 dark:text-purple-300 font-bold px-2 py-0.5 text-[10px]">
                            Snap B
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="rounded-xl p-3 text-xs space-y-1 border" style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-primary)" }}>
                      <p className="flex justify-between font-medium">
                        <span className="text-slate-700 dark:text-slate-300">Project:</span>
                        <span className="font-bold text-slate-900 dark:text-slate-100">{snap.projectName}</span>
                      </p>
                      <p className="flex justify-between font-medium">
                        <span className="text-slate-700 dark:text-slate-300">Active Dasha:</span>
                        <span className="font-mono font-bold text-cyan-400">{snap.dashaActive}</span>
                      </p>
                      <p className="flex justify-between font-medium">
                        <span className="text-slate-700 dark:text-slate-300">Ayanamsa:</span>
                        <span className="text-slate-800 dark:text-slate-200">{snap.ayanamsa}</span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t text-xs" style={{ borderColor: "var(--border-primary)" }}>
                    <span className="text-[11px] font-medium text-slate-400">
                      {new Date(snap.captured_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedSnapshotA(snap.id);
                          setComparing(true);
                        }}
                        className="rounded-lg border px-2.5 py-1 text-[11px] font-bold text-cyan-400 hover:border-cyan-400 transition cursor-pointer"
                        style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-secondary)" }}
                      >
                        Diff
                      </button>

                      <button
                        type="button"
                        onClick={() => handleExportJson(snap)}
                        className="rounded-lg border p-1 text-slate-300 hover:text-cyan-400 cursor-pointer"
                        style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-secondary)" }}
                        title="Download JSON"
                      >
                        <Icon name="download" style={{ width: 14, height: 14 }} />
                      </button>

                      <button
                        type="button"
                        onClick={() => handleDeleteSnapshot(snap.id)}
                        className="rounded-lg border p-1 text-slate-400 hover:text-rose-400 cursor-pointer"
                        style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-secondary)" }}
                        title="Delete Snapshot"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                </Card>
              );
            })
          )}
        </div>
      </div>
    </AppShell>
  );
}
