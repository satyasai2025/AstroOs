"use client";

/**
 * KP Overview — the high-level architecture view from the mockup:
 * the three engine tiers (Foundation → Analysis → Timing), the engine
 * module catalogue, and the data flow down to evidence/reasoning.
 */

const ENGINE_TIERS = [
  {
    tier: "Foundation Engine",
    tone: "#60a5fa",
    modules: [
      "Calculate Cusps",
      "Cusp Degrees",
      "Sign Lords",
      "Star Lords",
      "Sub Lords",
      "Sub-Sub Lords",
      "House Occupancy",
      "Node Connections",
      "KP Positions Snapshot",
    ],
  },
  {
    tier: "Analysis Engine",
    tone: "#fbbf24",
    modules: [
      "CSL Decision",
      "Significators",
      "Ruling Planets",
      "Event Promise",
      "Special Factors",
      "Cuspal Interlinks",
      "Evidence Chain",
    ],
  },
  {
    tier: "Timing Engine",
    tone: "#34d399",
    modules: [
      "Dasha Link",
      "Ruling Planet Triggers",
      "Transit Triggers",
      "Timing Windows",
      "Fructification Windows",
    ],
  },
];

export function KPOverview() {
  return (
    <div className="space-y-5">
      <div className="glass-card p-5">
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          KP Analysis — Architecture
        </h3>
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          One coherent pipeline with many analytical views: the calculation is done once on the
          backend and every module here reads from that same chart snapshot.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        {ENGINE_TIERS.map((tier) => (
          <div key={tier.tier} className="glass-card p-4">
            <div
              className="mb-3 flex items-center justify-between rounded-lg px-3 py-2"
              style={{ backgroundColor: `${tier.tone}1f`, border: `1px solid ${tier.tone}40` }}
            >
              <span className="text-sm font-semibold" style={{ color: tier.tone }}>
                {tier.tier}
              </span>
            </div>
            <ul className="space-y-1.5">
              {tier.modules.map((m) => (
                <li
                  key={m}
                  className="flex items-center gap-2 text-xs"
                  style={{ color: "var(--text-secondary)" }}
                >
                  <span className="inline-block h-1.5 w-1.5 rounded-full" style={{ backgroundColor: tier.tone }} />
                  {m}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="glass-card p-5">
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Data Flow
        </h3>
        <ol className="flex flex-wrap items-center gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
          {["Swiss Ephemeris", "Astronomy Engine", "Chart Engine", "KP Calculation Layer", "KP Analysis Engine", "KP Evidence / Explanation", "Frontend"].map(
            (step, i) => (
              <li key={step} className="flex items-center gap-2">
                <span className="rounded-full border px-3 py-1" style={{ borderColor: "var(--border-primary)" }}>
                  {step}
                </span>
                {i < 6 && <span aria-hidden="true" style={{ color: "var(--accent)" }}>→</span>}
              </li>
            ),
          )}
        </ol>
      </div>
    </div>
  );
}
