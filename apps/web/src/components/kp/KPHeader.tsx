"use client";

/**
 * KP Header — the "Precision + Logic + Evidence" masthead plus the six
 * KP principles shown in the mockup. Purely presentational.
 */

export function KPHeader() {
  const principles = [
    { title: "Cuspal Analysis (CSL)", detail: "Sub Lord of every cusp is the primary significator tool." },
    { title: "Significators", detail: "Houses signified by occupation, ownership and stellar links." },
    { title: "Event Promise", detail: "Yes/No judgment from CSL ↔ required-house alignment." },
    { title: "Timing Windows", detail: "Dasha + Transit triggers only after promise is positive." },
    { title: "Special Factors", detail: "Fortuna, nodes, retrogrades, interlinks and more." },
    { title: "Evidence Based Judgment", detail: "Every verdict carries a full reasoning chain." },
  ];

  return (
    <div className="mb-6 space-y-4">
      <div className="glass-card border-l-4 p-5" style={{ borderLeftColor: "var(--accent)" }}>
        <h2 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
          KP Analysis
        </h2>
        <p className="mt-1 text-sm font-medium" style={{ color: "var(--accent)" }}>
          Precision + Logic + Evidence
        </p>
        <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
          Krishnamurti Paddhati — Cusps, Sub Lords, Significators, Events, Timing &amp; More.
          Every figure below is derived from this chart&apos;s real cusp and planet positions
          (Star Lord / Sub Lord / Sub-Sub Lord stamped by the backend ephemeris), never invented.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {principles.map((p) => (
          <div key={p.title} className="glass-card p-4">
            <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
              {p.title}
            </p>
            <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
              {p.detail}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
