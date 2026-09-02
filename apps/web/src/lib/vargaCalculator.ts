/**
 * vargaCalculator.ts — Complete Shodashavarga (16 Vargas) Mathematical & Dignity Engine
 */

export interface VargaPlacement {
  planet: string;
  glyph: string;
  rashiNumber: number; // 1 = Aries, 12 = Pisces
  rashiName: string;
  rashiDeg: number;
  houseNumber: number; // 1 to 12
  dignity: string;
  score: number; // 0..20 scale
  status: "Exalted" | "Moolatrikona" | "Own Sign" | "Strong" | "Supportive" | "Moderate" | "Weak" | "Debilitated";
  color: string;
  textCol: string;
  isRetro?: boolean;
}

export interface VargaChartData {
  vargaCode: string;
  vargaName: string;
  domain: string;
  weight: number;
  ascendantRashi: number;
  ascendantName: string;
  centerRashis: {
    h1: number;
    h4: number;
    h7: number;
    h10: number;
  };
  houses: Record<number, { rashiNumber: number; planets: VargaPlacement[] }>;
  indicators: {
    ascendant: string;
    lord: string;
    tenthHouse: string;
    ak: string;
    weight: number;
    activation: string;
  };
  signalMetrics: { label: string; score: number; max: number }[];
  potentialScore: number;
  vimshopakaPlanets: VargaPlacement[];
}

export const RASHI_NAMES = [
  "Aries", "Taurus", "Gemini", "Cancer",
  "Leo", "Virgo", "Libra", "Scorpio",
  "Sagittarius", "Capricorn", "Aquarius", "Pisces"
];

export const RASHI_LORDS = [
  "Mars", "Venus", "Mercury", "Moon",
  "Sun", "Mercury", "Venus", "Mars",
  "Jupiter", "Saturn", "Saturn", "Jupiter"
];

// Natural planetary dignity definitions
const EXALTATION_SIGNS: Record<string, number> = {
  Sun: 1, Moon: 2, Mars: 10, Mercury: 6, Jupiter: 4, Venus: 12, Saturn: 7, Rahu: 2, Ketu: 8
};
const DEBILITATION_SIGNS: Record<string, number> = {
  Sun: 7, Moon: 8, Mars: 4, Mercury: 12, Jupiter: 10, Venus: 6, Saturn: 1, Rahu: 8, Ketu: 2
};
const OWN_SIGNS: Record<string, number[]> = {
  Sun: [5], Moon: [4], Mars: [1, 8], Mercury: [3, 6], Jupiter: [9, 12], Venus: [2, 7], Saturn: [10, 11], Rahu: [11], Ketu: [8]
};
const FRIEND_SIGNS: Record<string, number[]> = {
  Sun: [1, 4, 8, 9, 12],
  Moon: [1, 3, 5, 6],
  Mars: [4, 5, 9, 12],
  Mercury: [2, 5, 7],
  Jupiter: [1, 4, 5, 8],
  Venus: [3, 6, 10, 11],
  Saturn: [2, 3, 6, 7],
  Rahu: [2, 3, 6, 7],
  Ketu: [1, 4, 5, 9, 12]
};

export function getPlanetDignity(planet: string, sign: number): { dignity: string; score: number; status: VargaPlacement["status"]; color: string; textCol: string } {
  if (EXALTATION_SIGNS[planet] === sign) {
    return { dignity: "Exalted (Uchcha)", score: 20.0, status: "Exalted", color: "bg-emerald-400", textCol: "text-emerald-400 font-bold" };
  }
  if (DEBILITATION_SIGNS[planet] === sign) {
    return { dignity: "Debilitated (Neecha)", score: 5.0, status: "Debilitated", color: "bg-rose-600", textCol: "text-rose-400 font-bold" };
  }
  if (OWN_SIGNS[planet]?.includes(sign)) {
    return { dignity: "Own Sign (Swakshetra)", score: 18.0, status: "Own Sign", color: "bg-teal-400", textCol: "text-teal-300 font-bold" };
  }
  if (FRIEND_SIGNS[planet]?.includes(sign)) {
    return { dignity: "Friend (Mitra)", score: 15.0, status: "Strong", color: "bg-cyan-400", textCol: "text-cyan-300 font-semibold" };
  }
  return { dignity: "Neutral (Sama)", score: 11.0, status: "Moderate", color: "bg-amber-400", textCol: "text-amber-300" };
}

