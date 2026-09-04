import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  outputFileTracingRoot: path.join(__dirname, "..", ".."),
  // ── Rewrites ────────────────────────────────────────────────────────────────
  // beforeFiles aliases run before file-system routes.
  // afterFiles keeps the existing /api/* → FastAPI proxy unchanged.
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    return [
      { source: "/api/:path*", destination: `${apiBase}/api/:path*` },
    ];
  },

  // ── Redirects ───────────────────────────────────────────────────────────────
  async redirects() {
    return [
      {
        source: "/ai/explain",
        destination: "/phalita",
        permanent: false,
      },
    ];
  },

  // Strict React mode
  reactStrictMode: true,

  allowedDevOrigins: [
    "localhost",
    "127.0.0.1",
    "192.168.1.7",
    "localhost:3000",
    "127.0.0.1:3000",
    "192.168.1.7:3000",
    "*.monkeycode-ai.live",
  ],

  // Output standalone for Docker / production
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,

  // ESLint during builds is handled separately via dedicated lint scripts
  eslint: {
    ignoreDuringBuilds: true,
  },
};


export default nextConfig;
