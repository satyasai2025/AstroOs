---
name: pyswisseph house cusps indexing
description: swe.houses() returns 0-indexed 12-element tuple, not 1-indexed 13-element
---

swe.houses(jd, lat, lon, b'W') returns (cusps, ascmc) where:
- cusps is a 12-element tuple: cusps[0]=H1 cusp … cusps[11]=H12 cusp (0-indexed)
- ascmc[0] = Ascendant longitude

**Why:** A common mistake is assuming a 13-element 1-indexed tuple (like the C API docs suggest). pyswisseph wraps this differently. Using `cusps[1:13]` gives only 11 elements and causes IndexError in list comprehensions.

**How to apply:** Always use `cusps[0:12]` when reading house cusps from pyswisseph.
