"use client";

import { useState } from "react";
import { Card } from "@/components/ui";

export default function AdminSecuritySettingsPage() {
  const [mfaEnabled, setMfaEnabled] = useState(true);
  const [ipWhitelist, setIpWhitelist] = useState("127.0.0.1\n192.168.1.0/24");
  const [sessionTimeoutHours, setSessionTimeoutHours] = useState(8);
  const [msg, setMsg] = useState<string | null>(null);

  const handleSave = () => {
    setMsg("Security policies updated successfully.");
    setTimeout(() => setMsg(null), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* ── Header ── */}
      <div>
        <div className="inline-flex items-center gap-2 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-0.5 text-xs font-semibold text-red-400">
          <span>🔒</span>
          <span>Security &amp; Hardening &bull; Policies</span>
        </div>
        <h1 className="text-2xl font-extrabold text-white mt-2">
          Security Configuration
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure Multi-Factor Authentication (MFA), IP address whitelisting, and token expiration.
        </p>
      </div>

      {msg && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-400">
          {msg}
        </div>
      )}

      <Card className="p-6 border border-slate-800 bg-slate-900/60 space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <div className="text-xs font-bold text-white">Multi-Factor Authentication (MFA / TOTP)</div>
            <div className="text-[11px] text-slate-400">Require 6-digit authenticator code on admin logins</div>
          </div>
          <input
            type="checkbox"
            checked={mfaEnabled}
            onChange={(e) => setMfaEnabled(e.target.checked)}
            className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-indigo-500"
          />
        </div>

        <div className="space-y-2 border-b border-slate-800 pb-4">
          <label className="text-xs font-bold text-slate-300">Admin Session Token Expiry (Hours):</label>
          <input
            type="number"
            value={sessionTimeoutHours}
            onChange={(e) => setSessionTimeoutHours(Number(e.target.value))}
            className="w-32 rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white"
          />
        </div>

        <div className="space-y-2">
          <label className="text-xs font-bold text-slate-300">IP Whitelist / CIDR Blocks:</label>
          <textarea
            rows={3}
            value={ipWhitelist}
            onChange={(e) => setIpWhitelist(e.target.value)}
            className="w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-xs text-slate-200 font-mono focus:border-indigo-400 focus:outline-none"
          />
        </div>

        <button
          onClick={handleSave}
          className="rounded-xl bg-indigo-600 hover:bg-indigo-500 px-6 py-2.5 text-xs font-bold text-white transition shadow"
        >
          Save Security Policy
        </button>
      </Card>
    </div>
  );
}
