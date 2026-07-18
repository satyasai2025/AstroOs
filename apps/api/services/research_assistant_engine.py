"""
AstroOS — Research Assistant Engine (Phase E)

Natural language research queries over the knowledge base. Answers questions
by searching books, verses, rules, karakatvas, and doctrinal conflicts, then
synthesizing a structured answer with evidence citations.

All methods are static — no state. Depends on KnowledgeEngine for
search and conflict loading.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from apps.api.domain.ai_phase_e import ResearchAnswer, ResearchEvidence, ResearchQuery
from apps.api.domain.knowledge import KnowledgeSearchQuery, KnowledgeSearchResult
from apps.api.services.knowledge_engine import KnowledgeEngine

# Domain keyword mapping for routing research questions to the right search.
_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "graha": ["planet", "graha", "sun", "moon", "mars", "mercury", "jupiter",
              "venus", "saturn", "rahu", "ketu", "surya", "chandra", "mangal",
              "budha", "guru", "shukra", "shani"],
    "bhava": ["house", "bhava", "bhav", "1st house", "2nd house", "3rd house",
              "4th house", "5th house", "6th house", "7th house", "8th house",
              "9th house", "10th house", "11th house", "12th house"],
    "yoga": ["yoga", "combination", "raj yoga", "dhana yoga", "parijata",
             "gajakesari", "panch mahapurusha", "neecha bhanga"],
    "dasha": ["dasha", "period", "mahadasha", "antardasha", "vimshottari",
              "yogini", "ashtottari", "kalachakra", "chara",
              "timing", "prediction timing"],
    "aspect": ["aspect", "drishti", "gaze", "special aspect", "full aspect",
               "quarter aspect", "rahu aspect", "ketu aspect"],
    "dignity": ["dignity", "exaltation", "debilitated", "moolatrikona",
                "own sign", "friendly", "neutral", "enemy", "neecha",
                "uccha", "dig bala"],
    "transit": ["transit", "gochar", "current movement", "sade sati",
                "ashtama shani", "vedha", "dhaiya"],
    "remedy": ["remedy", "upaya", "gemstone", "mantra", "yantra",
               "donation", "fast", "ritual"],
    "karakatva": ["signification", "karakatva", "karaka", "signify",
                  "represent", "lord of", "house significator"],
    "conflict": ["disagreement", "conflict", "debate", "controversy",
                 "different view", "alternative", "tradition differ"],
}


def _detect_domain(question: str) -> Optional[str]:
    """Detect the most likely knowledge domain from a research question."""
    q = question.lower()
    scores: dict[str, int] = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in q)
        if score > 0:
            scores[domain] = score
    if not scores:
        return None
    # Return the domain with the highest keyword match count.
    return max(scores, key=scores.get)


def _format_evidence(results: list[KnowledgeSearchResult], limit: int = 5) -> tuple[ResearchEvidence, ...]:
    """Convert KnowledgeSearchResults to ResearchEvidence objects."""
    ev: list[ResearchEvidence] = []
    for r in results[:limit]:
        ev.append(ResearchEvidence(
            source=r.book_title or r.entity_type,
            reference=str(r.entity_id),
            text=r.snippet,
            relevance=r.relevance,
            entity_type=r.entity_type,
            tradition=r.tradition,
        ))
    return tuple(ev)


def _synthesize_answer(
    question: str,
    results: list[KnowledgeSearchResult],
    domain: Optional[str],
    conflicts: list,
) -> ResearchAnswer:
    """Synthesize a natural-language answer from search results."""
    unanswered: list[str] = []
    evidence_parts: list[str] = []
    conflict_refs: list[str] = []

    if not results:
        body = (
            f"I searched the knowledge base for information related to your question "
            f"about '{question}', but did not find any directly matching entries. "
            f"This may mean the specific topic has not been catalogued yet, "
            f"or a different search term might yield results."
        )
        return ResearchAnswer(
            question=question,
            summary="No matching knowledge found.",
            body=body,
            evidence=(),
            confidence="low",
            unanswered_aspects=(question,),
        )

    # Build evidence summary.
    for r in results[:3]:
        source = r.book_title or r.entity_type
        evidence_parts.append(f"• {source}: {r.snippet[:150]}")

    # Check for related conflicts.
    for c in conflicts:
        conflict_refs.append(c.id)

    # Generate answer body based on domain.
    if domain == "graha":
        body = (
            f"Based on the knowledge base, I found {len(results)} relevant entries "
            f"about the planetary topic you asked about.\n\n"
        ) + "\n".join(evidence_parts)

        if results[0].book_title:
            body += f"\n\nThe primary classical source cited is {results[0].book_title}."

    elif domain == "yoga":
        body = (
            f"Regarding the yoga combination in your question, the knowledge base "
            f"contains {len(results)} references.\n\n"
        ) + "\n".join(evidence_parts)

        if conflict_refs:
            body += "\n\nNote: There are documented doctrinal disagreements on aspects of this topic."
            unanswered.append("Doctrinal disagreements exist — see related conflicts.")

    elif domain == "dasha":
        body = (
            f"About dasha timing: the knowledge base has {len(results)} entries "
            f"related to your question.\n\n"
        ) + "\n".join(evidence_parts)

        unanswered.append("This answer covers principles but not chart-specific timing.")

    elif domain == "conflict":
        body = (
            f"This is an actively debated topic with {len(conflict_refs)} "
            f"documented doctrinal conflicts. The evidence is:\n\n"
        ) + "\n".join(evidence_parts)

    else:
        body = (
            f"I found {len(results)} relevant entries in the knowledge base.\n\n"
        ) + "\n".join(evidence_parts)

    # Determine confidence.
    confidence = "high" if len(results) >= 3 and results[0].relevance >= 2.0 else "medium"
    if not results or results[0].relevance < 1.0:
        confidence = "low"

    return ResearchAnswer(
        question=question,
        summary=f"Found {len(results)} relevant knowledge base entries.",
        body=body,
        evidence=_format_evidence(results),
        related_conflicts=tuple(conflict_refs),
        confidence=confidence,
        unanswered_aspects=tuple(unanswered),
    )


class ResearchAssistantEngine:
    """Answers natural language research questions over the knowledge base."""

    @staticmethod
    async def query(
        query: ResearchQuery,
        knowledge_engine: KnowledgeEngine,
    ) -> ResearchAnswer:
        """
        Process a natural language research query against the knowledge base.
        Searches books, verses, rules, karakatvas, and conflicts.
        """
        # Detect domain if not explicitly set.
        domain = query.domain_filter or _detect_domain(query.question)

        # Build search query from the question.
        search_text = query.question
        # Strip common question words for better matching.
        search_text = re.sub(
            r"^(what|where|when|why|how|is|are|does|do|can|tell me about|explain|describe)\s+",
            "", search_text, flags=re.IGNORECASE,
        )
        search_text = search_text.strip().rstrip("?")

        # Search knowledge base.
        search_query = KnowledgeSearchQuery(
            text=search_text,
            limit=query.max_results,
        )
        results = await knowledge_engine.search(search_query)

        # If no results, try with the original question.
        if not results:
            search_query = KnowledgeSearchQuery(
                text=query.question,
                limit=query.max_results,
            )
            results = await knowledge_engine.search(search_query)

        # Load conflicts for context.
        conflicts = knowledge_engine.load_conflicts()

        # Filter conflicts by domain if applicable.
        if domain:
            conflicts = [c for c in conflicts if c.domain == domain]

        # Synthesize answer.
        return _synthesize_answer(query.question, list(results), domain, conflicts)

    @staticmethod
    def available_domains() -> list[dict[str, Any]]:
        """Return the list of searchable knowledge domains."""
        return [
            {"id": "graha", "name": "Planets (Grahas)", "description": "Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu"},
            {"id": "bhava", "name": "Houses (Bhavas)", "description": "All 12 houses and their significations"},
            {"id": "yoga", "name": "Yogas & Combinations", "description": "Planetary combinations and their effects"},
            {"id": "dasha", "name": "Dasha Systems", "description": "Timing systems including Vimshottari, Yogini, Ashtottari"},
            {"id": "aspect", "name": "Aspects (Drishti)", "description": "How planets see and influence each other"},
            {"id": "dignity", "name": "Dignities", "description": "Exaltation, debilitation, own sign, friendly, enemy placements"},
            {"id": "transit", "name": "Transits (Gochara)", "description": "Current planetary movements and their effects"},
            {"id": "remedy", "name": "Remedies (Upaya)", "description": "Classical and modern remedial measures"},
            {"id": "karakatva", "name": "Significations (Karakatva)", "description": "What each planet, sign, and house signifies"},
            {"id": "conflict", "name": "Doctrinal Conflicts", "description": "Documented disagreements between traditions"},
        ]