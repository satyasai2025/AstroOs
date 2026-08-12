"use client";

import { getVargaGuide } from "@/lib/vargaGuides";
import { VARGA_DIVISORS } from "@/lib/astro";

interface VargaGuideCardProps {
  /** Varga code to describe, e.g. "D9". Renders nothing if unknown. */
  code: string;
  /** Visual tone. Defaults to "card" (filled panel). */
  variant?: "card" | "inline";
}

/**
 * Detailed per-varga explanation card shown on the Charts page.
 *
 * Purely presentational: pulls knowledge content from `lib/vargaGuides.ts`
 * and the short label/divisor from `VARGA_DIVISORS` (so the header can never
 * drift from the selector). Reused across the dedicated Divisional panel and
 * the main Chart view so users see the same "what / how to use / summary"
 * explainer everywhere a varga is selected.
 */
export function VargaGuideCard({ code, variant = "card" }: VargaGuideCardProps) {
  const guide = getVargaGuide(code);
  if (!guide) return null;

  const def = VARGA_DIVISORS[code];
  const boxed = variant === "card";

  return (
    <div
      className={boxed ? "glass-card p-4" : "space-y-3"}
      data-testid={`varga-guide-${code.toLowerCase()}`}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3
          className="text-xs font-semibold uppercase tracking-wide"
          style={{ color: "var(--accent)" }}
        >
          {guide.classicName}
          {def ? (
            <span className="ml-1 font-normal" style={{ color: "var(--text-muted)" }}>
              ({code} ÷{def.divisor})
            </span>
          ) : null}
        </h3>
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          How to read this chart
        </span>
      </div>

      <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
        {guide.description}
      </p>

      <div className="flex flex-wrap gap-1.5">
        {guide.governs.map((g) => (
          <span
            key={g}
            className="rounded-full px-2.5 py-0.5 text-xs font-medium"
            style={{
              backgroundColor: "var(--bg-surface-700)",
              color: "var(--text-primary)",
              border: "1px solid var(--border-primary)",
            }}
          >
            {g}
          </span>
        ))}
      </div>

      <div className="space-y-1 rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
        <p className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
          Mechanics
        </p>
        <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {guide.mechanics}
        </p>
      </div>

      <ol className="list-decimal space-y-1 pl-5">
        {guide.howToUse.map((step) => (
          <li key={step} className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            {step}
          </li>
        ))}
      </ol>

      <div className="rounded-lg p-3" style={{ backgroundColor: "var(--bg-surface-700)" }}>
        <p className="text-xs leading-snug" style={{ color: "var(--text-primary)" }}>
          <span className="font-semibold" style={{ color: "var(--accent)" }}>
            Summary:{" "}
          </span>
          {guide.summary}
        </p>
      </div>
    </div>
  );
}