"""
AstroOS — Medical Jyotish Engine (Alias / Canonical Wrapper)
============================================================
Exposes MedicalResearchService and disease vulnerability calculation models.
"""

from apps.api.services.medical_research_service import (
    MedicalResearchService,
    MedicalCaseRecord,
    MedicalVulnerabilityResult,
    DISEASE_DEFINITIONS,
    RASHI_NAMES,
    ELEMENTS
)

# Export canonical service
MedicalJyotishEngine = MedicalResearchService
