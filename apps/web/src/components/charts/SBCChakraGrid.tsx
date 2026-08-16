"use client";

import { useMemo, useState } from "react";
import { useSBCReport, type SBCGridPlanet } from "@/lib/sbc";
import { FULL_GRID, vedhaPath } from "@/lib/sbcCellnumTable";

/**
 * AstroOS — Sarvatobhadra Chakra (SBC) full 9x9 chakra display.
 *
 * The dedicated, full-real-estate counterpart to a JHora-style SBC
 * screen: all 81 cells (28 nakshatra border cells + 4 corners + 49
 * interior cells), live planet positions, and click-to-highlight
 * Vedha rays (matching the "Highlight aspects (vedhas) FROM this star"
 * right-click behaviour this project's SBC grid was cross-verified
 * against — see docs/sarvatobhadra_vedha_table.md and
 * apps/api/services/sbc_vedha_engine.py's module docstring).
 *
 * Interior cells show their real CellNum (see lib/sbcCellnumTable.ts)
 * rather than the classical Devanagari Varna letters JHora also draws
 * in them — that letter-grid is a separate, real classical sub-system
 * (name/sound-based analysis) this project has one unverified xlsm
 * extraction of and no independently-checked source for, so it's left
 * out rather than reproduced from a single unverified extraction.
 */

const UPPER_ROW = ["dhanishtha", "shatabhisha", "purva_bhadrapada", "uttara_bhadrapada", "revati", "ashwini", "bharani"];
const RIGHT_COLUMN = ["krittika", "rohini", "mrigashira", "ardra", "punarvasu", "pushya", "ashlesha"];
const BOTTOM_ROW = ["magha", "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati", "vishakha"];
const LEFT_COLUMN = ["anuradha", "jyeshtha", "mula", "purva_ashadha", "uttara_ashadha", "abhijit", "shravana"];

const NAKSHATRA_LABEL: Record<string, string> = {
  dhanishtha: "Dhan", shatabhisha: "Sata", purva_bhadrapada: "PBha", uttara_bhadrapada: "UBha",
  revati: "Reva", ashwini: "Aswi", bharani: "Bhar",
  krittika: "Krit", rohini: "Rohi", mrigashira: "Mrig", ardra: "Ardr", punarvasu: "Puna",
  pushya: "Push", ashlesha: "Asre",
  magha: "Magh", purva_phalguni: "PPha", uttara_phalguni: "UPha", hasta: "Hast", chitra: "Chit",
  swati: "Swat", vishakha: "Visa",
  anuradha: "Anu", jyeshtha: "Jye", mula: "Mool", purva_ashadha: "PSha", uttara_ashadha: "USha",
  abhijit: "Abhi", shravana: "Srav",
};

const PLANET_GLYPHS: Record<string, string> = {
  sun: "Su", moon: "Mo", mars: "Ma", mercury: "Me", jupiter: "Ju",
  venus: "Ve", saturn: "Sa", rahu: "Ra", ketu: "Ke",
};

const DIRECTION_COLOR: Record<"front" | "left" | "right", string> = {
  front: "rgba(52, 211, 153, 0.35)",  // green
  left: "rgba(56, 189, 248, 0.35)",   // blue
  right: "rgba(248, 113, 113, 0.35)", // red
};

const GRID_MIN = 1;
const GRID_MAX = 9;

function buildBorder(): Record<string, [number, number]> {
  const border: Record<string, [number, number]> = {};
  UPPER_ROW.forEach((n, i) => (border[n] = [2 + i, 1]));
  RIGHT_COLUMN.forEach((n, i) => (border[n] = [9, 2 + i]));
  BOTTOM_ROW.forEach((n, i) => (border[n] = [8 - i, 9]));
  LEFT_COLUMN.forEach((n, i) => (border[n] = [1, 8 - i]));
  return border;
}

const SBC_BORDER = buildBorder();
const ALL_NAKSHATRAS = Object.keys(SBC_BORDER);

