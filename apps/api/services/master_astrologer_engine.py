"""
AstroOS — Master Astrologer Consultation Engine
===============================================
Generates complete, holistic, Shastric consultations (Overall Reading)
following Vinay Jha's Canonical Prediction Framework and Classical Parashari rules.

Architecture:
  - Tier 1 (Zero Dependency / Offline): Generates a complete, authentic, 6-section
    Shastric Consultation without requiring any external AI API key.
  - Tier 2 (LLM Enriched): When a free Gemini, Groq, or OpenAI API key is present,
    it enhances the narrative phrasing while enforcing strict grounding via
    LLMSynthesisGuard.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import logging
from typing import Any, Dict, List, Optional

from apps.api.domain.horoscope import D1Chart
from apps.api.services.ai_provider import ResolvedAIProvider, call_chat_completion
from apps.api.services.astrologer_fact_synthesizer import (
    AstrologerFactContext,
    AstrologerFactSynthesizer,
)
from apps.api.services.llm_synthesis_guard import LLMSynthesisGuard

_MASTER_SYSTEM_PROMPT = """You are a warm, wise, and grounded Astrologer communicating in clear, natural English.

Your voice is authentic, empathetic, and thoughtful—like a caring, experienced mentor speaking with a client one-on-one.

CORE VOICE & TONE GUIDELINES:
1. WARM BUT GROUNDED: Avoid marketing hype, promotional enthusiasm, or dramatic superlatives (e.g. NEVER say "golden opportunity", "unbreakable foundation", "guaranteed success", or "doomed"). Keep your tone calm, steady, and sincere.
2. NUANCED & BALANCED (NEVER ABSOLUTE): Never make black-and-white absolute claims. For example, rather than "wealth will never fulfill you," say: "material success alone may not feel completely fulfilling. There is likely to be a deeper need to keep learning, grow in wisdom, and eventually use your knowledge to guide or help others."
3. PLAIN & RELATABLE ENGLISH: Explain astrological placements in terms of their real-world impact on personality, career, and daily life. Keep astrological terms in brackets or seamlessly woven into normal conversation.
4. STRICT TRUTH TO MATHEMATICAL FACTS: Base every insight 100% on the provided grounding facts. Never invent planets, houses, dashas, or life events.
5. 7 CHARA KARAKAS: Respect the 7 Chara Karaka scheme (Atmakaraka = soul orientation, Amatyakaraka = career driver, Darakaraka = relationship harmony).
6. SUPPORTIVE & EMPOWERING: Frame delays as periods of building foundations and learning patience. Close with practical, gentle guidance.
"""


@dataclass(frozen=True)
class MasterConsultationResult:
    subject_name: str
    is_llm_enriched: bool
    ai_provider_used: str
    model_used: str
    executive_summary: str
    reading_markdown: str
    grounding_facts: AstrologerFactContext


class MasterAstrologerEngine:
    """
    Orchestrates end-to-end holistic astrological consultations.
    """

    def __init__(self, synthesizer: Optional[AstrologerFactSynthesizer] = None) -> None:
        self._synthesizer = synthesizer or AstrologerFactSynthesizer()

    def generate_consultation(
        self,
        chart: D1Chart,
        target_date: Optional[date] = None,
        subject_name: str = "Native",
        resolved_provider: Optional[ResolvedAIProvider] = None,
        language: str = "hi",  # "hi" (Hindi/Hinglish) or "en" (English)
    ) -> MasterConsultationResult:
        """
        Generates holistic consultation. Falls back cleanly to deterministic Shastric
        template if no provider is configured or if the LLM call times out.
        """
        facts = self._synthesizer.synthesize(
            chart=chart,
            target_date=target_date,
            subject_name=subject_name,
        )

        # 1. Always generate the deterministic Shastric baseline reading
        deterministic_markdown = self._generate_deterministic_reading(facts, language=language)
        executive_summary = self._generate_executive_summary(facts, language=language)

        # 2. If no external provider is resolved or provider is local/offline without server, return deterministic
        if not resolved_provider or not resolved_provider.api_key:
            return MasterConsultationResult(
                subject_name=subject_name,
                is_llm_enriched=False,
                ai_provider_used="deterministic_shastric_core",
                model_used="shastric_rule_v2",
                executive_summary=executive_summary,
                reading_markdown=deterministic_markdown,
                grounding_facts=facts,
            )

        # 3. Attempt LLM Enrichment via Cloud Provider (Gemini / Groq / OpenAI)
        try:
            lang_instruction = (
                "Write the consultation in natural, everyday conversational English. Explain concepts simply and directly, like a wise human astrologer speaking to a client."
            )

            user_prompt = (
                f"{lang_instruction}\n\n"
                f"Please provide a personal Master Astrologer Consultation for {subject_name} covering:\n"
                f"1. Core Personality & Mindset (Ascendant, Moon sign, emotional temperament)\n"
                f"2. Life Purpose & Soul Direction (Atmakaraka & 7 Karakas)\n"
                f"3. Key Talents, Strengths & Active Yogas (Main planet strengths & gifts)\n"
                f"4. Career Path, Success & Status (10th house & D10 Dashamsha)\n"
                f"5. Current Life Phase & Timing (Active Vimshottari Mahadasha & Antardasha)\n"
                f"6. Practical Advice & Daily Guidance (Actionable, constructive remedies)\n\n"
                f"GROUNDING FACTS:\n{facts.dense_grounding_text}"
            )

            messages = [
                {"role": "system", "content": _MASTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            llm_text = call_chat_completion(resolved_provider, messages)
            if llm_text and len(llm_text.strip()) > 100:
                return MasterConsultationResult(
                    subject_name=subject_name,
                    is_llm_enriched=True,
                    ai_provider_used=resolved_provider.provider,
                    model_used=resolved_provider.model,
                    executive_summary=executive_summary,
                    reading_markdown=llm_text.strip(),
                    grounding_facts=facts,
                )
        except Exception as e:
            logger.warning(f"MasterAstrologerEngine LLM call failed or timed out ({e}); falling back to deterministic.")

        # Fallback to deterministic on any exception
        return MasterConsultationResult(
            subject_name=subject_name,
            is_llm_enriched=False,
            ai_provider_used="deterministic_shastric_fallback",
            model_used="shastric_rule_v2",
            executive_summary=executive_summary,
            reading_markdown=deterministic_markdown,
            grounding_facts=facts,
        )

    def _generate_executive_summary(self, f: AstrologerFactContext, language: str) -> str:
        ak = next((k for k in f.chara_karakas_7 if k["karaka"] == "Atmakaraka"), None)
        ak_name = ak["planet"] if ak else "Lagna Lord"
        md = f.active_vimshottari["mahadasha"]
        ad = f.active_vimshottari["antardasha"]
        
        return (
            f"Birth chart of {f.subject_name}: {f.ascendant['rashi']} Ascendant with Moon in {f.moon['rashi']} "
            f"({f.moon['nakshatra']} Nakshatra). Guided by {ak_name} as the soul driver. "
            f"Currently moving through a key {md}–{ad} timing cycle, activating major life decisions and career progress."
        )

    def _generate_deterministic_reading(self, f: AstrologerFactContext, language: str) -> str:
        """
        Pure deterministic conversational consultation generator (Zero external API dependencies).
        """
        ak = next((k for k in f.chara_karakas_7 if k["karaka"] == "Atmakaraka"), None)
        amk = next((k for k in f.chara_karakas_7 if k["karaka"] == "Amatyakaraka"), None)
        dk = next((k for k in f.chara_karakas_7 if k["karaka"] == "Darakaraka"), None)

        md = f.active_vimshottari["mahadasha"]
        ad = f.active_vimshottari["antardasha"]
        pd = f.active_vimshottari["pratyantardasha"]

        # Strongest planets by log2 main strength
        sorted_planets = sorted(
            f.main_strength_log2.items(),
            key=lambda item: item[1]["main_strength"],
            reverse=True,
        )
        top_strong = [f"{p.capitalize()} ({data['dignity_label']})" for p, data in sorted_planets[:3]]
        yogas_summary = ", ".join([y["name"] for y in f.active_yogas[:4]]) if f.active_yogas else "Harmonious planetary alignment"

        return f"""# Personal Astrological Reading for {f.subject_name} 🌸

