import { AppShell } from "@/components/layout/AppShell";
import { ResearchPatternsFiltersProvider } from "@/components/research/ResearchPatternsFiltersContext";

export default function ReportsLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell sectionColor="--section-reports">
      <ResearchPatternsFiltersProvider>{children}</ResearchPatternsFiltersProvider>
    </AppShell>
  );
}
