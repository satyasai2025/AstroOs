/**
 * AstroOS — Sarvatobhadra Chakra (SBC) CellNum grid — frontend mirror.
 *
 * Duplicates packages/shared/sbc_cellnum_table.py's 32 anchor rows
 * (Right/Front/Left CellNum paths per nakshatra, JHora-cross-checked
 * for Dhanishtha/Shatabhisha) so the client can highlight a clicked
 * nakshatra's Vedha rays without a round trip — same "static reference
 * geometry duplicated on the frontend" judgment call as SBC_BORDER in
 * SBCGridPanel.tsx / lib/astro.ts's PLANET_SYMBOLS.
 *
 * FULL_GRID additionally maps every one of the 81 cells (not just the
 * 28 nakshatra anchors) to its (col, row) position on the 9x9 grid.
 * The 49 interior cells are NOT independently sourced — they're
 * derived from the 7 upper-row nakshatras' real "front" paths, which
 * are straight vertical lines (front == classical Opposite, straight-
 * across) covering columns 2-8 x rows 2-9 completely. Cross-checked
 * against the left-column nakshatras' front paths (horizontal lines)
 * for every interior cell they also pass through — zero mismatches.
 * This is a legitimate geometric reconstruction from real sourced path
 * data, not a fabricated layout.
 */

export interface SBCAnchor {
  cellnum: number;
  nakshatra: string | null;
  right: number[];
  front: number[];
  left: number[];
}

const RAW: [number, string | null, number[], number[], number[]][] = [
  [1, null, [11, 21, 31, 41, 51, 61, 71, 81], [], []],
  [2, "krittika", [10], [11, 20, 29, 38, 47, 56, 65, 74], [12, 22, 32, 42, 52, 62, 72]],
  [3, "rohini", [11, 19], [12, 21, 30, 39, 48, 57, 66, 75], [13, 23, 33, 43, 53, 63]],
  [4, "mrigashira", [12, 20, 28], [13, 22, 31, 40, 49, 58, 67, 76], [14, 24, 34, 44, 54]],
  [5, "ardra", [13, 21, 29, 37], [14, 23, 32, 41, 50, 59, 68, 77], [15, 25, 35, 45]],
  [6, "punarvasu", [14, 22, 30, 38, 46], [15, 24, 33, 42, 51, 60, 69, 78], [16, 26, 36]],
  [7, "pushya", [15, 23, 31, 39, 47, 55], [16, 25, 34, 43, 52, 61, 70, 79], [17, 27]],
  [8, "ashlesha", [16, 24, 32, 40, 48, 56, 64], [17, 26, 35, 44, 53, 62, 71, 80], [18]],
  [9, null, [17, 25, 33, 41, 49, 57, 65, 73], [], []],
  [18, "magha", [8], [17, 16, 15, 14, 13, 12, 11, 10], [26, 34, 42, 50, 58, 66, 74]],
  [27, "purva_phalguni", [17, 7], [26, 25, 24, 23, 22, 21, 20, 19], [35, 43, 51, 59, 67, 75]],
  [36, "uttara_phalguni", [26, 16, 6], [35, 34, 33, 32, 31, 30, 29, 28], [44, 52, 60, 68, 76]],
  [45, "hasta", [35, 25, 15, 5], [44, 43, 42, 41, 40, 39, 38, 37], [53, 61, 69, 77]],
  [54, "chitra", [44, 34, 24, 14, 4], [53, 52, 51, 50, 49, 48, 47, 46], [62, 70, 78]],
  [63, "swati", [53, 43, 33, 23, 13, 3], [62, 61, 60, 59, 58, 57, 56, 55], [71, 79]],
  [72, "vishakha", [62, 52, 42, 32, 22, 12, 2], [71, 70, 69, 68, 67, 66, 65, 64], [80]],
  [81, null, [71, 61, 51, 41, 31, 21, 11, 1], [], []],
  [80, "anuradha", [72], [71, 62, 53, 44, 35, 26, 17, 8], [70, 60, 50, 40, 30, 20, 10]],
  [79, "jyeshtha", [71, 63], [70, 61, 52, 43, 34, 25, 16, 7], [69, 59, 49, 39, 29, 19]],
  [78, "mula", [70, 62, 54], [69, 60, 51, 42, 33, 24, 15, 6], [68, 58, 48, 38, 28]],
  [77, "purva_ashadha", [69, 61, 53, 45], [68, 59, 50, 41, 32, 23, 14, 5], [67, 57, 47, 37]],
  [76, "uttara_ashadha", [68, 60, 52, 44, 36], [67, 58, 49, 40, 31, 22, 13, 4], [66, 56, 46]],
  [75, "abhijit", [67, 59, 51, 43, 35, 27], [66, 57, 48, 39, 30, 21, 12, 3], [65, 55]],
  [74, "shravana", [66, 58, 50, 42, 34, 26, 18], [65, 56, 47, 38, 29, 20, 11, 2], [64]],
  [73, null, [65, 57, 49, 41, 33, 25, 17, 9], [], []],
  [64, "dhanishtha", [74], [65, 66, 67, 68, 69, 70, 71, 72], [56, 48, 40, 32, 24, 16, 8]],
  [55, "shatabhisha", [65, 75], [56, 57, 58, 59, 60, 61, 62, 63], [47, 39, 31, 23, 15, 7]],
  [46, "purva_bhadrapada", [56, 66, 76], [47, 48, 49, 50, 51, 52, 53, 54], [38, 30, 22, 14, 6]],
  [37, "uttara_bhadrapada", [47, 57, 67, 77], [38, 39, 40, 41, 42, 43, 44, 45], [29, 21, 13, 5]],
  [28, "revati", [38, 48, 58, 68, 78], [29, 30, 31, 32, 33, 34, 35, 36], [20, 12, 4]],
  [19, "ashwini", [29, 39, 49, 59, 69, 79], [20, 21, 22, 23, 24, 25, 26, 27], [11, 3]],
  [10, "bharani", [20, 30, 40, 50, 60, 70, 80], [11, 12, 13, 14, 15, 16, 17, 18], [2]],
];

