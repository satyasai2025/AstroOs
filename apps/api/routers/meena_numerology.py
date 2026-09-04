"""
FastAPI Router for Meena's Numerology Engine in AstroOS.
Provides story-driven life reports, activity-specific date finder, repeated numbers scanner, and help concepts.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from apps.api.schemas.meena_numerology import (
    MeenaNumerologyRequest,
    MeenaStoryReportResponse,
    ActivityFinderRequest,
    ActivityFinderResponse,
    RepeatedNumberScanRequest,
    RepeatedNumberScanResponse,
    MeenaHelpResponse,
)
from apps.api.services.meena_numerology_engine import AstroOSMeenaEngine

router = APIRouter(
    prefix="/numerology/meena",
    tags=["Meena Numerology Engine"]
)

# Maximum future projection window
MAX_FUTURE_YEARS = 5


@router.post("/report", response_model=MeenaStoryReportResponse)
async def generate_meena_story_report(
    payload: MeenaNumerologyRequest
):
    """
    Generates a personalized, jargon-free Life Story & Timing report
    based on Meena's Numerology Principles.
    Limits timing queries to a 5-year window.
    """
    current_year = datetime.now().year
    target_year = payload.target_year or current_year

    if target_year > current_year + MAX_FUTURE_YEARS:
        raise HTTPException(
            status_code=400,
            detail=f"Timing projections are limited to a 5-year window (up to {current_year + MAX_FUTURE_YEARS}) to keep focus on actionable, present-centered life chapters."
        )

    try:
        report = AstroOSMeenaEngine.generate_story_report(
            day=payload.day,
            month=payload.month,
            year=payload.year,
            full_name=payload.full_name,
            public_name=payload.public_name,
            daily_name=payload.daily_name,
            target_year=target_year,
            target_month=payload.target_month or 9,
        )
        return report
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")


@router.post("/activity-finder", response_model=ActivityFinderResponse)
async def find_activity_dates(
    payload: ActivityFinderRequest
):
    """
    Returns the best calendar dates in a target month for specific real-world activities
    (shopping deals, luxury, career interviews, property, travel, etc.).
    Limits queries to a 5-year window.
    """
    current_year = datetime.now().year
    target_year = payload.target_year or current_year

    if target_year > current_year + MAX_FUTURE_YEARS:
        raise HTTPException(
            status_code=400,
            detail=f"Activity date finding is limited to a 5-year window (up to {current_year + MAX_FUTURE_YEARS})."
        )

    try:
        best_dates, reasoning, advice = AstroOSMeenaEngine.get_activity_dates(
            activity_category=payload.activity_category,
            day=payload.day,
            month=payload.month,
            target_year=target_year,
            target_month=payload.target_month,
        )

        return ActivityFinderResponse(
            activity_category=payload.activity_category,
            target_month=payload.target_month,
            target_year=target_year,
            recommended_dates=best_dates[:8],
            reasoning=reasoning,
            actionable_advice=advice
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Activity finder error: {str(e)}")


@router.post("/scan-repeated-number", response_model=RepeatedNumberScanResponse)
async def scan_repeated_number(
    payload: RepeatedNumberScanRequest
):
    """
    Interprets repeated synchronicity numbers (1111, 222, 333, 444, 555, 777, 888, 999, 000)
    using subconscious alignment and cognitive alertness frameworks.
    """
    current_year = datetime.now().year
    target_year = payload.target_year or current_year

    if target_year > current_year + MAX_FUTURE_YEARS:
        raise HTTPException(
            status_code=400,
            detail=f"Timing projections are limited to a 5-year window (up to {current_year + MAX_FUTURE_YEARS})."
        )

    try:
        return AstroOSMeenaEngine.scan_repeated_number(
            sequence=payload.sequence,
            day=payload.day,
            month=payload.month,
            year=payload.year,
            target_year=target_year
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synchronicity scan error: {str(e)}")


@router.get("/help", response_model=MeenaHelpResponse)
async def get_meena_method_help():
    """
    Returns core philosophical and practical concepts of Meena's Numerology Method
    (2GB mental space rule, 90-minute emotional window, sound vibration vs spelling, etc.).
    """
    try:
        return AstroOSMeenaEngine.get_help_concepts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Help retrieval error: {str(e)}")


# Direct alias router for /numerology/* endpoints
alias_router = APIRouter(
    prefix="/numerology",
    tags=["Numerology"]
)
alias_router.add_api_route("/report", generate_meena_story_report, methods=["POST"], response_model=MeenaStoryReportResponse)
alias_router.add_api_route("/activity-finder", find_activity_dates, methods=["POST"], response_model=ActivityFinderResponse)
alias_router.add_api_route("/scan-repeated-number", scan_repeated_number, methods=["POST"], response_model=RepeatedNumberScanResponse)
alias_router.add_api_route("/help", get_meena_method_help, methods=["GET"], response_model=MeenaHelpResponse)

