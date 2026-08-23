/**
 * AstroOS — Sarvatobhadra Chakra (SBC) CellNum grid — frontend mirror.
 *
 * Duplicates packages/shared/sbc_cellnum_table.py's 32 anchor rows
 * (Right/Front/Left CellNum paths per nakshatra, Classical Vedic-cross-checked
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

export interface SBCCellSemantic {
  col: number;
  row: number;
  category: "nakshatra" | "rashi" | "swara" | "akshara" | "tithi";
  key: string;
  display_name_en: string;
  display_name_hi: string;
  layer: number;
  cell_num: number;
  metadata: {
    corner?: "NW" | "NE" | "SE" | "SW";
    nakshatra_number?: number;
    nakshatra_token?: string;
    rashi_code?: string;
    symbol?: string;
    tithi_group?: "nanda" | "bhadra" | "jaya" | "rikta" | "purna";
    tithis?: string;
    vara_overlay?: string[];
    vara_hi?: string;
    is_center?: boolean;
  };
}

export const SBC_81_CANONICAL: Record<string, SBCCellSemantic> = {
  // ── Ring 1 (9x9 Border): 4 Swaras (Corners) + 28 Nakshatras ───────────────
  "1,1": { col: 1, row: 1, category: "swara", key: "swara_a", display_name_en: "a", display_name_hi: "अ", layer: 1, cell_num: 1, metadata: { corner: "NW" } },
  "2,1": { col: 2, row: 1, category: "nakshatra", key: "dhanishtha", display_name_en: "Dhanishtha", display_name_hi: "धनिष्ठा", layer: 1, cell_num: 64, metadata: { nakshatra_number: 23, nakshatra_token: "dhanishtha" } },
  "3,1": { col: 3, row: 1, category: "nakshatra", key: "shatabhisha", display_name_en: "Shatabhisha", display_name_hi: "शतभिषा", layer: 1, cell_num: 55, metadata: { nakshatra_number: 24, nakshatra_token: "shatabhisha" } },
  "4,1": { col: 4, row: 1, category: "nakshatra", key: "purva_bhadrapada", display_name_en: "Purva Bhadra", display_name_hi: "पू.भाद्र.", layer: 1, cell_num: 46, metadata: { nakshatra_number: 25, nakshatra_token: "purva_bhadrapada" } },
  "5,1": { col: 5, row: 1, category: "nakshatra", key: "uttara_bhadrapada", display_name_en: "Uttara Bhadra", display_name_hi: "उ.भाद्र.", layer: 1, cell_num: 37, metadata: { nakshatra_number: 26, nakshatra_token: "uttara_bhadrapada" } },
  "6,1": { col: 6, row: 1, category: "nakshatra", key: "revati", display_name_en: "Revati", display_name_hi: "रेवती", layer: 1, cell_num: 28, metadata: { nakshatra_number: 27, nakshatra_token: "revati" } },
  "7,1": { col: 7, row: 1, category: "nakshatra", key: "ashwini", display_name_en: "Ashwini", display_name_hi: "अश्विनी", layer: 1, cell_num: 19, metadata: { nakshatra_number: 1, nakshatra_token: "ashwini" } },
  "8,1": { col: 8, row: 1, category: "nakshatra", key: "bharani", display_name_en: "Bharani", display_name_hi: "भरणी", layer: 1, cell_num: 10, metadata: { nakshatra_number: 2, nakshatra_token: "bharani" } },
  "9,1": { col: 9, row: 1, category: "swara", key: "swara_aa", display_name_en: "ā", display_name_hi: "आ", layer: 1, cell_num: 9, metadata: { corner: "NE" } },

  "9,2": { col: 9, row: 2, category: "nakshatra", key: "krittika", display_name_en: "Krittika", display_name_hi: "कृत्तिका", layer: 1, cell_num: 2, metadata: { nakshatra_number: 3, nakshatra_token: "krittika" } },
  "9,3": { col: 9, row: 3, category: "nakshatra", key: "rohini", display_name_en: "Rohini", display_name_hi: "रोहिणी", layer: 1, cell_num: 3, metadata: { nakshatra_number: 4, nakshatra_token: "rohini" } },
  "9,4": { col: 9, row: 4, category: "nakshatra", key: "mrigashira", display_name_en: "Mrigashira", display_name_hi: "मृगशिरा", layer: 1, cell_num: 4, metadata: { nakshatra_number: 5, nakshatra_token: "mrigashira" } },
  "9,5": { col: 9, row: 5, category: "nakshatra", key: "ardra", display_name_en: "Ardra", display_name_hi: "आर्द्रा", layer: 1, cell_num: 5, metadata: { nakshatra_number: 6, nakshatra_token: "ardra" } },
  "9,6": { col: 9, row: 6, category: "nakshatra", key: "punarvasu", display_name_en: "Punarvasu", display_name_hi: "पुनर्वसु", layer: 1, cell_num: 6, metadata: { nakshatra_number: 7, nakshatra_token: "punarvasu" } },
  "9,7": { col: 9, row: 7, category: "nakshatra", key: "pushya", display_name_en: "Pushya", display_name_hi: "पुष्य", layer: 1, cell_num: 7, metadata: { nakshatra_number: 8, nakshatra_token: "pushya" } },
  "9,8": { col: 9, row: 8, category: "nakshatra", key: "ashlesha", display_name_en: "Ashlesha", display_name_hi: "आश्लेषा", layer: 1, cell_num: 8, metadata: { nakshatra_number: 9, nakshatra_token: "ashlesha" } },
  "9,9": { col: 9, row: 9, category: "swara", key: "swara_i", display_name_en: "i", display_name_hi: "इ", layer: 1, cell_num: 81, metadata: { corner: "SE" } },

  "8,9": { col: 8, row: 9, category: "nakshatra", key: "magha", display_name_en: "Magha", display_name_hi: "मघा", layer: 1, cell_num: 18, metadata: { nakshatra_number: 10, nakshatra_token: "magha" } },
  "7,9": { col: 7, row: 9, category: "nakshatra", key: "purva_phalguni", display_name_en: "Purva Phalguni", display_name_hi: "पू.फाल्गुनी", layer: 1, cell_num: 27, metadata: { nakshatra_number: 11, nakshatra_token: "purva_phalguni" } },
  "6,9": { col: 6, row: 9, category: "nakshatra", key: "uttara_phalguni", display_name_en: "Uttara Phalguni", display_name_hi: "उ.फाल्गुनी", layer: 1, cell_num: 36, metadata: { nakshatra_number: 12, nakshatra_token: "uttara_phalguni" } },
  "5,9": { col: 5, row: 9, category: "nakshatra", key: "hasta", display_name_en: "Hasta", display_name_hi: "हस्त", layer: 1, cell_num: 45, metadata: { nakshatra_number: 13, nakshatra_token: "hasta" } },
  "4,9": { col: 4, row: 9, category: "nakshatra", key: "chitra", display_name_en: "Chitra", display_name_hi: "चित्रा", layer: 1, cell_num: 54, metadata: { nakshatra_number: 14, nakshatra_token: "chitra" } },
  "3,9": { col: 3, row: 9, category: "nakshatra", key: "swati", display_name_en: "Swati", display_name_hi: "स्वाती", layer: 1, cell_num: 63, metadata: { nakshatra_number: 15, nakshatra_token: "swati" } },
  "2,9": { col: 2, row: 9, category: "nakshatra", key: "vishakha", display_name_en: "Vishakha", display_name_hi: "विशाखा", layer: 1, cell_num: 72, metadata: { nakshatra_number: 16, nakshatra_token: "vishakha" } },
  "1,9": { col: 1, row: 9, category: "swara", key: "swara_ee", display_name_en: "ī", display_name_hi: "ई", layer: 1, cell_num: 73, metadata: { corner: "SW" } },

  "1,8": { col: 1, row: 8, category: "nakshatra", key: "anuradha", display_name_en: "Anuradha", display_name_hi: "अनुराधा", layer: 1, cell_num: 80, metadata: { nakshatra_number: 17, nakshatra_token: "anuradha" } },
  "1,7": { col: 1, row: 7, category: "nakshatra", key: "jyeshtha", display_name_en: "Jyeshtha", display_name_hi: "ज्येष्ठा", layer: 1, cell_num: 79, metadata: { nakshatra_number: 18, nakshatra_token: "jyeshtha" } },
  "1,6": { col: 1, row: 6, category: "nakshatra", key: "mula", display_name_en: "Mula", display_name_hi: "मूल", layer: 1, cell_num: 78, metadata: { nakshatra_number: 19, nakshatra_token: "mula" } },
  "1,5": { col: 1, row: 5, category: "nakshatra", key: "purva_ashadha", display_name_en: "Purva Ashadha", display_name_hi: "पूर्वाषाढ़ा", layer: 1, cell_num: 77, metadata: { nakshatra_number: 20, nakshatra_token: "purva_ashadha" } },
  "1,4": { col: 1, row: 4, category: "nakshatra", key: "uttara_ashadha", display_name_en: "Uttara Ashadha", display_name_hi: "उत्तराषाढ़ा", layer: 1, cell_num: 76, metadata: { nakshatra_number: 21, nakshatra_token: "uttara_ashadha" } },
  "1,3": { col: 1, row: 3, category: "nakshatra", key: "abhijit", display_name_en: "Abhijit", display_name_hi: "अभिजित", layer: 1, cell_num: 75, metadata: { nakshatra_number: 28, nakshatra_token: "abhijit" } },
  "1,2": { col: 1, row: 2, category: "nakshatra", key: "shravana", display_name_en: "Shravana", display_name_hi: "श्रवण", layer: 1, cell_num: 74, metadata: { nakshatra_number: 22, nakshatra_token: "shravana" } },

  // ── Ring 2 (7x7 Border): 4 Swaras (Corners) + 20 Aksharas (5 per side) ──
  "2,2": { col: 2, row: 2, category: "swara", key: "swara_u", display_name_en: "u", display_name_hi: "उ", layer: 2, cell_num: 65, metadata: { corner: "NW" } },
  "3,2": { col: 3, row: 2, category: "akshara", key: "akshara_ka", display_name_en: "ka", display_name_hi: "क", layer: 2, cell_num: 56, metadata: {} },
  "4,2": { col: 4, row: 2, category: "akshara", key: "akshara_kha", display_name_en: "kha", display_name_hi: "ख", layer: 2, cell_num: 47, metadata: {} },
  "5,2": { col: 5, row: 2, category: "akshara", key: "akshara_ga", display_name_en: "ga", display_name_hi: "ग", layer: 2, cell_num: 38, metadata: {} },
  "6,2": { col: 6, row: 2, category: "akshara", key: "akshara_gha", display_name_en: "gha", display_name_hi: "घ", layer: 2, cell_num: 29, metadata: {} },
  "7,2": { col: 7, row: 2, category: "akshara", key: "akshara_nga", display_name_en: "ṅa", display_name_hi: "ङ", layer: 2, cell_num: 20, metadata: {} },
  "8,2": { col: 8, row: 2, category: "swara", key: "swara_uu", display_name_en: "ū", display_name_hi: "ऊ", layer: 2, cell_num: 11, metadata: { corner: "NE" } },

  "8,3": { col: 8, row: 3, category: "akshara", key: "akshara_ca", display_name_en: "ca", display_name_hi: "च", layer: 2, cell_num: 12, metadata: {} },
  "8,4": { col: 8, row: 4, category: "akshara", key: "akshara_cha", display_name_en: "cha", display_name_hi: "छ", layer: 2, cell_num: 13, metadata: {} },
  "8,5": { col: 8, row: 5, category: "akshara", key: "akshara_ja", display_name_en: "ja", display_name_hi: "ज", layer: 2, cell_num: 14, metadata: {} },
  "8,6": { col: 8, row: 6, category: "akshara", key: "akshara_jha", display_name_en: "jha", display_name_hi: "झ", layer: 2, cell_num: 15, metadata: {} },
  "8,7": { col: 8, row: 7, category: "akshara", key: "akshara_nya", display_name_en: "ña", display_name_hi: "ञ", layer: 2, cell_num: 16, metadata: {} },
  "8,8": { col: 8, row: 8, category: "swara", key: "swara_ri", display_name_en: "ṛ", display_name_hi: "ऋ", layer: 2, cell_num: 17, metadata: { corner: "SE" } },

  "7,8": { col: 7, row: 8, category: "akshara", key: "akshara_tta", display_name_en: "ṭa", display_name_hi: "ट", layer: 2, cell_num: 26, metadata: {} },
  "6,8": { col: 6, row: 8, category: "akshara", key: "akshara_ttha", display_name_en: "ṭha", display_name_hi: "ठ", layer: 2, cell_num: 35, metadata: {} },
  "5,8": { col: 5, row: 8, category: "akshara", key: "akshara_dda", display_name_en: "ḍa", display_name_hi: "ड", layer: 2, cell_num: 44, metadata: {} },
  "4,8": { col: 4, row: 8, category: "akshara", key: "akshara_ddha", display_name_en: "ḍha", display_name_hi: "ढ", layer: 2, cell_num: 53, metadata: {} },
  "3,8": { col: 3, row: 8, category: "akshara", key: "akshara_nna", display_name_en: "ṇa", display_name_hi: "ण", layer: 2, cell_num: 62, metadata: {} },
  "2,8": { col: 2, row: 8, category: "swara", key: "swara_rii", display_name_en: "ṝ", display_name_hi: "ॠ", layer: 2, cell_num: 71, metadata: { corner: "SW" } },

  "2,7": { col: 2, row: 7, category: "akshara", key: "akshara_ta", display_name_en: "ta", display_name_hi: "त", layer: 2, cell_num: 70, metadata: {} },
  "2,6": { col: 2, row: 6, category: "akshara", key: "akshara_tha", display_name_en: "tha", display_name_hi: "थ", layer: 2, cell_num: 69, metadata: {} },
  "2,5": { col: 2, row: 5, category: "akshara", key: "akshara_da", display_name_en: "da", display_name_hi: "द", layer: 2, cell_num: 68, metadata: {} },
  "2,4": { col: 2, row: 4, category: "akshara", key: "akshara_dha", display_name_en: "dha", display_name_hi: "ध", layer: 2, cell_num: 67, metadata: {} },
  "2,3": { col: 2, row: 3, category: "akshara", key: "akshara_na", display_name_en: "na", display_name_hi: "न", layer: 2, cell_num: 66, metadata: {} },

  // ── Ring 3 (5x5 Border): 4 Swaras (Corners) + 12 Rashis (3 per side) ────
  "3,3": { col: 3, row: 3, category: "swara", key: "swara_lri", display_name_en: "ऌ", display_name_hi: "ऌ", layer: 3, cell_num: 57, metadata: { corner: "NW" } },
  "4,3": { col: 4, row: 3, category: "rashi", key: "rashi_makara", display_name_en: "Makara", display_name_hi: "मकर", layer: 3, cell_num: 48, metadata: { rashi_code: "capricorn", symbol: "♑" } },
  "5,3": { col: 5, row: 3, category: "rashi", key: "rashi_kumbha", display_name_en: "Kumbha", display_name_hi: "कुम्भ", layer: 3, cell_num: 39, metadata: { rashi_code: "aquarius", symbol: "♒" } },
  "6,3": { col: 6, row: 3, category: "rashi", key: "rashi_meena", display_name_en: "Meena", display_name_hi: "मीन", layer: 3, cell_num: 30, metadata: { rashi_code: "pisces", symbol: "♓" } },
  "7,3": { col: 7, row: 3, category: "swara", key: "swara_lrii", display_name_en: "ॡ", display_name_hi: "ॡ", layer: 3, cell_num: 21, metadata: { corner: "NE" } },

  "7,4": { col: 7, row: 4, category: "rashi", key: "rashi_mesha", display_name_en: "Mesha", display_name_hi: "मेष", layer: 3, cell_num: 22, metadata: { rashi_code: "aries", symbol: "♈" } },
  "7,5": { col: 7, row: 5, category: "rashi", key: "rashi_vrishabha", display_name_en: "Vrishabha", display_name_hi: "वृषभ", layer: 3, cell_num: 23, metadata: { rashi_code: "taurus", symbol: "♉" } },
  "7,6": { col: 7, row: 6, category: "rashi", key: "rashi_mithuna", display_name_en: "Mithuna", display_name_hi: "मिथुन", layer: 3, cell_num: 24, metadata: { rashi_code: "gemini", symbol: "♊" } },
  "7,7": { col: 7, row: 7, category: "swara", key: "swara_e", display_name_en: "e", display_name_hi: "ए", layer: 3, cell_num: 25, metadata: { corner: "SE" } },

  "6,7": { col: 6, row: 7, category: "rashi", key: "rashi_karka", display_name_en: "Karka", display_name_hi: "कर्क", layer: 3, cell_num: 34, metadata: { rashi_code: "cancer", symbol: "♋" } },
  "5,7": { col: 5, row: 7, category: "rashi", key: "rashi_simha", display_name_en: "Simha", display_name_hi: "सिंह", layer: 3, cell_num: 43, metadata: { rashi_code: "leo", symbol: "♌" } },
  "4,7": { col: 4, row: 7, category: "rashi", key: "rashi_kanya", display_name_en: "Kanya", display_name_hi: "कन्या", layer: 3, cell_num: 52, metadata: { rashi_code: "virgo", symbol: "♍" } },
  "3,7": { col: 3, row: 7, category: "swara", key: "swara_ai", display_name_en: "ai", display_name_hi: "ऐ", layer: 3, cell_num: 61, metadata: { corner: "SW" } },

  "3,6": { col: 3, row: 6, category: "rashi", key: "rashi_tula", display_name_en: "Tula", display_name_hi: "तुला", layer: 3, cell_num: 60, metadata: { rashi_code: "libra", symbol: "♎" } },
  "3,5": { col: 3, row: 5, category: "rashi", key: "rashi_vrishchika", display_name_en: "Vrishchika", display_name_hi: "वृश्चिक", layer: 3, cell_num: 59, metadata: { rashi_code: "scorpio", symbol: "♏" } },
  "3,4": { col: 3, row: 4, category: "rashi", key: "rashi_dhanu", display_name_en: "Dhanu", display_name_hi: "धनु", layer: 3, cell_num: 58, metadata: { rashi_code: "sagittarius", symbol: "♐" } },

  // ── Ring 4 & Center: 4 Swaras (Corners) + 5 Tithis (with 7 Vara Overlay) ──
  "4,4": { col: 4, row: 4, category: "swara", key: "swara_o", display_name_en: "o", display_name_hi: "ओ", layer: 4, cell_num: 49, metadata: { corner: "NW" } },
  "5,4": { col: 5, row: 4, category: "tithi", key: "tithi_nanda", display_name_en: "Nanda", display_name_hi: "नन्दा", layer: 4, cell_num: 40, metadata: { tithi_group: "nanda", tithis: "1, 6, 11", vara_overlay: ["Sun", "Mars"], vara_hi: "सूर्य / मंगल" } },
  "6,4": { col: 6, row: 4, category: "swara", key: "swara_au", display_name_en: "au", display_name_hi: "औ", layer: 4, cell_num: 31, metadata: { corner: "NE" } },

  "6,5": { col: 6, row: 5, category: "tithi", key: "tithi_bhadra", display_name_en: "Bhadra", display_name_hi: "भद्रा", layer: 4, cell_num: 32, metadata: { tithi_group: "bhadra", tithis: "2, 7, 12", vara_overlay: ["Moon", "Mercury"], vara_hi: "चन्द्र / बुध" } },
  "6,6": { col: 6, row: 6, category: "swara", key: "swara_am", display_name_en: "aṃ", display_name_hi: "अं", layer: 4, cell_num: 33, metadata: { corner: "SE" } },

  "5,6": { col: 5, row: 6, category: "tithi", key: "tithi_jaya", display_name_en: "Jaya", display_name_hi: "जया", layer: 4, cell_num: 42, metadata: { tithi_group: "jaya", tithis: "3, 8, 13", vara_overlay: ["Jupiter"], vara_hi: "गुरु" } },
  "4,6": { col: 4, row: 6, category: "swara", key: "swara_ah", display_name_en: "aḥ", display_name_hi: "अः", layer: 4, cell_num: 51, metadata: { corner: "SW" } },

  "4,5": { col: 4, row: 5, category: "tithi", key: "tithi_rikta", display_name_en: "Rikta", display_name_hi: "रिक्ता", layer: 4, cell_num: 50, metadata: { tithi_group: "rikta", tithis: "4, 9, 14", vara_overlay: ["Saturn"], vara_hi: "शनि" } },

  // ── Ring 5 (Center Core 1x1): Purna Tithi / Janma Focal Point ───────────
  "5,5": { col: 5, row: 5, category: "tithi", key: "tithi_purna", display_name_en: "Purna / Center", display_name_hi: "पूर्णा / केन्द्र", layer: 5, cell_num: 41, metadata: { tithi_group: "purna", tithis: "5, 10, 15/30", vara_overlay: ["Venus"], vara_hi: "शुक्र", is_center: true } },
};

// Backward compatibility map: cell_num -> SBCCellSemantic
export const SBC_81_CELLS: Record<number, SBCCellSemantic> = Object.fromEntries(
  Object.values(SBC_81_CANONICAL).map((cell) => [cell.cell_num, cell])
);


