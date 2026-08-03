"use client";

import { CategoryPatternsPanel } from "@/components/research/CategoryPatternsPanel";

export default function PatternsYogasPage() {
  return (
    <CategoryPatternsPanel
      tabTitle="Yogas"
      subtitle="Patterns driven by active classical yogas."
      blurb="Discovered patterns whose significant dimension is a natal yoga (Raja Yoga, Neecha Bhanga, Vimala Yoga, and others) present at birth."
      category="yoga"
      emptyMessage="No yoga-based patterns discovered yet — run Discover Patterns from Advanced Research on the Patterns tab."
    />
  );
}
