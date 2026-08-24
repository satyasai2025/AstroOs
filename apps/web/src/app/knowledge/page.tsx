"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Badge, Button, Card, KnowledgeGraph } from "@/components/ui";

interface StatDef {
  label: string;
  value: string;
  accent: "cyan" | "violet" | "gold" | "success";
  icon: string;
  type: string;
}

/**
 * These counts are placeholders matching the "AstroOS v2.3 Infographic" kit
 * mockup exactly (per explicit user direction — real wiring against the
 * backend catalogues comes later). Karakatvas is the one figure this app
 * genuinely has real data for today (450 seeded entries via
 * apps.api.scripts.seed_knowledge) — everything else here traces to no
 * live endpoint yet.
 */
const STATS: StatDef[] = [
  { label: "Planets", value: "9", accent: "cyan", icon: "☉", type: "planets" },
  { label: "Signs", value: "12", accent: "success", icon: "▦", type: "signs" },
  { label: "Houses", value: "12", accent: "cyan", icon: "⌂", type: "houses" },
  { label: "Nakshatras", value: "27", accent: "gold", icon: "★", type: "nakshatras" },
  { label: "Classical Yogas", value: "1,285", accent: "violet", icon: "◎", type: "yogas" },
  { label: "Divisional Charts", value: "16", accent: "cyan", icon: "☸", type: "vargas" },
  { label: "Dasha Systems", value: "5", accent: "gold", icon: "⏳", type: "dashas" },
  { label: "Ashtakavarga", value: "8", accent: "success", icon: "🔢", type: "ashtakavarga" },
  { label: "Transits (Gochara)", value: "5", accent: "cyan", icon: "🪐", type: "transits" },
  { label: "Shadbala", value: "6", accent: "gold", icon: "⚖", type: "shadbala" },
  { label: "Sahamas", value: "5", accent: "violet", icon: "🎯", type: "sahamas" },
  { label: "Prashna & KP", value: "249", accent: "cyan", icon: "🔮", type: "prashna_kp" },
  { label: "Karakatvas", value: "5,462", accent: "gold", icon: "▤", type: "karakatvas" },
  { label: "Classical Texts", value: "37", accent: "cyan", icon: "📜", type: "texts" },
  { label: "Vedic Rules Engine", value: "12,845", accent: "success", icon: "⚗", type: "rules" },
];

const CATEGORIES = [
  { icon: "☉", label: "Planets (Navagraha)", desc: "Nature, Ownership, Exaltation, Debilitation, Aspects, Strength…", count: 9, type: "planets" },
  { icon: "▦", label: "Signs (Rashi)", desc: "Characteristics, Elements, Qualities, Strength, Body Parts…", count: 12, type: "signs" },
  { icon: "⌂", label: "Houses (Bhava)", desc: "Meanings, Karakatvas, Body Parts, Professions, Events…", count: 12, type: "houses" },
  { icon: "★", label: "Nakshatras (27 Stars)", desc: "Deities, Symbols, Lords, Ganas, Yoni, Nadi, Characteristics…", count: 27, type: "nakshatras" },
  { icon: "◎", label: "Classical Yogas", desc: "Gaja Kesari, Raja Yogas, Pancha Mahapurusha, Dhana Yogas…", count: 10, type: "yogas" },
  { icon: "☸", label: "Divisional Charts (Shodashavarga)", desc: "D1, D9, D10, D12, D60 fine divisional mapping…", count: 16, type: "vargas" },
  { icon: "⏳", label: "Dashas & Timing Systems", desc: "Vimshottari, Ashtottari, Yogini, Chara, Kalachakra Dasha…", count: 5, type: "dashas" },
  { icon: "🔢", label: "Ashtakavarga & Kakshya", desc: "BAV (0-8), SAV (0-56), and 8 Kakshya subdivisions…", count: 3, type: "ashtakavarga" },
  { icon: "🪐", label: "Transits (Gochara, Vedha, Latta)", desc: "Sade Sati, Ashtama Shani, Murthi Nirnaya, Vedha, Latta…", count: 5, type: "transits" },
  { icon: "⚖", label: "Shadbala & Strengths", desc: "Sthana, Dig, Kala, Chesta, Naisargika, Drik Bala…", count: 6, type: "shadbala" },
  { icon: "🎯", label: "Sahamas (Arabic Parts)", desc: "Punya, Vidya, Vivaha, Karma, Raja Sahamas…", count: 5, type: "sahamas" },
  { icon: "🔮", label: "Prashna & KP Sub-Lord", desc: "Horary seed numbers 1-249, Sub-Lord, Cuspal Interlinks…", count: 3, type: "prashna_kp" },
  { icon: "▤", label: "Karakatvas (Significations)", desc: "Natural & Jaimini Karakas, 450+ seeded significations…", count: 450, type: "karakatvas" },
  { icon: "📜", label: "Classical Texts & Scriptures", desc: "BPHS, Saravali, Phaladeepika, Jataka Parijata, Uttara Kalamrita…", count: 6, type: "texts" },
  { icon: "⚗", label: "Vedic Rules Engine", desc: "Classical rule definitions evaluated against real charts…", count: 4, type: "rules" },
];

