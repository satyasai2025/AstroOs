"use client";

import React from "react";
import { useWorkflowStore } from "@/lib/store";

export function SplitWorkspaceLayout({ children }: { children: React.ReactNode }) {
  const result = useWorkflowStore((s) => s.result);
  
  return (
    <div className="flex h-full w-full overflow-hidden" style={{ backgroundColor: "var(--bg-primary)" }}>
      {/* Left Pane: Fixed 320px Sidebar */}
      <div className="w-[320px] flex-shrink-0 border-r p-4 overflow-y-auto" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-secondary)" }}>
        <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Active Subject
        </h2>
        {result ? (
          <div className="space-y-4">
            <div className="rounded-xl border p-4 shadow-sm" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
              <h3 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{result.subject.name || "Untitled Profile"}</h3>
              <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                {result.subject.birth_date} • {result.subject.birth_time}
              </p>
              <p className="mt-1 text-xs" style={{ color: "var(--text-tertiary)" }}>
                {result.subject.latitude}°, {result.subject.longitude}°
              </p>
            </div>

            <div className="rounded-xl border p-4 shadow-sm" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
              <h4 className="text-xs font-medium uppercase tracking-wider text-amber-500">
                Current Dasha
              </h4>
              <p className="mt-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                No active Dasha data loaded in store.
              </p>
            </div>

            <div className="rounded-xl border p-4 shadow-sm flex items-center justify-center h-48" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>[ Rasi Chart Graphic ]</p>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed p-6 text-center" style={{ borderColor: "var(--border-strong)", backgroundColor: "transparent" }}>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>No active chart loaded.</p>
            <p className="mt-2 text-xs" style={{ color: "var(--text-tertiary)" }}>
              Select or create a chart to view the subject profile.
            </p>
          </div>
        )}
      </div>

      {/* Right Pane: Main Content */}
      <div className="flex-1 overflow-y-auto p-6" style={{ backgroundColor: "var(--bg-primary)" }}>
        {children}
      </div>
    </div>
  );
}
