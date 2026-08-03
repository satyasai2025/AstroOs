import { ResearchPatternsFiltersProvider } from "@/components/research/ResearchPatternsFiltersContext";

/**
 * Wraps every /research/patterns/* route (Overview, Patterns, Combinations,
 * Yogas, Dashas, Transits, Houses, Nakshatras, Compare) in the shared
 * cross-tab filter Context. Next.js keeps this layout mounted across
 * client-side navigation between those sibling routes, so the Provider's
 * state persists as the user switches tabs.
 */
export default function ResearchPatternsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ResearchPatternsFiltersProvider>{children}</ResearchPatternsFiltersProvider>;
}
