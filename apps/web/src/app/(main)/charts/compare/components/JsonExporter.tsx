/** JsonExporter.tsx — snapshots a chart comparison as a downloadable JSON file. */
import type { ComparedChart } from './ComparisonWorkspace';

interface PlanetRow {
  planet: string;
  cells: ({ rashi: string; house: number; degree: number; retro: boolean } | null)[];
  highlight: string;
}

interface HouseRow {
  house: number;
  cells: { rashi: string; occupants: { planet: string }[] }[];
  highlight: string;
}

interface DashaRow {
  chart: ComparedChart;
  current: { mahadasha: { lord: string }; antardasha: { lord: string } | null; percentElapsed: number } | null;
}

interface LifeDomainScore {
  chartId: string;
  chartName: string;
  career: number;
  relationship: number;
  wealth: number;
  overallStrength: number;
  healthRisk: string;
}

interface ComparisonJsonData {
  charts: ComparedChart[];
  planetRows: PlanetRow[];
  houseRows: HouseRow[];
  yogaNames: string[];
  dashaRows: DashaRow[];
  lifeDomainScores: LifeDomainScore[];
}

export function buildComparisonJson(data: ComparisonJsonData): string {
  const { charts, planetRows, houseRows, yogaNames, dashaRows, lifeDomainScores } = data;

  const payload = {
    generated_at: charts.length > 0 ? new Date().toISOString() : null,
    charts: charts.map((c) => ({ id: c.id, name: c.name })),
    planets: planetRows.map((row) => ({
      planet: row.planet,
      match: row.highlight,
      by_chart: row.cells.map((cell, i) => ({
        chart_id: charts[i].id,
        rashi: cell?.rashi ?? null,
        degree: cell?.degree ?? null,
        retrograde: cell?.retro ?? null,
      })),
    })),
    houses: houseRows.map((row) => ({
      house: row.house,
      match: row.highlight,
      by_chart: row.cells.map((cell, i) => ({
        chart_id: charts[i].id,
        rashi: cell.rashi,
        occupants: cell.occupants.map((p) => p.planet),
      })),
    })),
    dasha: dashaRows.map(({ chart, current }) => ({
      chart_id: chart.id,
      current_mahadasha: current?.mahadasha.lord ?? null,
      current_antardasha: current?.antardasha?.lord ?? null,
      percent_elapsed: current?.percentElapsed ?? null,
    })),
    yogas: yogaNames.map((name) => ({
      name,
      by_chart: charts.map((c) => ({
        chart_id: c.id,
        present: c.result.yogas.results.some((y) => y.name === name && y.is_present),
      })),
    })),
    life_domain_scores: lifeDomainScores,
  };

  return JSON.stringify(payload, null, 2);
}

export function exportComparisonToJson(data: ComparisonJsonData): void {
  const json = buildComparisonJson(data);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `astroos-comparison-${Date.now()}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
