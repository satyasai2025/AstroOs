"""
AstroOS — Intelligence Event Prediction Modules (Chapter 07)
"""

from apps.api.services.intelligence.events.marriage import MarriagePredictor
from apps.api.services.intelligence.events.career import CareerPredictor
from apps.api.services.intelligence.events.health import HealthPredictor
from apps.api.services.intelligence.events.accident import AccidentPredictor

__all__ = [
    "MarriagePredictor",
    "CareerPredictor",
    "HealthPredictor",
    "AccidentPredictor",
]
