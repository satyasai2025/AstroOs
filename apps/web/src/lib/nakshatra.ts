/**
 * AstroOS — Nakshatra Core Engine
 *
 * Foundational calculation layer for the Nakshatra module. Implements the
 * domain model from the Nakshatra Architecture spec:
 *
 *   Nakshatra → Pada → Navamsha → Lord → Bhava → Dasha → Transit → Tara Bala
 *
 * All 27 nakshatras, 108 padas, 9 lords, deities, classifications, and
 * namaksharas are defined here as static reference data (BPHS-derived),
 * with pure calculation functions for position, tara bala, dasha, and
 * transit analysis.
 */

// ── Types ──────────────────────────────────────────────────────────────────────

export interface NakshatraPada {
  pada: number;
  start_degree: number;
  end_degree: number;
  navamsha: string;
  navamsha_lord: string;
}

export interface NakshatraClassification {
  tara_category: string;
  gana: string;
  yoni: string;
  nadi: string;
  deva_yama: string;
  tripadi: boolean;
  gandanta: boolean;
  varna: string;
  vashya: string;
  tatva: string;
  animal: string;
  symbol: string;
}

export interface NakshatraDef {
  id: number;
  sequence_number: number;
  name: string;
  sanskrit: string;
  devanagari: string;
  meaning: string;
  zodiac_start: number;
  zodiac_end: number;
  nakshatra_lord: string;
  yoga_tara: string;
  deity: string;
  deity_description: string;
  shakti: string;
  symbol: string;
  padas: NakshatraPada[];
  classifications: NakshatraClassification;
  namakshara: string[];
  karakatvas: string[];
  compatible: string[];
  incompatible: string[];
}

export interface PlanetNakshatraAnalysis {
  planet: string;
  longitude: number;
  rashi: string;
  rashi_degree: number;
  bhava: number;
  nakshatra: string;
  nakshatra_lord: string;
  yoga_tara: string;
  pada: number;
  pada_degree: number;
  navamsha: string;
  navamsha_lord: string;
  tara_bala: TaraBalaResult;
  gandanta: boolean;
  tripadi: boolean;
  dasha: {
    mahadasha: string;
    antardasha: string;
  };
  interpretation: string;
}

export interface TaraBalaResult {
  category: string;
  lord: string;
  favorable: boolean;
  description: string;
}

export interface DashaPeriod {
  lord: string;
  years: number;
  start_date: string;
  end_date: string;
  level: number;
  sub_periods: DashaPeriod[];
}

// ── Constants ──────────────────────────────────────────────────────────────────

export const NAKSHATRA_LORD_ORDER = [
  "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
];

export const VIMSHOTTARI_YEARS: Record<string, number> = {
  Ketu: 7,
  Venus: 20,
  Sun: 6,
  Moon: 10,
  Mars: 7,
  Rahu: 18,
  Jupiter: 16,
  Saturn: 19,
  Mercury: 17,
};

export const TARA_CATEGORIES = [
  "Janma", "Sampat", "Vipat", "Kshema", "Pratyari", "Sadhaka", "Naidhana", "Mitra", "Atimitra",
];

export const TARA_FAVORABLE: Record<string, boolean> = {
  Janma: true,
  Sampat: true,
  Vipat: false,
  Kshema: true,
  Pratyari: false,
  Sadhaka: true,
  Naidhana: false,
  Mitra: true,
  Atimitra: true,
};

export const TARA_DESCRIPTIONS: Record<string, string> = {
  Janma: "Birth star — foundational, self and identity",
  Sampat: "Wealth star — prosperity and resources",
  Vipat: "Danger star — obstacles and challenges",
  Kshema: "Comfort star — well-being and stability",
  Pratyari: "Enemy star — opposition and conflict",
  Sadhaka: "Achievement star — success and fulfillment",
  Naidhana: "Destruction star — endings and loss",
  Mitra: "Friend star — support and cooperation",
  Atimitra: "Best friend star — great fortune and harmony",
};

export const GANA_LABELS: Record<string, string> = {
  deva: "Deva (Divine)",
  manushya: "Manushya (Human)",
  rakshasa: "Rakshasa (Demonic)",
};

export const NADI_LABELS: Record<string, string> = {
  adi: "Adi (Vata)",
  madhya: "Madhya (Pitta)",
  antya: "Antya (Kapha)",
};

export const YONI_LABELS: Record<string, string> = {
  horse: "Horse (Ashwa)",
  elephant: "Elephant (Gaja)",
  sheep: "Sheep (Mesha)",
  serpent: "Serpent (Sarpa)",
  dog: "Dog (Shvana)",
  cat: "Cat (Marjara)",
  rat: "Rat (Mushika)",
  cow: "Cow (Go)",
  buffalo: "Buffalo (Mahisha)",
  tiger: "Tiger (Vyaghra)",
  deer: "Deer (Mriga)",
  monkey: "Monkey (Vanara)",
  mongoose: "Mongoose (Nakula)",
  lion: "Lion (Simha)",
};

export const RASHI_NAMES = [
  "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
  "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
];

export const RASHI_LORDS = [
  "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
  "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
];

export const NAVAMSHA_LORDS = [
  "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
  "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
];

export const PLANET_SYMBOLS: Record<string, string> = {
  Sun: "☉", Moon: "☽", Mars: "♂", Mercury: "☿", Jupiter: "♃",
  Venus: "♀", Saturn: "♄", Rahu: "☊", Ketu: "☋",
};

export const PLANET_KARAKATVAS: Record<string, string[]> = {
  Sun: ["Soul", "Father", "Authority", "Government", "Health", "Vitality", "Ego"],
  Moon: ["Mind", "Mother", "Emotions", "Public", "Comfort", "Fluids", "Nurturing"],
  Mars: ["Courage", "Siblings", "Land", "Energy", "Conflict", "Surgery", "Sports"],
  Mercury: ["Intellect", "Communication", "Business", "Education", "Speech", "Analysis"],
  Jupiter: ["Wisdom", "Wealth", "Children", "Guru", "Spirituality", "Expansion", "Fortune"],
  Venus: ["Marriage", "Love", "Luxury", "Art", "Beauty", "Vehicles", "Comforts"],
  Saturn: ["Career", "Discipline", "Longevity", "Delays", "Labor", "Old Age", "Structure"],
  Rahu: ["Obsession", "Foreign", "Illusion", "Ambition", "Technology", "Sudden Events"],
  Ketu: ["Detachment", "Spirituality", "Past Karma", "Isolation", "Moksha", "Intuition"],
};

