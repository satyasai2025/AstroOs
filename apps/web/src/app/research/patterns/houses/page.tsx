"use client";

import { CategoryPatternsPanel } from "@/components/research/CategoryPatternsPanel";

export default function PatternsHousesPage() {
  return (
    <CategoryPatternsPanel
      tabTitle="Houses"
      subtitle="Patterns driven by house-lord strength and activation."
      blurb="Discovered patterns whose significant dimension is a house lord's status (strong, activated, afflicted) at the time of the event."
      category="house"
      emptyMessage="No house-based patterns discovered yet — run Discover Patterns from Advanced Research on the Patterns tab."
    />
  );
}
