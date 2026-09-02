"""
Unit tests for Dense MLP baseline model implementing Section 12 architecture.
"""

import pytest
import torch
from apps.api.services.ml.dense_mlp_model import MLPOutput, PhalitaDenseMLP


def test_dense_mlp_forward_and_dimensions():
    batch_size = 16
    input_dim = 40  # Sample Phalita feature length
    model = PhalitaDenseMLP(input_dim=input_dim)

    x = torch.randn(batch_size, input_dim)
    output = model(x)

    assert isinstance(output, MLPOutput)
    # Check output shapes
    assert output.mean.shape == (batch_size, 1)
    assert output.variance.shape == (batch_size, 1)
    assert output.direction_prob.shape == (batch_size, 1)

    # Check value ranges
    assert (output.variance > 0.0).all()  # Variance must be strictly positive
    assert ((output.direction_prob >= 0.0) & (output.direction_prob <= 1.0)).all()  # Probabilities in [0, 1]


def test_dense_mlp_loss_computation_and_backward():
    batch_size = 8
    input_dim = 30
    model = PhalitaDenseMLP(input_dim=input_dim)

    x = torch.randn(batch_size, input_dim)
    y = torch.randn(batch_size, 1)

    output = model(x)
    losses = model.compute_loss(output, y)

    assert "total_loss" in losses
    assert "huber_loss" in losses
    assert "gnll_loss" in losses
    assert "bce_loss" in losses

    total_loss = losses["total_loss"]
    assert total_loss.item() > 0.0

    # Test backpropagation
    total_loss.backward()
    assert model.fc1.weight.grad is not None
    assert model.mean_head.weight.grad is not None