// ── 27 Nakshatras Master Data ──────────────────────────────────────────────────

const PADA_DEG = 13.3333 / 4; // 3°20'

function buildPadas(start: number, navamshaStart: number): NakshatraPada[] {
  const padas: NakshatraPada[] = [];
  for (let i = 0; i < 4; i++) {
    const navamshaIdx = (navamshaStart + i) % 12;
    padas.push({
      pada: i + 1,
      start_degree: start + i * PADA_DEG,
      end_degree: start + (i + 1) * PADA_DEG,
      navamsha: RASHI_NAMES[navamshaIdx],
      navamsha_lord: NAVAMSHA_LORDS[navamshaIdx],
    });
  }
  return padas;
}

export const NAKSHATRAS: NakshatraDef[] = [
  {
    id: 1, sequence_number: 1, name: "Ashwini", sanskrit: "Ashvinī", devanagari: "अश्विनी",
    meaning: "The horsewomen; the winners", zodiac_start: 0, zodiac_end: 13.3333,
    nakshatra_lord: "Ketu", yoga_tara: "Ketu", deity: "Ashwini Kumaras",
    deity_description: "The divine twin physicians of the gods, swift riders who bring healing and rejuvenation",
    shakti: "The power to heal and bestow speed and swift recovery", symbol: "Horse's head",
    padas: buildPadas(0, 0),
    classifications: {
      tara_category: "Janma", gana: "deva", yoni: "horse", nadi: "adi",
      deva_yama: "Deva", tripadi: false, gandanta: true, varna: "Kshatriya",
      vashya: "Chatushpada", tatva: "Vayu", animal: "Horse", symbol: "Horse's head",
    },
    namakshara: ["Chu", "Che", "Cho", "Chaa"],
    karakatvas: ["Healing", "Speed", "New beginnings", "Pioneering", "Medicine"],
    compatible: ["Ashwini", "Mrigashira"], incompatible: [],
  },
  {
    id: 2, sequence_number: 2, name: "Bharani", sanskrit: "Bharanī", devanagari: "भरणी",
    meaning: "The bearer; the one who carries", zodiac_start: 13.3333, zodiac_end: 26.6667,
    nakshatra_lord: "Venus", yoga_tara: "Venus", deity: "Yama",
    deity_description: "The god of death and dharma, who judges souls and maintains cosmic order",
    shakti: "The power to cleanse and purify through transformation", symbol: "Yoni",
    padas: buildPadas(13.3333, 1),
    classifications: {
      tara_category: "Sampat", gana: "manushya", yoni: "elephant", nadi: "madhya",
      deva_yama: "Yama", tripadi: false, gandanta: true, varna: "Shudra",
      vashya: "Chatushpada", tatva: "Prithvi", animal: "Elephant", symbol: "Yoni",
    },
    namakshara: ["Lee", "Loo", "Le", "Lo"],
    karakatvas: ["Transformation", "Discipline", "Responsibility", "Fertility", "Justice"],
    compatible: ["Bharani", "Pushya"], incompatible: [],
  },
  {
    id: 3, sequence_number: 3, name: "Krittika", sanskrit: "Kṛttikā", devanagari: "कृत्तिका",
    meaning: "The cutters; the Pleiades", zodiac_start: 26.6667, zodiac_end: 40,
    nakshatra_lord: "Sun", yoga_tara: "Sun", deity: "Agni",
    deity_description: "The god of fire, who purifies and transforms all things",
    shakti: "The power to burn away impurities and illuminate", symbol: "Razor / Flame",
    padas: buildPadas(26.6667, 2),
    classifications: {
      tara_category: "Vipat", gana: "rakshasa", yoni: "sheep", nadi: "adi",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Brahmin",
      vashya: "Chatushpada", tatva: "Agni", animal: "Sheep", symbol: "Razor / Flame",
    },
    namakshara: ["Aa", "Ee", "Uu", "Ae"],
    karakatvas: ["Courage", "Leadership", "Purification", "Determination", "Fire"],
    compatible: ["Krittika", "Uttara Phalguni"], incompatible: [],
  },
  {
    id: 4, sequence_number: 4, name: "Rohini", sanskrit: "Rohiṇī", devanagari: "रोहिणी",
    meaning: "The red one; the rising", zodiac_start: 40, zodiac_end: 53.3333,
    nakshatra_lord: "Moon", yoga_tara: "Moon", deity: "Brahma",
    deity_description: "The creator god, who brings forth all forms of life",
    shakti: "The power of growth and creation", symbol: "Cart / Chariot",
    padas: buildPadas(40, 3),
    classifications: {
      tara_category: "Kshema", gana: "manushya", yoni: "serpent", nadi: "madhya",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Shudra",
      vashya: "Manava", tatva: "Prithvi", animal: "Serpent", symbol: "Cart / Chariot",
    },
    namakshara: ["O", "Va", "Vi", "Vu"],
    karakatvas: ["Creativity", "Beauty", "Growth", "Prosperity", "Nurturing"],
    compatible: ["Rohini", "Hasta"], incompatible: [],
  },
  {
    id: 5, sequence_number: 5, name: "Mrigashira", sanskrit: "Mṛgaśira", devanagari: "मृगशिरा",
    meaning: "The deer's head", zodiac_start: 53.3333, zodiac_end: 66.6667,
    nakshatra_lord: "Mars", yoga_tara: "Mars", deity: "Soma",
    deity_description: "The moon god, who nourishes all beings with his cooling rays",
    shakti: "The power to give fulfillment and contentment", symbol: "Deer's head",
    padas: buildPadas(53.3333, 4),
    classifications: {
      tara_category: "Pratyari", gana: "deva", yoni: "serpent", nadi: "antya",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Vaishya",
      vashya: "Vanachara", tatva: "Prithvi", animal: "Serpent", symbol: "Deer's head",
    },
    namakshara: ["Ve", "Vo", "Ka", "Ki"],
    karakatvas: ["Search", "Curiosity", "Gentleness", "Exploration", "Comfort"],
    compatible: ["Mrigashira", "Chitra"], incompatible: [],
  },
  {
    id: 6, sequence_number: 6, name: "Ardra", sanskrit: "Ārdrā", devanagari: "आर्द्रा",
    meaning: "The moist one; the teardrop", zodiac_start: 66.6667, zodiac_end: 80,
    nakshatra_lord: "Rahu", yoga_tara: "Rahu", deity: "Rudra",
    deity_description: "The storm god, who brings destruction and renewal through his fierce power",
    shakti: "The power to bring effort and achievement through struggle", symbol: "Teardrop",
    padas: buildPadas(66.6667, 5),
    classifications: {
      tara_category: "Sadhaka", gana: "manushya", yoni: "dog", nadi: "adi",
      deva_yama: "Yama", tripadi: false, gandanta: false, varna: "Shudra",
      vashya: "Chatushpada", tatva: "Jala", animal: "Dog", symbol: "Teardrop",
    },
    namakshara: ["Ku", "Gha", "Ng", "Chha"],
    karakatvas: ["Intensity", "Transformation", "Storms", "Research", "Deep emotions"],
    compatible: ["Ardra", "Swati"], incompatible: [],
  },
  {
    id: 7, sequence_number: 7, name: "Punarvasu", sanskrit: "Punarvasu", devanagari: "पुनर्वसु",
    meaning: "The return of light", zodiac_start: 80, zodiac_end: 93.3333,
    nakshatra_lord: "Jupiter", yoga_tara: "Jupiter", deity: "Aditi",
    deity_description: "The mother of the gods, infinite and boundless, giver of abundance",
    shakti: "The power to restore and renew", symbol: "Quiver of arrows",
    padas: buildPadas(80, 6),
    classifications: {
      tara_category: "Naidhana", gana: "deva", yoni: "cat", nadi: "madhya",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Vaishya",
      vashya: "Manava", tatva: "Vayu", animal: "Cat", symbol: "Quiver of arrows",
    },
    namakshara: ["Ke", "Ko", "Ha", "Hi"],
    karakatvas: ["Renewal", "Restoration", "Abundance", "Optimism", "Return"],
    compatible: ["Punarvasu", "Shravana"], incompatible: [],
  },
  {
    id: 8, sequence_number: 8, name: "Pushya", sanskrit: "Puṣya", devanagari: "पुष्य",
    meaning: "The nourisher; the best", zodiac_start: 93.3333, zodiac_end: 106.6667,
    nakshatra_lord: "Saturn", yoga_tara: "Saturn", deity: "Brihaspati",
    deity_description: "The guru of the gods, who imparts wisdom and spiritual knowledge",
    shakti: "The power to nourish and sustain", symbol: "Cow's udder / Lotus",
    padas: buildPadas(93.3333, 7),
    classifications: {
      tara_category: "Mitra", gana: "deva", yoni: "sheep", nadi: "antya",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Kshatriya",
      vashya: "Chatushpada", tatva: "Jala", animal: "Sheep", symbol: "Cow's udder / Lotus",
    },
    namakshara: ["Hu", "He", "Ho", "Da"],
    karakatvas: ["Nourishment", "Wisdom", "Spirituality", "Prosperity", "Protection"],
    compatible: ["Pushya", "Anuradha"], incompatible: [],
  },
  {
    id: 9, sequence_number: 9, name: "Ashlesha", sanskrit: "Āśleṣā", devanagari: "आश्लेषा",
    meaning: "The embrace; the entwined", zodiac_start: 106.6667, zodiac_end: 120,
    nakshatra_lord: "Mercury", yoga_tara: "Mercury", deity: "Nagas",
    deity_description: "The serpent deities, who hold the secrets of the earth",
    shakti: "The power to coil and penetrate", symbol: "Coiled serpent",
    padas: buildPadas(106.6667, 8),
    classifications: {
      tara_category: "Atimitra", gana: "rakshasa", yoni: "cat", nadi: "adi",
      deva_yama: "Yama", tripadi: false, gandanta: false, varna: "Brahmin",
      vashya: "Jalachara", tatva: "Jala", animal: "Cat", symbol: "Coiled serpent",
    },
    namakshara: ["Di", "Du", "De", "Do"],
    karakatvas: ["Mystery", "Intuition", "Healing", "Transformation", "Secrets"],
    compatible: ["Ashlesha", "Jyeshtha"], incompatible: [],
  },
  {
    id: 10, sequence_number: 10, name: "Magha", sanskrit: "Maghā", devanagari: "मघा",
    meaning: "The mighty one", zodiac_start: 120, zodiac_end: 133.3333,
    nakshatra_lord: "Ketu", yoga_tara: "Ketu", deity: "Pitris",
    deity_description: "The ancestors, who guide and protect their descendants",
    shakti: "The power to honor and connect with lineage", symbol: "Royal throne",
    padas: buildPadas(120, 9),
    classifications: {
      tara_category: "Janma", gana: "rakshasa", yoni: "rat", nadi: "madhya",
      deva_yama: "Yama", tripadi: false, gandanta: false, varna: "Shudra",
      vashya: "Chatushpada", tatva: "Jala", animal: "Rat", symbol: "Royal throne",
    },
    namakshara: ["Ma", "Mi", "Mu", "Me"],
    karakatvas: ["Ancestry", "Royalty", "Legacy", "Authority", "Tradition"],
    compatible: ["Magha", "Mula"], incompatible: [],
  },
  {
    id: 11, sequence_number: 11, name: "Purva Phalguni", sanskrit: "Pūrva Phalgunī", devanagari: "पूर्व फाल्गुनी",
    meaning: "The former reddish one", zodiac_start: 133.3333, zodiac_end: 146.6667,
    nakshatra_lord: "Venus", yoga_tara: "Venus", deity: "Bhaga",
    deity_description: "The god of marital bliss and prosperity",
    shakti: "The power to create union and enjoyment", symbol: "Front legs of a bed",
    padas: buildPadas(133.3333, 10),
    classifications: {
      tara_category: "Sampat", gana: "manushya", yoni: "rat", nadi: "antya",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Brahmin",
      vashya: "Manava", tatva: "Agni", animal: "Rat", symbol: "Front legs of a bed",
    },
    namakshara: ["Mo", "Ta", "Ti", "Tu"],
    karakatvas: ["Pleasure", "Creativity", "Romance", "Art", "Enjoyment"],
    compatible: ["Purva Phalguni", "Purva Ashadha"], incompatible: [],
  },
  {
    id: 12, sequence_number: 12, name: "Uttara Phalguni", sanskrit: "Uttara Phalgunī", devanagari: "उत्तर फाल्गुनी",
    meaning: "The latter reddish one", zodiac_start: 146.6667, zodiac_end: 160,
    nakshatra_lord: "Sun", yoga_tara: "Sun", deity: "Aryaman",
    deity_description: "The god of patronage and contracts",
    shakti: "The power to bestow patronage and alliance", symbol: "Back legs of a bed",
    padas: buildPadas(146.6667, 11),
    classifications: {
      tara_category: "Vipat", gana: "manushya", yoni: "cow", nadi: "adi",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Kshatriya",
      vashya: "Manava", tatva: "Agni", animal: "Cow", symbol: "Back legs of a bed",
    },
    namakshara: ["Te", "To", "Pa", "Pi"],
    karakatvas: ["Friendship", "Marriage", "Patronage", "Generosity", "Stability"],
    compatible: ["Uttara Phalguni", "Uttara Ashadha"], incompatible: [],
  },
  {
    id: 13, sequence_number: 13, name: "Hasta", sanskrit: "Hasta", devanagari: "हस्त",
    meaning: "The hand", zodiac_start: 160, zodiac_end: 173.3333,
    nakshatra_lord: "Moon", yoga_tara: "Moon", deity: "Savitar",
    deity_description: "The sun god, who imparts skill and dexterity",
    shakti: "The power to achieve goals through skill", symbol: "Hand",
    padas: buildPadas(160, 0),
    classifications: {
      tara_category: "Kshema", gana: "deva", yoni: "buffalo", nadi: "madhya",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Vaishya",
      vashya: "Manava", tatva: "Vayu", animal: "Buffalo", symbol: "Hand",
    },
    namakshara: ["Pu", "Sha", "Na", "Tha"],
    karakatvas: ["Skill", "Craftsmanship", "Dexterity", "Achievement", "Hands"],
    compatible: ["Hasta", "Shravana"], incompatible: [],
  },
  {
    id: 14, sequence_number: 14, name: "Chitra", sanskrit: "Citrā", devanagari: "चित्रा",
    meaning: "The bright one; the brilliant", zodiac_start: 173.3333, zodiac_end: 186.6667,
    nakshatra_lord: "Mars", yoga_tara: "Mars", deity: "Tvashtar",
    deity_description: "The divine architect and craftsman",
    shakti: "The power to accumulate merit through good deeds", symbol: "Bright jewel / Pearl",
    padas: buildPadas(173.3333, 1),
    classifications: {
      tara_category: "Pratyari", gana: "rakshasa", yoni: "tiger", nadi: "antya",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Shudra",
      vashya: "Chatushpada", tatva: "Agni", animal: "Tiger", symbol: "Bright jewel / Pearl",
    },
    namakshara: ["Pe", "Po", "Ra", "Ri"],
    karakatvas: ["Beauty", "Artistry", "Architecture", "Brilliance", "Craftsmanship"],
    compatible: ["Chitra", "Dhanishta"], incompatible: [],
  },
  {
    id: 15, sequence_number: 15, name: "Swati", sanskrit: "Svātī", devanagari: "स्वाती",
    meaning: "The independent one", zodiac_start: 186.6667, zodiac_end: 200,
    nakshatra_lord: "Rahu", yoga_tara: "Rahu", deity: "Vayu",
    deity_description: "The wind god, who moves freely and independently",
    shakti: "The power to scatter and distribute", symbol: "Young sprout / Coral",
    padas: buildPadas(186.6667, 2),
    classifications: {
      tara_category: "Sadhaka", gana: "deva", yoni: "buffalo", nadi: "adi",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Vaishya",
      vashya: "Vanachara", tatva: "Vayu", animal: "Buffalo", symbol: "Young sprout / Coral",
    },
    namakshara: ["Ru", "Re", "Ro", "Ta"],
    karakatvas: ["Independence", "Freedom", "Trade", "Wind", "Adaptability"],
    compatible: ["Swati", "Shatabhisha"], incompatible: [],
  },
  {
    id: 16, sequence_number: 16, name: "Vishakha", sanskrit: "Viśākhā", devanagari: "विशाखा",
    meaning: "The forked one; the branched", zodiac_start: 200, zodiac_end: 213.3333,
    nakshatra_lord: "Jupiter", yoga_tara: "Jupiter", deity: "Indra & Agni",
    deity_description: "The gods of power and fire, who grant victory and achievement",
    shakti: "The power to achieve many goals", symbol: "Triumphal arch / Potter's wheel",
    padas: buildPadas(200, 3),
    classifications: {
      tara_category: "Naidhana", gana: "rakshasa", yoni: "tiger", nadi: "madhya",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Kshatriya",
      vashya: "Chatushpada", tatva: "Agni", animal: "Tiger", symbol: "Triumphal arch / Potter's wheel",
    },
    namakshara: ["Ti", "Tu", "Te", "To"],
    karakatvas: ["Ambition", "Achievement", "Victory", "Determination", "Purpose"],
    compatible: ["Vishakha", "Purva Bhadrapada"], incompatible: [],
  },
  {
    id: 17, sequence_number: 17, name: "Anuradha", sanskrit: "Anurādhā", devanagari: "अनुराधा",
    meaning: "The following one; the devoted", zodiac_start: 213.3333, zodiac_end: 226.6667,
    nakshatra_lord: "Saturn", yoga_tara: "Saturn", deity: "Mitra",
    deity_description: "The god of friendship and partnership",
    shakti: "The power to create harmony and devotion", symbol: "Lotus / Staff",
    padas: buildPadas(213.3333, 4),
    classifications: {
      tara_category: "Mitra", gana: "deva", yoni: "deer", nadi: "antya",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Kshatriya",
      vashya: "Vanachara", tatva: "Jala", animal: "Deer", symbol: "Lotus / Staff",
    },
    namakshara: ["Na", "Ni", "Nu", "Ne"],
    karakatvas: ["Friendship", "Devotion", "Harmony", "Cooperation", "Loyalty"],
    compatible: ["Anuradha", "Uttara Bhadrapada"], incompatible: [],
  },
  {
    id: 18, sequence_number: 18, name: "Jyeshtha", sanskrit: "Jyeṣṭhā", devanagari: "ज्येष्ठा",
    meaning: "The eldest; the senior", zodiac_start: 226.6667, zodiac_end: 240,
    nakshatra_lord: "Mercury", yoga_tara: "Mercury", deity: "Indra",
    deity_description: "The king of the gods, who grants power and authority",
    shakti: "The power to rise above and conquer", symbol: "Circular amulet / Earring",
    padas: buildPadas(226.6667, 5),
    classifications: {
      tara_category: "Atimitra", gana: "rakshasa", yoni: "deer", nadi: "adi",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Shudra",
      vashya: "Manava", tatva: "Vayu", animal: "Deer", symbol: "Circular amulet / Earring",
    },
    namakshara: ["No", "Ya", "Yi", "Yu"],
    karakatvas: ["Authority", "Leadership", "Protection", "Seniority", "Power"],
    compatible: ["Jyeshtha", "Revati"], incompatible: [],
  },
  {
    id: 19, sequence_number: 19, name: "Mula", sanskrit: "Mūla", devanagari: "मूल",
    meaning: "The root", zodiac_start: 240, zodiac_end: 253.3333,
    nakshatra_lord: "Ketu", yoga_tara: "Ketu", deity: "Nirriti",
    deity_description: "The goddess of dissolution, who uproots and destroys",
    shakti: "The power to destroy and uproot", symbol: "Bunch of roots / Lion's tail",
    padas: buildPadas(240, 6),
    classifications: {
      tara_category: "Janma", gana: "rakshasa", yoni: "dog", nadi: "madhya",
      deva_yama: "Yama", tripadi: true, gandanta: false, varna: "Brahmin",
      vashya: "Chatushpada", tatva: "Vayu", animal: "Dog", symbol: "Bunch of roots / Lion's tail",
    },
    namakshara: ["Ye", "Yo", "Bha", "Bhi"],
    karakatvas: ["Roots", "Research", "Investigation", "Transformation", "Truth"],
    compatible: ["Mula", "Ashwini"], incompatible: [],
  },
  {
    id: 20, sequence_number: 20, name: "Purva Ashadha", sanskrit: "Pūrva Aṣāḍhā", devanagari: "पूर्व आषाढ़ा",
    meaning: "The former invincible one", zodiac_start: 253.3333, zodiac_end: 266.6667,
    nakshatra_lord: "Venus", yoga_tara: "Venus", deity: "Apas",
    deity_description: "The goddess of waters, who purifies and rejuvenates",
    shakti: "The power to invigorate and purify", symbol: "Fan / Winnowing basket",
    padas: buildPadas(253.3333, 7),
    classifications: {
      tara_category: "Sampat", gana: "manushya", yoni: "monkey", nadi: "antya",
      deva_yama: "Deva", tripadi: true, gandanta: false, varna: "Brahmin",
      vashya: "Jalachara", tatva: "Jala", animal: "Monkey", symbol: "Fan / Winnowing basket",
    },
    namakshara: ["Bhu", "Dha", "Pha", "Dha"],
    karakatvas: ["Purification", "Invigoration", "Victory", "Optimism", "Rising"],
    compatible: ["Purva Ashadha", "Purva Phalguni"], incompatible: [],
  },
  {
    id: 21, sequence_number: 21, name: "Uttara Ashadha", sanskrit: "Uttara Aṣāḍhā", devanagari: "उत्तर आषाढ़ा",
    meaning: "The latter invincible one", zodiac_start: 266.6667, zodiac_end: 280,
    nakshatra_lord: "Sun", yoga_tara: "Sun", deity: "Vishvadevas",
    deity_description: "The universal gods, who grant collective wisdom and victory",
    shakti: "The power to achieve universal success", symbol: "Elephant tusk / Small bed",
    padas: buildPadas(266.6667, 8),
    classifications: {
      tara_category: "Vipat", gana: "manushya", yoni: "mongoose", nadi: "adi",
      deva_yama: "Deva", tripadi: true, gandanta: false, varna: "Kshatriya",
      vashya: "Manava", tatva: "Jala", animal: "Mongoose", symbol: "Elephant tusk / Small bed",
    },
    namakshara: ["Bhe", "Bho", "Ja", "Ji"],
    karakatvas: ["Victory", "Wisdom", "Leadership", "Universality", "Success"],
    compatible: ["Uttara Ashadha", "Uttara Phalguni"], incompatible: [],
  },
  {
    id: 22, sequence_number: 22, name: "Shravana", sanskrit: "Śravaṇa", devanagari: "श्रवण",
    meaning: "The hearing; the listener", zodiac_start: 280, zodiac_end: 293.3333,
    nakshatra_lord: "Moon", yoga_tara: "Moon", deity: "Vishnu",
    deity_description: "The preserver god, who maintains cosmic order",
    shakti: "The power to connect and unite", symbol: "Three footprints / Ear",
    padas: buildPadas(280, 9),
    classifications: {
      tara_category: "Kshema", gana: "deva", yoni: "monkey", nadi: "madhya",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Vaishya",
      vashya: "Vanachara", tatva: "Vayu", animal: "Monkey", symbol: "Three footprints / Ear",
    },
    namakshara: ["Khi", "Khu", "Khe", "Kho"],
    karakatvas: ["Listening", "Learning", "Connection", "Communication", "Wisdom"],
    compatible: ["Shravana", "Punarvasu"], incompatible: [],
  },
  {
    id: 23, sequence_number: 23, name: "Dhanishta", sanskrit: "Dhaniṣṭhā", devanagari: "धनिष्ठा",
    meaning: "The most wealthy", zodiac_start: 293.3333, zodiac_end: 306.6667,
    nakshatra_lord: "Mars", yoga_tara: "Mars", deity: "Vasus",
    deity_description: "The eight gods of wealth and abundance",
    shakti: "The power to bestow wealth and prosperity", symbol: "Drum / Flute",
    padas: buildPadas(293.3333, 10),
    classifications: {
      tara_category: "Pratyari", gana: "rakshasa", yoni: "lion", nadi: "antya",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Shudra",
      vashya: "Chatushpada", tatva: "Vayu", animal: "Lion", symbol: "Drum / Flute",
    },
    namakshara: ["Ga", "Gi", "Gu", "Ge"],
    karakatvas: ["Wealth", "Music", "Prosperity", "Rhythm", "Abundance"],
    compatible: ["Dhanishta", "Chitra"], incompatible: [],
  },
  {
    id: 24, sequence_number: 24, name: "Shatabhisha", sanskrit: "Śatabhiṣā", devanagari: "शतभिषा",
    meaning: "The hundred healers", zodiac_start: 306.6667, zodiac_end: 320,
    nakshatra_lord: "Rahu", yoga_tara: "Rahu", deity: "Varuna",
    deity_description: "The god of cosmic waters and universal law",
    shakti: "The power to heal and protect", symbol: "Empty circle / 100 stars",
    padas: buildPadas(306.6667, 11),
    classifications: {
      tara_category: "Sadhaka", gana: "rakshasa", yoni: "horse", nadi: "adi",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Brahmin",
      vashya: "Jalachara", tatva: "Vayu", animal: "Horse", symbol: "Empty circle / 100 stars",
    },
    namakshara: ["Go", "Sa", "Si", "Su"],
    karakatvas: ["Healing", "Mystery", "Medicine", "Secrecy", "Protection"],
    compatible: ["Shatabhisha", "Swati"], incompatible: [],
  },
  {
    id: 25, sequence_number: 25, name: "Purva Bhadrapada", sanskrit: "Pūrva Bhādrapadā", devanagari: "पूर्व भाद्रपदा",
    meaning: "The former blessed feet", zodiac_start: 320, zodiac_end: 333.3333,
    nakshatra_lord: "Jupiter", yoga_tara: "Jupiter", deity: "Aja Ekapada",
    deity_description: "The one-footed goat, who represents the cosmic fire of transformation",
    shakti: "The power to raise spiritual energy", symbol: "Sword / Two front legs of a funeral cot",
    padas: buildPadas(320, 0),
    classifications: {
      tara_category: "Naidhana", gana: "manushya", yoni: "lion", nadi: "madhya",
      deva_yama: "Yama", tripadi: false, gandanta: false, varna: "Brahmin",
      vashya: "Manava", tatva: "Vayu", animal: "Lion", symbol: "Sword / Two front legs of a funeral cot",
    },
    namakshara: ["Se", "So", "Da", "Di"],
    karakatvas: ["Spirituality", "Transformation", "Intensity", "Fire", "Mysticism"],
    compatible: ["Purva Bhadrapada", "Vishakha"], incompatible: [],
  },
  {
    id: 26, sequence_number: 26, name: "Uttara Bhadrapada", sanskrit: "Uttara Bhādrapadā", devanagari: "उत्तर भाद्रपदा",
    meaning: "The latter blessed feet", zodiac_start: 333.3333, zodiac_end: 346.6667,
    nakshatra_lord: "Saturn", yoga_tara: "Saturn", deity: "Ahir Budhnya",
    deity_description: "The serpent of the deep, who holds hidden wisdom",
    shakti: "The power to bring stability and depth", symbol: "Twins / Back legs of a funeral cot",
    padas: buildPadas(333.3333, 1),
    classifications: {
      tara_category: "Mitra", gana: "manushya", yoni: "cow", nadi: "antya",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Kshatriya",
      vashya: "Manava", tatva: "Jala", animal: "Cow", symbol: "Twins / Back legs of a funeral cot",
    },
    namakshara: ["Du", "Tha", "Jha", "Na"],
    karakatvas: ["Depth", "Stability", "Wisdom", "Patience", "Hidden knowledge"],
    compatible: ["Uttara Bhadrapada", "Anuradha"], incompatible: [],
  },
  {
    id: 27, sequence_number: 27, name: "Revati", sanskrit: "Revatī", devanagari: "रेवती",
    meaning: "The prosperous one", zodiac_start: 346.6667, zodiac_end: 360,
    nakshatra_lord: "Mercury", yoga_tara: "Mercury", deity: "Pushan",
    deity_description: "The nourisher, who guides travelers and protects the journey",
    shakti: "The power to nourish and guide", symbol: "Fish / Drum",
    padas: buildPadas(346.6667, 2),
    classifications: {
      tara_category: "Atimitra", gana: "deva", yoni: "elephant", nadi: "adi",
      deva_yama: "Deva", tripadi: false, gandanta: false, varna: "Vaishya",
      vashya: "Jalachara", tatva: "Jala", animal: "Elephant", symbol: "Fish / Drum",
    },
    namakshara: ["De", "Do", "Cha", "Chi"],
    karakatvas: ["Prosperity", "Nourishment", "Guidance", "Travel", "Completion"],
    compatible: ["Revati", "Jyeshtha"], incompatible: [],
  },
];

