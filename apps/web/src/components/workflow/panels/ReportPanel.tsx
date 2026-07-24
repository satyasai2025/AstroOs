import type { ReactNode } from "react";
import type { BenchmarkResponse, ChartReportResponse, ReportSectionResponse } from "@/lib/types";

// ── Small display primitives ──────────────────────────────────────────────────

function StatGrid({ items }: { items: { label: string; value: ReactNode }[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {items.map((item) => (
        <div key={item.label}>
          <p className="text-xs uppercase tracking-wide text-slate-500">{item.label}</p>
          <p className="text-sm text-slate-200">{item.value ?? "—"}</p>
        </div>
      ))}
    </div>
  );
}

function CountBreakdown({ counts }: { counts: Record<string, number> }) {
  const entries = Object.entries(counts);
  if (entries.length === 0) return <p className="text-xs text-slate-500">No data.</p>;
  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([label, count]) => (
        <span
          key={label}
          className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-300"
        >
          <span className="capitalize">{label.replace(/_/g, " ")}</span>{" "}
          <span className="text-slate-500">×{count}</span>
        </span>
      ))}
    </div>
  );
}

// ── Per-section renderers ─────────────────────────────────────────────────────
// Each mirrors the exact shape apps/api/services/report_engine.py builds for
// that section_type. Unknown/future section types fall back to raw JSON below
// rather than crashing.

function ChartSummarySection({ data }: { data: Record<string, unknown> }) {
  return (
    <StatGrid
      items={[
        { label: "Ayanamsa", value: String(data.ayanamsa ?? "—") },
        { label: "House System", value: String(data.house_system ?? "—") },
        {
          label: "Lagna",
          value:
            data.lagna_rashi != null
              ? `${String(data.lagna_rashi)} ${
                  typeof data.lagna_degree === "number" ? data.lagna_degree.toFixed(2) + "°" : ""
                }`
              : "—",
        },
        { label: "Moon Nakshatra", value: String(data.moon_nakshatra ?? "—") },
      ]}
    />
  );
}

interface PlanetRow {
  name: string;
  rashi: string;
  house: number;
  dignity: string | null;
  retrograde: boolean;
}

