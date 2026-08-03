"use client";

import { CategoryPatternsPanel } from "@/components/research/CategoryPatternsPanel";

export default function PatternsDashasPage() {
  return (
    <CategoryPatternsPanel
      tabTitle="Dashas"
      subtitle="Patterns driven by the active dasha period at the time of the event."
      blurb="Discovered patterns whose significant dimension is the mahadasha, antardasha, or pratyantardasha lord active when the event occurred."
      category="dasha"
      emptyMessage="No dasha-based patterns discovered yet — run Discover Patterns from Advanced Research on the Patterns tab."
    />
  );
}