// ── Lookup Helpers ─────────────────────────────────────────────────────────────

function normalizeNakName(s: string): string {
  return s.toLowerCase().replace(/[\s_-]+/g, "");
}

export function getNakshatraByName(name: string): NakshatraDef | undefined {
  if (!name) return undefined;
  const target = normalizeNakName(name);
  return NAKSHATRAS.find((n) => normalizeNakName(n.name) === target);
}

export function getNakshatraByLongitude(siderealDeg: number): NakshatraDef {
  const deg = ((siderealDeg % 360) + 360) % 360;
  const nakWidth = 360 / 27;
  const idx = Math.floor(deg / nakWidth);
  return NAKSHATRAS[idx];
}

export function getPadaByLongitude(siderealDeg: number): { nakshatra: NakshatraDef; pada: number; degreeInNakshatra: number } {
  const deg = ((siderealDeg % 360) + 360) % 360;
  const nakWidth = 360 / 27;
  const nakIndex = Math.floor(deg / nakWidth);
  const degreeInNak = deg - nakIndex * nakWidth;
  const pada = Math.min(4, Math.floor(degreeInNak / (nakWidth / 4)) + 1);
  return { nakshatra: NAKSHATRAS[nakIndex], pada, degreeInNakshatra: degreeInNak };
}

