"use client";

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
  { label: "Yogas", value: "1,285", accent: "violet", icon: "◎", type: "yogas" },
  { label: "Karakatvas", value: "5,462", accent: "gold", icon: "▤", type: "karakatvas" },
  { label: "Classical Texts", value: "37", accent: "cyan", icon: "▧", type: "texts" },
  { label: "Rules", value: "12,845", accent: "success", icon: "⚗", type: "rules" },
];

const CATEGORIES = [
  { icon: "☉", label: "Planets", desc: "Nature, Ownership, Exaltation, Debilitation, Aspects, Strength…", count: 9, type: "planets" },
  { icon: "▦", label: "Signs (Rashi)", desc: "Characteristics, Elements, Qualities, Strength, Body Parts…", count: 12, type: "signs" },
  { icon: "⌂", label: "Houses (Bhava)", desc: "Meanings, Karakatvas, Body Parts, Professions, Events…", count: 12, type: "houses" },
  { icon: "★", label: "Nakshatras", desc: "Deities, Symbols, Lords, Ganas, Yoni, Nadi, Characteristics…", count: 27, type: "nakshatras" },
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
  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Knowledge Home
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Centralized knowledge base of Vedic Astrology
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button href="/knowledge/browse" variant="violet">
            Browse Entities
          </Button>
          <Button href="/knowledge/tools" variant="secondary">
            Knowledge Tools
          </Button>
          <Button href="/knowledge/admin" variant="secondary">
            Admin
          </Button>
        </div>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
        {STATS.map((s) => (
          <StatCard key={s.label} stat={s} />
        ))}
      </div>

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
    </div>
  );
}
