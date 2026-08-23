"use client";

import { Suspense, useMemo, useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Badge, Card, KpiCard, Select, Table, Tabs } from "@/components/ui";
import { NakshatraArchitectureBanner } from "@/components/nakshatra/NakshatraArchitectureBanner";
import {
  NAKSHATRAS,
  NAKSHATRA_LORD_ORDER,
  VIMSHOTTARI_YEARS,
  TARA_CATEGORIES,
  TARA_FAVORABLE,
  TARA_DESCRIPTIONS,
  GANA_LABELS,
  NADI_LABELS,
  YONI_LABELS,
  PLANET_SYMBOLS,
  PLANET_KARAKATVAS,
  calculateTaraBala,
  calculateTaraMatrix,
  calculateVimshottari,
  calculateAntardashas,
  analyzePlanetNakshatra,
  getNakshatraByName,
  getNakshatrasByLord,
  checkSpecialRules,
  GANDANTA_NAKSHATRAS,
  TRIPADI_NAKSHATRAS,
  DEVA_NAKSHATRAS,
  YAMA_NAKSHATRAS,
  type NakshatraDef,
} from "@/lib/nakshatra";

export const dynamic = "force-dynamic";

type TabId =
  | "overview"
  | "natal"
  | "planetary"
  | "lagna-moon"
  | "pada"
  | "tara"
  | "dasha"
  | "transit"
  | "muhurta"
  | "special"
  | "namakshara"
  | "combined";

const TABS: { key: TabId; label: string }[] = [
  { key: "overview", label: "01 Overview" },
  { key: "natal", label: "02 Natal" },
  { key: "planetary", label: "03 Planetary" },
  { key: "lagna-moon", label: "04 Lagna & Moon" },
  { key: "pada", label: "05 Pada / Navamsha" },
  { key: "tara", label: "06 Tara Bala" },
  { key: "dasha", label: "07 Lords & Dasha" },
  { key: "transit", label: "08 Transit" },
  { key: "muhurta", label: "09 Muhurta" },
  { key: "special", label: "10 Special Rules" },
  { key: "namakshara", label: "11 Namakshara" },
  { key: "combined", label: "12 Combined Analysis" },
];

// ── Helper Components ──────────────────────────────────────────────────────────

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4">
      <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
        {title}
      </h2>
      {subtitle && (
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          {subtitle}
        </p>
      )}
    </div>
  );
}

function NakshatraCard({ nak, onSelect }: { nak: NakshatraDef; onSelect?: (n: NakshatraDef) => void }) {
  const c = nak.classifications;
  return (
    <div
      className="cursor-pointer transition-all hover:-translate-y-0.5"
      onClick={() => onSelect?.(nak)}
    >
      <Card
        style={{ padding: "var(--space-3)", display: "flex", flexDirection: "column", gap: 8 }}
      >
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              {nak.sequence_number}. {nak.name}
            </span>
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
              {nak.devanagari}
            </span>
          </div>
          <p className="mt-0.5 text-xs italic" style={{ color: "var(--text-secondary)" }}>
            {nak.meaning}
          </p>
        </div>
        <Badge tone="gold">{nak.nakshatra_lord}</Badge>
      </div>

      <div className="flex flex-wrap gap-1">
        <Badge tone="cyan">{c.gana}</Badge>
        <Badge tone="violet">{c.yoni}</Badge>
        <Badge tone="neutral">{c.nadi}</Badge>
        {c.gandanta && <Badge tone="danger">Gandanta</Badge>}
        {c.tripadi && <Badge tone="gold">Tripadi</Badge>}
      </div>

        <div className="flex items-center justify-between text-xs" style={{ color: "var(--text-muted)" }}>
          <span>{nak.zodiac_start.toFixed(1)}° – {nak.zodiac_end.toFixed(1)}°</span>
          <span>{nak.deity}</span>
        </div>
      </Card>
    </div>
  );
}

// ── Tab Components ─────────────────────────────────────────────────────────────

function OverviewTab({ onSelect }: { onSelect: (n: NakshatraDef) => void }) {
  const [filter, setFilter] = useState("");
  const [lordFilter, setLordFilter] = useState("");

  const filtered = useMemo(() => {
    return NAKSHATRAS.filter((n) => {
      const matchesSearch =
        !filter ||
        n.name.toLowerCase().includes(filter.toLowerCase()) ||
        n.devanagari.includes(filter) ||
        n.nakshatra_lord.toLowerCase().includes(filter.toLowerCase());
      const matchesLord = !lordFilter || n.nakshatra_lord === lordFilter;
      return matchesSearch && matchesLord;
    });
  }, [filter, lordFilter]);

  return (
    <div>
      <SectionHeader
        title="27 Nakshatras Overview"
        subtitle="Complete reference of all 27 lunar mansions with lords, deities, classifications, and padas"
      />

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Total Nakshatras" value="27" accent="cyan" />
        <KpiCard label="Total Padas" value="108" accent="gold" />
        <KpiCard label="Nakshatra Lords" value="9" accent="violet" />
        <KpiCard label="Gandanta" value={String(GANDANTA_NAKSHATRAS.length)} accent="violet" />
      </div>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="flex-1">
          <input
            type="search"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Search nakshatra, deity, or lord..."
            className="obsidian-input"
            aria-label="Search nakshatras"
          />
        </div>
        <div className="sm:w-48">
          <Select
            label="Filter by Lord"
            value={lordFilter}
            onChange={setLordFilter}
            placeholder="All lords"
            options={[{ value: "", label: "All lords" }, ...NAKSHATRA_LORD_ORDER.map((l) => ({ value: l, label: l }))]}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((nak) => (
          <NakshatraCard key={nak.id} nak={nak} onSelect={onSelect} />
        ))}
      </div>

      {filtered.length === 0 && (
        <Card style={{ padding: "2rem", textAlign: "center" }}>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            No nakshatras match your search.
          </p>
        </Card>
      )}
    </div>
  );
}

