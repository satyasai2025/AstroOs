"use client";

import { useMemo, useState } from "react";
import {
  computeAllHouseSignificators,
  computeEventSignificators,
  subLordDusthanaCheck,
  KP_EVENT_HOUSE_GROUPS,
  GRADE_LABELS,
  type KPEventKey,
  type SignificatorGrade,
} from "@/lib/kpSignificators";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import type { WorkflowAnalysisResponse } from "@/lib/types";

/** MD -> AD -> PD -> ... matching the depth getCurrentDashaChain() walks. */
const DASHA_LEVEL_NAMES = ["Mahadasha", "Antardasha", "Pratyantardasha", "Sookshma", "Prana"];

interface KPSignificatorExplorerProps {
  result: WorkflowAnalysisResponse;
}

const GRADE_COLOR: Record<SignificatorGrade, string> = {
  A: "#34d399", // strongest
  B: "#60a5fa",
  C: "#fbbf24",
  D: "#f87171", // weakest (just the house's own lord, no star/occupancy link)
};

function GradeBadge({ grade }: { grade: SignificatorGrade }) {
  return (
    <span
      className="inline-flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold"
      style={{ backgroundColor: `${GRADE_COLOR[grade]}26`, color: GRADE_COLOR[grade] }}
      title={GRADE_LABELS[grade]}
    >
      {grade}
    </span>
  );
}

