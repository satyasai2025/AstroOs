/** ComparisonWorkspace.tsx — side-by-side comparison of 2-4 saved charts. */
'use client';

import { useMemo, useState } from 'react';
import {
  PLANETS,
  RASHIS,
  PLANET_SYMBOLS,
  rashiIndexFromApiName,
  rashiLordFromApiName,
} from '@/lib/astro';
import {
  careerIndex,
  marriageIndex,
  wealthPotential,
  overallStrengthScore,
  healthRisk,
} from '@/lib/kpiScoring';
import type { DashaPeriodResponse, WorkflowAnalysisResponse } from '@/lib/types';
import { DifferenceHighlight } from './DifferenceHighlight';
import { exportComparisonToCsv } from './CsvExporter';
import { exportComparisonToPdf } from './PdfExporter';
import { exportComparisonToJson } from './JsonExporter';
import VennDiagram from './VennDiagram';
import EnhancedRadarChart from './EnhancedRadarChart';

const SERIES_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ec4899'];

export interface ComparedChart {
  id: string;
  name: string;
  result: WorkflowAnalysisResponse;
}

type HighlightType = 'exact' | 'similar' | 'different';
type TabId = 'planets' | 'houses' | 'dasha' | 'yogas' | 'summary';

const TABS: { id: TabId; label: string }[] = [
  { id: 'planets', label: 'Planets' },
  { id: 'houses', label: 'Houses' },
  { id: 'dasha', label: 'Dasha' },
  { id: 'yogas', label: 'Yogas' },
  { id: 'summary', label: 'Summary' },
];

/** The mahadasha (and its active antardasha, if any) whose window contains `at`. */
function findCurrentDasha(mahadashas: DashaPeriodResponse[], at: Date) {
  const t = at.getTime();
  const md = mahadashas.find(
    (m) => t >= new Date(m.start_date).getTime() && t <= new Date(m.end_date).getTime(),
  );
  if (!md) return null;
  const ad = md.sub_periods?.find(
    (p) => t >= new Date(p.start_date).getTime() && t <= new Date(p.end_date).getTime(),
  );
  const totalMs = new Date(md.end_date).getTime() - new Date(md.start_date).getTime();
  const elapsedMs = t - new Date(md.start_date).getTime();
  const percentElapsed = totalMs > 0 ? Math.round((elapsedMs / totalMs) * 100) : 0;
  return { mahadasha: md, antardasha: ad ?? null, percentElapsed };
}

function highlightFor(rashis: (string | null)[]): HighlightType {
  const present = rashis.filter((r): r is string => !!r);
  if (present.length < 2) return 'different';
  const allSame = present.every((r) => r.toLowerCase() === present[0].toLowerCase());
  if (allSame) return 'exact';
  const lords = present.map((r) => rashiLordFromApiName(r));
  const allSameLord = lords.every((l) => l && l === lords[0]);
  return allSameLord ? 'similar' : 'different';
}

interface Props {
  charts: ComparedChart[];
  onClose: () => void;
  onSave: (name: string) => void;
}

