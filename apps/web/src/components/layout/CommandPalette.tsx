"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen((o) => !o);
      }
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (!isOpen) return null;

  const navigate = (path: string) => {
    setIsOpen(false);
    setSearch("");
    router.push(path);
  };

  const commands = [
    { label: "Dashboard", path: "/dashboard", section: "Navigation" },
    { label: "Phalita MoE AI", path: "/phalita", section: "Navigation" },
    { label: "Research Patterns", path: "/research/patterns", section: "Navigation" },
    { label: "Chart Library", path: "/charts/history", section: "Navigation" },
    { label: "Transits", path: "/charts/transit", section: "Navigation" },
  ].filter((c) => c.label.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-slate-900/50 backdrop-blur-sm" onClick={() => setIsOpen(false)}>
      <div 
        className="w-full max-w-xl rounded-xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden" 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="border-b border-slate-700 p-3">
          <input
            autoFocus
            className="w-full bg-transparent px-3 py-2 text-lg text-slate-100 placeholder:text-slate-500 focus:outline-none"
            placeholder="Search commands... (e.g., Dashboard, Transits)"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        
        <div className="max-h-[60vh] overflow-y-auto p-2">
          {commands.length > 0 ? (
            commands.map((cmd) => (
              <button
                key={cmd.label}
                className="w-full rounded-md px-4 py-3 text-left text-sm text-slate-300 hover:bg-slate-800 hover:text-amber-400 focus:bg-slate-800 focus:text-amber-400 focus:outline-none transition-colors flex items-center justify-between"
                onClick={() => navigate(cmd.path)}
              >
                <span>{cmd.label}</span>
                <span className="text-xs text-slate-500">{cmd.section}</span>
              </button>
            ))
          ) : (
            <p className="p-4 text-center text-sm text-slate-500">No results found.</p>
          )}
        </div>
        <div className="border-t border-slate-800 bg-slate-900/50 p-2 text-center text-xs text-slate-500">
          Press <kbd className="rounded border border-slate-700 bg-slate-800 px-1 font-sans">Esc</kbd> to close
        </div>
      </div>
    </div>
  );
}