export function getRashiByLongitude(siderealDeg: number): { rashi: string; rashi_degree: number } {
  const deg = ((siderealDeg % 360) + 360) % 360;
  const idx = Math.floor(deg / 30);
  return { rashi: RASHI_NAMES[idx], rashi_degree: deg - idx * 30 };
}

export function getNavamshaByLongitude(siderealDeg: number): { navamsha: string; navamsha_lord: string } {
  const deg = ((siderealDeg % 360) + 360) % 360;
  const navamshaWidth = 360 / 108;
  const idx = Math.floor(deg / navamshaWidth);
  const rashiIdx = Math.floor(idx / 9);
  return { navamsha: RASHI_NAMES[rashiIdx], navamsha_lord: NAVAMSHA_LORDS[rashiIdx] };
}

// ── Tara Bala Calculation ──────────────────────────────────────────────────────

export function calculateTaraBala(birthNakshatra: string, targetNakshatra: string): TaraBalaResult {
  if (!birthNakshatra || !targetNakshatra) {
    return { category: "Unknown", lord: "Unknown", favorable: false, description: "Unknown nakshatra" };
  }
  const bNorm = normalizeNakName(birthNakshatra);
  const tNorm = normalizeNakName(targetNakshatra);
  const birthIdx = NAKSHATRAS.findIndex((n) => normalizeNakName(n.name) === bNorm);
  const targetIdx = NAKSHATRAS.findIndex((n) => normalizeNakName(n.name) === tNorm);
  if (birthIdx === -1 || targetIdx === -1) {
    return { category: "Unknown", lord: "Unknown", favorable: false, description: "Unknown nakshatra" };
  }
  const count = ((targetIdx - birthIdx) % 27 + 27) % 27;
  const categoryIdx = count % 9;
  const category = TARA_CATEGORIES[categoryIdx];
  const lord = NAKSHATRAS[targetIdx].nakshatra_lord;
  return {
    category,
    lord,
    favorable: TARA_FAVORABLE[category],
    description: TARA_DESCRIPTIONS[category],
  };
}

