"""
AstroOS — Technique Fixtures / Definitions

Concrete TechniqueDefinitions live here, one module per technique, each
registering (a) its evaluable rules into the code rule_registry and (b) the
technique itself into the technique_registry. Importing this package registers
every bundled technique — the same import-side-effect pattern used by
services/rules/ and the jaimini_yogas/ package.

The framework core (domain/technique.py, technique_engine.py, ...) contains NO
technique-specific knowledge. All domain content lives in these modules, so the
NEXT technique is a new file here — never a change to the framework.
"""

from __future__ import annotations

from apps.api.services.techniques import eye_health as _eye_health  # noqa: F401
from apps.api.services.techniques import event_timing_migrated as _event_timing_migrated  # noqa: F401
from apps.api.services.techniques import gajakesari_yoga as _gajakesari_yoga  # noqa: F401
from apps.api.services.techniques import panch_mahapurusha as _panch_mahapurusha  # noqa: F401
from apps.api.services.techniques import marriage_timing as _marriage_timing  # noqa: F401
from apps.api.services.techniques import wealth_dhana as _wealth_dhana  # noqa: F401
from apps.api.services.techniques import timing_events as _timing_events  # noqa: F401

# Astro-Cartography / Relocation fixtures (built on RelocationEngine facts).
from apps.api.services.techniques import relocated_chart_evaluation as _relocated_chart_evaluation  # noqa: F401
from apps.api.services.techniques import line_type_hierarchy as _line_type_hierarchy  # noqa: F401
from apps.api.services.techniques import map_line_reading as _map_line_reading  # noqa: F401
from apps.api.services.techniques import major_minor_frequencies as _major_minor_frequencies  # noqa: F401