const POPULAR_YOGAS = [
  { name: "Gaja Kesari Yoga", desc: "Jupiter in Kendra from Moon", tone: "Benefic" as const },
  { name: "Raj Yoga (Multiple)", desc: "Combination of Kendra & Trikona", tone: "Benefic" as const },
];

const GRAPH_NODES = [
  { id: "sun", x: 90, y: 60, label: "Sun", color: "var(--gold-400)", size: 22 },
  { id: "moon", x: 200, y: 50, label: "Moon", color: "var(--cyan-400)", size: 16 },
  { id: "mars", x: 210, y: 140, label: "Mars", color: "var(--violet-400)", size: 14 },
];
const GRAPH_EDGES = [
  { from: "sun", to: "moon" },
  { from: "sun", to: "mars" },
];

const SUGGESTIONS = [
  { label: "✨ Gaja Kesari Yoga", action: "/knowledge/browse?type=yogas" },
  { label: "☉ Sun Karakatvas", action: "/knowledge/browse?type=karakatvas" },
  { label: "⌂ 10th House (Career)", action: "/knowledge/browse?type=houses" },
  { label: "★ Ashwini Nakshatra", action: "/knowledge/browse?type=nakshatras" },
  { label: "📜 BPHS Classical Texts", action: "/knowledge/browse?type=texts" },
  { label: "🤖 Ask: Jupiter in 7th House", action: "/knowledge/ask?q=What%20is%20the%20effect%20of%20Jupiter%20in%20the%207th%20House?" },
];

function StatCard({ stat }: { stat: StatDef }) {
  const accentVar =
    stat.accent === "cyan"
      ? "var(--cyan-400)"
      : stat.accent === "violet"
        ? "var(--violet-400)"
        : stat.accent === "gold"
          ? "var(--gold-400)"
          : "var(--success-400)";
  return (
    <Card style={{ display: "flex", flexDirection: "column", gap: 10, minWidth: 0 }}>
      <span style={{ fontSize: 20, color: accentVar }} aria-hidden="true">
        {stat.icon}
      </span>
      <div>
        <p style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>{stat.label}</p>
        <p style={{ fontFamily: "var(--font-display)", fontSize: "var(--text-2xl)", fontWeight: "var(--weight-bold)", color: "var(--text-primary)" }}>
          {stat.value}
        </p>
      </div>
      <a href={`/knowledge/browse?type=${stat.type}`} style={{ fontSize: "var(--text-xs)", color: accentVar }}>
        View all
      </a>
    </Card>
  );
}