export function KPSignificatorExplorer({ result }: KPSignificatorExplorerProps) {
  const { chart } = result;
  const [eventKey, setEventKey] = useState<KPEventKey>("marriage");
  const [showAllHouses, setShowAllHouses] = useState(false);

  const allHouseSigs = useMemo(() => computeAllHouseSignificators(chart), [chart]);
  const eventResult = useMemo(
    () => computeEventSignificators(chart, eventKey, allHouseSigs),
    [chart, eventKey, allHouseSigs],
  );

  // Dasha integration — KP reads an event as fructifying when its
  // significator planets' OWN dasha/bhukti periods are running. Real data:
  // the currently-active MD/AD/PD chain from this chart's actual computed
  // dasha tree (same helper the Prediction Chain Explorer uses), not a new
  // timing rule invented for this view.
  const dashaChain = useMemo(() => getCurrentDashaChain(result.dasha.mahadashas), [result.dasha]);
  const activeDashaLevelByPlanet = useMemo(() => {
    const map = new Map<string, string>();
    dashaChain.forEach((period, i) => {
      // A planet can repeat across levels (e.g. same lord for MD and AD is
      // impossible in Vimshottari, but keep the FIRST/highest level found).
      if (!map.has(period.lord)) {
        map.set(period.lord, DASHA_LEVEL_NAMES[i] ?? `Level ${i + 1}`);
      }
    });
    return map;
  }, [dashaChain]);

  return (
    <div className="w-full max-w-4xl space-y-6">
      <div className="glass-card p-5">
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          KP Significators
        </h3>
        <p className="mb-4 text-xs" style={{ color: "var(--text-muted)" }}>
          Krishnamurti Paddhati house-significator grading (A strongest → D weakest). Star Lord and
          Sub Lord data come from this chart's actual planet/cusp positions — see the Chart tab for
          the raw values. The "Dasha Now" column flags significators whose own Mahadasha/Antardasha/
          Pratyantardasha is running today — classically when a promised event is most likely to
          fructify.
        </p>

        <div className="mb-4 flex flex-wrap gap-2">
          {(Object.keys(KP_EVENT_HOUSE_GROUPS) as KPEventKey[]).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setEventKey(key)}
              className="rounded-full px-3 py-1 text-xs font-semibold transition"
              style={{
                backgroundColor: eventKey === key ? "var(--accent)" : "var(--bg-card)",
                color: eventKey === key ? "var(--accent-text)" : "var(--text-secondary)",
                border: `1px solid ${eventKey === key ? "var(--accent)" : "var(--border-primary)"}`,
              }}
            >
              {KP_EVENT_HOUSE_GROUPS[key].label}
            </button>
          ))}
        </div>

        <p className="mb-3 text-xs" style={{ color: "var(--text-secondary)" }}>
          Houses read for {eventResult.label}: {eventResult.houses.join(", ")}
        </p>

        <div className="w-full overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-xs uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                <th className="py-2 pr-4">Planet</th>
                <th className="py-2 pr-4">Houses Signified</th>
                <th className="py-2 pr-4">Strongest Grade</th>
                <th className="py-2 pr-4">Sub Lord</th>
                <th className="py-2 pr-4">Sub Sub Lord</th>
                <th className="py-2 pr-4">Dasha Now</th>
                <th className="py-2">Caution</th>
              </tr>
            </thead>
            <tbody>
              {eventResult.planets.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-4 text-center text-xs" style={{ color: "var(--text-muted)" }}>
                    No planets signify these houses in this chart.
                  </td>
                </tr>
              )}
              {eventResult.planets.map((ps) => {
                const caution = subLordDusthanaCheck(chart, ps.planet, allHouseSigs);
                const planetData = chart.planets.find((p) => p.planet === ps.planet);
                const activeDashaLevel = activeDashaLevelByPlanet.get(ps.planet);
                return (
                  <tr key={ps.planet} className="border-b" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                    <td className="py-2 pr-4 font-medium">{ps.planet}</td>
                    <td className="py-2 pr-4" style={{ color: "var(--text-secondary)" }}>
                      {ps.housesSignified.join(", ")} of {eventResult.houses.join(", ")}
                    </td>
                    <td className="py-2 pr-4">
                      <GradeBadge grade={ps.strongestGrade} />
                    </td>
                    <td className="py-2 pr-4" style={{ color: "var(--text-secondary)" }}>
                      {caution?.subLord ?? "—"}
                    </td>
                    <td className="py-2 pr-4" style={{ color: "var(--text-secondary)" }}>
                      {planetData?.sub_sub_lord || "—"}
                    </td>
                    <td className="py-2 pr-4">
                      {activeDashaLevel ? (
                        <span
                          className="rounded-full px-2 py-0.5 text-[10px] font-medium"
                          style={{ backgroundColor: "rgba(52,211,153,0.15)", color: "#34d399" }}
                          title={`${ps.planet}'s own ${activeDashaLevel} is running right now — classically when this significator is most likely to fructify`}
                        >
                          {activeDashaLevel}
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-muted)" }}>—</span>
                      )}
                    </td>
                    <td className="py-2">
                      {caution?.cautionFlag ? (
                        <span
                          className="rounded-full px-2 py-0.5 text-[10px] font-medium"
                          style={{ backgroundColor: "rgba(248,113,113,0.15)", color: "#f87171" }}
                          title={`Sub Lord also signifies house(s) ${caution.dusthanaHousesSignified.join(", ")} (dusthana)`}
                        >
                          Sub Lord ties to dusthana
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-muted)" }}>—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="glass-card p-5">
        <button
          type="button"
          onClick={() => setShowAllHouses((v) => !v)}
          className="flex w-full items-center justify-between text-left"
        >
          <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            All 12 Houses — Full Significator Table
          </h3>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            {showAllHouses ? "Hide" : "Show"}
          </span>
        </button>

        {showAllHouses && (
          <div className="mt-4 space-y-4">
            {allHouseSigs.map((hs) => (
              <div key={hs.houseNumber} className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
                <p className="mb-1 text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
                  House {hs.houseNumber} ({hs.rashi ?? "—"}) — Lord: {hs.lord ?? "—"}
                  {hs.occupants.length > 0 && (
                    <span style={{ color: "var(--text-muted)" }}> · Occupants: {hs.occupants.join(", ")}</span>
                  )}
                </p>
                <div className="flex flex-wrap gap-2">
                  {hs.significators.length === 0 && (
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                      No significators found.
                    </span>
                  )}
                  {hs.significators.map((sig) => (
                    <span
                      key={sig.planet}
                      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs"
                      style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)", color: "var(--text-secondary)" }}
                    >
                      {sig.planet}
                      {sig.grades.map((g) => (
                        <GradeBadge key={g} grade={g} />
                      ))}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
