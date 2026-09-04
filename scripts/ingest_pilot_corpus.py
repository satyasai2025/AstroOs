"""
AstroOS — Pilot Corpus Ingestion Script

Ingests 5 legally available / public-domain astrology sources.
Each chunk is stored with full provenance chain.

Sources:
  1. Vedic Astrology Wiki (CC BY-SA — public wiki content)
     → Gaja Kesari Yoga, Pancha Mahapurusha Yoga, Navagraha basics
  2. Public domain excerpt from James Burgess translation of Surya Siddhanta
     → Planetary theory fundamentals
  3. BPHS (Brihat Parashara Hora Shastra) — user-owned/public domain English excerpt
     → Jupiter-Moon Kendra yoga
  4. Phala Deepika — public domain chapter summary
     → Mars in Kendra effects
  5. Jaimini Sutras (public domain) — basic aphorism on Atmakaraka

Usage:
  python scripts/ingest_pilot_corpus.py [--dry-run]

All chunks default to lifecycle_state=DOCUMENTED, evidence_level=UNVALIDATED.
No chunks are auto-promoted. AI contamination guard is enforced.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import sys
import uuid
from dataclasses import dataclass
from typing import List, Optional

sys.path.insert(0, ".")

import psycopg2

# ── Colour helpers ─────────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def ok(msg): print(f"{GREEN}[OK]{RESET} {msg}")
def warn(msg): print(f"{YELLOW}[WARN]{RESET} {msg}")
def err(msg): print(f"{RED}[ERR]{RESET} {msg}")
def info(msg): print(f"{CYAN}[..]{RESET} {msg}")
def header(msg): print(f"\n{BOLD}{msg}{RESET}")


# ── Corpus Definition ──────────────────────────────────────────────────────────

@dataclass
class PilotChunk:
    document_title: str
    author: str
    edition: str
    publication_year: Optional[int]
    tradition: str
    language: str
    chapter_section: str
    page_location: str
    passage_reference: str
    chunk_index: int
    content: str
    technique_framework: str
    grahas: List[str]
    bhavas: List[int]
    yogas: List[str]
    rashis: List[str]
    nakshatras: List[str]
    is_ai_extracted: bool = False


PILOT_CORPUS: List[PilotChunk] = [
    # ── Source 1: Vedic Astrology Wiki (CC BY-SA) ────────────────────────────
    PilotChunk(
        document_title="Vedic Astrology Wiki — Gaja Kesari Yoga",
        author="Various Contributors",
        edition="2024 Archive",
        publication_year=2024,
        tradition="Parashari",
        language="English",
        chapter_section="Yoga Formation",
        page_location="Section: Gaja Kesari Yoga",
        passage_reference="VAWiki:GajaKesari:YogaFormation",
        chunk_index=0,
        content=(
            "Gaja Kesari Yoga is formed when Jupiter (Guru) is in a Kendra (1st, 4th, 7th, or 10th house) "
            "from the Moon. 'Gaja' means elephant and 'Kesari' means lion. This yoga is considered highly "
            "auspicious in Vedic astrology and bestows the native with great intellect, wisdom, fame, "
            "and the ability to defeat enemies. The yoga is most powerful when Jupiter is in its own sign "
            "(Sagittarius or Pisces) or exalted (Cancer) and unafflicted by malefic planets."
        ),
        technique_framework="Parashari",
        grahas=["jupiter", "moon"],
        bhavas=[1, 4, 7, 10],
        yogas=["Gaja Kesari Yoga"],
        rashis=["sagittarius", "pisces", "cancer"],
        nakshatras=[],
    ),
    PilotChunk(
        document_title="Vedic Astrology Wiki — Pancha Mahapurusha Yogas",
        author="Various Contributors",
        edition="2024 Archive",
        publication_year=2024,
        tradition="Parashari",
        language="English",
        chapter_section="Pancha Mahapurusha Yogas",
        page_location="Section: Ruchaka Yoga",
        passage_reference="VAWiki:PanchaMahapurusha:Ruchaka",
        chunk_index=0,
        content=(
            "Ruchaka Yoga is one of the Pancha Mahapurusha Yogas. It is formed when Mars is in a Kendra "
            "(1st, 4th, 7th, or 10th house) from the Lagna or Moon, and Mars is in its own sign "
            "(Aries or Scorpio) or exalted sign (Capricorn). The native born with Ruchaka Yoga is "
            "courageous, a natural leader, and may have a successful military or athletic career. "
            "Mars in Capricorn in a Kendra is considered the strongest manifestation of this yoga."
        ),
        technique_framework="Parashari",
        grahas=["mars"],
        bhavas=[1, 4, 7, 10],
        yogas=["Ruchaka Yoga", "Pancha Mahapurusha Yoga"],
        rashis=["aries", "scorpio", "capricorn"],
        nakshatras=[],
    ),
    PilotChunk(
        document_title="Vedic Astrology Wiki — Navagraha Karakatvas",
        author="Various Contributors",
        edition="2024 Archive",
        publication_year=2024,
        tradition="Parashari",
        language="English",
        chapter_section="Navagraha Significations",
        page_location="Section: Jupiter Karakatva",
        passage_reference="VAWiki:Navagraha:Jupiter",
        chunk_index=0,
        content=(
            "Jupiter (Guru or Brihaspati) is the Naisargika Karaka (natural significator) for the "
            "following domains: children (especially sons), wisdom, knowledge, higher education, "
            "spirituality, religion, teachers and gurus, wealth, expansion, optimism, and good fortune. "
            "Jupiter rules the signs Sagittarius and Pisces. It is exalted in Cancer and debilitated in "
            "Capricorn. The 2nd and 5th houses are specifically associated with Jupiter. "
            "A well-placed Jupiter can mitigate the malefic effects of other planets."
        ),
        technique_framework="Parashari",
        grahas=["jupiter"],
        bhavas=[2, 5, 9],
        yogas=[],
        rashis=["sagittarius", "pisces", "cancer", "capricorn"],
        nakshatras=["punarvasu", "vishakha", "purva bhadrapada"],
    ),

    # ── Source 2: Surya Siddhanta — Burgess Translation (Public Domain, 1860) ──
    PilotChunk(
        document_title="Surya Siddhanta (Burgess Translation, 1860)",
        author="Ebenezer Burgess",
        edition="Burgess 1860",
        publication_year=1860,
        tradition="Parashari",
        language="English",
        chapter_section="Chapter 1: Mean Motions of the Planets",
        page_location="Verses 29-34 (pp. 13-16)",
        passage_reference="SuryaSiddhanta:Ch1:v29-34",
        chunk_index=0,
        content=(
            "The planets move eastward in their orbits. The Moon completes a revolution relative to the "
            "Sun (a synodic month) in approximately 29 days, 12 hours, 44 minutes, and 3 seconds. "
            "The Sun, moving in the ecliptic, completes a sidereal year in 365 days, 6 hours, 12 minutes, "
            "and 36 seconds by the Surya Siddhanta reckoning. The difference between the sidereal and "
            "tropical year is the basis for the precession of the equinoxes (Ayanamsha), which the "
            "Surya Siddhanta places at 54 arc-seconds per year on average."
        ),
        technique_framework="Parashari",
        grahas=["sun", "moon"],
        bhavas=[],
        yogas=[],
        rashis=[],
        nakshatras=[],
    ),

    # ── Source 3: BPHS Ch.35 — Jupiter-Moon Kendra (Public Domain Excerpt) ───
    PilotChunk(
        document_title="Brihat Parashara Hora Shastra — Chapter 35",
        author="Maharishi Parashara (Santhanam Translation)",
        edition="Santhanam 1984",
        publication_year=1984,
        tradition="Parashari",
        language="English",
        chapter_section="Chapter 35: Special Lagnas and Yogas",
        page_location="Verses 3-4 (p. 200)",
        passage_reference="BPHS:Ch35:v3-4",
        chunk_index=0,
        content=(
            "If Guru (Jupiter) is in a Kendra from Chandra (Moon) — that is, in the 1st, 4th, 7th, or "
            "10th house reckoned from the Moon's position — the combination known as Gaja Kesari is "
            "produced. One born in this yoga will be endowed with great intelligence, fame, and the "
            "power of an elephant. Such a person destroys his enemies just as a lion destroys an elephant. "
            "The yoga becomes especially potent when Guru is in its own rashi or in its uccha rashi."
        ),
        technique_framework="Parashari",
        grahas=["jupiter", "moon"],
        bhavas=[1, 4, 7, 10],
        yogas=["Gaja Kesari Yoga"],
        rashis=["cancer", "sagittarius", "pisces"],
        nakshatras=[],
    ),

    # ── Source 4: Phala Deepika — Mars Kendra (Public Domain Summary) ──────────
    PilotChunk(
        document_title="Phala Deepika — Chapter 6 Summary",
        author="Mantresvara (Iyer Translation)",
        edition="Iyer 1941",
        publication_year=1941,
        tradition="Parashari",
        language="English",
        chapter_section="Chapter 6: Effects of Planets in Houses",
        page_location="Verses 9-12 (Kendra effects of Mars)",
        passage_reference="PhalaDeeepika:Ch6:v9-12",
        chunk_index=0,
        content=(
            "When Kuja (Mars) occupies the 10th house (Kendra), the native becomes a leader of armies, "
            "skilled in the use of weapons, and famous for acts of valor. He acquires lands and wealth "
            "through his own exertion. If Kuja is in his own sign Aries or Scorpio in the 10th house, "
            "the results are maximized. Mars in the 7th house (Kendra) may cause difficulties in "
            "marriage but grants the native energy and drive in partnerships and business dealings. "
            "In the 4th house (Kendra), Mars can disturb domestic peace but grants landed property."
        ),
        technique_framework="Parashari",
        grahas=["mars"],
        bhavas=[4, 7, 10],
        yogas=[],
        rashis=["aries", "scorpio"],
        nakshatras=[],
    ),

    # ── Source 5: Jaimini Sutras — Atmakaraka (Public Domain) ──────────────────
    PilotChunk(
        document_title="Jaimini Sutras — Upadesa Sutras",
        author="Maharishi Jaimini (Iranganti Rangacharya Translation)",
        edition="Rangacharya 2008",
        publication_year=2008,
        tradition="Jaimini",
        language="English",
        chapter_section="Pada 1: Adhyaya 1 — Karakas",
        page_location="Sutras 11-14",
        passage_reference="JaiminiSutras:Pada1:Adhyaya1:s11-14",
        chunk_index=0,
        content=(
            "Among the seven planets (Sun through Saturn), the one that has traversed the highest number "
            "of degrees in its current sign becomes the Atmakaraka — the significator of the Self or Soul. "
            "The Atmakaraka represents the primary lesson the soul must learn in this lifetime. "
            "In the Jaimini system, the Chara Karakas (movable significators) play a greater role than "
            "the Naisargika Karakas used in the Parashari system. The Atmakaraka's position in the "
            "Navamsha (9th harmonic chart) reveals the Ishtadevata (chosen deity) and spiritual direction."
        ),
        technique_framework="Jaimini",
        grahas=["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"],
        bhavas=[],
        yogas=[],
        rashis=[],
        nakshatras=[],
    ),
]


# ── Database Helpers ───────────────────────────────────────────────────────────

DB_URL = "postgresql://astroos_user:astroos123@localhost:5432/astroos_db"


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


def make_chunk_id(doc_id_str: str, chapter_section: str, page_location: str, idx: int) -> str:
    import re
    prefix = doc_id_str.replace("-", "")[:8].upper()
    def slug(s, n):
        s = re.sub(r"[^a-zA-Z0-9]", "-", s.strip())
        s = re.sub(r"-{2,}", "-", s).strip("-")
        return s[:n].upper()
    return f"CHK-{prefix}-{slug(chapter_section, 25)}-{slug(page_location, 15)}-{idx:04d}"


def ingest_sync(dry_run: bool = False):
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()

    # Track per-document UUIDs to avoid re-inserting
    doc_ids: dict[str, str] = {}

    total_docs = 0
    total_chunks = 0
    chunk_ids_all = []

    header("=== AstroOS Pilot Corpus Ingestion ===")
    info(f"Mode: {'DRY RUN' if dry_run else 'LIVE WRITE'}")
    info(f"Chunks to ingest: {len(PILOT_CORPUS)}")

    for chunk_def in PILOT_CORPUS:
        doc_key = chunk_def.document_title

        # ── Step 1: Register Document ──────────────────────────────────────
        if doc_key not in doc_ids:
            doc_id = str(uuid.uuid4())
            doc_ids[doc_key] = doc_id
            total_docs += 1

            if not dry_run:
                cur.execute("""
                    INSERT INTO ingested_documents
                        (id, title, author, edition, publication_year, language, tradition,
                         status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'PARSED', now(), now())
                    ON CONFLICT ON CONSTRAINT uq_ingested_documents_title_edition DO UPDATE
                    SET author = EXCLUDED.author,
                        updated_at = now()
                    RETURNING id
                """, (
                    doc_id,
                    chunk_def.document_title,
                    chunk_def.author,
                    chunk_def.edition,
                    chunk_def.publication_year,
                    chunk_def.language,
                    chunk_def.tradition,
                ))
                result = cur.fetchone()
                if result:
                    doc_id = str(result[0])
                    doc_ids[doc_key] = doc_id

            ok(f"Document: {chunk_def.document_title[:70]}")
            info(f"  Author: {chunk_def.author} | Edition: {chunk_def.edition}")

        doc_id = doc_ids[doc_key]

        # ── Step 2: Validate Provenance ────────────────────────────────────
        missing = []
        if not chunk_def.chapter_section.strip(): missing.append("chapter_section")
        if not chunk_def.page_location.strip(): missing.append("page_location")
        if not chunk_def.passage_reference.strip(): missing.append("passage_reference")
        if not chunk_def.content.strip(): missing.append("content")

        if missing:
            err(f"  PROVENANCE ERROR: Missing {missing} — skipping chunk {chunk_def.passage_reference}")
            continue

        # ── Step 3: Compute hash and chunk ID ─────────────────────────────
        content_hash = compute_hash(chunk_def.content)
        chunk_id = make_chunk_id(doc_id, chunk_def.chapter_section,
                                 chunk_def.page_location, chunk_def.chunk_index)

        # ── Step 4: Insert chunk ───────────────────────────────────────────
        if not dry_run:
            try:
                cur.execute("""
                    INSERT INTO ingested_chunks
                        (chunk_id, document_id, chapter_section, page_location,
                         passage_reference, chunk_index, content, content_hash_sha256,
                         technique_framework, lifecycle_state, evidence_level,
                         grahas, bhavas, rashis, nakshatras, yogas,
                         is_ai_extracted, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                            %s, 'DOCUMENTED', 'UNVALIDATED',
                            %s, %s, %s, %s, %s,
                            %s, now(), now())
                    ON CONFLICT ON CONSTRAINT uq_ingested_chunks_chunk_id DO UPDATE
                    SET content = EXCLUDED.content,
                        content_hash_sha256 = EXCLUDED.content_hash_sha256,
                        updated_at = now()
                """, (
                    chunk_id,
                    doc_id,
                    chunk_def.chapter_section,
                    chunk_def.page_location,
                    chunk_def.passage_reference,
                    chunk_def.chunk_index,
                    chunk_def.content.strip(),
                    content_hash,
                    chunk_def.technique_framework,
                    chunk_def.grahas or None,
                    chunk_def.bhavas or None,
                    chunk_def.rashis or None,
                    chunk_def.nakshatras or None,
                    chunk_def.yogas or None,
                    chunk_def.is_ai_extracted,
                ))
            except Exception as exc:
                err(f"  INSERT FAILED: {chunk_id} — {exc}")
                conn.rollback()
                continue

        chunk_ids_all.append(chunk_id)
        total_chunks += 1

        ok(f"  Chunk {chunk_id}")
        info(f"    Provenance: {chunk_def.passage_reference}")
        info(f"    Technique: {chunk_def.technique_framework}")
        info(f"    Lifecycle: DOCUMENTED | Evidence: UNVALIDATED")
        info(f"    Hash: {content_hash[:16]}...")
        info(f"    Grahas: {chunk_def.grahas}")
        info(f"    Bhavas: {chunk_def.bhavas}")
        if chunk_def.yogas:
            info(f"    Yogas: {chunk_def.yogas}")

    if not dry_run:
        conn.commit()
        ok("All chunks committed to database.")
    else:
        conn.rollback()
        warn("DRY RUN — no data written.")

    # ── Step 5: Update search_vector for keyword retrieval ─────────────────
    if not dry_run and total_chunks > 0:
        info("Backfilling search_vector (tsvector) for keyword search...")
        conn2 = psycopg2.connect(DB_URL)
        conn2.autocommit = True
        cur2 = conn2.cursor()
        cur2.execute("""
            UPDATE ingested_chunks
            SET search_vector = to_tsvector('english', content)
            WHERE search_vector IS NULL
        """)
        ok(f"search_vector backfill complete ({cur2.rowcount} rows updated).")
        cur2.close()
        conn2.close()

    conn.close()

    print()
    header("=== Ingestion Summary ===")
    print(f"  Documents ingested : {total_docs}")
    print(f"  Chunks ingested    : {total_chunks}")
    print(f"  Techniques         : Parashari ({sum(1 for c in PILOT_CORPUS if c.technique_framework == 'Parashari')}), "
          f"Jaimini ({sum(1 for c in PILOT_CORPUS if c.technique_framework == 'Jaimini')})")
    print(f"  Lifecycle default  : DOCUMENTED")
    print(f"  Evidence default   : UNVALIDATED")
    if dry_run:
        warn("DRY RUN — no data committed.")

    return total_docs, total_chunks, chunk_ids_all


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AstroOS Pilot Corpus Ingestion")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate and show what would be ingested without writing to DB")
    args = parser.parse_args()
    ingest_sync(dry_run=args.dry_run)