export function calculateTaraMatrix(birthNakshatra: string): { nakshatra: NakshatraDef; tara: TaraBalaResult }[] {
  return NAKSHATRAS.map((nak) => ({
    nakshatra: nak,
    tara: calculateTaraBala(birthNakshatra, nak.name),
  }));
}

// ── Dasha Calculation ──────────────────────────────────────────────────────────

export function calculateVimshottari(
  birthNakshatra: string,
  birthDate: Date,
): { mahadashas: DashaPeriod[]; balanceYears: number; balanceFraction: number } {
  const nak = getNakshatraByName(birthNakshatra);
  if (!nak) return { mahadashas: [], balanceYears: 0, balanceFraction: 0 };

  const lordIdx = NAKSHATRA_LORD_ORDER.indexOf(nak.nakshatra_lord);
  const lordYears = VIMSHOTTARI_YEARS[nak.nakshatra_lord];

  const degreeInNak = nak.zodiac_start % 13.3333;
  const fractionElapsed = degreeInNak / 13.3333;
  const balanceFraction = 1 - fractionElapsed;
  const balanceYears = lordYears * balanceFraction;

  const mahadashas: DashaPeriod[] = [];
  const startDate = new Date(birthDate);
  let currentDate = new Date(startDate);

  mahadashas.push({
    lord: nak.nakshatra_lord,
    years: balanceYears,
    start_date: currentDate.toISOString().slice(0, 10),
    end_date: new Date(currentDate.getTime() + balanceYears * 365.25 * 24 * 3600 * 1000).toISOString().slice(0, 10),
    level: 0,
    sub_periods: [],
  });
  currentDate = new Date(mahadashas[0].end_date);

  for (let i = 1; i < 9; i++) {
    const nextLord = NAKSHATRA_LORD_ORDER[(lordIdx + i) % 9];
    const years = VIMSHOTTARI_YEARS[nextLord];
    const endDate = new Date(currentDate.getTime() + years * 365.25 * 24 * 3600 * 1000);
    mahadashas.push({
      lord: nextLord,
      years,
      start_date: currentDate.toISOString().slice(0, 10),
      end_date: endDate.toISOString().slice(0, 10),
      level: 0,
      sub_periods: [],
    });
    currentDate = endDate;
  }

  return { mahadashas, balanceYears, balanceFraction };
}

