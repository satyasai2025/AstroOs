import { ResearchPatternsFiltersProvider } from "@/components/research/ResearchPatternsFiltersContext";

export default function ResearchPatternsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ResearchPatternsFiltersProvider>
      {children}
    </ResearchPatternsFiltersProvider>
  );
}
