/**
 * AstroOS — Yoga Knowledge Module (static reference data)
 *
 * Supplements the backend YogaEngine results with qualitative, classical
 * knowledge (effects, positive/negative results, intensity, classical
 * references, related yogas, descriptions) drawn from:
 *   - jyotish-knowledge-base/catalogues/yogas/ YAML files
 *   - BPHS, Phaladeepika, Saravali, Jataka Parijata, traditional sources
 *
 * Matches by yoga name (the canonical name is consistent across KB and backend).
 * Falls back to generic descriptions for any yoga not in this map, so adding a
 * new registered yoga to the backend won't break the dashboard — it'll just
 * show the basic rule conditions instead of the enriched description.
 */

"use client";

import type { YogaResultResponse } from "./types";

export type YogaIntensity = "strong" | "moderate" | "weak" | "mixed";

export interface YogaEffects {
  positive: string[];
  negative: string[];
  intensity: YogaIntensity;
}

export interface YogaClassicalReference {
  source: string;
  chapter: string | number | null;
  verse: string | number | null;
  excerpt: string;
}

export interface YogaKnowledgeEntry {
  yoga_id: string;
  name: string;
  description: string;
  aliases: string[];
  effects: YogaEffects;
  classicalReferences: YogaClassicalReference[];
  relatedYogas: string[];
  /** Categories this yoga is commonly grouped with for cross-reference. */
  tags: string[];
}

