"""
AstroOS — Deterministic Baseline Engine
=======================================
Implements the complete deterministic Phalita baseline error and ALL 8 secondary metrics
strictly per Section 11 of 'Phalita MoE AI Model' (phalita-moe-ai-model.md):

  - F_det(t) = deterministic Phalita score
  - error(t) = F_det(t) - actual(t)
  - Primary metric: SD (Standard deviation of error)
  - 8 Secondary metrics:
      1. correlation (Pearson r)
      2. direction accuracy (%)
      3. peak/trough timing error
      4. volatility fit (Ratio of standard deviations)
      5. drawdown error (Max drawdown absolute difference)
      6. walk-forward stability (Rolling window SD dispersion)
      7. probability calibration (Brier score)
      8. residual autocorrelation (Lag-1 autocorrelation)
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DeterministicBaselineReport:
    """Statistical performance metrics strictly per Section 11 of Jha's paper."""
    sample_count: int
    mean_error: float
    standard_deviation_error: float        # Primary metric: SD
    mean_absolute_error: float

    # All 8 Secondary Metrics per Section 11
    correlation: float                     # 1. correlation
    direction_accuracy_pct: float          # 2. direction accuracy
    peak_trough_timing_error: float        # 3. peak/trough timing
    volatility_fit: float                  # 4. volatility fit
    drawdown_error: float                  # 5. drawdown error
    walk_forward_stability: float          # 6. walk-forward stability
    probability_calibration: float         # 7. probability calibration
    residual_autocorrelation: float        # 8. residual autocorrelation


class DeterministicBaselineEngine:
    """Computes baseline error metrics for pure Shastric deterministic scoring."""

    @staticmethod
    def _compute_max_drawdown(series: List[float]) -> float:
        """Computes maximum peak-to-trough decline in cumulative series."""
        if not series:
            return 0.0
        peak = series[0]
        max_dd = 0.0
        for x in series:
            if x > peak:
                peak = x
            dd = peak - x
            if dd > max_dd:
                max_dd = dd
        return max_dd

    @staticmethod
    def _find_extrema_indices(series: List[float]) -> List[int]:
        """Finds local peaks and troughs in a time series."""
        extrema = []
        for i in range(1, len(series) - 1):
            if (series[i] > series[i - 1] and series[i] > series[i + 1]) or \
               (series[i] < series[i - 1] and series[i] < series[i + 1]):
                extrema.append(i)
        return extrema

    @classmethod
    def evaluate(
        cls,
        predictions: List[float],
        actuals: List[float],
        rolling_window_size: int = 5,
    ) -> DeterministicBaselineReport:
        """
        Evaluates predictions vs ground truth actuals per Jha's Section 11 equations.
        """
        n = len(predictions)
        if n == 0 or len(actuals) != n:
            raise ValueError("Predictions and actuals must be non-empty and of equal length.")

        errors = [p - a for p, a in zip(predictions, actuals)]
        mean_err = sum(errors) / n
        mae = sum(abs(e) for e in errors) / n

        # Primary Metric: Standard Deviation of Error (SD)
        var_err = sum((e - mean_err) ** 2 for e in errors) / n
        sd_err = math.sqrt(var_err)

        # 1. Pearson Correlation (r)
        mean_p = sum(predictions) / n
        mean_a = sum(actuals) / n
        num = sum((p - mean_p) * (a - mean_a) for p, a in zip(predictions, actuals))
        den_p = math.sqrt(sum((p - mean_p) ** 2 for p in predictions))
        den_a = math.sqrt(sum((a - mean_a) ** 2 for a in actuals))
        corr = (num / (den_p * den_a)) if (den_p > 1e-9 and den_a > 1e-9) else 0.0

        # 2. Direction Accuracy (%)
        dir_matches = sum(
            1 for p, a in zip(predictions, actuals)
            if (p >= 0 and a >= 0) or (p < 0 and a < 0)
        )
        dir_acc = (dir_matches / n) * 100.0

        # 3. Peak/Trough Timing Error
        p_extrema = cls._find_extrema_indices(predictions)
        a_extrema = cls._find_extrema_indices(actuals)
        if p_extrema and a_extrema:
            timing_diffs = []
            for pe in p_extrema:
                closest_a = min(a_extrema, key=lambda ae: abs(ae - pe))
                timing_diffs.append(abs(pe - closest_a))
            peak_timing_err = sum(timing_diffs) / len(timing_diffs)
        else:
            peak_timing_err = 0.0

        # 4. Volatility Fit (Ratio of standard deviations: sigma_pred / sigma_actual)
        sd_p = den_p / math.sqrt(n) if n > 0 else 1.0
        sd_a = den_a / math.sqrt(n) if n > 0 else 1.0
        vol_fit = round(sd_p / sd_a, 4) if sd_a > 1e-9 else 1.0

        # 5. Drawdown Error (|MaxDD_pred - MaxDD_actual|)
        dd_p = cls._compute_max_drawdown(predictions)
        dd_a = cls._compute_max_drawdown(actuals)
        dd_error = abs(dd_p - dd_a)

        # 6. Walk-Forward Stability (Standard deviation of SD error across rolling slices)
        if n >= rolling_window_size * 2:
            rolling_sds = []
            for start_idx in range(0, n - rolling_window_size + 1, rolling_window_size // 2 or 1):
                slice_errors = errors[start_idx : start_idx + rolling_window_size]
                s_mean = sum(slice_errors) / len(slice_errors)
                s_var = sum((se - s_mean) ** 2 for se in slice_errors) / len(slice_errors)
                rolling_sds.append(math.sqrt(s_var))
            mean_rsd = sum(rolling_sds) / len(rolling_sds)
            walk_forward_stab = math.sqrt(sum((rs - mean_rsd) ** 2 for rs in rolling_sds) / len(rolling_sds))
        else:
            walk_forward_stab = 0.0

        # 7. Probability Calibration (Brier Score on directional probability)
        # Convert prediction to sigmoid probability: p_hat = 1 / (1 + exp(-p))
        brier_scores = []
        for p, a in zip(predictions, actuals):
            p_prob = 1.0 / (1.0 + math.exp(-max(-20.0, min(20.0, p))))
            y_true = 1.0 if a > 0 else 0.0
            brier_scores.append((p_prob - y_true) ** 2)
        brier_calib = sum(brier_scores) / n

        # 8. Residual Autocorrelation (Lag-1 Autocorrelation of errors)
        if n > 1 and var_err > 1e-9:
            num_ac = sum((errors[t] - mean_err) * (errors[t - 1] - mean_err) for t in range(1, n))
            den_ac = sum((e - mean_err) ** 2 for e in errors)
            res_autocorr = num_ac / den_ac if den_ac > 1e-9 else 0.0
        else:
            res_autocorr = 0.0

        return DeterministicBaselineReport(
            sample_count=n,
            mean_error=round(mean_err, 4),
            standard_deviation_error=round(sd_err, 4),
            mean_absolute_error=round(mae, 4),
            correlation=round(corr, 4),
            direction_accuracy_pct=round(dir_acc, 2),
            peak_trough_timing_error=round(peak_timing_err, 4),
            volatility_fit=round(vol_fit, 4),
            drawdown_error=round(dd_error, 4),
            walk_forward_stability=round(walk_forward_stab, 4),
            probability_calibration=round(brier_calib, 4),
            residual_autocorrelation=round(res_autocorr, 4),
        )
