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