export function ComparisonWorkspace({ charts, onClose, onSave }: Props) {
  const [activeTab, setActiveTab] = useState<TabId>('planets');
  const [saveName, setSaveName] = useState('');

  const now = useMemo(() => new Date(), []);

  const planetRows = useMemo(
    () =>
      PLANETS.map((planet) => {
        const cells = charts.map((c) => {
          const p = c.result.chart.planets.find(
            (pl) => pl.planet.toLowerCase() === planet.toLowerCase(),
          );
          return p
            ? { rashi: p.rashi, house: p.rashi_house_number, degree: p.rashi_degree, retro: p.is_retrograde }
            : null;
        });
        const highlight = highlightFor(cells.map((c) => c?.rashi ?? null));
        return { planet, cells, highlight };
      }),
    [charts],
  );

  const houseRows = useMemo(
    () =>
      Array.from({ length: 12 }, (_, i) => i + 1).map((house) => {
        const cells = charts.map((c) => {
          const ascIdx = rashiIndexFromApiName(c.result.chart.ascendant.rashi);
          const rashi = RASHIS[(ascIdx + house - 1) % 12];
          const occupants = c.result.chart.planets.filter((p) => p.rashi_house_number === house);
          return { rashi, occupants };
        });
        const highlight = highlightFor(cells.map((c) => c.rashi));
        return { house, cells, highlight };
      }),
    [charts],
  );

  const dashaRows = useMemo(
    () => charts.map((c) => ({ chart: c, current: findCurrentDasha(c.result.dasha.mahadashas, now) })),
    [charts, now],
  );

  const yogaNames = useMemo(() => {
    const names = new Set<string>();
    charts.forEach((c) => c.result.yogas.results.forEach((y) => y.is_present && names.add(y.name)));
    return Array.from(names).sort();
  }, [charts]);

  const sameSignCount = planetRows.filter((r) => r.highlight === 'exact').length;
  const sameSignPercent = Math.round((sameSignCount / planetRows.length) * 100);
  const differingPlanets = planetRows.filter((r) => r.highlight !== 'exact').map((r) => r.planet);

  // Real, chart-grounded heuristic scores (documented default weights over
  // real house-lord/karaka/yoga data — see lib/kpiScoring.ts) — the same
  // scoring already used on the dashboard's Prediction Chains, applied per
  // compared chart here instead of invented narrative text.
  const lifeDomainScores = useMemo(
    () =>
      charts.map((c) => ({
        chartId: c.id,
        chartName: c.name,
        career: careerIndex(c.result),
        relationship: marriageIndex(c.result),
        wealth: wealthPotential(c.result),
        overallStrength: overallStrengthScore(c.result),
        healthRisk: healthRisk(c.result),
      })),
    [charts],
  );

  const radarSeries = lifeDomainScores.map((s, i) => ({
    name: s.chartName,
    color: SERIES_COLORS[i % SERIES_COLORS.length],
    values: [s.relationship, s.career, s.wealth, s.overallStrength],
  }));

  const [shareCopied, setShareCopied] = useState(false);
  const handleShare = async () => {
    const url = `${window.location.origin}/charts/compare?ids=${charts.map((c) => c.id).join(',')}`;
    try {
      await navigator.clipboard.writeText(url);
      setShareCopied(true);
      setTimeout(() => setShareCopied(false), 2000);
    } catch {
      window.prompt('Copy this link:', url);
    }
  };

  const handleExportCsv = () => exportComparisonToCsv({ charts, planetRows, houseRows, yogaNames, dashaRows });
  const handleExportPdf = () => exportComparisonToPdf({ charts, planetRows, sameSignPercent, differingPlanets });
  const handleExportJson = () =>
    exportComparisonToJson({ charts, planetRows, houseRows, yogaNames, dashaRows, lifeDomainScores });

  return (
    <div className="obsidian-card flex flex-col overflow-hidden">
      {/* Header */}
      <div
        className="flex flex-wrap items-center justify-between gap-3 border-b p-4"
        style={{ borderColor: 'var(--border-primary)' }}
      >
        <div>
          <h1 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
            Comparing {charts.length} Charts
          </h1>
          <p className="mt-0.5 text-xs" style={{ color: 'var(--text-secondary)' }}>
            {charts.map((c) => c.name).join(' · ')}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="text"
            value={saveName}
            onChange={(e) => setSaveName(e.target.value)}
            placeholder="Name this comparison"
            className="obsidian-input w-44 text-xs"
          />
          <button
            type="button"
            onClick={() => saveName.trim() && onSave(saveName.trim())}
            disabled={!saveName.trim()}
            className="obsidian-btn-secondary text-xs disabled:cursor-not-allowed disabled:opacity-40"
          >
            Save
          </button>
          <button type="button" onClick={handleShare} className="obsidian-btn-secondary text-xs">
            {shareCopied ? '✓ Link Copied' : '🔗 Share'}
          </button>
          <button type="button" onClick={handleExportJson} className="obsidian-btn-secondary text-xs">
            🗂️ Export JSON
          </button>
          <button type="button" onClick={handleExportCsv} className="obsidian-btn-secondary text-xs">
            📊 Export CSV
          </button>
          <button type="button" onClick={handleExportPdf} className="obsidian-btn-primary text-xs">
            📄 Export PDF
          </button>
          <button type="button" onClick={onClose} className="obsidian-btn-secondary text-xs">
            ← Back
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div
        className="flex gap-1 border-b px-4 pt-3"
        style={{ borderColor: 'var(--border-primary)' }}
        role="tablist"
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
            className="rounded-t-md px-3 py-2 text-sm font-medium transition-colors"
            style={{
              color: activeTab === tab.id ? 'var(--obsidian-accent-tertiary)' : 'var(--text-secondary)',
              borderBottom: activeTab === tab.id ? '2px solid var(--obsidian-accent-tertiary)' : '2px solid transparent',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="p-5">
        {activeTab === 'planets' && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-xs uppercase" style={{ borderColor: 'var(--border-primary)', color: 'var(--text-muted)' }}>
                  <th className="py-2 pr-3">Planet</th>
                  {charts.map((c) => (
                    <th key={c.id} className="py-2 pr-3">{c.name}</th>
                  ))}
                  <th className="py-2 pr-3">Match</th>
                </tr>
              </thead>
              <tbody>
                {planetRows.map((row) => (
                  <tr key={row.planet} className="border-b" style={{ borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }}>
                    <td className="py-2 pr-3 font-medium">
                      {PLANET_SYMBOLS[row.planet] ?? ''} {row.planet}
                    </td>
                    {row.cells.map((cell, i) => (
                      <td key={charts[i].id} className="py-2 pr-3 capitalize">
                        {cell ? `${cell.rashi} ${cell.degree.toFixed(1)}°${cell.retro ? ' (R)' : ''}` : '—'}
                      </td>
                    ))}
                    <td className="py-2 pr-3">
                      <DifferenceHighlight label={row.planet} highlightType={row.highlight} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'houses' && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-xs uppercase" style={{ borderColor: 'var(--border-primary)', color: 'var(--text-muted)' }}>
                  <th className="py-2 pr-3">House</th>
                  {charts.map((c) => (
                    <th key={c.id} className="py-2 pr-3">{c.name}</th>
                  ))}
                  <th className="py-2 pr-3">Match</th>
                </tr>
              </thead>
              <tbody>
                {houseRows.map((row) => (
                  <tr key={row.house} className="border-b" style={{ borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }}>
                    <td className="py-2 pr-3 font-medium">{row.house}</td>
                    {row.cells.map((cell, i) => (
                      <td key={charts[i].id} className="py-2 pr-3 capitalize">
                        {cell.rashi}
                        {cell.occupants.length > 0 && (
                          <span className="ml-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                            ({cell.occupants.map((p) => PLANET_SYMBOLS[p.planet] ?? p.planet.slice(0, 2)).join(' ')})
                          </span>
                        )}
                      </td>
                    ))}
                    <td className="py-2 pr-3">
                      <DifferenceHighlight label={`House ${row.house}`} highlightType={row.highlight} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'dasha' && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {dashaRows.map(({ chart, current }) => (
              <div key={chart.id} className="rounded-lg border p-3" style={{ borderColor: 'var(--border-primary)' }}>
                <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>
                  {chart.name}
                </p>
                {current ? (
                  <>
                    <p className="mt-1 text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
                      {current.mahadasha.lord}
                      {current.antardasha ? ` / ${current.antardasha.lord}` : ''}
                    </p>
                    <p className="mt-0.5 text-xs" style={{ color: 'var(--text-secondary)' }}>
                      {current.percentElapsed}% elapsed of {current.mahadasha.lord} MD
                    </p>
                  </>
                ) : (
                  <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>No active dasha found</p>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'yogas' && (
          <div className="overflow-x-auto">
            {yogaNames.length === 0 ? (
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                No yogas detected in any of the compared charts.
              </p>
            ) : (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-xs uppercase" style={{ borderColor: 'var(--border-primary)', color: 'var(--text-muted)' }}>
                    <th className="py-2 pr-3">Yoga</th>
                    {charts.map((c) => (
                      <th key={c.id} className="py-2 pr-3">{c.name}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {yogaNames.map((name) => (
                    <tr key={name} className="border-b" style={{ borderColor: 'var(--border-primary)', color: 'var(--text-primary)' }}>
                      <td className="py-2 pr-3 font-medium">{name}</td>
                      {charts.map((c) => {
                        const present = c.result.yogas.results.some((y) => y.name === name && y.is_present);
                        return (
                          <td key={c.id} className="py-2 pr-3">
                            {present ? (
                              <span style={{ color: '#4ade80' }}>✓</span>
                            ) : (
                              <span style={{ color: 'var(--text-muted)' }}>—</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {activeTab === 'summary' && (
          <div className="space-y-4">
            <div className="rounded-lg border p-4" style={{ borderColor: 'var(--border-primary)' }}>
              <p className="text-sm" style={{ color: 'var(--text-primary)' }}>
                <span className="text-xl font-bold" style={{ color: 'var(--obsidian-accent-tertiary)' }}>
                  {sameSignPercent}%
                </span>{' '}
                of planets share the same rashi across all {charts.length} charts ({sameSignCount} of {planetRows.length}).
              </p>

              {/* Life Domain Scores — real chart-grounded heuristic scoring
                  (lib/kpiScoring.ts: 10th/7th/2nd/11th/6th house-lord
                  strength + karaka planets + career yogas), the same scoring
                  already used in Prediction Chains. Documented default
                  weights, not a claim of classical formula authority — see
                  kpiScoring.ts's own doc comments for exactly which fields
                  feed each score. */}
              <div className="mt-4 rounded-lg border p-4" style={{ borderColor: 'var(--border-primary)' }}>
                <h4 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                  Life Domain Scores
                </h4>
                <p className="mt-0.5 text-[11px]" style={{ color: 'var(--text-muted)' }}>
                  Heuristic scores from house-lord strength, karaka planets, and yogas — not a classical formula, see kpiScoring.ts.
                </p>
                <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {lifeDomainScores.map((s) => (
                    <div key={s.chartId} className="rounded-lg border p-3" style={{ borderColor: 'var(--border-primary)' }}>
                      <p className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>{s.chartName}</p>
                      <dl className="mt-2 space-y-1 text-xs">
                        <div className="flex justify-between"><dt style={{ color: 'var(--text-muted)' }}>Career</dt><dd style={{ color: 'var(--text-secondary)' }}>{s.career}%</dd></div>
                        <div className="flex justify-between"><dt style={{ color: 'var(--text-muted)' }}>Relationship</dt><dd style={{ color: 'var(--text-secondary)' }}>{s.relationship}%</dd></div>
                        <div className="flex justify-between"><dt style={{ color: 'var(--text-muted)' }}>Wealth</dt><dd style={{ color: 'var(--text-secondary)' }}>{s.wealth}%</dd></div>
                        <div className="flex justify-between"><dt style={{ color: 'var(--text-muted)' }}>Overall Strength</dt><dd style={{ color: 'var(--text-secondary)' }}>{s.overallStrength}%</dd></div>
                        <div className="flex justify-between"><dt style={{ color: 'var(--text-muted)' }}>Health Risk</dt><dd style={{ color: 'var(--text-secondary)' }}>{s.healthRisk}</dd></div>
                      </dl>
                    </div>
                  ))}
                </div>
              </div>

              {/* Venn Diagram */}
              <div className="mt-4 rounded-lg border p-4" style={{ borderColor: 'var(--border-primary)' }}>
                <h4 className="text-sm font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
                  Planetary Overlap Visualization
                </h4>
                {charts.length > 2 && (
                  <p className="mb-2 text-[11px]" style={{ color: 'var(--text-muted)' }}>
                    Showing overlap between {charts[0]?.name} and {charts[charts.length - 1]?.name} only — a Venn diagram compares two sets at a time.
                  </p>
                )}
                <VennDiagram
                  leftSet={{
                    label: charts[0]?.name ?? 'Chart A',
                    set: planetRows.filter(r => r.cells[0]?.rashi).map(r => r.cells[0]?.rashi!),
                    color: '#3b82f6',
                  }}
                  rightSet={{
                    label: charts[charts.length - 1]?.name ?? 'Chart B',
                    set: planetRows.filter(r => r.cells[charts.length - 1]?.rashi).map(r => r.cells[charts.length - 1]?.rashi!),
                    color: '#10b981',
                  }}
                  overlap={{
                    label: 'Shared',
                    overlappingPercentage: sameSignPercent,
                    overlappingPlanets: planetRows.filter(r => r.highlight === 'exact').map(r => r.planet),
                  }}
                />
              </div>
            </div>

            {/* Radar chart across all compared charts, real per-chart scores */}
            <div className="rounded-lg border p-4" style={{ borderColor: 'var(--border-primary)' }}>
              <h4 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                Multi-Dimensional Comparison
              </h4>
              <EnhancedRadarChart
                axes={['Relationship', 'Career', 'Wealth', 'Overall Strength']}
                series={radarSeries}
              />
            </div>

            {differingPlanets.length > 0 && (
              <div className="rounded-lg border p-4" style={{ borderColor: 'var(--border-primary)' }}>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>
                  Differing Placements
                </p>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  {differingPlanets.join(', ')}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ComparisonWorkspace;
