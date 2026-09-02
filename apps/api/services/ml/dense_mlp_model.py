"""
AstroOS — Dense MLP Baseline Model
==================================
Implements the Dense Multi-Layer Perceptron (MLP) baseline strictly per Section 12
of 'Phalita MoE AI Model' (phalita-moe-ai-model.md):

  - Input: X = Phalita signed feature vector
  - Topology: Input(N) -> Dense(512) -> Dense(256) -> Dense(128) -> Multi-Task Heads
  - Multi-Task Heads:
      1. Point Estimate (Mean head)
      2. Uncertainty / Variance (Gaussian NLL log-variance head)
      3. Directional Probability (Sigmoid head)
  - Loss Functions: Huber Loss, Gaussian NLL, Directional BCE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass(frozen=True)
class MLPOutput:
    """Multi-task output predictions from Dense MLP."""
    mean: torch.Tensor
    variance: torch.Tensor
    direction_prob: torch.Tensor


class PhalitaDenseMLP(nn.Module):
    """
    Section 12: Dense MLP Baseline Model.
    Architecture:
      Input (N) -> Linear(512) -> LayerNorm -> ReLU -> Dropout
                -> Linear(256) -> LayerNorm -> ReLU -> Dropout
                -> Linear(128) -> LayerNorm -> ReLU
                -> Heads: [Mean, LogVar, DirectionProb]
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dims: Tuple[int, int, int] = (512, 256, 128),
        dropout_rate: float = 0.1,
    ):
        super().__init__()
        self.input_dim = input_dim

        # Backbone Layers (Section 12 lines 710-712)
        h1, h2, h3 = hidden_dims
        self.fc1 = nn.Linear(input_dim, h1)
        self.norm1 = nn.LayerNorm(h1)
        self.drop1 = nn.Dropout(dropout_rate)

        self.fc2 = nn.Linear(h1, h2)
        self.norm2 = nn.LayerNorm(h2)
        self.drop2 = nn.Dropout(dropout_rate)

        self.fc3 = nn.Linear(h2, h3)
        self.norm3 = nn.LayerNorm(h3)

        # Multi-Task Prediction Heads (Section 12 lines 713-723)
        self.mean_head = nn.Linear(h3, 1)        # Continuous event return / score
        self.logvar_head = nn.Linear(h3, 1)      # Heteroscedastic uncertainty (log sigma^2)
        self.direction_head = nn.Linear(h3, 1)    # Directional up/down probability

    def forward(self, x: torch.Tensor) -> MLPOutput:
        h = F.relu(self.norm1(self.fc1(x)))
        h = self.drop1(h)

        h = F.relu(self.norm2(self.fc2(h)))
        h = self.drop2(h)

        h = F.relu(self.norm3(self.fc3(h)))

        mean = self.mean_head(h)
        logvar = self.logvar_head(h)
        # Clamped variance to avoid numerical instabilities
        variance = torch.exp(torch.clamp(logvar, min=-6.0, max=4.0))
        direction_prob = torch.sigmoid(self.direction_head(h))

        return MLPOutput(mean=mean, variance=variance, direction_prob=direction_prob)

    @staticmethod
    def compute_loss(
        predictions: MLPOutput,
        targets: torch.Tensor,
        huber_delta: float = 1.0,
        use_gaussian_nll: bool = True,
    ) -> Dict[str, torch.Tensor]:
        """
        Computes composite loss strictly per Section 12:
          - Huber Loss for robust outlier handling
          - Gaussian NLL for uncertainty calibration: 0.5 * (log(var) + (y - mu)^2 / var)
          - Directional BCE for directional matching
        """
        # 1. Huber Loss (Robust baseline)
        huber_loss = F.huber_loss(predictions.mean, targets, delta=huber_delta)

        # 2. Gaussian NLL Loss
        if use_gaussian_nll:
            gnll_loss = 0.5 * (torch.log(predictions.variance) + ((targets - predictions.mean) ** 2) / predictions.variance).mean()
        else:
            gnll_loss = torch.tensor(0.0, device=targets.device)

        # 3. Directional BCE Loss
        target_dir = (targets > 0).float()
        bce_loss = F.binary_cross_entropy(predictions.direction_prob, target_dir)

        # Composite total loss
        total_loss = huber_loss + 0.3 * gnll_loss + 0.2 * bce_loss

        return {
            "total_loss": total_loss,
            "huber_loss": huber_loss,
            "gnll_loss": gnll_loss,
            "bce_loss": bce_loss,
        }