const _KNOWLEDGE: Record<string, YogaKnowledgeEntry> = {
  "Gajakesari Yoga": {
    yoga_id: "BPHS-OMY-001",
    name: "Gajakesari Yoga",
    aliases: ["Elephant-Lion Yoga"],
    description:
      "Formed when Jupiter is placed in a Kendra (1st, 4th, 7th, or 10th house) from the Moon. " +
      "The name literally means 'Elephant-Lion', suggesting a person with the strength of an " +
      "elephant and the regality of a lion. One of the most celebrated raja yogas. The yoga is " +
      "strengthened when Jupiter is not debilitated or combust.",
    effects: {
      positive: [
        "Wealth and prosperity throughout life",
        "Strong reputation and social standing",
        "High intelligence and wisdom",
        "Authority and leadership",
        "Recognition in one's field of work",
      ],
      negative: [],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: 2,
        excerpt:
          "When Chandra (Moon) and Guru (Jupiter) conjoin or Jupiter is in a kendra from Moon, " +
          "a powerful Raja Yoga known as Gajakesari Yoga is formed, granting wealth, fame, and children.",
      },
    ],
    relatedYogas: ["Chandra Mangala Yoga", "Adhi Yoga", "Lakshmi Yoga"],
    tags: ["raja", "benefic", "leadership"],
  },
  "Budhaditya Yoga": {
    yoga_id: "BPHS-OMY-005",
    name: "Budhaditya Yoga",
    aliases: ["Mercury-Sun Yoga"],
    description:
      "Formed when Sun and Mercury are in conjunction in the same sign. Mercury represents " +
      "intelligence and communication; the Sun represents authority and soul. Their conjunction " +
      "merges intellectual acuity with authoritative expression. The yoga is stronger when Mercury " +
      "is not combust.",
    effects: {
      positive: [
        "Sharp intellect and analytical ability",
        "Educational achievement and academic excellence",
        "Strong communication and oratory skills",
        "Success in administrative and government-related work",
        "Good memory and learning capacity",
      ],
      negative: ["When Mercury is combust, communication may suffer"],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: 7,
        excerpt:
          "Sun and Mercury in conjunction produce Budhaditya Yoga, granting learning, intelligence, " +
          "and eloquence.",
      },
    ],
    relatedYogas: ["Saraswati Yoga", "Gajakesari Yoga"],
    tags: ["raja", "benefic", "education", "communication"],
  },
  "Kalasarpa Yoga": {
    yoga_id: "BPHS-OMY-007",
    name: "Kalasarpa Yoga",
    aliases: [],
    description:
      "Formed when all 7 classical grahas are confined entirely to one hemisphere of the " +
      "Rahu-Ketu axis, with none straddling both sides. This yoga concentrates all planetary " +
      "energy into a focused area of life, often producing intense but one-dimensional results.",
    effects: {
      positive: ["Intense focus in one life area"],
      negative: [
        "All life areas concentrated in one hemisphere — imbalance in distribution",
        "Potential for obsession or tunnel vision",
      ],
      intensity: "mixed",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt:
          "When all grahas are hemmed between Rahu and Ketu, Kalasarpa Yoga arises.",
      },
    ],
    relatedYogas: ["Gajakesari Yoga"],
    tags: ["special", "malefic", "karmic"],
  },
  "Amala Yoga": {
    yoga_id: "BPHS-OMY-006",
    name: "Amala Yoga",
    aliases: [],
    description:
      "Formed when a natural benefic occupies the 10th house from the lagna or from the Moon. " +
      "Confers dignity, recognition, and high status in one's profession or public life.",
    effects: {
      positive: ["High status", "Public recognition", "Professional dignity"],
      negative: [],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Benefics in the 10th confer Amala Yoga.",
      },
    ],
    relatedYogas: ["Adhi Yoga"],
    tags: ["raja", "benefic", "career"],
  },
  "Vosi Yoga": {
    yoga_id: "BPHS-OMY-002",
    name: "Vosi Yoga",
    aliases: [],
    description:
      "Formed when a planet (other than the Moon) is placed in the 2nd house from the Sun. " +
      "Confers wealth and material gains through speech and communication.",
    effects: {
      positive: ["Wealth through speech", "Material gains"],
      negative: [],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Planets in the 2nd from the Sun produce Vosi Yoga.",
      },
    ],
    relatedYogas: ["Budhaditya Yoga"],
    tags: ["dhana", "benefic"],
  },
  "Vasi Yoga": {
    yoga_id: "BPHS-OMY-003",
    name: "Vasi Yoga",
    aliases: [],
    description:
      "Formed when a planet (other than the Moon) is placed in the 12th house from the Sun. " +
      "Confers hidden wealth and secret knowledge.",
    effects: {
      positive: ["Hidden wealth", "Secret knowledge", "Foreign lands"],
      negative: [],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Planets in the 12th from the Sun produce Vasi Yoga.",
      },
    ],
    relatedYogas: ["Vosi Yoga"],
    tags: ["dhana", "benefic"],
  },
  "Ubhayachari Yoga": {
    yoga_id: "BPHS-OMY-004",
    name: "Ubhayachari Yoga",
    aliases: [],
    description:
      "Formed when planets are placed in both the 2nd and 12th houses from the Sun simultaneously. " +
      "Confers gains through both speech and secret means.",
    effects: {
      positive: ["Dual wealth sources", "Versatile gains"],
      negative: [],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Planets in both the 2nd and 12th from the Sun produce Ubhayachari Yoga.",
      },
    ],
    relatedYogas: ["Vosi Yoga", "Vasi Yoga"],
    tags: ["dhana", "benefic"],
  },
  "Kendra-Trikona Raja Yoga": {
    yoga_id: "BPHS-RY-001",
    name: "Kendra-Trikona Raja Yoga",
    aliases: ["Raja Yoga"],
    description:
      "Formed when the lord of a kendra house (1/4/7/10) is associated with the lord of a " +
      "trikona house (1/5/9) — through conjunction, mutual aspect, or one-way aspect. " +
      "This is the central Raja Yoga formulation in Parashara Hora Shastra.",
    effects: {
      positive: [
        "High status and recognition",
        "Leadership positions",
        "Success in government or authority roles",
        "Wealth and fame",
      ],
      negative: [],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt:
          "When the lord of a kendra and the lord of a trikona are associated, a powerful Raja Yoga arises.",
      },
      {
        source: "Phaladeepika",
        chapter: 3,
        verse: 2,
        excerpt: "The conjunction of kendra and trikona lords produces Raja Yoga.",
      },
    ],
    relatedYogas: ["Adhi Yoga", "Chandra Mangala Yoga", "Lakshmi Yoga"],
    tags: ["raja", "benefic", "leadership"],
  },
  "Ruchaka Yoga": {
    yoga_id: "BPHS-PM-001",
    name: "Ruchaka Yoga",
    aliases: [],
    description:
      "Formed when Mars is in its own sign (Aries) or exalted (Capricorn) and placed in a Kendra " +
      "house from the lagna. One of the Panch Mahapurusha Yogas, granting martial prowess, " +
      "leadership, and victory over enemies.",
    effects: {
      positive: [
        "Valour and courage",
        "Leadership in military or competitive fields",
        "Victory over enemies",
        "Land and property gains",
      ],
      negative: ["Aggression if Mars is afflicted"],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: 1,
        excerpt:
          "Mars in Aries or Capricorn in a kendra produces Ruchaka Yoga, the Yoga of the Hero.",
      },
    ],
    relatedYogas: ["Hamsa Yoga", "Malavya Yoga", "Sasa Yoga", "Bhadra Yoga"],
    tags: ["raja", "benefic", "pancha-mahapurusha"],
  },
  "Bhadra Yoga": {
    yoga_id: "BPHS-PM-002",
    name: "Bhadra Yoga",
    aliases: [],
    description:
      "Formed when Mercury is in its own sign (Virgo/Gemini) or exalted (Virgo) and placed in a " +
      "Kendra house from the lagna. Grants intelligence, learning, and success through intellect.",
    effects: {
      positive: [
        "Exceptional intelligence and learning",
        "Success through intellect and communication",
        "Wealth through business",
        "Eloquence and diplomatic skills",
      ],
      negative: ["Overthinking or indecision if Mercury is afflicted"],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: 1,
        excerpt:
          "Mercury in its own or exalted sign in a kendra produces Bhadra Yoga.",
      },
    ],
    relatedYogas: ["Ruchaka Yoga", "Hamsa Yoga", "Saraswati Yoga"],
    tags: ["raja", "benefic", "pancha-mahapurusha"],
  },
  "Hamsa Yoga": {
    yoga_id: "BPHS-PM-003",
    name: "Hamsa Yoga",
    aliases: ["Jupiter Raja Yoga"],
    description:
      "Formed when Jupiter is in its own sign (Sagittarius/Pisces) or exalted (Cancer) and placed in " +
      "a Kendra house from the lagna. The most powerful of the Panch Mahapurusha Yogas, granting " +
      "wisdom, leadership, and spiritual advancement.",
    effects: {
      positive: [
        "Wisdom and spiritual advancement",
        "Leadership and authority",
        "Wealth and prosperity",
        "Respect in scholarly and religious circles",
        "Children and descendants",
      ],
      negative: [],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: 1,
        excerpt:
          "Jupiter in its own or exalted sign in a kendra produces Hamsa Yoga, the Yoga of Excellence.",
      },
    ],
    relatedYogas: ["Ruchaka Yoga", "Malavya Yoga", "Gajakesari Yoga"],
    tags: ["raja", "benefic", "pancha-mahapurusha", "wisdom"],
  },
  "Malavya Yoga": {
    yoga_id: "BPHS-PM-004",
    name: "Malavya Yoga",
    aliases: ["Venus Raja Yoga"],
    description:
      "Formed when Venus is in its own sign (Taurus/Libra) or exalted (Pisces) and placed in a " +
      "Kendra house from the lagna. Grants beauty, artistic talent, wealth, and harmonious relationships.",
    effects: {
      positive: [
        "Beauty and artistic talent",
        "Wealth and luxury",
        "Harmonious relationships and marriage",
        "Diplomatic skills and grace",
      ],
      negative: ["Luxury addiction if Venus is afflicted"],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: 1,
        excerpt:
          "Venus in its own or exalted sign in a kendra produces Malavya Yoga.",
      },
    ],
    relatedYogas: ["Hamsa Yoga", "Sasa Yoga", "Lakshmi Yoga"],
    tags: ["raja", "benefic", "pancha-mahapurusha", "arts"],
  },
  "Sasa Yoga": {
    yoga_id: "BPHS-PM-005",
    name: "Sasa Yoga",
    aliases: ["Saturn Raja Yoga"],
    description:
      "Formed when Saturn is in its own sign (Capricorn/Aquarius) or exalted (Libra) and placed in " +
      "a Kendra house from the lagna. Grants longevity, discipline, and slow-but-steady success. " +
      "Often produces individuals who rise to power later in life.",
    effects: {
      positive: [
        "Longevity and discipline",
        "Slow but steady rise to power",
        "Success in government or large organizations",
        "Property and land gains",
      ],
      negative: ["Delayed success and struggles in early life"],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: 1,
        excerpt:
          "Saturn in its own or exalted sign in a kendra produces Sasa Yoga.",
      },
    ],
    relatedYogas: ["Ruchaka Yoga", "Malavya Yoga"],
    tags: ["raja", "benefic", "pancha-mahapurusha", "career"],
  },
  "Neecha Bhanga Raja Yoga (Sun)": {
    yoga_id: "BPHS-NBRY-001",
    name: "Neecha Bhanga Raja Yoga (Sun)",
    aliases: ["Sun Debilitation Cancellation"],
    description:
      "Formed when the Sun is debilitated (in Libra) and its debilitation is cancelled through " +
      "one of the classical conditions: the dispositor of the debilitation sign is in a Kendra, " +
      "the sign's exaltation lord is associated with the debilitated planet, or the dispositor is itself " +
      "exalted.",
    effects: {
      positive: [
        "Transformation from weakness to strength",
        "Rise after initial setbacks",
        "Superior results through overcoming adversity",
      ],
      negative: ["Initial period of struggle before results manifest"],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 2,
        verse: null,
        excerpt:
          "When a debilitated planet's neecha is bhanga (cancelled), it produces Raja Yoga results.",
      },
    ],
    relatedYogas: ["Neecha Bhanga Raja Yoga (Moon)", "Ruchaka Yoga"],
    tags: ["special", "benefic", "cancellation"],
  },
  "Neecha Bhanga Raja Yoga (Moon)": {
    yoga_id: "BPHS-NBRY-002",
    name: "Neecha Bhanga Raja Yoga (Moon)",
    aliases: ["Moon Debilitation Cancellation"],
    description:
      "Formed when the Moon is debilitated (in Sun sign) and its debilitation is cancelled through " +
      "classical neecha bhanga conditions.",
    effects: {
      positive: [
        "Emotional resilience developed through adversity",
        "Rise after early struggles",
        "Superior results through overcoming weakness",
      ],
      negative: ["Initial emotional difficulty"],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 2,
        verse: null,
        excerpt:
          "Neecha bhanga cancels debilitation and produces positive results.",
      },
    ],
    relatedYogas: ["Neecha Bhanga Raja Yoga (Sun)", "Chandra Yoga"],
    tags: ["special", "benefic", "cancellation"],
  },
  "Neecha Bhanga Raja Yoga (Mars)": {
    yoga_id: "BPHS-NBRY-003",
    name: "Neecha Bhanga Raja Yoga (Mars)",
    aliases: [],
    description: "Mars debilitation cancellation producing Raja Yoga effects.",
    effects: {
      positive: ["Strength through overcoming adversity", "Victory after struggle"],
      negative: ["Initial setbacks in conflict or energy"],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 2,
        verse: null,
        excerpt: "Neecha bhanga for Mars produces Raja Yoga.",
      },
    ],
    relatedYogas: ["Ruchaka Yoga", "Neecha Bhanga Raja Yoga (Sun)"],
    tags: ["special", "benefic", "cancellation"],
  },
  "Neecha Bhanga Raja Yoga (Mercury)": {
    yoga_id: "BPHS-NBRY-004",
    name: "Neecha Bhanga Raja Yoga (Mercury)",
    aliases: [],
    description: "Mercury debilitation cancellation producing Raja Yoga effects.",
    effects: {
      positive: ["Intellectual resilience", "Success in communication after struggle"],
      negative: ["Initial communication difficulties"],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 2,
        verse: null,
        excerpt: "Neecha bhanga for Mercury produces Raja Yoga.",
      },
    ],
    relatedYogas: ["Saraswati Yoga", "Bhadra Yoga"],
    tags: ["special", "benefic", "cancellation"],
  },
  "Neecha Bhanga Raja Yoga (Jupiter)": {
    yoga_id: "BPHS-NBRY-005",
    name: "Neecha Bhanga Raja Yoga (Jupiter)",
    aliases: [],
    description: "Jupiter debilitation cancellation producing Raja Yoga effects.",
    effects: {
      positive: ["Wisdom through adversity", "Spiritual growth after struggle"],
      negative: ["Initial obstacles in wisdom or expansion"],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 2,
        verse: null,
        excerpt: "Neecha bhanga for Jupiter produces Raja Yoga.",
      },
    ],
    relatedYogas: ["Hamsa Yoga", "Gajakesari Yoga"],
    tags: ["special", "benefic", "cancellation"],
  },
  "Neecha Bhanga Raja Yoga (Venus)": {
    yoga_id: "BPHS-NBRY-006",
    name: "Neecha Bhanga Raja Yoga (Venus)",
    aliases: [],
    description: "Venus debilitation cancellation producing Raja Yoga effects.",
    effects: {
      positive: ["Beauty and harmony restored through struggle", "Success in arts after adversity"],
      negative: ["Initial relationship or aesthetic difficulties"],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 2,
        verse: null,
        excerpt: "Neecha bhanga for Venus produces Raja Yoga.",
      },
    ],
    relatedYogas: ["Malavya Yoga", "Lakshmi Yoga"],
    tags: ["special", "benefic", "cancellation"],
  },
  "Neecha Bhanga Raja Yoga (Saturn)": {
    yoga_id: "BPHS-NBRY-007",
    name: "Neecha Bhanga Raja Yoga (Saturn)",
    aliases: [],
    description: "Saturn debilitation cancellation producing Raja Yoga effects.",
    effects: {
      positive: ["Discipline earned through hardship", "Authority gained through perseverance"],
      negative: ["Initial delays and obstacles"],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 2,
        verse: null,
        excerpt: "Neecha bhanga for Saturn produces Raja Yoga.",
      },
    ],
    relatedYogas: ["Sasa Yoga", "Neecha Bhanga Raja Yoga (Sun)"],
    tags: ["special", "benefic", "cancellation"],
  },
  "Neecha Bhanga Raja Yoga (Rahu)": {
    yoga_id: "BPHS-NBRY-008",
    name: "Neecha Bhanga Raja Yoga (Rahu)",
    aliases: [],
    description: "Rahu debilitation cancellation producing Raja Yoga effects.",
    effects: {
      positive: ["Transformation of obsessive tendencies into mastery"],
      negative: ["Initial confusion or mental unrest"],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 2,
        verse: null,
        excerpt: "Neecha bhanga for Rahu produces Raja Yoga.",
      },
    ],
    relatedYogas: ["Kalasarpa Yoga"],
    tags: ["special", "benefic", "cancellation"],
  },
  "Neecha Bhanga Raja Yoga (Ketu)": {
    yoga_id: "BPHS-NBRY-009",
    name: "Neecha Bhanga Raja Yoga (Ketu)",
    aliases: [],
    description: "Ketu debilitation cancellation producing Raja Yoga effects.",
    effects: {
      positive: ["Spiritual advancement through overcoming karma"],
      negative: ["Initial spiritual confusion or detachment"],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 2,
        verse: null,
        excerpt: "Neecha bhanga for Ketu produces Raja Yoga.",
      },
    ],
    relatedYogas: ["Kalasarpa Yoga"],
    tags: ["special", "benefic", "cancellation", "spiritual"],
  },
  "Sunapha Yoga": {
    yoga_id: "BPHS-CY-001",
    name: "Sunapha Yoga",
    aliases: [],
    description:
      "Formed when a planet (other than the Sun) is placed in the 2nd house from the Moon. " +
      "Confers wealth and material comforts through family, speech, and personal resources.",
    effects: {
      positive: ["Wealth through family and speech", "Material comforts", "Good food and drink"],
      negative: [],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Planets in the 2nd from the Moon produce Sunapha Yoga.",
      },
    ],
    relatedYogas: ["Gajakesari Yoga"],
    tags: ["chandra", "dhana", "benefic"],
  },
  "Anapha Yoga": {
    yoga_id: "BPHS-CY-002",
    name: "Anapha Yoga",
    aliases: [],
    description:
      "Formed when a planet (other than the Sun) is placed in the 12th house from the Moon. " +
      "Confers wealth through hidden means, foreign lands, or expenditure.",
    effects: {
      positive: ["Wealth through hidden means", "Foreign travel or residence", "Spiritual inclination"],
      negative: [],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Planets in the 12th from the Moon produce Anapha Yoga.",
      },
    ],
    relatedYogas: ["Sunapha Yoga"],
    tags: ["chandra", "dhana", "benefic"],
  },
  "Durudhara Yoga": {
    yoga_id: "BPHS-CY-003",
    name: "Durudhara Yoga",
    aliases: [],
    description:
      "Formed when planets are placed in both the 2nd and 12th houses from the Moon simultaneously. " +
      "Confers wealth through both visible resources and hidden means.",
    effects: {
      positive: ["Dual wealth sources", "Versatile financial gains"],
      negative: [],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Planets in both 2nd and 12th from the Moon produce Durudhara Yoga.",
      },
    ],
    relatedYogas: ["Sunapha Yoga", "Anapha Yoga"],
    tags: ["chandra", "dhana", "benefic"],
  },
  "Kemadruma Yoga": {
    yoga_id: "BPHS-CY-004",
    name: "Kemadruma Yoga",
    aliases: ["Kemadrum Yoga"],
    description:
      "Formed when no planet occupies the 2nd or 12th house from the Moon, and no planet is " +
      "conjunct the Moon. Classically an inauspicious combination indicating struggle, but " +
      "can be canceled if the Moon is in a Kendra from the Lagna and strong, or if benefics " +
      "occupy the 11th and 2nd houses.",
    effects: {
      positive: ["Potential for greatness if yoga is canceled"],
      negative: [
        "Struggle and difficulty in early life",
        "Separation from wealth",
        "Mental anxiety and worry",
      ],
      intensity: "weak",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt:
          "When no planet is in the 2nd or 12th from the Moon, and none conjoins it, " +
          "Kemadruma Yoga arises.",
      },
    ],
    relatedYogas: ["Adhi Yoga", "Gajakesari Yoga"],
    tags: ["chandra", "malefic", "karmic"],
  },
  "Adhi Yoga": {
    yoga_id: "BPHS-CY-005",
    name: "Adhi Yoga",
    aliases: [],
    description:
      "Formed when natural benefics occupy the 6th, 7th, and 8th houses from the Moon. " +
      "Full strength when all three houses are occupied by benefics; partial when only 1-2 are occupied. " +
      "Grants protection, longevity, and success over enemies and obstacles.",
    effects: {
      positive: [
        "Protection from enemies and obstacles",
        "Longevity and good health",
        "Success over competitors",
        "Popularity and social respect",
      ],
      negative: [],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt:
          "Benefics in the 6th, 7th, and 8th from the Moon produce Adhi Yoga.",
      },
    ],
    relatedYogas: ["Chandra Mangala Yoga", "Lakshmi Yoga"],
    tags: ["chandra", "benefic", "protection"],
  },
  "Chandra Mangala Yoga": {
    yoga_id: "BPHS-CY-006",
    name: "Chandra Mangala Yoga",
    aliases: ["Moon-Mars Yoga"],
    description:
      "Formed when the Moon and Mars are in conjunction or mutually aspecting (7th from each other). " +
      "The conjunction produces stronger results than the aspect. Mars should ideally not be debilitated.",
    effects: {
      positive: [
        "Wealth through independent effort and courage",
        "Financial prosperity through one's own hard work",
        "Assertiveness and pioneering spirit",
        "Success in business and trade",
        "Strong willpower and determination",
      ],
      negative: ["Temperamental tendencies when Moon is afflicted"],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: 10,
        excerpt: "Moon and Mars in conjunction produce Chandra-Mangala Yoga.",
      },
    ],
    relatedYogas: ["Ruchaka Yoga", "Adhi Yoga"],
    tags: ["raja", "chandra", "benefic", "wealth"],
  },
  "Amavasya Yoga": {
    yoga_id: "BPHS-CY-007",
    name: "Amavasya Yoga",
    aliases: ["New Moon Yoga"],
    description:
      "Formed when the Sun and Moon are within approximately 12 degrees of each other (conjunction/ conjunction). " +
      "Represents the New Moon phase — a time of new beginnings and inner reflection. " +
      "Classical results depend heavily on the house and sign involved.",
    effects: {
      positive: ["New beginnings", "Inner reflection and planning"],
      negative: ["Hidden enemies or obstacles", "Unclear direction"],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Sun and Moon in proximity produce Amavasya Yoga.",
      },
    ],
    relatedYogas: ["Vyatipata Yoga", "Budhaditya Yoga"],
    tags: ["chandra", "special"],
  },
  "Vyatipata Yoga": {
    yoga_id: "BPHS-CY-008",
    name: "Vyatipata Yoga",
    aliases: [],
    description:
      "Formed when the Moon and Sun are in mutual dusthanas (6th, 8th, or 12th from each other). " +
      "A challenging yoga that can produce obstacles, particularly in partnership and communication areas.",
    effects: {
      positive: ["Potential for great spiritual growth"],
      negative: [
        "Obstacles in partnerships",
        "Communication difficulties",
        "Health issues in early life",
      ],
      intensity: "weak",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Sun and Moon in dusthanas produce Vyatipata Yoga.",
      },
    ],
    relatedYogas: ["Amavasya Yoga", "Kemadruma Yoga"],
    tags: ["chandra", "malefic"],
  },
  "Dhana Yoga (2nd-11th Lord Association)": {
    yoga_id: "BPHS-DY-001",
    name: "Dhana Yoga (2nd-11th Lord Association)",
    aliases: ["Wealth Yoga"],
    description:
      "Formed when the lords of the 2nd house (wealth, family resources) and 11th house (gains, income) " +
      "are associated — through conjunction, mutual aspect, or one-way aspect. This is one of the classic " +
      "wealth-producing combinations.",
    effects: {
      positive: [
        "Wealth accumulation",
        "Financial stability",
        "Good family fortune",
        "Success in earning through profession",
      ],
      negative: [],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Association of 2nd and 11th lords produces Dhana Yoga.",
      },
    ],
    relatedYogas: ["Lakshmi Yoga", "Kubera Yoga"],
    tags: ["dhana", "benefic", "wealth"],
  },
  "Dhana Yoga (11th Lord in Kendra/Trikona)": {
    yoga_id: "BPHS-DY-002",
    name: "Dhana Yoga (11th Lord in Kendra/Trikona)",
    aliases: ["11th Lord Wealth Yoga"],
    description:
      "Formed when the lord of the 11th house is placed in a Kendra (1/4/7/10) or Trikona (1/5/9) " +
      "house from the Lagna. The 11th lord in an auspicious house strengthens wealth and gains.",
    effects: {
      positive: [
        "Financial gains and prosperity",
        "Success in business",
        "Social recognition and respect",
      ],
      negative: [],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "The 11th lord in a Kendra or Trikona produces Dhana Yoga.",
      },
    ],
    relatedYogas: ["Adhi Yoga", "Lakshmi Yoga"],
    tags: ["dhana", "benefic", "wealth"],
  },
  Lakshmi: {
    yoga_id: "BPHS-COMP-001",
    name: "Lakshmi Yoga",
    aliases: [],
    description:
      "Formed when the 9th lord is in its own sign or exalted, AND Venus is in a Kendra from the Lagna. " +
      "The 9th lord represents fortune and dharma; Venus represents luxury and comfort. " +
      "This yoga confers wealth, prosperity, and a harmonious family life.",
    effects: {
      positive: [
        "Abundant wealth and prosperity",
        "Harmonious family life",
        "Fortune and luck",
        "Luxury and comforts",
      ],
      negative: [],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Ninth lord in own/exalted sign + Venus in Kendra = Lakshmi Yoga.",
      },
      {
        source: "Phaladeepika",
        chapter: 3,
        verse: null,
        excerpt: "Lakshmi Yoga grants immense wealth and family happiness.",
      },
    ],
    relatedYogas: ["Dhana Yoga", "Hamsa Yoga", "Gajakesari Yoga"],
    tags: ["dhana", "benefic", "wealth", "fortune"],
  },
  "Saraswati Yoga": {
    yoga_id: "BPHS-COMP-002",
    name: "Saraswati Yoga",
    aliases: [],
    description:
      "Formed when Jupiter, Venus, and Mercury are all in Kendra houses from the Lagna. " +
      "The conjunction or association of these three benefic planets of learning produces " +
      "exceptional intelligence, learning, and oratory skills.",
    effects: {
      positive: [
        "Exceptional learning and education",
        "Excellent communication and oratory",
        "Musical and artistic talents",
        "Wisdom and discrimination",
      ],
      negative: [],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Jupiter, Venus, and Mercury in Kendra produce Saraswati Yoga.",
      },
    ],
    relatedYogas: ["Bhadra Yoga", "Budhaditya Yoga"],
    tags: ["raja", "benefic", "education", "arts"],
  },
  "Harsha Yoga": {
    yoga_id: "BPHS-COMP-003",
    name: "Harsha Yoga",
    aliases: [],
    description:
      "Formed when the lord of the 6th house is placed in the 6th house itself. " +
      "Confers victory over enemies, good health, and financial gains through competition.",
    effects: {
      positive: ["Victory over enemies", "Good health", "Financial gains", "Competence"],
      negative: [],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "6th lord in the 6th house produces Harsha Yoga.",
      },
    ],
    relatedYogas: ["Adhi Yoga"],
    tags: ["benefic", "victory"],
  },
  "Sarala Yoga": {
    yoga_id: "BPHS-COMP-004",
    name: "Sarala Yoga",
    aliases: [],
    description:
      "Formed when the lord of the 8th house is placed in the 8th house itself. " +
      "Confers longevity, courage, and the ability to overcome hidden enemies and obstacles.",
    effects: {
      positive: ["Longevity", "Courage", "Overcoming hidden enemies", "Mystery-solving ability"],
      negative: [],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "8th lord in the 8th house produces Sarala Yoga.",
      },
    ],
    relatedYogas: ["Vimala Yoga"],
    tags: ["benefic", "longevity"],
  },
  "Vimala Yoga": {
    yoga_id: "BPHS-COMP-005",
    name: "Vimala Yoga",
    aliases: [],
    description:
      "Formed when the lord of the 12th house is placed in the 12th house itself. " +
      "Confers purity of mind, spiritual inclination, and gains through expenditure " +
      "and foreign lands.",
    effects: {
      positive: ["Purity of mind", "Spiritual progress", "Foreign gains", "Charitable nature"],
      negative: [],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "12th lord in the 12th house produces Vimala Yoga.",
      },
    ],
    relatedYogas: ["Sarala Yoga"],
    tags: ["benefic", "spiritual"],
  },
  "Dridha Yoga": {
    yoga_id: "BPHS-COMP-006",
    name: "Dridha Yoga",
    aliases: [],
    description:
      "Formed when the lords of the 6th, 8th, and 12th houses are all placed in their own " +
      "respective houses (own signs or exalted). This powerful combination grants " +
      "longevity, victory over enemies, and spiritual merit.",
    effects: {
      positive: [
        "Great longevity",
        "Complete victory over enemies and obstacles",
        "Spiritual merit and purity",
        "Financial stability",
      ],
      negative: [],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "6th, 8th, and 12th lords in own houses produce Dridha Yoga.",
      },
    ],
    relatedYogas: ["Harsha Yoga", "Sarala Yoga", "Vimala Yoga"],
    tags: ["benefic", "longevity", "victory", "spiritual"],
  },
  "Guru-Mangala Yoga": {
    yoga_id: "BPHS-COMP-007",
    name: "Guru-Mangala Yoga",
    aliases: [],
    description:
      "Formed when Jupiter (Guru) is aspecting Mars. This is a powerful combination " +
      "for success in competitive fields, particularly sports, military, and technology. " +
      "Confers courage, strategic thinking, and expansion through initiative.",
    effects: {
      positive: [
        "Success in competitive fields",
        "Courage and initiative",
        "Strategic thinking",
        "Expansion through action",
      ],
      negative: [],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Jupiter's aspect on Mars produces Guru-Mangala Yoga.",
      },
    ],
    relatedYogas: ["Ruchaka Yoga", "Hamsa Yoga"],
    tags: ["raja", "benefic", "action"],
  },
  "Papakartari Yoga": {
    yoga_id: "BPHS-ARY-001",
    name: "Papakartari Yoga",
    aliases: [],
    description:
      "Formed when malefic planets hem the Lagna (one in the 12th, one in the 2nd). " +
      "A challenging yoga that can produce obstacles, particularly in the early part of life. " +
      "The effects depend heavily on which malefics are involved and their strength.",
    effects: {
      positive: ["Resilience developed through adversity"],
      negative: [
        "Obstacles in early life",
        "Health issues",
        "Financial losses",
        "Enemies and conflicts",
      ],
      intensity: "mixed",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: null,
        excerpt: "Malefics on both sides of the Lagna produce Papakartari Yoga.",
      },
    ],
    relatedYogas: ["Kemadruma Yoga", "Mangal Dosha"],
    tags: ["dosha", "malefic"],
  },
  "Mangal Dosha": {
    yoga_id: "BPHS-ARY-001DOSHA",
    name: "Mangal Dosha",
    aliases: ["Mars Defect"],
    description:
      "Formed when Mars is placed in the 1st, 4th, 7th, 8th, or 12th house from the Lagna or Moon. " +
      "Classically associated with delays or difficulties in marriage, though the strength of Mars " +
      "and other factors can modify the results significantly.",
    effects: {
      positive: ["Courage and determination"],
      negative: [
        "Marital discord or delay",
        "Conflict in relationships",
        "Aggressive tendencies",
      ],
      intensity: "moderate",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 36,
        verse: null,
        excerpt: "Mars in a kendra or tribhagi house from Lagna/Moon produces Mangal Dosha.",
      },
    ],
    relatedYogas: ["Chandra Mangala Yoga", "Ruchaka Yoga"],
    tags: ["dosha", "malefic", "marriage"],
  },
  "Pancha Mahapurusha Yoga": {
    yoga_id: "BPHS-PM-001",
    name: "Pancha Mahapurusha Yoga",
    aliases: [],
    description:
      "The five great-person yogas, each formed by one of the outer planets (Mars, Mercury, Jupiter, " +
      "Venus, Saturn) being in its own sign or exalted, and placed in a Kendra from the Lagna. " +
      "These are among the most powerful Raja Yogas in Jyotish.",
    effects: {
      positive: ["High status", "Leadership", "Power and authority", "Spiritual advancement"],
      negative: [],
      intensity: "strong",
    },
    classicalReferences: [
      {
        source: "BPHS",
        chapter: 5,
        verse: 1,
        excerpt: "Each of the five outer planets in own/exalted sign in Kendra produces a Mahapurusha Yoga.",
      },
    ],
    relatedYogas: ["Kendra-Trikona Raja Yoga", "Hamsa Yoga"],
    tags: ["raja", "benefic", "pancha-mahapurusha"],
  },
};

