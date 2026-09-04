"use client";

import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { SouthIndianChart } from "@/components/charts/SouthIndianChart";
import { useWorkflowStore } from "@/lib/store";
import type { AscendantSchema, TransitResponse } from "@/lib/types";

export function TransitWheel({
  transits,
  houseReference,
  natalAscendant,
}: {
  transits: TransitResponse;
  houseReference: "moon" | "ascendant";
  natalAscendant?: AscendantSchema;
}) {
  const chartStyle = useWorkflowStore((s) => s.chartStyle);
  const setChartStyle = useWorkflowStore((s) => s.setChartStyle);

  const referenceRashi = houseReference === "ascendant" && natalAscendant ? natalAscendant.rashi : transits.natal_moon_rashi;
  const gocharaAscendant = { rashi: referenceRashi };
  const planets = transits.planets.map((p) => ({
    planet: p.planet,
    rashi: p.transit_rashi,
  }));

  const chartTitle = houseReference === "ascendant" ? "Gochara (Natal Lagna)" : "Gochara (Natal Moon)";

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between px-1">
        <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
          {chartTitle}
        </span>
        <div className="flex items-center rounded-lg p-0.5 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
          <button
            type="button"
            onClick={() => setChartStyle("north")}
            className={`px-2 py-0.5 text-[10px] font-semibold rounded transition ${
              chartStyle === "north"
                ? "bg-cyan-500 text-white shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
            aria-pressed={chartStyle === "north"}
          >
            North
          </button>
          <button
            type="button"
            onClick={() => setChartStyle("south")}
            className={`px-2 py-0.5 text-[10px] font-semibold rounded transition ${
              chartStyle === "south"
                ? "bg-cyan-500 text-white shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
            aria-pressed={chartStyle === "south"}
          >
            South
          </button>
        </div>
      </div>

      {chartStyle === "south" ? (
        <SouthIndianChart
          title={chartTitle}
          ascendant={gocharaAscendant}
          planets={planets}
          size={340}
        />
      ) : (
        <NorthIndianChart
          title={chartTitle}
          ascendant={gocharaAscendant}
          planets={planets}
          size={340}
        />
      )}
    </div>
  );
}
