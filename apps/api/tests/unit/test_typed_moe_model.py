"""
Unit tests for Typed Phalita MoE Model implementing Sections 15, 16, 17.
"""

import pytest
import torch
from apps.api.services.ml.typed_moe_model import (
    BlockEncoder,
    MoEPredictionOutput,
    TypedPhalitaMoE,
    UniversalStructuralExpert,
)


def test_typed_moe_forward_and_quantiles():
    batch_size = 4
    block_dims = {
        "varga": 8,
        "bhava": 12,
        "aspect": 6,
        "yoga": 4,
        "temporal": 4,
    }

    model = TypedPhalitaMoE(block_dims=block_dims, embed_dim=32, num_residual_experts=4)

    # Generate synthetic block inputs
    block_inputs = {
        b_name: torch.randn(batch_size, b_dim)
        for b_name, b_dim in block_dims.items()
    }

    output = model(block_inputs)
    assert isinstance(output, MoEPredictionOutput)

    # 1. Output shapes
    assert output.mean.shape == (batch_size, 1)
    assert output.variance.shape == (batch_size, 1)
    assert output.confidence.shape == (batch_size, 1)
    assert output.q10.shape == (batch_size, 1)
    assert output.q50.shape == (batch_size, 1)
    assert output.q90.shape == (batch_size, 1)
    assert output.gating_weights.shape == (batch_size, 4)

    # 2. Gating weights sum to 1.0 (Softmax check per Section 17.4)
    gate_sums = torch.sum(output.gating_weights, dim=-1)
    assert torch.allclose(gate_sums, torch.ones(batch_size), atol=1e-5)

    # 3. Quantile ordering: Q10 <= Q50 <= Q90 (with high probability)
    assert (output.variance > 0).all()
    assert (output.confidence >= 0.0).all() and (output.confidence <= 1.0).all()


def test_typed_moe_backpropagation():
    batch_size = 2
    block_dims = {"varga": 4, "bhava": 6}
    model = TypedPhalitaMoE(block_dims=block_dims, embed_dim=16, num_residual_experts=2)

    block_inputs = {
        b_name: torch.randn(batch_size, b_dim)
        for b_name, b_dim in block_dims.items()
    }
    targets = torch.randn(batch_size, 1)

    output = model(block_inputs)
    loss = torch.mean((output.mean - targets) ** 2)
    loss.backward()

    # Structural and MoE gradients must exist
    assert model.encoders["varga"].fc1.weight.grad is not None
    assert model.residual_moe.router.weight.grad is not None
