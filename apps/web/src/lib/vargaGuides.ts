/**
 * Per-varga (divisional chart) reference guides for the Charts page.
 *
 * This is presentation/knowledge content only — it describes what each
 * divisional chart rules and how to read it. The actual varga *calculation*
 * lives server-side (`apps/api/services/divisional_engine.py`); this module
 * never computes anything. Divisor values and short display labels are owned
 * by `VARGA_DIVISORS` in `lib/astro.ts` — this module deliberately reuses
 * them rather than duplicating the labels, so the card header and the guide
 * can never drift out of sync.
 */

export interface VargaGuide {
  /** Canonical code, e.g. "D9". */
  code: string;
  /** Classical name, e.g. "Navamsha". */
  classicName: string;
  /** Lay description of what the chart subdivides. */
  description: string;
  /** The life domains this varga is classically read for. */
  governs: string[];
  /** What a varga placement physically represents. */
  mechanics: string;
  /** Step-by-step reading discipline for this chart. */
  howToUse: string[];
  /** One-line takeaway shown to the user. */
  summary: string;
}

export const VARGA_GUIDES: Record<string, VargaGuide> = {
  D1: {
    code: "D1",
    classicName: "Rashi",
    description:
      "The moon-to-moon Rashi chart (divided ÷1) is the natal birth chart itself — the unrefined 'as-is' picture of the life.",
    governs: ["Physical body", "Overall life", "Foundation", "Baseline personality"],
    mechanics:
      "Every other divisional chart is a refinement of this one. D1 is always read first and is the anchor every varga is tested against.",
    howToUse: [
      "Always start here — D1 sets the frame and the baseline strengths/weaknesses.",
      "Use D1 for the gross, everyday matters: body, health, home, and the literal chain of significations.",
      "When a planet is strong in D1, its matters are settled at the visible level; when it only shines in a varga, the matter develops at a deeper or later layer.",
    ],
    summary: "The foundation — read every matter here first, then confirm in the relevant varga.",
  },
  D2: {
    code: "D2",
    classicName: "Hora",
    description:
      "The Hora chart (÷2) splits each sign into a day (male/Sun) half and a night (female/Moon) half — a simple two-fold division.",
    governs: ["Wealth", "Money", "Food", "Prosperity"],
    mechanics:
      "Each sign is cut in half: the first 15° is the Sun's 'day' hora, the second 15° the Moon's 'night' hora. Which half a planet falls in tinges the sign's colour and the planet's wealth flavour.",
    howToUse: [
      "Read D2 mainly for money and wealth-signification of each planet.",
      "Check which hora each wealth-significator (2nd lord, 11th lord, Saturn, Venus) occupies to see if wealth expresses openly (day/Sun) or quietly (night/Moon).",
      "Use it as a quick prosperity check rather than a life-map — D2 is thin; weigh it lightly.",
    ],
    summary:
      "A quick day/night hemisphere split of each sign — read it for money, food, and the flavour of prosperity.",
  },
  D3: {
    code: "D3",
    classicName: "Drekkana",
    description:
      "The Drekkana chart (÷3) divides each 30° sign into three 10° decanates, each ruled by the lord of the 1st, 5th, or 9th sign counting from it.",
    governs: ["Courage", "Self-effort", "Siblings", "Vigour"],
    mechanics:
      "Each sign is cut into three 10° thirds; the decanate ruler adds a tempering quality to every planet and to the ascendant's native courage.",
    howToUse: [
      "Read D3 for drive, initiative, and resilience — how the native asserts themselves.",
      "Weigh the D3 ascendant (the 'dawn' decanate) for overall courage and will.",
      "Look to D3 for sibling significators when D1 is ambiguous.",
    ],
    summary:
      "Divided by threes — the chart of courage, self-effort, and the virile expression of each planet.",
  },
  D4: {
    code: "D4",
    classicName: "Chathurthamsha",
    description:
      "The Chathurthamsha chart (÷4) divides each sign into four 7°30′ parts — the chart of property, land, and fixed rootedness.",
    governs: ["Lands", "Property", "Houses", "Real estate", "Fixed assets", "Abode"],
    mechanics:
      "Each sign is quartered; the culminating 7°30′ slice tells you which 'quarter' of a sign a planet's material rooting sits in.",
    howToUse: [
      "Read D4 for real estate, landed property, houses, and material inheritance.",
      "Inspect the 4th house and the 4th lord's D4 positioning for home and fixed assets.",
      "Use D4 to distinguish 'what you own and settle in' from the more fluid, movable matters read in D2/D7.",
    ],
    summary:
      "The four-part chart of lands, property, houses, and the fixed roots of one's material foundation.",
  },
  D5: {
    code: "D5",
    classicName: "Panchamsha",
    description:
      "The Panchamsha chart (÷5) divides each sign into five 6° parts, mapped to a fixed set of five target signs — classically read for fame, power, and spiritual authority.",
    governs: ["Fame", "Power", "Spiritual authority", "Status"],
    mechanics:
      "Each sign is split into five 6° parts; unlike most vargas, the parts map to an explicit, non-sequential set of target signs rather than a simple offset.",
    howToUse: [
      "Read D5 for fame, personal power, and spiritual or worldly authority.",
      "Weigh it alongside D9 and D10 rather than as a standalone chart — D5 is a minor supporting varga.",
    ],
    summary:
      "The five-part chart of fame, power, and spiritual authority.",
  },
  D6: {
    code: "D6",
    classicName: "Shashthamsha",
    description:
      "The Shashthamsha chart (÷6) divides each sign into six 5° parts — the chart of health, disease, obstacles, and enemies (6th-house matters).",
    governs: ["Health", "Disease", "Obstacles", "Enemies", "Debts"],
    mechanics:
      "Each sign is split into six 5° parts, starting from Aries for odd signs and Libra for even signs.",
    howToUse: [
      "Read D6 for health vulnerabilities, chronic ailments, and the nature of obstacles or adversaries.",
      "Check the 6th lord and any malefics' D6 placement for the type of struggle a planet's significations face.",
    ],
    summary:
      "The six-part chart of health, disease, obstacles, and enemies.",
  },
  D7: {
    code: "D7",
    classicName: "Saptamamsha",
    description:
      "The Saptamamsha chart (÷7) divides each sign into seven parts — classically the chart of children, progeny, and seed/creation.",
    governs: ["Children", "Progeny", "Creation", "Fertility", "Legacy"],
    mechanics:
      "Each sign is split into seven ~4°17′ parts; the resulting placement shows the refined condition of the 'seed' significations (5th house, Jupiter, etc.).",
    howToUse: [
      "Read D7 for offspring — number and quality of children, and the 5th house matters of creation.",
      "Look for the 5th lord and Jupiter's D7 placement as the main children indicators.",
      "In modern practice also link D7 to the fruits of one's labour and generative projects.",
    ],
    summary:
      "The seven-part chart of children, progeny, and generative creation.",
  },
  D8: {
    code: "D8",
    classicName: "Ashtamsha",
    description:
      "The Ashtamsha chart (÷8) divides each sign into eight 3°45′ parts — the chart of longevity, sudden events, and transformation (8th-house matters).",
    governs: ["Longevity", "Sudden events", "Transformation", "Accidents", "Inheritance"],
    mechanics:
      "Each sign is split into eight parts, with the starting sign set by the natal sign's quality — Movable signs start from Aries, Fixed from Sagittarius, Dual from Leo.",
    howToUse: [
      "Read D8 for longevity indicators, sudden or transformative events, and the nature of unexpected reversals.",
      "Use it as a supporting chart alongside D1 and the 8th house — not as a standalone longevity predictor.",
    ],
    summary:
      "The eight-part chart of longevity, sudden events, and transformation.",
  },
  D9: {
    code: "D9",
    classicName: "Navamsha",
    description:
      "The Navamsha chart (÷9) is the single most important divisional chart after D1. It reflects marriage, partnership, dharma, and the refined inner self.",
    governs: ["Marriage", "Partnerships", "Dharma", "Innate nature", "Life purpose"],
    mechanics:
      "Each sign is divided into nine equal 3°20′ parts. A planet's D9 position shows the *inner quality* behind its D1 promise, and is the standard confirmation chart for judging strength.",
    howToUse: [
      "Treat D9 as the confirmation chart — a planet behaving well here elevates a middling D1 position; a poor D9 dents a strong D1 show.",
      "Read the 7th house and 7th lord in D9 for marriage and partnership quality.",
      "A planet in the same sign in both D1 and D9 is Vargottama — exceptionally strong.",
      "Use D9 for life purpose and dharma, not just marriage.",
    ],
    summary:
      "The most consulted varga — read it for marriage, partnerships, and the refined inner strength behind every planet.",
  },
  D10: {
    code: "D10",
    classicName: "Dashamsha",
    description:
      "The Dashamsha chart (÷10) divides each sign by ten into 3° parts — the chart of profession, career, honor, and public standing.",
    governs: ["Career", "Profession", "Authority", "Public standing", "Reputation"],
    mechanics:
      "Each sign is split into ten 3° parts; the D10 placement of the 10th lord and karmic significators reveals how the professional life is enacted.",
    howToUse: [
      "Read D10 for career direction, profession, and the level of public authority and name.",
      "Focus on the 10th house, 10th lord, and karmic significators (Saturn, Sun, Jupiter) in D10.",
      "Cross-check a strong D10 against the D1 10th house — career is judged confidently only when both support the same reading.",
    ],
    summary:
      "The ten-part chart of career, profession, and public reputation — the go-to for professional life.",
  },
  D11: {
    code: "D11",
    classicName: "Rudramsha",
    description:
      "The Rudramsha chart (÷11) divides each sign into eleven parts — the chart of death-related matters, gains through struggle, and destruction of adversaries (11th/8th-house overlap).",
    governs: ["Gains through struggle", "Destruction of enemies", "Death-related matters", "Inheritance"],
    mechanics:
      "Each sign is split into eleven ~2°44′ parts; the starting sign is found by counting the natal sign's position from Aries and counting that same number backward from Aries.",
    howToUse: [
      "Read D11 for gains achieved through struggle or conflict, and the fate of adversaries.",
      "Treat it as a minor, supporting varga — cross-check against D1's 8th and 11th houses rather than reading it alone.",
    ],
    summary:
      "The eleven-part chart of gains through struggle and the destruction of adversaries.",
  },
  D12: {
    code: "D12",
    classicName: "Dwadashamsha",
    description:
      "The Dwadashamsha chart (÷12) divides each sign into twelve 2°30′ parts — read classically for parents and the ancestral line.",
    governs: ["Father", "Parents", "Ancestral lineage", "Roots"],
    mechanics:
      "Each sign is split into twelve parts; the resulting placements detail the condition of one's parental and ancestral roots.",
    howToUse: [
      "Read D12 mainly for the father and the paternal/ancestral inheritance.",
      "Weigh the lord of the sign connected to parents and ancestral significators in D12.",
      "Use it to separate 'inherited conditioning' from the native's own effort read in D10.",
    ],
    summary:
      "The twelve-part chart of parents and ancestral lineage.",
  },
  D16: {
    code: "D16",
    classicName: "Shodashamsha",
    description:
      "The Shodashamsha chart (÷16) divides each sign into sixteen 1°52′30″ parts — read for vehicles, travel, possessions, and comforts.",
    governs: ["Vehicles", "Travel", "Possessions", "Comforts", "Acquisition"],
    mechanics:
      "Each sign is cut into sixteen parts; planets here reveal the wish-fulfillment and acquired-comfort layer of the life.",
    howToUse: [
      "Read D16 for what one acquires and rides — vehicles, homes-based comforts, and worldly acquisitions.",
      "Look at the placements of Mercury, Venus, and the comfort/4th significators in D16.",
      "Use it as the possession and comfort chart, distinct from the wealth chart D2.",
    ],
    summary:
      "The sixteen-part chart of vehicles, travel, possessions, and acquired comforts.",
  },
  D20: {
    code: "D20",
    classicName: "Vimshamsha",
    description:
      "The Vimshamsha chart (÷20) divides each sign into twenty 1°30′ parts — read for spiritual practice, worship, and religious inclination.",
    governs: ["Spirituality", "Worship", "Religious practice", "Spiritual merit"],
    mechanics:
      "Each sign is split into twenty parts; the D20 placements show the depth and type of one's spiritual path and devotional practice.",
    howToUse: [
      "Read D20 for spiritual/religious inclination, including the Rishi Argala on spiritual planets.",
      "Weigh Jupiter and the 9th/12th house connections in D20 for the type of worship and practice.",
      "Use D20 to see whether spirituality is a genuine inner path or a surface observance.",
    ],
    summary:
      "The twenty-part chart of spiritual practice, worship, and religious inclination.",
  },
  D24: {
    code: "D24",
    classicName: "Siddhamsha",
    description:
      "The Siddhamsha (Chathurthamsha/Soothramsa) chart (÷24) divides each sign into twenty-four 1°15′ parts — read for education, learning, and intellect.",
    governs: ["Education", "Learning", "Intellect", "Knowledge", "Study"],
    mechanics:
      "Each sign is cut into twenty-four parts; D24 placements reveal the quality and scope of the intellectual and academic life.",
    howToUse: [
      "Read D24 for academic success, the intellect, and the pursuit of knowledge.",
      "Focus on Mercury, Jupiter, the 5th (education), and the 4th (learning environment) in D24.",
      "Use D24 to judge the depth of scholarship and the native's capacity for study.",
    ],
    summary:
      "The twenty-four-part chart of education, intellect, and the pursuit of knowledge.",
  },
  D27: {
    code: "D27",
    classicName: "Bhamsha",
    description:
      "The Bhamsha (Nakshatramsa) chart (÷27) divides each sign into twenty-seven 1°6′40″ parts, matching the 27 nakshatras — read for strengths, weaknesses, and constitution.",
    governs: ["Strengths", "Weaknesses", "Physical constitution", "Vitality", "Nature"],
    mechanics:
      "Each sign is split into 27 parts that map onto the navamsas of the nakshatra lords; the resulting placement shades each planet's innate strength and weakness.",
    howToUse: [
      "Read D27 for the inherent strengths and weaknesses behind each planet and the overall constitution.",
      "Check the D27 position of key functional benefics/malefics to see where the native's nature is 'notched'.",
      "Use it as the vitality and nature chart — lighter than D9 but useful for constitution.",
    ],
    summary:
      "The twenty-seven-part chart of innate strengths, weaknesses, and physical constitution.",
  },
  D30: {
    code: "D30",
    classicName: "Trimshamsha",
    description:
      "The Trimshamsha chart (÷30) divides each sign into thirty unequal parts (planets rule varying arc lengths) — read diagnostically for misfortune, obstacles, and negative karma.",
    governs: ["Misfortunes", "Obstacles", "Illness", "Negative karma", "Adversity"],
    mechanics:
      "Each sign is divided into 30 trimshamshas where the five planets rule arcs of differing length (Sun 5°, Moon 5°, Mars 7°, Mercury 5°, Venus 7°, Saturn 8°); placements flag where hardship concentrates.",
    howToUse: [
      "Read D30 when diagnosing problems — illnesses, obstacles, thefts, and reverses.",
      "Identify which planets occupy harsh trimshamshas to locate the source of adversity.",
      "Weigh it diagnostically (why things go wrong) rather than as a general life map.",
    ],
    summary:
      "The thirty-part diagnostic chart of misfortune, obstacles, illness, and adverse karma.",
  },
  D40: {
    code: "D40",
    classicName: "Khavedamsha",
    description:
      "The Khavedamsha chart (÷40) divides each sign into forty 45′ parts — read for the mother and for inherited auspicious/inauspicious karma.",
    governs: ["Mother", "Maternal lineage", "Inherited karma", "Grace"],
    mechanics:
      "Each sign is split into forty parts; D40 placements reveal the mother's condition and the auspiciousness of what one inherits.",
    howToUse: [
      "Read D40 for the mother, maternal lineage, and the flow of inherited grace or hindrance.",
      "Look at the mother-significator (Moon, Venus, 4th lord) nor D40 positioning.",
      "Use it alongside D12 (father) to separate the two parental lines.",
    ],
    summary:
      "The forty-part chart of the mother, maternal lineage, and inherited karma.",
  },
  D45: {
    code: "D45",
    classicName: "Akshavedamsha",
    description:
      "The Akshavedamsha chart (÷45) divides each sign into forty-five 40′ parts — read for the overall fortune of the paternal line and the household's collective fate.",
    governs: ["Paternal fortune", "Family estate", "Collective fate"],
    mechanics:
      "Each sign is cut into forty-five parts; D45 placements weight the collective fortune of the family/ancestral house.",
    howToUse: [
      "Read D45 for the fortunes of the paternal line and the family's collective standing.",
      "Weigh it with D12 for father and D40 for mother to build the full ancestral picture.",
      "Use D45 sparingly and always in conjunction with D1 — it is a fine-grain chart.",
    ],
    summary:
      "The forty-five-part chart of paternal-line fortune and the family's collective fate.",
  },
  D60: {
    code: "D60",
    classicName: "Shastyamsha",
    description:
      "The Shastyamsha chart (÷60) divides each sign into sixty 30′ parts — the most detailed 'karmic fine-print' chart used for the finest judgment and past-life karma.",
    governs: ["Karmic fine-print", "Destiny details", "Past-life karma", "Fine judgment"],
    mechanics:
      "Each sign is cut into sixty parts; planets here carry the most granular, karmically-loaded imprint, useful for the deepest fine-tuning of a reading.",
    howToUse: [
      "Read D60 for the deep, karmic detail and final fine judgment of an outcome.",
      "Use it to refine — not replace — conclusions from D1 and D9 when precision matters.",
      "Check repeated Vargottama-like strength here as a sign of deeply settled karmic stability.",
    ],
    summary:
      "The sixty-part karmic fine-print chart — the deepest refinement and finest judgment of a life.",
  },
};

/** @returns the guide for a varga code, or undefined if the code is unknown. */
export function getVargaGuide(code: string): VargaGuide | undefined {
  return VARGA_GUIDES[code];
}