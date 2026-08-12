/**
 * AstroOS — North Indian chart house geometry.
 *
 * Shared between NorthIndianChart (single-ring) and MixedVargaTransitChart
 * (concentric dual-ring). See NorthIndianChart.tsx's original comment for
 * the full derivation: an outer square, both diagonals, and an inner
 * diamond connecting the midpoints of the four sides produce exactly 12
 * regions — a rhombus at each side's midpoint (houses 1/4/7/10, the
 * Kendras) and two triangles filling each corner (the rest). Coordinates
 * are worked out in a 0–100 unit square; house 1 is fixed at the top,
 * proceeding counter-clockwise per the standard North Indian convention.
 */

export const A: [number, number] = [0, 0]; // top-left
export const B: [number, number] = [100, 0]; // top-right
export const C: [number, number] = [100, 100]; // bottom-right
export const D: [number, number] = [0, 100]; // bottom-left
export const O: [number, number] = [50, 50]; // center
export const M_AB: [number, number] = [50, 0];
export const M_BC: [number, number] = [100, 50];
export const M_CD: [number, number] = [50, 100];
export const M_DA: [number, number] = [0, 50];
const MID_AO: [number, number] = [25, 25];
const MID_BO: [number, number] = [75, 25];
const MID_CO: [number, number] = [75, 75];
const MID_DO: [number, number] = [25, 75];

export const HOUSE_UNIT_POLYGONS: Record<number, [number, number][]> = {
  1: [M_AB, MID_BO, O, MID_AO],
  2: [A, MID_AO, M_AB],
  3: [A, M_DA, MID_AO],
  4: [M_DA, MID_AO, O, MID_DO],
  5: [D, MID_DO, M_DA],
  6: [D, M_CD, MID_DO],
  7: [M_CD, MID_DO, O, MID_CO],
  8: [C, MID_CO, M_CD],
  9: [C, M_BC, MID_CO],
  10: [M_BC, MID_CO, O, MID_BO],
  11: [B, M_BC, MID_BO],
  12: [B, MID_BO, M_AB],
};

export function centroid(points: [number, number][]): [number, number] {
  const n = points.length;
  const sum = points.reduce((acc, [x, y]) => [acc[0] + x, acc[1] + y], [0, 0]);
  return [sum[0] / n, sum[1] / n];
}

export const HOUSE_CENTROIDS: Record<number, [number, number]> = Object.fromEntries(
  Object.entries(HOUSE_UNIT_POLYGONS).map(([h, pts]) => [Number(h), centroid(pts)]),
);

/** Farthest vertex of a house's polygon from the chart center — the
 * outer corner/edge-midpoint that house actually touches. */
export function farthestVertexFromCenter(points: [number, number][]): [number, number] {
  return points.reduce((farthest, p) => {
    const d = (p[0] - O[0]) ** 2 + (p[1] - O[1]) ** 2;
    const df = (farthest[0] - O[0]) ** 2 + (farthest[1] - O[1]) ** 2;
    return d > df ? p : farthest;
  }, points[0]);
}

export function interpolatePoint(
  from: [number, number],
  to: [number, number],
  t: number,
): [number, number] {
  return [from[0] + (to[0] - from[0]) * t, from[1] + (to[1] - from[1]) * t];
}

export const HOUSE_NUMBER_UNIT_POS: Record<number, [number, number]> = Object.fromEntries(
  Object.entries(HOUSE_UNIT_POLYGONS).map(([h, pts]) => {
    const house = Number(h);
    const outer = farthestVertexFromCenter(pts);
    return [house, interpolatePoint(HOUSE_CENTROIDS[house], outer, 0.55)];
  }),
);

/** Scale a unit-square point toward/away from the center O — used to draw
 * a smaller (inner ring) or larger (outer ring) copy of the same 12-house
 * construction concentrically. scale=1 reproduces the original point. */
export function scaleFromCenter([x, y]: [number, number], scale: number): [number, number] {
  return [O[0] + (x - O[0]) * scale, O[1] + (y - O[1]) * scale];
}
