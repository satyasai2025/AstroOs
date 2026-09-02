"""
AstroOS — Weight Rectification Engine
=====================================
Implements the complete weight rectification cycle strictly per Section 13
of 'Phalita MoE AI Model' (phalita-moe-ai-model.md):

  - Section 13.1: Coordinate Rectification (W_i -> W_i + delta)
  - Section 13.2: ALL 12 Block-Level Rectification Groups:
      1. planetary_natural_weights
      2. functional_nature_weights
      3. house_weights
      4. aspect_falloff_weights
      5. dignity_weights
      6. varga_weights
      7. temporal_level_weights
      8. yoga_class_weights
      9. d2_deity_weights
     10. vry_inversion_weights
     11. pada_arudha_weights
     12. gochara_activation_weights
  - Section 13.3: Iterative Repeat Cycle (Accept iff SD_train < baseline AND SD_val < baseline)
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Callable, Dict, List, Optional, Tuple


@dataclass
class RectificationState:
    """
    Section 13.2: Complete State of all 12 Classical Weight Groups.
    """
    # 1. Planetary natural weights (Line 743)
    planetary_natural_weights: Dict[str, float] = field(default_factory=lambda: {
        "jupiter": 1.0, "venus": 1.0, "moon": 0.5, "mercury": 0.5,
        "sun": -0.25, "mars": -1.0, "saturn": -1.0, "rahu": -1.0, "ketu": -1.0,
    })

    # 2. Functional benefic/malefic weights (Line 745)
    functional_nature_weights: Dict[str, float] = field(default_factory=lambda: {
        "trikona_lord": 1.0, "kendra_lord": 0.75, "trishadaya_lord": -0.75, "dusthana_lord": -1.0,
    })

    # 3. House weights (Line 747)
    house_weights: Dict[str, float] = field(default_factory=lambda: {
        f"H{i}": 1.0 for i in range(1, 13)
    })

    # 4. Aspect falloff weights (Line 749)
    aspect_falloff_weights: Dict[str, float] = field(default_factory=lambda: {
        "max_orb_deg": 8.0, "half_orb_strength": 0.5, "exact_aspect_strength": 1.0,
    })

    # 5. Dignity weights (Line 751)
    dignity_weights: Dict[str, float] = field(default_factory=lambda: {
        "exalted": 60.0, "moolatrikona": 45.0, "own": 30.0, "great_friend": 22.5,
        "friend": 15.0, "sama": 7.5, "enemy": 3.75, "great_enemy": 1.875, "debilitated": 0.0,
    })

    # 6. Varga weights (Line 753)
    varga_weights: Dict[str, float] = field(default_factory=lambda: {
        "D1": 3.5, "D60": 4.0, "D9": 3.0, "D16": 2.0, "D10": 1.5, "D2": 1.0, "D3": 1.0, "D30": 1.0,
    })

    # 7. Temporal-level weights (Line 755)
    temporal_level_weights: Dict[str, float] = field(default_factory=lambda: {
        "annual": 1.0, "monthly": 0.75, "vidasha": 0.50, "gochara": 0.25,
    })

    # 8. Yoga-class weights (Line 757)
    yoga_class_weights: Dict[str, float] = field(default_factory=lambda: {
        "RajaYoga": 1.0, "DhanaYoga": 0.9, "ArishtaYoga": -1.0, "MahapurushaYoga": 1.2,
    })

    # 9. D2 deity weights (Line 759)
    d2_deity_weights: Dict[str, float] = field(default_factory=lambda: {
        "Deva": 1.0, "Pitri": 0.8,
    })

    # 10. VRY/inversion weights (Line 761)
    vry_inversion_weights: Dict[str, float] = field(default_factory=lambda: {
        "Harsha": 0.8, "Sarala": 0.8, "Vimala": 0.8,
    })

    # 11. Pada / Arudha weights (Line 763)
    pada_arudha_weights: Dict[str, float] = field(default_factory=lambda: {
        "ArudhaLagna": 1.0, "DhanaArudha_A2": 0.8, "KarmaArudha_A10": 0.9, "LabhaArudha_A11": 0.85,
    })

    # 12. Gochara activation weights (Line 765)
    gochara_activation_weights: Dict[str, float] = field(default_factory=lambda: {
        "vedha_suppression": 0.7, "kakshya_activation": 1.0, "ashtakavarga_bindu_scale": 0.125,
    })


@dataclass(frozen=True)
class RectificationStepResult:
    """Outcome of a single coordinate or block rectification step."""
    parameter_group: str
    parameter_name: str
    old_value: float
    new_value: float
    old_train_sd: float
    new_train_sd: float
    old_val_sd: float
    new_val_sd: float
    is_accepted: bool
    improvement_train_pct: float
    improvement_val_pct: float


class WeightRectificationEngine:
    """
    Section 13: Weight Rectification Engine.
    Empirical refinement cycle for all 12 classical Shastric weight groups.
    """

    @staticmethod
    def compute_sd(predictions: List[float], targets: List[float]) -> float:
        """Computes Standard Deviation of error (SD)."""
        n = len(predictions)
        if n == 0:
            return 0.0
        errors = [p - t for p, t in zip(predictions, targets)]
        mean_e = sum(errors) / n
        var_e = sum((e - mean_e) ** 2 for e in errors) / n
        return math.sqrt(var_e)

    @classmethod
    def coordinate_rectification_step(
        cls,
        group_name: str,
        param_group: Dict[str, float],
        param_key: str,
        delta: float,
        eval_fn: Callable[[Dict[str, float]], Tuple[List[float], List[float], List[float], List[float]]],
    ) -> RectificationStepResult:
        """
        Section 13.1: Coordinate Rectification.
        Perturbs W_i -> W_i + delta.
        Accepts update ONLY IF both SD_train decreases AND SD_val decreases.
        """
        # Baseline evaluation
        train_p0, train_y, val_p0, val_y = eval_fn(param_group)
        sd_train_0 = cls.compute_sd(train_p0, train_y)
        sd_val_0 = cls.compute_sd(val_p0, val_y)

        old_val = param_group[param_key]
        candidate_val = old_val + delta

        # Candidate evaluation
        test_group = dict(param_group)
        test_group[param_key] = candidate_val
        train_p1, _, val_p1, _ = eval_fn(test_group)
        sd_train_1 = cls.compute_sd(train_p1, train_y)
        sd_val_1 = cls.compute_sd(val_p1, val_y)

        # Acceptance Rule (Section 13.1 lines 737-738)
        # Accepted only if both training and validation SD decrease
        is_accepted = (sd_train_1 < sd_train_0) and (sd_val_1 < sd_val_0)

        imp_train = ((sd_train_0 - sd_train_1) / sd_train_0) * 100.0 if sd_train_0 > 1e-9 else 0.0
        imp_val = ((sd_val_0 - sd_val_1) / sd_val_0) * 100.0 if sd_val_0 > 1e-9 else 0.0

        if is_accepted:
            param_group[param_key] = candidate_val

        return RectificationStepResult(
            parameter_group=group_name,
            parameter_name=param_key,
            old_value=old_val,
            new_value=candidate_val if is_accepted else old_val,
            old_train_sd=round(sd_train_0, 4),
            new_train_sd=round(sd_train_1, 4),
            old_val_sd=round(sd_val_0, 4),
            new_val_sd=round(sd_val_1, 4),
            is_accepted=is_accepted,
            improvement_train_pct=round(imp_train, 2),
            improvement_val_pct=round(imp_val, 2),
        )

    @classmethod
    def run_full_rectification_cycle(
        cls,
        state: RectificationState,
        eval_fn_factory: Callable[[str], Callable[[Dict[str, float]], Tuple[List[float], List[float], List[float], List[float]]]],
        step_sizes: Dict[str, float] = None,
        max_iterations: int = 1,
    ) -> List[RectificationStepResult]:
        """
        Section 13.3: Full Iterative Rectification Cycle across ALL 12 parameter groups.
        """
        if step_sizes is None:
            step_sizes = {
                "planetary_natural": 0.05,
                "functional_nature": 0.05,
                "house": 0.05,
                "aspect_falloff": 0.1,
                "dignity": 1.0,
                "varga": 0.1,
                "temporal_level": 0.05,
                "yoga_class": 0.05,
                "d2_deity": 0.05,
                "vry_inversion": 0.05,
                "pada_arudha": 0.05,
                "gochara_activation": 0.05,
            }

        audit_log: List[RectificationStepResult] = []

        groups = [
            ("planetary_natural", state.planetary_natural_weights),
            ("functional_nature", state.functional_nature_weights),
            ("house", state.house_weights),
            ("aspect_falloff", state.aspect_falloff_weights),
            ("dignity", state.dignity_weights),
            ("varga", state.varga_weights),
            ("temporal_level", state.temporal_level_weights),
            ("yoga_class", state.yoga_class_weights),
            ("d2_deity", state.d2_deity_weights),
            ("vry_inversion", state.vry_inversion_weights),
            ("pada_arudha", state.pada_arudha_weights),
            ("gochara_activation", state.gochara_activation_weights),
        ]

        for _ in range(max_iterations):
            for group_name, group_dict in groups:
                eval_fn = eval_fn_factory(group_name)
                delta = step_sizes.get(group_name, 0.05)
                for k in list(group_dict.keys()):
                    res = cls.coordinate_rectification_step(
                        group_name=group_name,
                        param_group=group_dict,
                        param_key=k,
                        delta=delta,
                        eval_fn=eval_fn,
                    )
                    audit_log.append(res)

        return audit_log
