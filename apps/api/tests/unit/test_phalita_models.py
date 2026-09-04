"""
Unit tests for Phalita Models (Weight Rectifier, Dense MLP, Mixture of Experts).
"""

import pytest
import torch

from apps.api.services.phalita_core.dataset_pipeline import DatasetBundle, DatasetTemporalSlice
from apps.api.services.phalita_models.baseline_mlp import BaselineMLPTrainer, PhalitaDenseMLP
from apps.api.services.phalita_models.phalita_moe import PhalitaMoE, PhalitaMoETrainer
from apps.api.services.phalita_models.weight_rectifier import RectifiedWeights, WeightRectifier


@pytest.fixture
def sample_dataset_bundle():
    """Construct mock dataset bundle with positive events and negative controls."""
    train_slices = []
    val_slices = []

    # 10 positive event slices (high features)
    for i in range(10):
        feat = [0.8] * 128
        feat[108] = 1.2  # Yoga
        feat[109] = 0.9  # MD
        feat[110] = 0.8  # AD
        feat[112] = 0.9  # Domain potential
        train_slices.append(
            DatasetTemporalSlice(
                slice_id=f"tr_pos_{i}",
                person_id=f"p_tr_{i}",
                split="TRAIN",
                domain="career",
                slice_start=None,
                slice_end=None,
                label=1,
                active_md_lord="sun",
                active_ad_lord="moon",
                features=feat,
            )
        )

    # 30 negative control slices (low/neutral features)
    for i in range(30):
        feat = [-0.3] * 128
        feat[108] = -0.5
        feat[109] = -0.4
        feat[110] = -0.3
        feat[112] = -0.5
        train_slices.append(
            DatasetTemporalSlice(
                slice_id=f"tr_neg_{i}",
                person_id=f"p_tr_neg_{i}",
                split="TRAIN",
                domain="career",
                slice_start=None,
                slice_end=None,
                label=0,
                active_md_lord="saturn",
                active_ad_lord="rahu",
                features=feat,
            )
        )

    # Validation slices
    for i in range(5):
        feat = [0.7] * 128
        val_slices.append(
            DatasetTemporalSlice(
                slice_id=f"val_pos_{i}",
                person_id=f"p_val_{i}",
                split="VALIDATION",
                domain="career",
                slice_start=None,
                slice_end=None,
                label=1,
                active_md_lord="sun",
                active_ad_lord="jupiter",
                features=feat,
            )
        )
    for i in range(15):
        feat = [-0.2] * 128
        val_slices.append(
            DatasetTemporalSlice(
                slice_id=f"val_neg_{i}",
                person_id=f"p_val_neg_{i}",
                split="VALIDATION",
                domain="career",
                slice_start=None,
                slice_end=None,
                label=0,
                active_md_lord="saturn",
                active_ad_lord="ketu",
                features=feat,
            )
        )

    return DatasetBundle(
        train_slices=train_slices,
        val_slices=val_slices,
        calib_slices=val_slices[:5],
        holdout_slices=val_slices,
        total_persons=20,
        total_events=15,
        total_controls=45,
    )


def test_weight_rectifier_optimization(sample_dataset_bundle):
    rectifier = WeightRectifier(learning_rate=0.1, max_epochs=5)
    weights, report = rectifier.train_rectification(sample_dataset_bundle)

    assert isinstance(weights, RectifiedWeights)
    assert report["epochs"] == 5
    assert "val_metrics" in report
    assert report["val_metrics"]["f1_score"] >= 0.0


def test_baseline_mlp_forward_and_training(sample_dataset_bundle):
    trainer = BaselineMLPTrainer(epochs=5, batch_size=8)
    model, report = trainer.train_model(sample_dataset_bundle)

    assert isinstance(model, PhalitaDenseMLP)
    assert report["epochs"] == 5

    # Test forward pass with tensor
    test_x = torch.randn(4, 128)
    probs = trainer.predict_proba(model, test_x)
    assert probs.shape == (4,)
    assert (probs >= 0.0).all() and (probs <= 1.0).all()


def test_phalita_moe_architecture(sample_dataset_bundle):
    trainer = PhalitaMoETrainer(epochs=5, batch_size=8)
    moe_model, report = trainer.train_moe(sample_dataset_bundle)

    assert isinstance(moe_model, PhalitaMoE)
    assert report["epochs"] == 5

    # Test expert attention distribution
    test_x = torch.randn(6, 128)
    logits, gates = moe_model(test_x)
    assert logits.shape == (6,)
    assert gates.shape == (6, 3)
    # Gating weights across experts must sum to 1.0 per sample
    assert torch.allclose(gates.sum(dim=-1), torch.ones(6), atol=1e-5)