export function calculateAntardashas(mahadasha: DashaPeriod): DashaPeriod[] {
  const lordIdx = NAKSHATRA_LORD_ORDER.indexOf(mahadasha.lord);
  const subPeriods: DashaPeriod[] = [];
  let currentDate = new Date(mahadasha.start_date);

  for (let i = 0; i < 9; i++) {
    const subLord = NAKSHATRA_LORD_ORDER[(lordIdx + i) % 9];
    const subYears = (mahadasha.years * VIMSHOTTARI_YEARS[subLord]) / 120;
    const endDate = new Date(currentDate.getTime() + subYears * 365.25 * 24 * 3600 * 1000);
    subPeriods.push({
      lord: subLord,
      years: subYears,
      start_date: currentDate.toISOString().slice(0, 10),
      end_date: endDate.toISOString().slice(0, 10),
      level: 1,
      sub_periods: [],
    });
    currentDate = endDate;
  }

  return subPeriods;
}

// ── Transit / Gochara ──────────────────────────────────────────────────────────

export interface TransitAnalysis {
  planet: string;
  transitNakshatra: string;
  transitPada: number;
  transitRashi: string;
  taraBala: TaraBalaResult;
  favorable: boolean;
}

export function analyzeTransit(
  natalMoonNakshatra: string,
  transitPlanet: string,
  transitLongitude: number,
): TransitAnalysis {
  const { nakshatra, pada } = getPadaByLongitude(transitLongitude);
  const { rashi } = getRashiByLongitude(transitLongitude);
  const tara = calculateTaraBala(natalMoonNakshatra, nakshatra.name);
  return {
    planet: transitPlanet,
    transitNakshatra: nakshatra.name,
    transitPada: pada,
    transitRashi: rashi,
    taraBala: tara,
    favorable: tara.favorable,
  };
}

