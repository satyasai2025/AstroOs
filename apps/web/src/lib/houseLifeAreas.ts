/**
 * AstroOS — House Dependency Network: static house → life-area mapping
 *
 * Classical/conventional Vedic house-signification knowledge, fixed content
 * (not computed per-chart), used to render the "1st House → Body → Health →
 * Confidence → Career → Marriage → Children → Finance → Spirituality"
 * cascade from ASTROOS_VISION_V3_ROADMAP.md (Phase 4).
 *
 * The cascade is a defensible linear simplification of house significations
 * for presentation purposes — a real chart has many cross-house dependencies,
 * but the vision doc explicitly asks for a simple ~8-9 node cascade, so each
 * life-area step below is anchored to the single house most conventionally
 * associated with it in classical house-signification lists (BPHS-style):
 *
 *   1st house  → Body        (Tanu Bhava — the physical body/self, root of the chain)
 *   6th house  → Health      (Roga Bhava — disease, injury, daily struggle)
 *   5th house  → Confidence  (Purva Punya/intelligence, self-expression, creativity)
 *   10th house → Career      (Karma Bhava — profession, public standing)
 *   7th house  → Marriage    (Kalatra Bhava — partnerships, spouse)
 *   5th house  → Children    (Putra Bhava — progeny; 5th is reused deliberately,
 *                             it classically governs both confidence/intellect
 *                             and children — the vision doc itself lists 5th
 *                             for both "confidence-ish" and "children")
 *   2nd house  → Finance     (Dhana Bhava — accumulated wealth, family resources)
 *   9th house  → Spirituality (Dharma Bhava — higher purpose, fortune, guru;
 *                              paired classically with the 12th for moksha, but
 *                              9th is used as the single representative house
 *                              here to keep the cascade to one house per node)
 */

export interface HouseLifeAreaNode {
  /** Stable identifier for the node (used as React key). */
  id: string;
  /** Life-area label shown in the cascade. */
  label: string;
  /** The Vedic house number (1-12) this node's strength is derived from. */
  houseNumber: number;
  /** Short classical name for the house, shown as a subtitle. */
  houseName: string;
  /** One-line rationale for why this house maps to this life area. */
  description: string;
}

/**
 * The fixed, linear cascade rendered by HouseDependencyNetwork, in display
 * order. The 1st house is the root; if it is weak, the whole downstream
 * chain is tinted red (per the vision doc's "cascading red-highlight").
 */
export const HOUSE_LIFE_AREA_CASCADE: HouseLifeAreaNode[] = [
  {
    id: "body",
    label: "Body",
    houseNumber: 1,
    houseName: "Tanu Bhava (1st)",
    description: "The physical self and root of the cascade — the Ascendant house.",
  },
  {
    id: "health",
    label: "Health",
    houseNumber: 6,
    houseName: "Roga Bhava (6th)",
    description: "Disease, injury, and daily vitality struggles stem from the body.",
  },
  {
    id: "confidence",
    label: "Confidence",
    houseNumber: 5,
    houseName: "Purva Punya Bhava (5th)",
    description: "Self-expression, intellect, and inner confidence follow from health.",
  },
  {
    id: "career",
    label: "Career",
    houseNumber: 10,
    houseName: "Karma Bhava (10th)",
    description: "Professional standing and public achievement build on confidence.",
  },
  {
    id: "marriage",
    label: "Marriage",
    houseNumber: 7,
    houseName: "Kalatra Bhava (7th)",
    description: "Partnership and marital life are shaped by career stability.",
  },
  {
    id: "children",
    label: "Children",
    houseNumber: 5,
    houseName: "Putra Bhava (5th)",
    description: "Progeny and family growth classically follow from marriage.",
  },
  {
    id: "finance",
    label: "Finance",
    houseNumber: 2,
    houseName: "Dhana Bhava (2nd)",
    description: "Accumulated family wealth and resources support raising children.",
  },
  {
    id: "spirituality",
    label: "Spirituality",
    houseNumber: 9,
    houseName: "Dharma Bhava (9th)",
    description: "Higher purpose and fortune are the culmination of a settled material life.",
  },
];
