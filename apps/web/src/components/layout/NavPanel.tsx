"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface NavItem {
  href: string;
  label: string;
  subtitle?: string;
  icon: string;
  disabled?: boolean;
  /** Optional client-side view ID for SPA-style routing within workspace */
  viewId?: string;
}

interface NavModule {
  id: string;
  number: string;
  label: string;
  subtitle?: string;
  icon: string;
  color: string;
  items: NavItem[];
}

interface NavGroup {
  label: string;
  modules: NavModule[];
}

/* ------------------------------------------------------------------ */
/*  12-Module Navigation Map                                           */
/* ------------------------------------------------------------------ */

const NAV_GROUPS: NavGroup[] = [
  {
    label: "Core",
    modules: [
      {
        id: "auth",
        number: "01",
        label: "Authentication",
        subtitle: "Login · Register · OAuth",
        icon: "user",
        color: "--obsidian-accent-primary",
        items: [
          { href: "/login", label: "Sign In", subtitle: "Email & password", icon: "login", viewId: "auth-signin" },
          { href: "/register", label: "Register", subtitle: "Create account", icon: "register", viewId: "auth-register" },
          { href: "/forgot-password", label: "Forgot Password", icon: "key", disabled: true },
          { href: "/profile/setup", label: "Profile Setup", icon: "settings", disabled: true },
        ],
      },
      {
        id: "dashboard",
        number: "02",
        label: "Dashboard",
        subtitle: "Overview · Metrics · Activity",
        icon: "dashboard",
        color: "--obsidian-accent-primary",
        items: [
          { href: "/dashboard", label: "Executive Overview", subtitle: "KPIs & charts", icon: "chart", viewId: "dashboard-executive" },
          { href: "/research/dashboard", label: "Research Dashboard", subtitle: "Research analytics", icon: "search", viewId: "research-dashboard" },
          { href: "/dashboard/notifications", label: "Notifications", icon: "bell", disabled: true },
          { href: "/dashboard/timeline", label: "Timeline", icon: "clock", disabled: true },
        ],
      },
      {
        id: "settings",
        number: "12",
        label: "Settings",
        subtitle: "Profile · Theme · Security",
        icon: "settings",
        color: "--obsidian-text-muted",
        items: [
          { href: "/settings/profile", label: "Profile", icon: "user", viewId: "settings-profile", disabled: true },
          { href: "/settings/theme", label: "Theme", icon: "palette", viewId: "settings-theme", disabled: true },
          { href: "/settings/security", label: "Security", icon: "shield", viewId: "settings-security", disabled: true },
          { href: "/settings/preferences", label: "Preferences", icon: "settings", viewId: "settings-preferences", disabled: true },
        ],
      },
    ],
  },
  {
    label: "Charts & Analysis",
    modules: [
      {
        id: "chart-management",
        number: "03",
        label: "Chart Management",
        subtitle: "Library · Import · Compare",
        icon: "library",
        color: "#06CFFF",
        items: [
          { href: "/charts/history", label: "Chart Library", subtitle: "Browse saved charts", icon: "grid", viewId: "chart-library" },
          { href: "/dashboard", label: "New Chart", subtitle: "Create natal chart", icon: "plus", viewId: "chart-new" },
          { href: "/charts/import", label: "Import Chart", icon: "upload", disabled: true },
          { href: "/charts/compare", label: "Compare Charts", subtitle: "Side-by-side analysis", icon: "layers", viewId: "chart-compare" },
          { href: "/charts/collections", label: "Collections", icon: "folder", disabled: true },
        ],
      },
      {
        id: "chart-workspace",
        number: "04",
        label: "Chart Workspace",
        subtitle: "Kundli · Planets · Houses",
        icon: "compass",
        color: "#06CFFF",
        items: [
          { href: "/charts?view=chart", label: "Interactive Kundli", subtitle: "Birth chart visualization", icon: "compass", viewId: "workspace-kundli" },
          { href: "/charts?view=planets", label: "Planet Explorer", icon: "search", disabled: true },
          { href: "/charts?view=houses", label: "House Explorer", subtitle: "Bhava analysis", icon: "house", viewId: "workspace-houses" },
          { href: "/charts?view=divisional", label: "Divisional Charts", subtitle: "D-1 through D-60", icon: "grid", viewId: "workspace-divisional" },
          { href: "/charts?view=relationships", label: "Planet Relationships", subtitle: "Aspect graph", icon: "network", viewId: "workspace-relationships" },
        ],
      },
      {
        id: "analysis",
        number: "05",
        label: "Analysis",
        subtitle: "Dasha · Transit · Yogas",
        icon: "analysis",
        color: "#06CFFF",
        items: [
          { href: "/charts?view=dasha", label: "Dasha", subtitle: "Vimshottari periods", icon: "clock", viewId: "analysis-dasha" },
          { href: "/charts?view=timeline", label: "Transit", subtitle: "Current planetary positions", icon: "orbit", viewId: "analysis-transit" },
          { href: "/charts?view=yogas", label: "Yogas", icon: "star", disabled: true },
          { href: "/charts?view=ashtakavarga", label: "Ashtakavarga", icon: "grid", disabled: true },
          { href: "/charts?view=strength", label: "Shadbala", subtitle: "Planet strength", icon: "bar", viewId: "analysis-shadbala" },
          { href: "/charts?view=kp", label: "KP Analysis", subtitle: "Krishnamurti Paddhati", icon: "target", viewId: "analysis-kp" },
          { href: "/charts?view=jaimini", label: "Jaimini", icon: "book", disabled: true },
        ],
      },
    ],
  },
  {
    label: "Intelligence",
    modules: [
      {
        id: "ai",
        number: "06",
        label: "AI",
        subtitle: "Explain · Chat · Confidence",
        icon: "sparkle",
        color: "#8B5CF6",
        items: [
          { href: "/ai/explain", label: "AI Explain", icon: "sparkle", viewId: "ai-explain", disabled: true },
          { href: "/ai/chat", label: "AI Chat", icon: "chat", viewId: "ai-chat", disabled: true },
          { href: "/ai/confidence", label: "Confidence Scores", icon: "target", viewId: "ai-confidence", disabled: true },
          { href: "/ai/evidence", label: "Evidence Chain", icon: "chain", viewId: "ai-evidence", disabled: true },
        ],
      },
      {
        id: "research",
        number: "07",
        label: "Research",
        subtitle: "Search · Patterns · Graph",
        icon: "research",
        color: "#8B5CF6",
        items: [
          { href: "/research/reverse-search", label: "Reverse Search", icon: "search", viewId: "research-reverse-search" },
          { href: "/research/projects", label: "Research Explorer", subtitle: "Browse projects", icon: "compass", viewId: "research-explorer" },
          { href: "/research/patterns", label: "Pattern Discovery", icon: "sparkle", viewId: "research-patterns", disabled: true },
          { href: "/research/knowledge-graph", label: "Knowledge Graph", icon: "network", viewId: "research-knowledge-graph", disabled: true },
          { href: "/research/notebook", label: "Notebook", icon: "document", viewId: "research-notebook", disabled: true },
        ],
      },
      {
        id: "knowledge-base",
        number: "08",
        label: "Knowledge Base",
        subtitle: "BPHS · Saravali · Rules",
        icon: "book",
        color: "#8B5CF6",
        items: [
          { href: "/knowledge/bphs", label: "BPHS", icon: "book", viewId: "kb-bphs" },
          { href: "/knowledge/saravali", label: "Saravali", icon: "book", viewId: "kb-saravali" },
          { href: "/knowledge/rules", label: "Rule Explorer", icon: "settings", viewId: "kb-rules", disabled: true },
          { href: "/knowledge/literature", label: "Literature", icon: "document", viewId: "kb-literature" },
          { href: "/knowledge/citations", label: "Citations", icon: "link", viewId: "kb-citations", disabled: true },
        ],
      },
    ],
  },
  {
    label: "Life & Reports",
    modules: [
      {
        id: "life-events",
        number: "09",
        label: "Life Events",
        subtitle: "Marriage · Career · Health",
        icon: "heart",
        color: "#F5A623",
        items: [
          { href: "/life/marriage", label: "Marriage", icon: "heart", viewId: "life-marriage", disabled: true },
          { href: "/life/career", label: "Career", icon: "briefcase", viewId: "life-career", disabled: true },
          { href: "/life/health", label: "Health", icon: "health", viewId: "life-health", disabled: true },
          { href: "/life/timeline", label: "Timeline", icon: "clock", viewId: "life-timeline", disabled: true },
        ],
      },
      {
        id: "reports",
        number: "10",
        label: "Reports",
        subtitle: "PDF · AI · Export",
        icon: "report",
        color: "#F5A623",
        items: [
          { href: "/reports/pdf", label: "PDF Reports", icon: "document", viewId: "reports-pdf", disabled: true },
          { href: "/reports/ai", label: "AI Reports", icon: "sparkle", viewId: "reports-ai", disabled: true },
          { href: "/reports/comparison", label: "Comparison", icon: "layers", viewId: "reports-comparison", disabled: true },
          { href: "/reports/export", label: "Export", icon: "download", viewId: "reports-export", disabled: true },
        ],
      },
    ],
  },
  {
    label: "System",
    modules: [
      {
        id: "admin",
        number: "11",
        label: "Administration",
        subtitle: "Rules · Plugins · Logs",
        icon: "shield",
        color: "#5A6B80",
        items: [
          { href: "/admin/rules", label: "Rules Engine", icon: "settings", viewId: "admin-rules", disabled: true },
          { href: "/admin/literature", label: "Literature", icon: "book", viewId: "admin-literature", disabled: true },
          { href: "/admin/plugins", label: "Plugins", icon: "puzzle", viewId: "admin-plugins", disabled: true },
          { href: "/admin", label: "Audit & Logs", subtitle: "System activity", icon: "shield", viewId: "admin-audit" },
          { href: "/admin/health", label: "System Health", icon: "heart", viewId: "admin-health", disabled: true },
        ],
      },
    ],
  },
];