function PlanetsSection({ data }: { data: Record<string, unknown> }) {
  const planets = (data.planets as PlanetRow[] | undefined) ?? [];
  if (planets.length === 0) return <p className="text-xs text-slate-500">No planetary data.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-slate-500">
            <th className="py-1 pr-3 text-left">Planet</th>
            <th className="px-2 text-left">Rashi</th>
            <th className="px-2 text-right">House</th>
            <th className="px-2 text-left">Dignity</th>
            <th className="pl-2 text-right">Retro</th>
          </tr>
        </thead>
        <tbody>
          {planets.map((p) => (
            <tr key={p.name} className="border-t border-white/5">
              <td className="py-1 pr-3 capitalize text-slate-200">{p.name}</td>
              <td className="px-2 capitalize text-slate-400">{p.rashi}</td>
              <td className="px-2 text-right text-slate-400">{p.house}</td>
              <td className="px-2 capitalize text-slate-400">{p.dignity ?? "—"}</td>
              <td className="pl-2 text-right text-slate-400">{p.retrograde ? "℞" : ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TimelineSummarySection({ data }: { data: Record<string, unknown> }) {
  const dateRange = (data.date_range as [string, string] | undefined) ?? undefined;
  const perCategory = (data.events_per_category as Record<string, number> | undefined) ?? {};
  return (
    <div className="space-y-3">
      <StatGrid
        items={[
          { label: "Total Events", value: String(data.total_events ?? 0) },
          {
            label: "Date Range",
            value: dateRange ? `${dateRange[0]} → ${dateRange[1]}` : "—",
          },
        ]}
      />
      <CountBreakdown counts={perCategory} />
    </div>
  );
}

function VerificationSummarySection({ data }: { data: Record<string, unknown> }) {
  const strengths = (data.strengths as Record<string, number> | undefined) ?? {};
  return (
    <div className="space-y-3">
      <StatGrid
        items={[
          { label: "Verification Pairs", value: String(data.total_pairs ?? 0) },
          { label: "Rules Evaluated", value: String(data.total_rules ?? 0) },
        ]}
      />
      <CountBreakdown counts={strengths} />
    </div>
  );
}

interface CitationRow {
  entity_type: string;
  entity_id: string;
  title: string;
  snippet: string;
  book_title: string;
  tradition: string;
}

function KnowledgeCitationsSection({ data }: { data: Record<string, unknown> }) {
  const citations = (data.citations as CitationRow[] | undefined) ?? [];
  if (citations.length === 0) return <p className="text-xs text-slate-500">No citations.</p>;
  return (
    <div className="space-y-2">
      {citations.map((c, i) => (
        <div key={`${c.entity_id}-${i}`} className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
          <p className="text-sm font-medium text-slate-200">{c.title}</p>
          <p className="mt-1 text-xs text-slate-400">{c.snippet}</p>
          <p className="mt-1 text-xs text-slate-500">
            {c.book_title} · <span className="capitalize">{c.tradition}</span>
          </p>
        </div>
      ))}
    </div>
  );
}

interface DistributionRow {
  label: string;
  variable: string;
  total: number;
}

function StatisticsSummarySection({ data }: { data: Record<string, unknown> }) {
  const distributions = (data.distributions as DistributionRow[] | undefined) ?? [];
  return (
    <div className="space-y-3">
      <StatGrid items={[{ label: "Sample Size", value: String(data.sample_size ?? 0) }]} />
      {distributions.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-slate-500">
                <th className="py-1 pr-3 text-left">Label</th>
                <th className="px-2 text-left">Variable</th>
                <th className="pl-2 text-right">Total</th>
              </tr>
            </thead>
            <tbody>
              {distributions.map((d, i) => (
                <tr key={`${d.variable}-${i}`} className="border-t border-white/5">
                  <td className="py-1 pr-3 text-slate-200">{d.label}</td>
                  <td className="px-2 text-slate-400">{d.variable}</td>
                  <td className="pl-2 text-right text-slate-400">{d.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SnapshotOverviewSection({ data }: { data: Record<string, unknown> }) {
  const labels = (data.labels as string[] | undefined) ?? [];
  return (
    <div className="space-y-3">
      <StatGrid items={[{ label: "Snapshots", value: String(data.snapshot_count ?? 0) }]} />
      {labels.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {labels.map((label, i) => (
            <span
              key={`${label}-${i}`}
              className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-300"
            >
              {label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

interface PlanetComparisonRow {
  chart_index: number;
  chart_label: string;
  planet: string;
  rashi: string;
  house: number;
  dignity: string | null;
}

function PlanetComparisonSection({ data }: { data: Record<string, unknown> }) {
  const planets = (data.planets as PlanetComparisonRow[] | undefined) ?? [];
  if (planets.length === 0) return <p className="text-xs text-slate-500">No comparison data.</p>;
  const byChart = new Map<string, PlanetComparisonRow[]>();
  for (const p of planets) {
    const key = p.chart_label;
    if (!byChart.has(key)) byChart.set(key, []);
    byChart.get(key)!.push(p);
  }
  return (
    <div className="space-y-4">
      {[...byChart.entries()].map(([label, rows]) => (
        <div key={label}>
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <tbody>
                {rows.map((p) => (
                  <tr key={p.planet} className="border-t border-white/5">
                    <td className="py-1 pr-3 capitalize text-slate-200">{p.planet}</td>
                    <td className="px-2 capitalize text-slate-400">{p.rashi}</td>
                    <td className="px-2 text-right text-slate-400">House {p.house}</td>
                    <td className="pl-2 capitalize text-slate-400">{p.dignity ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}

function RawFallbackSection({ data }: { data: Record<string, unknown> }) {
  return (
    <pre className="overflow-x-auto whitespace-pre-wrap break-words text-xs text-slate-400">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

const SECTION_RENDERERS: Record<string, (props: { data: Record<string, unknown> }) => ReactNode> = {
  chart_summary: ChartSummarySection,
  planets: PlanetsSection,
  timeline_summary: TimelineSummarySection,
  verification_summary: VerificationSummarySection,
  knowledge_citations: KnowledgeCitationsSection,
  statistics_summary: StatisticsSummarySection,
  snapshot_overview: SnapshotOverviewSection,
  planet_comparison: PlanetComparisonSection,
};

function ReportSection({ section }: { section: ReportSectionResponse }) {
  const Renderer = SECTION_RENDERERS[section.section_type] ?? RawFallbackSection;
  return <Renderer data={section.data} />;
}

// ── Main panel ─────────────────────────────────────────────────────────────────

export function ReportPanel({
  report,
  benchmark,
}: {
  report: ChartReportResponse;
  benchmark: BenchmarkResponse;
}) {
  return (
    <div className="space-y-6">
      <div className="glass-card p-5">
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-amber-300/80">
          {report.title}
        </h3>
        <p className="mb-4 text-xs text-slate-500">
          Subject: {report.subject_name} · Generated{" "}
          {new Date(report.metadata.generated_at).toUTCString()}
        </p>

        <div className="space-y-4">
          {[...report.sections]
            .sort((a, b) => a.order - b.order)
            .map((section) => (
              <div key={section.section_type} className="border-t border-white/5 pt-4 first:border-none first:pt-0">
                <h4 className="mb-2 text-sm font-medium text-slate-100">{section.title}</h4>
                <ReportSection section={section} />
              </div>
            ))}
        </div>
      </div>

      <div className={`glass-card p-5 ${
        benchmark.status === "passed" ? "border-emerald-500/30" :
        benchmark.status === "failed" ? "border-red-500/30" :
        "border-dashed"
      }`}>
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Benchmark Validation
        </h3>

        {benchmark.status === "not_applicable" ? (
          <div className="flex items-start gap-2">
            <span
              className="mt-0.5 inline-block h-2 w-2 flex-shrink-0 rounded-full bg-slate-500"
              aria-hidden="true"
            />
            <p className="text-sm text-slate-400">{benchmark.detail}</p>
          </div>
        ) : (
          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-2">
              <span className={`inline-block h-2 w-2 rounded-full ${
                benchmark.status === "passed" ? "bg-emerald-400" : "bg-red-400"
              }`} />
              <span className={benchmark.status === "passed" ? "text-emerald-300" : "text-red-300"}>
                {benchmark.status.toUpperCase()}
              </span>
              <span className="text-xs text-slate-500">
                vs {benchmark.reference_name} ({benchmark.reference_id})
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-slate-500">Mean Error</span>
                <p className="text-slate-200">{benchmark.mean_error}°</p>
              </div>
              <div>
                <span className="text-slate-500">Max Error</span>
                <p className="text-slate-200">{benchmark.max_error}°</p>
              </div>
              <div>
                <span className="text-slate-500">Tolerance</span>
                <p className="text-slate-200">±{benchmark.tolerance}°</p>
              </div>
            </div>
            {benchmark.planets.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-slate-500">
                      <th className="text-left py-1 pr-2">Planet</th>
                      <th className="text-right px-2">Computed</th>
                      <th className="text-right px-2">Expected</th>
                      <th className="text-right px-2">Error</th>
                      <th className="text-right pl-2">OK</th>
                    </tr>
                  </thead>
                  <tbody>
                    {benchmark.planets.map((p) => (
                      <tr key={p.planet} className="border-t border-white/5">
                        <td className="py-1 pr-2 text-slate-300">{p.planet}</td>
                        <td className="text-right px-2 text-slate-400">{p.computed_longitude.toFixed(2)}°</td>
                        <td className="text-right px-2 text-slate-400">{p.expected_longitude.toFixed(2)}°</td>
                        <td className={`text-right px-2 ${p.within_tolerance ? "text-emerald-400" : "text-red-400"}`}>
                          {p.error_degrees.toFixed(4)}°
                        </td>
                        <td className="text-right pl-2">{p.within_tolerance ? "✓" : "✗"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
