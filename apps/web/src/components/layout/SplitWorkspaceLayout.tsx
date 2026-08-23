"use client";

import React, { useState, useEffect } from "react";
import { useWorkflowStore } from "@/lib/store";

export function SplitWorkspaceLayout({
  children,
  title,
  subtitle,
}: {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
}) {
  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);
  const setRequest = useWorkflowStore((s) => s.setRequest);

  const [leftWidth, setLeftWidth] = useState(() => {
    if (typeof window === "undefined") return 280;
    try {
      const stored = localStorage.getItem("workspace:subject_width");
      const parsed = stored ? parseInt(stored, 10) : 280;
      return isNaN(parsed) ? 280 : Math.max(160, Math.min(450, parsed));
    } catch {
      return 280;
    }
  });

  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    try {
      return localStorage.getItem("workspace:subject_collapsed") === "true";
    } catch {
      return false;
    }
  });

  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (!request && typeof window !== "undefined") {
      const stored = localStorage.getItem("astroos_active_chart_request");
      if (stored) {
        try {
          setRequest(JSON.parse(stored));
        } catch {
          // ignore
        }
      }
    }
  }, [request, setRequest]);

  const toggleCollapse = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("workspace:subject_collapsed", String(next));
      } catch {}
      return next;
    });
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    setIsDragging(true);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    const newWidth = e.clientX - 250; // offset approx left sidebar width
    if (newWidth >= 160 && newWidth <= 450) {
      setLeftWidth(newWidth);
      if (isCollapsed) setIsCollapsed(false);
    }
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (isDragging) {
      setIsDragging(false);
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
        localStorage.setItem("workspace:subject_width", String(leftWidth));
      } catch {}
    }
  };

  return (
    <div className="flex h-full w-full overflow-hidden bg-slate-50 dark:bg-slate-950 relative select-none">
      {/* ── Left Column: Native Info Profile ── */}
      {!isCollapsed && (
        <div
          style={{ width: `${leftWidth}px` }}
          className="flex-shrink-0 border-r border-slate-200 dark:border-slate-800 p-3 overflow-y-auto bg-white/70 dark:bg-slate-900/60 backdrop-blur-sm transition-none flex flex-col justify-between"
        >
          <div>
            <div className="mb-3 flex items-center justify-between gap-1">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Native Info
              </h2>
              <button
                type="button"
                onClick={toggleCollapse}
                className="rounded px-2 py-0.5 text-[10px] font-bold text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100 transition cursor-pointer"
                title="Hide Native Info Column to maximize main workspace space"
              >
                ◀ Hide Info
              </button>
            </div>

            {request ? (
              <div className="space-y-3">
                <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3.5 shadow-sm">
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">{request.subject_name || "Active Chart"}</h3>
                  <p className="mt-0.5 text-xs font-mono text-slate-600 dark:text-slate-400">
                    {new Date(request.birth_datetime_utc).toLocaleString()}
                  </p>
                  <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                    {request.latitude.toFixed(2)}°, {request.longitude.toFixed(2)}° · {request.place_name || request.ayanamsa}
                  </p>
                </div>

                {result && (
                  <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3.5 shadow-sm">
                    <h4 className="text-[11px] font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400">
                      Ascendant &amp; Moon
                    </h4>
                    <p className="mt-1.5 text-xs text-slate-700 dark:text-slate-300">
                      Lagna: <span className="font-semibold capitalize text-cyan-600 dark:text-cyan-400">{result.chart.ascendant.rashi}</span> ({result.chart.ascendant.nakshatra})
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-300 dark:border-slate-800 p-4 text-center">
                <p className="text-xs font-medium text-slate-700 dark:text-slate-300">No active chart loaded.</p>
                <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                  Select or create a chart to view the subject profile.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Drag Handle Divider ── */}
      {!isCollapsed && (
        <div
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onDoubleClick={() => setLeftWidth(280)}
          className={`w-1.5 relative z-20 cursor-col-resize flex-none items-center justify-center transition-colors ${
            isDragging ? "bg-cyan-400 shadow-[0_0_10px_#06b6d4]" : "hover:bg-cyan-500/40 border-r border-slate-200 dark:border-slate-800"
          }`}
          title="Drag to resize Native Info column (Double-click to reset)"
        >
          <div className="w-0.5 h-8 bg-slate-400/40 rounded-full" />
        </div>
      )}

      {/* ── Main Workspace Column ── */}
      <div className="min-w-0 flex-1 overflow-x-hidden overflow-y-auto p-3 md:p-4 bg-slate-50/50 dark:bg-slate-950">
        {isCollapsed && (
          <div className="mb-3 flex items-center">
            <button
              type="button"
              onClick={toggleCollapse}
              className="flex items-center gap-1.5 rounded-lg border border-cyan-500/30 bg-cyan-950/40 px-3 py-1 text-xs font-bold text-cyan-400 hover:bg-cyan-500/20 transition cursor-pointer shadow-sm"
            >
              <span>👤 ▶ Show Native Info</span>
            </button>
          </div>
        )}

        {title && (
          <div className="mb-3 pb-2 border-b border-slate-200 dark:border-slate-800">
            <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100">{title}</h1>
            {subtitle && <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400">{subtitle}</p>}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}
