/**
 * navConfig.ts — Single source of truth for all AstroOS navigation.
 *
 * 4 Parent Groups:
 *   1. Core Charts
 *   2. Predictive & Technical
 *   3. Research
 *   4. Platform
 */

export interface NavItem {
  href: string;
  label: string;
  subtitle?: string;
  icon: string;
  disabled?: boolean;
  adminOnly?: boolean;
  viewId?: string;
  beta?: boolean;
}

export interface NavModule {
  id: string;
  number: string;
  label: string;
  subtitle: string;
  icon: string;
  color: string;
  items: NavItem[];
}

export interface NavGroup {
  label: string;
  modules: NavModule[];
}

export interface NavSection {
  title: string;
  color: string;
  items: NavItem[];
}

export const SHOW_BETA_FEATURES =
  typeof process !== "undefined" &&
  (process.env.NEXT_PUBLIC_SHOW_BETA_FEATURES === "true" || process.env.SHOW_BETA_FEATURES === "true");

export const VIEW_TO_CLEAN_PATH: Record<string, string> = {
  chart: "/charts/birth",
  kundli: "/charts/kundli",
  divisional: "/charts/divisional",
  houses: "/charts/houses",
  "relationships-v2": "/charts/relationships",
  dasha: "/charts/dasha",
  timeline: "/charts/timeline",
  strength: "/charts/strength",
  kp: "/charts/kp",
  yogas: "/charts/yogas",
  ashtakavarga: "/charts/ashtakavarga",
  jaimini: "/charts/jaimini",
  planets: "/charts/planets",
  nakshatra: "/charts/nakshatra",
  predictions: "/charts/predictions",
  sbc: "/charts?view=sbc",
  tarabala: "/charts/tarabala",
};

/**
 * Universal active route matcher for both clean URL paths and legacy query-view paths.
 */
export function isRouteActive(
  itemHref: string,
  pathname: string,
  searchParams?: { get: (key: string) => string | null } | null
): boolean {
  if (!itemHref || itemHref === "#" || itemHref.startsWith("?")) return false;

  const [itemBase, itemQuery] = itemHref.split("?");

  // If item has specific query params (e.g. /nakshatra?tab=tara)
  if (itemQuery && searchParams) {
    const itemParams = new URLSearchParams(itemQuery);
    if (pathname !== itemBase) return false;
    for (const [key, val] of itemParams.entries()) {
      if (searchParams.get(key) !== val) return false;
    }
    return true;
  }

  // Exact base match
  if (pathname === itemBase) {
    return true;
  }

  // If pathname is /charts and searchParams has ?view=
  if (pathname === "/charts" && searchParams) {
    const view = searchParams.get("view");
    if (view && VIEW_TO_CLEAN_PATH[view] === itemBase) {
      return true;
    }
  }

  // If pathname is /research/projects and searchParams has ?tab=snapshot
  if (pathname === "/research/projects" && searchParams) {
    if (searchParams.get("tab") === "snapshot" && itemBase === "/research/snapshot-manager") {
      return true;
    }
  }

  // Subpath match (e.g. /settings/profile matches /settings/profile/...)
  if (itemBase !== "/dashboard" && itemBase !== "/charts" && pathname.startsWith(itemBase + "/")) {
    return true;
  }

  return false;
}

