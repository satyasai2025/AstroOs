"use client";

import { useState, useMemo } from "react";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Verse {
  id: string;
  source: "BPHS" | "Saravali" | "Phaladeepika" | "Jaimini" | "Parashara";
  sanskrit: string;
  translation: string;
  context: string;
  chapter: string;
  verseNumber: string;
  confidence?: number; // 0-1
  citation?: {
    book?: string;
    chapter?: string;
    verse?: string;
    translator?: string;
  };
  relatedYogas?: string[]; // e.g. ["raja_yoga_1", "gajakesari_7"]
}

interface ClassicalLiteratureViewProps {
  /** Initial verse to display; if none, shows catalog */
  initialVerseId?: string;
  /** Filter by text search */
  onVerseSelect?: (verse: Verse) => void;
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const SOURCES = [
  { id: "BPHS", label: "Brihat Parashara Hora Shastra" },
  { id: "Saravali", label: "Saravali of Kalyanavarma" },
  { id: "Phaladeepika", label: "Phaladeepika of Mantreswara" },
  { id: "Jaimini", label: "Jaimini Sutras" },
  { id: "Parashara", label: "Parashara Smriti" },
] as const;


/** Sample verses — real data would come from a backend API */
const SAMPLE_VERSES: Verse[] = [
  {
    id: "bphs-ch1-v3",
    source: "BPHS",
    sanskrit: "यो बालः केन्द्रे त्रिभुवने च भानोर्भामिनी योषिदयितः प्रभुश्च। येनিন্তशः काले धरया कृतस्तं सूर्याश्म जानIH सततं प्रसन्नः॥",
    translation:
      "If the Sun is in the ascendant, or in the mid-heaven, or in the 7th, or in the 10th, or in the 4th, then he is ever pleased (gives good results).",
    context: "Chapter 1: The Sun. General effects of the Sun in various houses.",
    chapter: "Chapter 1",
    verseNumber: "Verse 3",
    confidence: 0.98,
    citation: {
      book: "Brihat Parashara Hora Shastra",
      chapter: "1",
      verse: "3",
      translator: "G. V. Sharma",
    },
    relatedYogas: ["surya_yoga_1", "sun_in_kendra"],
  },
  {
    id: "saravali-ch10-v1",
    source: "Saravali",
    sanskrit: "यो ब内省nio जनसंस्कारैस्तिष्ठेद्राजा स क synthase विजयी। माrgamApi rAga\] GAM  ANdrEw न chaेये chIJANaH।।",
    translation:
      "A king born with royal combination, who is well instructed, who is a scholar, who is endowed with good qualities, and who is victorious, will not be afraid of crossing the ocean.",
    context: "Chapter 10: Raja Yogas. Definition of a true king.",
    chapter: "Chapter 10",
    verseNumber: "Verse 1",
    confidence: 0.95,
    citation: {
      book: "Saravali of Kalyanavarma",
      chapter: "10",
      verse: "1",
      translator: "R. Santhanam",
    },
    relatedYogas: ["raja_yoga_mahalanka", "royal_combinations"],
  },
  {
    id: "bphs-ch30-v15",
    source: "BPHS",
    sanskrit: "योगा फलानि विविक्तं यो नQuantity उदये च राशौ च तेषां मध्ये यदृच्छया योगो जायते।",
    translation:
      "The results of yogas are manifold according as they arise in the kendras, the trikonas, or elsewhere, and also depending on the strength of the planets.",
    context: "Chapter 30: Yogas. General principle of yoga formation.",
    chapter: "Chapter 30",
    verseNumber: "Verse 15",
    confidence: 0.92,
    citation: {
      book: "Brihat Parashara Hora Shastra",
      chapter: "30",
      verse: "15",
    },
    relatedYogas: ["general_yoga_principle"],
  },
  {
    id: "phaladeepika-ch3-v12",
    source: "Phaladeepika",
    sanskrit: "गुणैर्भागैर्वित्युभिः पुत्रलाभः श्रrixel शुभैर्देह उपगतैर्बुधैश्च। मार्गे शुभ nelleकरणं कुLet is going to reach जन्मतः परमभाग्यमात्रं वा॥",
    translation:
      "If all benefics are in the 10th from the 9th and the 9th is occupied by its lord, or if the lord of the 9th is in a kendra with the lord of the ascendant, there will be good fortune, happiness, and acquisition of progeny.",
    context: "Chapter 3: The 9th House. Fortune and dharma.",
    chapter: "Chapter 3",
    verseNumber: "Verse 12",
    confidence: 0.88,
    relatedYogas: ["dharma_yoga", "ninth_house_fortune"],
  },
  {
    id: "bphs-ch38-v4",
    source: "BPHS",
    sanskrit: "अपराजित讪ेक长发 योगो नाम महायोगो योगानां मुखी दुःखिनी न Śuddhiर कदा धनं येन चला शक्ति স্তুति गृहीतः शुभैर�ဋ न केन्द्रे।",
    translation:
      "There is a great yoga called Aparajita. If the lord of the 10th is in the 10th, or if the lord of the 9th is in the 9th, or if the lord of the 8th is in the 8th, then this yoga arises.",
    context: "Chapter 38: Aparajita Yoga. One of the Panch Mahapurusha yogas.",
    chapter: "Chapter 38",
    verseNumber: "Verse 4",
    confidence: 0.99,
    relatedYogas: ["aparajita_yoga", "panch_mahapurusha"],
  },
];

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

export default function ClassicalLiteratureView({
  initialVerseId,
  onVerseSelect,
}: ClassicalLiteratureViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSource, setSelectedSource] = useState<string>("all");
  const [selectedVerse, setSelectedVerse] = useState<Verse | null>(
    initialVerseId
      ? SAMPLE_VERSES.find((v) => v.id === initialVerseId) || null
      : null,
  );

