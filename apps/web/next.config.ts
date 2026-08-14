import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // API requests forwarded to FastAPI backend
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiBase}/api/:path*`,
      },
    ];
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
};

export default nextConfig;