// Base D1 Benchmark Longitudes
export const DEFAULT_D1_LONGITUDES: Record<string, { deg: number; glyph: string; isRetro?: boolean }> = {
  Asc: { deg: 311.2, glyph: "As" }, // 11°12' Aquarius (11)
  Sun: { deg: 74.1, glyph: "☉ Su" }, // 14°06' Gemini (3)
  Moon: { deg: 237.3, glyph: "☽ Mo" }, // 27°18' Scorpio (8)
  Mars: { deg: 340.4, glyph: "♂ Ma" }, // 10°24' Pisces (12)
  Mercury: { deg: 82.5, glyph: "☿ Me" }, // 22°30' Gemini (3)
  Jupiter: { deg: 259.8, glyph: "♃ Ju", isRetro: false }, // 19°48' Sagittarius (9)
  Venus: { deg: 38.9, glyph: "♀ Ve" }, // 8°54' Taurus (2)
  Saturn: { deg: 64.6, glyph: "♄ Sa", isRetro: true }, // 4°36' Gemini (3)
  Rahu: { deg: 318.2, glyph: "☊ Ra" }, // 18°12' Aquarius (11)
  Ketu: { deg: 138.2, glyph: "☋ Ke" }, // 18°12' Leo (5)
};

export const SHODASHAVARGA_LIST = [
  { code: "D1", name: "Rasi", domain: "Physical Body & General Vitality", weight: 3.5, metrics: ["Physical Vitality", "Life Force", "Stamina", "Immunity", "Core Resilience"] },
  { code: "D2", name: "Hora", domain: "Wealth & Family Assets", weight: 1.0, metrics: ["Liquid Wealth", "Cashflow", "Family Prosperity", "Speech Eloquence", "Savings Retention"] },
  { code: "D3", name: "Drekkana", domain: "Courage & Siblings", weight: 1.0, metrics: ["Courage & Boldness", "Siblings Harmony", "Media & Writing", "Self-Initiative", "Manual Dexterity"] },
  { code: "D4", name: "Chaturthamsha", domain: "Real Estate & Home", weight: 0.5, metrics: ["Real Estate Assets", "Fixed Property", "Conveyances", "Domestic Peace", "Homeland Stability"] },
  { code: "D7", name: "Saptamsha", domain: "Children & Lineage", weight: 0.5, metrics: ["Progeny Lineage", "Creative Genius", "Child Well-being", "Karmic Continuation", "Mentorship Output"] },
  { code: "D9", name: "Navamsha", domain: "Dharma, Soul & Marriage", weight: 3.0, metrics: ["Dharma Fulfillment", "Soul Evolution", "Marriage Harmony", "Inner Fortitude", "Bhagya Manifestation"] },
  { code: "D10", name: "Dashamsha", domain: "Career & Authority", weight: 0.5, metrics: ["Leadership", "Authority", "Public Influence", "Stability", "Growth Potential"] },
  { code: "D12", name: "Dwadashamsha", domain: "Parents & Lineage", weight: 0.5, metrics: ["Ancestral Karma", "Lineage Blessing", "Father's Legacy", "Mother's Lineage", "Heritage Protection"] },
  { code: "D16", name: "Shodashamsha", domain: "Vehicles & Luxuries", weight: 2.0, metrics: ["Vehicle Safety", "Worldly Comforts", "Aesthetic Pleasures", "Emotional Joy", "Luxury Acquisition"] },
  { code: "D20", name: "Vimshamsha", domain: "Spiritual Sadhana", weight: 0.5, metrics: ["Sadhana Discipline", "Meditation Purity", "Mantric Power", "Devotional Strength", "Inner Peace"] },
  { code: "D24", name: "Siddhamsha", domain: "Higher Learning & Intellect", weight: 0.5, metrics: ["Academic Excellence", "Intellectual Acumen", "Research Aptitude", "Philosophical Wisdom", "Analytical Power"] },
  { code: "D27", name: "Nakshatramsha", domain: "Strengths & Immunity", weight: 0.5, metrics: ["Physical Immunity", "Energetic Reserves", "Subconscious Stamina", "Vitality Balance", "Vulnerability Shield"] },
  { code: "D30", name: "Trimshamsha", domain: "Misfortunes & Debts", weight: 1.0, metrics: ["Adversity Resistance", "Debt Cleansing", "Karmic Protection", "Enemy Resilience", "Shadow Transmutation"] },
  { code: "D40", name: "Khavedamsha", domain: "Auspicious Blessings", weight: 0.5, metrics: ["Auspicious Karma", "Divine Grace", "Serendipity", "Karmic Blessings", "Spiritual Merit"] },
  { code: "D45", name: "Akshavedamsha", domain: "Micro-character", weight: 0.5, metrics: ["Moral Character", "Ethical Discipline", "Personal Integrity", "Virtuous Disposition", "Dharma Alignment"] },
  { code: "D60", name: "Shashtiamsha", domain: "Past-Life Prarabdha", weight: 4.0, metrics: ["Prarabdha Resolution", "Past-Life Merit", "Karmic Root Cleansing", "Supreme Destiny", "Soul Integration"] },
];

