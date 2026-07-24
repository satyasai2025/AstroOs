"""
FastAPI application package for AstroOS API.

This module serves as the main entry point for the FastAPI application,
exposing the core application instance for use in tests, orchestration,
and deployment scenarios.

The primary application is defined in main.py and imported here for
convenient access across the project. This pattern maintains a clean
namespace while ensuring that the application instance is accessible
across different contexts.
"""

from .main import app

# Export for convenience and test compatibility
__all__ = ["app"]