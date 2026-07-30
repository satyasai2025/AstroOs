"use client";

import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import type { AscendantSchema, TransitResponse } from "@/lib/types";

/**
 * The classical Gochara (transit) chart, with each graha placed by its
 * *transiting* rashi. `houseReference` picks which rashi stands in for
 * house 1: the natal Moon (Chandra Lagna — the traditional Gochara
 * convention) or the natal Ascendant (Lagna) itself. Both are computed
 * purely from real rashi values already on hand — no extra backend call
 * needed, since NorthIndianChart derives every planet's house from the
 * rashi offset against whichever rashi it's given as "ascendant". Reuses
 * NorthIndianChart as-is — this is exactly the "ascendant + planets" shape
 * it already renders for D1/varga charts.
 */
export function TransitWheel({
  transits,
  houseReference,
  natalAscendant,
}: {
  transits: TransitResponse;
  houseReference: "moon" | "ascendant";
  natalAscendant?: AscendantSchema;
}) {
  const referenceRashi = houseReference === "ascendant" && natalAscendant ? natalAscendant.rashi : transits.natal_moon_rashi;
  const gocharaAscendant = { rashi: referenceRashi };
  const planets = transits.planets.map((p) => ({
    planet: p.planet,
    rashi: p.transit_rashi,
  }));

  return (
    <div className="flex flex-col gap-2">
      <NorthIndianChart
        title={houseReference === "ascendant" ? "Gochara — houses from natal Lagna" : "Gochara — houses from natal Moon"}
        ascendant={gocharaAscendant}
        planets={planets}
        size={340}
      />
    </div>
  );
}
