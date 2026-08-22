"use client";

import React, { useState, useMemo, useEffect } from "react";
import {
  MASTER_LIFE_EVENTS_CATALOG,
  type MasterEventItem,
} from "@/lib/eventsMasterCatalog";

export function CentralEventsExplorer() {
  const [activeTab, setActiveTab] = useState<"list" | "search" | "custom">("list");
  const [selectedEventId, setSelectedEventId] = useState<string>(
    MASTER_LIFE_EVENTS_CATALOG[0]?.id ?? "competitive-exam"
  );
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("All");

  // Custom Events State (stored in localStorage)
  const [customEvents, setCustomEvents] = useState<MasterEventItem[]>([]);
  const [custName, setCustName] = useState<string>("");
  const [custMainHouse, setCustMainHouse] = useState<string>("VI");
  const [custSupporting, setCustSupporting] = useState<string>("IV, IX, XI");
  const [custDesc, setCustDesc] = useState<string>("");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("astroos_custom_events");
      if (saved) {
        setCustomEvents(JSON.parse(saved));
      }
    } catch {
      // ignore
    }
  }, []);

  const handleSaveCustomEvent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!custName.trim()) return;

    const newEvent: MasterEventItem = {
      id: `custom-${Date.now()}`,
      name: custName.trim(),
      category: "Custom Astrological Events",
      mainHouse: custMainHouse,
      supportingHouses: custSupporting
        .split(",")
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean),
      description: custDesc || "Custom user-defined life event.",
      kpFormula: `Main House ${custMainHouse} with supporting cusps ${custSupporting}.`,
    };

    const updated = [newEvent, ...customEvents];
    setCustomEvents(updated);
    try {
      localStorage.setItem("astroos_custom_events", JSON.stringify(updated));
    } catch {
      // ignore
    }

    setCustName("");
    setCustDesc("");
    setSelectedEventId(newEvent.id);
    setActiveTab("list");
  };

  const allEvents = useMemo(() => {
    return [...customEvents, ...MASTER_LIFE_EVENTS_CATALOG];
  }, [customEvents]);

  // Filtered Events
  const filteredEvents = useMemo(() => {
    return allEvents.filter((item) => {
      const matchQuery =
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.mainHouse.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.supportingHouses.some((h) =>
          h.toLowerCase().includes(searchQuery.toLowerCase())
        ) ||
        item.category.toLowerCase().includes(searchQuery.toLowerCase());

      const matchCategory =
        categoryFilter === "All" || item.category === categoryFilter;

      return matchQuery && matchCategory;
    });
  }, [allEvents, searchQuery, categoryFilter]);

  const selectedEvent = useMemo(() => {
    return (
      allEvents.find((e) => e.id === selectedEventId) ??
      filteredEvents[0] ??
      allEvents[0]
    );
  }, [allEvents, selectedEventId, filteredEvents]);

  const categories = useMemo(() => {
    const set = new Set<string>();
    allEvents.forEach((e) => set.add(e.category));
    return ["All", ...Array.from(set)];
  }, [allEvents]);

  return (
    <div className="w-full space-y-5">
      {/* Top Header Card */}
      <div
        style={{
          background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
          border: "1.5px solid #334155",
          borderRadius: "14px",
          padding: "20px 24px",
          boxShadow: "0 10px 30px rgba(0, 0, 0, 0.4)",
        }}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-bold uppercase tracking-wider mb-2">
              <span>🌟 Unified Astrological Knowledge Base</span>
              <span>•</span>
              <span>300+ Life Events Master Catalog</span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Central Life Events & Cuspal Formula Explorer
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Cross-examine exact Main House triggers and Supporting Cusps across KP, Parashari, Jaimini, and Bayesian Event Rectification.
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap gap-2 mt-6 pt-4 border-t border-slate-800">
          {[
            { id: "list", label: "📋 All Events List", count: allEvents.length },
            { id: "search", label: "🔍 Fast Search", count: filteredEvents.length },
            { id: "custom", label: "➕ Custom Events", count: customEvents.length },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id as any)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all"
              style={{
                background: activeTab === tab.id ? "rgba(59, 130, 246, 0.2)" : "#1e293b",
                border: activeTab === tab.id ? "1.5px solid #3b82f6" : "1px solid #334155",
                color: activeTab === tab.id ? "#60a5fa" : "#94a3b8",
                boxShadow: activeTab === tab.id ? "0 0 15px rgba(59, 130, 246, 0.25)" : "none",
              }}
            >
              <span>{tab.label}</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/80 text-slate-300 font-normal">
                {tab.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* --- TAB 1 & 2: LIST & SEARCH VIEW (LOKPA Split-Screen Style) --- */}
      {(activeTab === "list" || activeTab === "search") && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              placeholder="Search event name (e.g. Competitive exam, Marriage, Loss, Surgery, Debt)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:border-blue-500 outline-none"
            />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:border-blue-500 outline-none"
            >
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Split Screen Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
            {/* Left Column: Alphabetical Events List */}
            <div
              className="lg:col-span-6 rounded-xl border border-slate-800 bg-slate-900/80 p-2 overflow-hidden flex flex-col"
              style={{ maxHeight: "650px" }}
            >
              <div className="px-3 py-2 text-xs font-bold text-slate-400 border-b border-slate-800 flex justify-between">
                <span>Select Event ({filteredEvents.length} items)</span>
                <span className="text-cyan-400">Alphabetical Index</span>
              </div>
              <div className="overflow-y-auto space-y-1 p-1 flex-1 custom-scrollbar">
                {filteredEvents.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-500">
                    No matching life events found.
                  </div>
                ) : (
                  filteredEvents.map((item) => {
                    const isSelected = selectedEvent?.id === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setSelectedEventId(item.id)}
                        className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-all flex items-center justify-between group"
                        style={{
                          background: isSelected ? "rgba(59, 130, 246, 0.2)" : "transparent",
                          border: isSelected ? "1px solid #3b82f6" : "1px solid transparent",
                          color: isSelected ? "#ffffff" : "#cbd5e1",
                        }}
                      >
                        <span className="truncate pr-2 group-hover:text-blue-400 transition">
                          {item.name}
                        </span>
                        <div className="flex items-center gap-1.5 shrink-0">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                            H{item.mainHouse}
                          </span>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </div>

            {/* Right Column: Exact LOKPA-Style Details Box */}
            <div className="lg:col-span-6 space-y-4">
              {selectedEvent ? (
                <div
                  style={{
                    background: "#0f172a",
                    border: "1.5px solid #1e293b",
                    borderRadius: "14px",
                    padding: "24px",
                    boxShadow: "0 10px 30px rgba(0, 0, 0, 0.4)",
                  }}
                  className="space-y-6"
                >
                  {/* Top Header Card */}
                  <div className="border-b border-slate-800 pb-4">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 uppercase">
                      {selectedEvent.category}
                    </span>
                    <h2 className="text-xl font-bold text-white mt-1.5">
                      {selectedEvent.name}
                    </h2>
                    <p className="text-xs text-slate-300 mt-1">
                      {selectedEvent.description}
                    </p>
                  </div>

                  {/* LOKPA Style Main House & Supporting Houses Box */}
                  <div
                    style={{
                      background: "#1e293b",
                      border: "1.5px solid #334155",
                      borderRadius: "12px",
                      padding: "20px",
                    }}
                    className="space-y-3"
                  >
                    <div className="text-sm font-bold text-white tracking-wide">
                      {selectedEvent.name}
                    </div>

                    <div className="flex items-center gap-3 pt-1">
                      <span className="text-xs font-semibold text-slate-400">Main House:</span>
                      <span className="px-3 py-1 rounded bg-blue-600/20 border border-blue-500 text-blue-400 font-bold text-sm tracking-wider">
                        {selectedEvent.mainHouse}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 pt-1">
                      <span className="text-xs font-semibold text-slate-400">Supporting Houses:</span>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {selectedEvent.supportingHouses.map((h, i) => (
                          <span
                            key={i}
                            className="px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold text-xs"
                          >
                            {h}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Astrological Synthesis Details */}
                  <div className="space-y-3 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                    <div className="text-xs font-bold text-amber-400 uppercase tracking-wider">
                      📜 KP & Classical Interpretation Rule
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed m-0">
                      {selectedEvent.kpFormula}
                    </p>

                    {selectedEvent.significatorKarakas && (
                      <div className="pt-2 text-xs text-slate-400">
                        Governing Planetary Karakas:{" "}
                        <strong className="text-cyan-400">
                          {selectedEvent.significatorKarakas.join(", ")}
                        </strong>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
                  Select an event from the list to view its complete house breakdown.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* --- TAB 3: CUSTOM EVENTS BUILDER --- */}
      {activeTab === "custom" && (
        <div
          style={{
            background: "#0f172a",
            border: "1.5px solid #1e293b",
            borderRadius: "14px",
            padding: "24px",
          }}
          className="max-w-2xl mx-auto space-y-5"
        >
          <div>
            <h3 className="text-lg font-bold text-white">Create Custom Life Event</h3>
            <p className="text-xs text-slate-400 mt-1">
              Add your own proprietary astrological research events with custom Main House and Supporting Cusps.
            </p>
          </div>

          <form onSubmit={handleSaveCustomEvent} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Event Title / Description
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Cleared Bar Council Exam, Buying Luxury Yacht, Patent Grant"
                value={custName}
                onChange={(e) => setCustName(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Main Trigger House (Roman)
                </label>
                <select
                  value={custMainHouse}
                  onChange={(e) => setCustMainHouse(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 outline-none"
                >
                  {["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"].map(
                    (h) => (
                      <option key={h} value={h}>
                        House {h}
                      </option>
                    )
                  )}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Supporting Houses (Comma separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. II, XI or IV, IX, XI"
                  value={custSupporting}
                  onChange={(e) => setCustSupporting(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-white focus:border-blue-500 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Astrological Rationale & Notes
              </label>
              <textarea
                rows={3}
                placeholder="Why these houses signify this event..."
                value={custDesc}
                onChange={(e) => setCustDesc(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-xs text-white focus:border-blue-500 outline-none"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="submit"
                className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition shadow-lg shadow-blue-500/20"
              >
                Save Custom Event
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
