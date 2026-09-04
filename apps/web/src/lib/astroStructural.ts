/**
 * AstroOS — 13-Parameter Structural Reference Tables
 *
 * The analytical backbone of Planet Explorer. Four typed tables describe each
 * graha's construction across Rashi / Graha / Bhava / Nakshatra+Pada. Values
 * are classical reference data (Parashara-derived) kept as short display
 * strings. Where recognised classical authorities differ or a value is not
 * standard, the cell is the explicit `REF_UNAVAILABLE` marker — we never
 * fabricate a value the user can later assume is correct.
 *
 * The Nakshatra table is keyed PADA-SPECIFICALLY ("Ardra-Pada-1".."Ardra-Pada-4")
 * because a few parameters depend on pada. The Navamsha Sign Link (sutra 1) is
 * intentionally left blank here — it is computed live from the chart's real D9
 * position helper `navamshaSignFromLongitude`, not from a static lookup.
 */

/** Marker for a structural value with no single reliable classical source. */
export const REF_UNAVAILABLE = "Reference unavailable";

// ── Param labels (one per sutra, per column) ───────────────────────────────

export const RASHI_PARAMS = [
  "Mobility",
  "Internal Guna",
  "Tatva (Element)",
  "Gender",
  "Lordship",
  "Compass Direction",
  "Varna",
  "Diurnal Strength",
  "Rising Method",
  "Physical Form",
  "Natural Abode",
  "Material Type",
  "Body Part",
];

export const GRAHA_PARAMS = [
  "Movement Style",
  "Psychological Guna",
  "Elemental Rule",
  "Gender",
  "Planetary Cabinet",
  "Directional Strength",
  "Varna Class",
  "Dhatu (Humour)",
  "Abode",
  "Taste (Rasa)",
  "Time-Cycle Rule",
  "Vision (Drishti)",
  "Anatomical System",
];

export const BHAVA_PARAMS = [
  "Purushartha",
  "Geometric Shape",
  "Functional Nature",
  "Upachaya Growth",
  "Maraka Status",
  "Bhava Karaka",
  "Bhavat Bhavam",
  "Argala Influence",
  "Yoga Formation",
  "Aspect Rules",
  "Compass Direction",
  "Cosmic Mapping",
  "Chara/Sthira Base",
];

export const NAKSHATRA_PARAMS = [
  "Navamsha Sign Link",
  "Tri-Guna Matrix",
  "Purushartha",
  "Vimshottari Lord",
  "Ruling Deity",
  "Physical Symbol",
  "Direction of Motion",
  "Nadi",
  "Gana",
  "Yoni",
  "Gender Alignment",
  "Soul Caste (Varna)",
  "Sacred Tree (Vriksha)",
];

export interface StructuralEntry {
  /** params[0..12], one per sutra for this entity. */
  params: string[];
}

/** Navamsha (D9) sign name from a sidereal longitude — the live, non-fabricated
 *  "Navamsha Sign Link". Applies the Parashara odd/even sign rotation. */
export function navamshaSignFromLongitude(siderealDeg: number): string {
  const RASHI_EN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"];
  const deg = ((siderealDeg % 360) + 360) % 360;
  const signIdx = Math.floor(deg / 30);
  const inSign = deg - signIdx * 30;
  const ninth = Math.floor(inSign / (30 / 9)); // 0..8
  const oddSign = signIdx % 2 === 0; // odd (male) signs are 1,3,5,7,9,11 → index even
  const navIdx = oddSign ? (signIdx + ninth) % 12 : (signIdx + 8 - ninth) % 12;
  return RASHI_EN[navIdx];
}

// ── Rashi (12) ───────────────────────────────────────────────────────────────
// Standard values: mobility, element, gender, lordship, compass direction,
// rising method, abode and body-part are single-source Parashara facts.

