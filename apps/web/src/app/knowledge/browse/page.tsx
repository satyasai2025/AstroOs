"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Badge, Card, Select } from "@/components/ui";
import { KARAKATVA_GRAHAS, useKarakatvaSearch } from "@/lib/karakatva";

export const dynamic = "force-dynamic";

type EntityType =
  | "planets"
  | "signs"
  | "houses"
  | "nakshatras"
  | "yogas"
  | "vargas"
  | "dashas"
  | "ashtakavarga"
  | "transits"
  | "shadbala"
  | "sahamas"
  | "prashna_kp"
  | "karakatvas"
  | "texts"
  | "rules";

const ENTITY_TYPES: { value: EntityType; label: string }[] = [
  { value: "planets", label: "Planets (Navagraha)" },
  { value: "signs", label: "Signs (Rashi)" },
  { value: "houses", label: "Houses (Bhava)" },
  { value: "nakshatras", label: "Nakshatras (27 Stars)" },
  { value: "yogas", label: "Classical Yogas" },
  { value: "vargas", label: "Divisional Charts (Shodashavarga)" },
  { value: "dashas", label: "Dashas & Timing Systems" },
  { value: "ashtakavarga", label: "Ashtakavarga & Kakshya" },
  { value: "transits", label: "Transits (Gochara, Vedha, Latta)" },
  { value: "shadbala", label: "Shadbala & Planetary Strengths" },
  { value: "sahamas", label: "Sahamas (Arabic Parts)" },
  { value: "prashna_kp", label: "Prashna & KP Sub-Lord" },
  { value: "karakatvas", label: "Karakatvas (Significations)" },
  { value: "texts", label: "Classical Texts & Scriptures" },
  { value: "rules", label: "Vedic Rules Engine" },
];

/**
 * Comprehensive reference data for all 15 Vedic Astrological Categories.
 */
