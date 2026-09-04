"""
AstroOS — Typed Phalita MoE (Mixture of Experts) Architecture
=============================================================
Implements the canonical Typed Phalita MoE model strictly per Sections 15, 16, 17
of 'Phalita MoE AI Model' (phalita-moe-ai-model.md):

  - Section 16.1: Universal Structural Experts (Varga, Bhava, Yoga, Aspect, Temporal)
                  *MANDATORY — NEVER omitted or zeroed by the router*
  - Section 16.2: Domain Interpretation Experts (Jataka, Financial, Health, Weather)
  - Section 17.2: Block Encoders (Varga, Bhava, Aspect, Yoga, Temporal)
  - Section 17.4: Router / Soft Gating on Residual Stochastic Experts
  - Section 17.6: Fusion Layer (Mean, Variance, Confidence, Quantiles Q10, Q50, Q90)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass(frozen=True)
class StructuralExpertOutput:
    """Output from an individual universal structural expert (Section 17.5)."""
    score: torch.Tensor
    confidence: torch.Tensor
    embedding: torch.Tensor
    diagnostic_vector: torch.Tensor


@dataclass(frozen=True)
class MoEPredictionOutput:
    """Full comprehensive prediction output from Typed Phalita MoE."""
    mean: torch.Tensor
    variance: torch.Tensor
    confidence: torch.Tensor
    q10: torch.Tensor
    q50: torch.Tensor
    q90: torch.Tensor
    gating_weights: torch.Tensor
    structural_score: torch.Tensor
    residual_score: torch.Tensor


class BlockEncoder(nn.Module):
    """Encodes a specific feature block into a compact latent embedding (Section 17.2)."""

    def __init__(self, input_dim: int, embed_dim: int = 64):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, embed_dim)
        self.norm = nn.LayerNorm(embed_dim)
        self.fc2 = nn.Linear(embed_dim, embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = F.relu(self.norm(self.fc1(x)))
        return F.relu(self.fc2(h))


class UniversalStructuralExpert(nn.Module):
    """
    Section 16.1 & 17.5: Universal Structural Expert.
    Computes deterministic structural forces (Varga, Bhava, Aspect, Yoga).
    """

    def __init__(self, embed_dim: int = 64, hidden_dim: int = 128):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.score_head = nn.Linear(hidden_dim, 1)
        self.confidence_head = nn.Linear(hidden_dim, 1)
        self.diag_head = nn.Linear(hidden_dim, 4)

    def forward(self, x_embed: torch.Tensor) -> StructuralExpertOutput:
        h = self.mlp(x_embed)
        score = self.score_head(h)
        confidence = torch.sigmoid(self.confidence_head(h))
        diag = torch.tanh(self.diag_head(h))
        return StructuralExpertOutput(
            score=score,
            confidence=confidence,
            embedding=h,
            diagnostic_vector=diag,
        )


class ResidualMoELayer(nn.Module):
    """
    Section 17.4 & 17.9: Residual Stochastic MoE Layer.
    Soft-gated mixture of K residual experts capturing non-linear stochastic regimes.
    """

    def __init__(self, latent_dim: int, num_experts: int = 4, expert_width: int = 128):
        super().__init__()
        self.num_experts = num_experts
        self.router = nn.Linear(latent_dim, num_experts)

        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(latent_dim, expert_width),
                nn.ReLU(),
                nn.Linear(expert_width, 1),
            )
            for _ in range(num_experts)
        ])

    def forward(self, z: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # Softmax gating weights (Section 17.4)
        gate_logits = self.router(z)
        gating_weights = F.softmax(gate_logits, dim=-1)  # [batch, num_experts]

        # Evaluate each expert
        expert_outputs = torch.stack([exp(z) for exp in self.experts], dim=1)  # [batch, num_experts, 1]
        
        # Weighted combination: sum_k G(z)_k * Expert_k(z)
        weighted_residual = torch.sum(gating_weights.unsqueeze(-1) * expert_outputs, dim=1)  # [batch, 1]

        return weighted_residual, gating_weights


class TypedPhalitaMoE(nn.Module):
    """
    Section 15, 16, 17: Complete Typed Phalita MoE Model.
    Combines Universal Structural Encoders + Mandatory Structural Experts
             + Gated Residual Experts + Fusion Output Heads.
    """

    def __init__(
        self,
        block_dims: Dict[str, int],  # e.g. {"varga": 8, "bhava": 12, "aspect": 6, "yoga": 5, "temporal": 4}
        embed_dim: int = 64,
        num_residual_experts: int = 4,
    ):
        super().__init__()
        self.block_names = list(block_dims.keys())

        # 1. Block Encoders (Section 17.2)
        self.encoders = nn.ModuleDict({
            b_name: BlockEncoder(input_dim=b_dim, embed_dim=embed_dim)
            for b_name, b_dim in block_dims.items()
        })

        # 2. Universal Structural Experts (Section 16.1) — MANDATORY
        self.structural_experts = nn.ModuleDict({
            b_name: UniversalStructuralExpert(embed_dim=embed_dim)
            for b_name in block_dims.keys()
        })

        # 3. Combined Latent Dimension (Section 17.3)
        latent_dim = embed_dim * len(block_dims)

        # 4. Residual Stochastic MoE Layer (Section 17.4)
        self.residual_moe = ResidualMoELayer(
            latent_dim=latent_dim,
            num_experts=num_residual_experts,
        )

        # 5. Fusion Layer & Quantile / Uncertainty Heads (Section 17.6 & 17.9)
        fusion_in = latent_dim + len(block_dims) + 1  # latent + structural scores + residual
        self.fusion_mlp = nn.Sequential(
            nn.Linear(fusion_in, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
        )

        self.mean_head = nn.Linear(64, 1)
        self.logvar_head = nn.Linear(64, 1)
        self.confidence_head = nn.Linear(64, 1)
        self.q10_head = nn.Linear(64, 1)
        self.q50_head = nn.Linear(64, 1)
        self.q90_head = nn.Linear(64, 1)

    def forward(self, block_inputs: Dict[str, torch.Tensor]) -> MoEPredictionOutput:
        batch_size = next(iter(block_inputs.values())).shape[0]

        # 1. Encode Blocks & Run Structural Experts
        embeddings = []
        struct_scores = []

        for b_name in self.block_names:
            x_b = block_inputs[b_name]
            z_b = self.encoders[b_name](x_b)
            embeddings.append(z_b)

            exp_out = self.structural_experts[b_name](z_b)
            struct_scores.append(exp_out.score)

        # Combined Latent Vector (Section 17.3)
        z_combined = torch.cat(embeddings, dim=-1)  # [batch, latent_dim]
        struct_combined = torch.cat(struct_scores, dim=-1)  # [batch, num_blocks]
        total_struct_score = torch.sum(struct_combined, dim=-1, keepdim=True)  # [batch, 1]

        # 2. Residual MoE Soft Routing (Section 17.4)
        residual_score, gating_weights = self.residual_moe(z_combined)

        # 3. Fusion Layer
        fusion_input = torch.cat([z_combined, struct_combined, residual_score], dim=-1)
        h_fuse = self.fusion_mlp(fusion_input)

        # 4. Predictions: Structural + Residual + Multi-head adjustments
        base_prediction = total_struct_score + residual_score + self.mean_head(h_fuse)
        logvar = self.logvar_head(h_fuse)
        variance = torch.exp(torch.clamp(logvar, min=-6.0, max=4.0))
        confidence = torch.sigmoid(self.confidence_head(h_fuse))

        # Quantile heads (Q10, Q50, Q90 per Section 17.9)
        q50 = base_prediction + self.q50_head(h_fuse)
        q10 = q50 - 1.28 * torch.sqrt(variance) + self.q10_head(h_fuse)
        q90 = q50 + 1.28 * torch.sqrt(variance) + self.q90_head(h_fuse)

        return MoEPredictionOutput(
            mean=base_prediction,
            variance=variance,
            confidence=confidence,
            q10=q10,
            q50=q50,
            q90=q90,
            gating_weights=gating_weights,
            structural_score=total_struct_score,
            residual_score=residual_score,
        )
