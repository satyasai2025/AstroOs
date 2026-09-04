"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui";

interface ApiKeyItem {
  id: string;
  name: string;
  prefix: string;
  tier: string;
  rateLimit: string;
  created_at: string;
  status: "active" | "revoked";
}

const DEFAULT_KEYS: ApiKeyItem[] = [
  {
    id: "key_001",
    name: "Production Web App",
    prefix: "ak_live_7f8a...",
    tier: "Enterprise (Unlimited)",
    rateLimit: "1,000 req/min",
    created_at: "2026-08-27",
    status: "active",
  },
  {
    id: "key_002",
    name: "Research Batch Exporter",
    prefix: "ak_live_2c3b...",
    tier: "Scholar Tier",
    rateLimit: "300 req/min",
    created_at: "2026-08-20",
    status: "active",
  },
];

export default function AdminApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyItem[]>(DEFAULT_KEYS);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleRevoke = (id: string) => {
    setKeys((prev) =>
      prev.map((k) =>
        k.id === id ? { ...k, status: k.status === "active" ? "revoked" : "active" } : k
      )
    );
  };

  if (!mounted) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="text-xs text-slate-400">Loading API Keys...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div>
        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-0.5 text-xs font-semibold text-emerald-400">
          <span>🔑</span>
          <span>Developer Platform &bull; API Keys</span>
        </div>
        <h1 className="text-2xl font-extrabold text-white mt-2">
          API Keys &amp; Developer Access
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Manage developer API tokens, rate limiting quotas, and revoke compromised keys.
        </p>
      </div>

      <Card className="p-0 overflow-hidden border border-slate-800 bg-slate-900/60">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                <th className="py-3 px-4 font-semibold">Key Name</th>
                <th className="py-3 px-4 font-semibold">Token Prefix</th>
                <th className="py-3 px-4 font-semibold">Access Tier</th>
                <th className="py-3 px-4 font-semibold">Rate Limit</th>
                <th className="py-3 px-4 font-semibold">Created</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {keys.map((k) => (
                <tr key={k.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-3 px-4 font-bold text-white">{k.name}</td>
                  <td className="py-3 px-4 font-mono text-[11px] text-cyan-400">{k.prefix}</td>
                  <td className="py-3 px-4">{k.tier}</td>
                  <td className="py-3 px-4 text-slate-400">{k.rateLimit}</td>
                  <td className="py-3 px-4 text-slate-400">{k.created_at}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                        k.status === "active"
                          ? "bg-emerald-500/20 text-emerald-400"
                          : "bg-red-500/20 text-red-400"
                      }`}
                    >
                      {k.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => toggleRevoke(k.id)}
                      className="rounded bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-[11px] font-bold text-red-400 border border-slate-700"
                    >
                      {k.status === "active" ? "Revoke" : "Reactivate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