export const RASHI_STRUCTURE: Record<string, StructuralEntry> = {
  Aries: { params: ["Movable (Chara)", "Tamasic", "Fire", "Masculine", "Mars", "East", REF_UNAVAILABLE, "Nocturnal", "Odd (Shirsha)", "A ram; horned head", "Mountain, forest, wilds", REF_UNAVAILABLE, "Head"] },
  Taurus: { params: ["Fixed (Sthira)", "Rajasic", "Earth", "Feminine", "Venus", "South", REF_UNAVAILABLE, "Diurnal", "Even (Prishtha)", "A bull; strong neck", "Plains, pasture, farmland", REF_UNAVAILABLE, "Face & throat"] },
  Gemini: { params: ["Dual (Dvisvabhava)", "Sattvic", "Air", "Masculine", "Mercury", "West", REF_UNAVAILABLE, "Diurnal", "Odd (Shirsha)", "A twin; winged couple", "Grove, marketplace, crossroads", REF_UNAVAILABLE, "Arms & shoulders"] },
  Cancer: { params: ["Movable (Chara)", "Sattvic", "Water", "Feminine", "Moon", "North", REF_UNAVAILABLE, "Nocturnal", "Even (Prishtha)", "A crab; back-mounted", "River, shore, watery home", REF_UNAVAILABLE, "Chest & breasts"] },
  Leo: { params: ["Fixed (Sthira)", "Rajasic", "Fire", "Masculine", "Sun", "East", REF_UNAVAILABLE, "Diurnal", "Odd (Shirsha)", "A lion; maned form", "Mountain cave, royal den", REF_UNAVAILABLE, "Heart & stomach"] },
  Virgo: { params: ["Dual (Dvisvabhava)", "Tamasic", "Earth", "Feminine", "Mercury", "South", REF_UNAVAILABLE, "Diurnal", "Even (Prishtha)", "A maiden with sheaf", "Field, threshing floor, home", REF_UNAVAILABLE, "Belly & intestines"] },
  Libra: { params: ["Movable (Chara)", "Rajasic", "Air", "Masculine", "Venus", "West", REF_UNAVAILABLE, "Diurnal", "Odd (Shirsha)", "A man with a balance", "Market, court, trade-place", REF_UNAVAILABLE, "Navel & lower back"] },
  Scorpio: { params: ["Fixed (Sthira)", "Tamasic", "Water", "Feminine", "Mars", "North", REF_UNAVAILABLE, "Nocturnal", "Even (Prishtha)", "A scorpion; stinging tail", "Crevice, well, secret place", REF_UNAVAILABLE, "Genitals & hips"] },
  Sagittarius: { params: ["Dual (Dvisvabhava)", "Sattvic", "Fire", "Masculine", "Jupiter", "East", REF_UNAVAILABLE, "Diurnal", "Odd (Shirsha)", "A centaur archer", "Temple, stable, open ground", REF_UNAVAILABLE, "Thighs"] },
  Capricorn: { params: ["Movable (Chara)", "Tamasic", "Earth", "Feminine", "Saturn", "South", REF_UNAVAILABLE, "Nocturnal", "Even (Prishtha)", "A crocodile; fish-tailed", "Coast, marsh, low place", REF_UNAVAILABLE, "Knees"] },
  Aquarius: { params: ["Fixed (Sthira)", "Sattvic", "Air", "Masculine", "Saturn", "West", REF_UNAVAILABLE, "Diurnal", "Odd (Shirsha)", "A water-bearer", "Waterside, workshop, pond", REF_UNAVAILABLE, "Ankles & calves"] },
  Pisces: { params: ["Dual (Dvisvabhava)", "Sattvic", "Water", "Feminine", "Jupiter", "North", REF_UNAVAILABLE, "Nocturnal", "Even (Prishtha)", "Two fishes bound", "Ocean, lake, holy place", REF_UNAVAILABLE, "Feet"] },
};

// ── Graha (9) ────────────────────────────────────────────────────────────────
// Digbala (directional strength), element, gender and humour are standard;
// psychological guna, cabinet and some hermetic rows vary by school → marked.

