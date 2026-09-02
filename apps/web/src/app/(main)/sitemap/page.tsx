"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { Icon, type IconName } from "@/components/ui";

interface SitemapItem {
  title: string;
  href: string;
  description: string;
  badge?: string;
  badgeColor?: "cyan" | "gold" | "violet" | "emerald" | "amber" | "rose" | "blue";
  icon: IconName;
  status?: "active" | "beta" | "enterprise";
}

interface SitemapCategory {
  id: string;
  title: string;
  description: string;
  accentColor: string;
  icon: IconName;
  items: SitemapItem[];
}

const SITEMAP_CATEGORIES: SitemapCategory[] = [
  {
    id: "core-charts",
    title: "1. Core Workstation & Natal Mathematics",
    description:
      "Astronomical chart creation, sub-arcsecond Swiss Ephemeris calculations, D1–D60 divisional matrices, and planetary strength diagnostics.",
    accentColor: "from-cyan-500 to-blue-600",
    icon: "compass",
    items: [
      {
        title: "Birth Chart Workspace",
        href: "/charts/birth",
        description: "Comprehensive multi-panel interactive birth chart workspace with instant calculation overlays.",
        badge: "Primary Workspace",
        badgeColor: "cyan",
        icon: "compass",
      },
      {
        title: "Interactive Kundli",
        href: "/charts?view=kundli",
        description: "Dynamic North & South Indian chart visualizer with planetary aspects, bhavas, and degrees.",
        badge: "Visualizer",
        badgeColor: "cyan",
        icon: "chart",
      },
      {
        title: "Divisional Charts (D1–D60)",
        href: "/charts?view=divisional",
        description: "Full Shodashavarga and higher divisional matrices with Bhavottama and Vargottama detection.",
        badge: "Shodashavarga",
        badgeColor: "cyan",
        icon: "grid",
      },
      {
        title: "Planet Explorer & Shadbala",
        href: "/charts/planets",
        description: "Detailed dignity, combustion, retrogression, planetary war (Graha Yuddha), and 6-fold Shadbala diagnostics.",
        badge: "Sub-arcsecond",
        badgeColor: "cyan",
        icon: "star",
      },
      {
        title: "House / Bhava Explorer",
        href: "/charts?view=houses",
        description: "Bhava Chalita cusps, house lords, sign occupancies, and functional benefic/malefic classifications.",
        badge: "Bhavachalita",
        badgeColor: "cyan",
        icon: "sparkle",
      },
      {
        title: "Meena Numerology",
        href: "/numerology",
        description: "Empirical Meena numerological life chapters, name syllable vibration, and destiny numbers.",
        badge: "Meena System",
        badgeColor: "amber",
        icon: "sparkle",
      },
      {
        title: "Chart Comparison (Synastry & Transit)",
        href: "/charts/compare",
        description: "Side-by-side multi-chart synastry, dual-wheel transit overlays, and inter-aspect matrices.",
        badge: "Dual Analysis",
        badgeColor: "blue",
        icon: "layers",
      },
      {
        title: "Birth Time Rectification",
        href: "/charts/rectify",
        description: "Lagna sensitivity testing, Tatwa Shodhana, Upagraha alignment, and sub-minute rectification tools.",
        badge: "Sensitivity",
        badgeColor: "violet",
        icon: "clock",
      },
      {
        title: "Saved Chart Library",
        href: "/charts/history",
        description: "Searchable repository of personal, celebrity, and historical research horoscopes.",
        badge: "Library",
        badgeColor: "cyan",
        icon: "folder",
      },
      {
        title: "Chart Data Importer",
        href: "/charts/import",
        description: "Import charts from Jagannatha Hora, Parashara's Light, JSON, CSV, or Quick Time Entry.",
        badge: "Interoperable",
        badgeColor: "blue",
        icon: "upload",
      },
    ],
  },
  {
    id: "predictive-timing",
    title: "2. Predictive Frameworks & Classical Timing",
    description:
      "Canonical Vimshottari dasha hierarchy, Gochara transits, Sarvatobhadra Chakra rays, and Phalita Mixture of Experts.",
    accentColor: "from-amber-400 to-orange-500",
    icon: "clock",
    items: [
      {
        title: "Phalita MoE Consultation",
        href: "/phalita",
        description: "Canonical 3-Chart & Mixture-of-Experts engine synthesizing BPHS rules into unified predictive judgments.",
        badge: "Flagship MoE",
        badgeColor: "gold",
        icon: "sparkle",
      },
      {
        title: "Medini Jyotisha (Mundane)",
        href: "/medini",
        description: "Planetary cabinet (Nava Nayakas), solar ingresses (Sankranti), and geopolitical forecasting.",
        badge: "Mundane Ingress",
        badgeColor: "gold",
        icon: "compass",
      },
      {
        title: "Muhurta & Panchanga",
        href: "/muhurta",
        description: "Real-time Panchanga, Choghadiya, Hora, Rahu Kalam, and auspicious electional timing.",
        badge: "Electional",
        badgeColor: "amber",
        icon: "calendar",
      },
      {
        title: "Vimshottari Dasha Hierarchy",
        href: "/charts/dasha",
        description: "Maha, Antar, Pratyantar, Sookshma, and Pranadasha multi-tier timeline with lord strength correlation.",
        badge: "5 Levels",
        badgeColor: "gold",
        icon: "clock",
      },
      {
        title: "Live Gochara Transit Timeline",
        href: "/charts/transit",
        description: "Real-time planetary motion tracking, Kakshya degrees, Ashtakavarga transit scores, and retrogrades.",
        badge: "Real-time",
        badgeColor: "amber",
        icon: "orbit",
      },
      {
        title: "Unified Event Timing",
        href: "/timing",
        description: "Multi-system convergence timing: Dasha, Gochara, Tarabala, and SBC ray intersections.",
        badge: "Convergence",
        badgeColor: "gold",
        icon: "target",
      },
      {
        title: "Sarvatobhadra Chakra (SBC)",
        href: "/charts/sbc",
        description: "9x9 Sarvatobhadra grid with 112-pada Vedha rays (Front, Left, Right, Up, Down) and Sanghatta.",
        badge: "9x9 Vedha Grid",
        badgeColor: "gold",
        icon: "grid",
      },
      {
        title: "Navatara & Tarabala Matrix",
        href: "/charts/tarabala",
        description: "27-Nakshatra Tarabala (Janma, Sampat, Vipat, Kshema, etc.) across 3 cycles of 9 stars.",
        badge: "27-Tara",
        badgeColor: "amber",
        icon: "star",
      },
      {
        title: "KP System & Horary Prashna",
        href: "/charts/prashna",
        description: "Krishnamurti Paddhati 249 sub-lord tables, Cuspal interlinks, and Arabic Parts catalogue.",
        badge: "KP 249",
        badgeColor: "gold",
        icon: "target",
      },
      {
        title: "Prediction Chain Explorer",
        href: "/predictions",
        description: "Interactive causal graph demonstrating how primary astrological promises trigger through transits.",
        badge: "Causal Chains",
        badgeColor: "amber",
        icon: "network",
      },
      {
        title: "Multi-Method Confluence",
        href: "/predictions/confluence",
        description: "Cross-validating predictions across Parashari, Jaimini, KP, and Nadi methods simultaneously.",
        badge: "Confluence",
        badgeColor: "gold",
        icon: "sparkle",
      },
      {
        title: "Relationship Compatibility",
        href: "/compatibility/report",
        description: "Ashtakoota 36-point Guna Milan, Kuja Dosha, Vedha, Rajju, and composite chart synergy.",
        badge: "Ashtakoota",
        badgeColor: "rose",
        icon: "heart",
      },
    ],
  },
  {
    id: "research-science",
    title: "3. Research Suite & Empirical Science",
    description:
      "Hypothesis testing, large-cohort backtesting, reverse astronomical pattern search, and cryptographic publication audits.",
    accentColor: "from-violet-500 to-purple-600",
    icon: "research",
    items: [
      {
        title: "Research Projects Explorer",
        href: "/research/projects",
        description: "Manage research cohorts, experiment hypotheses, and version-controlled chart datasets.",
        badge: "Cohorts",
        badgeColor: "violet",
        icon: "compass",
      },
      {
        title: "Reverse Astrological Search",
        href: "/research/reverse-search",
        description: "Search 5,000+ years of ephemeris data for precise planetary combinations and configurations.",
        badge: "5000-Year Search",
        badgeColor: "violet",
        icon: "search",
      },
      {
        title: "Pattern Discovery & Mining",
        href: "/research/patterns",
        description: "Statistical pattern discovery across planetary dignity, dasha timings, and verified life events.",
        badge: "Mining",
        badgeColor: "violet",
        icon: "sparkle",
      },
      {
        title: "Prediction Explainability",
        href: "/research/explainability",
        description: "SHAP-style factor decomposition and counterfactual reasoning for astrological predictions.",
        badge: "XAI",
        badgeColor: "violet",
        icon: "target",
      },
      {
        title: "The Empirical Chronicles",
        href: "/research/scholar",
        description: "Scholar journal, statistical audit writeups, and automated academic publication drafting.",
        badge: "Scholar Journal",
        badgeColor: "violet",
        icon: "book",
      },
      {
        title: "Evidence Registry",
        href: "/research/evidence-registry",
        description: "Cryptographically verifiable registry linking astrological signatures to timestamped historical ground truth.",
        badge: "Cryptographic",
        badgeColor: "emerald",
        icon: "shield",
      },
      {
        title: "Research Datasets Hub",
        href: "/research/datasets",
        description: "Curated datasets of verified birth charts across longevity, career milestones, wealth, and health.",
        badge: "Datasets",
        badgeColor: "violet",
        icon: "grid",
      },
      {
        title: "Publication Audit Reports",
        href: "/research/publication",
        description: "Peer-review ready diagnostic exports with statistical p-values, odds ratios, and sample distributions.",
        badge: "P30 Audit",
        badgeColor: "violet",
        icon: "document",
      },
      {
        title: "Backtest Engine",
        href: "/research/backtest",
        description: "Automated retrospective testing of classical slokas against known historical cohorts.",
        badge: "Automated",
        badgeColor: "violet",
        icon: "clock",
      },
      {
        title: "Research Notebook & Astro DSL",
        href: "/research/notebook",
        description: "Interactive scripting workspace using domain-specific astrological syntax for rapid experimentation.",
        badge: "DSL",
        badgeColor: "violet",
        icon: "document",
      },
      {
        title: "Snapshot Manager",
        href: "/research/snapshot-manager",
        description: "Immutable research snapshots allowing 100% reproducible calculation states.",
        badge: "Reproducibility",
        badgeColor: "violet",
        icon: "camera",
      },
    ],
  },
  {
    id: "knowledge-literature",
    title: "4. Knowledge Base & Classical Literature",
    description:
      "Canonical Sanskrit sloka repositories, English translations, attribution graph, and governed RAG Copilot.",
    accentColor: "from-emerald-500 to-teal-600",
    icon: "book",
    items: [
      {
        title: "Knowledge Base Portal",
        href: "/knowledge",
        description: "Centralized knowledge portal indexing classical Jyotisha principles, commentaries, and slokas.",
        badge: "Portal",
        badgeColor: "emerald",
        icon: "book",
      },
      {
        title: "Brihat Parashara Hora Shastra (BPHS)",
        href: "/knowledge/bphs",
        description: "Searchable chapters, Sanskrit verses, and commentaries for the foundational Parashari text.",
        badge: "Parashara",
        badgeColor: "emerald",
        icon: "book",
      },
      {
        title: "Saravali Reference Engine",
        href: "/knowledge/saravali",
        description: "Complete classical compilation by Kalyanavarma covering planetary states, rajayogas, and bhava results.",
        badge: "Saravali",
        badgeColor: "emerald",
        icon: "book",
      },
      {
        title: "Classical Literature Library",
        href: "/knowledge/literature",
        description: "Extended classical bibliography including Phaladeepika, Jataka Parijata, and Uttara Kalamrita.",
        badge: "Bibliography",
        badgeColor: "emerald",
        icon: "document",
      },
      {
        title: "Governed AI Copilot",
        href: "/ai",
        description: "Shastra-grounded AI assistant strictly adhering to classical treatises with zero hallucination constraints.",
        badge: "Strictly Grounded",
        badgeColor: "emerald",
        icon: "chat",
      },
      {
        title: "Knowledge Graph Explorer",
        href: "/knowledge-graph/explorer",
        description: "Graph visualization of nodes, karakatwas, house-planet relationships, and classical rule dependencies.",
        badge: "Graph DB",
        badgeColor: "emerald",
        icon: "network",
      },
      {
        title: "300+ Life Event Formulas",
        href: "/events",
        description: "Rigorous astrological condition formulas mapping to concrete life events (promotions, surgery, weddings).",
        badge: "Event Catalog",
        badgeColor: "emerald",
        icon: "calendar",
      },
    ],
  },
  {
    id: "life-domains-reports",
    title: "5. Life Domains & Reporting Engine",
    description:
      "Domain-specific life analysis modules and multi-format client export generators (PDF, AI, JSON, CSV).",
    accentColor: "from-pink-500 to-rose-600",
    icon: "heart",
    items: [
      {
        title: "Executive Dashboard",
        href: "/dashboard",
        description: "Top-level KPI summary of recent charts, active transits, current dasha lords, and daily panchang.",
        badge: "Command Center",
        badgeColor: "rose",
        icon: "dashboard",
      },
      {
        title: "Career & Profession Forecast",
        href: "/life/career",
        description: "10th house, D10 Dashamsha, Amatyakaraka, and dasha-driven vocation analysis.",
        badge: "D10 Focus",
        badgeColor: "rose",
        icon: "briefcase",
      },
      {
        title: "Marriage & Relationship Timeline",
        href: "/life/marriage",
        description: "7th house, D9 Navamsha, Darakaraka, and Upapada Lagna timing for partnership.",
        badge: "D9 Focus",
        badgeColor: "rose",
        icon: "heart",
      },
      {
        title: "Health & Vitality Diagnostics",
        href: "/life/health",
        description: "6th/8th/12th houses, Maraka lords, Rogakaraka, and Ayurveda dosha balance.",
        badge: "Medical Ast.",
        badgeColor: "rose",
        icon: "shield",
      },
      {
        title: "Life Progression Timeline",
        href: "/life/timeline",
        description: "Chronological milestone timeline mapping life events to concurrent dasha and transit periods.",
        badge: "Milestones",
        badgeColor: "rose",
        icon: "clock",
      },
      {
        title: "PDF Reports Generator",
        href: "/reports/pdf",
        description: "Print-ready high-resolution Vedic horoscope reports with customizable color themes and branding.",
        badge: "PDF Export",
        badgeColor: "rose",
        icon: "document",
      },
      {
        title: "Full Synthesis Comprehensive Report",
        href: "/reports/full",
        description: "Exhaustive multi-page consultation document combining all 16 vargas, dashas, and yogas.",
        badge: "Full Dossier",
        badgeColor: "rose",
        icon: "book",
      },
      {
        title: "AI Consultation Synthesis",
        href: "/reports/ai",
        description: "AI-assisted consultation summaries personalized to client question prompts.",
        badge: "AI Synthesis",
        badgeColor: "rose",
        icon: "sparkle",
      },
    ],
  },
  {
    id: "settings-admin",
    title: "6. Platform, Settings & Administration",
    description:
      "Calculations settings, Ayanamsa configuration, Bring-Your-Own-Key (BYOK) AI models, security, and administrative oversight.",
    accentColor: "from-blue-500 to-indigo-600",
    icon: "settings",
    items: [
      {
        title: "Practitioner Profile & Credentials",
        href: "/settings/profile",
        description: "Manage practitioner identity, bio, consultation timezone, and custom branding emblem.",
        badge: "Credentials",
        badgeColor: "blue",
        icon: "user",
      },
      {
        title: "Astrology & Ephemeris Engine Settings",
        href: "/settings/astrology",
        description: "Configure Ayanamsa presets (Lahiri, KP, Raman, Deva Datta), House Systems, and Node types.",
        badge: "Calculation Core",
        badgeColor: "blue",
        icon: "star",
      },
      {
        title: "AI Model Keys (BYOK)",
        href: "/settings/ai",
        description: "Connect your Gemini, Anthropic Claude, OpenAI, or local Ollama API keys securely.",
        badge: "BYOK",
        badgeColor: "blue",
        icon: "cpu",
      },
      {
        title: "Appearance & Theme Customization",
        href: "/settings/appearance",
        description: "Dark/Light themes, Obsidian palettes, font scaling, and data density preferences.",
        badge: "UI Theme",
        badgeColor: "blue",
        icon: "palette",
      },
      {
        title: "Security & API Access",
        href: "/settings/security",
        description: "Session management, password encryption, and API keys for external integration.",
        badge: "Security",
        badgeColor: "blue",
        icon: "shield",
      },
      {
        title: "Data Backup & Privacy Controls",
        href: "/settings/data",
        description: "Export full chart database in JSON format, purge cache, or delete account data.",
        badge: "Data Privacy",
        badgeColor: "blue",
        icon: "database",
      },
      {
        title: "Documentation & Classical Methodology",
        href: "/help",
        description: "Comprehensive guides, mathematical formulas, and literature attribution standards.",
        badge: "Docs",
        badgeColor: "emerald",
        icon: "book",
      },
      {
        title: "Pricing & Platform Plans",
        href: "/pricing",
        description: "Scholar, Practitioner, and Institutional enterprise plan options.",
        badge: "Plans",
        badgeColor: "gold",
        icon: "briefcase",
      },
      {
        title: "Administrative Control Center",
        href: "/admin",
        description: "Audit logs, user role permissions, system health checks, and plugin management.",
        badge: "Admin Only",
        badgeColor: "violet",
        icon: "shield",
      },
    ],
  },
];

