"""
AstroOS — Ephemeris HTTP Schemas

Pydantic models for ephemeris-related API responses.
Only the router layer imports from here; the service layer uses dtos.py.
"""

from typing import Optional

from pydantic import BaseModel, Field

from apps.api.services.ephemeris_service import EphemerisMode


class EphemerisStatusSchema(BaseModel):
    """Embedded in the health-check response."""

    mode: EphemerisMode = Field(
        description=(
            "'swiss_ephemeris' = official .se1 files loaded (high precision); "
            "'moshier' = built-in polynomial fallback (no files, lower precision); "
            "'unknown' = test calculation failed."
        )
    )
    official_data: bool = Field(
        description="True when mode == 'swiss_ephemeris'."
    )
    path: str = Field(description="Absolute path where .se1 files are expected.")
    se1_files: list[str] = Field(
        default_factory=list,
        description="Sorted list of .se1 files found at path.",
    )
    test_longitude: Optional[float] = Field(
        default=None,
        description="Sun longitude at J2000.0 used for detection (degrees, ecliptic).",
    )
    error: Optional[str] = Field(
        default=None,
        description="Set when the probe calculation itself raised a C-library error.",
    )

    model_config = {"from_attributes": True}
