/** DifferenceHighlight.tsx */
import React from 'react';

type DifferenceHighlightProps = {
  label: string;
  highlightType: 'exact' | 'similar' | 'different';
};

const STYLES: Record<DifferenceHighlightProps['highlightType'], { bg: string; fg: string }> = {
  exact: { bg: 'rgba(34, 197, 94, 0.15)', fg: '#4ade80' },
  similar: { bg: 'rgba(234, 179, 8, 0.15)', fg: '#facc15' },
  different: { bg: 'rgba(239, 68, 68, 0.15)', fg: '#f87171' },
};

const LABELS: Record<DifferenceHighlightProps['highlightType'], string> = {
  exact: '✓ Same',
  similar: '≈ Similar',
  different: '✗ Different',
};

export const DifferenceHighlight: React.FC<DifferenceHighlightProps> = ({ label, highlightType }) => {
  const style = STYLES[highlightType];
  return (
    <span
      title={label}
      className="inline-block whitespace-nowrap rounded px-2 py-1 text-xs font-medium"
      style={{ backgroundColor: style.bg, color: style.fg }}
    >
      {LABELS[highlightType]}
    </span>
  );
};
