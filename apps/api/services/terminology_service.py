"""
AstroOS — Sanskrit & English Astrological Terminology Service
Handles bidirectional resolution, transliteration/IAST aliases, house groupings,
and query expansion for classical Jyotish knowledge retrieval.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

# ── 1. Graha (Planet) Terminology Mappings ─────────────────────────────────────

GRAHA_ALIASES: dict[str, list[str]] = {
    "sun": [
        "surya", "ravi", "aditya", "bhanu", "divakara", "savitr", "savitri",
        "arka", "dinakara", "pushan", "aryama", "bhaskar", "surya-deva",
        "heli", "surya", "सूर्य", "रवि", "आदित्य", "भानु", "अर्क",
    ],
    "moon": [
        "chandra", "soma", "indu", "vidhu", "shashanka", "shashank", "sita",
        "himakar", "mriganka", "chandrama", "nishapati", "chandra-deva",
        "चन्द्र", "सोम", "इन्दु", "विधु", "शशाङ्क", "मृगाङ्क",
    ],
    "mars": [
        "mangala", "mangal", "kuja", "bhauma", "angaraka", "angarak",
        "rudhira", "kshititanaya", "skanda", "lohitanga", "aravinda",
        "मङ्गल", "कुज", "भौम", "अङ्गारक", "रुधिर", "क्षितितनय",
    ],
    "mercury": [
        "budha", "budh", "saumya", "rajaputra", "jna", "bodhana",
        "rauhineya", "chandraputra", "vid", "बुध", "सौम्य", "राजपुत्र", "ज्ञ",
    ],
    "jupiter": [
        "brihaspati", "guru", "devaguru", "deva-guru", "angiras", "jiva",
        "suraguru", "vachaspati", "devejya", "arya", "brahaspati",
        "बृहस्पति", "गुरु", "देवगुरु", "जीव", "वाचस्पति", "देवेज्य",
    ],
    "venus": [
        "shukra", "sukra", "bhargava", "daityaguru", "daitya-guru", "ushana",
        "kavya", "sita", "asuraguru", "daityejya", "bhrigu", "bhrigunandana",
        "शुक्र", "भार्गव", "दैत्यगुरु", "उशना", "काव्य", "भृगु",
    ],
    "saturn": [
        "shani", "sani", "shanaishchara", "shanaischara", "manda", "chayyaputra",
        "chhayaputra", "kona", "saura", "asita", "pangula", "arkaputra",
        "शनि", "शनैश्चर", "मन्द", "छायापुत्र", "सौर", "असित",
    ],
    "rahu": [
        "rahu", "rahuvu", "svarbhanu", "tama", "tamas", "asura", "phani",
        "bhujanga", "sarpa", "dragon-head", "राहु", "स्वर्भानु", "तमस्", "फणी",
    ],
    "ketu": [
        "ketu", "ketuvu", "dhvaja", "shikhi", "anila", "dhvaja-graha",
        "dragon-tail", "केतु", "ध्वज", "शिखी",
    ],
}

# ── 2. Rashi (Sign) Terminology Mappings ───────────────────────────────────────

RASHI_ALIASES: dict[str, list[str]] = {
    "aries": ["mesha", "mesh", "kriya", "aja", "मेष", "क्रिय", "अज"],
    "taurus": ["vrishabha", "vrisha", "vrishabh", "uksha", "tavuru", "वृषभ", "वृष", "उक्ष"],
    "gemini": ["mithuna", "mithun", "dvandva", "yugma", "jituma", "मिथुन", "द्वन्द्व", "युग्म"],
    "cancer": ["karka", "karkata", "karkataka", "kataka", "kulira", "कर्क", "कर्कट", "कुलीर"],
    "leo": ["simha", "singha", "simh", "singh", "leya", "सिंह", "लेय"],
    "virgo": ["kanya", "kanja", "parthena", "pathona", "कन्या", "पाथोन"],
    "libra": ["tula", "thula", "tul", "juka", "धटा", "तुला", "जूक"],
    "scorpio": ["vrischika", "vrishchika", "vrischik", "ali", "kourpi", "वृश्चिक", "अलि", "कौर्पि"],
    "sagittarius": ["dhanu", "dhanush", "dhanurdhara", "dhanvi", "taushika", "धनु", "धनुष", "धन्वी"],
    "capricorn": ["makara", "makar", "nakra", "mrigasyasya", "akokera", "मकर", "नक्र", "मृगास्य"],
    "aquarius": ["kumbha", "kumbh", "ghata", "toyadhara", "hrodroga", "कुम्भ", "घट", "तोयधर"],
    "pisces": ["meena", "mina", "matsya", "antya", "itthyas", "मीन", "मत्स्य", "अन्त्य"],
}

# ── 3. Bhava (House) Names & Groupings ────────────────────────────────────────

BHAVA_NAMES: dict[int, list[str]] = {
    1: ["tanu", "lagna", "ascendant", "deha", "kalpa", "adya", "1st", "house-1", "first-house", "तनु", "लग्न"],
    2: ["dhana", "kosa", "kutumba", "vitta", "nayana", "2nd", "house-2", "second-house", "धन", "कुटुम्ब", "वित्त"],
    3: ["sahaja", "bhratri", "bhrata", "vikrama", "parakrama", "dhairya", "3rd", "house-3", "सहज", "भ्रातृ", "विक्रम"],
    4: ["sukha", "matri", "bandhu", "veshma", "patala", "griha", "vahana", "vidya-bhava", "4th", "house-4", "सुख", "मातृ", "बन्धु", "गृह"],
    5: ["putra", "suta", "tanaya", "buddhi", "vidya", "dhi", "purvapunya", "5th", "house-5", "पुत्र", "सुत", "बुद्धि", "पूर्वपुण्य"],
    6: ["ari", "shatru", "ripu", "roga", "rina", "kshata", "gada", "6th", "house-6", "अरि", "शत्रु", "रिपु", "रोग", "ऋण"],
    7: ["yuvati", "kalatra", "jaya", "kama", "madana", "dyuna", "dara", "7th", "house-7", "युवति", "कलत्र", "जाया", "काम", "द्यूत"],
    8: ["randhra", "ayu", "mrityu", "vinasha", "nidhana", "ashta", "chhidra", "8th", "house-8", "रन्ध्र", "आयु", "मृत्यु", "निधन"],
    9: ["bhagya", "dharma", "tapa", "guru-bhava", "pitri-bhava", "subha", "9th", "house-9", "भाग्य", "धर्म", "तप", "शुभ"],
    10: ["karma", "karyasiddhi", "rajya", "vyapara", "mana", "meshurana", "aspada", "ajna", "10th", "house-10", "कर्म", "राज्य", "व्यापार"],
    11: ["labha", "aya", "prapti", "agamana", "upanthya", "11th", "house-11", "लाभ", "आय", "प्राप्ति"],
    12: ["vyaya", "moksha", "sayana", "antya", "bandhana", "ripa", "12th", "house-12", "व्यय", "मोक्ष", "शयन"],
}

BHAVA_GROUPS: dict[str, list[int]] = {
    "kendra": [1, 4, 7, 10],
    "quadrant": [1, 4, 7, 10],
    "trikona": [1, 5, 9],
    "trine": [1, 5, 9],
    "dusthana": [6, 8, 12],
    "trika": [6, 8, 12],
    "evil-houses": [6, 8, 12],
    "upachaya": [3, 6, 10, 11],
    "panapara": [2, 5, 8, 11],
    "succedent": [2, 5, 8, 11],
    "apoklima": [3, 6, 9, 12],
    "cadent": [3, 6, 9, 12],
    "maraka": [2, 7],
    "killer": [2, 7],
    "trishadaya": [3, 6, 11],
    "dharma": [1, 5, 9],
    "artha": [2, 6, 10],
    "kama": [3, 7, 11],
    "moksha": [4, 8, 12],
}


class TerminologyService:
    """
    Unified Sanskrit & English Astrological Terminology Resolver & Query Expander.
    """

    @classmethod
    def resolve_graha(cls, term: str) -> Optional[str]:
        """Maps a Sanskrit or English planet alias to canonical English key (e.g. 'guru' -> 'jupiter')."""
        t = term.strip().lower()
        for canonical, aliases in GRAHA_ALIASES.items():
            if t == canonical or t in aliases:
                return canonical
        return None

    @classmethod
    def resolve_rashi(cls, term: str) -> Optional[str]:
        """Maps a Sanskrit or English sign alias to canonical English key (e.g. 'mesha' -> 'aries')."""
        t = term.strip().lower()
        for canonical, aliases in RASHI_ALIASES.items():
            if t == canonical or t in aliases:
                return canonical
        return None

    @classmethod
    def resolve_bhava(cls, term: str) -> Optional[int]:
        """Maps a Sanskrit or English house name to house number (1..12)."""
        t = term.strip().lower()
        # Direct integer check
        if t.isdigit():
            val = int(t)
            if 1 <= val <= 12:
                return val
        for num, aliases in BHAVA_NAMES.items():
            if t in aliases:
                return num
        return None

    @classmethod
    def resolve_house_group(cls, term: str) -> Optional[list[int]]:
        """Maps house group names (kendra, trikona, dusthana, etc.) to list of house numbers."""
        t = term.strip().lower()
        return BHAVA_GROUPS.get(t)

    @classmethod
    def expand_query_tokens(cls, query: str) -> list[str]:
        """
        Enriches a search query by extracting Sanskrit/English astrological entities
        and injecting their canonical synonyms into the token list.
        """
        raw_tokens = [t for t in re.split(r"\W+", query.lower()) if len(t) > 1]
        expanded: Set[str] = set(raw_tokens)

        for token in raw_tokens:
            # 1. Check Graha
            graha = cls.resolve_graha(token)
            if graha:
                expanded.add(graha)
                expanded.update(GRAHA_ALIASES.get(graha, [])[:4])

            # 2. Check Rashi
            rashi = cls.resolve_rashi(token)
            if rashi:
                expanded.add(rashi)
                expanded.update(RASHI_ALIASES.get(rashi, [])[:3])

            # 3. Check Bhava
            bhava = cls.resolve_bhava(token)
            if bhava:
                expanded.add(f"house_{bhava}")
                expanded.add(str(bhava))
                expanded.update(BHAVA_NAMES.get(bhava, [])[:3])

            # 4. Check House Group
            group = cls.resolve_house_group(token)
            if group:
                for h in group:
                    expanded.add(f"house_{h}")
                    expanded.add(str(h))

        return sorted(list(expanded))
