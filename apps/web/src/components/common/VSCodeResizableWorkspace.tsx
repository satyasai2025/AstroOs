"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";

interface VSCodeResizableWorkspaceProps {
  initialSidebarWidth?: number;
  initialTerminalHeight?: number;
  minSidebarWidth?: number;
  maxSidebarWidth?: number;
  minTerminalHeight?: number;
  maxTerminalHeight?: number;
  sidebarContent?: React.ReactNode;
  mainContent?: React.ReactNode;
  terminalContent?: React.ReactNode;
  title?: string;
}

export function VSCodeResizableWorkspace({
  initialSidebarWidth = 280,
  initialTerminalHeight = 220,
  minSidebarWidth = 160,
  maxSidebarWidth = 550,
  minTerminalHeight = 80,
  maxTerminalHeight = 500,
  sidebarContent,
  mainContent,
  terminalContent,
  title = "AstroOS VS Code Split Workspace",
}: VSCodeResizableWorkspaceProps) {
  const [sidebarWidth, setSidebarWidth] = useState(initialSidebarWidth);
  const [terminalHeight, setTerminalHeight] = useState(initialTerminalHeight);

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isTerminalCollapsed, setIsTerminalCollapsed] = useState(false);

  const [isDraggingSidebar, setIsDraggingSidebar] = useState(false);
  const [isDraggingTerminal, setIsDraggingTerminal] = useState(false);
  const [activeTerminalTab, setActiveTerminalTab] = useState<"terminal" | "output" | "evidence" | "problems">("terminal");

  const containerRef = useRef<HTMLDivElement>(null);

  // ── Vertical Drag Divider (Sidebar Width Resizing) ──
  const handleSidebarPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    const target = e.currentTarget;
    target.setPointerCapture(e.pointerId);
    setIsDraggingSidebar(true);
  };

  const handleSidebarPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDraggingSidebar || !containerRef.current) return;
    const containerRect = containerRef.current.getBoundingClientRect();
    const newWidth = e.clientX - containerRect.left;
    if (newWidth >= minSidebarWidth && newWidth <= maxSidebarWidth) {
      setSidebarWidth(newWidth);
      if (isSidebarCollapsed) setIsSidebarCollapsed(false);
    }
  };

  const handleSidebarPointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (isDraggingSidebar) {
      setIsDraggingSidebar(false);
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
      } catch (err) {
        // ignore fallback
      }
    }
  };

  // ── Horizontal Drag Divider (Terminal Height Resizing) ──
  const handleTerminalPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    const target = e.currentTarget;
    target.setPointerCapture(e.pointerId);
    setIsDraggingTerminal(true);
  };

  const handleTerminalPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDraggingTerminal || !containerRef.current) return;
    const containerRect = containerRef.current.getBoundingClientRect();
    const newHeight = containerRect.bottom - e.clientY;
    if (newHeight >= minTerminalHeight && newHeight <= maxTerminalHeight) {
      setTerminalHeight(newHeight);
      if (isTerminalCollapsed) setIsTerminalCollapsed(false);
    }
  };

  const handleTerminalPointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (isDraggingTerminal) {
      setIsDraggingTerminal(false);
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
      } catch (err) {
        // ignore fallback
      }
    }
  };

  // Prevent text selection while dragging
  useEffect(() => {
    if (isDraggingSidebar || isDraggingTerminal) {
      document.body.style.userSelect = "none";
      document.body.style.cursor = isDraggingSidebar ? "col-resize" : "row-resize";
    } else {
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
    }
  }, [isDraggingSidebar, isDraggingTerminal]);

  return (
    <div
      ref={containerRef}
      className="relative flex flex-col h-[750px] w-full rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-900 text-slate-100 shadow-2xl overflow-hidden font-sans select-none"
    >
      {/* ── Top Window Status Bar (VS Code Header) ── */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-slate-950/90 text-xs font-semibold">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500/80 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block"></span>
          </div>
          <span className="text-slate-400 font-mono text-[11px] ml-2">AstroOS Workspace</span>
          <span className="text-slate-600">/</span>
          <span className="text-slate-200 font-bold">{title}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsSidebarCollapsed((prev) => !prev)}
            className={`px-2 py-1 rounded text-[11px] font-mono transition cursor-pointer ${
              isSidebarCollapsed ? "bg-cyan-500/20 text-cyan-400" : "bg-slate-800 text-slate-300 hover:text-slate-100"
            }`}
          >
            {isSidebarCollapsed ? "▸ Show Sidebar" : "◂ Sidebar"}
          </button>
          <button
            type="button"
            onClick={() => setIsTerminalCollapsed((prev) => !prev)}
            className={`px-2 py-1 rounded text-[11px] font-mono transition cursor-pointer ${
              isTerminalCollapsed ? "bg-amber-500/20 text-amber-400" : "bg-slate-800 text-slate-300 hover:text-slate-100"
            }`}
          >
            {isTerminalCollapsed ? "▴ Show Terminal" : "▾ Terminal"}
          </button>
        </div>
      </div>

      {/* ── Main Split View Body (Sidebar + Right Workspace) ── */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* PANEL 1: SIDEBAR (Left) */}
        {!isSidebarCollapsed && (
          <div
            style={{ width: `${sidebarWidth}px` }}
            className="flex-none flex flex-col border-r border-slate-800 bg-slate-950/60 overflow-hidden transition-none"
          >
            <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800 text-[11px] font-extrabold uppercase text-slate-400 tracking-wider">
              <span>EXPLORER / QUERY PANELS</span>
              <span className="text-slate-500 font-mono text-[10px]">{Math.round(sidebarWidth)}px</span>
            </div>

            <div className="flex-1 overflow-y-auto p-3 text-xs space-y-3 custom-scrollbar">
              {sidebarContent || (
                <div className="space-y-2">
                  <div className="p-2.5 rounded-xl border border-slate-800 bg-slate-900/80">
                    <span className="text-[10px] text-cyan-400 uppercase font-bold block font-mono">✦ Active Prashna Query</span>
                    <p className="text-slate-200 font-semibold mt-1 text-xs">&ldquo;Will I get selected for this job?&rdquo;</p>
                  </div>

                  <div className="p-2.5 rounded-xl border border-slate-800 bg-slate-900/80 space-y-1.5 text-[11px]">
                    <span className="text-[10px] text-amber-400 uppercase font-bold block font-mono">🪐 Planetary Positions</span>
                    <div className="flex justify-between text-slate-300">
                      <span>Lagna (Asc)</span>
                      <strong className="text-cyan-300 font-mono">Virgo 21°13&apos;</strong>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Moon (Chandra)</span>
                      <strong className="text-amber-300 font-mono">Pushya 04°22&apos;</strong>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Sun (Surya)</span>
                      <strong className="text-emerald-300 font-mono">Leo 05°40&apos;</strong>
                    </div>
                  </div>

                  <div className="p-2.5 rounded-xl border border-slate-800 bg-slate-900/80 text-[11px] space-y-1">
                    <span className="text-[10px] text-emerald-400 uppercase font-bold block font-mono">🎯 KP Horary Seed</span>
                    <div className="text-slate-200 font-bold font-mono text-xs">KP 249 System → Seed #14</div>
                    <p className="text-slate-400 text-[10px]">Cuspal Sub Lord: Venus (Sub of Mars)</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── DRAG HANDLE 1: VERTICAL SPLIT DIVIDER (Between Sidebar & Main) ── */}
        {!isSidebarCollapsed && (
          <div
            onPointerDown={handleSidebarPointerDown}
            onPointerMove={handleSidebarPointerMove}
            onPointerUp={handleSidebarPointerUp}
            className={`w-1.5 relative z-20 cursor-col-resize flex-none hover:bg-cyan-500 transition-colors ${
              isDraggingSidebar ? "bg-cyan-400 shadow-[0_0_12px_#06b6d4]" : "bg-slate-800/80"
            }`}
            title="Drag horizontally to resize sidebar width"
          >
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-40">
              <div className="w-0.5 h-6 bg-slate-400 rounded-full"></div>
            </div>
          </div>
        )}

        {/* RIGHT AREA (Main Editor + Terminal) */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* PANEL 2: MAIN EDITOR / WORKSPACE (Top Right) */}
          <div className="flex-1 flex flex-col min-h-0 bg-slate-900/40 overflow-y-auto custom-scrollbar p-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
              <div className="flex items-center gap-2">
                <span className="text-cyan-400 font-bold text-xs">📄 HoraryAnalysisEngine.tsx</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 font-mono">React 19 / TS</span>
              </div>
              <span className="text-[11px] text-slate-500 font-mono">Main Editor Workspace</span>
            </div>

            {mainContent || (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-2">
                    <span className="text-xs font-bold text-cyan-400 uppercase font-mono">✦ Horary Verdict &amp; Confidence</span>
                    <div className="flex items-center gap-3">
                      <span className="text-3xl font-extrabold text-emerald-400 font-mono">92%</span>
                      <div>
                        <div className="text-xs font-extrabold text-emerald-300 uppercase tracking-wider">VERDICT: YES</div>
                        <span className="text-[10px] text-slate-400">Strong Cuspal Alignment</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-2">
                    <span className="text-xs font-bold text-amber-400 uppercase font-mono">☀️ Timing Window</span>
                    <div className="text-sm font-bold text-amber-300 font-mono">Oct 15 – Nov 04, 2026</div>
                    <p className="text-[11px] text-slate-400">Triggered during Jupiter Transit over 10th House Sub Lord.</p>
                  </div>
                </div>

                <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 font-mono text-xs text-slate-300 space-y-2">
                  <div className="text-cyan-400 font-bold text-xs">// KP 4-Tier Sub Lord Significator Trace</div>
                  <pre className="text-[11px] text-emerald-400 leading-relaxed overflow-x-auto bg-slate-950 p-3 rounded-lg border border-slate-800">
{`House 10 (Career): Sub Lord = Venus [Star Lord = Mars (House 2, 10)] -> Grade A
House 6 (Employment): Sub Lord = Saturn [Star Lord = Jupiter (House 6, 11)] -> Grade A
House 11 (Fulfillment): Sub Lord = Moon [Star Lord = Mercury (House 10)] -> Grade B
Rule Check: Cuspal Sub Lord of 10th does NOT signify 9th (12th from 10th). NO VETO.`}
                  </pre>
                </div>
              </div>
            )}
          </div>

          {/* ── DRAG HANDLE 2: HORIZONTAL SPLIT DIVIDER (Between Editor & Terminal) ── */}
          {!isTerminalCollapsed && (
            <div
              onPointerDown={handleTerminalPointerDown}
              onPointerMove={handleTerminalPointerMove}
              onPointerUp={handleTerminalPointerUp}
              className={`h-1.5 relative z-20 cursor-row-resize flex-none hover:bg-amber-500 transition-colors ${
                isDraggingTerminal ? "bg-amber-400 shadow-[0_0_12px_#f59e0b]" : "bg-slate-800/80"
              }`}
              title="Drag vertically to resize bottom terminal panel height"
            >
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-40">
                <div className="h-0.5 w-8 bg-slate-400 rounded-full"></div>
              </div>
            </div>
          )}

          {/* PANEL 3: BOTTOM TERMINAL / OUTPUT PANEL (Bottom Right) */}
          {!isTerminalCollapsed && (
            <div
              style={{ height: `${terminalHeight}px` }}
              className="flex-none flex flex-col border-t border-slate-800 bg-slate-950/90 overflow-hidden transition-none"
            >
              <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800 text-[11px] font-mono">
                <div className="flex items-center gap-3">
                  {(["terminal", "output", "evidence", "problems"] as const).map((tab) => (
                    <button
                      key={tab}
                      type="button"
                      onClick={() => setActiveTerminalTab(tab)}
                      className={`uppercase tracking-wider font-extrabold text-[10px] transition cursor-pointer ${
                        activeTerminalTab === tab
                          ? "text-amber-400 border-b-2 border-amber-400 pb-0.5"
                          : "text-slate-500 hover:text-slate-300"
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500">{Math.round(terminalHeight)}px</span>
                  <button
                    type="button"
                    onClick={() => setIsTerminalCollapsed(true)}
                    className="text-slate-400 hover:text-slate-100 text-xs px-1"
                  >
                    ✕
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-3 font-mono text-[11px] text-slate-300 space-y-1.5 custom-scrollbar">
                {terminalContent || (
                  <>
                    {activeTerminalTab === "terminal" && (
                      <div className="space-y-1 text-slate-300">
                        <div className="text-emerald-400 font-bold">$ astroos calculate-prashna --seed=14 --system=kp_249</div>
                        <div className="text-slate-400">[INFO] Swiss Ephemeris sidereal mode set to Lahiri (Ayanamsha: 24°10&apos;12&quot;)</div>
                        <div className="text-cyan-400">[CALC] Computed 40 Classical Sahams &amp; 12 Placidus Cusps in 4.2ms</div>
                        <div className="text-emerald-400">[SUCCESS] Horary verdict evaluation completed: 92% YES</div>
                      </div>
                    )}
                    {activeTerminalTab === "output" && (
                      <div className="text-slate-400 space-y-1">
                        <div>[LOG] Server process running on localhost:3000</div>
                        <div>[LOG] Prashna Engine ready with 249 KP Seeds</div>
                      </div>
                    )}
                    {activeTerminalTab === "evidence" && (
                      <div className="text-amber-300 space-y-1">
                        <div>Evidence 1: Lagna Lord Moon conjunct Pushya Nakshatra Lord Saturn</div>
                        <div>Evidence 2: 10th Cuspal Sub Lord Venus connected with 2nd House Lord Mars</div>
                      </div>
                    )}
                    {activeTerminalTab === "problems" && (
                      <div className="text-slate-500">No diagnostic warnings or syntax errors found.</div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
