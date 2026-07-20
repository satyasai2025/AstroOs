"""Precision test suite for AstroOS calculation accuracy (Phase I.2 / v2.1.0).

DB-free by design — runs without TEST_DATABASE_URL. Validates:
  - Swiss Ephemeris planetary position accuracy against golden references
  - Shadbala component computation correctness
  - Ashtakavarga bindu counts per planet/house
  - Moshier fallback precision degradation
"""