/* ------------------------------------------------------------------ */
/*  SVG Icon Map                                                       */
/* ------------------------------------------------------------------ */

function NavIcon({ name, className = "" }: { name: string; className?: string }) {
  const cls = className || "h-4 w-4 flex-shrink-0";
  const common = {
    width: 16,
    height: 16,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className: cls,
    "aria-hidden": true as const,
  };
  switch (name) {
    case "user":
      return <svg {...common}><circle cx="12" cy="8" r="4" /><path d="M4 21v-1a6 6 0 0 1 12 0v1" /></svg>;
    case "dashboard":
      return <svg {...common}><rect x="3" y="3" width="7" height="9" rx="1" /><rect x="14" y="3" width="7" height="5" rx="1" /><rect x="14" y="12" width="7" height="9" rx="1" /><rect x="3" y="16" width="7" height="5" rx="1" /></svg>;
    case "settings":
      return <svg {...common}><circle cx="12" cy="12" r="3" /><path d="M19.4 13a7.4 7.4 0 0 0 0-2l2-1.5-2-3.4-2.3.9a7.6 7.6 0 0 0-1.7-1L15 3.5h-4l-.4 2.5a7.6 7.6 0 0 0-1.7 1l-2.3-.9-2 3.4L6.6 11a7.4 7.4 0 0 0 0 2l-2 1.5 2 3.4 2.3-.9a7.6 7.6 0 0 0 1.7 1l.4 2.5h4l.4-2.5a7.6 7.6 0 0 0 1.7-1l2.3.9 2-3.4-2-1.5Z" /></svg>;
    case "library":
      return <svg {...common}><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" /></svg>;
    case "compass":
      return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="m15 9-2 6-6 2 2-6 6-2Z" /></svg>;
    case "analysis":
      return <svg {...common}><path d="m21 21-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z" /><path d="M10 7v6M7 10h6" /></svg>;
    case "sparkle":
      return <svg {...common}><path d="M12 3v4M12 17v4M3 12h4M17 12h4" /><path d="m6 6 2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" /></svg>;
    case "research":
      return <svg {...common}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /><path d="M11 8v6M8 11h6" /></svg>;
    case "book":
      return <svg {...common}><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Z" /><path d="M4 5.5v16" /></svg>;
    case "heart":
      return <svg {...common}><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" /></svg>;
    case "report":
      return <svg {...common}><path d="M7 3h7l5 5v13H7z" /><path d="M14 3v5h5" /><path d="M9 12h6M9 16h4" /></svg>;
    case "shield":
      return <svg {...common}><path d="M12 3 5 6v6c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6l-7-3Z" /></svg>;
    case "plus":
      return <svg {...common}><path d="M12 5v14M5 12h14" /></svg>;
    case "grid":
      return <svg {...common}><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>;
    case "layers":
      return <svg {...common}><path d="m12 3 9 5-9 5-9-5 9-5Z" /><path d="m3 13 9 5 9-5" /></svg>;
    case "upload":
      return <svg {...common}><path d="M12 16V4M6 10l6-6 6 6" /><path d="M4 20h16" /></svg>;
    case "folder":
      return <svg {...common}><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z" /></svg>;
    case "house":
      return <svg {...common}><path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8" /><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /></svg>;
    case "clock":
      return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 3" /></svg>;
    case "orbit":
      return <svg {...common}><circle cx="12" cy="12" r="2.5" /><ellipse cx="12" cy="12" rx="9" ry="4" /></svg>;
    case "star":
      return <svg {...common}><path d="m12 3 2.6 6.2L21 10l-5 4.3L17.4 21 12 17.5 6.6 21 8 14.3 3 10l6.4-.8L12 3Z" /></svg>;
    case "bar":
      return <svg {...common}><path d="M5 20V10M12 20V4M19 20v-7" /></svg>;
    case "target":
      return <svg {...common}><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="4" /><circle cx="12" cy="12" r="0.6" fill="currentColor" /></svg>;
    case "network":
      return <svg {...common}><circle cx="6" cy="6" r="2.3" /><circle cx="18" cy="6" r="2.3" /><circle cx="12" cy="18" r="2.3" /><path d="M8 7.2 16 7.2M7 8l4 8M17 8l-4 8" /></svg>;
    case "bell":
      return <svg {...common}><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" /></svg>;
    case "chart":
      return <svg {...common}><path d="M3 3v18h18" /><path d="m19 9-5 5-4-4-3 3" /></svg>;
    case "search":
      return <svg {...common}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>;
    case "login":
      return <svg {...common}><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" /><polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" /></svg>;
    case "register":
      return <svg {...common}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><line x1="19" y1="8" x2="19" y2="14" /><line x1="22" y1="11" x2="16" y2="11" /></svg>;
    case "key":
      return <svg {...common}><circle cx="7.5" cy="15.5" r="5.5" /><path d="m21 2-9.3 9.3" /><path d="m16 7 3-3" /></svg>;
    case "palette":
      return <svg {...common}><circle cx="13.5" cy="6.5" r="2.5" /><circle cx="17.5" cy="10.5" r="2.5" /><circle cx="8.5" cy="7.5" r="2.5" /><circle cx="6.5" cy="12.5" r="2.5" /><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2Z" /></svg>;
    case "chat":
      return <svg {...common}><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" /></svg>;
    case "chain":
      return <svg {...common}><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" /><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" /></svg>;
    case "link":
      return <svg {...common}><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" /><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" /></svg>;
    case "briefcase":
      return <svg {...common}><path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" /><rect width="20" height="14" x="2" y="6" rx="2" /></svg>;
    case "health":
      return <svg {...common}><path d="M11 2a2 2 0 0 0-2 2v5H4a2 2 0 0 0-2 2v2c0 1.1.9 2 2 2h5v5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-5h5a2 2 0 0 0 2-2v-2a2 2 0 0 0-2-2h-5V4a2 2 0 0 0-2-2h-2Z" /></svg>;
    case "download":
      return <svg {...common}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>;
    case "puzzle":
      return <svg {...common}><path d="M19.439 7.85c-.049.322.059.648.289.878l1.568 1.568c.47.47.706 1.087.706 1.704s-.235 1.233-.706 1.704l-1.611 1.611a.98.98 0 0 1-.837.276c-.47-.07-.802-.48-.968-.925a2.501 2.501 0 1 0-3.214 3.214c.446.166.855.497.925.968a.979.979 0 0 1-.276.837l-1.61 1.61a2.404 2.404 0 0 1-1.705.707 2.402 2.402 0 0 1-1.704-.706l-1.568-1.568a1.026 1.026 0 0 0-.877-.29c-.493.074-.84.504-1.02.968a2.5 2.5 0 1 1-3.237-3.237c.464-.18.894-.527.967-1.02a1.026 1.026 0 0 0-.289-.877l-1.568-1.568A2.402 2.402 0 0 1 1.998 12c0-.617.236-1.234.706-1.704L4.315 8.685a.98.98 0 0 1 .837-.276c.47.07.802.48.968.925a2.501 2.501 0 1 0 3.214-3.214c-.446-.166-.855-.497-.925-.968a.979.979 0 0 1 .276-.837l1.61-1.61a2.402 2.402 0 0 1 1.705-.706c.617 0 1.234.236 1.704.706l1.568 1.568c.23.23.556.338.877.29.493-.074.84-.504 1.02-.968a2.5 2.5 0 1 1 3.237 3.237c-.464.18-.894.527-.967 1.02Z" /></svg>;
    default:
      return <svg {...common}><circle cx="12" cy="12" r="8" /></svg>;
  }
}

