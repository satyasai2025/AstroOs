---
name: pyswisseph SIDM constant names
description: Correct SIDM constant names in pyswisseph — some differ from docs
---

Verified working constants:
- swe.SIDM_LAHIRI ✅
- swe.SIDM_KRISHNAMURTI ✅
- swe.SIDM_RAMAN ✅
- swe.SIDM_YUKTESHWAR ✅
- swe.SIDM_FAGAN_BRADLEY ✅
- swe.SIDM_TRUE_CITRA ✅  ← note: CITRA not CHITRA

**Why:** The traditional spelling "Chitra" is used in docs and Sanskrit, but pyswisseph uses "Citra". Typo causes AttributeError at module import time.

**How to apply:** When adding new ayanamsa IDs, check `dir(swe)` first.