export const NAV_CONFIG: NavGroup[] = [
  {
    label: "Core Charts",
    modules: [
      {
        id: "chart-management",
        number: "01",
        label: "Chart Library",
        subtitle: "Library · Import · Compare",
        icon: "library",
        color: "--section-charts",
        items: [
          { href: "/charts/history", label: "Chart Library", subtitle: "Browse saved charts", icon: "grid", viewId: "chart-library" },
          { href: "/charts/import", label: "Import Chart", icon: "upload" },
          { href: "/charts/compare", label: "Compare Charts", subtitle: "Side-by-side analysis", icon: "layers", viewId: "chart-compare" },
          { href: "/charts/rectify", label: "Rectification", subtitle: "Lagna sensitivity & upagrahas", icon: "clock" },
          { href: "/charts/collections", label: "Collections", icon: "folder" },
        ],
      },
      {
        id: "chart-workspace",
        number: "02",
        label: "Birth Chart",
        subtitle: "Kundli · Planets · Houses",
        icon: "compass",
        color: "--section-charts",
        items: [
          { href: "/charts?view=kundli", label: "Interactive Kundli", subtitle: "Birth chart visualization", icon: "compass", viewId: "workspace-kundli" },
          { href: "/charts?view=chart", label: "Chart View", subtitle: "Planetary detail panels", icon: "chart", viewId: "workspace-chart" },
          { href: "/charts/planets", label: "Planet Explorer", subtitle: "Structural & functional analysis", icon: "search", viewId: "workspace-planets" },
          { href: "/charts?view=houses", label: "House Explorer", subtitle: "Bhava analysis", icon: "house", viewId: "workspace-houses" },
          { href: "/charts?view=divisional", label: "Divisional Charts", subtitle: "D-1 through D-60", icon: "grid", viewId: "workspace-divisional" },
          { href: "/charts?view=relationships-v2", label: "Planet Relationships", subtitle: "Aspect graph", icon: "network", viewId: "workspace-relationships-v2" },
          { href: "/numerology", label: "Meena Numerology", subtitle: "Life Chapters & Sound Vibration", icon: "sparkle", viewId: "workspace-numerology" },
        ],
      },
      {
        id: "nakshatra",
        number: "03",
        label: "Nakshatra",
        subtitle: "27 Stars · Padas · Tara",
        icon: "star",
        color: "--section-analysis",
        items: [
          { href: "/nakshatra", label: "Nakshatra Module", subtitle: "Overview · Natal · Planetary", icon: "star", viewId: "nakshatra-overview" },
          { href: "/nakshatra?tab=tara", label: "Tara Bala", subtitle: "9-fold matrix", icon: "target", viewId: "nakshatra-tara" },
          { href: "/nakshatra?tab=dasha", label: "Lords & Dasha", subtitle: "Vimshottari timeline", icon: "clock", viewId: "nakshatra-dasha" },
          { href: "/nakshatra?tab=transit", label: "Transit / Gochara", subtitle: "Live transit analysis", icon: "orbit", viewId: "nakshatra-transit" },
          { href: "/nakshatra?tab=muhurta", label: "Muhurta", subtitle: "Timing suitability", icon: "sparkle", viewId: "nakshatra-muhurta" },
          { href: "/nakshatra?tab=special", label: "Special Rules", subtitle: "Gandanta · Tripadi", icon: "shield", viewId: "nakshatra-special" },
          { href: "/nakshatra?tab=namakshara", label: "Namakshara", subtitle: "Name syllables", icon: "book", viewId: "nakshatra-namakshara" },
          { href: "/nakshatra?tab=combined", label: "Combined Analysis", subtitle: "Full synthesis", icon: "layers", viewId: "nakshatra-combined" },
        ],
      },
    ],
  },
  {
    label: "Predictive & Technical",
    modules: [
      {
        id: "analysis",
        number: "04",
        label: "Predictive Analysis",
        subtitle: "Dasha · Transit · Yogas",
        icon: "analysis",
        color: "--section-analysis",
        items: [
          { href: "/charts/dasha", label: "Dasha", subtitle: "Vimshottari periods", icon: "clock", viewId: "analysis-dasha" },
          { href: "/charts/transit", label: "Transit & Gochar", subtitle: "Live Gochar & Real-time Timeline", icon: "orbit", viewId: "analysis-gochar" },
          { href: "/charts?view=timeline", label: "Transit (Timeline)", subtitle: "Current planetary positions", icon: "orbit", viewId: "analysis-transit" },
          { href: "/charts?view=yogas", label: "Yogas", icon: "star" },
          { href: "/charts?view=ashtakavarga", label: "Ashtakavarga", icon: "grid" },
          { href: "/charts?view=strength", label: "Shadbala", subtitle: "Planet strength", icon: "bar", viewId: "analysis-shadbala" },
          { href: "/timing", label: "Unified Event Timing", subtitle: "Sensitive timelines & convergence", icon: "clock", viewId: "analysis-timing" },
          { href: "/charts/sbc", label: "Sarvatobhadra Chakra (SBC)", subtitle: "9x9 Grid · 112-Pada Vedha Rays", icon: "grid", viewId: "analysis-sbc" },
          { href: "/charts/tarabala", label: "Navatara / Tarabala", subtitle: "27-Tara · 9 Cycles", icon: "star", viewId: "analysis-tarabala" },
          { href: "/phalita", label: "Phalita MoE Consultation", subtitle: "Canonical 3-Chart & MoE", icon: "sparkle", viewId: "analysis-phalita" },
          { href: "/medini", label: "Medini Jyotisha", subtitle: "National & Geopolitical Ingress", icon: "globe", viewId: "analysis-medini" },
          { href: "/muhurta", label: "Muhurta & Panchanga", subtitle: "Auspicious Timing & SSS Mode", icon: "clock", viewId: "analysis-muhurta" },
          { href: "/relocation", label: "Relocation & Astro-Cartography", subtitle: "Find Best Locations & World Lines", icon: "compass", viewId: "analysis-relocation" },
        ],
      },

      {
        id: "technical-systems",
        number: "05",
        label: "Technical Systems",
        subtitle: "KP · Jaimini · Prediction",
        icon: "target",
        color: "--section-analysis",
        items: [
          { href: "/charts?view=kp", label: "KP Analysis", subtitle: "Krishnamurti Paddhati", icon: "target", viewId: "analysis-kp" },
          { href: "/charts/prashna", label: "Prashna (Horary)", subtitle: "KP Horary · Arabic Parts", icon: "sparkle", viewId: "analysis-prashna" },
          { href: "/events", label: "Events Explorer", subtitle: "300+ Life Events & Formulas", icon: "calendar", viewId: "analysis-events" },
          { href: "/charts?view=jaimini", label: "Jaimini", icon: "book" },
          { href: "/predictions", label: "Prediction Chain Explorer", icon: "sparkle" },
          { href: "/numerology", label: "Meena Numerology", subtitle: "Life Chapters & Timing Map", icon: "sparkle", viewId: "analysis-numerology" },
        ],
      },
      {
        id: "ai",
        number: "06",
        label: "AI Intelligence",
        subtitle: "Explain · Chat · Confidence",
        icon: "sparkle",
        color: "--section-research",
        items: [
          { href: "/phalita", label: "Phalita MoE AI", subtitle: "Canonical 3-Chart & MoE", icon: "sparkle", viewId: "ai-phalita" },
          { href: "/research/explainability", label: "Prediction Explainability", subtitle: "Factor decomposition & counterfactuals", icon: "target", viewId: "ai-explainability" },
          { href: "/ai", label: "Governed RAG Copilot", subtitle: "Shastra-grounded AI", icon: "chat", viewId: "ai-copilot" },
        ],
      },
    ],
  },
  {
    label: "Research",
    modules: [
      {
        id: "research",
        number: "07",
        label: "Research Tools",
        subtitle: "Search · Patterns · Cases",
        icon: "research",
        color: "--section-research",
        items: [
          { href: "/research/projects", label: "Research Explorer", subtitle: "Browse projects", icon: "compass", viewId: "research-explorer" },
          { href: "/research/reverse-search", label: "Reverse Search", icon: "search", viewId: "research-reverse-search" },
          { href: "/research/dashboard", label: "Research Dashboard", subtitle: "Research analytics", icon: "bar", viewId: "research-dashboard" },
          { href: "/research/import", label: "Case Import", icon: "document", viewId: "research-import" },
          { href: "/research/categories", label: "Category Tree", icon: "grid", viewId: "research-categories" },
          { href: "/research/event-types", label: "Event Tree", icon: "grid", viewId: "research-event-types" },
          { href: "/research/cases/bulk-import", label: "Bulk Import", icon: "document", viewId: "research-bulk-import" },
          { href: "/research/patterns", label: "Pattern Discovery", icon: "sparkle", viewId: "research-patterns" },
          { href: "/research/cases", label: "Case Studies", icon: "document" },
          { href: "/research/snapshot-manager", label: "Snapshot Manager", icon: "camera", viewId: "research-snapshot-manager" },
          { href: "/research/notebook", label: "Notebook", icon: "document", viewId: "research-notebook" },
          { href: "/research/datasets", label: "Datasets", icon: "grid" },
          { href: "/research/scholar", label: "The Empirical Chronicles", subtitle: "Scholar Blog & Auto-Publish", icon: "sparkle" },
          { href: "/research/publication", label: "Publication Reports", subtitle: "Cryptographic P30 Audit", icon: "document" },
          { href: "/research/events", label: "Event Verification", icon: "document" },
          { href: "/research/rules", label: "Rule Validation", icon: "shield" },
          { href: "/research/relocation", label: "Relocation Studio", subtitle: "Astro-cartography techniques", icon: "compass", viewId: "research-relocation" },
        ],
      },
      {
        id: "knowledge-graph",
        number: "08",
        label: "Knowledge Graph",
        subtitle: "Visualizations · Explorer",
        icon: "network",
        color: "--section-research",
        items: [
          { href: "/knowledge-graph", label: "Visualizations", icon: "network" },
          { href: "/knowledge-graph/explorer", label: "Graph Explorer", icon: "search" },
          { href: "/knowledge-graph/entities", label: "Entity Browser", icon: "book", disabled: true, beta: true },
          { href: "/knowledge-graph/rules", label: "Rule Explorer", icon: "shield", disabled: true, beta: true },
          { href: "/knowledge-graph/saved", label: "Saved Graphs", icon: "camera", disabled: true, beta: true },
          { href: "/knowledge-graph/compare", label: "Graph Compare", icon: "layers", disabled: true, beta: true },
        ],
      },
      {
        id: "knowledge-base",
        number: "09",
        label: "Knowledge Base",
        subtitle: "BPHS · Saravali · Rules",
        icon: "book",
        color: "--section-research",
        items: [
          { href: "/knowledge", label: "Knowledge Base", icon: "book" },
          { href: "/knowledge/bphs", label: "BPHS", icon: "book", viewId: "kb-bphs" },
          { href: "/knowledge/saravali", label: "Saravali", icon: "book", viewId: "kb-saravali" },
          { href: "/knowledge/rules", label: "Rule Explorer", icon: "settings", viewId: "kb-rules", disabled: true, beta: true },
          { href: "/knowledge/literature", label: "Literature", icon: "document", viewId: "kb-literature" },
          { href: "/knowledge/citations", label: "Citations", icon: "link", viewId: "kb-citations", disabled: true, beta: true },
        ],
      },
    ],
  },
  {
    label: "Platform",
    modules: [
      {
        id: "dashboard",
        number: "10",
        label: "Dashboard",
        subtitle: "Overview · Metrics · Activity",
        icon: "dashboard",
        color: "--obsidian-accent-primary",
        items: [
          { href: "/dashboard", label: "Executive Overview", subtitle: "KPIs & charts", icon: "chart", viewId: "dashboard-executive" },
          { href: "/dashboard/notifications", label: "Notifications", icon: "bell", disabled: true, beta: true },
          { href: "/dashboard/timeline", label: "Timeline", icon: "clock", disabled: true, beta: true },
        ],
      },
      {
        id: "life-events",
        number: "11",
        label: "Life Events",
        subtitle: "Marriage · Career · Health",
        icon: "heart",
        color: "--section-charts",
        items: [
          { href: "/life/marriage", label: "Marriage", icon: "heart", viewId: "life-marriage" },
          { href: "/life/career", label: "Career", icon: "briefcase", viewId: "life-career" },
          { href: "/life/health", label: "Health", icon: "health", viewId: "life-health" },
          { href: "/life/timeline", label: "Timeline", icon: "clock", viewId: "life-timeline" },
        ],
      },
      {
        id: "reports",
        number: "12",
        label: "Reports",
        subtitle: "PDF · AI · Export",
        icon: "report",
        color: "--section-charts",
        items: [
          { href: "/reports/pdf", label: "PDF Reports", icon: "document", viewId: "reports-pdf" },
          { href: "/reports/full", label: "Full Report", icon: "book", viewId: "reports-full" },
          { href: "/reports/ai", label: "AI Reports", icon: "sparkle", viewId: "reports-ai" },
          { href: "/reports/comparison", label: "Comparison", icon: "layers", viewId: "reports-comparison" },
          { href: "/reports/export", label: "Export", icon: "download", viewId: "reports-export" },
        ],
      },
      {
        id: "settings",
        number: "13",
        label: "Settings",
        subtitle: "Profile · Astrology · AI · Appearance",
        icon: "settings",
        color: "--obsidian-text-muted",
        items: [
          { href: "/settings/profile", label: "Profile", icon: "user", viewId: "settings-profile" },
          { href: "/settings/astrology", label: "Astrology", icon: "star", viewId: "settings-astrology" },
          { href: "/settings/ai", label: "AI", icon: "cpu", viewId: "settings-ai" },
          { href: "/settings/appearance", label: "Appearance", icon: "palette", viewId: "settings-appearance" },
          { href: "/settings/security", label: "Security", icon: "shield", viewId: "settings-security" },
          { href: "/settings/data", label: "Data", icon: "database", viewId: "settings-data" },
          { href: "/sitemap", label: "Sitemap & Index", icon: "grid", viewId: "settings-sitemap" },
        ],
      },
      {
        id: "admin",
        number: "14",
        label: "Administration",
        subtitle: "Rules · Plugins · Logs",
        icon: "shield",
        color: "--section-system",
        items: [
          { href: "/admin/rules", label: "Rules Engine", icon: "settings", viewId: "admin-rules" },
          { href: "/admin/literature", label: "Literature", icon: "book", viewId: "admin-literature" },
          { href: "/admin/plugins", label: "Plugins", icon: "puzzle", viewId: "admin-plugins" },
          { href: "/admin", label: "Audit & Logs", subtitle: "System activity", icon: "shield", viewId: "admin-audit", adminOnly: true },
          { href: "/admin/health", label: "System Health", icon: "heart", viewId: "admin-health" },
        ],
      },
    ],
  },
];