export const GRAHA_STRUCTURE: Record<string, StructuralEntry> = {
  Sun: { params: ["Steady (regular speed)", "Sattvic", "Fire (Tejas)", "Masculine", "Sovereign (King)", "Strongest in 10th", "Kshatriya", "Bone (Asthi)", "Palace / well-lit dwelling", "Pungent", "6 Vimshottari MD-years", "Full (7th only)", "Heart, bone, vitality"] },
  Moon: { params: ["Fast (Chara-gati)", "Sattvic", "Water (Apas)", "Feminine", "Chief Minister", "Strongest in 4th", "Vaishya", "Lymph & fluid (Rasa)", "Homes near water", "Salty", "10 Vimshottari MD-years", "Full (7th only)", "Mind, fluids, blood"] },
  Mars: { params: ["Irregular (Vakra-prone)", "Tamasic", "Fire (Agni)", "Masculine", "Commander-in-Chief", "Strongest in 10th", "Kshatriya", "Marrow & blood (Majja)", "Furnace / workshop", "Pungent", "7 Vimshottari MD-years", "4th, 7th, 8th", "Muscle, blood, marrow"] },
  Mercury: { params: ["Very fast (Atichara)", "Rajasic", "Earth (Prithvi)", "Neuter", "Prince (Ambassador of mind)", "Strongest in 1st (Asc)", "Shudra", "Skin (Twak)", "Playground / market", "Mixed (all rasa)", "17 Vimshottari MD-years", "Full (7th only)", "Skin, intellect, speech"] },
  Jupiter: { params: ["Slow, steady", "Sattvic", "Ether (Akasha)", "Masculine", "Guru (Minister)", "Strongest in 1st (Asc)", "Brahmana", "Fat (Meda)", "Treasury / temple", "Sweet", "16 Vimshottari MD-years", "5th, 7th, 9th", "Liver, fat, wisdom"] },
  Venus: { params: ["Regular, soft", "Sattvic", "Water (Apas)", "Feminine", "Envoy (Ambassador)", "Strongest in 7th", "Brahmana", "Reproductive fluid (Shukra)", "Bedchamber / pleasure house", "Sour", "20 Vimshottari MD-years", "Full (7th only)", "Reproductive & renal systems"] },
  Saturn: { params: ["Slowest, irregular", "Tamasic", "Air (Vayu)", "Masculine", "Worker (Servant)", "Strongest in 7th", "Shudra", "Bone & nerves (Snayu)", "Ruins / place of iron", "Astringent", "19 Vimshottari MD-years", "3rd, 7th, 10th", "Bones, joints, nerves"] },
  Rahu: { params: ["Shadow (headless)", "Tamasic", "Smoke (unique)", "Masculine (shadow)", "Shadow advisor", REF_UNAVAILABLE, "Outcaste (mixed)", "Subtle transcendence", "Gambling house / foreign land", "Bitter", "18 Vimshottari MD-years", "5th, 7th, 9th (special)", "Skin, aura, illusion"] },
  Ketu: { params: ["Shadow (headless)", "Sattvic-Tamasic", "Ether (Akasha-special)", "Masculine (shadow)", "Hidden servant", REF_UNAVAILABLE, "Outcaste (mixed)", "Moksha fluid", "Cremation ground / retreat", "Tasteless (no rasa)", "7 Vimshottari MD-years", "5th, 7th, 9th (special)", "Feet, subtle body, aura"] },
};

// ── Bhava (12) ───────────────────────────────────────────────────────────────
// Purushartha, functional nature, karaka and maraka are standard Parashara
// facts; geometric shape / cosmic mapping / chara-sthira base are classical
// schemata with competing versions → a few left unavailable.