export default function SitemapPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  // Filtered categories and items based on search query
  const filteredCategories = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();

    return SITEMAP_CATEGORIES.map((cat) => {
      // Filter items within category
      const matchedItems = cat.items.filter((item) => {
        if (!q) return true;
        return (
          item.title.toLowerCase().includes(q) ||
          item.description.toLowerCase().includes(q) ||
          item.href.toLowerCase().includes(q) ||
          (item.badge && item.badge.toLowerCase().includes(q))
        );
      });

      return {
        ...cat,
        items: matchedItems,
      };
    }).filter((cat) => {
      if (selectedCategory !== "all" && cat.id !== selectedCategory) return false;
      return cat.items.length > 0;
    });
  }, [searchQuery, selectedCategory]);

  const totalIndexedLinks = useMemo(() => {
    return SITEMAP_CATEGORIES.reduce((acc, cat) => acc + cat.items.length, 0);
  }, []);

  return (
    <div className="space-y-8 pb-16">
      {/* ── Header Banner ── */}
      <div
        className="relative overflow-hidden rounded-2xl border p-6 md:p-8 shadow-xl transition-colors"
        style={{
          backgroundColor: "var(--bg-card)",
          borderColor: "var(--border-primary)",
        }}
      >
        <div
          className="absolute top-0 right-0 -mt-8 -mr-8 h-64 w-64 rounded-full blur-3xl pointer-events-none opacity-40"
          style={{ backgroundColor: "var(--cyan-400)" }}
        />
        <div
          className="absolute bottom-0 left-1/3 -mb-8 h-48 w-48 rounded-full blur-3xl pointer-events-none opacity-30"
          style={{ backgroundColor: "var(--obsidian-accent-tertiary, #a78bfa)" }}
        />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2 max-w-3xl">
            <div
              className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold"
              style={{
                backgroundColor: "var(--bg-secondary)",
                borderColor: "var(--border-primary)",
                color: "var(--cyan-400)",
              }}
            >
              <span className="h-2 w-2 rounded-full animate-pulse" style={{ backgroundColor: "var(--cyan-400)" }} />
              <span>AstroOS Navigation Directory</span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight" style={{ color: "var(--text-primary)" }}>
              Sitemap & Architectural Index
            </h1>

            <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              Complete directory of all computational engines, predictive modules, research tools, classical literature
              repositories, and administrative features across the AstroOS ecosystem.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <a
              href="/sitemap.xml"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-bold transition-all shadow-md hover:scale-105"
              style={{
                backgroundColor: "var(--bg-secondary)",
                borderColor: "var(--border-primary)",
                color: "var(--cyan-400)",
              }}
            >
              <Icon name="analysis" className="h-4 w-4" />
              <span>Raw XML Sitemap</span>
              <span>↗</span>
            </a>

            <div
              className="inline-flex items-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-mono"
              style={{
                backgroundColor: "var(--bg-secondary)",
                borderColor: "var(--border-primary)",
                color: "var(--text-secondary)",
              }}
            >
              <span className="font-bold" style={{ color: "var(--cyan-400)" }}>{totalIndexedLinks}</span>
              <span>Modules Indexed</span>
            </div>
          </div>
        </div>

        {/* ── Search & Filter Bar ── */}
        <div
          className="mt-8 pt-6 border-t flex flex-col sm:flex-row items-center gap-4"
          style={{ borderColor: "var(--border-primary)" }}
        >
          <div className="relative w-full sm:max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none" style={{ color: "var(--text-muted)" }}>
              <Icon name="search" className="h-4 w-4" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search sitemap by module, keyword, or path..."
              className="w-full pl-10 pr-4 py-2 text-xs rounded-xl border transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500"
              style={{
                backgroundColor: "var(--bg-input, var(--bg-secondary))",
                borderColor: "var(--border-primary)",
                color: "var(--text-primary)",
              }}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-xs hover:opacity-80"
                style={{ color: "var(--text-muted)" }}
              >
                Clear
              </button>
            )}
          </div>

          {/* Category Quick Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto w-full pb-1 sm:pb-0 text-xs no-scrollbar">
            <button
              onClick={() => setSelectedCategory("all")}
              className="px-3 py-1.5 rounded-lg font-medium transition whitespace-nowrap"
              style={{
                backgroundColor: selectedCategory === "all" ? "var(--cyan-400)" : "var(--bg-secondary)",
                color: selectedCategory === "all" ? "var(--text-inverse, #0f172a)" : "var(--text-secondary)",
                fontWeight: selectedCategory === "all" ? "700" : "500",
                border: "1px solid var(--border-primary)",
              }}
            >
              All Categories
            </button>
            {SITEMAP_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className="px-3 py-1.5 rounded-lg font-medium transition whitespace-nowrap"
                style={{
                  backgroundColor: selectedCategory === cat.id ? "var(--cyan-400)" : "var(--bg-secondary)",
                  color: selectedCategory === cat.id ? "var(--text-inverse, #0f172a)" : "var(--text-secondary)",
                  fontWeight: selectedCategory === cat.id ? "700" : "500",
                  border: "1px solid var(--border-primary)",
                }}
              >
                {cat.title.split(". ")[1] || cat.title}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Categorized Sections ── */}
      <div className="space-y-10">
        {filteredCategories.length === 0 ? (
          <div
            className="rounded-2xl border p-12 text-center"
            style={{
              backgroundColor: "var(--bg-card)",
              borderColor: "var(--border-primary)",
            }}
          >
            <Icon name="search" className="h-10 w-10 mx-auto mb-3" style={{ color: "var(--text-muted)" }} />
            <h3 className="text-base font-bold" style={{ color: "var(--text-primary)" }}>No matching modules found</h3>
            <p className="text-xs mt-1 max-w-sm mx-auto" style={{ color: "var(--text-muted)" }}>
              No pages match your search term &quot;{searchQuery}&quot;. Try searching for another astrological term or clear the filter.
            </p>
            <button
              onClick={() => {
                setSearchQuery("");
                setSelectedCategory("all");
              }}
              className="mt-4 px-4 py-2 rounded-xl font-bold text-xs transition"
              style={{
                backgroundColor: "var(--cyan-400)",
                color: "var(--text-inverse, #0f172a)",
              }}
            >
              Reset Filters
            </button>
          </div>
        ) : (
          filteredCategories.map((category) => (
            <section key={category.id} className="space-y-4" id={category.id}>
              {/* Category Section Header */}
              <div
                className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1 border-b pb-3"
                style={{ borderColor: "var(--border-primary)" }}
              >
                <div className="flex items-center gap-3">
                  <span className={`h-3 w-3 rounded-full bg-gradient-to-r ${category.accentColor}`} />
                  <h2 className="text-lg font-bold tracking-wide" style={{ color: "var(--text-primary)" }}>
                    {category.title}
                  </h2>
                </div>
                <p className="text-xs max-w-xl" style={{ color: "var(--text-muted)" }}>
                  {category.description}
                </p>
              </div>

              {/* Items Grid */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {category.items.map((item) => (
                  <Link
                    key={item.href + item.title}
                    href={item.href}
                    className="group relative flex flex-col justify-between rounded-xl border p-4 transition-all hover:-translate-y-0.5 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    style={{
                      backgroundColor: "var(--bg-card)",
                      borderColor: "var(--border-primary)",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = "var(--bg-card-hover)";
                      e.currentTarget.style.borderColor = "var(--cyan-400)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = "var(--bg-card)";
                      e.currentTarget.style.borderColor = "var(--border-primary)";
                    }}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <div
                            className="flex h-7 w-7 items-center justify-center rounded-lg transition-colors"
                            style={{
                              backgroundColor: "var(--bg-secondary)",
                              color: "var(--cyan-400)",
                            }}
                          >
                            <Icon name={item.icon} className="h-4 w-4" />
                          </div>
                          <h3 className="text-sm font-bold transition-colors" style={{ color: "var(--text-primary)" }}>
                            {item.title}
                          </h3>
                        </div>

                        {item.badge && (
                          <span
                            className="text-[10px] font-semibold px-2 py-0.5 rounded-full border"
                            style={{
                              backgroundColor: "var(--bg-secondary)",
                              borderColor: "var(--border-primary)",
                              color: "var(--text-secondary)",
                            }}
                          >
                            {item.badge}
                          </span>
                        )}
                      </div>

                      <p className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                        {item.description}
                      </p>
                    </div>

                    <div
                      className="mt-4 pt-2.5 border-t flex items-center justify-between text-[11px] font-mono transition-colors"
                      style={{
                        borderColor: "var(--border-primary)",
                        color: "var(--text-muted)",
                      }}
                    >
                      <span className="truncate max-w-[220px]">{item.href}</span>
                      <span className="transform group-hover:translate-x-1 transition-transform" style={{ color: "var(--cyan-400)" }}>
                        →
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          ))
        )}
      </div>
    </div>
  );
}
