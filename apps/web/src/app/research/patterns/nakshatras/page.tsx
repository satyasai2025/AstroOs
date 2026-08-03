"use client";

import { CategoryPatternsPanel } from "@/components/research/CategoryPatternsPanel";

export default function PatternsNakshatrasPage() {
  return (
    <CategoryPatternsPanel
      tabTitle="Nakshatras"
      subtitle="Patterns driven by active nakshatra placements."
      blurb="Discovered patterns whose significant dimension is a natal or activated nakshatra at the time of the event."
      category="nakshatra"
      emptyMessage="No nakshatra-based patterns discovered yet — this dataset hasn't surfaced any that clear the significance floor."
    />
  );
}
