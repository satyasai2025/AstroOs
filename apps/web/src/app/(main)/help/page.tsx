"use client";

import { Card } from "@/components/ui";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card>
      <h2 className="mb-2 text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
        {title}
      </h2>
      <div className="space-y-2 text-sm" style={{ color: "var(--text-secondary)" }}>
        {children}
      </div>
    </Card>
  );
}

export default function HelpPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Help &amp; Guide
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          How to read and use the research tools in this app.
        </p>
      </div>

      <Section title="Sarvatobhadra Chakra (/charts/sbc)">
        <p>
          A 9x9 grid with 28 cells around the border — one per nakshatra (including Abhijit). The 4
          corners are unused junction points.
        </p>
        <p>
          <strong>Reading the grid:</strong> each border cell shows the nakshatra&apos;s short name on
          top, and (in blue, bold) which planet(s) are currently transiting that nakshatra below it.
          Interior cells show a plain reference number (CellNum) — real sourced data, not decorative.
        </p>
        <p>
          <strong>Janma element dropdown:</strong> pick the nakshatra you want to check for an active
          Vedha (obstruction/piercing) — usually your natal Moon&apos;s nakshatra, but any of the 28 can
          be checked.
        </p>
        <p>
          <strong>Clicking a cell:</strong> click any border nakshatra to highlight its three Vedha rays
          — green (Front), blue (Left), red (Right) — the same interaction as JHora&apos;s
          &quot;Highlight aspects (vedhas) FROM this star&quot;.
        </p>
        <p>
          <strong>Vedha result panel:</strong> only benefic planets (Jupiter/Venus always; Moon only
          mid-lunar-cycle; Mercury unless sitting with a malefic) cast a ray — the direction is decided
          by that planet&apos;s own speed. &quot;No benefic Vedha hits right now&quot; is a normal,
          common result — it just means no qualifying planet&apos;s ray currently lands on the selected
          nakshatra at this exact moment. Use{" "}
          <code className="rounded px-1" style={{ background: "var(--bg-secondary)" }}>
            POST /api/v1/sbc/scan
          </code>{" "}
          to scan a date range and find every day a hit actually occurs, instead of only checking the
          current instant.
        </p>
      </Section>

      <Section title="Navatara / Tarabala (/charts/tarabala)">
        <p>
          Enter a Janma Nakshatra (your natal Moon&apos;s nakshatra) and birth date/time. Lagna
          Nakshatra and an active dasha chain are optional extras that unlock two more sections.
        </p>
        <p>
          <strong>Special Points table:</strong> a real, separately-sourced 28-nakshatra (Abhijit-
          inclusive) reference table (Janma, Karma, Samudayika, Sanghatika, Jaati, Naidhana, Desa,
          Abhisheka, Aadhana, Vainashika, Manasa) — shows which nakshatra each named point falls on,
          counted from the Moon and (if given) from the Lagna.
        </p>
        <p>
          <strong>Natal / Transit Tarabala tables:</strong> for each of the 9 planets, which of the 9
          Tara categories (Janma/Sampat/Vipat/Kshema/Pratyari/Sadhaka/Naidhana/Mitra/Paramamitra) its
          own natal or current transiting nakshatra falls into, relative to the Janma Nakshatra —
          5 categories are favorable, 4 unfavorable.
        </p>
        <p>
          <strong>Dasha-hierarchy convergence:</strong> if you enter an active dasha chain (e.g.{" "}
          <code className="rounded px-1" style={{ background: "var(--bg-secondary)" }}>
            venus,sun,moon
          </code>
          , Mahadasha first), each level&apos;s ruling lord is checked against its fixed Tara position
          — the count of how many levels are simultaneously favorable is a stronger signal than any
          one level alone.
        </p>
        <p>
          <strong>Yearly Tara:</strong> which of the full 27 uniquely-named year-positions is currently
          running, counted by exact solar-return anniversaries of the birth moment (not calendar
          years).
        </p>
      </Section>

      <Section title="General notes">
        <p>
          These tools compute real classical formulas from sourced references (Saravali, a working SBC
          tool&apos;s own VBA/spreadsheet logic, cross-checked live against JHora where possible) — they
          are not fabricated or approximated for display purposes. Where a source itself is ambiguous or
          unconfirmed, that&apos;s stated directly in the relevant panel or in code comments rather than
          silently picking one answer.
        </p>
        <p>
          A single &quot;clear&quot; or &quot;no hit&quot; result at one moment is normal and expected —
          these are snapshot checks, not predictions. Use the date-range scan (SBC) or check multiple
          reference points together (Tarabala&apos;s convergence count) before treating any single
          result as a strong signal.
        </p>
      </Section>
    </div>
  );
}
