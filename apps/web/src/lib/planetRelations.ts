/**
 * AstroOS — Naisargika Maitri (natural planetary friendship) table
 *
 * Static classical data, not derived from a chart — same 3-category
 * (friend/neutral/enemy) table already used server-side in
 * apps/api/services/ashtakoota_engine.py's PLANET_FRIENDSHIP constant
 * for Ashtakoota's Graha Maitri koota. Kept in sync with that table's
 * values; ported here as a small static frontend dataset rather than
 * round-tripping to the backend for something that never changes.
 *
 * Scoped to the 7 classical planets only (Sun through Saturn) — Rahu
 * and Ketu have no settled Naisargika Maitri entry in classical texts
 * (the shadow planets' friendships are a separate, contested topic),
 * so they're intentionally omitted rather than given a fabricated row.
 */

export type ClassicalPlanet =
  | "sun"
  | "moon"
  | "mars"
  | "mercury"
  | "jupiter"
  | "venus"
  | "saturn";

export interface NaturalRelationship {
  friends: ClassicalPlanet[];
  neutral: ClassicalPlanet[];
  enemies: ClassicalPlanet[];
}

// 5 = Friend, 4 = Neutral, 0 = Enemy — mirrors PLANET_FRIENDSHIP exactly,
// self-relationship entries dropped (a planet has no relationship to itself).
const RAW_FRIENDSHIP: Record<ClassicalPlanet, Record<ClassicalPlanet, number>> = {
  sun: { sun: 5, moon: 5, mars: 5, mercury: 4, jupiter: 5, venus: 0, saturn: 0 },
  moon: { sun: 5, moon: 5, mars: 4, mercury: 5, jupiter: 4, venus: 4, saturn: 4 },
  mars: { sun: 5, moon: 5, mars: 5, mercury: 0, jupiter: 5, venus: 4, saturn: 4 },
  mercury: { sun: 5, moon: 0, mars: 4, mercury: 5, jupiter: 4, venus: 5, saturn: 4 },
  jupiter: { sun: 5, moon: 5, mars: 5, mercury: 0, jupiter: 5, venus: 0, saturn: 4 },
  venus: { sun: 0, moon: 0, mars: 4, mercury: 5, jupiter: 4, venus: 5, saturn: 5 },
  saturn: { sun: 0, moon: 0, mars: 0, mercury: 5, jupiter: 4, venus: 5, saturn: 5 },
};

export const CLASSICAL_PLANETS: ClassicalPlanet[] = [
  "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
];

/** Natural friend/neutral/enemy list for one classical planet, or null
 * if `planet` isn't one of the 7 (e.g. Rahu/Ketu, Ascendant). */
export function naturalRelationship(planet: string): NaturalRelationship | null {
  const key = planet.toLowerCase() as ClassicalPlanet;
  const row = RAW_FRIENDSHIP[key];
  if (!row) return null;

  const friends: ClassicalPlanet[] = [];
  const neutral: ClassicalPlanet[] = [];
  const enemies: ClassicalPlanet[] = [];

  for (const other of CLASSICAL_PLANETS) {
    if (other === key) continue;
    const score = row[other];
    if (score === 5) friends.push(other);
    else if (score === 4) neutral.push(other);
    else enemies.push(other);
  }

  return { friends, neutral, enemies };
}
