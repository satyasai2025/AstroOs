---
name: Divisional chart (Varga) computation rules
description: Parashara varga formulas implemented for D2–D60; special cases and gotchas
---

All 15 vargas implemented in apps/api/services/divisional_engine.py.

Key non-obvious rules:
- D2 Hora: only two possible signs (Cancer/Leo). Odd sign → Leo first, Cancer second. Even sign → Cancer first, Leo second.
- D3 Drekkana: offsets [0, 4, 8] from natal sign (NOT the general (sign×N+part)%12 formula).
- D4 Chaturthamsha: (sign_index + part × 3) % 12.
- D9 Navamsha: (sign_index × 9 + part) % 12 — the standard formula works correctly.
- D30 Trimshamsha: non-uniform partition (5/5/8/7/5° odd, 5/7/8/5/5° even). Sun and Moon keep their D1 sign unchanged.
- D60 Shashtiamsha: 60 parts of 0.5°; odd→Aries start, even→Libra start.

**Why:** Each varga has a different starting-sign rule set by Parashara. The general formula (sign × N + part) % 12 only works for D9; all others need specific offset tables.

**How to apply:** Use the dispatch table _VARGA_CALCULATOR; add new vargas there.
