import React from 'react';
import { MeenaNumerologyDashboard } from '@/components/numerology/MeenaNumerologyDashboard';

export const metadata = {
  title: "Meena Numerology | AstroOS",
  description: "Personal life story, 4 life chapters, and actionable timing guide based on Meena's Numerology Method."
};

export default function NumerologyPage() {
  return (
    <main className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
      <MeenaNumerologyDashboard />
    </main>
  );
}
