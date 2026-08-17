import { AppShell } from "@/components/layout/AppShell";
import { ResearchPatternsFiltersProvider } from "@/components/research/ResearchPatternsFiltersContext";

export default function AiLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell sectionColor="--section-ai">
      <ResearchPatternsFiltersProvider>{children}</ResearchPatternsFiltersProvider>
    </AppShell>
  );
}
