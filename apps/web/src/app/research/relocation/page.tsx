"use client";

import { AppShell } from "@/components/layout/AppShell";
import { RelocationStudio } from "@/components/research/RelocationStudio";

export default function RelocationPage() {
  return (
    <AppShell sectionColor="--section-research">
      <div className="max-w-7xl mx-auto space-y-6 pb-12">
        <RelocationStudio />
      </div>
    </AppShell>
  );
}
