/** CompareChartsModal.tsx */
'use client';
import React, { useState, useCallback } from 'react';

type ChartOption = {
  id: string;
  name: string;
  subtitle?: string;
};

type CompareChartsModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onCompare: (selectedChartIds: string[]) => void;
  availableCharts: ChartOption[];
};

export const CompareChartsModal: React.FC<CompareChartsModalProps> = ({
  isOpen,
  onClose,
  onCompare,
  availableCharts,
}) => {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const MAX_SELECTION = 4;

  const toggleChart = useCallback((chartId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(chartId)) {
        next.delete(chartId);
      } else if (next.size < MAX_SELECTION) {
        next.add(chartId);
      }
      return next;
    });
  }, []);

  const handleCompare = useCallback(() => {
    if (selectedIds.size >= 2) {
      onCompare(Array.from(selectedIds));
    }
  }, [selectedIds, onCompare]);

  const handleCancel = useCallback(() => {
    setSelectedIds(new Set());
    onClose();
  }, [onClose]);

  if (!isOpen) return null;

  const canCompare = selectedIds.size >= 2;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={handleCancel} aria-hidden="true" />

      <div
        className="obsidian-card relative w-full max-w-md overflow-hidden"
        style={{ backgroundColor: 'var(--bg-card)' }}
      >
        <div
          className="flex items-center justify-between border-b px-6 py-4"
          style={{ borderColor: 'var(--border-primary)' }}
        >
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
            Choose Charts
          </h2>
          <button
            onClick={handleCancel}
            className="text-xl leading-none transition"
            style={{ color: 'var(--text-muted)' }}
            aria-label="Close modal"
          >
            ×
          </button>
        </div>

        <div className="max-h-80 overflow-y-auto px-6 py-4">
          {availableCharts.length === 0 ? (
            <p className="py-4 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
              No saved charts available
            </p>
          ) : (
            <ul className="space-y-2" role="group" aria-label="Select charts to compare">
              {availableCharts.map((chart) => {
                const isSelected = selectedIds.has(chart.id);
                const isDisabled = !isSelected && selectedIds.size >= MAX_SELECTION;
                return (
                  <li key={chart.id}>
                    <label
                      className="flex items-center gap-3 rounded-lg px-3 py-2 transition-colors"
                      style={{
                        cursor: isDisabled ? 'not-allowed' : 'pointer',
                        opacity: isDisabled ? 0.4 : 1,
                        backgroundColor: isSelected ? 'var(--obsidian-accent-tertiary-soft)' : 'transparent',
                        boxShadow: isSelected ? 'inset 0 0 0 1px var(--obsidian-accent-tertiary)' : undefined,
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleChart(chart.id)}
                        disabled={isDisabled}
                        className="h-4 w-4 rounded"
                        aria-label={`Select ${chart.name}`}
                      />
                      <div className="min-w-0 flex-1">
                        <span
                          className="block truncate text-sm font-medium"
                          style={{ color: 'var(--text-primary)' }}
                        >
                          {chart.name}
                        </span>
                        {chart.subtitle && (
                          <span className="block truncate text-xs" style={{ color: 'var(--text-muted)' }}>
                            {chart.subtitle}
                          </span>
                        )}
                      </div>
                      {isSelected && (
                        <span
                          className="flex-shrink-0 text-xs font-semibold"
                          style={{ color: 'var(--obsidian-accent-tertiary)' }}
                        >
                          ✓
                        </span>
                      )}
                    </label>
                  </li>
                );
              })}
            </ul>
          )}

          <div
            className="mt-4 rounded-lg px-3 py-2 text-xs"
            style={{ backgroundColor: 'var(--obsidian-surface)', color: 'var(--text-secondary)' }}
          >
            {selectedIds.size} of {MAX_SELECTION} charts selected
            {selectedIds.size < 2 && (
              <span className="ml-2" style={{ color: 'var(--obsidian-status-warning, #f59e0b)' }}>
                (minimum 2 required)
              </span>
            )}
          </div>
        </div>

        <div
          className="flex justify-end gap-3 border-t px-6 py-4"
          style={{ borderColor: 'var(--border-primary)' }}
        >
          <button type="button" onClick={handleCancel} className="obsidian-btn-secondary text-sm">
            Cancel
          </button>
          <button
            type="button"
            onClick={handleCompare}
            disabled={!canCompare}
            className="obsidian-btn-primary text-sm disabled:cursor-not-allowed disabled:opacity-40"
          >
            Compare →
          </button>
        </div>
      </div>
    </div>
  );
};
