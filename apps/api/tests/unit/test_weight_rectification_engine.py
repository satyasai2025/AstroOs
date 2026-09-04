"""
Unit tests for Weight Rectification Engine implementing all 12 Section 13.2 groups.
"""

import pytest
from apps.api.services.ml.weight_rectification_engine import (
    RectificationState,
    RectificationStepResult,
    WeightRectificationEngine,
)


def test_rectification_state_contains_all_12_groups():
    state = RectificationState()
    
    # Check all 12 canonical groups from Jha Section 13.2 (lines 743-765)
    assert len(state.planetary_natural_weights) == 9
    assert len(state.functional_nature_weights) == 4
    assert len(state.house_weights) == 12
    assert "max_orb_deg" in state.aspect_falloff_weights
    assert "exalted" in state.dignity_weights
    assert len(state.varga_weights) >= 6
    assert len(state.temporal_level_weights) == 4
    assert "RajaYoga" in state.yoga_class_weights
    assert "Deva" in state.d2_deity_weights
    assert "Harsha" in state.vry_inversion_weights
    assert "ArudhaLagna" in state.pada_arudha_weights
    assert "vedha_suppression" in state.gochara_activation_weights


def test_coordinate_rectification_accepted_when_sd_decreases():
    param_group = {"jupiter": 1.0, "venus": 1.0}
    
    # Mock evaluation where increasing jupiter reduces error across multi-sample dataset
    def mock_eval(weights):
        j_val = weights["jupiter"]
        train_p = [j_val * 1.0, j_val * 3.0]
        train_y = [1.2 * 1.0, 1.2 * 3.0]
        val_p = [j_val * 1.0, j_val * 3.0]
        val_y = [1.2 * 1.0, 1.2 * 3.0]
        return train_p, train_y, val_p, val_y

    res = WeightRectificationEngine.coordinate_rectification_step(
        group_name="planetary_natural",
        param_group=param_group,
        param_key="jupiter",
        delta=0.1,
        eval_fn=mock_eval,
    )

    assert res.is_accepted is True
    assert res.new_value == 1.1
    assert res.new_train_sd < res.old_train_sd
    assert res.new_val_sd < res.old_val_sd
    assert param_group["jupiter"] == 1.1


def test_full_rectification_cycle_runs_across_all_12_groups():
    state = RectificationState()
    
    def eval_factory(group_name):
        def mock_eval(weights):
            return [1.0, 2.0], [1.0, 2.0], [1.0, 2.0], [1.0, 2.0]
        return mock_eval

    logs = WeightRectificationEngine.run_full_rectification_cycle(
        state=state,
        eval_fn_factory=eval_factory,
        max_iterations=1,
    )

    # Must log updates across all parameters in all 12 groups
    groups_logged = {log.parameter_group for log in logs}
    assert len(groups_logged) == 12
    assert len(logs) > 50  # Over 50 individual weight parameters tested