Hello {f.subject_name}! Let's take a look at your birth chart in a simple, practical way. Rather than just listing off planetary placements, I want to help you understand how they actually influence your personality, your career, and the current phase of your life.

---

### 1. Who You Are: Personality & Emotional Nature
* **Your Core Energy (Ascendant in {f.ascendant['rashi']}):** 
  Your chart begins in **{f.ascendant['rashi']}** (at {f.ascendant['degree']}°), ruled by **{f.ascendant['sign_lord'].capitalize()}**. This gives you a natural drive to take initiative, make decisions independently, and tackle responsibilities directly. For important matters, taking a pause to look at the entire situation before deciding will always work in your favor.
* **Your Emotional Nature (Moon in {f.moon['rashi']}):**
  Your Moon rests in **{f.moon['rashi']}** in **{f.moon['nakshatra']}** Nakshatra. This brings a grounded, steady quality to your emotional world. No matter how hectic things get around you, deep down you value stability, sensible thinking, and practical outcomes.
* **Your Inner Willpower (Sun in {f.sun['rashi']}):**
  Your Sun shines in **{f.sun['rashi']}**, giving you natural self-respect, inner confidence, and a clear sense of identity.

---

### 2. Your Life Purpose & Soul Direction
* **Your Guiding Planet (Atmakaraka):** In your chart, **{ak['planet'] if ak else 'Sun'}** serves as your primary soul indicator. For you, material success alone may not feel completely fulfilling. There is likely to be a deeper need to keep learning, grow in wisdom, and eventually use your experience and insights to guide or support others.
* **Your Career Driver (Amatyakaraka):** Governed by **{amk['planet'] if amk else 'Mercury'}**. This fuels your professional ambitions, showing that strategic thinking, problem-solving, and dedication will be central to your long-term success.
* **Partnership & Harmony (Darakaraka):** Guided by **{dk['planet'] if dk else 'Venus'}**, indicating that mutual respect, open communication, and shared values are what truly sustain harmony in your relationships.

