# Data Dictionary: ASTRO-RF-SIGNS-v1.0.0

## Field Definitions

| # | Field Name | Type | Required | Description | Constraints | Example |
|---|------------|------|----------|-------------|-------------|---------|
| 1 | sign_number | Integer | Yes | Sign number (1–12 starting from Aries) | 1–12 | 1 |
| 2 | name | String | Yes | Zodiac sign name (English slug) | Enum: aries..pisces | aries |
| 3 | sanskrit_name | String | Yes | Sanskrit name in IAST transliteration | Max 20 chars | Mesha |
| 4 | lord | String | Yes | Ruling graha (planet) | Enum: sun..ketu | mars |
| 5 | element | String | Yes | Classical element | fire/earth/air/water | fire |
| 6 | modality | String | Yes | Classical modality | cardinal/fixed/dual | cardinal |
| 7 | gender | String | Yes | Classical gender | masculine/feminine | male |
| 8 | direction | String | No | Classical direction | Null pending Knowledge Office | null |
| 9 | start_degree | Decimal | Yes | Starting ecliptic degree | 0.0–360.0 | 0.0 |
| 10 | end_degree | Decimal | Yes | Ending ecliptic degree | 0.0–360.0 | 30.0 |

## Enum Values

### name
aries, taurus, gemini, cancer, leo, virgo, libra, scorpio, sagittarius, capricorn, aquarius, pisces

### lord
mars, venus, mercury, moon, sun, jupiter, saturn

### element
fire, earth, air, water

### modality
cardinal, fixed, dual

### gender
male, female

## Sources
- Degree ranges: Classical 30° per sign division
- Lord: BPHS classical rulership table
- Element: Classical triplicity
- Modality: Classical quadruplicity
- Gender: Classical odd/even sign classification
- Direction: NULL — pending Knowledge Office textual verification
