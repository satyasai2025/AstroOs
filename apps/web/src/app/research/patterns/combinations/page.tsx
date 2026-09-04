"use client";

import { CategoryPatternsPanel } from "@/components/research/CategoryPatternsPanel";

export default function PatternsCombinationsPage() {
  return (
    <CategoryPatternsPanel
      tabTitle="Combinations"
      subtitle="Multi-dimension patterns — two or more astrological factors co-occurring together."
      blurb="Patterns where at least two dimensions (e.g. a dasha AND a yoga, or a transit AND a house activation) jointly beat the independence-expected rate — stronger evidence than any single factor alone."
      minDimensions={2}
      emptyMessage="No multi-dimension patterns discovered yet — run Discover Patterns from Advanced Research on the Patterns tab."
    />
  );
}