export const NAV_SECTIONS: NavSection[] = [
  {
    title: "MAIN",
    color: "--section-charts",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: "dashboard" },
      { href: "/charts/birth", label: "Chart Workspace", icon: "compass" },
      { href: "/phalita", label: "Phalita MoE Consultation", icon: "sparkle" },
      { href: "/medini", label: "Medini Jyotisha (Mundane)", icon: "globe" },
      { href: "/muhurta", label: "Muhurta & Panchanga", icon: "clock" },
      { href: "/numerology", label: "Meena Numerology", icon: "star" },
      { href: "/research/explainability", label: "Prediction Explainability", icon: "target" },
      { href: "/events", label: "Life Event Explorer", icon: "calendar" },
      { href: "/research/projects", label: "Research Explorer", icon: "search" },
      { href: "/sitemap", label: "Sitemap & Directory", icon: "grid" },
      { href: "/help", label: "Help & Methodology", icon: "book" },
    ],
  },
  {
    title: "ANALYSIS MODULES",
    color: "--section-analysis",
    items: [
      { href: "/charts?view=kundli", label: "Interactive Kundli", icon: "compass" },
      { href: "/charts?view=divisional", label: "Divisional Charts", icon: "grid" },
      { href: "/charts/planets", label: "Planet Explorer", icon: "search" },
      { href: "/charts?view=houses", label: "House Explorer", icon: "house" },
      { href: "/charts/dasha", label: "Dasha Explorer", icon: "clock" },
      { href: "/charts/transit", label: "Transit Explorer", icon: "orbit" },
      { href: "/charts?view=yogas", label: "Yogas & Combinations", icon: "star" },
      { href: "/charts?view=ashtakavarga", label: "Ashtakavarga", icon: "grid" },
      { href: "/charts/kp", label: "KP Analysis", icon: "target" },
      { href: "/charts?view=jaimini", label: "Jaimini Analysis", icon: "book" },
      { href: "/charts/sbc", label: "Sarvatobhadra Chakra (SBC)", icon: "grid" },
      { href: "/timing", label: "Unified Event Timing", icon: "clock" },
      { href: "/charts/tarabala", label: "Navatara / Tarabala", icon: "star" },
    ],
  },
  {
    title: "RESEARCH & DATA",
    color: "--section-research",
    items: [
      { href: "/research/reverse-search", label: "Reverse Search", icon: "search" },
      { href: "/research/patterns", label: "Pattern Discovery", icon: "sparkle" },
      { href: "/research/dashboard", label: "Research Statistics", icon: "bar" },
      { href: "/relocation", label: "Relocation Studio", icon: "compass" },
      { href: "/knowledge", label: "Knowledge Base", icon: "book" },
      { href: "/knowledge/bphs", label: "Classical References", icon: "book" },
    ],
  },
  {
    title: "ADMINISTRATION",
    color: "--section-system",
    items: [
      { href: "/admin/users", label: "User Management", icon: "user" },
      { href: "/admin/permissions", label: "Roles & Permissions", icon: "shield" },
      { href: "/research/snapshot-manager", label: "Data Snapshots", icon: "camera" },
      { href: "/settings/profile", label: "System Settings", icon: "settings" },
    ],
  },
];
