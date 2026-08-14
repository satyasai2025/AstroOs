/**
 * AstroOS — Master Alignment Matrix & Astrological Configuration Enforcement
 *
 * Implements strict validation rules for Ayanamsa + House System + Dasha System
 * combinations based on classical astrological theory and practical conventions.
 *
 * ## Critical Configuration Rules:
 * 1. Jaimini (Narayana, Chara) & Kalachakra: Must use Whole Sign + Vedic Ayanamsa (Lahiri/True Chitra)
 * 2. Koch / Placidus: Prioritize Secondary Progressions and time-based movements over sign-based dashas
 * 3. KP: Locked to Placidus + Vimshottari
 * 4. Yukteshwar: Locked to Whole Sign + Vimshottari
 * 5. Fagan-Bradley: Restricted to quadrant houses + Vimshottari (experimental)
 *
 * @module chart-alignment
 */

import type { AyanamsaCode, HouseSystemCode, DashaSystemCode } from "./types";

// ── Option Definitions ────────────────────────────────────────────────────────

export const AYANAMSA_OPTIONS: { value: AyanamsaCode; label: string }[] = [
  { value: "lahiri", label: "Lahiri" },
  { value: "true_chitra", label: "True Chitra" },
  { value: "raman", label: "Raman" },
  { value: "yukteshwar", label: "Yukteshwar" },
  { value: "kp", label: "KP" },
  { value: "fagan_bradley", label: "Fagan-Bradley" },
];

export const HOUSE_SYSTEM_OPTIONS: { value: HouseSystemCode; label: string }[] = [
  { value: "W", label: "Whole Sign" },
  { value: "P", label: "Placidus" },
  { value: "K", label: "Koch" },
  { value: "E", label: "Equal" },
];

export const DASHA_SYSTEM_OPTIONS: { value: DashaSystemCode; label: string }[] = [
  { value: "vimshottari", label: "Vimshottari" },
  { value: "yogini", label: "Yogini" },
  { value: "ashtottari", label: "Ashtottari" },
  { value: "kalachakra", label: "Kalachakra" },
  { value: "chara", label: "Chara (Jaimini)" },
  { value: "narayana", label: "Narayana (Jaimini)" },
];

// ── Master Alignment Matrix ───────────────────────────────────────────────────

/**
 * Defines which House Systems and Dasha Systems are compatible with each Ayanamsa.
 * Used for filtering dropdown options and auto-switching incompatible selections.
 */
const ALIGNMENT_MATRIX: Record<
  AyanamsaCode,
  {
    compatibleHouseSystems: HouseSystemCode[];
    compatibleDashaSystems: DashaSystemCode[];
    defaultHouseSystem: HouseSystemCode;
    defaultDashaSystem: DashaSystemCode;
  }
> = {
  lahiri: {
    compatibleHouseSystems: ["W", "E"],
    compatibleDashaSystems: ["vimshottari", "yogini", "ashtottari", "kalachakra"],
    defaultHouseSystem: "W",
    defaultDashaSystem: "vimshottari",
  },
  true_chitra: {
    compatibleHouseSystems: ["W", "E"],
    compatibleDashaSystems: ["vimshottari", "yogini", "ashtottari", "kalachakra", "chara", "narayana"],
    defaultHouseSystem: "W",
    defaultDashaSystem: "vimshottari",
  },
  // True Pushya paksha — same sidereal family as Lahiri/True Chitra, so it
  // carries the same house/dasha compatibility; only the ayanamsa value differs.
  true_pushya: {
    compatibleHouseSystems: ["W", "E"],
    compatibleDashaSystems: ["vimshottari", "yogini", "ashtottari", "kalachakra", "chara", "narayana"],
    defaultHouseSystem: "W",
    defaultDashaSystem: "vimshottari",
  },
  raman: {
    compatibleHouseSystems: ["W", "E"],
    compatibleDashaSystems: ["vimshottari", "yogini", "ashtottari"],
    defaultHouseSystem: "W",
    defaultDashaSystem: "vimshottari",
  },
  yukteshwar: {
    compatibleHouseSystems: ["W"],
    compatibleDashaSystems: ["vimshottari"],
    defaultHouseSystem: "W",
    defaultDashaSystem: "vimshottari",
  },
  kp: {
    compatibleHouseSystems: ["P"],
    compatibleDashaSystems: ["vimshottari"],
    defaultHouseSystem: "P",
    defaultDashaSystem: "vimshottari",
  },
  fagan_bradley: {
    compatibleHouseSystems: ["P", "K", "E"],
    compatibleDashaSystems: ["vimshottari"],
    defaultHouseSystem: "P",
    defaultDashaSystem: "vimshottari",
  },
};