export const SBC_ANCHORS: Record<number, SBCAnchor> = Object.fromEntries(
  RAW.map(([cellnum, nakshatra, right, front, left]) => [cellnum, { cellnum, nakshatra, right, front, left }])
);

export const NAKSHATRA_TO_CELLNUM: Record<string, number> = Object.fromEntries(
  RAW.filter(([, n]) => n !== null).map(([cellnum, n]) => [n as string, cellnum])
);

export function vedhaPath(nakshatra: string, direction: "front" | "left" | "right"): number[] {
  const cellnum = NAKSHATRA_TO_CELLNUM[nakshatra];
  return SBC_ANCHORS[cellnum][direction];
}

// (col,row) -> cellnum for all 81 cells, 1-indexed. Derived per this
// file's module docstring (border anchors + upper-row/left-column
// front paths).
export const FULL_GRID: Record<string, number> = {
  "2,1": 64, "3,1": 55, "4,1": 46, "5,1": 37, "6,1": 28, "7,1": 19, "8,1": 10,
  "9,2": 2, "9,3": 3, "9,4": 4, "9,5": 5, "9,6": 6, "9,7": 7, "9,8": 8,
  "8,9": 18, "7,9": 27, "6,9": 36, "5,9": 45, "4,9": 54, "3,9": 63, "2,9": 72,
  "1,8": 80, "1,7": 79, "1,6": 78, "1,5": 77, "1,4": 76, "1,3": 75, "1,2": 74,
  "2,2": 65, "2,3": 66, "2,4": 67, "2,5": 68, "2,6": 69, "2,7": 70, "2,8": 71,
  "3,2": 56, "3,3": 57, "3,4": 58, "3,5": 59, "3,6": 60, "3,7": 61, "3,8": 62,
  "4,2": 47, "4,3": 48, "4,4": 49, "4,5": 50, "4,6": 51, "4,7": 52, "4,8": 53,
  "5,2": 38, "5,3": 39, "5,4": 40, "5,5": 41, "5,6": 42, "5,7": 43, "5,8": 44,
  "6,2": 29, "6,3": 30, "6,4": 31, "6,5": 32, "6,6": 33, "6,7": 34, "6,8": 35,
  "7,2": 20, "7,3": 21, "7,4": 22, "7,5": 23, "7,6": 24, "7,7": 25, "7,8": 26,
  "8,2": 11, "8,3": 12, "8,4": 13, "8,5": 14, "8,6": 15, "8,7": 16, "8,8": 17,
  "1,1": 1, "9,1": 9, "1,9": 73, "9,9": 81,
};

export const CELLNUM_TO_COORD: Record<number, [number, number]> = Object.fromEntries(
  Object.entries(FULL_GRID).map(([key, cellnum]) => {
    const [col, row] = key.split(",").map(Number);
    return [cellnum, [col, row]];
  })
);