export default function KnowledgeHomePage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

  const handleAskAI = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) {
      router.push("/knowledge/ask");
    } else {
      router.push(`/knowledge/ask?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleBrowse = () => {
    router.push("/knowledge/browse");
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Knowledge Home
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Centralized knowledge base & classical reference engine of Vedic Astrology
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button href="/knowledge/ask" variant="primary">
            Ask AstroOS
          </Button>
          <Button href="/knowledge/browse" variant="violet">
            Browse Entities
          </Button>
          <Button href="/help" variant="secondary">
            Help Center
          </Button>
          <Button href="/knowledge/admin" variant="secondary">
            Admin
          </Button>
        </div>
      </div>

      {/* Global Knowledge Search Hero Card */}
      <Card style={{ padding: "20px 24px", background: "linear-gradient(180deg, var(--bg-card) 0%, rgba(56, 189, 248, 0.04) 100%)" }}>
        <div className="max-w-3xl">
          <div className="mb-2 flex items-center gap-2">
            <span className="text-base" aria-hidden="true">🔍</span>
            <h2 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
              Search Knowledge Base & Classical Texts
            </h2>
          </div>
          <p className="mb-4 text-xs" style={{ color: "var(--text-secondary)" }}>
            Ask a natural question to AI, search 5,000+ Karakatvas, explore Yogas, or lookup classical slokas from BPHS & Saravali.
          </p>

          <form onSubmit={handleAskAI} className="flex flex-col gap-2 sm:flex-row">
            <div className="relative flex-1">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search concepts, e.g. 'Gaja Kesari Yoga', 'Jupiter in 7th House', 'Mesha Rashi'…"
                className="w-full rounded-lg px-3.5 py-2.5 text-sm outline-none transition-all"
                style={{
                  backgroundColor: "var(--bg-surface, var(--bg-card))",
                  border: "1px solid var(--border-primary)",
                  color: "var(--text-primary)",
                }}
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit" variant="primary">
                Ask AI Q&A
              </Button>
              <Button type="button" onClick={handleBrowse} variant="secondary">
                Browse Entities
              </Button>
            </div>
          </form>

          {/* Quick suggestions */}
          <div className="mt-3 flex flex-wrap items-center gap-1.5 pt-2">
            <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
              Quick Examples:
            </span>
            {SUGGESTIONS.map((item) => (
              <Link
                key={item.label}
                href={item.action}
                className="inline-flex items-center rounded-md px-2 py-0.5 text-xs transition-colors hover:opacity-80"
                style={{
                  backgroundColor: "var(--bg-subtle, rgba(255, 255, 255, 0.05))",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-secondary)",
                }}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
        {STATS.map((s) => (
          <StatCard key={s.label} stat={s} />
        ))}
      </div>

      {/* 3 Columns Section */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card padding="0" style={{ gridColumn: "span 1" }}>
          <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>
              Knowledge Categories
            </span>
          </div>
          <div>
            {CATEGORIES.map((c) => (
              <a
                key={c.label}
                href={`/knowledge/browse?type=${c.type}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "12px 18px",
                  borderBottom: "1px solid var(--border-subtle)",
                }}
              >
                <span style={{ fontSize: 16 }} aria-hidden="true">
                  {c.icon}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)", color: "var(--text-primary)" }}>{c.label}</p>
                  <p style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>{c.desc}</p>
                </div>
                <span style={{ fontSize: "var(--text-sm)", color: "var(--text-tertiary)" }}>{c.count}</span>
              </a>
            ))}
          </div>
        </Card>

        <Card padding="0">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 18px", borderBottom: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>Popular Yogas</span>
            <a href="/knowledge/browse?type=yogas" style={{ fontSize: "var(--text-xs)", color: "var(--cyan-400)" }}>
              View all
            </a>
          </div>
          <div style={{ padding: "6px 18px" }}>
            {POPULAR_YOGAS.map((y) => (
              <div key={y.name} style={{ display: "flex", justifyContent: "space-between", gap: 8, padding: "10px 0", borderBottom: "1px solid var(--border-subtle)" }}>
                <div>
                  <p style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)", color: "var(--text-primary)" }}>{y.name}</p>
                  <p style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>{y.desc}</p>
                </div>
                <Badge tone="success">{y.tone}</Badge>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <p className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Knowledge Graph
          </p>
          <KnowledgeGraph nodes={GRAPH_NODES} edges={GRAPH_EDGES} width={260} height={170} />
        </Card>
      </div>

      {/* How To Use & Help Guide Section */}
      <Card style={{ padding: "20px 24px" }}>
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base">💡</span>
              <h3 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
                How to use AstroOS Knowledge Base
              </h3>
            </div>
            <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
              Quick guide on searching, querying AI, and verifying classical astrological literature.
            </p>
          </div>
          <Link
            href="/help"
            className="inline-flex items-center gap-1 text-xs font-semibold hover:underline"
            style={{ color: "var(--cyan-400)" }}
          >
            Visit Full AstroOS Help Center →
          </Link>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-lg p-3.5" style={{ backgroundColor: "var(--bg-subtle, rgba(255, 255, 255, 0.02))", border: "1px solid var(--border-subtle)" }}>
            <div className="mb-1 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              🤖 1. Ask Classical Questions
            </div>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
              Use <strong>Ask AstroOS</strong> to query combinations (e.g. <em>"Sun in 10th house"</em>). Answers cite verified classical texts like BPHS and Saravali without hallucinations.
            </p>
          </div>

          <div className="rounded-lg p-3.5" style={{ backgroundColor: "var(--bg-subtle, rgba(255, 255, 255, 0.02))", border: "1px solid var(--border-subtle)" }}>
            <div className="mb-1 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              📊 2. Explore 5,000+ Karakatvas
            </div>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
              Filter through planetary significations and house meanings under <strong>Browse Entities</strong> to discover deeper interpretive nuances for each planet and sign.
            </p>
          </div>

          <div className="rounded-lg p-3.5" style={{ backgroundColor: "var(--bg-subtle, rgba(255, 255, 255, 0.02))", border: "1px solid var(--border-subtle)" }}>
            <div className="mb-1 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              📚 3. Classical Literature & Rules
            </div>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
              Inspect astrological rules and slokas evaluated by the calculation engine to understand why a chart prediction or yoga is triggered.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
