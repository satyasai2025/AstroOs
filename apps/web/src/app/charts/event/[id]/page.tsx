"use client";

import { useParams } from "next/navigation";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { useEventAnalysis } from "@/lib/eventAnalysis";
import type {
  EventAnalysisReport,
  EventChartArtifact,
  EventDashaArtifact,
  EventTransitArtifact,
} from "@/lib/types";

const DIMENSION_KEYS = [
  "natal_promise",
  "dasha_support",
  "transit_influence",
  "planetary_strength",
  "yogas_activated",
  "muhurta",
] as const;

const DIMENSION_TITLES: Record<string, string> = {
  natal_promise: "Natal Promise",
  dasha_support: "Dasha Support",
  transit_influence: "Transit Influence",
  planetary_strength: "Planetary Strength",
  yogas_activated: "Yogas Activated",
  muhurta: "Muhurta",
};

const STATUS_COLOR: Record<string, string> = {
  supported: "var(--obsidian-accent-success, #10B981)",
  mixed: "#fbbf24",
  weak: "var(--obsidian-status-danger, #ef4444)",
  descriptive: "var(--text-muted)",
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLOR[status] ?? "var(--text-muted)";
  return (
    <span
      className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase"
      style={{ backgroundColor: `${color}22`, color, border: `1px solid ${color}55` }}
    >
      {status}
    </span>
  );
}

export default function EventAnalysisPage() {
  const params = useParams<{ id: string }>();
  const { data, isLoading, isError, error } = useEventAnalysis(params.id ?? null);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl p-6">
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading Event Analysis…</p>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto max-w-5xl p-6">
        <h1 className="mb-2 text-lg font-bold" style={{ color: "var(--text-primary)" }}>Event Analysis</h1>
        <p className="text-sm" style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>
          Could not load this event analysis: {(error as Error)?.message ?? "unknown error"}
        </p>
      </div>
    );
  }

  const artifacts = data.artifacts ?? {};
  const eventChart = artifacts.event_chart_id ?? null;
  const transits = artifacts.transit_chart_id ?? null;
  const dasha = artifacts.dasha_snapshot_id ?? null;

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>{data.event_name}</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
          Event Analysis · {new Date(data.event_datetime_utc).toLocaleString()}
          {data.place_name ? ` · ${data.place_name}` : ""}
          {data.category ? ` · ${data.category}` : ""}
        </p>
      </div>

      {/* Score */}
      <div className="grid grid-cols-2 gap-4">
        <div
          className="rounded-lg border p-4"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}
        >
          <p className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Overall Score</p>
          <p className="mt-1 text-3xl font-bold" style={{ color: "var(--obsidian-accent-tertiary)" }}>
            {data.overall_score != null ? data.overall_score : "—"}
          </p>
        </div>
        <div
          className="rounded-lg border p-4"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}
        >
          <p className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Status</p>
          <p className="mt-1 text-sm font-semibold capitalize" style={{ color: "var(--text-primary)" }}>{data.status}</p>
          <p className="mt-1 text-[11px]" style={{ color: "var(--text-muted)" }}>Scope: {data.scope.join(", ") || "n/a"}</p>
        </div>
      </div>

      {/* Score breakdown — how the overall score was built, dimension by dimension */}
      <ScoreBreakdownSection report={data.analysis_report_json} />

      {/* Event D1 chart */}
      <EventChartSection eventChart={eventChart} name={data.event_name} />

      {/* Transits */}
      <TransitSection transits={transits} />

      {/* Dasha chain */}
      <DashaSection dasha={dasha} />

      {/* Planetary dignities (the one thing the report has that isn't shown above) */}
      <PlanetDignitySection report={data.analysis_report_json} />

      {/* Evidence behind each scored dimension */}
      <EvidenceSections report={data.analysis_report_json} />

      {data.status !== "completed" && (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          This analysis has not completed successfully — artifacts may be incomplete.
        </p>
      )}
    </div>
  );
}

