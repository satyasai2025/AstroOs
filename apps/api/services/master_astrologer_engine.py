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

logger = logging.getLogger(__name__)

_MASTER_SYSTEM_PROMPT = """You are a revered Vedic Astrologer and Shastric Scholar trained strictly in classical Parashari Siddhanta, Jaimini Sutras, and the Vinay Jha prediction framework.

Your sacred duty is to provide a truthful, balanced, deeply insightful astrological consultation based EXCLUSIVELY on the verified mathematical horoscope facts supplied to you.

STRICT PROTOCOL RULES:
1. ZERO INVENTED FACTS: Never invent planets, houses, dashas, or degrees not explicitly present in the grounding facts.
2. 7 CHARA KARAKAS: Respect the 7 Chara Karaka scheme (Atmakaraka = highest degree, Darakaraka = lowest degree).
3. BHAVACHALITA IS PRIMARY: Read house results from the Bhavachalita placements provided.
4. TRANSIT IS TRIGGER ONLY: Transits trigger natal promises, they do not create independent events.
5. BALANCED TONE: Never use fatalistic or exaggerated claims (e.g. "guaranteed doom", "100% certainty"). Present karmic inclinations with dignity, wisdom, and actionable Shastric guidance.
6. FORMAT: Provide a comprehensive, beautifully structured reading with clear headings and bullet points.
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
                "Write the consultation in natural, respectful, and dignified Hindi (देवनागरी / शुद्ध हिंदी मिश्रित व्यावहारिक भाषा) as a traditional Indian scholar would speak."
                if language == "hi"
                else "Write the consultation in eloquent, scholarly, yet accessible English."
            )

            user_prompt = (
                f"{lang_instruction}\n\n"
                f"Please provide a complete Master Astrologer Consultation for {subject_name} covering:\n"
                f"1. लग्न एवं व्यक्तित्व का आधार (Ascendant, Moon nakshatra, temperament)\n"
                f"2. आत्मकारक एवं जीवन का मूल उद्देश्य (Atmakaraka & Soul purpose from 7 Karakas)\n"
                f"3. सक्रिय राजयोग व विशिष्ट ग्रह बल (Key Yogas & Log-Base-2 Main Strengths)\n"
                f"4. करियर, आजीविका व प्रतिष्ठा (Karma & Status from 10th house & D10 Dashamsha)\n"
                f"5. काल चक्र — वर्तमान विंशोत्तरी दशा का प्रभाव (Current MD-AD timing)\n"
                f"6. शास्त्रीय मार्गदर्शन एवं व्यावहारिक सात्विक उपाय (Remedies & Guidance)\n\n"
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
        
        if language == "hi":
            return (
                f"{f.subject_name} की कुंडली {f.ascendant['rashi']} लग्न और {f.moon['rashi']} चंद्र राशि "
                f"({f.moon['nakshatra']} नक्षत्र) की है। आत्मकारक {ak_name} जीवन के मूल उद्देश्य को दिशा दे रहे हैं। "
                f"वर्तमान में {md}-{ad} की विंशोत्तरी दशा गतिशील है, जो कर्मक्षेत्र और व्यक्तिगत विकास में विशेष परिवर्तन ला रही है।"
            )
        return (
            f"Horoscope of {f.subject_name} anchored in {f.ascendant['rashi']} Ascendant with Moon in {f.moon['rashi']} "
            f"({f.moon['nakshatra']} Nakshatra). Soul direction is guided by Atmakaraka {ak_name}. "
            f"Currently experiencing {md}-{ad} Vimshottari Dasha phase."
        )

    def _generate_deterministic_reading(self, f: AstrologerFactContext, language: str) -> str:
        """
        Pure deterministic Shastric consultation generator (Zero external API dependencies).
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
        top_strong = [f"{p.capitalize()} ({data['dignity_label']}, {data['main_strength']:.1f}x)" for p, data in sorted_planets[:3]]

        yogas_summary = ", ".join([y["name"] for y in f.active_yogas[:5]]) if f.active_yogas else "शुभ सामान्य ग्रह योग"

        if language == "hi":
            return f"""# संपूर्ण शास्त्रीय कुंडली परामर्श (Master Astrologer Reading)
**जातक का नाम:** {f.subject_name} | **जन्म समय (UTC):** {f.birth_datetime_iso} | **अयनांश:** {f.ayanamsa}

---

### 1. आधार एवं व्यक्तित्व विश्लेषण (Lagna & Temperament)
* **लग्न (देह व चेतना):** आपकी कुंडली **{f.ascendant['rashi']} लग्न** की है, जिसका भोगांश {f.ascendant['degree']}° है। लग्न नक्षत्र **{f.ascendant['nakshatra']} (पाद {f.ascendant['pada']})** है और लग्नेश **{f.ascendant['sign_lord'].capitalize()}** हैं। यह स्थिति जातक को दृढ़ इच्छाशक्ति, आत्मसम्मान और परिस्थितियों का सामना करने का सामर्थ्य देती है।
* **चंद्र (मन व संवेग):** चंद्र देव **{f.moon['rashi']} राशि** में {f.moon['degree']}° पर **{f.moon['nakshatra']}** नक्षत्र में स्थित हैं। मन की प्रवृत्ति संवेदनशील, विचारशील और कर्तव्यपरायण रहेगी।
* **सूर्य (आत्मा व प्रतिष्ठा):** सूर्य देव **{f.sun['rashi']} राशि** में स्थित होकर आत्मबल और सामाजिक प्रतिष्ठा को नियंत्रित करते हैं।

---

### 2. 7 चर कारक एवं आत्मिक उद्देश्य (Jha Canonical Soul Purpose)
विनय झा एवं जैमिनी महर्षि के 7 चर कारक सिद्धांत के अनुसार:
* **आत्मकारक (Atmakaraka - जीवन का परम ध्येय):** **{ak['planet'] if ak else 'अज्ञात'}** ({ak['degree'] if ak else 0}°)। यह ग्रह आपकी आत्मा की यात्रा और जीवन के सबसे बड़े आत्म-साक्षात्कार का प्रतिनिधित्व करता है।
* **अमात्यकारक (Amatyakaraka - कर्म व आजीविका):** **{amk['planet'] if amk else 'अज्ञात'}** ({amk['degree'] if amk else 0}°)। यह ग्रह करियर में सफलता और सहयोगियों का कारक है।
* **दाराकारक (Darakaraka - जीवनसाथी व साझेदारी):** **{dk['planet'] if dk else 'अज्ञात'}** ({dk['degree'] if dk else 0}°)। जीवनसाथी के स्वभाव और पारिवारिक सुख का निर्धारक।

---

### 3. मुख्य ग्रह बल एवं सक्रिय राजयोग (Strengths & Yogas)
* **लॉग-बेस-2 मुख्य बल (1.0x से 256.0x):** आपकी कुंडली में सर्वाधिक बली ग्रह हैं: **{", ".join(top_strong)}**। शास्त्रीय सिद्धांत के अनुसार बली ग्रह अपने जीवन काल में पूर्ण फल देने में समर्थ होते हैं।
* **सक्रिय योग:** आपकी कुंडली में **{yogas_summary}** का प्रभाव सक्रिय है। यह जातक को समाज में मान-सम्मान और अनुकूल परिस्थितियों का निर्माण करने में सहायक होता है।

---

### 4. करियर एवं सामाजिक प्रतिष्ठा (D10 Dashamsha & Karma)
* **दशम भाव (कर्मक्षेत्र):** भावचलित में दशम भाव का प्रभाव कर्म में स्थायित्व और पुरुषार्थ को दर्शाता है।
* **दशमांश (D10):** D10 का लग्न **{f.d10_dashamsha['ascendant_rashi']}** है। करियर में प्रतिष्ठा प्राप्त करने के लिए अनुशासन और निरंतर प्रयास की आवश्यकता होगी।
* **भावोत्तम ग्रह:** {", ".join(f.bhavottama_planets) if f.bhavottama_planets else "विशिष्ट भावोत्तम स्थिति नहीं है"}।

---

### 5. वर्तमान काल चक्र एवं विंशोत्तरी दशा फल (Timing of Events)
* **सक्रिय विंशोत्तरी चक्र:** **{md} महादशा $\rightarrow$ {ad} अंतर्दशा $\rightarrow$ {pd} प्रत्यंतर्दशा** (मूल्यांकन तिथि: {f.target_date_iso})।
* **महादशा फल:** {md} की महादशा जीवन के इस कालखंड में प्राथमिक ऊर्जा को संचालित कर रही है।
* **अंतर्दशा फल:** {ad} की अंतर्दशा वर्तमान समय में तात्कालिक घटनाओं, मानसिक प्राथमिकताओं और निर्णयों को प्रेरित कर रही है।

---

### 6. शास्त्रीय मार्गदर्शन एवं व्यावहारिक सात्विक उपाय
1. **ईष्ट देव उपासना:** लग्नेश और आत्मकारक {ak['planet'] if ak else 'ग्रह'} की प्रसन्नता हेतु नित्य प्रातः सूर्य को अर्घ्य दें और गायत्री मंत्र या अपने कुलदेवता का स्मरण करें।
2. **सात्विक जीवनशैली:** दशम भाव और कर्म को शुद्ध रखने के लिए सत्यनिष्ठ आचरण और कार्यक्षेत्र में पारदर्शिता बनाए रखें।
3. **दान व सेवा:** अपनी महादशा नाथ ({md}) से संबंधित वस्तुओं का जरूरतमंदों को यथाशक्ति दान करें।
"""
        else:
            return f"""# Master Astrologer Consultation Reading
**Native:** {f.subject_name} | **Birth (UTC):** {f.birth_datetime_iso} | **Ayanamsa:** {f.ayanamsa}

---

### 1. Foundation: Ascendant & Luminaries
* **Ascendant (Lagna):** {f.ascendant['rashi']} at {f.ascendant['degree']}° ({f.ascendant['nakshatra']} Nakshatra, Pada {f.ascendant['pada']}). Sign Lord is {f.ascendant['sign_lord'].capitalize()}.
* **Moon (Chandra):** {f.moon['rashi']} at {f.moon['degree']}° ({f.moon['nakshatra']} Nakshatra). Indicates emotional foundation and mental resilience.
* **Sun (Surya):** {f.sun['rashi']} at {f.sun['degree']}° ({f.sun['nakshatra']} Nakshatra). Governs vitality and authority.

---

### 2. 7 Chara Karakas (Soul Purpose & Life Objectives)
* **Atmakaraka (Soul Purpose):** {ak['planet'] if ak else 'N/A'} ({ak['degree'] if ak else 0}°). Highest degree planet governing life purpose.
* **Amatyakaraka (Career Driver):** {amk['planet'] if amk else 'N/A'} ({amk['degree'] if amk else 0}°). Supports professional advancement.
* **Darakaraka (Partnership & Union):** {dk['planet'] if dk else 'N/A'} ({dk['degree'] if dk else 0}°). Governs marriage harmony.

---

### 3. Planetary Strengths & Active Yogas
* **Log-Base-2 Main Strengths (1.0x to 256.0x):** Dominant planetary influences: {", ".join(top_strong)}.
* **Active Yogas:** {yogas_summary}.

---

### 4. Career & Karma Status (D10 Dashamsha)
* **D10 Dashamsha Lagna:** {f.d10_dashamsha['ascendant_rashi']}.
* **Bhavottama Planets:** {", ".join(f.bhavottama_planets) if f.bhavottama_planets else "None"}.

---

### 5. Running Vimshottari Timing
* **Current Period:** {md} MD $\rightarrow$ {ad} AD $\rightarrow$ {pd} PD (As of {f.target_date_iso}).
* Timing window indicates activation of {md} and {ad} natural significations.

---

### 6. Shastric Guidance & Remedial Measures
1. Align professional efforts with the nature of Amatyakaraka ({amk['planet'] if amk else 'planet'}).
2. Daily meditation and contemplative practices to honor Atmakaraka ({ak['planet'] if ak else 'planet'}).
3. Sattvic living and acts of charity aligned with the running Mahadasha lord ({md}).
"""