function planetsByNakshatra(positions: SBCGridPlanet[]): Record<string, SBCGridPlanet[]> {
  const map: Record<string, SBCGridPlanet[]> = {};
  for (const p of positions) {
    (map[p.nakshatra] ??= []).push(p);
  }
  return map;
}

export function SBCChakraGrid() {
  const [janmaNakshatra, setJanmaNakshatra] = useState<string>("ashwini");
  const [rayFrom, setRayFrom] = useState<string | null>(null);
  const { data, isLoading, error } = useSBCReport(null, janmaNakshatra);

  const grouped = useMemo(() => (data ? planetsByNakshatra(data.positions) : {}), [data]);

  const highlightedCells = useMemo(() => {
    if (!rayFrom) return {};
    const map: Record<number, "front" | "left" | "right"> = {};
    (["front", "left", "right"] as const).forEach((dir) => {
      for (const cellnum of vedhaPath(rayFrom, dir)) {
        map[cellnum] = dir;
      }
    });
    return map;
  }, [rayFrom]);

  const cells = useMemo(() => {
    const grid: { col: number; row: number; nakshatra: string | null; cellnum: number }[][] = [];
    for (let row = GRID_MIN; row <= GRID_MAX; row++) {
      const rowCells: { col: number; row: number; nakshatra: string | null; cellnum: number }[] = [];
      for (let col = GRID_MIN; col <= GRID_MAX; col++) {
        const cellnum = FULL_GRID[`${col},${row}`];
        const nakshatra = ALL_NAKSHATRAS.find((n) => SBC_BORDER[n][0] === col && SBC_BORDER[n][1] === row) ?? null;
        rowCells.push({ col, row, nakshatra, cellnum });
      }
      grid.push(rowCells);
    }
    return grid;
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            Sarvatobhadra Chakra
          </h2>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            9x9 grid, 28 nakshatras (Abhijit included) on the border — click a nakshatra cell to highlight its
            Vedha rays, same as JHora&apos;s &quot;Highlight aspects (vedhas) FROM this star&quot;.
          </p>
        </div>
        <label className="flex items-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
          Janma element
          <select
            value={janmaNakshatra}
            onChange={(e) => setJanmaNakshatra(e.target.value)}
            className="rounded border px-2 py-1 text-xs"
            style={{ borderColor: "var(--border-primary)", background: "var(--bg-secondary)", color: "var(--text-primary)" }}
          >
            {ALL_NAKSHATRAS.map((n) => (
              <option key={n} value={n}>
                {NAKSHATRA_LABEL[n] ?? n}
              </option>
            ))}
          </select>
        </label>
      </div>

      {isLoading && (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          Computing current grid…
        </p>
      )}
      {error && (
        <p className="text-sm" style={{ color: "#f87171" }}>
          Could not load SBC grid.
        </p>
      )}

      {data && (
        <>
          <div className="flex items-center gap-4 text-[11px]" style={{ color: "var(--text-muted)" }}>
            <span>
              <span className="inline-block h-2.5 w-2.5 rounded-sm align-middle" style={{ background: DIRECTION_COLOR.front }} /> Front
            </span>
            <span>
              <span className="inline-block h-2.5 w-2.5 rounded-sm align-middle" style={{ background: DIRECTION_COLOR.left }} /> Left
            </span>
            <span>
              <span className="inline-block h-2.5 w-2.5 rounded-sm align-middle" style={{ background: DIRECTION_COLOR.right }} /> Right
            </span>
            {rayFrom && (
              <button
                type="button"
                onClick={() => setRayFrom(null)}
                className="rounded-full border px-2 py-0.5"
                style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}
              >
                Clear rays ({NAKSHATRA_LABEL[rayFrom] ?? rayFrom})
              </button>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="border-collapse text-center" style={{ tableLayout: "fixed" }}>
              <tbody>
                {cells.map((rowCells, rIdx) => (
                  <tr key={rIdx}>
                    {rowCells.map((cell, cIdx) => {
                      const isJanma = cell.nakshatra === janmaNakshatra;
                      const isRayOrigin = cell.nakshatra === rayFrom;
                      const rayDirection = highlightedCells[cell.cellnum];
                      const occupants = cell.nakshatra ? grouped[cell.nakshatra] ?? [] : [];

                      let background = "var(--bg-secondary)";
                      if (isJanma) background = "rgba(250, 204, 21, 0.18)";
                      if (rayDirection) background = DIRECTION_COLOR[rayDirection];
                      if (isRayOrigin) background = "rgba(250, 204, 21, 0.35)";

                      return (
                        <td
                          key={cIdx}
                          onClick={() => cell.nakshatra && setRayFrom(cell.nakshatra === rayFrom ? null : cell.nakshatra)}
                          className="h-14 w-16 border p-0.5 align-top"
                          style={{
                            borderColor: isJanma ? "#facc15" : "var(--border-primary)",
                            borderWidth: isJanma ? 2 : 1,
                            background,
                            cursor: cell.nakshatra ? "pointer" : "default",
                          }}
                        >
                          <div className="flex h-full flex-col justify-between">
                            {cell.nakshatra ? (
                              <>
                                <span className="text-[10px]" style={{ color: isJanma ? "#facc15" : "var(--text-secondary)" }}>
                                  {NAKSHATRA_LABEL[cell.nakshatra]}
                                </span>
                                <span className="text-[13px] font-bold leading-none" style={{ color: "#38bdf8" }}>
                                  {occupants.map((o) => PLANET_GLYPHS[o.planet] ?? o.planet).join(" ")}
                                </span>
                              </>
                            ) : (
                              <span className="text-[9px]" style={{ color: "var(--text-muted)" }}>
                                {cell.cellnum}
                              </span>
                            )}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>
            Tithi {data.tithi_number} ·{" "}
            {new Date(data.moment_utc).toLocaleString("en-US", {
              year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
            })}
            . Interior cell numbers are real CellNum values (source: a real SBC tool&apos;s Vedha_Map sheet),
            not decorative — they&apos;re what the Front/Left/Right ray highlighting above actually checks against.
          </p>

          {data.vedha_result && (
            <div className="space-y-1 border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                  Vedha onto {NAKSHATRA_LABEL[janmaNakshatra] ?? janmaNakshatra} (Janma element)
                </span>
                <span
                  className="rounded-full px-2 py-0.5 text-[10px] font-medium uppercase"
                  style={{
                    color: data.vedha_result.total_score > 0 ? "#34d399" : "var(--text-muted)",
                    border: `1px solid ${data.vedha_result.total_score > 0 ? "#34d399" : "var(--border-primary)"}`,
                  }}
                >
                  Score {data.vedha_result.total_score.toFixed(1)}
                </span>
              </div>

              {data.vedha_result.zeroed_by_malefic_conjunction && (
                <p className="text-xs" style={{ color: "#f87171" }}>
                  A casting benefic shares its nakshatra with a malefic — total score zeroed (all-or-nothing rule).
                </p>
              )}

              {data.vedha_result.hits.length === 0 ? (
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                  No benefic Vedha hits right now.
                </p>
              ) : (
                <ul className="space-y-0.5 text-sm">
                  {data.vedha_result.hits.map((h, i) => (
                    <li key={i} style={{ color: "var(--text-secondary)" }}>
                      <button
                        type="button"
                        className="underline decoration-dotted"
                        onClick={() => setRayFrom(h.from_nakshatra)}
                      >
                        {PLANET_GLYPHS[h.planet] ?? h.planet} in {NAKSHATRA_LABEL[h.from_nakshatra] ?? h.from_nakshatra}
                      </button>{" "}
                      casts {h.direction} — score {h.score.toFixed(1)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