/* ------------------------------------------------------------------ */
/*  Chevron Icon                                                       */
/* ------------------------------------------------------------------ */

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="flex-shrink-0 transition-transform duration-200"
      style={{ transform: open ? "rotate(90deg)" : "rotate(0deg)" }}
      aria-hidden="true"
    >
      <path d="m9 18 6-6-6-6" />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/*  Search Filter                                                      */
/* ------------------------------------------------------------------ */

function NavSearchFilter({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="relative mx-2 mb-3">
      <svg
        className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2"
        viewBox="0 0 24 24"
        fill="none"
        stroke="var(--obsidian-text-muted)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
      <input
        type="text"
        placeholder="Search navigation…"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="obsidian-input w-full py-1.5 pl-8 pr-3 text-xs"
        aria-label="Filter navigation items"
      />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main NavPanel Component                                            */
/* ------------------------------------------------------------------ */

interface NavPanelProps {
  className?: string;
  /** If provided, navigation is client-side view switching instead of URL routing */
  onNavigate?: (viewId: string) => void;
  /** Current active view ID (used when onNavigate is provided) */
  currentView?: string;
  /** If true, sidebar collapses to icon-only width */
  collapsed?: boolean;
}

export default function NavPanel({
  className = "",
  onNavigate,
  currentView = "",
  collapsed = false,
}: NavPanelProps) {
  const pathname = usePathname();
  const [filter, setFilter] = useState("");
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(() => {
    return Object.fromEntries(NAV_GROUPS.map((g) => [g.label, true]));
  });
  const [expandedModules, setExpandedModules] = useState<Record<string, boolean>>(() => {
    return { dashboard: true };
  });

  const toggleGroup = (label: string) =>
    setExpandedGroups((prev) => ({ ...prev, [label]: !prev[label] }));

  const toggleModule = (id: string) =>
    setExpandedModules((prev) => ({ ...prev, [id]: !prev[id] }));

  /** Determine if an item is active: uses viewId match (SPA mode) or pathname (normal mode) */
  const isActive = useCallback(
    (item: NavItem) => {
      if (onNavigate && item.viewId) {
        return currentView === item.viewId;
      }
      if (!item.href || item.href === "#" || item.href.startsWith("?")) return false;
      return pathname === item.href || pathname.startsWith(item.href + "/");
    },
    [onNavigate, currentView, pathname],
  );

  /** Handle navigation click: either call onNavigate (SPA) or let Link navigate normally */
  const handleItemClick = useCallback(
    (e: React.MouseEvent, item: NavItem) => {
      if (onNavigate && item.viewId) {
        e.preventDefault();
        onNavigate(item.viewId);
      }
    },
    [onNavigate],
  );

  const matchesFilter = (item: NavItem, filterLower: string) =>
    item.label.toLowerCase().includes(filterLower);

  const filterLower = filter.toLowerCase().trim();

  return (
    <aside
      className={`flex h-dvh flex-shrink-0 flex-col overflow-hidden border-r ${className}`}
      style={{
        width: collapsed ? "56px" : "288px",
        borderColor: "var(--obsidian-border)",
        backgroundColor: "var(--obsidian-surface)",
      }}
      aria-label="Main navigation"
    >
      {/* ── Brand Header ── */}
      <div className="flex items-center gap-2.5 border-b px-4 py-4" style={{ borderColor: "var(--obsidian-border)" }}>
        <span className="obsidian-icon-bg flex h-9 w-9 items-center justify-center rounded-lg text-sm font-bold flex-shrink-0">
          ॐ
        </span>
        {!collapsed && (
          <div className="leading-tight min-w-0">
            <span className="block text-sm font-bold tracking-wide" style={{ color: "var(--obsidian-text-primary)", fontFamily: "var(--font-heading)" }}>
              ASTRO<span style={{ color: "var(--obsidian-accent-primary)" }}>OS</span>
            </span>
            <span className="block text-[10px]" style={{ color: "var(--obsidian-text-muted)" }}>
              Design System v1.0
            </span>
          </div>
        )}
      </div>

      {/* ── Enterprise Badge ── */}
      {!collapsed && (
        <div className="px-4 py-2">
          <span className="obsidian-badge-gold w-full justify-center gap-1.5" style={{ fontSize: "11px" }}>
            ✦ Vedic Research Platform
          </span>
        </div>
      )}

      {/* ── Search (hidden when collapsed) ── */}
      {!collapsed && (
        <div className="px-2 pt-3">
          <NavSearchFilter value={filter} onChange={setFilter} />
        </div>
      )}

      {/* ── Navigation Tree ── */}
      <nav className="flex-1 overflow-y-auto px-2 pb-4" aria-label="Navigation modules">
        {NAV_GROUPS.map((group) => {
          const filteredModules = group.modules
            .map((mod) => {
              if (!filterLower) return mod;
              const items = mod.items.filter((item) => matchesFilter(item, filterLower));
              if (mod.label.toLowerCase().includes(filterLower) || items.length > 0) {
                return { ...mod, items: items.length > 0 ? items : mod.items };
              }
              return null;
            })
            .filter(Boolean) as NavModule[];

          if (filteredModules.length === 0) return null;

          const groupOpen = expandedGroups[group.label] ?? true;

          return (
            <div key={group.label} className="mb-3">
              {/* Group header */}
              {!collapsed && (
                <button
                  type="button"
                  onClick={() => toggleGroup(group.label)}
                  className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-[10px] font-semibold uppercase tracking-widest transition-colors"
                  style={{ color: "var(--obsidian-text-muted)" }}
                  aria-expanded={groupOpen}
                >
                  <span>{group.label}</span>
                  <Chevron open={groupOpen} />
                </button>
              )}

              {/* Modules */}
              {(groupOpen || collapsed) && (
                <div className="mt-0.5 flex flex-col gap-0.5">
                  {filteredModules.map((mod) => {
                    const modOpen = expandedModules[mod.id] ?? false;
                    const hasActiveChild = mod.items.some((item) => isActive(item));
                    const modColor = `var(${mod.color})`;

                    return (
                      <div key={mod.id} className="relative">
                        {/* Module header */}
                        <button
                          type="button"
                          onClick={() => toggleModule(mod.id)}
                          className="obsidian-nav-module relative flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-xs font-medium transition-colors"
                          style={{
                            backgroundColor: hasActiveChild || modOpen ? "var(--obsidian-border)" : "transparent",
                            color: hasActiveChild ? modColor : "var(--obsidian-text-secondary)",
                          }}
                          aria-expanded={modOpen}
                          title={collapsed ? mod.label : undefined}
                        >
                          {/* Cyan dot indicator for active module */}
                          {hasActiveChild && !collapsed && (
                            <span className="obsidian-nav-active-dot" style={{ left: "2px" }} />
                          )}

                          <NavIcon name={mod.icon} />
                          {!collapsed && (
                            <>
                              <div className="flex-1 text-left">
                                <div>{mod.label}</div>
                                {mod.subtitle && (
                                  <div className="text-[10px]" style={{ color: "var(--obsidian-text-muted)" }}>
                                    {mod.subtitle}
                                  </div>
                                )}
                              </div>
                              <span className="mr-1 rounded px-1 py-0.5 text-[9px] font-semibold" style={{ color: modColor, opacity: 0.6 }}>
                                {mod.number}
                              </span>
                              <Chevron open={modOpen} />
                            </>
                          )}
                        </button>

                        {/* Module items (hidden when collapsed) */}
                        {modOpen && !collapsed && (
                          <div className="ml-3 mt-0.5 flex flex-col gap-0.5 border-l pl-2" style={{ borderColor: "var(--obsidian-border)" }}>
                            {mod.items
                              .filter((item) => !filterLower || matchesFilter(item, filterLower))
                              .map((item) =>
                                item.disabled ? (
                                  <span
                                    key={item.label}
                                    className="flex items-center justify-between gap-2 rounded-lg px-2.5 py-1.5 text-[11px]"
                                    style={{ color: "var(--obsidian-text-muted)", opacity: 0.45, cursor: "default" }}
                                    title="Coming soon"
                                  >
                                    <span className="flex items-center gap-2">
                                      <NavIcon name={item.icon} className="h-3.5 w-3.5" />
                                      {item.label}
                                    </span>
                                    <span className="obsidian-badge" style={{ border: "1px solid var(--obsidian-border)", fontSize: "8px" }}>
                                      Soon
                                    </span>
                                  </span>
                                ) : (
                                  <Link
                                    key={item.label + item.href}
                                    href={item.href}
                                    onClick={(e) => handleItemClick(e, item)}
                                    className="relative flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-[11px] font-medium transition-colors"
                                    style={{
                                      backgroundColor: isActive(item) ? "var(--obsidian-accent-primary-soft)" : "transparent",
                                      color: isActive(item) ? "var(--obsidian-accent-primary)" : "var(--obsidian-text-secondary)",
                                    }}
                                    onMouseEnter={(e) => {
                                      if (!isActive(item)) {
                                        e.currentTarget.style.backgroundColor = "var(--obsidian-surface-hover)";
                                        e.currentTarget.style.color = "var(--obsidian-text-primary)";
                                      }
                                    }}
                                    onMouseLeave={(e) => {
                                      if (!isActive(item)) {
                                        e.currentTarget.style.backgroundColor = "transparent";
                                        e.currentTarget.style.color = "var(--obsidian-text-secondary)";
                                      }
                                    }}
                                    aria-current={isActive(item) ? "page" : undefined}
                                  >
                                    {/* Cyan dot for active item */}
                                    {isActive(item) && (
                                      <span className="absolute left-0 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full" style={{ background: "var(--obsidian-accent-primary)", boxShadow: "0 0 8px var(--obsidian-accent-primary)" }} />
                                    )}
                                    <NavIcon name={item.icon} className="h-3.5 w-3.5" />
                                    <div className="flex-1 min-w-0">
                                      <div>{item.label}</div>
                                      {item.subtitle && (
                                        <div className="text-[9px]" style={{ color: "var(--obsidian-text-muted)" }}>
                                          {item.subtitle}
                                        </div>
                                      )}
                                    </div>
                                  </Link>
                                ),
                              )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}

        {filterLower && NAV_GROUPS.every((g) => {
          const mods = g.modules.filter((m) =>
            m.label.toLowerCase().includes(filterLower) ||
            m.items.some((i) => i.label.toLowerCase().includes(filterLower))
          );
          return mods.length === 0;
        }) && (
          <p className="obsidian-label mt-4 text-center text-xs">No results for &ldquo;{filter}&rdquo;</p>
        )}
      </nav>

      {/* ── Footer ── */}
      <div className="border-t px-3 py-3" style={{ borderColor: "var(--obsidian-border)" }}>
        {!collapsed ? (
          <p className="text-center text-[9px]" style={{ color: "var(--obsidian-text-muted)" }}>
            AstroOS v2.3 · Lakshmi Release
          </p>
        ) : (
          <p className="text-center text-[8px]" style={{ color: "var(--obsidian-text-muted)" }}>
            v2.3
          </p>
        )}
      </div>
    </aside>
  );
}
