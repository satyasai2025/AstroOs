"use client";

import { useState, useCallback, useMemo } from "react";

import NavPanel from "./NavPanel";
import ResearchDashboard from "../dashboard/ResearchDashboard";
import InteractiveKundliView from "../charts/InteractiveKundliView";
import ReverseSearchView from "../dashboard/ReverseSearchView";
import ClassicalLiteratureView from "../dashboard/ClassicalLiteratureView";
import type { D1ChartResponse } from "@/lib/types";

/* ------------------------------------------------------------------ */
/*  Mock Chart Development Sample                                       */
/* ------------------------------------------------------------------ */

const MOCK_CHART: D1ChartResponse = {
  ascendant: {
    longitude: 0,
    sidereal_longitude: 0,
    rashi: "Mesha",
    rashi_degree: 0,
    nakshatra: "Ashwini",
    pada: 1,
    nakshatra_lord: "Ketu",
    sub_lord: "",
    sub_sub_lord: "",
  },
  houses: [
    { house_number: 1, longitude: 0, sidereal_longitude: 0, rashi: "Mesha", nakshatra_lord: "Ketu", sub_lord: "", sub_sub_lord: "" },
    { house_number: 2, longitude: 30, sidereal_longitude: 30, rashi: "Vrishabha", nakshatra_lord: "Venus", sub_lord: "", sub_sub_lord: "" },
    { house_number: 3, longitude: 60, sidereal_longitude: 60, rashi: "Mithuna", nakshatra_lord: "Mercury", sub_lord: "", sub_sub_lord: "" },
    { house_number: 4, longitude: 90, sidereal_longitude: 90, rashi: "Karka", nakshatra_lord: "Moon", sub_lord: "", sub_sub_lord: "" },
    { house_number: 5, longitude: 120, sidereal_longitude: 120, rashi: "Simha", nakshatra_lord: "Sun", sub_lord: "", sub_sub_lord: "" },
    { house_number: 6, longitude: 150, sidereal_longitude: 150, rashi: "Kanya", nakshatra_lord: "Mercury", sub_lord: "", sub_sub_lord: "" },
    { house_number: 7, longitude: 180, sidereal_longitude: 180, rashi: "Tula", nakshatra_lord: "Venus", sub_lord: "", sub_sub_lord: "" },
    { house_number: 8, longitude: 210, sidereal_longitude: 210, rashi: "Vrischika", nakshatra_lord: "Mars", sub_lord: "", sub_sub_lord: "" },
    { house_number: 9, longitude: 240, sidereal_longitude: 240, rashi: "Dhanu", nakshatra_lord: "Jupiter", sub_lord: "", sub_sub_lord: "" },
    { house_number: 10, longitude: 270, sidereal_longitude: 270, rashi: "Makara", nakshatra_lord: "Saturn", sub_lord: "", sub_sub_lord: "" },
    { house_number: 11, longitude: 300, sidereal_longitude: 300, rashi: "Kumbha", nakshatra_lord: "Saturn", sub_lord: "", sub_sub_lord: "" },
    { house_number: 12, longitude: 330, sidereal_longitude: 330, rashi: "Meena", nakshatra_lord: "Jupiter", sub_lord: "", sub_sub_lord: "" },
  ],
  planets: [
    { planet: "Sun", sidereal_longitude: 280, rashi: "Makara", rashi_degree: 10.0, house_number: 10, nakshatra: "Sravana", pada: 2, is_retrograde: false, is_combust: false, combustion_orb: null, dignity: "exalted", nakshatra_lord: "Venus", sub_lord: "", sub_sub_lord: "", rashi_house_number: 10 },
    { planet: "Moon", sidereal_longitude: 50, rashi: "Mithuna", rashi_degree: 20.0, house_number: 3, nakshatra: "Mrigashira", pada: 1, is_retrograde: false, is_combust: false, combustion_orb: null, dignity: "own_sign", nakshatra_lord: "Mars", sub_lord: "", sub_sub_lord: "", rashi_house_number: 3 },
    { planet: "Mars", sidereal_longitude: 90, rashi: "Karka", rashi_degree: 0.0, house_number: 4, nakshatra: "Pushya", pada: 1, is_retrograde: false, is_combust: false, combustion_orb: null, dignity: "friendly", nakshatra_lord: "Saturn", sub_lord: "", sub_sub_lord: "", rashi_house_number: 4 },
    { planet: "Mercury", sidereal_longitude: 100, rashi: "Karka", rashi_degree: 10.0, house_number: 4, nakshatra: "Pushya", pada: 2, is_retrograde: false, is_combust: false, combustion_orb: null, dignity: "neutral", nakshatra_lord: "Saturn", sub_lord: "", sub_sub_lord: "", rashi_house_number: 4 },
    { planet: "Jupiter", sidereal_longitude: 120, rashi: "Karka", rashi_degree: 0.0, house_number: 4, nakshatra: "Pushya", pada: 3, is_retrograde: true, is_combust: false, combustion_orb: null, dignity: "own_sign", nakshatra_lord: "Moon", sub_lord: "", sub_sub_lord: "", rashi_house_number: 4 },
    { planet: "Venus", sidereal_longitude: 210, rashi: "Vrischika", rashi_degree: 0.0, house_number: 8, nakshatra: "Anuradha", pada: 1, is_retrograde: false, is_combust: false, combustion_orb: null, dignity: "enemy", nakshatra_lord: "Saturn", sub_lord: "", sub_sub_lord: "", rashi_house_number: 8 },
    { planet: "Saturn", sidereal_longitude: 300, rashi: "Kumbha", rashi_degree: 0.0, house_number: 11, nakshatra: "Shatabhisha", pada: 1, is_retrograde: true, is_combust: false, combustion_orb: null, dignity: "own_sign", nakshatra_lord: "Rahu", sub_lord: "", sub_sub_lord: "", rashi_house_number: 11 },
    { planet: "Rahu", sidereal_longitude: 140, rashi: "Simha", rashi_degree: 20.0, house_number: 5, nakshatra: "Magha", pada: 1, is_retrograde: false, is_combust: false, combustion_orb: null, dignity: null, nakshatra_lord: "Ketu", sub_lord: "", sub_sub_lord: "", rashi_house_number: 5 },
    { planet: "Ketu", sidereal_longitude: 320, rashi: "Kumbha", rashi_degree: 20.0, house_number: 11, nakshatra: "Shatabhisha", pada: 3, is_retrograde: false, is_combust: false, combustion_orb: null, dignity: null, nakshatra_lord: "Rahu", sub_lord: "", sub_sub_lord: "", rashi_house_number: 11 },
  ],
  aspects: [
    { from_planet: "Sun", to_planet: "Moon", aspect_type: "trine", orb_degrees: 3.2, is_applying: false },
    { from_planet: "Mars", to_planet: "Jupiter", aspect_type: "trine", orb_degrees: 0.8, is_applying: true },
    { from_planet: "Saturn", to_planet: "Moon", aspect_type: "square", orb_degrees: 2.1, is_applying: true },
    { from_planet: "Mercury", to_planet: "Venus", aspect_type: "conjunction", orb_degrees: 0.5, is_applying: true },
  ],
  planet_strengths: [
    { planet: "Sun", dignity: "exalted", is_retrograde: false, is_combust: false, house_number: 10, is_in_own_sign: false, is_exalted: true, is_debilitated: false, is_in_kendra: true, is_in_trikona: false, is_in_dusthana: false, strength_score: 9.2 },
    { planet: "Moon", dignity: "own_sign", is_retrograde: false, is_combust: false, house_number: 3, is_in_own_sign: true, is_exalted: false, is_debilitated: false, is_in_kendra: false, is_in_trikona: true, is_in_dusthana: false, strength_score: 7.8 },
    { planet: "Mars", dignity: "friendly", is_retrograde: false, is_combust: false, house_number: 4, is_in_own_sign: false, is_exalted: false, is_debilitated: false, is_in_kendra: true, is_in_trikona: false, is_in_dusthana: false, strength_score: 6.5 },
    { planet: "Mercury", dignity: "neutral", is_retrograde: false, is_combust: false, house_number: 4, is_in_own_sign: false, is_exalted: false, is_debilitated: false, is_in_kendra: true, is_in_trikona: false, is_in_dusthana: false, strength_score: 5.2 },
    { planet: "Jupiter", dignity: "own_sign", is_retrograde: true, is_combust: false, house_number: 4, is_in_own_sign: true, is_exalted: false, is_debilitated: false, is_in_kendra: true, is_in_trikona: false, is_in_dusthana: false, strength_score: 5.8 },
    { planet: "Venus", dignity: "enemy", is_retrograde: false, is_combust: false, house_number: 8, is_in_own_sign: false, is_exalted: false, is_debilitated: false, is_in_kendra: false, is_in_trikona: false, is_in_dusthana: true, strength_score: 3.1 },
    { planet: "Saturn", dignity: "own_sign", is_retrograde: true, is_combust: false, house_number: 11, is_in_own_sign: true, is_exalted: false, is_debilitated: false, is_in_kendra: false, is_in_trikona: false, is_in_dusthana: false, strength_score: 6.0 },
    { planet: "Rahu", dignity: null, is_retrograde: false, is_combust: false, house_number: 5, is_in_own_sign: false, is_exalted: false, is_debilitated: false, is_in_kendra: false, is_in_trikona: true, is_in_dusthana: false, strength_score: 4.5 },
    { planet: "Ketu", dignity: null, is_retrograde: false, is_combust: false, house_number: 11, is_in_own_sign: false, is_exalted: false, is_debilitated: false, is_in_kendra: false, is_in_trikona: false, is_in_dusthana: false, strength_score: 4.0 },
  ],
  panchanga: {
    tithi: { number: 2, name: "Tritiya", paksha: "Shukla", completion_percent: 15.4 },
    nakshatra: {
      nakshatra: "Pushya",
      nakshatra_number: 8,
      pada: 2,
      lord: "Saturn",
      degree_in_nakshatra: 17.8,
      degree_in_pada: 8.9,
    },
    yoga: { number: 13, name: "Vyaghata", completion_percent: 55.0 },
    karana: { number: 2, name: "Bava", is_fixed: false },
    vara: { number: 3, name: "Buddha", lord: "Moon" },
    julian_day: 2458000.5,
    ayanamsa_deg: 24.0821,
  },
  ayanamsa_system: "lahiri",
  house_system: "W",
  julian_day: 2458000.5,
};