function NatalTab({ selectedNak, onSelect }: { selectedNak: NakshatraDef | null; onSelect: (n: NakshatraDef) => void }) {
  const [selectedName, setSelectedName] = useState(selectedNak?.name ?? "Ashwini");
  const nak = getNakshatraByName(selectedName) ?? NAKSHATRAS[0];

  return (
    <div>
      <SectionHeader
        title="Natal Nakshatra Analysis"
        subtitle="Deep dive into a single nakshatra's complete profile — position, structure, relations, and context"
      />

      <div className="mb-4 max-w-xs">
        <Select
          label="Select Nakshatra"
          value={nak.name}
          onChange={(v) => {
            setSelectedName(v);
            const found = getNakshatraByName(v);
            if (found) onSelect(found);
          }}
          options={NAKSHATRAS.map((n) => ({ value: n.name, label: `${n.sequence_number}. ${n.name}` }))}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card style={{ padding: "var(--space-4)" }}>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
              {nak.name} <span style={{ color: "var(--text-muted)" }}>{nak.devanagari}</span>
            </h3>
            <Badge tone="gold">{nak.nakshatra_lord}</Badge>
          </div>

          <p className="mb-3 text-sm italic" style={{ color: "var(--text-secondary)" }}>
            {nak.meaning}
          </p>

          <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Zodiac Range</span>
              <span style={{ color: "var(--text-primary)" }}>{nak.zodiac_start.toFixed(1)}° – {nak.zodiac_end.toFixed(1)}°</span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Yoga Tara</span>
              <span style={{ color: "var(--text-primary)" }}>{nak.yoga_tara}</span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Symbol</span>
              <span style={{ color: "var(--text-primary)" }}>{nak.symbol}</span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Deity</span>
              <span style={{ color: "var(--text-primary)" }}>{nak.deity}</span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Shakti</span>
              <span style={{ color: "var(--text-primary)" }}>{nak.shakti}</span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Namaksharas</span>
              <span style={{ color: "var(--text-primary)" }}>{nak.namakshara.join(", ")}</span>
            </div>
          </div>

          <p className="mt-3 text-sm" style={{ color: "var(--text-secondary)" }}>
            {nak.deity_description}
          </p>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-base font-semibold" style={{ color: "var(--text-primary)" }}>
            Classifications
          </h3>
          <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Gana</span>
              <span style={{ color: "var(--text-primary)" }}>{GANA_LABELS[nak.classifications.gana] ?? nak.classifications.gana}</span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Yoni</span>
              <span style={{ color: "var(--text-primary)" }}>{YONI_LABELS[nak.classifications.yoni] ?? nak.classifications.yoni}</span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Nadi</span>
              <span style={{ color: "var(--text-primary)" }}>{NADI_LABELS[nak.classifications.nadi] ?? nak.classifications.nadi}</span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Varna</span>
              <span style={{ color: "var(--text-primary)" }}>{nak.classifications.varna}</span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Vashya</span>
              <span style={{ color: "var(--text-primary)" }}>{nak.classifications.vashya}</span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Tatva</span>
              <span style={{ color: "var(--text-primary)" }}>{nak.classifications.tatva}</span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Deva/Yama</span>
              <span style={{ color: "var(--text-primary)" }}>{nak.classifications.deva_yama}</span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Gandanta</span>
              <span style={{ color: nak.classifications.gandanta ? "var(--danger-400)" : "var(--success-400)" }}>
                {nak.classifications.gandanta ? "Yes" : "No"}
              </span>
            </div>
            <div>
              <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Tripadi</span>
              <span style={{ color: nak.classifications.tripadi ? "var(--gold-400)" : "var(--text-primary)" }}>
                {nak.classifications.tripadi ? "Yes" : "No"}
              </span>
            </div>
          </div>

          <div className="mt-4">
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
              Karakatvas
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {nak.karakatvas.map((k) => (
                <Badge key={k} tone="cyan">{k}</Badge>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
              Compatibility
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {nak.compatible.map((c) => (
                <Badge key={c} tone="success">{c}</Badge>
              ))}
              {nak.incompatible.map((c) => (
                <Badge key={c} tone="danger">{c}</Badge>
              ))}
            </div>
          </div>
        </Card>
      </div>

      <div className="mt-4">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-base font-semibold" style={{ color: "var(--text-primary)" }}>
            Padas & Navamsha Mapping
          </h3>
          <Table
            columns={[
              { key: "pada", label: "Pada" },
              { key: "range", label: "Degree Range" },
              { key: "navamsha", label: "Navamsha (D9)" },
              { key: "lord", label: "Navamsha Lord" },
              { key: "namakshara", label: "Namakshara" },
            ]}
            rows={nak.padas.map((p) => ({
              pada: `Pada ${p.pada}`,
              range: `${p.start_degree.toFixed(1)}° – ${p.end_degree.toFixed(1)}°`,
              navamsha: p.navamsha,
              lord: p.navamsha_lord,
              namakshara: nak.namakshara[p.pada - 1] ?? "—",
            }))}
          />
        </Card>
      </div>
    </div>
  );
}

function PlanetaryTab() {
  // Sample planetary positions for demonstration — in production these come from the chart API
  const samplePlanets = useMemo(() => {
    const positions: { planet: string; longitude: number; bhava: number }[] = [
      { planet: "Sun", longitude: 14.67, bhava: 1 },
      { planet: "Moon", longitude: 93.33, bhava: 4 },
      { planet: "Mars", longitude: 53.33, bhava: 2 },
      { planet: "Mercury", longitude: 26.67, bhava: 1 },
      { planet: "Jupiter", longitude: 200, bhava: 7 },
      { planet: "Venus", longitude: 173.33, bhava: 6 },
      { planet: "Saturn", longitude: 306.67, bhava: 11 },
      { planet: "Rahu", longitude: 66.67, bhava: 3 },
      { planet: "Ketu", longitude: 246.67, bhava: 9 },
    ];
    return positions.map((p) => analyzePlanetNakshatra(p.planet, p.longitude, p.bhava, "Ashwini"));
  }, []);

  return (
    <div>
      <SectionHeader
        title="Planetary Nakshatra Analysis"
        subtitle="Complete analytical chain for every planet: Planet → Rashi → Nakshatra → Pada → Lord → Navamsha → Bhava"
      />

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Planets Analyzed" value="9" accent="cyan" />
        <KpiCard label="Gandanta Positions" value={String(samplePlanets.filter((p) => p.gandanta).length)} accent="violet" />
        <KpiCard label="Tripadi Positions" value={String(samplePlanets.filter((p) => p.tripadi).length)} accent="gold" />
        <KpiCard label="Favorable Tara" value={String(samplePlanets.filter((p) => p.tara_bala.favorable).length)} accent="success" />
      </div>

      <div className="grid grid-cols-1 gap-3">
        {samplePlanets.map((p) => (
          <Card key={p.planet} style={{ padding: "var(--space-3)" }}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="text-xl" style={{ color: "var(--gold-400)" }} aria-hidden="true">
                  {PLANET_SYMBOLS[p.planet]}
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                      {p.planet}
                    </span>
                    <Badge tone="cyan">{p.rashi}</Badge>
                    <Badge tone="neutral">House {p.bhava}</Badge>
                  </div>
                  <p className="mt-0.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {p.longitude.toFixed(2)}° sidereal · {p.rashi_degree.toFixed(2)}° in {p.rashi}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-1.5">
                <Badge tone="gold">{p.nakshatra}</Badge>
                <Badge tone="violet">Pada {p.pada}</Badge>
                <Badge tone="neutral">Lord: {p.nakshatra_lord}</Badge>
                <Badge tone="cyan">D9: {p.navamsha}</Badge>
                <Badge tone="neutral">D9 Lord: {p.navamsha_lord}</Badge>
                {p.gandanta && <Badge tone="danger">Gandanta</Badge>}
                {p.tripadi && <Badge tone="gold">Tripadi</Badge>}
              </div>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold tracking-wider text-slate-800 dark:text-slate-200 uppercase">Total Nakshatras</span>
              <Badge tone={p.tara_bala.favorable ? "success" : "danger"}>
                {p.tara_bala.category} {p.tara_bala.favorable ? "✓" : "✗"}
              </Badge>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                Mahadasha: {p.dasha.mahadasha} · Antardasha: {p.dasha.antardasha}
              </span>
            </div>

            <p className="mt-2 text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              {p.interpretation}
            </p>
          </Card>
        ))}
      </div>
    </div>
  );
}

function LagnaMoonTab() {
  const [lagnaNak, setLagnaNak] = useState("Ashwini");
  const [moonNak, setMoonNak] = useState("Pushya");

  const lagna = getNakshatraByName(lagnaNak) ?? NAKSHATRAS[0];
  const moon = getNakshatraByName(moonNak) ?? NAKSHATRAS[7];
  const tara = calculateTaraBala(moonNak, lagnaNak);

  return (
    <div>
      <SectionHeader
        title="Lagna & Moon Nakshatra Deep Dive"
        subtitle="Analyze the relationship between the Ascendant and Moon nakshatras — the two most important points in the chart"
      />

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Select
          label="Lagna Nakshatra"
          value={lagnaNak}
          onChange={setLagnaNak}
          options={NAKSHATRAS.map((n) => ({ value: n.name, label: `${n.sequence_number}. ${n.name}` }))}
        />
        <Select
          label="Moon Nakshatra"
          value={moonNak}
          onChange={setMoonNak}
          options={NAKSHATRAS.map((n) => ({ value: n.name, label: `${n.sequence_number}. ${n.name}` }))}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Lagna — {lagna.name}
          </h3>
          <div className="space-y-1 text-sm">
            <p style={{ color: "var(--text-secondary)" }}>Lord: <span style={{ color: "var(--text-primary)" }}>{lagna.nakshatra_lord}</span></p>
            <p style={{ color: "var(--text-secondary)" }}>Deity: <span style={{ color: "var(--text-primary)" }}>{lagna.deity}</span></p>
            <p style={{ color: "var(--text-secondary)" }}>Gana: <span style={{ color: "var(--text-primary)" }}>{GANA_LABELS[lagna.classifications.gana]}</span></p>
            <p style={{ color: "var(--text-secondary)" }}>Yoni: <span style={{ color: "var(--text-primary)" }}>{YONI_LABELS[lagna.classifications.yoni]}</span></p>
            <p style={{ color: "var(--text-secondary)" }}>Nadi: <span style={{ color: "var(--text-primary)" }}>{NADI_LABELS[lagna.classifications.nadi]}</span></p>
          </div>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Moon — {moon.name}
          </h3>
          <div className="space-y-1 text-sm">
            <p style={{ color: "var(--text-secondary)" }}>Lord: <span style={{ color: "var(--text-primary)" }}>{moon.nakshatra_lord}</span></p>
            <p style={{ color: "var(--text-secondary)" }}>Deity: <span style={{ color: "var(--text-primary)" }}>{moon.deity}</span></p>
            <p style={{ color: "var(--text-secondary)" }}>Gana: <span style={{ color: "var(--text-primary)" }}>{GANA_LABELS[moon.classifications.gana]}</span></p>
            <p style={{ color: "var(--text-secondary)" }}>Yoni: <span style={{ color: "var(--text-primary)" }}>{YONI_LABELS[moon.classifications.yoni]}</span></p>
            <p style={{ color: "var(--text-secondary)" }}>Nadi: <span style={{ color: "var(--text-primary)" }}>{NADI_LABELS[moon.classifications.nadi]}</span></p>
          </div>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Tara Relationship
          </h3>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge tone={tara.favorable ? "success" : "danger"}>{tara.category}</Badge>
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {tara.favorable ? "Favorable" : "Unfavorable"}
              </span>
            </div>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              {tara.description}
            </p>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              From Moon ({moon.name}) to Lagna ({lagna.name})
            </p>
          </div>
        </Card>
      </div>

      <div className="mt-4">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Chart Impact Analysis
          </h3>
          <div className="space-y-2 text-sm">
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Lagna Lord ({lagna.nakshatra_lord})</span> in {lagna.name} — the Ascendant's nakshatra lord shapes the native's core personality, physical constitution, and life direction.
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Moon Lord ({moon.nakshatra_lord})</span> in {moon.name} — the Moon's nakshatra governs the mind, emotional nature, and the Vimshottari Dasha sequence.
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Tara Bala: {tara.category}</span> — {tara.description}. This relationship between Lagna and Moon nakshatras indicates {tara.favorable ? "harmony and support between the self and the mind" : "tension or challenge between the self and the mind"}.
            </p>
            {lagna.classifications.gana === moon.classifications.gana ? (
              <p style={{ color: "var(--text-secondary)" }}>
                <span className="font-medium" style={{ color: "var(--success-400)" }}>Same Gana ({GANA_LABELS[lagna.classifications.gana]})</span> — compatible temperament between Lagna and Moon.
              </p>
            ) : (
              <p style={{ color: "var(--text-secondary)" }}>
                <span className="font-medium" style={{ color: "var(--warning-400)" }}>Different Gana</span> — {GANA_LABELS[lagna.classifications.gana]} (Lagna) vs {GANA_LABELS[moon.classifications.gana]} (Moon) — potential temperamental differences.
              </p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function PadaTab() {
  const [selectedNak, setSelectedNak] = useState("Ashwini");
  const nak = getNakshatraByName(selectedNak) ?? NAKSHATRAS[0];

  return (
    <div>
      <SectionHeader
        title="Pada / Navamsha Detail View"
        subtitle="All 108 padas with their Navamsha (D9) mappings, lords, and namaksharas"
      />

      <div className="mb-4 max-w-xs">
        <Select
          label="Select Nakshatra"
          value={nak.name}
          onChange={setSelectedNak}
          options={NAKSHATRAS.map((n) => ({ value: n.name, label: `${n.sequence_number}. ${n.name}` }))}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            {nak.name} — Padas & Navamsha
          </h3>
          <Table
            columns={[
              { key: "pada", label: "Pada" },
              { key: "range", label: "Range" },
              { key: "navamsha", label: "Navamsha" },
              { key: "lord", label: "Lord" },
              { key: "namakshara", label: "Namakshara" },
            ]}
            rows={nak.padas.map((p) => ({
              pada: `Pada ${p.pada}`,
              range: `${p.start_degree.toFixed(1)}° – ${p.end_degree.toFixed(1)}°`,
              navamsha: p.navamsha,
              lord: p.navamsha_lord,
              namakshara: nak.namakshara[p.pada - 1] ?? "—",
            }))}
          />
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Navamsha Lord Analysis
          </h3>
          <div className="space-y-3">
            {nak.padas.map((p) => {
              const karakatvas = PLANET_KARAKATVAS[p.navamsha_lord] ?? [];
              return (
                <div key={p.pada} className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                      Pada {p.pada} → {p.navamsha}
                    </span>
                    <Badge tone="gold">{p.navamsha_lord}</Badge>
                  </div>
                  <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {p.navamsha_lord} rules {p.navamsha}. Karakatvas: {karakatvas.slice(0, 4).join(", ")}
                  </p>
                </div>
              );
            })}
          </div>
        </Card>
      </div>
    </div>
  );
}

function TaraTab() {
  const [birthNak, setBirthNak] = useState("Ashwini");
  const matrix = useMemo(() => calculateTaraMatrix(birthNak), [birthNak]);

  return (
    <div>
      <SectionHeader
        title="Tara Bala Matrix"
        subtitle="The 9-fold Tara relationship from the birth (Janma) nakshatra to all 27 nakshatras"
      />

      <div className="mb-4 max-w-xs">
        <Select
          label="Birth (Janma) Nakshatra"
          value={birthNak}
          onChange={setBirthNak}
          options={NAKSHATRAS.map((n) => ({ value: n.name, label: `${n.sequence_number}. ${n.name}` }))}
        />
      </div>

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3 lg:grid-cols-9">
        {TARA_CATEGORIES.map((cat) => (
          <KpiCard
            key={cat}
            label={cat}
            value={String(matrix.filter((m) => m.tara.category === cat).length)}
            accent={TARA_FAVORABLE[cat] ? "success" : "violet"}
            caveat={TARA_DESCRIPTIONS[cat]}
          />
        ))}
      </div>

      <Card style={{ padding: "var(--space-4)" }}>
        <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Full Tara Matrix from {birthNak}
        </h3>
        <Table
          columns={[
            { key: "seq", label: "#" },
            { key: "nakshatra", label: "Nakshatra" },
            { key: "lord", label: "Lord" },
            { key: "category", label: "Tara Category" },
            { key: "favorable", label: "Favorable" },
            { key: "description", label: "Description" },
          ]}
          rows={matrix.map((m) => ({
            seq: m.nakshatra.sequence_number,
            nakshatra: m.nakshatra.name,
            lord: m.nakshatra.nakshatra_lord,
            category: m.tara.category,
            favorable: m.tara.favorable ? "✓" : "✗",
            description: m.tara.description,
          }))}
        />
      </Card>
    </div>
  );
}

function DashaTab() {
  const [birthNak, setBirthNak] = useState("Ashwini");
  const [birthDate, setBirthDate] = useState("1990-01-01");
  const [expandedLord, setExpandedLord] = useState<string | null>(null);

  const dasha = useMemo(() => {
    const date = new Date(birthDate);
    return calculateVimshottari(birthNak, date);
  }, [birthNak, birthDate]);

  const lordsByNakshatra = useMemo(() => {
    return NAKSHATRA_LORD_ORDER.map((lord) => ({
      lord,
      years: VIMSHOTTARI_YEARS[lord],
      nakshatras: getNakshatrasByLord(lord),
    }));
  }, []);

  return (
    <div>
      <SectionHeader
        title="Nakshatra Lords & Vimshottari Dasha"
        subtitle="The 9 planetary lords, their nakshatras, and the Vimshottari Dasha timeline"
      />

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Select
          label="Birth Nakshatra"
          value={birthNak}
          onChange={setBirthNak}
          options={NAKSHATRAS.map((n) => ({ value: n.name, label: `${n.sequence_number}. ${n.name}` }))}
        />
        <div>
          <label className="mb-1 block text-sm" style={{ color: "var(--text-secondary)" }}>
            Birth Date
          </label>
          <input
            type="date"
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            className="obsidian-input"
          />
        </div>
      </div>

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3 lg:grid-cols-9">
        {lordsByNakshatra.map((l) => (
          <KpiCard
            key={l.lord}
            label={l.lord}
            value={`${l.years}y`}
            accent={l.lord === dasha.mahadashas[0]?.lord ? "gold" : "cyan"}
            caveat={`${l.nakshatras.length} nakshatras`}
          />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Mahadasha Timeline
          </h3>
          <div className="space-y-2">
            {dasha.mahadashas.map((period) => (
              <div key={period.lord + period.start_date}>
                <button
                  type="button"
                  onClick={() => setExpandedLord(expandedLord === period.lord ? null : period.lord)}
                  className="w-full rounded-lg border p-3 text-left transition"
                  style={{
                    borderColor: expandedLord === period.lord ? "var(--accent)" : "var(--border-primary)",
                    backgroundColor: expandedLord === period.lord ? "var(--bg-card-hover)" : "var(--bg-card)",
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                        {period.lord}
                      </span>
                      <Badge tone="gold">{period.years.toFixed(1)} years</Badge>
                    </div>
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                      {period.start_date} → {period.end_date}
                    </span>
                  </div>
                </button>
                {expandedLord === period.lord && (
                  <div className="mt-2 rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
                      Antardashas
                    </h4>
                    <div className="grid grid-cols-1 gap-1 sm:grid-cols-3">
                      {calculateAntardashas(period).map((sub) => (
                        <div key={sub.lord + sub.start_date} className="rounded p-2" style={{ backgroundColor: "var(--bg-card)" }}>
                          <span className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>
                            {sub.lord}
                          </span>
                          <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>
                            {sub.years.toFixed(2)}y · {sub.start_date} → {sub.end_date}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Nakshatras by Lord
          </h3>
          <div className="space-y-3">
            {lordsByNakshatra.map((l) => (
              <div key={l.lord}>
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {l.lord}
                  </span>
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                    {l.years} years · {l.nakshatras.length} nakshatras
                  </span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {l.nakshatras.map((n) => (
                    <Badge key={n.name} tone={n.name === birthNak ? "gold" : "neutral"}>
                      {n.name}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

function TransitTab() {
  const [moonNak, setMoonNak] = useState("Ashwini");
  const [transitNak, setTransitNak] = useState("Pushya");

  const moon = getNakshatraByName(moonNak) ?? NAKSHATRAS[0];
  const transit = getNakshatraByName(transitNak) ?? NAKSHATRAS[7];
  const tara = calculateTaraBala(moonNak, transitNak);

  return (
    <div>
      <SectionHeader
        title="Transit / Gochara Analysis"
        subtitle="Analyze how transiting planets interact with the natal Moon nakshatra through Tara Bala"
      />

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Select
          label="Natal Moon Nakshatra"
          value={moonNak}
          onChange={setMoonNak}
          options={NAKSHATRAS.map((n) => ({ value: n.name, label: `${n.sequence_number}. ${n.name}` }))}
        />
        <Select
          label="Transit Nakshatra"
          value={transitNak}
          onChange={setTransitNak}
          options={NAKSHATRAS.map((n) => ({ value: n.name, label: `${n.sequence_number}. ${n.name}` }))}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Transit Relationship
          </h3>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge tone={tara.favorable ? "success" : "danger"}>{tara.category}</Badge>
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {tara.favorable ? "Favorable Transit" : "Unfavorable Transit"}
              </span>
            </div>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              {tara.description}
            </p>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              Transit {transit.name} from natal Moon {moon.name}
            </p>
          </div>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Transit Planet Effects
          </h3>
          <div className="space-y-2 text-sm">
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>{transit.name}</span> transiting through {transit.nakshatra_lord}'s nakshatra activates {transit.nakshatra_lord} significations.
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              Deity: {transit.deity} — {transit.deity_description}
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              Karakatvas: {transit.karakatvas.join(", ")}
            </p>
          </div>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Dasha Relationship
          </h3>
          <div className="space-y-2 text-sm">
            <p style={{ color: "var(--text-secondary)" }}>
              Transit lord: <span className="font-medium" style={{ color: "var(--text-primary)" }}>{transit.nakshatra_lord}</span>
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              Natal Moon lord: <span className="font-medium" style={{ color: "var(--text-primary)" }}>{moon.nakshatra_lord}</span>
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              {transit.nakshatra_lord === moon.nakshatra_lord ? (
                <span style={{ color: "var(--success-400)" }}>
                  Same lord — strong activation of the Moon's significations during this transit.
                </span>
              ) : (
                <span>
                  Different lords — {transit.nakshatra_lord} transit activates {transit.nakshatra_lord} themes while {moon.nakshatra_lord} governs the mind.
                </span>
              )}
            </p>
          </div>
        </Card>
      </div>

      <div className="mt-4">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            All Transit Nakshatras from {moon.name}
          </h3>
          <Table
            columns={[
              { key: "seq", label: "#" },
              { key: "nakshatra", label: "Nakshatra" },
              { key: "lord", label: "Lord" },
              { key: "category", label: "Tara" },
              { key: "favorable", label: "Favorable" },
            ]}
            rows={NAKSHATRAS.map((n) => {
              const t = calculateTaraBala(moonNak, n.name);
              return {
                seq: n.sequence_number,
                nakshatra: n.name,
                lord: n.nakshatra_lord,
                category: t.category,
                favorable: t.favorable ? "✓" : "✗",
              };
            })}
          />
        </Card>
      </div>
    </div>
  );
}

function MuhurtaTab() {
  const [janmaNak, setJanmaNak] = useState("Ashwini");
  const [currentNak, setCurrentNak] = useState("Pushya");
  const [activity, setActivity] = useState("Starting a new business");

  const janma = getNakshatraByName(janmaNak) ?? NAKSHATRAS[0];
  const current = getNakshatraByName(currentNak) ?? NAKSHATRAS[7];
  const tara = calculateTaraBala(janmaNak, currentNak);

  const unsuitableActivities = ["travel", "journey", "marriage", "surgery", "starting business"];
  const isSensitive = unsuitableActivities.some((a) => activity.toLowerCase().includes(a));
  const suitable = tara.favorable && !(isSensitive && !tara.favorable);

  return (
    <div>
      <SectionHeader
        title="Muhurta — Auspicious Timing"
        subtitle="Evaluate the suitability of the current nakshatra for a specific activity based on Tara Bala"
      />

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Select
          label="Janma Nakshatra"
          value={janmaNak}
          onChange={setJanmaNak}
          options={NAKSHATRAS.map((n) => ({ value: n.name, label: `${n.sequence_number}. ${n.name}` }))}
        />
        <Select
          label="Current Nakshatra"
          value={currentNak}
          onChange={setCurrentNak}
          options={NAKSHATRAS.map((n) => ({ value: n.name, label: `${n.sequence_number}. ${n.name}` }))}
        />
        <div>
          <label className="mb-1 block text-sm" style={{ color: "var(--text-secondary)" }}>
            Activity
          </label>
          <input
            type="text"
            value={activity}
            onChange={(e) => setActivity(e.target.value)}
            className="obsidian-input"
            placeholder="e.g. Starting a business, Marriage, Travel..."
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Muhurta Evaluation
          </h3>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="text-2xl" style={{ color: suitable ? "var(--success-400)" : "var(--danger-400)" }}>
                {suitable ? "✓" : "✗"}
              </span>
              <div>
                <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  {suitable ? "Auspicious Timing" : "Inauspicious Timing"}
                </p>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  {suitable
                    ? `Favorable for ${activity} — ${tara.category} Tara is auspicious`
                    : `Avoid ${activity} — ${tara.category} Tara is inauspicious`}
                </p>
              </div>
            </div>

            <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Current Nakshatra</span>
                  <span style={{ color: "var(--text-primary)" }}>{current.name}</span>
                </div>
                <div>
                  <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Janma Nakshatra</span>
                  <span style={{ color: "var(--text-primary)" }}>{janma.name}</span>
                </div>
                <div>
                  <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Tara Bala</span>
                  <span style={{ color: tara.favorable ? "var(--success-400)" : "var(--danger-400)" }}>
                    {tara.category}
                  </span>
                </div>
                <div>
                  <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Lord</span>
                  <span style={{ color: "var(--text-primary)" }}>{current.nakshatra_lord}</span>
                </div>
              </div>
            </div>

            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              {tara.description}
            </p>
          </div>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Activity Suitability Guide
          </h3>
          <div className="space-y-2">
            {[
              { activity: "Marriage", suitable: tara.favorable && tara.category !== "Naidhana" },
              { activity: "Starting Business", suitable: tara.favorable && tara.category !== "Vipat" },
              { activity: "Travel / Journey", suitable: tara.favorable && tara.category !== "Pratyari" },
              { activity: "Education / Learning", suitable: tara.favorable },
              { activity: "Medical Treatment", suitable: tara.favorable && tara.category !== "Naidhana" },
              { activity: "Spiritual Practice", suitable: true },
            ].map((item) => (
              <div key={item.activity} className="flex items-center justify-between rounded-lg border p-2.5" style={{ borderColor: "var(--border-primary)" }}>
                <span className="text-sm" style={{ color: "var(--text-primary)" }}>{item.activity}</span>
                <Badge tone={item.suitable ? "success" : "danger"}>
                  {item.suitable ? "Suitable" : "Avoid"}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

function SpecialRulesTab() {
  return (
    <div>
      <SectionHeader
        title="Special Rules — Gandanta, Tripadi, Deva/Yama"
        subtitle="Special classifications and conditions that modify nakshatra interpretations"
      />

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <KpiCard label="Gandanta" value={String(GANDANTA_NAKSHATRAS.length)} accent="violet" caveat="Fire-water junctions" />
        <KpiCard label="Tripadi" value={String(TRIPADI_NAKSHATRAS.length)} accent="gold" caveat="Three-pada nakshatras" />
        <KpiCard label="Deva" value={String(DEVA_NAKSHATRAS.length)} accent="success" caveat="Divine nature" />
        <KpiCard label="Yama" value={String(YAMA_NAKSHATRAS.length)} accent="violet" caveat="Mortal nature" />
        <KpiCard label="Deva Gana" value={String(NAKSHATRAS.filter((n) => n.classifications.gana === "deva").length)} accent="cyan" caveat="Divine temperament" />
        <KpiCard label="Rakshasa Gana" value={String(NAKSHATRAS.filter((n) => n.classifications.gana === "rakshasa").length)} accent="violet" caveat="Demonic temperament" />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Gandanta Nakshatras
          </h3>
          <p className="mb-3 text-xs" style={{ color: "var(--text-secondary)" }}>
            Gandanta points are the junctions between fire and water signs — sensitive transition zones where karmic energy is intense.
          </p>
          <div className="space-y-2">
            {GANDANTA_NAKSHATRAS.map((name) => {
              const nak = getNakshatraByName(name);
              if (!nak) return null;
              return (
                <div key={name} className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                      {nak.name} ({nak.devanagari})
                    </span>
                    <Badge tone="danger">Gandanta</Badge>
                  </div>
                  <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {nak.zodiac_start.toFixed(1)}° – {nak.zodiac_end.toFixed(1)}° · Lord: {nak.nakshatra_lord} · {nak.meaning}
                  </p>
                </div>
              );
            })}
          </div>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Tripadi Nakshatras
          </h3>
          <p className="mb-3 text-xs" style={{ color: "var(--text-secondary)" }}>
            Tripadi nakshatras span only 3 padas (10°) instead of 4, giving them special spiritual significance.
          </p>
          <div className="space-y-2">
            {TRIPADI_NAKSHATRAS.map((name) => {
              const nak = getNakshatraByName(name);
              if (!nak) return null;
              return (
                <div key={name} className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                      {nak.name} ({nak.devanagari})
                    </span>
                    <Badge tone="gold">Tripadi</Badge>
                  </div>
                  <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {nak.zodiac_start.toFixed(1)}° – {nak.zodiac_end.toFixed(1)}° · Lord: {nak.nakshatra_lord} · {nak.meaning}
                  </p>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Deva Nakshatras ({DEVA_NAKSHATRAS.length})
          </h3>
          <p className="mb-3 text-xs" style={{ color: "var(--text-secondary)" }}>
            Divine nakshatras — benefic influence, spiritual nature, and favorable outcomes.
          </p>
          <div className="flex flex-wrap gap-1.5">
            {DEVA_NAKSHATRAS.map((name) => {
              const nak = getNakshatraByName(name);
              return nak ? (
                <Badge key={name} tone="success">{nak.sequence_number}. {name}</Badge>
              ) : null;
            })}
          </div>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Yama Nakshatras ({YAMA_NAKSHATRAS.length})
          </h3>
          <p className="mb-3 text-xs" style={{ color: "var(--text-secondary)" }}>
            Mortal nakshatras — karmic influence, practical nature, and worldly outcomes.
          </p>
          <div className="flex flex-wrap gap-1.5">
            {YAMA_NAKSHATRAS.map((name) => {
              const nak = getNakshatraByName(name);
              return nak ? (
                <Badge key={name} tone="violet">{nak.sequence_number}. {name}</Badge>
              ) : null;
            })}
          </div>
        </Card>
      </div>
    </div>
  );
}

function NamaksharaTab() {
  const [selectedNak, setSelectedNak] = useState("Ashwini");
  const nak = getNakshatraByName(selectedNak) ?? NAKSHATRAS[0];

  return (
    <div>
      <SectionHeader
        title="Namakshara / Avakahada Chakra"
        subtitle="Name syllables (Namaksharas) for each nakshatra pada — used for naming ceremonies and Avakahada Chakra"
      />

      <div className="mb-4 max-w-xs">
        <Select
          label="Select Nakshatra"
          value={nak.name}
          onChange={setSelectedNak}
          options={NAKSHATRAS.map((n) => ({ value: n.name, label: `${n.sequence_number}. ${n.name}` }))}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            {nak.name} — Namaksharas
          </h3>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {nak.padas.map((p) => (
              <div key={p.pada} className="rounded-lg border p-3 text-center" style={{ borderColor: "var(--border-primary)" }}>
                <span className="block text-xs" style={{ color: "var(--text-muted)" }}>Pada {p.pada}</span>
                <span className="mt-1 block text-xl font-bold" style={{ color: "var(--accent)" }}>
                  {nak.namakshara[p.pada - 1] ?? "—"}
                </span>
                <span className="mt-1 block text-[10px]" style={{ color: "var(--text-muted)" }}>
                  {p.start_degree.toFixed(1)}° – {p.end_degree.toFixed(1)}°
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Avakahada Chakra
          </h3>
          <p className="mb-3 text-xs" style={{ color: "var(--text-secondary)" }}>
            The Avakahada Chakra maps each pada to its Namakshara syllable, used in traditional naming ceremonies (Namakarana).
          </p>
          <Table
            columns={[
              { key: "pada", label: "Pada" },
              { key: "namakshara", label: "Namakshara" },
              { key: "navamsha", label: "Navamsha" },
              { key: "lord", label: "Navamsha Lord" },
            ]}
            rows={nak.padas.map((p) => ({
              pada: `Pada ${p.pada}`,
              namakshara: nak.namakshara[p.pada - 1] ?? "—",
              navamsha: p.navamsha,
              lord: p.navamsha_lord,
            }))}
          />
        </Card>
      </div>

      <div className="mt-4">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            All 108 Namaksharas
          </h3>
          <div className="grid grid-cols-2 gap-1 sm:grid-cols-3 lg:grid-cols-6">
            {NAKSHATRAS.map((n) => (
              <div key={n.id} className="rounded border p-2" style={{ borderColor: "var(--border-primary)" }}>
                <span className="block text-xs font-medium" style={{ color: "var(--text-primary)" }}>
                  {n.sequence_number}. {n.name}
                </span>
                <span className="mt-0.5 block text-[10px]" style={{ color: "var(--text-muted)" }}>
                  {n.namakshara.join(" · ")}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

function CombinedTab({ selectedNak }: { selectedNak: NakshatraDef | null }) {
  const nak = selectedNak ?? NAKSHATRAS[0];
  const special = checkSpecialRules(nak.name);
  const tara = calculateTaraBala("Ashwini", nak.name);

  return (
    <div>
      <SectionHeader
        title="Combined Analysis — Full Synthesis"
        subtitle="Synthesizing Position, Lordship, Pada, Bhava, Tara Bala, Dasha, Transit, Special Conditions, and Context"
      />

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Nakshatra" value={nak.name} accent="cyan" caveat={`${nak.devanagari} · ${nak.meaning}`} />
        <KpiCard label="Lord" value={nak.nakshatra_lord} accent="gold" caveat={`Yoga Tara: ${nak.yoga_tara}`} />
        <KpiCard label="Tara Bala" value={tara.category} accent={tara.favorable ? "success" : "violet"} caveat={tara.description} />
        <KpiCard label="Special Rules" value={special.gandanta ? "Gandanta" : special.tripadi ? "Tripadi" : "Standard"} accent={special.gandanta ? "violet" : "violet"} caveat={special.description} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Position & Structure
          </h3>
          <div className="space-y-2 text-sm">
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Position:</span> {nak.zodiac_start.toFixed(1)}° – {nak.zodiac_end.toFixed(1)}° sidereal
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Pada Structure:</span> 4 padas × 3°20' each = 13°20' total
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Navamsha Mapping:</span> {nak.padas.map((p) => `${p.pada}→${p.navamsha}`).join(", ")}
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Deity:</span> {nak.deity} — {nak.deity_description}
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Shakti:</span> {nak.shakti}
            </p>
          </div>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Lordship & Dasha
          </h3>
          <div className="space-y-2 text-sm">
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Nakshatra Lord:</span> {nak.nakshatra_lord} — {VIMSHOTTARI_YEARS[nak.nakshatra_lord]} years in Vimshottari
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Yoga Tara:</span> {nak.yoga_tara}
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Vimshottari Sequence:</span> {NAKSHATRA_LORD_ORDER.join(" → ")}
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Karakatvas:</span> {nak.karakatvas.join(", ")}
            </p>
          </div>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Special Conditions
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Gandanta:</span>
              <Badge tone={special.gandanta ? "danger" : "success"}>{special.gandanta ? "Yes" : "No"}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Tripadi:</span>
              <Badge tone={special.tripadi ? "gold" : "neutral"}>{special.tripadi ? "Yes" : "No"}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Deva/Yama:</span>
              <Badge tone={special.devaYama === "Deva" ? "success" : "violet"}>{special.devaYama}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>Gana:</span>
              <Badge tone="cyan">{GANA_LABELS[special.gana] ?? special.gana}</Badge>
            </div>
            <p className="mt-2 text-xs" style={{ color: "var(--text-secondary)" }}>
              {special.description}
            </p>
          </div>
        </Card>

        <Card style={{ padding: "var(--space-4)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Final Synthesis
          </h3>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{nak.name}</span> ({nak.devanagari}) is the {nak.sequence_number}
            {nak.sequence_number === 1 ? "st" : nak.sequence_number === 2 ? "nd" : nak.sequence_number === 3 ? "rd" : "th"} nakshatra,
            spanning {nak.zodiac_start.toFixed(1)}° to {nak.zodiac_end.toFixed(1)}° of the zodiac. Ruled by{" "}
            <span className="font-semibold" style={{ color: "var(--gold-400)" }}>{nak.nakshatra_lord}</span>,
            its deity is <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{nak.deity}</span>.
            The nakshatra's meaning — "{nak.meaning}" — reflects its core essence.
            {special.gandanta && " This is a Gandanta position, marking a sensitive karmic junction."}
            {special.tripadi && " As a Tripadi nakshatra, it carries special spiritual significance."}
            {" "}Its Tara relationship from Ashwini is <span className="font-semibold" style={{ color: tara.favorable ? "var(--success-400)" : "var(--danger-400)" }}>
              {tara.category}
            </span> ({tara.favorable ? "favorable" : "unfavorable"}).
          </p>
        </Card>
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────

function NakshatraPageContent() {
  const searchParams = useSearchParams();
  const requestedTab = searchParams.get("tab");
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [selectedNak, setSelectedNak] = useState<NakshatraDef | null>(null);

  useEffect(() => {
    if (requestedTab && TABS.some((t) => t.key === requestedTab)) {
      setActiveTab(requestedTab as TabId);
    }
  }, [requestedTab]);

  return (
    <>
      <div className="mb-4">
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Nakshatra Core Engine &amp; Analysis Module
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Foundational calculation layer — 27 nakshatras, 108 padas, 9 lords, Tara Bala, Dasha, Transit, and Muhurta analysis
        </p>
      </div>

      <NakshatraArchitectureBanner />

      <div className="mb-6">
        <Tabs
          tabs={TABS}
          active={activeTab}
          onChange={(key) => setActiveTab(key as TabId)}
        />
      </div>

      <div className="animate-fade-in">
        {activeTab === "overview" && <OverviewTab onSelect={setSelectedNak} />}
        {activeTab === "natal" && <NatalTab selectedNak={selectedNak} onSelect={setSelectedNak} />}
        {activeTab === "planetary" && <PlanetaryTab />}
        {activeTab === "lagna-moon" && <LagnaMoonTab />}
        {activeTab === "pada" && <PadaTab />}
        {activeTab === "tara" && <TaraTab />}
        {activeTab === "dasha" && <DashaTab />}
        {activeTab === "transit" && <TransitTab />}
        {activeTab === "muhurta" && <MuhurtaTab />}
        {activeTab === "special" && <SpecialRulesTab />}
        {activeTab === "namakshara" && <NamaksharaTab />}
        {activeTab === "combined" && <CombinedTab selectedNak={selectedNak} />}
      </div>
    </>
  );
}

export default function NakshatraPage() {
  return (
    <Suspense fallback={null}>
      <NakshatraPageContent />
    </Suspense>
  );
}