const REFERENCE_ROWS: Record<Exclude<EntityType, "karakatvas">, { title: string; desc: string; details?: string }[]> = {
  planets: [
    { title: "Sun (Surya)", desc: "Soul (Atma), Father, Authority, Government, Exalted in Mesha (10°), Debilitated in Tula (10°). Own sign: Simha." },
    { title: "Moon (Chandra)", desc: "Mind (Manas), Mother, Emotions, Exalted in Vrishabha (3°), Debilitated in Vrishchika (3°). Own sign: Karka." },
    { title: "Mars (Mangala / Kuja)", desc: "Courage, Siblings, Energy, Land, Exalted in Makara (28°), Debilitated in Karka (28°). Own signs: Mesha & Vrishchika." },
    { title: "Mercury (Budha)", desc: "Intellect, Speech, Commerce, Logic, Exalted in Kanya (15°), Debilitated in Meena (15°). Own signs: Mithuna & Kanya." },
    { title: "Jupiter (Guru / Brihaspati)", desc: "Wisdom, Dharma, Children, Wealth, Exalted in Karka (5°), Debilitated in Makara (5°). Own signs: Dhanu & Meena." },
    { title: "Venus (Shukra)", desc: "Love, Beauty, Marriage, Arts, Exalted in Meena (27°), Debilitated in Kanya (27°). Own signs: Vrishabha & Tula." },
    { title: "Saturn (Shani)", desc: "Karma, Longevity, Discipline, Servants, Exalted in Tula (20°), Debilitated in Mesha (20°). Own signs: Makara & Kumbha." },
    { title: "Rahu (North Node)", desc: "Desire, Innovation, Foreign lands, Illusions, Exalted in Mithuna/Vrishabha, Debilitated in Dhanu/Vrishchika." },
    { title: "Ketu (South Node)", desc: "Moksha, Spirituality, Detachment, Intuition, Exalted in Dhanu/Vrishchika, Debilitated in Mithuna/Vrishabha." },
  ],
  signs: [
    { title: "1. Mesha (Aries)", desc: "Fire sign, Cardinal (Chara), Ruled by Mars. Exaltation sign of Sun. Body part: Head." },
    { title: "2. Vrishabha (Taurus)", desc: "Earth sign, Fixed (Sthira), Ruled by Venus. Exaltation sign of Moon. Body part: Face, Throat." },
    { title: "3. Mithuna (Gemini)", desc: "Air sign, Dual (Dwiswabhava), Ruled by Mercury. Body part: Arms, Chest." },
    { title: "4. Karka (Cancer)", desc: "Water sign, Cardinal (Chara), Ruled by Moon. Exaltation sign of Jupiter. Body part: Heart, Chest." },
    { title: "5. Simha (Leo)", desc: "Fire sign, Fixed (Sthira), Ruled by Sun. Body part: Stomach, Spine." },
    { title: "6. Kanya (Virgo)", desc: "Earth sign, Dual (Dwiswabhava), Ruled by Mercury. Exaltation sign of Mercury. Body part: Abdomen." },
    { title: "7. Tula (Libra)", desc: "Air sign, Cardinal (Chara), Ruled by Venus. Exaltation sign of Saturn. Body part: Reins, Lower Back." },
    { title: "8. Vrishchika (Scorpio)", desc: "Water sign, Fixed (Sthira), Ruled by Mars. Body part: Private Organs." },
    { title: "9. Dhanu (Sagittarius)", desc: "Fire sign, Dual (Dwiswabhava), Ruled by Jupiter. Body part: Thighs." },
    { title: "10. Makara (Capricorn)", desc: "Earth sign, Cardinal (Chara), Ruled by Saturn. Exaltation sign of Mars. Body part: Knees." },
    { title: "11. Kumbha (Aquarius)", desc: "Air sign, Fixed (Sthira), Ruled by Saturn & Rahu. Body part: Calves, Ankles." },
    { title: "12. Meena (Pisces)", desc: "Water sign, Dual (Dwiswabhava), Ruled by Jupiter. Exaltation sign of Venus. Body part: Feet." },
  ],
  houses: [
    { title: "1st House — Tanu Bhava (Lagna)", desc: "Self, physical body, vitality, health, fame, general life direction, head." },
    { title: "2nd House — Dhana Bhava", desc: "Wealth, family, speech, food, right eye, assets, face." },
    { title: "3rd House — Sahaja Bhava", desc: "Younger siblings, courage, communications, short travels, hands, shoulders." },
    { title: "4th House — Sukha Bhava", desc: "Mother, home, vehicles, land, happiness, emotional foundation, chest." },
    { title: "5th House — Putra Bhava", desc: "Children, intelligence (Buddhi), past life merit (Purva Punya), romance, speculation." },
    { title: "6th House — Satru & Roga Bhava", desc: "Enemies, diseases, debts, litigation, service, daily work, intestine." },
    { title: "7th House — Kalatra Bhava", desc: "Spouse, marriage, business partnerships, trade, public relations, groin." },
    { title: "8th House — Randhra & Ayur Bhava", desc: "Longevity, sudden transformations, secrets, occult, unearned wealth, research." },
    { title: "9th House — Dharma & Bhagya Bhava", desc: "Father, Guru, higher knowledge, luck, religion, long travels, thighs." },
    { title: "10th House — Karma Bhava", desc: "Career, profession, status, authority, government honors, knees." },
    { title: "11th House — Labha Bhava", desc: "Gains, income, elder siblings, fulfillment of desires, social network, ankles." },
    { title: "12th House — Vyaya Bhava", desc: "Losses, expenditure, foreign lands, moksha, sleep, bed pleasures, feet." },
  ],
  nakshatras: [
    { title: "1. Ashwini (0° - 13°20' Mesha)", desc: "Ketu Lord, Deity: Ashwini Kumaras. Symbol: Horse Head. Swift healing, initiation." },
    { title: "2. Bharani (13°20' - 26°40' Mesha)", desc: "Venus Lord, Deity: Yama. Symbol: Yoni. Transformation, restraint, creation." },
    { title: "3. Krittika (26°40' Mesha - 10° Vrishabha)", desc: "Sun Lord, Deity: Agni. Symbol: Razor / Flame. Purification, sharp intelligence." },
    { title: "4. Rohini (10° - 23°20' Vrishabha)", desc: "Moon Lord, Deity: Brahma. Symbol: Chariot. Growth, beauty, magnetism, fertility." },
    { title: "5. Mrigashira (23°20' Vrishabha - 6°40' Mithuna)", desc: "Mars Lord, Deity: Soma. Symbol: Deer Head. Searching, curiosity, gentle nature." },
    { title: "6. Ardra (6°40' - 20° Mithuna)", desc: "Rahu Lord, Deity: Rudra. Symbol: Teardrop. Storms, emotional catharsis, transformation." },
    { title: "7. Punarvasu (20° Mithuna - 3°20' Karka)", desc: "Jupiter Lord, Deity: Aditi. Symbol: Bow and Quiver. Return of light, renewal, safety." },
    { title: "8. Pushya (3°20' - 16°40' Karka)", desc: "Saturn Lord, Deity: Brihaspati. Symbol: Cow's Udder. Most auspicious star for nourishment & spirituality." },
    { title: "9. Ashlesha (16°40' - 30° Karka)", desc: "Mercury Lord, Deity: Nagas. Symbol: Coiled Serpent. Kundalini energy, intuition, diplomacy." },
    { title: "10. Magha (0° - 13°20' Simha)", desc: "Ketu Lord, Deity: Pitris (Ancestors). Symbol: Royal Throne. Lineage, leadership, royal dignity." },
    { title: "11. Purva Phalguni (13°20' - 26°40' Simha)", desc: "Venus Lord, Deity: Bhaga. Symbol: Hammock / Couch. Romance, relaxation, creative arts." },
    { title: "12. Uttara Phalguni (26°40' Simha - 10° Kanya)", desc: "Sun Lord, Deity: Aryaman. Symbol: Bed legs. Patronage, contracts, honorable relationships." },
    { title: "13. Hasta (10° - 23°20' Kanya)", desc: "Moon Lord, Deity: Savitar. Symbol: Open Hand / Fist. Craftsmanship, skill, healing, dexterity." },
    { title: "14. Chitra (23°20' Kanya - 6°40' Tula)", desc: "Mars Lord, Deity: Vishwakarma. Symbol: Jewel / Pearl. Architecture, design, brilliance." },
    { title: "15. Swati (6°40' - 20° Tula)", desc: "Rahu Lord, Deity: Vayu. Symbol: Young Plant Shoot / Sword. Independence, diplomacy, mobility." },
    { title: "16. Vishakha (20° Tula - 3°20' Vrishchika)", desc: "Jupiter Lord, Deity: Indra & Agni. Symbol: Triumphal Arch. Goal orientation, focused determination." },
    { title: "17. Anuradha (3°20' - 16°40' Vrishchika)", desc: "Saturn Lord, Deity: Mitra. Symbol: Lotus / Staff. Friendship, devotion, endurance." },
    { title: "18. Jyeshtha (16°40' - 30° Vrishchika)", desc: "Mercury Lord, Deity: Indra. Symbol: Circular Amulet / Umbrella. Seniority, protection, heroism." },
    { title: "19. Mula (0° - 13°20' Dhanu)", desc: "Ketu Lord, Deity: Nirriti. Symbol: Tied Roots. Deep investigation, unearthing root causes." },
    { title: "20. Purva Ashadha (13°20' - 26°40' Dhanu)", desc: "Venus Lord, Deity: Apas (Water). Symbol: Winnowing Basket. Invincibility, purification." },
    { title: "21. Uttara Ashadha (26°40' Dhanu - 10° Makara)", desc: "Sun Lord, Deity: Vishwadevas. Symbol: Elephant Tusk. Final victory, righteousness." },
    { title: "22. Shravana (10° - 23°20' Makara)", desc: "Moon Lord, Deity: Vishnu. Symbol: Three Footprints / Ear. Deep listening, oral tradition." },
    { title: "23. Dhanishta (23°20' Makara - 6°40' Kumbha)", desc: "Mars Lord, Deity: Eight Vasus. Symbol: Drum / Flute. Music, wealth, rhythmic timing." },
    { title: "24. Shatabhisha (6°40' - 20° Kumbha)", desc: "Rahu Lord, Deity: Varuna. Symbol: Empty Circle / 100 Physicians. Healing, mystery, secret knowledge." },
    { title: "25. Purva Bhadrapada (20° Kumbha - 3°20' Meena)", desc: "Jupiter Lord, Deity: Aja Ekapada. Symbol: Front Legs of Funeral Cot. Tapasya, spiritual fire." },
    { title: "26. Uttara Bhadrapada (3°20' - 16°40' Meena)", desc: "Saturn Lord, Deity: Ahirbudhnya. Symbol: Back Legs of Cot / Serpent in Deep Waters. Wisdom, restraint." },
    { title: "27. Revati (16°40' - 30° Meena)", desc: "Mercury Lord, Deity: Pushan. Symbol: Fish / Drum. Nourishment, completion, journey's end." },
  ],
  yogas: [
    { title: "Gaja Kesari Yoga", desc: "Jupiter in Kendra (1st, 4th, 7th, 10th) from Moon. Bestows intelligence, lasting reputation, and protective fortune." },
    { title: "Budhaditya Yoga", desc: "Sun and Mercury conjunct in same sign. Bestows sharp analytical intellect, administrative skill, and scholarship." },
    { title: "Raja Yoga (Kendra & Trikona Combination)", desc: "Lord of a Kendra (1, 4, 7, 10) combines with Lord of a Trikona (1, 5, 9). Grants power, status, and leadership." },
    { title: "Dhana Yogas (Wealth Combinations)", desc: "Interconnection between 1st, 2nd, 5th, 9th, and 11th houses or their lords. Generates high financial prosperity." },
    { title: "Ruchaka Yoga (Pancha Mahapurusha)", desc: "Mars in own sign or exaltation in a Kendra house. Grants physical strength, heroism, military/executive authority." },
    { title: "Bhadra Yoga (Pancha Mahapurusha)", desc: "Mercury in own sign or exaltation in a Kendra house. Grants eloquent speech, commerce mastery, and longevity." },
    { title: "Hamsa Yoga (Pancha Mahapurusha)", desc: "Jupiter in own sign or exaltation in a Kendra house. Grants righteous nature, spiritual wisdom, and societal respect." },
    { title: "Malavya Yoga (Pancha Mahapurusha)", desc: "Venus in own sign or exaltation in a Kendra house. Grants artistic genius, luxury, vehicles, and marital bliss." },
    { title: "Sasa Yoga (Pancha Mahapurusha)", desc: "Saturn in own sign or exaltation in a Kendra house. Grants mass authority, political leadership, and perseverance." },
    { title: "Vipreet Raja Yogas (Harsha, Sarala, Vimala)", desc: "6th, 8th, 12th lords placed in 6th, 8th, or 12th houses. Overcomes adversity to achieve sudden triumph." },
  ],
  vargas: [
    { title: "D1 — Rashi Chart", desc: "Primary natal chart representing physical existence and general life overview." },
    { title: "D2 — Hora Chart", desc: "Wealth, financial prosperity, and speech split into Sun & Moon halves." },
    { title: "D3 — Drekkana Chart", desc: "Siblings, courage, third-house matters, and 36 Decans." },
    { title: "D4 — Chaturthamsa (Turyamsa)", desc: "Fixed assets, land, real estate, home, and fortune." },
    { title: "D7 — Saptamsha", desc: "Children, grandchildren, progeny strength, and creative lineage." },
    { title: "D9 — Navamsha", desc: "Spouse, inner soul dignity, marriage, dharma, and planetary strength verification." },
    { title: "D10 — Dashamsha", desc: "Career, profession, executive power, honors, and public standing." },
    { title: "D12 — Dwadasamsha", desc: "Parents, ancestral karma, and family lineage." },
    { title: "D16 — Shodashamsha", desc: "Vehicles, comforts, conveyances, and luxuries." },
    { title: "D20 — Vimsamsha", desc: "Spiritual practice, upasana, religious devotion, and meditation." },
    { title: "D24 — Chaturvimsamsha (Siddhamsa)", desc: "Education, learning, higher knowledge, academic achievements." },
    { title: "D27 — Saptavimsamsha (Nakshatramsa)", desc: "Strengths, weaknesses, and subconscious stamina." },
    { title: "D30 — Trimsamsha", desc: "Afflictions, misfortunes, character flaws, and karmic debts." },
    { title: "D40 — Khavedamsha", desc: "Auspicious and inauspicious karmic effects." },
    { title: "D45 — Akshavedamsha", desc: "Fine analysis of all human matters." },
    { title: "D60 — Shashtiamsha", desc: "Past life karma and authoritative fine-grained planetary strength." },
  ],
  dashas: [
    { title: "Vimshottari Dasha (120-Year Nakshatra Cycle)", desc: "Primary Parashari timing system based on birth Moon Nakshatra (Ketu 7y, Venus 20y, Sun 6y, Moon 10y, Mars 7y, Rahu 18y, Jupiter 16y, Saturn 19y, Mercury 17y)." },
    { title: "Ashtottari Dasha (108-Year Non-Solar Cycle)", desc: "Used when Rahu is in Kendra/Trikona to Lagna lord in Krishna Paksha." },
    { title: "Yogini Dasha (36-Year 8-Yogini Cycle)", desc: "Mangala, Pingala, Dhanya, Bhramari, Bhadrika, Ulka, Siddha, Sankata cycles." },
    { title: "Chara Dasha (Jaimini Rashi Dasha)", desc: "Sign-based dasha system evaluating Karakas and sign strengths." },
    { title: "Kalachakra Dasha (Wheel of Time)", desc: "Based on Nakshatra Pada progression across Deha and Jeeva signs." },
  ],
  ashtakavarga: [
    { title: "BAV (Bhinna Ashtakavarga)", desc: "Individual planet score (0 to 8 bindus) per sign evaluating personal planetary strength." },
    { title: "SAV (Samudaya Ashtakavarga)", desc: "Composite sign score (0 to 56 bindus). Signs with 28+ bindus deliver prosperous transit results." },
    { title: "Kakshya Subdivision (3°45' Zones)", desc: "Each 30° sign divided into 8 Kakshyas ruled by Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna." },
  ],
  transits: [
    { title: "Sade Sati (Saturn Transit)", desc: "7.5 year transit of Saturn through 12th, 1st, and 2nd houses from natal Moon." },
    { title: "Ashtama Shani", desc: "Transit of Saturn through 8th house from natal Moon, causing transformative challenges." },
    { title: "Murthi Nirnaya (Transit Metallic Quality)", desc: "Swarna (Gold 🥇), Ropya (Silver 🥈), Tamra (Copper 🥉), Loha (Iron 🪙) based on Moon sign at transit entry." },
    { title: "House-based Vedha & Vipreet Vedha", desc: "Obstruction rules where transit results are neutralized by opposing planet positions." },
    { title: "Latta (Planetary Kicks)", desc: "Puro Latta (forward kick) and Prishta Latta (backward kick) on sensitive nakshatras." },
  ],
  shadbala: [
    { title: "Sthana Bala (Positional Strength)", desc: "Based on Uchcha (Exaltation), Saptavargiya, Ojhayugma, Kendra, and Drekkana position." },
    { title: "Dig Bala (Directional Strength)", desc: "Sun/Mars in 10th, Jupiter/Mercury in 1st, Moon/Venus in 4th, Saturn in 7th." },
    { title: "Kala Bala (Temporal Strength)", desc: "Nathonnatha, Paksha, Tribhaga, Varsha, Masa, Dina, Hora, Ayana Bala." },
    { title: "Chesta Bala (Motional Strength)", desc: "Based on planetary retrograde motion, speed, and brightness." },
    { title: "Naisargika Bala (Natural Strength)", desc: "Fixed natural rank: Sun > Moon > Venus > Jupiter > Mercury > Mars > Saturn." },
    { title: "Drik Bala (Aspectual Strength)", desc: "Strength derived from benefic or malefic aspects cast by other planets." },
  ],
  sahamas: [
    { title: "Punya Sahama (Fortune & Merit)", desc: "Moon - Sun + Lagna (Day birth) / Sun - Moon + Lagna (Night birth)." },
    { title: "Vidya Sahama (Education & Knowledge)", desc: "Sun - Moon + Lagna (Day birth)." },
    { title: "Vivaha Sahama (Marriage & Union)", desc: "Venus - Saturn + Lagna." },
    { title: "Karma Sahama (Career & Achievements)", desc: "Mars - Sun + Lagna." },
    { title: "Raja Sahama (Status & Power)", desc: "Saturn - Sun + Lagna." },
  ],
  prashna_kp: [
    { title: "Prashna Horary Seed (1 - 249)", desc: "Random horary seed number mapping to Nakshatra Sub-Lord divisions." },
    { title: "Sub-Lord Theory (KP System)", desc: "Determines final event outcome based on the Sub-Lord of the relevant house cusp." },
    { title: "Cuspal Interlinks (CIL)", desc: "Interlinkages between house cuspal sub-sub lords confirming event promise." },
  ],
  texts: [
    { title: "Brihat Parashara Hora Shastra (BPHS)", desc: "Foundational classical encyclopedia of Vedic Astrology attributed to Sage Parashara." },
    { title: "Saravali", desc: "Masterwork by Kalyana Varma covering yogas, planetary states, and divisional chart interpretations." },
    { title: "Phaladeepika", desc: "Classical masterpiece by Mantreswara explaining transit results, dasha fruits, and yogas." },
    { title: "Jataka Parijata", desc: "Authoritative text by Vaidyanatha Dikshita on planetary yogas and predictive rules." },
    { title: "Uttara Kalamrita", desc: "Classical compendium by Kalidasa rich in Karakatvas and unique predictive principles." },
    { title: "Hora Sara", desc: "Classical text by Prithuyasas (son of Varahamihira) detailing dasha effects and house results." },
  ],
  rules: [
    { title: "10th Lord in Kendra — Professional Supremacy", desc: "10th lord placed in 1st, 4th, 7th, or 10th house creates high career stability and leadership." },
    { title: "Dharma-Karma Raj Yoga (9th & 10th Lords)", desc: "Conjunction or mutual aspect between 9th and 10th lords produces supreme authority and honor." },
    { title: "Jupiter Aspect on Lagna — Protective Shield", desc: "5th, 7th, or 9th aspect of Jupiter on Lagna neutralizes 100,000 afflictions in the chart." },
    { title: "Exalted Lagna Lord — Vitality & Success", desc: "Lagna lord in exaltation sign grants radiant health, longevity, and high self-esteem." },
  ],
};

function BrowseContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const type = (searchParams.get("type") as EntityType) ?? "planets";
  const [graha, setGraha] = useState("sun");

  const karakatvaQuery = useKarakatvaSearch({ graha });

  const setType = (v: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("type", v);
    router.push(`/knowledge/browse?${params.toString()}`);
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Knowledge Browse
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Browse Vedic astrology reference entities by category.
        </p>
      </div>

      <div className="mb-4 max-w-xs">
        <Select label="Entity Type" options={ENTITY_TYPES} value={type} onChange={setType} />
      </div>

      {type === "karakatvas" ? (
        <div className="space-y-3">
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            Real data from the Karakatva database (450 seeded entries) — same source as{" "}
            <a href="/karakatva" style={{ color: "var(--cyan-400)" }}>
              /karakatva
            </a>
            .
          </p>
          <div className="max-w-xs">
            <Select
              label="Filter by Graha"
              options={KARAKATVA_GRAHAS.map((g) => ({ value: g, label: g }))}
              value={graha}
              onChange={setGraha}
            />
          </div>
          {karakatvaQuery.isLoading && (
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              Loading…
            </p>
          )}
          {karakatvaQuery.data?.karakatvas.slice(0, 20).map((item) => (
            <Card key={item.id}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
                  {item.subject}
                </h3>
                {item.graha && <Badge tone="cyan">{item.graha}</Badge>}
              </div>
              {item.description && (
                <p className="mt-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                  {item.description}
                </p>
              )}
            </Card>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-400">
              Showing authoritative Vedic reference entities for <strong className="text-cyan-400 font-bold">{ENTITY_TYPES.find(t => t.value === type)?.label}</strong>:
            </p>
            <Badge tone="cyan">{REFERENCE_ROWS[type]?.length || 0} Entries</Badge>
          </div>
          {REFERENCE_ROWS[type]?.map((row) => (
            <Card key={row.title}>
              <h3 className="text-base font-bold text-white">
                {row.title}
              </h3>
              <p className="mt-1 text-sm text-slate-300 leading-relaxed">
                {row.desc}
              </p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default function KnowledgeBrowsePage() {
  return (
    <Suspense fallback={null}>
      <BrowseContent />
    </Suspense>
  );
}
