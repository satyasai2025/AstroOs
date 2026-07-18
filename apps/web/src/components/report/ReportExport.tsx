// Report Export Component (Phase F - Frontend)

import { useState } from 'react';

interface ReportExportProps {
  chartId: string;
  birthData: {
    birth_datetime_utc: string;
    latitude: number;
    longitude: number;
  };
}

export function ReportExport({ chartId, birthData }: ReportExportProps) {
  const [loading, setLoading] = useState<'pdf' | 'csv' | null>(null);

  const handleExport = async (format: 'pdf' | 'csv') => {
    setLoading(format);
    try {
      const response = await fetch(`/api/v1/report/chart/${format}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(birthData),
      });

      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chart-report.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="flex gap-2" data-chart-id={chartId}>
      <button
        type="button"
        onClick={() => handleExport('pdf')}
        disabled={loading !== null}
        className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:bg-white/10 disabled:opacity-40"
      >
        {loading === 'pdf' ? 'Exporting...' : 'PDF'}
      </button>
      <button
        type="button"
        onClick={() => handleExport('csv')}
        disabled={loading !== null}
        className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:bg-white/10 disabled:opacity-40"
      >
        {loading === 'csv' ? 'Exporting...' : 'CSV'}
      </button>
    </div>
  );
}
