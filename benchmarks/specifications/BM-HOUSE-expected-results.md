# BM-HOUSE — Expected Results Specification

> **Part Of:** BM-HOUSE Benchmark Family
> **Version:** 1.0.0
> **Status:** DRAFT (Phase 4)
> **Date:** 2026-07-15

---

## 1. Reference Computation Method

Same as BM-CALC: reference values computed by Swiss Ephemeris `swe.houses()` via `EphemerisWrapper.get_ascendant_and_cusps()`, captured as content-addressed golden results.

---

## 2. Expected Output Per Test Case

### 2.1 BM-HOUSE-001 through BM-HOUSE-005 (Whole Sign, 5 charts)

**Expected outcome:** For each chart:

1. **House 1** rashi = lagna rashi
2. **House N** rashi = `(lagna_rashi_index + N - 1) % 12` — mathematical invariant
3. **Sidereal longitudes** are exactly at sign boundaries (N-1) × 30° from lagna = 0°
4. **Tropical longitudes** = sidereal + ayanamsa (mod 360)
5. **No intercepted signs** — each of the 12 signs appears exactly once

**Example structure (REF-001, lagna = Virgo):**
```
House 1: Virgo     0.0° sidereal  |  kendra   | trikona  | lord Mercury
House 2: Libra     30.0° sidereal | panapara  | —        | lord Venus
House 3: Scorpio   60.0° sidereal | apoklima  | —        | lord Mars
House 4: Sagittarius 90.0°        | kendra    | —        | lord Jupiter
House 5: Capricorn 120.0°         | panapara  | trikona  | lord Saturn
House 6: Aquarius  150.0°         | apoklima  | dusthana + upachaya | lord Saturn
House 7: Pisces    180.0°         | kendra    | —        | lord Jupiter
House 8: Aries     210.0°         | panapara  | dusthana | lord Mars
House 9: Taurus    240.0°         | apoklima  | trikona  | lord Venus
House 10: Gemini   270.0°         | kendra    | upachaya | lord Mercury
House 11: Cancer   300.0°         | panapara  | upachaya | lord Moon
House 12: Leo      330.0°         | apoklima  | dusthana | lord Sun
```

### 2.2 BM-HOUSE-006 through BM-HOUSE-009 (Placidus, Koch, Equal — REF-001)

**Expected outcome — Equal (E):**
- House N sidereal = (ascendant_sidereal + (N-1) × 30°) mod 360
- This is a mathematical invariant verifiable without reference data
- No intercepted signs

**Expected outcome — Placidus (P) and Koch (K):**
- Cusps from Swiss Ephemeris `swe.houses()` with system 'P' or 'K'
- Sidereal cusp = tropical cusp − ayanamsa (mod 360)
- Intercepted signs are possible (fewer than 12 distinct signs among the 12 cusps)
- Values MUST be captured from reference run; cannot be derived by formula
- Cross-check against astro.com recommended

### 2.3 BM-HOUSE-010 (House Classification — all systems, REF-001)

**Expected outcome:** Classification is SYSTEM-INDEPENDENT. Regardless of which house system is used, the classification of house 1 through 12 by NUMBER is fixed:

| House | Quadrant | Special | Rationale |
|-------|----------|---------|-----------|
| 1 | kendra | trikona | Angular, trinal |
| 2 | panapara | — | Succedent |
| 3 | apoklima | upachaya | Cadent, growth |
| 4 | kendra | — | Angular |
| 5 | panapara | trikona | Succedent, trinal |
| 6 | apoklima | dusthana, upachaya | Cadent, difficult, growth |
| 7 | kendra | — | Angular |
| 8 | panapara | dusthana | Succedent, difficult |
| 9 | apoklima | trikona | Cadent, trinal |
| 10 | kendra | upachaya | Angular, growth |
| 11 | panapara | upachaya | Succedent, growth |
| 12 | apoklima | dusthana | Cadent, difficult |