export const BHAVA_STRUCTURE: Record<string, StructuralEntry> = {
  "1": { params: ["Dharma", "Square (Lagna)", "Kendra · Trikona", "Growth house -3", "Non-maraka", "Self (Tanu)", "Bhavat bhavam of 7", "Argala from 3/10/11", "Soul yoga knot", "Sees 7 (opposition)", "East", REF_UNAVAILABLE, "Chara basics"] },
  "2": { params: ["Artha", "Triangle (Dhana)", "Wealth (Dhana)", "Non-upachaya", "Maraka (with 7)", "Wealth (Dhana)", "Bhavat bhavam of 8", "Argala from 4/8/12", "Speech yoga", "Neutered", "North-east", REF_UNAVAILABLE, "Fixed holdings"] },
  "3": { params: ["Kama", "Square (Parakrama)", "Upachaya", "Upachaya (growth)", "Non-maraka", "Courage (Parakrama)", "Bhavat bhavam of 9", "Argala from 5/9", "Battle yoga", "Sees 9 (trine)", "South-east", REF_UNAVAILABLE, "Chara initiative"] },
  "4": { params: ["Moksha", "Triangle (Sukha)", "Kendra · Jaya", "Growth house -2", "Non-maraka", "Home (Sukha)", "Bhavat bhavam of 10", "Argala from 6/10/2", "Heart yoga", "Sees 7 & 10", "South", REF_UNAVAILABLE, "Fixed ground"] },
  "5": { params: ["Dharma", "Triangle (Putra)", "Trikona", "Non-upachaya", "Non-maraka", "Children (Putra)", "Bhavat bhavam of 11", "Argala from 7/11", "Mantra/budhi yoga", "Sees 9 (trine)", "South-west", REF_UNAVAILABLE, "Chara creations"] },
  "6": { params: ["Artha", "Square (Ari)", "Dusthana · Upachaya", "Upachaya (growth)", "Non-maraka", "Enemies (Ari)", "Bhavat bhavam of 12", "Argala from 8/12/4", "Combat / service yoga", "Neutered", "West", REF_UNAVAILABLE, "Chara service"] },
  "7": { params: ["Kama", "Triangle (Kalatra)", "Kendra", "Non-upachaya", "Maraka (with 2)", "Spouse (Kalatra)", "Bhavat bhavam of 1", "Argala from 9/1/5", "Union yoga", "Sees 1 & 4 (7-ward)", "North-west", REF_UNAVAILABLE, "Fixed partnership"] },
  "8": { params: ["Moksha", "Square (Ayuh)", "Dusthana · Randhra", "Non-upachaya", "Non-maraka", "Longevity (Ayuh)", "Bhavat bhavam of 2", "Argala from 10/2/6", "Longevity yoga", "Sees 12 (opposition)", "North", REF_UNAVAILABLE, "Chara crisis"] },
  "9": { params: ["Dharma", "Triangle (Bhagya)", "Trikona", "Non-upachaya", "Non-maraka", "Fortune (Bhagya)", "Bhavat bhavam of 3", "Argala from 11/3", "Seeker/Guru yoga", "Sees 5 (trine)", "North-east", REF_UNAVAILABLE, "Fixed destiny"] },
  "10": { params: ["Artha", "Triangle (Karma)", "Kendra", "Upachaya (growth)", "Non-maraka", "Action (Karma)", "Bhavat bhavam of 4", "Argala from 12/4/8", "Achievement yoga", "Sees 4 & 1 (kendra)", "Mid-heaven (zenith)", REF_UNAVAILABLE, "Chara work"] },
  "11": { params: ["Kama", "Square (Labha)", "Upachaya", "Upachaya (largest)", "Non-maraka", "Gains (Labha)", "Bhavat bhavam of 5", "Argala from 1/5", "Gain yoga", "Sees 3,5 (trines)", "North-east", REF_UNAVAILABLE, "Chara aspiration"] },
  "12": { params: ["Moksha", "Square (Vyaya)", "Dusthana · Vyahala", "Non-upachaya", "Non-maraka", "Loss (Vyaya)", "Bhavat bhavam of 6", "Argala from 2/6/10", "Moksha yoga", "Sees 6 (opposition)", "West-north", REF_UNAVAILABLE, "Chara dissolution"] },
};

// ── Nakshatra base (27 × 12 static params; pad-1 navamsha computed live) ─────
// Deity, gana, yoni, nadi, varna and vriksha are standard classical tables.
// Keys for the repeatable-pada row point to the shared base via generation.

type NakBase = [string, string, string, string, string, string, string, string, string, string, string, string];
//            [Tri-guna, Purushartha, Lord(yes repeat), Deity, Symbol, Motion, Nadi, Gana, Yoni, Gender, Varna/Caste, Vriksha]

