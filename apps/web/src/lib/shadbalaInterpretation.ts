/**
 * AstroOS — Downstream Shadbala Interpretation Layer
 *
 * Keeps calculation / evaluation purely canonical and mathematical.
 * This module consumes the canonical SaravaliPlanetSummary facts downstream
 * to generate classical Dasa & Transit interpretations and Auspiciousness ratings.
 */

import type { SaravaliPlanetSummary } from "./shadbala";

export interface PlanetInterpretation {
  auspiciousness: string;
  dashaInterpretation: string;
  transitImpact: string;
}

export function getShadbalaInterpretation(planet: SaravaliPlanetSummary): PlanetInterpretation {
  const pName = planet.planet_display_name;
  const pLower = planet.planet.toLowerCase();
  const ratio = planet.strength_ratio;
  const isStrong = planet.is_strong;
  const isBenefic = ["jupiter", "venus", "mercury", "moon"].includes(pLower);

  if (isStrong) {
    if (isBenefic) {
      return {
        auspiciousness: "Highly Auspicious",
        dashaInterpretation: `${pName} possesses full Shadbala strength (${ratio.toFixed(2)}× required threshold), conferring radiant fortune, intellectual clarity, harmony, and material/spiritual prosperity during its Dasha and Bhukti periods.`,
        transitImpact: `${pName}'s favorable transits will bear maximum positive fruit without obstruction.`,
      };
    } else {
      return {
        auspiciousness: "Powerful & Decisive",
        dashaInterpretation: `${pName} possesses robust structural power (${ratio.toFixed(2)}× required threshold). As a natural malefic, it provides the native with decisive authority, endurance, courage, and victory over adversaries, though requiring balanced expression.`,
        transitImpact: `${pName}'s strong transit aspects stimulate decisive breakthroughs and protective force.`,
      };
    }
  } else {
    if (isBenefic) {
      return {
        auspiciousness: "Subdued Benefic",
        dashaInterpretation: `${pName} is below the classical strength threshold (${ratio.toFixed(2)}× required threshold). Its natural benefic grace remains intact but may produce subdued results or require conscious effort and remedial balance during its operating periods.`,
        transitImpact: `Transits of ${pName} may require supportive yogas or benefic aspects to fully manifest.`,
      };
    } else {
      return {
        auspiciousness: "Requires Attention",
        dashaInterpretation: `${pName} is deficient in Shadbala (${ratio.toFixed(2)}× required threshold). During its Dasa periods, challenges, friction, or delays may surface, making patience, discipline, and remedial measures beneficial.`,
        transitImpact: `Challenging transits of ${pName} should be navigated with caution and preparation.`,
      };
    }
  }
}
