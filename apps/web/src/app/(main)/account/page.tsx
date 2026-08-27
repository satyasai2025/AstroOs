"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import {
  DashboardSummary,
  fetchDashboardSummary,
} from "@/lib/billing";
import { useCurrentUser } from "@/lib/auth";
import { Badge, Button, Card, Icon } from "@/components/ui";

export default function AccountDashboardPage() {
  const { data: user } = useCurrentUser();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "charts" | "billing" | "security">("overview");

  useEffect(() => {
    async function loadSummary() {
      setLoading(true);
      try {
        const data = await fetchDashboardSummary();
        setSummary(data);
      } catch (err) {
        console.error("Failed to load dashboard summary", err);
      } finally {
        setLoading(false);
      }
    }
    loadSummary();
  }, []);

  const getPlanBadge = (code?: string) => {
    switch (code) {
      case "RESEARCH":
        return <span className="rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 px-3 py-0.5 text-xs font-bold">RESEARCH SCHOLAR</span>;
      case "PRO":
        return <span className="rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-3 py-0.5 text-xs font-bold">PRO PRACTITIONER</span>;
      case "CUSTOM":
        return <span className="rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-0.5 text-xs font-bold">ENTERPRISE</span>;
      default:
        return <span className="rounded-full bg-slate-800 text-slate-400 border border-slate-700 px-3 py-0.5 text-xs font-bold">FREE COMMUNITY</span>;
    }
  };

  return (
    <AppShell>
      <div className="min-h-screen bg-slate-950 text-slate-100 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* ── Practitioner Identity Banner ── */}
          <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-850 to-slate-950 p-6 sm:p-8 shadow-xl">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 text-2xl font-extrabold text-slate-950 shadow-lg">
                  {summary?.display_name?.charAt(0).toUpperCase() || "ॐ"}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2.5">
                    <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
                      {summary?.display_name || user?.display_name || "Practitioner"}
                    </h1>
                    {getPlanBadge(summary?.plan_code)}
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    {summary?.email || user?.email} &bull; Timezone: Asia/Kolkata (IST)
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Link
                  href="/pricing"
                  className="rounded-xl bg-cyan-500 hover:bg-cyan-400 px-4 py-2 text-xs font-bold text-slate-950 transition shadow"
                >
                  Upgrade Tier
                </Link>
                <Link
                  href="/settings/profile"
                  className="rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-750 px-4 py-2 text-xs font-bold text-slate-200 transition"
                >
                  Edit Profile
                </Link>
              </div>
            </div>
          </div>

          {/* ── 4 Quick Metric Gauges ── */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* 1. Saved Horoscopes */}
            <Card className="p-5 border border-slate-800 bg-slate-900/60 space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="font-semibold text-slate-300">Saved Horoscopes</span>
                <span className="text-cyan-400 font-bold">
                  {summary?.saved_horoscopes_count || 0} / {summary?.saved_horoscopes_limit ?? "∞"}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-cyan-500 rounded-full"
                  style={{
                    width: `${
                      summary?.saved_horoscopes_limit
                        ? Math.min(100, ((summary.saved_horoscopes_count || 0) / summary.saved_horoscopes_limit) * 100)
                        : 20
                    }%`,
                  }}
                />
              </div>
              <div className="flex items-center justify-between text-[11px] pt-1">
                <Link href="/charts/birth" className="text-cyan-400 hover:underline font-medium">
                  + Calculate New Chart
                </Link>
                <Link href="/charts/history" className="text-slate-400 hover:text-white">
                  View All &rarr;
                </Link>
              </div>
            </Card>

            {/* 2. Monthly Research Runs */}
            <Card className="p-5 border border-slate-800 bg-slate-900/60 space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="font-semibold text-slate-300">Research Projects</span>
                <span className="text-purple-400 font-bold">
                  {summary?.research_runs_used || 0} / {summary?.research_runs_limit ?? "0 on Free"}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-purple-500 rounded-full"
                  style={{
                    width: `${summary?.research_runs_limit ? 30 : 0}%`,
                  }}
                />
              </div>
              <div className="flex items-center justify-between text-[11px] pt-1">
                <Link href="/research" className="text-purple-400 hover:underline font-medium">
                  Open Research Studio
                </Link>
                <span className="text-slate-500">Resets monthly</span>
              </div>
            </Card>

            {/* 3. Subscription Status */}
            <Card className="p-5 border border-slate-800 bg-slate-900/60 space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="font-semibold text-slate-300">Subscription Plan</span>
                <span className="text-emerald-400 font-bold uppercase">
                  {summary?.subscription_status || "Active (Free)"}
                </span>
              </div>
              <p className="text-sm font-extrabold text-white">
                AstroOS {summary?.plan_code || "FREE"}
              </p>
              <div className="flex items-center justify-between text-[11px] pt-1">
                <Link href="/settings/billing" className="text-cyan-400 hover:underline font-medium">
                  Manage Invoices
                </Link>
                <Link href="/pricing" className="text-slate-400 hover:text-white">
                  Change Plan &rarr;
                </Link>
              </div>
            </Card>

            {/* 4. Security & Sessions */}
            <Card className="p-5 border border-slate-800 bg-slate-900/60 space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="font-semibold text-slate-300">Security Health</span>
                <span className="text-emerald-400 font-bold">Secure</span>
              </div>
              <p className="text-sm font-extrabold text-white">
                Password Active &bull; 2FA Ready
              </p>
              <div className="flex items-center justify-between text-[11px] pt-1">
                <Link href="/settings/security" className="text-cyan-400 hover:underline font-medium">
                  Session Controls
                </Link>
                <Link href="/settings/security" className="text-slate-400 hover:text-white">
                  Update Password &rarr;
                </Link>
              </div>
            </Card>
          </div>

          {/* ── Direct Quick Links Hub ── */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Quick Link 1: Calculation Suite */}
            <Card className="p-5 border border-slate-800 bg-slate-900/40 space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🪐</span>
                <div>
                  <h3 className="text-sm font-bold text-white">Ephemeris &amp; Charts</h3>
                  <p className="text-xs text-slate-400">Compute D1-D60, Vimshottari, KP, and SBC charts.</p>
                </div>
              </div>
              <div className="pt-2 flex flex-wrap gap-2 text-xs">
                <Link href="/charts/birth" className="rounded-lg bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-slate-300">
                  Birth Chart
                </Link>
                <Link href="/charts/transit" className="rounded-lg bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-slate-300">
                  Transit Sky Clock
                </Link>
                <Link href="/charts/dasha" className="rounded-lg bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-slate-300">
                  Multi-Dasha
                </Link>
              </div>
            </Card>

            {/* Quick Link 2: Research Tools */}
            <Card className="p-5 border border-slate-800 bg-slate-900/40 space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🔬</span>
                <div>
                  <h3 className="text-sm font-bold text-white">Research Workspace</h3>
                  <p className="text-xs text-slate-400">Statistical cohort correlation and AstroDSL rule authoring.</p>
                </div>
              </div>
              <div className="pt-2 flex flex-wrap gap-2 text-xs">
                <Link href="/research" className="rounded-lg bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-slate-300">
                  Cohort Studio
                </Link>
                <Link href="/knowledge-graph" className="rounded-lg bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-slate-300">
                  Knowledge Graph
                </Link>
              </div>
            </Card>

            {/* Quick Link 3: Preferences & Invoices */}
            <Card className="p-5 border border-slate-800 bg-slate-900/40 space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">⚙️</span>
                <div>
                  <h3 className="text-sm font-bold text-white">Account Settings</h3>
                  <p className="text-xs text-slate-400">Invoices, Swiss Ephemeris defaults, and notifications.</p>
                </div>
              </div>
              <div className="pt-2 flex flex-wrap gap-2 text-xs">
                <Link href="/settings/billing" className="rounded-lg bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-slate-300">
                  Billing &amp; GST Invoices
                </Link>
                <Link href="/settings/notifications" className="rounded-lg bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-slate-300">
                  Notifications
                </Link>
                <Link href="/settings/astrology" className="rounded-lg bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-slate-300">
                  Ayanamsa Defaults
                </Link>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