function _defaultEntry(name: string, yoga_id: string): YogaKnowledgeEntry {
  return {
    yoga_id,
    name,
    aliases: [],
    description: `A classical planetary combination (${name}). See the formation rule conditions below for specific details.`,
    effects: { positive: [], negative: [], intensity: "moderate" },
    classicalReferences: [{ source: "BPHS", chapter: null, verse: null, excerpt: "" }],
    relatedYogas: [],
    tags: [],
  };
}

/** Look up enriched knowledge for a yoga by its name. */
export function getYogaKnowledge(
  result: YogaResultResponse,
): YogaKnowledgeEntry {
  return _KNOWLEDGE[result.name] ?? _defaultEntry(result.name, result.yoga_id);
}

/** Look up by name directly (for "related yogas" cross-references). */
export function getYogaKnowledgeByName(name: string): YogaKnowledgeEntry | undefined {
  return _KNOWLEDGE[name];
}

/** All yoga names that exist in the knowledge base. */
export const KNOWN_YOGA_NAMES: string[] = Object.keys(_KNOWLEDGE);

/** Yoga category → display color. */
export const YOGA_CATEGORY_COLORS: Record<string, string> = {
  "Panch Mahapurusha": "var(--accent)",
  "Raja Yoga": "var(--status-success)",
  "Dhana Yoga": "var(--status-warning)",
  "Chandra Yoga": "var(--accent)",
  "Neecha Bhanga Raja Yoga": "var(--status-success)",
  "Composite Yoga": "var(--status-success)",
  "Nabhasa Yoga": "var(--accent)",
  "Sanyasa Yoga": "var(--text-muted)",
  "Other Major Yoga": "var(--accent)",
  "Arishta Yoga": "var(--status-danger)",
};

/** Map yoga name → list of other yoga names that are conceptually related. */
export const YOGA_RELATIONSHIPS: Record<string, string[]> = Object.fromEntries(
  Object.entries(_KNOWLEDGE).map(([k, v]) => [k, v.relatedYogas]),
);