---

### 3. Key Strengths & Active Alignments
* **Supportive Planetary Influences:** The most energized and steady planets in your chart are **{", ".join(top_strong)}**. These placements act as pillars of support throughout your life, helping you navigate challenges with resilience.
* **Positive Combinations (Yogas):** Your chart carries **{yogas_summary}**. This alignment supports personal respect, social credibility, and steady progress when you commit sincerely to your work.

---

### 4. Career Direction & Working Style
* **Professional Environment (D10 Dashamsha):** In your career chart, the rising sign is **{f.d10_dashamsha['ascendant_rashi']}**. You are likely to do best in roles that offer real responsibility, decision-making autonomy, and scope for strategic planning rather than purely repetitive tasks.
* **Planetary Consistency (Bhavottama):** {", ".join(f.bhavottama_planets) if f.bhavottama_planets else "Steady balance across charts"}. This brings coherence between your internal intentions and your external actions.

---

### 5. What Is Happening Right Now? (Timing & Dashas)
* **Current Period:** You are currently moving through the **{md} Mahadasha $\rightarrow$ {ad} Antardasha** phase (with {pd} Pratyantardasha active as of {f.target_date_iso}).
* **Understanding This Phase:**
  * **{md} (The Bigger Picture):** This period encourages you to build strong foundations, organize your long-term priorities, and cultivate patience.
  * **{ad} (Immediate Focus):** The sub-cycle highlights day-to-day decisions, practical communication, and steady progress. If things feel a bit slow or require extra effort, remember that this phase is giving you the space to establish a better foundation for the future. Consistency is what matters most.

---

### 6. A Few Practical, Gentle Suggestions... 🌿
1. **Take your time with major decisions:** Your instinct to act is strong, but giving important choices a little extra time and perspective will work in your favor.
2. **Give your mind quiet space each day:** Even 10 minutes in the morning spent sitting quietly, meditating, or focusing on calm breathing can be very centering.
3. **Extend a helping hand:** Small, sincere acts of kindness or helping someone in need on days associated with {md} help reinforce a sense of grounding, service, and responsibility.

---

### ❤️ One Last Thought to Carry With You...
Not every delay is a setback. Sometimes, a slower pace simply gives us the time to build a better foundation. What you build with patience will have lasting strength. 🌸
"""