function PlaceholderView({ module, title }: { module: string; title: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <div className="obsidian-icon-bg mb-6 flex h-20 w-20 items-center justify-center rounded-2xl" style={{ backgroundColor: "var(--obsidian-border)", color: "var(--obsidian-accent-primary)" }}>
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
          <path d="m6 6 2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" />
        </svg>
      </div>
      <h2 className="text-xl font-bold mb-2" style={{ color: "var(--obsidian-text-primary)" }}>{title}</h2>
      <p className="text-sm max-w-md" style={{ color: "var(--obsidian-text-secondary)" }}>
        Module <span style={{ color: "var(--obsidian-accent-primary)" }}>{module}</span> — coming soon.
      </p>
      <div className="mt-6 rounded-lg border px-4 py-3 text-xs" style={{ borderColor: "var(--obsidian-border)", color: "var(--obsidian-text-muted)" }}>
        Expected: Q4 2026 · AstroOS v2.4+
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  View ID → Component registry                                        */
/* ------------------------------------------------------------------ */

type ViewId = keyof typeof VIEW_COMPONENTS;

const VIEW_COMPONENTS = {
  // Dashboard
  "research-dashboard": ResearchDashboard,
  "dashboard-executive": () => <PlaceholderView module="02" title="Executive Dashboard" />,
  "dashboard-notifications": () => <PlaceholderView module="02" title="Notifications" />,
  "dashboard-timeline": () => <PlaceholderView module="02" title="Timeline" />,

  // Authentication
  "auth-signin": () => <PlaceholderView module="01" title="Sign In" />,
  "auth-register": () => <PlaceholderView module="01" title="Register" />,

  // Chart Management
  "chart-library": () => <PlaceholderView module="03" title="Chart Library" />,
  "chart-new": () => <PlaceholderView module="03" title="New Chart" />,
  "chart-import": () => <PlaceholderView module="03" title="Import Chart" />,
  "chart-compare": () => <PlaceholderView module="03" title="Compare Charts" />,
  "chart-collections": () => <PlaceholderView module="03" title="Collections" />,

  // Chart Workspace
  "workspace-kundli": () => <InteractiveKundliView chart={MOCK_CHART} />,
  "workspace-planets": () => <PlaceholderView module="04" title="Planet Explorer" />,
  "workspace-houses": () => <PlaceholderView module="04" title="House Explorer" />,
  "workspace-divisional": () => <PlaceholderView module="04" title="Divisional Charts" />,
  "workspace-relationships": () => <PlaceholderView module="04" title="Planet Relationship Graph" />,

  // Analysis
  "analysis-dasha": () => <PlaceholderView module="05" title="Dasha Analysis" />,
  "analysis-transit": () => <PlaceholderView module="05" title="Transit Analysis" />,
  "analysis-yogas": () => <PlaceholderView module="05" title="Yogas & Combinations" />,
  "analysis-ashtakavarga": () => <PlaceholderView module="05" title="Ashtakavarga" />,
  "analysis-shadbala": () => <PlaceholderView module="05" title="Shadbala" />,
  "analysis-kp": () => <PlaceholderView module="05" title="KP Analysis" />,
  "analysis-jaimini": () => <PlaceholderView module="05" title="Jaimini Analysis" />,

  // AI
  "ai-explain": () => <PlaceholderView module="06" title="AI Explain" />,
  "ai-chat": () => <PlaceholderView module="06" title="AI Chat" />,
  "ai-confidence": () => <PlaceholderView module="06" title="Confidence Scores" />,
  "ai-evidence": () => <PlaceholderView module="06" title="Evidence Chain" />,

  // Research
  "research-explorer": () => <PlaceholderView module="07" title="Research Explorer" />,
  "research-reverse-search": () => <ReverseSearchView />,
  "research-patterns": () => <PlaceholderView module="07" title="Pattern Discovery" />,
  "research-knowledge-graph": () => <PlaceholderView module="07" title="Knowledge Graph" />,
  "research-notebook": () => <PlaceholderView module="07" title="Notebook" />,

  // Knowledge Base
  "kb-bphs": () => <ClassicalLiteratureView />,
  "kb-saravali": () => <ClassicalLiteratureView />,
  "kb-rules": () => <PlaceholderView module="08" title="Rule Explorer" />,
  "kb-literature": () => <ClassicalLiteratureView />,
  "kb-citations": () => <PlaceholderView module="08" title="Citations" />,

  // Life Events
  "life-marriage": () => <PlaceholderView module="09" title="Marriage Timing" />,
  "life-career": () => <PlaceholderView module="09" title="Career Analysis" />,
  "life-health": () => <PlaceholderView module="09" title="Health & Longevity" />,
  "life-timeline": () => <PlaceholderView module="09" title="Life Timeline" />,

  // Reports
  "reports-pdf": () => <PlaceholderView module="10" title="PDF Reports" />,
  "reports-ai": () => <PlaceholderView module="10" title="AI Reports" />,
  "reports-comparison": () => <PlaceholderView module="10" title="Comparison Reports" />,
  "reports-export": () => <PlaceholderView module="10" title="Export" />,

  // Administration
  "admin-rules": () => <PlaceholderView module="11" title="Rules Engine" />,
  "admin-literature": () => <PlaceholderView module="11" title="Literature Admin" />,
  "admin-plugins": () => <PlaceholderView module="11" title="Plugins" />,
  "admin-audit": () => <PlaceholderView module="11" title="Audit & Logs" />,
  "admin-health": () => <PlaceholderView module="11" title="System Health" />,

  // Settings
  "settings-profile": () => <PlaceholderView module="12" title="Profile Settings" />,
  "settings-theme": () => <PlaceholderView module="12" title="Theme Settings" />,
  "settings-security": () => <PlaceholderView module="12" title="Security Settings" />,
  "settings-preferences": () => <PlaceholderView module="12" title="Preferences" />,
};

/* ------------------------------------------------------------------ */
/*  Main Workspace Component                                           */
/* ------------------------------------------------------------------ */

const DEFAULT_VIEW: ViewId = "research-dashboard";

export default function ResearchWorkspace() {
  const [currentView, setCurrentView] = useState<ViewId>(DEFAULT_VIEW);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleNavigate = useCallback((viewId: string) => {
    if (viewId in VIEW_COMPONENTS) {
      setCurrentView(viewId as ViewId);
    }
  }, []);

  const CurrentViewComponent = useMemo(() => VIEW_COMPONENTS[currentView], [currentView]);

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: "var(--obsidian-canvas)" }}>
      {/* ── Sidebar ── */}
      <div className="flex-shrink-0 transition-all duration-200" style={{ width: sidebarCollapsed ? "56px" : "288px" }}>
        <NavPanel
          onNavigate={handleNavigate}
          currentView={currentView}
          collapsed={sidebarCollapsed}
        />
      </div>

      {/* ── Main Canvas ── */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Top bar */}
        <header
          className="flex items-center justify-between border-b px-4 py-2"
          style={{ borderColor: "var(--obsidian-border)", backgroundColor: "var(--obsidian-surface)" }}
        >
          <button
            type="button"
            onClick={() => setSidebarCollapsed((v) => !v)}
            className="theme-toggle flex h-8 w-8 items-center justify-center rounded transition-colors"
            style={{ color: "var(--obsidian-text-secondary)" }}
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {sidebarCollapsed ? <path d="M15 18l-6-6 6-6" /> : <path d="M9 18l6-6-6-6" />}
            </svg>
          </button>
          <div className="flex-1 px-3">
            <span className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--obsidian-text-muted)" }}>
              {currentView.split("-").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" / ")}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className="obsidian-icon-bg flex h-6 w-6 items-center justify-center rounded text-[10px]"
              style={{ backgroundColor: "var(--obsidian-status-success-bg)", color: "var(--obsidian-status-success)" }}
            >
              ?
            </span>
            <span className="text-xs font-medium" style={{ color: "var(--obsidian-text-secondary)" }}>User</span>
          </div>
        </header>

        {/* Content area */}
        <main id="research-main-canvas" className="flex-1 overflow-y-auto" style={{ backgroundColor: "var(--obsidian-canvas)" }}>
          <CurrentViewComponent />
        </main>
      </div>
    </div>
  );
}
