import { ResearchPatternsFiltersProvider } from "@/components/research/ResearchPatternsFiltersContext";

/**
 * Wraps every /ai/* route in the shared Research Patterns filter Context.
 *
 * ResearchPatternsShell (the sidebar navigation component that contains the
 * "AI Explain" link) calls useResearchPatternsFilters() internally, which
 * throws if its Provider isn't in scope. The /research/patterns/* layout
 * already provides this context for those pages, and /reports/* mirrors it
 * for its own route tree — this does the same for /ai/*.
 */
export default function AiLayout({ children }: { children: React.ReactNode }) {
  return (
    <ResearchPatternsFiltersProvider>{children}</ResearchPatternsFiltersProvider>
  );
}