const NAK_BASE: Record<string, NakBase> = {
  Ashwini: ["Sattvic", "Artha", "Ketu", "The Ashwini Kumaras (healer twins)", "Horse head", "Sagittarius-forward", "Adi (Vata)", "Deva", "Horse (Ashwa)", "Masculine", "Brahmana", "Kumbha (wood-apple)"],
  Bharani: ["Tamasic", "Moksha", "Venus", "Yama (Dharma King)", "Yoni (vulva); lamp", "Cancer-transverse", "Madhya (Pitta)", "Manushya", "Elephant (Gaja)", "Feminine", "Shudra", "Amla"],
  Krittika: ["Rajasic", "Kama", "Sun", "Agni (god of fire)", "Flame; razor", "Aries/Leo-agni", "Anta (Kapha)", "Rakshasa", "Goat/Buffalo", "Feminine", "Kshatriya", "Fig (Udumbara)"],
  Rohini: ["Rajasic", "Kama", "Moon", "Brahma / Prajapati", "Bull-cart (chariot)", "Taurus-forward", "Madhya (Pitta)", "Manushya", "Serpent (Sarpa)", "Feminine", "Shudra", "Jamun (jambu)"],
  Mrigashira: ["Sattvic", "Artha", "Mars", "Soma (the Moon)", "Deer head", "Gemini-transverse", "Adi (Vata)", "Deva", "Serpent (Sarpa)", "Feminine", "Kshatriya", "Khoya (acacia)"],
  Ardra: ["Rajasic", "Kama", "Rahu", "Rudra (storm god)", "Teardrop; human form", "Gemini-back", "Madhya (Pitta)", "Manushya", "Dog (Shvan)", "Feminine", "Shudra", "Agarwood (Aguru)"],
  Punarvasu: ["Sattvic", "Artha", "Jupiter", "Aditi (infinite Mother)", "Bow & quiver", "Cancer-back", "Anta (Kapha)", "Deva", "Cat (Marjara)", "Masculine", "Vaishya", "Bamboo"],
  Pushya: ["Sattvic", "Artha", "Saturn", "Brihaspati (Jupiter)", "Cow's udder; lotus", "Cancer-forward", "Madhya (Pitta)", "Deva", "Ram/Sheep (Mesha)", "Masculine", "Shudra", REF_UNAVAILABLE],
  Ashlesha: ["Tamasic", "Moksha", "Mercury", "Naga (serpent kings)", "Coiled serpent", "Cancer-back", "Adi (Vata)", "Rakshasa", "Cat (Marjara)", "Masculine", "Shudra", REF_UNAVAILABLE],
  Magha: ["Rajasic", "Dharma", "Ketu", "Pitris (ancestors)", "Throne; palanquin", "Leo-forward", "Anta (Kapha)", "Rakshasa", "Rat (Mushaka)", "Masculine", "Kshatriya", "Banyan (Vata)"],
  "Purva Phalguni": ["Rajasic", "Dharma", "Venus", "Bhaga (god of bliss)", "Front legs of cot", "Leo-forward", "Madhya (Pitta)", "Manushya", "Rat (Mushaka)", "Feminine", "Brahmana", "Madhuka"],
  "Uttara Phalguni": ["Sattvic", "Dharma", "Sun", "Aryaman (patron of contracts)", "Back legs of cot", "Leo-back", "Anta (Kapha)", "Manushya", "Bull (Vrishabha)", "Feminine", "Kshatriya", "Fig (Udumbara)"],
  Hasta: ["Sattvic", "Artha", "Moon", "Savitar (creative Sun)", "Open hand (fist)", "Virgo-transverse", "Anta (Kapha)", "Deva", "Buffalo (Mahish)", "Feminine", "Vaishya", "Jasmine"],
  Chitra: ["Tamasic", "Kama", "Mars", "Vishvakarma (celestial architect)", "Bright jewel; pearl", "Virgo-forward", "Madhya (Pitta)", "Rakshasa", "Tiger (Vyaghra)", "Feminine", "Shudra", "Banyan (Vata)"],
  Swati: ["Rajasic", "Kama", "Rahu", "Vayu (wind god)", "Coral; young sprout", "Libra-forward", "Adi (Vata)", "Deva", "Buffalo (Mahish)", "Masculine", "Vaishya", "Arjuna tree"],
  Vishakha: ["Rajasic", "Kama", "Jupiter", "Indra & Agni (two-horned)", "Archway; nail/arrow", "Libra-transverse", "Anta (Kapha)", "Manushya", "Tiger (Vyaghra)", "Feminine", "Kshatriya", "Banyan (Vata)"],
  Anuradha: ["Sattvic", "Dharma", "Saturn", "Mitra (friendship god)", "Lotus (triumphal arch); key", "Libra-back", "Anta (Kapha)", "Deva", "Deer (Mriga)", "Feminine", "Brahmana", "Kadamba tree"],
  Jyeshtha: ["Tamasic", "Moksha", "Mercury", "Indra (god of power)", "Earring; lotus", "Scorpio-back", "Adi (Vata)", "Rakshasa", "Deer (Mriga)", "Feminine", "Shudra", "Tamarisk"],
  Mula: ["Tamasic", "Moksha", "Ketu", "Nirriti (goddess of dissolution)", "Tied roots; lion's tail", "Scorpio-back", "Madhya (Pitta)", "Rakshasa", "Dog (Shvan)", "Feminine", "Kshatriya", "Khadira (acacia)"],
  "Purva Ashadha": ["Rajasic", "Kama", "Venus", "Apas (waters / Varuna)", "Fan (winnowing); tusk", "Sagittarius-forward", "Adi (Vata)", "Deva", "Monkey (Vanara)", "Feminine", "Brahmana", "Pomegranate"],
  "Uttara Ashadha": ["Sattvic", "Dharma", "Sun", "The Vishvadevas / Ganga", "Elephant tusk; plank", "Sagittarius-back", "Anta (Kapha)", "Manushya", "Mongoose (Nakul)", "Masculine", "Shudra", "Jackfruit (Panasa)"],
  Shravana: ["Sattvic", "Dharma", "Moon", "Vishnu (the Preserver)", "Ear (three footprints)", "Capricorn-forward", "Madhya (Pitta)", "Deva", "Monkey (Vanara)", "Masculine", "Brahmana", REF_UNAVAILABLE],
  Dhanishta: ["Tamasic", "Moksha", "Mars", "The Eight Vasus", "Drum (mridanga)", "Capricorn-back", "Madhya (Pitta)", "Rakshasa", "Lion (Simha)", "Feminine", "Vaishya", "Mango tree"],
  Shatabhisha: ["Rajasic", "Artha", "Rahu", "Varuna (water/universal)", "Empty circle; triskelion (wheel)", "Aquarius-transverse", "Anta (Kapha)", "Rakshasa", "Horse (Ashwa)", "Masculine", "Shudra", "Neem tree"],
  "Purva Bhadrapada": ["Tamasic", "Moksha", "Jupiter", "Aja Ekapada (the One-footed Goat)", "Sword; twin feet", "Aquarius-back", "Anta (Kapha)", "Manushya", "Lion (Simha)", "Masculine", "Brahmana", "Arjuna tree"],
  "Uttara Bhadrapada": ["Sattvic", "Artha", "Saturn", "Ahir Budhnya (serpent of deep)", "Twin legs; gator", "Pisces-forward", "Adi (Vata)", "Manushya", "Cow (Go)", "Masculine", "Brahmana", "Udumbara (fig)"],
  Revati: ["Sattvic", "Dharma", "Mercury", "Pushan (nourisher / cattle god)", "Fish (pai) drum", "Pisces-back", "Anta (Kapha)", "Deva", "Elephant (Gaja)", "Feminine", "Brahmana", "Ashoka tree"],
};

/** Build all 108 pada-specific entries from the 27-entry base. Sutra 1
 *  (Navamsha Sign Link) is left blank → resolved live at render time. */
const NAK_STRUCTURE: Record<string, StructuralEntry> = {};
for (const [name, base] of Object.entries(NAK_BASE)) {
  for (let p = 1; p <= 4; p++) {
    NAK_STRUCTURE[`${name}-Pada-${p}`] = { params: ["", ...base] };
  }
}
export const NAKSHATRA_STRUCTURE: Record<string, StructuralEntry> = NAK_STRUCTURE;