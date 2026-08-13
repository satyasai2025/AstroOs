"""
AstroOS — Jaimini Yoga Modules (Layer 6: Calculation Engine)

Importing this package registers every Jaimini yoga rule module's
evaluator into jaimini_yoga_registry. JaiminiYogaEngine imports this
package to ensure registration happens before evaluation — identical
structure to apps/api/services/yogas/__init__.py for Parashari yogas.

Deliberately narrow initial scope (5 rules, one per approved category —
see JaiminiYogaEngine's module docstring): only well-established,
citable classical Jaimini principles, no generic Parashari yogas
(already covered by YogaEngine), no experimental/inferred combinations.
"""

from apps.api.services.jaimini_yogas import (  # noqa: F401
    arudha_yoga,
    atmakaraka_dignity_yoga,
    dara_upapada_yoga,
    karakamsa_yoga,
    raja_yoga,
)
