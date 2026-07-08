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

  // Output standalone for Docker / production
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
};

export default nextConfig;
