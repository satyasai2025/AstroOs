import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  outputFileTracingRoot: path.join(__dirname, "..", ".."),
  // ── Rewrites ────────────────────────────────────────────────────────────────
  // beforeFiles aliases run before file-system routes.
  // afterFiles keeps the existing /api/* → FastAPI proxy unchanged.
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    return {
      beforeFiles: [
        // ── Chart view clean-URL aliases ──────────────────────────────────
        // Each maps a semantic slug → the existing ?view= param so that
        // charts/page.tsx ViewMode switch and all calculation hooks are
        // untouched. The browser sees the clean URL; Next.js serves the
        // query-param route internally.
        { source: "/charts/birth",         destination: "/charts?view=chart" },
        { source: "/charts/kundli",        destination: "/charts?view=kundli" },
        { source: "/charts/divisional",    destination: "/charts?view=divisional" },
        { source: "/charts/houses",        destination: "/charts?view=houses" },
        { source: "/charts/relationships", destination: "/charts?view=relationships-v2" },
        { source: "/charts/dasha",         destination: "/charts?view=dasha" },
        { source: "/charts/timeline",      destination: "/charts?view=timeline" },
        { source: "/charts/strength",      destination: "/charts?view=strength" },
        { source: "/charts/kp",            destination: "/charts?view=kp" },
        { source: "/charts/yogas",         destination: "/charts?view=yogas" },
        { source: "/charts/ashtakavarga",  destination: "/charts?view=ashtakavarga" },
        { source: "/charts/jaimini",       destination: "/charts?view=jaimini" },
        { source: "/charts/planets",       destination: "/charts?view=planets" },
        { source: "/charts/nakshatra",     destination: "/charts?view=nakshatra" },
        { source: "/charts/predictions",   destination: "/charts?view=predictions" },

        // ── Research view aliases ─────────────────────────────────────────
        // Snapshot Manager was a nav duplicate of /research/projects.
        // Both slugs now map to projects with a tab hint for future sub-tabs.
        { source: "/research/snapshot",         destination: "/research/projects?tab=snapshot" },
        { source: "/research/snapshot-manager", destination: "/research/projects?tab=snapshot" },
      ],
      afterFiles: [
        // ── API proxy (unchanged) ─────────────────────────────────────────
        { source: "/api/:path*", destination: `${apiBase}/api/:path*` },
      ],
    };
  },

  // Strict React mode
  reactStrictMode: true,

  // Allow the platform preview host to hit the dev server.
  // NOTE: the option is `allowedDevOrigins` and it is TOP-LEVEL. It was
  // previously written as `experimental.allowedHosts`, which does not exist
  // in Next.js 15.5 — that produced a TS2353 type error and, worse, silently
  // did nothing, so the preview host was never actually allowed.
  allowedDevOrigins: ["*.monkeycode-ai.live"],

  // Output standalone for Docker / production
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,

  // ESLint during builds is handled separately via dedicated lint scripts
  eslint: {
    ignoreDuringBuilds: true,
  },
};


export default nextConfig;