export function calculateVargaSign(longDeg: number, vargaCode: string): { sign: number; remDeg: number } {
  const normDeg = ((longDeg % 360) + 360) % 360;
  const d1Sign = Math.floor(normDeg / 30) + 1; // 1..12
  const degInSign = normDeg % 30; // 0..30
  const isOdd = d1Sign % 2 === 1;

  let targetSign = d1Sign;
  let partDeg = degInSign;

  switch (vargaCode.toUpperCase()) {
    case "D1":
      targetSign = d1Sign;
      partDeg = degInSign;
      break;
    case "D2": {
      const horaIndex = Math.floor(degInSign / 15);
      targetSign = isOdd ? (horaIndex === 0 ? 5 : 4) : (horaIndex === 0 ? 4 : 5);
      partDeg = (degInSign % 15) * 2;
      break;
    }
    case "D3": {
      const dIndex = Math.floor(degInSign / 10);
      targetSign = ((d1Sign - 1 + dIndex * 4) % 12) + 1;
      partDeg = (degInSign % 10) * 3;
      break;
    }
    case "D4": {
      const cIndex = Math.floor(degInSign / 7.5);
      targetSign = ((d1Sign - 1 + cIndex * 3) % 12) + 1;
      partDeg = (degInSign % 7.5) * 4;
      break;
    }
    case "D7": {
      const sIndex = Math.floor(degInSign / (30 / 7));
      const startSign = isOdd ? d1Sign : ((d1Sign + 5) % 12) + 1;
      targetSign = ((startSign - 1 + sIndex) % 12) + 1;
      partDeg = (degInSign % (30 / 7)) * 7;
      break;
    }
    case "D9": {
      const nIndex = Math.floor(degInSign / (30 / 9));
      let startSign = 1;
      if ([1, 5, 9].includes(d1Sign)) startSign = 1;
      else if ([2, 6, 10].includes(d1Sign)) startSign = 10;
      else if ([3, 7, 11].includes(d1Sign)) startSign = 7;
      else startSign = 4;
      targetSign = ((startSign - 1 + nIndex) % 12) + 1;
      partDeg = (degInSign % (30 / 9)) * 9;
      break;
    }
    case "D10": {
      const d10Index = Math.floor(degInSign / 3);
      const startSign = isOdd ? d1Sign : ((d1Sign + 7) % 12) + 1;
      targetSign = ((startSign - 1 + d10Index) % 12) + 1;
      partDeg = (degInSign % 3) * 10;
      break;
    }
    case "D12": {
      const d12Index = Math.floor(degInSign / 2.5);
      targetSign = ((d1Sign - 1 + d12Index) % 12) + 1;
      partDeg = (degInSign % 2.5) * 12;
      break;
    }
    case "D16": {
      const s16Index = Math.floor(degInSign / (30 / 16));
      let startSign = 1;
      if ([1, 4, 7, 10].includes(d1Sign)) startSign = 1;
      else if ([2, 5, 8, 11].includes(d1Sign)) startSign = 5;
      else startSign = 9;
      targetSign = ((startSign - 1 + s16Index) % 12) + 1;
      partDeg = (degInSign % (30 / 16)) * 16;
      break;
    }
    case "D20": {
      const v20Index = Math.floor(degInSign / 1.5);
      let startSign = 1;
      if ([1, 4, 7, 10].includes(d1Sign)) startSign = 1;
      else if ([2, 5, 8, 11].includes(d1Sign)) startSign = 9;
      else startSign = 5;
      targetSign = ((startSign - 1 + v20Index) % 12) + 1;
      partDeg = (degInSign % 1.5) * 20;
      break;
    }
    case "D24": {
      const s24Index = Math.floor(degInSign / 1.25);
      const startSign = isOdd ? 5 : 4;
      targetSign = ((startSign - 1 + s24Index) % 12) + 1;
      partDeg = (degInSign % 1.25) * 24;
      break;
    }
    case "D27": {
      const n27Index = Math.floor(degInSign / (30 / 27));
      let startSign = 1;
      if ([1, 5, 9].includes(d1Sign)) startSign = 1;
      else if ([2, 6, 10].includes(d1Sign)) startSign = 4;
      else if ([3, 7, 11].includes(d1Sign)) startSign = 7;
      else startSign = 10;
      targetSign = ((startSign - 1 + n27Index) % 12) + 1;
      partDeg = (degInSign % (30 / 27)) * 27;
      break;
    }
    case "D30": {
      if (isOdd) {
        if (degInSign < 5) targetSign = 1;
        else if (degInSign < 10) targetSign = 11;
        else if (degInSign < 18) targetSign = 9;
        else if (degInSign < 25) targetSign = 3;
        else targetSign = 7;
      } else {
        if (degInSign < 5) targetSign = 2;
        else if (degInSign < 12) targetSign = 6;
        else if (degInSign < 20) targetSign = 12;
        else if (degInSign < 25) targetSign = 10;
        else targetSign = 8;
      }
      partDeg = degInSign;
      break;
    }
    case "D40": {
      const s40Index = Math.floor(degInSign / (30 / 40));
      const startSign = isOdd ? 1 : 7;
      targetSign = ((startSign - 1 + s40Index) % 12) + 1;
      partDeg = (degInSign % (30 / 40)) * 40;
      break;
    }
    case "D45": {
      const s45Index = Math.floor(degInSign / (30 / 45));
      let startSign = 1;
      if ([1, 4, 7, 10].includes(d1Sign)) startSign = 1;
      else if ([2, 5, 8, 11].includes(d1Sign)) startSign = 5;
      else startSign = 9;
      targetSign = ((startSign - 1 + s45Index) % 12) + 1;
      partDeg = (degInSign % (30 / 45)) * 45;
      break;
    }
    case "D60": {
      const d60Index = Math.floor(degInSign / 0.5);
      targetSign = ((d1Sign - 1 + d60Index) % 12) + 1;
      partDeg = (degInSign % 0.5) * 60;
      break;
    }
    default:
      targetSign = d1Sign;
      partDeg = degInSign;
  }

  return { sign: targetSign, remDeg: partDeg };
}

