"use client";

import { CategoryPatternsPanel } from "@/components/research/CategoryPatternsPanel";

export default function PatternsTransitsPage() {
  return (
    <CategoryPatternsPanel
      tabTitle="Transits"
      subtitle="Patterns driven by planetary transits at the time of the event."
      blurb="Discovered patterns whose significant dimension is a transiting planet's rashi position (gochara) at the time of the event."
      category="transit"
      emptyMessage="No transit-based patterns discovered yet — run Discover Patterns from Advanced Research on the Patterns tab."
    />
  );
}