/**
 * Sign-based dashas that require Whole Sign houses and Vedic ayanamsas.
 */
const SIGN_BASED_DASHAS: DashaSystemCode[] = ["chara", "narayana", "kalachakra"];

/**
 * Quadrant house systems that prioritize time-based methods over sign-based dashas.
 */
const QUADRANT_HOUSE_SYSTEMS: HouseSystemCode[] = ["P", "K"];

// ── Alert Banner Definitions ──────────────────────────────────────────────────

export type BannerSeverity = "lock" | "advisory" | "info";

export interface AlignmentBanner {
  field: "ayanamsa" | "houseSystem" | "dashaSystem" | "global";
  severity: BannerSeverity;
  message: string;
}

// ── Alignment Result Interface ────────────────────────────────────────────────

export interface AlignmentResult {
  /** Corrected/validated values after applying all rules */
  values: {
    ayanamsa: AyanamsaCode;
    houseSystem: HouseSystemCode;
    dashaSystem: DashaSystemCode;
  };
  /** Maps each option to a disabled reason (undefined = enabled) */
  disabled: {
    ayanamsa: Record<AyanamsaCode, string | undefined>;
    houseSystem: Record<HouseSystemCode, string | undefined>;
    dashaSystem: Record<DashaSystemCode, string | undefined>;
  };
  /** Contextual alert banners to display */
  banners: AlignmentBanner[];
}

// ── Core Alignment Resolution Function ────────────────────────────────────────

/**
 * Resolves astrological configuration alignment based on the Master Alignment Matrix.
 * Applies cascading rules in strict hierarchical order to prevent invalid combinations.
 *
 * **Evaluation Priority:**
 * 1. Dasha System Check (highest priority - sign-based dashas enforce strict constraints)
 * 2. Ayanamsa Check
 * 3. House System Check
 *
 * @param current - Current form state with ayanamsa, houseSystem, dashaSystem
 * @param changedField - Which field the user just changed (or 'init' for initial load)
 * @returns Validated configuration with corrected values, disabled options, and UI banners
 */