### 2.4 BM-HOUSE-011 (House Lordship — all systems, REF-001)

**Expected outcome:** Lordship is SYSTEM-DEPENDENT because it depends on which sign OCCUPIES each house, which varies per house system.

For each house, lord = `SIGN_LORDS[house.rashi]`. The mapping is:

| Rashi | Lord | Note |
|-------|------|------|
| Aries | Mars | — |
| Taurus | Venus | — |
| Gemini | Mercury | — |
| Cancer | Moon | — |
| Leo | Sun | — |
| Virgo | Mercury | Mercury rules 2 signs |
| Libra | Venus | Venus rules 2 signs |
| Scorpio | Mars | Mars rules 2 signs |
| Sagittarius | Jupiter | — |
| Capricorn | Saturn | — |
| Aquarius | Saturn | Saturn rules 2 signs |
| Pisces | Jupiter | Jupiter rules 2 signs |

Mercury, Venus, Mars, Jupiter, Saturn rule 2 signs. Sun and Moon rule 1 sign each.

### 2.5 BM-HOUSE-012 (Planet-House Assignment — all systems, REF-001)

**Expected outcome:** Planet's house depends on which rashi the planet occupies AND which rashi is on the cusp of each house.

For Whole Sign: Planet house = `(planet_rashi_index - lagna_rashi_index) % 12 + 1`
For other systems: Planet house = house whose cusp rashi matches planet's rashi (may differ from Whole Sign)

**Validation:** For each planet across all 4 systems:
- Whole Sign assignment is mathematically invariant (formula above)
- Placidus/Koch/Equal may differ from Whole Sign at the boundaries (planet near rashi edge, different cusp rashi)

### 2.6 BM-HOUSE-013 (Whole Sign Latitude Independence)

**Expected outcome:** Whole Sign house cusps are IDENTICAL across all tested latitudes (0° through 66.5°N) for the same birth time. This is a mathematical property of the Whole Sign system.

### 2.7 BM-HOUSE-014 (Placidus Latitude Sensitivity)

**Expected outcome:** Placidus house cusps VARY with latitude. The variation is:
- Largest at extreme latitudes (66.5°N)
- Smallest at equator (0°)
- Cusp longitudes change smoothly with latitude
- Intercepted signs may appear/disappear at different latitudes

---

## 3. Known Expected Behaviors

| Behavior | Expected | Rationale |
|----------|----------|-----------|
| Whole Sign: house N rashi = (lagna + N - 1) % 12 | Always true | Definition of Whole Sign |
| Equal: house N cusp = asc + (N-1) × 30° | Always true | Definition of Equal |
| Placidus: house sizes vary with latitude | Always true | Property of Placidus |
| Koch: no cusp outside [0, 360) | Always true | Wrapping applied |
| 12 houses always present | Always true | Engine guarantees |
| House classification deterministic | Always true | Fixed lookup |
| House lord deterministic given rashi | Always true | Fixed lookup |
| Whole Sign: no intercepted signs | Always true | Each sign = exactly 1 house |

---

## 4. Validation Criteria

| Check | Type | Method |
|-------|------|--------|
| Sidereal cusp in [0, 360) | Range | Unit check |
| Cusp N < Cusp N+1 (mod 360) | Ordering | Verifies no crossing |
| 12 distinct house numbers | Completeness | Set check |
| Rashi consistent with longitude | Consistency | longitude→rashi function |
| Lord consistent with rashi | Consistency | SIGN_LORDS lookup |
| Classification consistent with house number | Consistency | Fixed mapping |
| Whole Sign invariance across latitude | System invariant | Cross-latitude comparison |
| Equal invariant | System invariant | asc + (N-1)×30 formula |

---

## 5. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-15 | Chief QA & Benchmark Architect (Agent 4) | Initial expected results specification |

---

*End of BM-HOUSE Expected Results Specification.*
