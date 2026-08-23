"use client";

import React, { useState, useRef, useEffect } from "react";
import { useWorkflowStore } from "@/lib/store";

export function ResizableAIDrawer() {
  const [isOpen, setIsOpen] = useState(false);
  const [height, setHeight] = useState(320);
  const [isDragging, setIsDragging] = useState(false);
  const [activeTab, setActiveTab] = useState<"verdict" | "evidence" | "timing" | "raw">("verdict");

  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);

  const drawerRef = useRef<HTMLDivElement>(null);

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    setIsDragging(true);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    const newHeight = window.innerHeight - e.clientY;
    if (newHeight >= 100 && newHeight <= window.innerHeight * 0.85) {
      setHeight(newHeight);
      if (!isOpen) setIsOpen(true);
    }
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (isDragging) {
      setIsDragging(false);
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
      } catch (err) {}
    }
  };

  return (
    <>
      {/* Trigger Pill at Bottom Right */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="fixed bottom-3 right-6 z-40 flex items-center gap-2 rounded-full border border-cyan-500/40 bg-slate-900/90 px-3.5 py-1.5 text-xs font-extrabold text-cyan-400 shadow-xl backdrop-blur-md hover:bg-cyan-500/20 transition cursor-pointer"
      >
        <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse"></span>
        <span>✨ AI Astrologer Panel</span>
        <span className="text-[10px] text-slate-400 font-mono">{isOpen ? "▾" : "▴"}</span>
      </button>

      {/* Resizable Bottom Drawer */}
      {isOpen && (
        <div
          ref={drawerRef}
          style={{ height: `${height}px` }}
          className="fixed bottom-0 left-0 right-0 z-40 flex flex-col border-t border-slate-700/80 bg-slate-950/95 text-slate-100 shadow-2xl backdrop-blur-md select-none transition-none"
        >
          {/* ── DRAG HANDLE BAR (Top Divider) ── */}
          <div
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            className={`h-2 w-full cursor-row-resize flex items-center justify-center transition-colors ${
              isDragging ? "bg-cyan-400 shadow-[0_0_12px_#06b6d4]" : "bg-slate-800/80 hover:bg-cyan-500/60"
            }`}
            title="Drag up or down to resize AI Astrologer Drawer height"
          >
            <div className="w-10 h-1 bg-slate-400/60 rounded-full" />
          </div>

          {/* Drawer Navigation Bar */}
          <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2 bg-slate-900/90 text-xs">
            <div className="flex items-center gap-3">
              <span className="font-extrabold text-cyan-400 flex items-center gap-1.5">
                <span>✨</span> AI Predictive Engine
              </span>
              <div className="flex items-center gap-1 font-mono text-[11px]">
                {(["verdict", "evidence", "timing", "raw"] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setActiveTab(tab)}
                    className={`px-2.5 py-0.5 rounded uppercase tracking-wider font-bold transition cursor-pointer ${
                      activeTab === tab
                        ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-[10px] text-slate-500 font-mono">{Math.round(height)}px Height</span>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-slate-100 font-bold px-1 text-xs cursor-pointer"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Drawer Body Content */}
          <div className="flex-1 overflow-y-auto p-4 text-xs font-mono leading-relaxed space-y-3 custom-scrollbar text-slate-200">
            {activeTab === "verdict" && (
              <div className="space-y-3">
                <div className="p-3 rounded-xl border border-emerald-500/30 bg-emerald-950/30 text-emerald-300">
                  <span className="text-[10px] uppercase font-bold text-emerald-400 block">Horary &amp; KP Synthesis Verdict</span>
                  <div className="text-sm font-extrabold mt-0.5">VERDICT: YES (85% Confidence)</div>
                  <p className="mt-1 text-[11px] font-sans text-slate-200">
                    Primary 10th and 6th cuspal sub lords are favorably aligned with benefic aspects from Jupiter. Event fructification promised without veto negation.
                  </p>
                </div>
              </div>
            )}

            {activeTab === "evidence" && (
              <div className="space-y-2">
                <div className="text-cyan-400 font-bold">// 4-Tier Significator Evidence Trace</div>
                <div className="p-2.5 rounded bg-slate-900 border border-slate-800 text-[11px]">
                  <p>• Grade A: 10th Sub Lord Venus is in Star of Mars (House 2, 10)</p>
                  <p>• Grade A: 6th Sub Lord Saturn is in Star of Jupiter (House 6, 11)</p>
                  <p>• Grade B: Moon is in Pushya Nakshatra (Pada 4) in Lagna</p>
                </div>
              </div>
            )}

            {activeTab === "timing" && (
              <div className="space-y-2">
                <div className="text-amber-400 font-bold">// Timing Window Calculation</div>
                <div className="p-2.5 rounded bg-slate-900 border border-slate-800 text-[11px]">
                  <p>Likely Window: Oct 15, 2026 – Nov 04, 2026</p>
                  <p>Trigger: Sun transits Libra over Natal/Horary Venus Sub Lord</p>
                </div>
              </div>
            )}

            {activeTab === "raw" && (
              <div className="space-y-2">
                <div className="text-slate-400 font-bold">// Raw Calculation Payload</div>
                <pre className="p-2.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-400 overflow-x-auto">
{JSON.stringify({ horary_seed: 14, system: "kp_249", ascendant: "Virgo 21°13'", moon: "Pushya 04°22'" }, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