  // Filter verses
  const filteredVerses = useMemo(() => {
    return SAMPLE_VERSES.filter((verse) => {
      const matchesSearch =
        searchQuery === "" ||
        verse.sanskrit.toLowerCase().includes(searchQuery.toLowerCase()) ||
        verse.translation.toLowerCase().includes(searchQuery.toLowerCase()) ||
        verse.context.toLowerCase().includes(searchQuery.toLowerCase()) ||
        verse.id.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesSource =
        selectedSource === "all" || verse.source === selectedSource;
      return matchesSearch && matchesSource;
    });
  }, [searchQuery, selectedSource]);

  const handleVerseSelect = (verse: Verse) => {
    setSelectedVerse(verse);
    onVerseSelect?.(verse);
  };

  return (
    <div className="flex h-full flex-col">
      {/* ── Header ── */}
      <div
        className="border-b px-4 py-3"
        style={{ borderColor: "var(--obsidian-border)" }}
      >
        <div className="flex items-center justify-between">
          <div>
            <h1
              className="text-base font-bold"
              style={{ color: "var(--obsidian-text-primary)" }}
            >
              Classical Literature
            </h1>
            <p
              className="mt-0.5 text-xs"
              style={{ color: "var(--obsidian-text-muted)" }}
            >
              BPHS · Saravali · Key Sanskrit Slokas with Translations
            </p>
          </div>
          <div className="text-right text-xs" style={{ color: "var(--obsidian-text-muted)" }}>
            {filteredVerses.length} verse{filteredVerses.length !== 1 ? "s" : ""}
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* ── Left: Verse Catalog ── */}
        <div
          className="w-80 overflow-y-auto border-r"
          style={{ borderColor: "var(--obsidian-border)" }}
        >
          {/* Filters */}
          <div className="sticky top-0 border-b p-3" style={{ borderColor: "var(--obsidian-border)", backgroundColor: "var(--obsidian-surface)" }}>
            <input
              type="text"
              placeholder="Search slokas, translations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="mb-2 w-full rounded-md border px-2.5 py-1.5 text-xs"
              style={{
                borderColor: "var(--obsidian-border)",
                backgroundColor: "var(--obsidian-canvas)",
                color: "var(--obsidian-text-primary)",
              }}
            />
            <div className="flex gap-1">
              <select
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
                className="flex-1 rounded border bg-[var(--bg-card)] px-2 py-1 text-xs"
                style={{ borderColor: "var(--obsidian-border)", color: "var(--obsidian-text-primary)" }}
              >
                <option value="all">All Sources</option>
                {SOURCES.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.id}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Verse List */}
          <div className="divide-y" style={{ borderColor: "var(--obsidian-border)" }}>
            {filteredVerses.map((verse) => (
              <button
                key={verse.id}
                onClick={() => handleVerseSelect(verse)}
                className="w-full px-3 py-2 text-left hover:bg-[var(--obsidian-surface-hover)] transition-colors"
                style={{
                  backgroundColor:
                    selectedVerse?.id === verse.id
                      ? "rgba(6, 207, 255, 0.08)"
                      : undefined,
                  borderLeft:
                    selectedVerse?.id === verse.id
                      ? "2px solid var(--obsidian-accent-primary)"
                      : "2px solid transparent",
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className="rounded px-1 text-[10px] font-bold uppercase"
                        style={{
                          backgroundColor:
                            verse.source === "BPHS"
                              ? "rgba(245, 158, 11, 0.15)"
                              : verse.source === "Saravali"
                                ? "rgba(139, 92, 246, 0.15)"
                                : "rgba(107, 114, 128, 0.15)",
                          color:
                            verse.source === "BPHS"
                              ? "#F59E0B"
                              : verse.source === "Saravali"
                                ? "#8B5CF6"
                                : "var(--obsidian-text-secondary)",
                        }}
                      >
                        {verse.source}
                      </span>
                      <span
                        className="text-[10px]"
                        style={{ color: "var(--obsidian-text-muted)" }}
                      >
                        {verse.chapter} · {verse.verseNumber}
                      </span>
                    </div>
                    <p
                      className="mt-1 line-clamp-2 text-xs"
                      style={{ color: "var(--obsidian-text-secondary)" }}
                    >
                      {verse.translation.slice(0, 100)}...
                    </p>
                    {verse.confidence && (
                      <div className="mt-1 flex items-center gap-1">
                        <div className="h-1 w-12 rounded-full bg-gray-700 overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${verse.confidence * 100}%`,
                              backgroundColor:
                                verse.confidence > 0.9
                                  ? "#22C55E"
                                  : verse.confidence > 0.75
                                    ? "#06CFFF"
                                    : "#F59E0B",
                            }}
                          />
                        </div>
                        <span
                          className="text-[10px]"
                          style={{ color: "var(--obsidian-text-muted)" }}
                        >
                          {Math.round(verse.confidence * 100)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </button>
            ))}
            {filteredVerses.length === 0 && (
              <div
                className="px-3 py-6 text-center text-sm"
                style={{ color: "var(--obsidian-text-muted)" }}
              >
                No verses found. Try another search term.
              </div>
            )}
          </div>
        </div>

        {/* ── Right: Verse Detail ── */}
        <div className="flex-1 overflow-y-auto p-4">
          {selectedVerse ? (
            <div className="mx-auto max-w-2xl">
              {/* Header */}
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className="rounded px-2 py-0.5 text-xs font-bold uppercase"
                      style={{
                        backgroundColor:
                          selectedVerse.source === "BPHS"
                            ? "rgba(245, 158, 11, 0.15)"
                            : selectedVerse.source === "Saravali"
                              ? "rgba(139, 92, 246, 0.15)"
                              : "rgba(107, 114, 128, 0.15)",
                        color:
                          selectedVerse.source === "BPHS"
                            ? "#F59E0B"
                            : selectedVerse.source === "Saravali"
                              ? "#8B5CF6"
                              : "var(--obsidian-text-secondary)",
                      }}
                    >
                      {selectedVerse.source}
                    </span>
                    <span
                      className="text-xs"
                      style={{ color: "var(--obsidian-text-muted)" }}
                    >
                      {selectedVerse.chapter} · {selectedVerse.verseNumber}
                    </span>
                  </div>
                  <h2
                    className="mt-2 text-lg font-bold"
                    style={{ color: "var(--obsidian-text-primary)" }}
                  >
                    {selectedVerse.context}
                  </h2>
                  {selectedVerse.confidence && (
                    <div className="mt-2 flex items-center gap-2">
                      <span className="text-xs" style={{ color: "var(--obsidian-text-muted)" }}>
                        AI Confidence:
                      </span>
                      <div className="h-1.5 flex-1 max-w-xs rounded-full bg-gray-700 overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${selectedVerse.confidence * 100}%`,
                            backgroundColor:
                              selectedVerse.confidence > 0.9
                                ? "#22C55E"
                                : selectedVerse.confidence > 0.75
                                  ? "#06CFFF"
                                  : "#F59E0B",
                          }}
                        />
                      </div>
                      <span
                        className="text-xs font-medium"
                        style={{ color: "var(--obsidian-text-secondary)" }}
                      >
                        {Math.round(selectedVerse.confidence * 100)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Sanskrit */}
              <div
                className="mb-4 rounded-lg p-4"
                style={{
                  backgroundColor: "var(--obsidian-surface)",
                  border: "1px solid var(--obsidian-border)",
                }}
              >
                <div
                  className="mb-2 text-xs uppercase tracking-wider"
                  style={{ color: "var(--obsidian-text-muted)" }}
                >
                  Sanskrit
                </div>
                <p
                  className="font-serif text-lg leading-relaxed"
                  style={{
                    color: "var(--obsidian-text-primary)",
                    fontFamily:
                      'var(--font-noto-serif), "Georgia", serif',
                  }}
                >
                  {selectedVerse.sanskrit}
                </p>
              </div>

              {/* Translation */}
              <div
                className="mb-4 rounded-lg p-4"
                style={{
                  backgroundColor: "var(--obsidian-canvas)",
                  border: "1px solid var(--obsidian-border)",
                }}
              >
                <div
                  className="mb-2 text-xs uppercase tracking-wider"
                  style={{ color: "var(--obsidian-text-muted)" }}
                >
                  Translation
                </div>
                <p
                  className="text-sm leading-relaxed"
                  style={{ color: "var(--obsidian-text-secondary)" }}
                >
                  {selectedVerse.translation}
                </p>
              </div>

              {/* Citation */}
              {selectedVerse.citation && (
                <div
                  className="mb-4 rounded-lg p-3 text-sm"
                  style={{
                    backgroundColor: "rgba(107, 114, 128, 0.1)",
                    border: "1px dashed var(--obsidian-border)",
                  }}
                >
                  <div
                    className="mb-1 text-xs uppercase tracking-wider"
                    style={{ color: "var(--obsidian-text-muted)" }}
                  >
                    Citation
                  </div>
                  <p style={{ color: "var(--obsidian-text-secondary)" }}>
                    {selectedVerse.citation.translator && (
                      <>Tr. {selectedVerse.citation.translator} · </>
                    )}
                    {selectedVerse.citation.book} {selectedVerse.citation.chapter}
                    .{selectedVerse.citation.verse}
                  </p>
                </div>
              )}

              {/* Related Yogas */}
              {selectedVerse.relatedYogas && selectedVerse.relatedYogas.length > 0 && (
                <div>
                  <div
                    className="mb-2 text-xs uppercase tracking-wider"
                    style={{ color: "var(--obsidian-text-muted)" }}
                  >
                    Related Yogas
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedVerse.relatedYogas.map((yogaId) => (
                      <span
                        key={yogaId}
                        className="rounded px-2 py-1 text-xs font-mono"
                        style={{
                          backgroundColor: "var(--obsidian-surface)",
                          color: "var(--obsidian-accent-primary)",
                          border: "1px solid var(--obsidian-border)",
                        }}
                      >
                        {yogaId}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex h-full flex-col items-center justify-center text-center p-8">
              <svg
                width="64"
                height="64"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1"
                className="mb-4 opacity-20"
                style={{ color: "var(--obsidian-accent-primary)" }}
              >
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
              </svg>
              <h3
                className="text-base font-semibold"
                style={{ color: "var(--obsidian-text-primary)" }}
              >
                Select a Sloka
              </h3>
              <p
                className="mt-1 max-w-md text-sm"
                style={{ color: "var(--obsidian-text-muted)" }}
              >
                Choose a verse from the catalog on the left to view its Sanskrit text, translation, and related astrological combinations.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