export function resolveAstrologicalAlignment(
  current: { ayanamsa: AyanamsaCode; houseSystem: HouseSystemCode; dashaSystem: DashaSystemCode },
  changedField: "ayanamsa" | "houseSystem" | "dashaSystem" | "init"
): AlignmentResult {
  let { ayanamsa, houseSystem, dashaSystem } = current;
  const banners: AlignmentBanner[] = [];

  // Initialize disabled maps (undefined = enabled)
  const disabledAyanamsa: Record<AyanamsaCode, string | undefined> = {
    lahiri: undefined,
    true_chitra: undefined,
    true_pushya: undefined,
    raman: undefined,
    yukteshwar: undefined,
    kp: undefined,
    fagan_bradley: undefined,
  };
  const disabledHouseSystem: Record<HouseSystemCode, string | undefined> = {
    W: undefined,
    P: undefined,
    K: undefined,
    E: undefined,
  };
  const disabledDashaSystem: Record<DashaSystemCode, string | undefined> = {
    vimshottari: undefined,
    yogini: undefined,
    ashtottari: undefined,
    kalachakra: undefined,
    chara: undefined,
    narayana: undefined,
  };

  // ── Priority 1: Dasha System Constraints (Highest) ──────────────────────────

  if (SIGN_BASED_DASHAS.includes(dashaSystem)) {
    // Force Whole Sign
    if (houseSystem !== "W") {
      houseSystem = "W";
    }

    // Lock to Whole Sign only
    disabledHouseSystem["P"] = "Requires Whole Sign for Jaimini/Kalachakra";
    disabledHouseSystem["K"] = "Requires Whole Sign for Jaimini/Kalachakra";
    disabledHouseSystem["E"] = "Requires Whole Sign for Jaimini/Kalachakra";

    // Force Vedic Ayanamsa (Lahiri or True Chitra)
    if (ayanamsa !== "lahiri" && ayanamsa !== "true_chitra") {
      ayanamsa = "true_chitra";
    }

    // Lock to Vedic ayanamsas only
    disabledAyanamsa["raman"] = "Jaimini/Kalachakra require Lahiri or True Chitra";
    disabledAyanamsa["yukteshwar"] = "Jaimini/Kalachakra require Lahiri or True Chitra";
    disabledAyanamsa["kp"] = "Jaimini/Kalachakra require Lahiri or True Chitra";
    disabledAyanamsa["fagan_bradley"] = "Jaimini/Kalachakra require Lahiri or True Chitra";

    banners.push({
      field: "dashaSystem",
      severity: "lock",
      message: "Locked to Whole Sign and Vedic Ayanamsa (Lahiri/True Chitra) for Jaimini & Kalachakra sign-based timing.",
    });
  }

  // ── Priority 2: Ayanamsa Constraints ─────────────────────────────────────────

  const matrix = ALIGNMENT_MATRIX[ayanamsa];

  // Auto-switch house/dasha if incompatible with current ayanamsa
  if (!matrix.compatibleHouseSystems.includes(houseSystem)) {
    houseSystem = matrix.defaultHouseSystem;
  }
  if (!matrix.compatibleDashaSystems.includes(dashaSystem)) {
    dashaSystem = matrix.defaultDashaSystem;
  }

  // Disable incompatible house systems
  HOUSE_SYSTEM_OPTIONS.forEach((opt) => {
    if (!matrix.compatibleHouseSystems.includes(opt.value)) {
      disabledHouseSystem[opt.value] = `Incompatible with ${AYANAMSA_OPTIONS.find((a) => a.value === ayanamsa)?.label}`;
    }
  });

  // Disable incompatible dasha systems
  DASHA_SYSTEM_OPTIONS.forEach((opt) => {
    if (!matrix.compatibleDashaSystems.includes(opt.value)) {
      disabledDashaSystem[opt.value] = `Incompatible with ${AYANAMSA_OPTIONS.find((a) => a.value === ayanamsa)?.label}`;
    }
  });

  // Specific ayanamsa rules and banners
  if (ayanamsa === "kp") {
    banners.push({
      field: "ayanamsa",
      severity: "lock",
      message: "KP practice explicitly requires KP Ayanamsa + Placidus houses, coupled with Vimshottari timing.",
    });
  } else if (ayanamsa === "yukteshwar") {
    banners.push({
      field: "ayanamsa",
      severity: "info",
      message: "Sri Yukteshwar ayanamsa is conventionally paired with Whole Sign (Rashi) houses and Vimshottari dasha.",
    });
  } else if (ayanamsa === "fagan_bradley") {
    banners.push({
      field: "ayanamsa",
      severity: "advisory",
      message: "Western Sidereal / Huber systems prioritize Secondary Progressions & Transits over sign-based dashas when using quadrant houses.",
    });
  }

  // ── Priority 3: House System Constraints ─────────────────────────────────────

  if (QUADRANT_HOUSE_SYSTEMS.includes(houseSystem)) {
    // Disable sign-based dashas for quadrant systems
    SIGN_BASED_DASHAS.forEach((dasha) => {
      disabledDashaSystem[dasha] = "Incompatible with quadrant houses (use Whole Sign)";
    });

    // If user was using a sign-based dasha, auto-switch to Vimshottari
    if (SIGN_BASED_DASHAS.includes(dashaSystem)) {
      dashaSystem = "vimshottari";
    }

    // Show advisory banner about quadrant systems
    if (!banners.some((b) => b.field === "ayanamsa" && b.severity === "advisory")) {
      banners.push({
        field: "houseSystem",
        severity: "advisory",
        message: "Unequal quadrant systems (Koch / Placidus) focus on temporal transits and progressions over sign-based dashas.",
      });
    }
  }

  return {
    values: {
      ayanamsa,
      houseSystem,
      dashaSystem,
    },
    disabled: {
      ayanamsa: disabledAyanamsa,
      houseSystem: disabledHouseSystem,
      dashaSystem: disabledDashaSystem,
    },
    banners,
  };
}
