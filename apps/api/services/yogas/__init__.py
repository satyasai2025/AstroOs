"""
AstroOS — Yoga Modules (Module 8, Phase 1 + Phase 2)

Importing this package registers every yoga module's evaluators into the
yoga_registry. YogaEngine imports this package to ensure registration
happens before evaluation, rather than each yoga module needing to be
imported manually and separately.

Phase 1 (v2.0.0): Original 11 yoga modules.
Phase 2 (v2.1.0 "Vistara"): composite_yogas added for multi-planet/house yogas.
"""

from apps.api.services.yogas import (  # noqa: F401
    arishta_yoga,
    chandra_yoga,
    composite_yogas,
    dhana_yoga,
    gajakesari,
    nabhasa_yoga,
    neecha_bhanga,
    other_classical_yogas,
    panch_mahapurusha,
    raja_yoga,
    sanyasa_yoga,
    solar_yogas,
)
