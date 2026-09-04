"""
AstroOS — Noise Diagnostic Engine
=================================
Implements the 4-quadrant noise diagnostic classification strictly per Section 18
of 'Phalita MoE AI Model' (phalita-moe-ai-model.md):

  - Section 18.1: DataNoise     (Incomplete data, timestamp mismatch, coordinates uncertainty)
  - Section 18.2: RulesNoise    (Weak-field fuzzy zones, contradictory rule alignments)
  - Section 18.3: ModelNoise    (Linear regime breakdown, high curvature residuals)
  - Section 18.4: UsefulNoise   (Genuine stochastic volatility envelope)
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class NoiseDiagnosticReport:
    """Diagnostic profile across the four canonical noise categories."""
    data_noise_score: float          # [0.0, 1.0]
    rules_noise_score: float         # [0.0, 1.0]
    model_noise_score: float         # [0.0, 1.0]
    useful_noise_bandwidth: float    # Width of expected volatility envelope
    dominant_noise_category: str     # "DATA", "RULES", "MODEL", "CLEAN"
    is_prediction_trustworthy: bool  # True if composite noise < threshold


class NoiseDiagnosticEngine:
    """Classifies and isolates noise categories strictly per Jha's Section 18."""

    @classmethod
    def diagnose(
        cls,
        latitude: float,
        longitude: float,
        deterministic_score: float,
        planet_block_total: float,
        residual_error: float,
        varga_opposition_index: float = 0.0,
    ) -> NoiseDiagnosticReport:
        """
        Diagnoses noise components given planetary feature state and model residuals.
        """
        # 1. Data Noise (Section 18.1): Coordinate or timestamp anomalies
        data_noise = 0.0
        if latitude == 0.0 or longitude == 0.0 or abs(latitude) > 90.0 or abs(longitude) > 180.0:
            data_noise = 1.0
        # Low deterministic score also indicates data noise
        if deterministic_score < 0.3:
            data_noise = max(data_noise, 0.7)

        # 2. Rules Noise (Section 18.2): Weak-field fuzzy zones or opposing varga conflicts
        # Weak-field zone: |PlanetBlock| < 0.15 where noise dominates signal
        rules_noise = 0.0
        if abs(planet_block_total) < 0.15:
            rules_noise = max(rules_noise, 0.8)
        if varga_opposition_index > 0.6:  # Strong D1 vs D9 cancellation tension
            rules_noise = max(rules_noise, 0.7)
        # Low deterministic score with moderate planet block also indicates rules noise
        if deterministic_score < 0.5 and abs(planet_block_total) < 0.5:
            rules_noise = max(rules_noise, 0.6)

        # 3. Model Noise (Section 18.3): Non-linear breakdown when residuals are extreme
        model_noise = 0.0
        if abs(deterministic_score) > 15.0 or abs(residual_error) > 5.0:
            model_noise = min(1.0, abs(residual_error) / 10.0)

        # 4. Useful Noise Band (Section 18.4): Expected stochastic envelope
        useful_band = round(0.15 * max(1.0, abs(deterministic_score)), 4)

        # Dominant Category Determination
        scores = {
            "DATA": data_noise,
            "RULES": rules_noise,
            "MODEL": model_noise,
        }
        dominant_cat = max(scores, key=scores.get)
        if scores[dominant_cat] < 0.3:
            dominant_cat = "CLEAN"

        # Trustworthiness check
        is_trustworthy = (data_noise < 0.5) and (rules_noise < 0.75) and (model_noise < 0.75)

        return NoiseDiagnosticReport(
            data_noise_score=round(data_noise, 4),
            rules_noise_score=round(rules_noise, 4),
            model_noise_score=round(model_noise, 4),
            useful_noise_bandwidth=useful_band,
            dominant_noise_category=dominant_cat,
            is_prediction_trustworthy=is_trustworthy,
        )
