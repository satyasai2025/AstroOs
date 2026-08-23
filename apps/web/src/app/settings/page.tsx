"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { SettingsLayout } from "@/components/settings/SettingsLayout";
import { Card, Icon, type IconName } from "@/components/ui";
import { useCurrentUser } from "@/lib/auth";

interface SettingsCategory {
  id: string;
  title: string;
  href: string;
  icon: IconName;
  accentColor: string;
  description: string;
  keySettings: string[];
  badge: string;
}

const SETTINGS_CATEGORIES: SettingsCategory[] = [
  {
    id: "profile",
    title: "Profile & Practitioner Credentials",
    href: "/settings/profile",
    icon: "user",
    accentColor: "from-cyan-500 to-blue-600",
    description:
      "Manage your personal identity, contact details, timezone, astrological specializations, avatar emblem, and bio.",
    keySettings: ["Display Name & Email", "Astrological Specializations", "Practitioner Level & Bio", "Default Timezone (IST/UTC)"],
    badge: "Identity & Credentials",
  },
  {
    id: "astrology",
    title: "Astrology & Calculation Engine",
    href: "/settings/astrology",
    icon: "star",
    accentColor: "from-amber-400 to-orange-500",
    description:
      "Configure your preferred Ayanamsa (Lahiri, KP, Raman), House Division System, Chart Style (North/South Indian), Node Types, and Dasha defaults.",
    keySettings: ["Ayanamsa (Lahiri/KP/Raman)", "House System (Whole Sign / Placidus)", "Chart Style (North/South Indian)", "True vs Mean Lunar Node"],
    badge: "Swiss Ephemeris Defaults",
  },
  {
    id: "ai",
    title: "AI Intelligence & Model Providers",
    href: "/settings/ai",
    icon: "cpu",
    accentColor: "from-purple-500 to-indigo-600",
    description:
      "Bring Your Own Key (BYOK) for Gemini, Anthropic Claude, OpenAI, OpenRouter, or local Ollama for automated chart explanations and reasoning.",
    keySettings: ["API Key Management", "Provider & Model Selection", "Temperature & Token Limits", "Connection Health Test"],
    badge: "BYOK Customization",
  },
  {
    id: "appearance",
    title: "Appearance, Theme & Density",
    href: "/settings/appearance",
    icon: "palette",
    accentColor: "from-pink-500 to-rose-600",
    description:
      "Switch between Dark, Light, and System themes, customize primary accent colors (Cyan, Violet, Emerald, Gold), and set display density.",
    keySettings: ["Theme (Dark / Light / System)", "Accent Color Palette", "Comfortable vs Compact Density", "High Contrast Mode"],
    badge: "UI & Visuals",
  },
  {
    id: "security",
    title: "Security, Password & Sessions",
    href: "/settings/security",
    icon: "shield",
    accentColor: "from-emerald-500 to-teal-600",
    description:
      "Update your account password, manage active browser login sessions, configure two-factor authentication, and monitor security events.",
    keySettings: ["Change Account Password", "Active Device & Session Log", "Two-Factor Authentication", "Remote Session Sign Out"],
    badge: "Access & Security",
  },
  {
    id: "data",
    title: "Data Storage, Backup & Exports",
    href: "/settings/data",
    icon: "database",
    accentColor: "from-blue-500 to-cyan-600",
    description:
      "Export your complete horoscope library and research datasets in JSON/CSV, import backups, purge cached computations, or manage account data.",
    keySettings: ["Export Charts JSON / CSV", "Backup Research Cohorts", "Clear Offline Local Cache", "Account Data Purge"],
    badge: "Portability & Backups",
  },
];

export default function SettingsHubPage() {
  const { data: user } = useCurrentUser();
  const [searchQuery, setSearchQuery] = useState("");

  const filteredCategories = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return SETTINGS_CATEGORIES;

    return SETTINGS_CATEGORIES.filter(
      (cat) =>
        cat.title.toLowerCase().includes(q) ||
        cat.description.toLowerCase().includes(q) ||
        cat.keySettings.some((k) => k.toLowerCase().includes(q))
    );
  }, [searchQuery]);

  return (
    <SettingsLayout
      title="Settings &amp; Preferences Hub"
      description="Configure your astrological calculations, account credentials, AI models, UI theme, and data backups."
    >
      <div className="space-y-8">
        {/* ── Search and Quick Banner ── */}
        <div className="relative overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800 bg-gradient-to-br from-slate-900 via-slate-850 to-slate-950 p-6 text-white shadow-xl">
          <div className="relative z-10 max-w-2xl space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-300">
              <span>⚙️</span>
              <span>AstroOS Platform Configuration</span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight sm:text-3xl text-white">
              Manage Your Platform Preferences
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Fine-tune calculation algorithms, personalized astrological credentials, external AI integrations, and privacy controls.
            </p>

            {/* Instant Search Bar */}
            <div className="relative mt-4 max-w-lg">
              <input
                type="text"
                placeholder="Search settings (e.g. Ayanamsa, Password, API Key, Theme, Timezone)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-800/90 py-2.5 pl-10 pr-4 text-xs sm:text-sm text-slate-100 placeholder-slate-400 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20"
              />
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
                <Icon name="search" style={{ width: 16, height: 16 }} />
              </div>
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-xs text-slate-400 hover:text-white"
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        </div>

        {/* ── Settings Categories Grid ── */}
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
          {filteredCategories.map((cat) => (
            <Link key={cat.id} href={cat.href} className="group block">
              <Card className="h-full flex flex-col justify-between p-5 border border-slate-200 dark:border-slate-800 transition-all hover:border-cyan-500/50 hover:shadow-lg hover:shadow-cyan-500/5 group-hover:-translate-y-0.5">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div
                      className={`flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br ${cat.accentColor} text-white shadow-md`}
                    >
                      <Icon name={cat.icon} style={{ width: 22, height: 22 }} />
                    </div>
                    <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2.5 py-0.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400">
                      {cat.badge}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors">
                      {cat.title}
                    </h3>
                    <p className="mt-1 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                      {cat.description}
                    </p>
                  </div>

                  <div className="space-y-1 pt-2 border-t border-slate-100 dark:border-slate-800">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Key Options:
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {cat.keySettings.map((keyOpt, i) => (
                        <span
                          key={i}
                          className="rounded bg-slate-100 dark:bg-slate-800/80 px-2 py-0.5 text-[10px] text-slate-700 dark:text-slate-300"
                        >
                          {keyOpt}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-semibold text-cyan-600 dark:text-cyan-400">
                  <span>Configure {cat.title.split(" ")[0]}</span>
                  <span className="transition-transform group-hover:translate-x-1">&rarr;</span>
                </div>
              </Card>
            </Link>
          ))}
        </div>

        {/* ── Quick Help & Documentation Card ── */}
        <Card className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border border-cyan-500/20 bg-cyan-500/5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-cyan-500 text-slate-950">
              <Icon name="book" style={{ width: 20, height: 20 }} />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Looking for tool instructions and astrological interpretation rules?
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Check out the interactive AstroOS User Manual with detailed guides on SBC, Tarabala, KP, Dasha, and Divisional Charts.
              </p>
            </div>
          </div>
          <Link
            href="/help"
            className="inline-flex flex-shrink-0 items-center gap-1.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 px-4 py-2 text-xs font-bold text-slate-950 transition shadow-sm"
          >
            <span>Open User Guide</span>
            <span>&rarr;</span>
          </Link>
        </Card>
      </div>
    </SettingsLayout>
  );
}