function EventChartSection({ eventChart, name }: { eventChart: EventChartArtifact | null; name: string }) {
  if (!eventChart) return null;
  const planets = eventChart.planets.map((p) => ({
    planet: p.planet,
    rashi: p.rashi,
    house_number: p.house_number ?? undefined,
    is_retrograde: p.retrograde ?? false,
    rashi_degree: p.degree_in_rashi ?? undefined,
  }));
  return (
    <Section title="Event Chart">
      <div className="flex flex-col items-start gap-4 sm:flex-row">
        <NorthIndianChart
          title={`${name} — Event D1`}
          ascendant={{
            rashi: eventChart.ascendant.rashi,
            rashi_degree: eventChart.ascendant.degree_in_rashi ?? undefined,
          }}
          planets={planets}
          size={360}
        />
        <div className="flex-1 text-xs" style={{ color: "var(--text-muted)" }}>
          <p>Event Lagna: {eventChart.ascendant.rashi}</p>
          <p>{eventChart.ayanamsa_system} · {eventChart.house_system}</p>
        </div>
      </div>
    </Section>
  );
}

function TransitSection({ transits }: { transits: EventTransitArtifact | null }) {
  if (!transits || transits.transits.length === 0) return null;
  return (
    <Section title="Event Transits">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b" style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}>
              <th className="py-2 pr-3 font-semibold">Planet</th>
              <th className="py-2 pr-3 font-semibold">Transit Rashi</th>
              <th className="py-2 pr-3 font-semibold">From Moon</th>
              <th className="py-2 pr-3 font-semibold">Retro</th>
              <th className="py-2 pr-3 font-semibold">Sade Sati</th>
              <th className="py-2 pr-3 font-semibold">Vedha</th>
            </tr>
          </thead>
          <tbody style={{ color: "var(--text-primary)" }}>
            {transits.transits.map((t) => (
              <tr key={t.planet} className="border-b" style={{ borderColor: "var(--border-primary)" }}>
                <td className="py-1.5 pr-3 capitalize">{t.planet}</td>
                <td className="py-1.5 pr-3 capitalize">{t.transit_rashi}</td>
                <td className="py-1.5 pr-3">{t.house_from_natal_moon ?? "—"}</td>
                <td className="py-1.5 pr-3">{t.retrograde ? "Yes" : "No"}</td>
                <td className="py-1.5 pr-3">{t.is_sade_sati ? "Yes" : "No"}</td>
                <td className="py-1.5 pr-3">{t.has_vedha ? "Yes" : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Section>
  );
}

function DashaSection({ dasha }: { dasha: EventDashaArtifact | null }) {
  if (!dasha || dasha.chain.length === 0) return null;
  return (
    <Section title="Active Dasha">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b" style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}>
            <th className="py-2 pr-3 font-semibold">Lord</th>
            <th className="py-2 pr-3 font-semibold">Level</th>
            <th className="py-2 pr-3 font-semibold">From</th>
            <th className="py-2 pr-3 font-semibold">To</th>
            <th className="py-2 pr-3 font-semibold">Days</th>
          </tr>
        </thead>
        <tbody style={{ color: "var(--text-primary)" }}>
          {dasha.chain.map((p) => (
            <tr key={`${p.lord}-${p.level}`} className="border-b" style={{ borderColor: "var(--border-primary)" }}>
              <td className="py-1.5 pr-3 capitalize">{p.lord}</td>
              <td className="py-1.5 pr-3">{p.level}</td>
              <td className="py-1.5 pr-3">{p.start_date}</td>
              <td className="py-1.5 pr-3">{p.end_date}</td>
              <td className="py-1.5 pr-3">{p.duration_days}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Section>
  );
}

interface ScoreDimension {
  key: string;
  label: string;
  weight: number;
  points_earned: number;
  points_max: number;
  status: string;
}

function ScoreBreakdownSection({ report }: { report: EventAnalysisReport | null }) {
  const section = report?.sections.find((s) => s.content.section_type === "score_breakdown");
  const data = section?.content.data as { overall_score?: number; dimensions?: ScoreDimension[] } | undefined;
  if (!data?.dimensions || data.dimensions.length === 0) return null;

  return (
    <Section title="Score Breakdown">
      <div className="space-y-3">
        {data.dimensions.map((d) => {
          const pct = d.points_max > 0 ? (d.points_earned / d.points_max) * 100 : 0;
          const color = STATUS_COLOR[d.status] ?? "var(--obsidian-accent-tertiary)";
          return (
            <div key={d.key}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="font-medium" style={{ color: "var(--text-primary)" }}>{d.label}</span>
                <span className="flex items-center gap-2" style={{ color: "var(--text-muted)" }}>
                  {d.points_earned.toFixed(1)} / {d.points_max.toFixed(0)}
                  <StatusBadge status={d.status} />
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full" style={{ backgroundColor: "var(--bg-card)" }}>
                <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
              </div>
            </div>
          );
        })}
      </div>
    </Section>
  );
}

interface DimensionEvidence {
  status: string;
  sub_score_pct: number | null;
  weight: number;
  points_earned: number;
  points_max: number;
  evidence: string[];
}

function EvidenceSections({ report }: { report: EventAnalysisReport | null }) {
  if (!report) return null;
  const dimensionKeys: readonly string[] = DIMENSION_KEYS;
  // Older analyses (run before evidence-based sections existed) persisted
  // these same section_type keys with a different data shape (e.g. a raw
  // {chain, count} or {transits, count} dump, no `evidence` array) — only
  // render sections that actually have the new shape, so an old stored
  // report just omits this block instead of crashing on it.
  const sections = report.sections.filter(
    (s) =>
      dimensionKeys.includes(s.content.section_type) &&
      Array.isArray((s.content.data as { evidence?: unknown } | undefined)?.evidence),
  );
  if (sections.length === 0) return null;

  return (
    <>
      {sections.map((s) => {
        const data = s.content.data as unknown as DimensionEvidence;
        const title = DIMENSION_TITLES[s.content.section_type] ?? s.content.section_type;
        return (
          <Section key={s.content.section_type} title={title}>
            <div className="mb-3 flex items-center justify-between">
              <StatusBadge status={data.status} />
              {data.sub_score_pct != null && (
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {data.sub_score_pct.toFixed(0)}% · {data.points_earned.toFixed(1)}/{data.points_max.toFixed(0)} pts
                </span>
              )}
            </div>
            <ul className="space-y-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
              {data.evidence.map((line, i) => (
                <li key={i} className="flex gap-2">
                  <span style={{ color: "var(--text-muted)" }}>•</span>
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </Section>
        );
      })}
    </>
  );
}

interface ReportPlanetRow {
  name: string;
  house: number | null;
  rashi: string;
  dignity: string | null;
  retrograde: boolean;
}

function PlanetDignitySection({
  report,
}: {
  report: EventAnalysisReport | null;
}) {
  const planetsSection = report?.sections.find((s) => s.content.section_type === "planets");
  const planets = (planetsSection?.content.data as { planets?: ReportPlanetRow[] } | undefined)?.planets;
  if (!planets || planets.length === 0) return null;

  return (
    <Section title="Planetary Dignity (Event Chart)">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b" style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}>
            <th className="py-2 pr-3 font-semibold">Planet</th>
            <th className="py-2 pr-3 font-semibold">Rashi</th>
            <th className="py-2 pr-3 font-semibold">House</th>
            <th className="py-2 pr-3 font-semibold">Dignity</th>
            <th className="py-2 pr-3 font-semibold">Retro</th>
          </tr>
        </thead>
        <tbody style={{ color: "var(--text-primary)" }}>
          {planets.map((p) => (
            <tr key={p.name} className="border-b" style={{ borderColor: "var(--border-primary)" }}>
              <td className="py-1.5 pr-3 capitalize">{p.name}</td>
              <td className="py-1.5 pr-3 capitalize">{p.rashi}</td>
              <td className="py-1.5 pr-3">{p.house ?? "—"}</td>
              <td className="py-1.5 pr-3 capitalize">{p.dignity ?? "—"}</td>
              <td className="py-1.5 pr-3">{p.retrograde ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Section>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{title}</h2>
      <div
        className="rounded-lg border p-4"
        style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}
      >
        {children}
      </div>
    </div>
  );
}