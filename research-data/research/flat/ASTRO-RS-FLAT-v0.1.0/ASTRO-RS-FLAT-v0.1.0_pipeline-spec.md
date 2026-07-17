# RS-FLAT v0.1.0 — Flattened Chart Records Pipeline Specification

## Overview

RS-FLAT is a derived dataset: raw birth data + AstroOS calculation engines → flattened computed chart records. It is the primary input for the Statistics Engine, Research Engine, and AI Engine.

## Pipeline Architecture

```
┌───────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Source       │     │  Computation     │     │  RS-FLAT Output  │
│  Datasets     │────▶│  Pipeline        │────▶│  (Parquet/CSV)   │
│               │     │  (AstroOS        │     │                  │
│ PB-WIKI       │     │   Engines)       │     │ 147 features     │
│ SY-RANDOM     │     │                  │     │ per record       │
│ PB-WIKIDATA   │     │ HoroscopeEngine  │     │                  │
│               │     │ DashaEngine      │     │ Ready for        │
│ User charts   │     │ ShadbalaEngine   │     │ StatisticsEngine │
│               │     │ YogaEngine       │     │ ResearchEngine   │
│               │     │ DivisionalEngine │     │ AI Engine        │
└───────────────┘     └──────────────────┘     └──────────────────┘
```

## Input Requirements

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `birth_datetime_utc` | Yes | — | Date/time in UTC |
| `latitude` | Yes | — | WGS84 decimal degrees |
| `longitude` | Yes | — | WGS84 decimal degrees |
| `timezone_offset_minutes` | Yes | — | For local time calculations |
| `ayanamsa` | No | `lahiri` | Ayanamsa system |
| `house_system` | No | `whole_sign` | House system code |

## Output Schema (147 features)

All fields computed by AstroOS engines. This is the Statistics Engine import schema from Phase 7 §3.3:

```yaml
# === IDENTITY ===
record_id: string
source_dataset_id: string
source_record_id: string

# === BIRTH PARAMS ===
birth_year: int                # 1900-2020
birth_month: int               # 1-12
birth_dow: int                 # 0=Monday .. 6=Sunday
birth_hour: float              # decimal hour 0-24
latitude: float
longitude: float
country_code: string           # ISO 3166-1 alpha-2

# === LAGNA (ASCENDANT) ===
lagna_rashi: string            # enum: aries..pisces
lagna_nakshatra: string        # enum: 27 nakshatras
lagna_pada: int                # 1-4
lagna_degree: float            # 0-30 in sign

# === PLANET RASHIS (9 fields) ===
sun_rashi: string
moon_rashi: string
mars_rashi: string
mercury_rashi: string
jupiter_rashi: string
venus_rashi: string
saturn_rashi: string
rahu_rashi: string
ketu_rashi: string

# === PLANET HOUSES (9 fields) ===
sun_house: int                 # 1-12
moon_house: int
mars_house: int
mercury_house: int
jupiter_house: int
venus_house: int
saturn_house: int
rahu_house: int
ketu_house: int

# === PLANET DIGNITIES (9 fields) ===
sun_dignity: string            # enum: exalted..debilitated
moon_dignity: string
mars_dignity: string
mercury_dignity: string
jupiter_dignity: string
venus_dignity: string
saturn_dignity: string
rahu_dignity: string
ketu_dignity: string

# === PLANET RETROGRADE (9 booleans) ===
sun_retrograde: bool
moon_retrograde: bool
mars_retrograde: bool
mercury_retrograde: bool
jupiter_retrograde: bool
venus_retrograde: bool
saturn_retrograde: bool
rahu_retrograde: bool
ketu_retrograde: bool

# === PLANET NAKSHATRAS (9 fields) ===
sun_nakshatra: string
moon_nakshatra: string
mars_nakshatra: string
mercury_nakshatra: string
jupiter_nakshatra: string
venus_nakshatra: string
saturn_nakshatra: string
rahu_nakshatra: string
ketu_nakshatra: string

# === PLANET PADA (9 ints) ===
sun_pada: int                  # 1-4
moon_pada: int
mars_pada: int
mercury_pada: int
jupiter_pada: int
venus_pada: int
saturn_pada: int
rahu_pada: int
ketu_pada: int

# === PLANET LONGITUDES (9 floats) ===
sun_longitude: float           # 0-360
moon_longitude: float
mars_longitude: float
mercury_longitude: float
jupiter_longitude: float
venus_longitude: float
saturn_longitude: float
rahu_longitude: float
ketu_longitude: float

# === HOUSES ===
# House rashi (12 fields)
house_1_rashi: string
house_2_rashi: string
# ... through house_12_rashi

# House lord (12 fields)
house_1_lord: string
# ... through house_12_lord

# === SPECIAL ===
moon_nakshatra_lord: string    # The graha ruling Moon's nakshatra
has_raja_yoga: bool            # Any Raja Yoga detected by YogaEngine
has_dhana_yoga: bool           # Any Dhana Yoga detected
has_sanyasa_yoga: bool         # Any Sanyasa Yoga detected
is_leo_ascendant: bool         # Convenience flag

# === DASHA (current at birth) ===
current_mahadasha_lord: string
current_mahadasha_balance: float   # Remaining years
current_antardasha_lord: string

# === METADATA ===
engine_version: string         # AstroOS engine version used
computed_at: string            # ISO 8601 timestamp
computation_params: object     # {ayanamsa, house_system, ephemeris}
confidence_tier: string        # From source dataset
```

## Implementation Notes

| Concern | Guidance |
|---------|----------|
| **Engine** | Compute using `HoroscopeEngine.calculate()` + `DashaEngine.calculate()` + `YogaEngine.detect_all()` + `ShadbalaEngine.calculate()` |
| **Batch size** | Process 100-1000 records per batch |
| **Idempotency** | Same input + same engine version = identical output |
| **Null handling** | Graceful degradation: if ShadbalaEngine not available, leave shadbala fields null |
| **Format** | Output Parquet (ZSTD) for storage, CSV for ad-hoc use |
| **Checksum** | SHA-256 of each output batch; overall checksum via manifest |

## Priority Source Datasets

| Priority | Source | Est. Records | Est. Compute Time | Notes |
|----------|--------|-------------|-------------------|-------|
| 1 | SY-RANDOM v1.0.0 | 100,000 | ~10 min on 8-core | Baseline statistical profiles |
| 2 | PB-WIKI (future v1.0.0) | 10,000+ | ~1 min | Real notable-person profiles |
| 3 | PB-WIKIDATA (future v1.0.0) | 50,000+ | ~5 min | Extended real profiles |

## Dataset Metadata (Future)

```json
{
  "dataset_id": "ASTRO-RS-FLAT-v1.0.0",
  "name": "Flattened Chart Records",
  "description": "Denormalized computed chart data for statistical analysis and ML training.",
  "category": "Research",
  "type": "Flattened Chart Records",
  "provenance_tier": "Derived",
  "features": 147,
  "record_count": "TBD (depends on compute pipeline run)",
  "format": "Parquet + CSV",
  "computation_engines": ["HoroscopeEngine", "DashaEngine", "ShadbalaEngine", "YogaEngine", "DivisionalEngine"],
  "lifecycle_stage": "Candidacy"
}
```

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| AstroOS computation engines | Internal | Available |
| Source dataset (SY-RANDOM) | Internal | ✅ Stable v1.0.0 |
| Source dataset (PB-WIKI) | Internal | 🟡 Candidacy v0.1.0 |
| Computation pipeline script | Implementation | Needs engineering team |
