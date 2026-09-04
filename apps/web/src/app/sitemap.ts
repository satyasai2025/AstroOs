import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://astroos.internal";
  const lastModified = new Date();

  // Comprehensive route list across all AstroOS modules and capabilities
  const routes: Array<{
    path: string;
    changeFrequency: "always" | "hourly" | "daily" | "weekly" | "monthly" | "yearly" | "never";
    priority: number;
  }> = [
    // 1. Landing & Home
    { path: "", changeFrequency: "daily", priority: 1.0 },

    // 2. Core Charts & Workstation
    { path: "/charts", changeFrequency: "daily", priority: 0.95 },
    { path: "/charts/birth", changeFrequency: "daily", priority: 0.95 },
    { path: "/charts/history", changeFrequency: "daily", priority: 0.85 },
    { path: "/charts/compare", changeFrequency: "weekly", priority: 0.85 },
    { path: "/charts/rectify", changeFrequency: "weekly", priority: 0.8 },
    { path: "/charts/import", changeFrequency: "monthly", priority: 0.75 },
    { path: "/charts/planets", changeFrequency: "daily", priority: 0.9 },
    { path: "/charts/dasha", changeFrequency: "daily", priority: 0.9 },
    { path: "/charts/transit", changeFrequency: "daily", priority: 0.9 },
    { path: "/charts/sbc", changeFrequency: "daily", priority: 0.85 },
    { path: "/charts/tarabala", changeFrequency: "daily", priority: 0.85 },
    { path: "/charts/kp", changeFrequency: "weekly", priority: 0.85 },
    { path: "/charts/prashna", changeFrequency: "daily", priority: 0.85 },

    // 3. Predictive Frameworks & Vedic Engines
    { path: "/phalita", changeFrequency: "daily", priority: 0.95 },
    { path: "/medini", changeFrequency: "daily", priority: 0.95 },
    { path: "/muhurta", changeFrequency: "daily", priority: 0.9 },
    { path: "/nakshatra", changeFrequency: "weekly", priority: 0.9 },
    { path: "/timing", changeFrequency: "daily", priority: 0.9 },
    { path: "/numerology", changeFrequency: "weekly", priority: 0.85 },
    { path: "/events", changeFrequency: "weekly", priority: 0.85 },
    { path: "/predictions", changeFrequency: "daily", priority: 0.85 },
    { path: "/predictions/confluence", changeFrequency: "daily", priority: 0.85 },
    { path: "/compatibility/report", changeFrequency: "weekly", priority: 0.85 },
    { path: "/consultation", changeFrequency: "weekly", priority: 0.8 },
    { path: "/karakatva", changeFrequency: "monthly", priority: 0.8 },

    // 4. AI Intelligence & Governed Copilots
    { path: "/ai", changeFrequency: "daily", priority: 0.9 },
    { path: "/ai/explain", changeFrequency: "daily", priority: 0.85 },
    { path: "/research/explainability", changeFrequency: "weekly", priority: 0.85 },

    // 5. Research Suite & Empirical Benchmarks
    { path: "/research", changeFrequency: "daily", priority: 0.9 },
    { path: "/research/dashboard", changeFrequency: "daily", priority: 0.85 },
    { path: "/research/projects", changeFrequency: "daily", priority: 0.85 },
    { path: "/research/reverse-search", changeFrequency: "weekly", priority: 0.85 },
    { path: "/research/patterns", changeFrequency: "weekly", priority: 0.85 },
    { path: "/research/patterns/overview", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/patterns/explore", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/patterns/dashas", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/patterns/transits", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/patterns/yogas", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/patterns/nakshatras", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/patterns/houses", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/patterns/combinations", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/patterns/compare", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/cases", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/datasets", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/evidence-registry", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/scholar", changeFrequency: "daily", priority: 0.85 },
    { path: "/research/publication", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/backtest", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/astro-dsl", changeFrequency: "monthly", priority: 0.8 },
    { path: "/research/notebook", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/hypotheses", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/hypothesis-mining", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/benchmarks", changeFrequency: "weekly", priority: 0.8 },
    { path: "/research/reproducibility", changeFrequency: "monthly", priority: 0.75 },
    { path: "/research/snapshot-manager", changeFrequency: "monthly", priority: 0.75 },

    // 6. Knowledge Base & Classical Literature
    { path: "/knowledge", changeFrequency: "weekly", priority: 0.85 },
    { path: "/knowledge/bphs", changeFrequency: "monthly", priority: 0.85 },
    { path: "/knowledge/saravali", changeFrequency: "monthly", priority: 0.85 },
    { path: "/knowledge/literature", changeFrequency: "monthly", priority: 0.8 },
    { path: "/knowledge/browse", changeFrequency: "weekly", priority: 0.8 },
    { path: "/knowledge/ask", changeFrequency: "daily", priority: 0.8 },
    { path: "/knowledge-graph", changeFrequency: "weekly", priority: 0.85 },
    { path: "/knowledge-graph/explorer", changeFrequency: "weekly", priority: 0.85 },

    // 7. Platform, Life Events & Reports
    { path: "/dashboard", changeFrequency: "daily", priority: 0.9 },
    { path: "/life/career", changeFrequency: "weekly", priority: 0.85 },
    { path: "/life/marriage", changeFrequency: "weekly", priority: 0.85 },
    { path: "/life/health", changeFrequency: "weekly", priority: 0.85 },
    { path: "/life/timeline", changeFrequency: "daily", priority: 0.85 },
    { path: "/reports", changeFrequency: "weekly", priority: 0.8 },
    { path: "/reports/pdf", changeFrequency: "weekly", priority: 0.8 },
    { path: "/reports/full", changeFrequency: "weekly", priority: 0.8 },
    { path: "/reports/ai", changeFrequency: "weekly", priority: 0.8 },
    { path: "/reports/comparison", changeFrequency: "weekly", priority: 0.8 },
    { path: "/reports/export", changeFrequency: "monthly", priority: 0.75 },
    { path: "/pricing", changeFrequency: "monthly", priority: 0.8 },
    { path: "/help", changeFrequency: "weekly", priority: 0.8 },
    { path: "/account", changeFrequency: "weekly", priority: 0.7 },

    // 8. Settings & Customization
    { path: "/settings", changeFrequency: "monthly", priority: 0.7 },
    { path: "/settings/profile", changeFrequency: "monthly", priority: 0.7 },
    { path: "/settings/astrology", changeFrequency: "monthly", priority: 0.75 },
    { path: "/settings/ai", changeFrequency: "monthly", priority: 0.7 },
    { path: "/settings/appearance", changeFrequency: "monthly", priority: 0.7 },
    { path: "/settings/security", changeFrequency: "monthly", priority: 0.7 },
    { path: "/settings/data", changeFrequency: "monthly", priority: 0.7 },
    { path: "/settings/notifications", changeFrequency: "monthly", priority: 0.65 },

    // 9. Visual HTML Sitemap
    { path: "/sitemap", changeFrequency: "daily", priority: 0.75 },
  ];

  return routes.map((r) => ({
    url: `${baseUrl}${r.path}`,
    lastModified,
    changeFrequency: r.changeFrequency,
    priority: r.priority,
  }));
}