// ── Muhurta ────────────────────────────────────────────────────────────────────

export interface MuhurtaResult {
  currentNakshatra: string;
  currentPada: number;
  janmaNakshatra: string;
  taraBala: TaraBalaResult;
  suitable: boolean;
  activitySuitability: string;
  timingEvaluation: string;
}

export function evaluateMuhurta(
  janmaNakshatra: string,
  currentLongitude: number,
  activity: string,
): MuhurtaResult {
  const { nakshatra, pada } = getPadaByLongitude(currentLongitude);
  const tara = calculateTaraBala(janmaNakshatra, nakshatra.name);

  const unsuitableActivities = ["travel", "journey", "marriage", "surgery", "starting business"];
  const activityLower = activity.toLowerCase();
  const isSensitiveActivity = unsuitableActivities.some((a) => activityLower.includes(a));

  const suitable = tara.favorable && !(isSensitiveActivity && !tara.favorable);

  return {
    currentNakshatra: nakshatra.name,
    currentPada: pada,
    janmaNakshatra,
    taraBala: tara,
    suitable,
    activitySuitability: suitable
      ? `Favorable for ${activity} — ${tara.category} Tara is auspicious`
      : `Avoid ${activity} — ${tara.category} Tara is inauspicious`,
    timingEvaluation: suitable
      ? `Good timing window in ${nakshatra.name} Pada ${pada}`
      : `Wait for a more favorable nakshatra`,
  };
}

