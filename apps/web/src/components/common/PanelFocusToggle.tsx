"use client";

import React, { useState, useEffect } from "react";

export type PanelSizingMode = "narrow" | "normal" | "wide" | "fullscreen";

interface Props {
  mode: PanelSizingMode;
  onModeChange: (mode: PanelSizingMode) => void;
  title?: string;
  className?: string;
}

export function PanelFocusToggle({ mode, onModeChange, title, className = "" }: Props) {
  return (
    <div className={`inline-flex items-center gap-1 p-1 rounded-xl border bg-slate-900/40 backdrop-blur-sm ${className}`} style={{ borderColor: "var(--border-primary)" }}>
      {title && <span className="text-[10px] font-bold text-slate-400 px-1 uppercase tracking-wider hidden sm:inline">{title}</span>}

      <button
        type="button"
        title="Narrow / Compact View"
        onClick={() => onModeChange("narrow")}
        className={`px-2 py-1 rounded-lg text-[10px] font-extrabold transition cursor-pointer ${
          mode === "narrow"
            ? "bg-cyan-500 text-slate-950 shadow-xs"
            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
        }`}
      >
        <span>⇥ Narrow</span>
      </button>

      <button
        type="button"
        title="Normal Balanced View"
        onClick={() => onModeChange("normal")}
        className={`px-2 py-1 rounded-lg text-[10px] font-extrabold transition cursor-pointer ${
          mode === "normal"
            ? "bg-cyan-500 text-slate-950 shadow-xs"
            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
        }`}
      >
        <span>Standard</span>
      </button>

      <button
        type="button"
        title="Wide / Expanded View"
        onClick={() => onModeChange("wide")}
        className={`px-2 py-1 rounded-lg text-[10px] font-extrabold transition cursor-pointer ${
          mode === "wide"
            ? "bg-cyan-500 text-slate-950 shadow-xs"
            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
        }`}
      >
        <span>Wide ↔</span>
      </button>

      <button
        type="button"
        title="Full Screen Focus Mode"
        onClick={() => onModeChange(mode === "fullscreen" ? "normal" : "fullscreen")}
        className={`px-2 py-1 rounded-lg text-[10px] font-extrabold transition cursor-pointer ${
          mode === "fullscreen"
            ? "bg-amber-500 text-slate-950 shadow-xs"
            : "text-slate-400 hover:text-amber-300 hover:bg-slate-800/50"
        }`}
      >
        <span>{mode === "fullscreen" ? "✕ Exit Focus" : "🔍 Focus"}</span>
      </button>
    </div>
  );
}
