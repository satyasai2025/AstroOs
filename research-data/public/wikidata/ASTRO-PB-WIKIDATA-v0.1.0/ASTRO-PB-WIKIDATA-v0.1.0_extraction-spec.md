# PB-WIKIDATA Extraction Specification

## Overview

Extract structured birth data from Wikidata using SPARQL queries.
Wikidata structured data is CC-0 licensed — no attribution required.

## SPARQL Query

```sparql
# PB-WIKIDATA v1.0 — Birth data extraction
# Wikidata SPARQL endpoint: https://query.wikidata.org/sparql
# Output format: JSON
# License: CC-0 (Wikidata structured data)

SELECT DISTINCT ?item ?itemLabel ?birthDate ?birthDatePrecision 
       ?birthPlaceLabel ?birthPlaceLat ?birthPlaceLng ?countryLabel
       ?genderLabel ?occupationLabel ?deathDate
WHERE {
  # Instance of human
  ?item wdt:P31 wd:Q5 .
  
  # Has date of birth (P569) with precision
  ?item p:P569 ?birthStatement .
  ?birthStatement ps:P569 ?birthDate .
  ?birthStatement psv:P569 ?birthValue .
  ?birthValue wikibase:precision ?birthDatePrecision .
  
  # Must have at least year precision (9 = year, 10 = decade, 11 = century)
  FILTER(?birthDatePrecision >= 9)
  
  # Birth place (optional)
  OPTIONAL { ?item wdt:P19 ?birthPlace . }
  
  # Coordinates of birth place (optional)
  OPTIONAL { 
    ?item wdt:P19 ?bp .
    ?bp wdt:P625 ?bpCoords .
    BIND(STR(?bpCoords) AS ?coordStr)
  }
  
  # Country of birth place (optional)
  OPTIONAL {
    ?item wdt:P19 ?bp2 .
    ?bp2 wdt:P17 ?country .
  }
  
  # Gender (optional — P21)
  OPTIONAL { ?item wdt:P21 ?gender . }
  
  # Occupation (optional — P106)
  OPTIONAL { ?item wdt:P106 ?occupation . }
  
  # Death date (optional — P570)
  OPTIONAL { ?item wdt:P570 ?deathDate . }
  
  # Labels in English
  SERVICE wikibase:label { 
    bd:serviceParam wikibase:language "en" . 
  }
}
# LIMIT can be removed for full extraction; start with 10000
LIMIT 10000
```

## Query Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Endpoint | https://query.wikidata.org/sparql | Public endpoint |
| Method | GET with URL-encoded query | |
| Format | JSON | |
| User-Agent | AstroOS-ResearchDataOffice/1.0 | Required by Wikidata policy |
| Rate limit | ~1 query/sec for unregistered; 10/sec for registered | Use `User-Agent` header |
| Max results | 10,000 per query (use OFFSET for pagination) | |

## Pagination Strategy

Wikidata SPARQL endpoint returns max ~10,000 rows per query.
Use `OFFSET` with `LIMIT` for full extraction:

```sparql
LIMIT 10000
OFFSET 0    -- first batch
OFFSET 10000  -- second batch
...
```

Alternative: Use `DATE` filters per decade:
```sparql
FILTER(?birthDate >= "1900-01-01"^^xsd:dateTime && ?birthDate < "1910-01-01"^^xsd:dateTime)
```

## Post-Processing

After extracting raw SPARQL results:

1. **Parse coordinates**: `Point(lat lng)` → separate lat/lng fields
2. **Parse precision codes**:
   - 11 = century (discard — too imprecise)
   - 10 = decade (keep birth_year only)
   - 9 = year (keep birth_date with year precision)
   - 8 = month (keep birth_date with month precision)
   - 7 = day (keep exact birth_date)
3. **Map occupations**: Group Wikidata occupation Q-IDs into ISCO-like categories
4. **Deduplicate**: Remove duplicate Wikidata IDs (keep first occurrence)
5. **Validate**: Check coordinates, date ranges

## Schema (Output CSV)

| Column | Type | Source |
|--------|------|--------|
| `_record_id` | String | Auto-generated: `ASTRO-REC-WIKIDATA-{NNNNNN}` |
| `_dataset_id` | String | `ASTRO-PB-WIKIDATA-v1.0.0` |
| `wikidata_id` | String | Wikidata Q-ID (e.g., Q937) |
| `person_label` | String | `?itemLabel` |
| `birth_date` | Date | `?birthDate` (ISO 8601) |
| `birth_date_precision` | Integer | `?birthDatePrecision` (7=day, 8=month, 9=year) |
| `birth_place` | String | `?birthPlaceLabel` |
| `birth_latitude` | Decimal | Parsed from `?bpCoords` |
| `birth_longitude` | Decimal | Parsed from `?bpCoords` |
| `country` | String | `?countryLabel` |
| `gender` | String | `?genderLabel` |
| `occupation` | String | `?occupationLabel` (pipe-separated if multiple) |
| `death_date` | Date | `?deathDate` (optional) |

## Dataset Metadata

| Field | Value |
|-------|-------|
| Dataset ID | `ASTRO-PB-WIKIDATA-v1.0.0` |
| License | CC-0 (Wikidata structured data) |
| Privacy | Public (notable individuals; data from public sources) |
| Confidence | Verified_Single (Wikidata single source) |
| Provenance | Primary (Wikidata SPARQL query) |
| Query Version | 1.0 |
| Extraction Date | TBD |

## Known Limitations

1. **Birth times not available**: Wikidata does not record birth times for most individuals
2. **Geographic precision varies**: Birth place coordinates are for the location, not the specific birthplace
3. **Notability bias**: Only individuals with Wikidata entries are included
4. **Western bias**: Wikidata coverage varies by geography and culture
5. **Date precision varies**: Not all entries have day-precision dates