// ── Special Rules ──────────────────────────────────────────────────────────────

export interface SpecialRuleResult {
  nakshatra: string;
  gandanta: boolean;
  tripadi: boolean;
  devaYama: string;
  gana: string;
  description: string;
}

export function checkSpecialRules(nakshatraName: string): SpecialRuleResult {
  const nak = getNakshatraByName(nakshatraName);
  if (!nak) {
    return { nakshatra: nakshatraName, gandanta: false, tripadi: false, devaYama: "Unknown", gana: "Unknown", description: "Unknown nakshatra" };
  }
  const c = nak.classifications;
  const descriptions: string[] = [];
  if (c.gandanta) descriptions.push("Gandanta — junction between fire and water signs, a sensitive transition point");
  if (c.tripadi) descriptions.push("Tripadi — three-pada nakshatra with special spiritual significance");
  if (c.deva_yama === "Deva") descriptions.push("Deva gana — divine nature, benefic influence");
  else descriptions.push("Yama gana — mortal nature, karmic influence");
  if (descriptions.length === 0) descriptions.push("No special rules apply");

  return {
    nakshatra: nak.name,
    gandanta: c.gandanta,
    tripadi: c.tripadi,
    devaYama: c.deva_yama,
    gana: c.gana,
    description: descriptions.join(". "),
  };
}

// ── Namakshara / Avakahada ─────────────────────────────────────────────────────

export interface NamaksharaResult {
  nakshatra: string;
  pada: number;
  namakshara: string;
  avakahada: string;
}

export function getNamakshara(nakshatraName: string, pada: number): NamaksharaResult {
  const nak = getNakshatraByName(nakshatraName);
  if (!nak) return { nakshatra: nakshatraName, pada, namakshara: "—", avakahada: "—" };
  const namakshara = nak.namakshara[pada - 1] ?? "—";
  return {
    nakshatra: nak.name,
    pada,
    namakshara,
    avakahada: `${nak.name} Pada ${pada}`,
  };
}

// ── Planet Analysis ────────────────────────────────────────────────────────────

export function analyzePlanetNakshatra(
  planet: string,
  siderealLongitude: number,
  bhava: number,
  natalMoonNakshatra?: string,
): PlanetNakshatraAnalysis {
  const { nakshatra, pada, degreeInNakshatra } = getPadaByLongitude(siderealLongitude);
  const { rashi, rashi_degree } = getRashiByLongitude(siderealLongitude);
  const { navamsha, navamsha_lord } = getNavamshaByLongitude(siderealLongitude);

  const tara = natalMoonNakshatra
    ? calculateTaraBala(natalMoonNakshatra, nakshatra.name)
    : { category: "—", lord: nakshatra.nakshatra_lord, favorable: true, description: "No natal moon reference" };

  const c = nakshatra.classifications;

  const interpretations: string[] = [];
  interpretations.push(`${planet} is in ${nakshatra.name} (${nakshatra.devanagari}), ruled by ${nakshatra.nakshatra_lord}.`);
  interpretations.push(`Pada ${pada} falls in ${navamsha} (Navamsha), ruled by ${navamsha_lord}.`);
  if (c.gandanta) interpretations.push("This is a Gandanta position — a sensitive junction point.");
  if (c.tripadi) interpretations.push("This is a Tripadi nakshatra with special spiritual significance.");
  interpretations.push(`Deity: ${nakshatra.deity}. ${nakshatra.deity_description}.`);
  interpretations.push(`Shakti: ${nakshatra.shakti}.`);
  if (tara.category !== "—") {
    interpretations.push(`Tara Bala from Moon: ${tara.category} (${tara.favorable ? "favorable" : "unfavorable"}).`);
  }

  return {
    planet,
    longitude: siderealLongitude,
    rashi,
    rashi_degree,
    bhava,
    nakshatra: nakshatra.name,
    nakshatra_lord: nakshatra.nakshatra_lord,
    yoga_tara: nakshatra.yoga_tara,
    pada,
    pada_degree: degreeInNakshatra,
    navamsha,
    navamsha_lord,
    tara_bala: tara,
    gandanta: c.gandanta,
    tripadi: c.tripadi,
    dasha: {
      mahadasha: nakshatra.nakshatra_lord,
      antardasha: navamsha_lord,
    },
    interpretation: interpretations.join(" "),
  };
}

// ── Gandanta Nakshatras ────────────────────────────────────────────────────────

export const GANDANTA_NAKSHATRAS = ["Ashwini", "Ashlesha", "Magha", "Jyeshtha", "Mula", "Revati"];

export const TRIPADI_NAKSHATRAS = ["Mula", "Purva Ashadha", "Uttara Ashadha"];

// ── Deva / Yama Nakshatras ─────────────────────────────────────────────────────

export const DEVA_NAKSHATRAS = NAKSHATRAS.filter((n) => n.classifications.deva_yama === "Deva").map((n) => n.name);
export const YAMA_NAKSHATRAS = NAKSHATRAS.filter((n) => n.classifications.deva_yama === "Yama").map((n) => n.name);

// ── Nakshatra Groups by Lord ───────────────────────────────────────────────────

export function getNakshatrasByLord(lord: string): NakshatraDef[] {
  return NAKSHATRAS.filter((n) => n.nakshatra_lord === lord);
}

export function getNakshatrasByGana(gana: string): NakshatraDef[] {
  return NAKSHATRAS.filter((n) => n.classifications.gana === gana);
}

export function getNakshatrasByNadi(nadi: string): NakshatraDef[] {
  return NAKSHATRAS.filter((n) => n.classifications.nadi === nadi);
}

export function getNakshatrasByYoni(yoni: string): NakshatraDef[] {
  return NAKSHATRAS.filter((n) => n.classifications.yoni === yoni);
}