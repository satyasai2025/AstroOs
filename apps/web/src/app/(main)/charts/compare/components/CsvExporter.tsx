/** CsvExporter.tsx — builds a CSV snapshot of a chart comparison and triggers a download. */
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

interface ComparisonCsvData {
  charts: ComparedChart[];
  planetRows: PlanetRow[];
  houseRows: HouseRow[];
  yogaNames: string[];
  dashaRows: DashaRow[];
}

function escapeCsvCell(value: string): string {
  return /[",\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

function toCsvLine(cells: string[]): string {
  return cells.map(escapeCsvCell).join(',');
}

export function buildComparisonCsv(data: ComparisonCsvData): string {
  const { charts, planetRows, houseRows, yogaNames, dashaRows } = data;
  const names = charts.map((c) => c.name);
  const lines: string[] = [];

  lines.push('=== Planet Comparison ===');
  lines.push(toCsvLine(['Planet', ...names, 'Match']));
  planetRows.forEach((row) => {
    lines.push(
      toCsvLine([
        row.planet,
        ...row.cells.map((c) => (c ? `${c.rashi} ${c.degree.toFixed(1)}°${c.retro ? ' (R)' : ''}` : '—')),
        row.highlight,
      ]),
    );
  });
  lines.push('');

  lines.push('=== House Comparison ===');
  lines.push(toCsvLine(['House', ...names, 'Match']));
  houseRows.forEach((row) => {
    lines.push(
      toCsvLine([
        String(row.house),
        ...row.cells.map((c) => `${c.rashi}${c.occupants.length ? ` (${c.occupants.map((p) => p.planet).join(', ')})` : ''}`),
        row.highlight,
      ]),
    );
  });
  lines.push('');

  lines.push('=== Dasha Comparison ===');
  lines.push(toCsvLine(['Chart', 'Current Mahadasha', 'Current Antardasha', '% Elapsed']));
  dashaRows.forEach(({ chart, current }) => {
    lines.push(
      toCsvLine([
        chart.name,
        current?.mahadasha.lord ?? '—',
        current?.antardasha?.lord ?? '—',
        current ? `${current.percentElapsed}%` : '—',
      ]),
    );
  });
  lines.push('');

  lines.push('=== Yogas ===');
  lines.push(toCsvLine(['Yoga', ...names]));
  yogaNames.forEach((name) => {
    const row = [name];
    charts.forEach((c) => {
      row.push(c.result.yogas.results.some((y) => y.name === name && y.is_present) ? 'Yes' : 'No');
    });
    lines.push(toCsvLine(row));
  });

  return lines.join('\n');
}

export function exportComparisonToCsv(data: ComparisonCsvData): void {
  const csv = buildComparisonCsv(data);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `astroos-comparison-${Date.now()}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
