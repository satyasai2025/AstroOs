import { ResearchPatternsFiltersProvider } from "@/components/research/ResearchPatternsFiltersContext";

/**
 * Wraps every /reports/* route in the shared Research Patterns filter Context.
 *
 * ResearchPatternsShell (the sidebar navigation component that contains the
 * "Reports" link) calls useResearchPatternsFilters() internally, which throws
 * if its Provider isn't in scope. The /research/patterns/* layout already
 * provides this context for those pages — but /reports/* is a separate
 * top-level route tree, so this layout mirrors that provider wrapper here.
 */
export default function ReportsLayout({ children }: { children: React.ReactNode }) {
  return (
    <ResearchPatternsFiltersProvider>{children}</ResearchPatternsFiltersProvider>
  );
}