export function generateVargaChart(
  vargaCode: string,
  longitudes: Record<string, { deg: number; glyph: string; isRetro?: boolean }> = DEFAULT_D1_LONGITUDES
): VargaChartData {
  const vInfo = SHODASHAVARGA_LIST.find((v) => v.code === vargaCode) || SHODASHAVARGA_LIST[6];
  const ascInfo = calculateVargaSign(longitudes.Asc?.deg ?? 311.2, vargaCode);
  const ascRashi = ascInfo.sign;

  const houses: Record<number, { rashiNumber: number; planets: VargaPlacement[] }> = {};
  for (let h = 1; h <= 12; h++) {
    const rashiNum = ((ascRashi - 1 + (h - 1)) % 12) + 1;
    houses[h] = { rashiNumber: rashiNum, planets: [] };
  }

  const vimshopakaPlanets: VargaPlacement[] = [];
  let totalScore = 0;

  for (const [planetName, pData] of Object.entries(longitudes)) {
    if (planetName === "Asc") continue;
    const { sign, remDeg } = calculateVargaSign(pData.deg, vargaCode);
    const houseNum = ((sign - ascRashi + 12) % 12) + 1;
    const dignityInfo = getPlanetDignity(planetName, sign);

    const placement: VargaPlacement = {
      planet: planetName,
      glyph: pData.glyph,
      rashiNumber: sign,
      rashiName: RASHI_NAMES[sign - 1],
      rashiDeg: remDeg,
      houseNumber: houseNum,
      dignity: dignityInfo.dignity,
      score: dignityInfo.score,
      status: dignityInfo.status,
      color: dignityInfo.color,
      textCol: dignityInfo.textCol,
      isRetro: pData.isRetro,
    };

    houses[houseNum].planets.push(placement);
    vimshopakaPlanets.push(placement);
    totalScore += dignityInfo.score;
  }

  const avgScore = totalScore / vimshopakaPlanets.length;
  const potentialScore = Math.min(96, Math.max(58, Math.round((avgScore / 20) * 100)));

  const centerRashis = {
    h1: houses[1].rashiNumber,
    h4: houses[4].rashiNumber,
    h7: houses[7].rashiNumber,
    h10: houses[10].rashiNumber,
  };

  const tenthRashi = houses[10].rashiNumber;

  // Dynamic Signal Metrics
  const signalMetrics = vInfo.metrics.map((label, idx) => {
    const baseVal = 14 + ((avgScore + idx * 1.5) % 5.5);
    return {
      label,
      score: Math.min(19.5, Math.max(12.0, parseFloat(baseVal.toFixed(1)))),
      max: 20,
    };
  });

  return {
    vargaCode: vInfo.code,
    vargaName: vInfo.name,
    domain: vInfo.domain,
    weight: vInfo.weight,
    ascendantRashi: ascRashi,
    ascendantName: RASHI_NAMES[ascRashi - 1],
    centerRashis,
    houses,
    indicators: {
      ascendant: `${RASHI_NAMES[ascRashi - 1]} (${ascRashi})`,
      lord: RASHI_LORDS[ascRashi - 1],
      tenthHouse: `${RASHI_NAMES[tenthRashi - 1]} (${tenthRashi})`,
      ak: "Saturn (Strong)",
      weight: vInfo.weight,
      activation: potentialScore >= 75 ? "High" : "Moderate",
    },
    signalMetrics,
    potentialScore,
    vimshopakaPlanets,
  };
}
