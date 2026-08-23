"use client";

import React from "react";
import { VSCodeResizableWorkspace } from "@/components/common/VSCodeResizableWorkspace";

export default function WorkspacePage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-extrabold text-slate-100 flex items-center gap-2">
            <span>💻</span> VS Code Resizable Split Workspace
          </h1>
          <p className="text-xs text-slate-400 font-medium">
            3-Panel Drag-to-Resize Layout (Sidebar Width + Bottom Terminal Height) with Mouse/Touch Events
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-mono">
            Zero NPM Dependencies
          </span>
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono">
            Touch + Mouse Smooth Drag
          </span>
        </div>
      </div>

      {/* Demo VS Code Workspace */}
      <VSCodeResizableWorkspace
        title="AstroOS Interactive Resizable IDE Split View"
        initialSidebarWidth={280}
        initialTerminalHeight={220}
      />
    </div>
  );
}
