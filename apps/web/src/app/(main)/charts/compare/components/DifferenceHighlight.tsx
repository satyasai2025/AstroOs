/** DifferenceHighlight.tsx */
import React from 'react';

type DifferenceHighlightProps = {
  label: string;
  highlightType: 'exact' | 'similar' | 'different';
};

const LABELS: Record<DifferenceHighlightProps['highlightType'], string> = {
  exact: '✓ Same',
  similar: '≈ Similar',
  different: '✗ Different',
};

export const DifferenceHighlight: React.FC<DifferenceHighlightProps> = ({ label, highlightType }) => {
  const badgeClasses = {
    exact: "bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800",
    similar: "bg-amber-100 text-amber-900 border border-amber-300 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800",
    different: "bg-rose-100 text-rose-900 border border-rose-300 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800",
  }[highlightType];

  return (
    <span
      title={label}
      className={`inline-block whitespace-nowrap rounded px-2 py-0.5 text-xs font-semibold ${badgeClasses}`}
    >
      {LABELS[highlightType]}
    </span>
  );
};
