"""
AstroOS — Typed Phalita Mixture of Experts (MoE) Neural Engine (Phase 5)
========================================================================

Architecture:
1. Gating Network (Router): Softmax attention across specialized experts.
2. Expert 1 (Natal Structural): D1 Grahas, Bhavas, Kendras/Trikonas.
3. Expert 2 (Divisional & Yogas): Raja/Dhana/VRY Yogas and Harmonic balance.
4. Expert 3 (Temporal & Dasha): 5-Level Vimshottari confluence + Sadharmi angular interactions.
5. Residual Fusion Layer: Blends expert representations with diagnostic tracking.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    _NN_MODULE = nn.Module
except ImportError:
    torch = None
    nn = None
    F = None
    optim = None
    _NN_MODULE = object

from apps.api.services.phalita_core.dataset_pipeline import DatasetBundle, DatasetTemporalSlice


class StructuralExpert(_NN_MODULE):
    """Specializes in D1 planetary positions and house lordship structures."""
    def __init__(self, input_dim: int = 108, hidden_dim: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x is first 108 features (0 to 107)
        return self.net(x[:, :108]).squeeze(-1)


class YogaDivisionalExpert(_NN_MODULE):
    """Specializes in classical Yogas, cancellations, and composite dignity."""
    def __init__(self, input_dim: int = 37, hidden_dim: int = 32):
        super().__init__()
        if nn:
            self.net = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.15),
                nn.Linear(hidden_dim, 1),
            )

    def forward(self, x: Any) -> Any:
        # x is features 72 to 108 (37 features)
        return self.net(x[:, 72:109]).squeeze(-1)


class TemporalDashaExpert(_NN_MODULE):
    """Specializes in active Vimshottari levels, Sadharmi angles, and transit timings."""
    def __init__(self, input_dim: int = 20, hidden_dim: int = 32):
        super().__init__()
        if nn:
            self.net = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.15),
                nn.Linear(hidden_dim, 1),
            )

    def forward(self, x: Any) -> Any:
        # x is features 108 to 127 (20 features)
        return self.net(x[:, 108:128]).squeeze(-1)


class PhalitaMoE(_NN_MODULE):
    """Typed Mixture of Experts for astrological inference."""

    def __init__(
        self,
        input_dim: int = 128,
        hidden_dim: int = 64,
        router_hidden: int = 32,
        dropout: float = 0.20,
    ):
        super().__init__()
        self.input_dim = input_dim
        if nn:
            # 1. Specialized Experts
            self.expert_structural = StructuralExpert(input_dim=108, hidden_dim=hidden_dim // 2)
            self.expert_divisional = YogaDivisionalExpert(input_dim=37, hidden_dim=hidden_dim // 2)
            self.expert_temporal = TemporalDashaExpert(input_dim=20, hidden_dim=hidden_dim // 2)

            # 2. Attention-based Gating Router
            self.router = nn.Sequential(
                nn.Linear(input_dim, router_hidden),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(router_hidden, 3),  # 3 expert routing logits
            )

            # 3. Residual Fusion Linear Layer
            self.fusion = nn.Sequential(
                nn.Linear(3 + input_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, 1),
            )

    def forward(self, x: Any) -> Tuple[Any, Any]:
        """
        Forward pass.
        Returns:
            fused_logit: shape [B]
            router_weights: shape [B, 3] (routing distribution across experts)
        """
        # Expert predictions
        pred_struct = self.expert_structural(x)    # [B]
        pred_div = self.expert_divisional(x)        # [B]
        pred_temp = self.expert_temporal(x)          # [B]

        # Stack expert predictions
        expert_stack = torch.stack([pred_struct, pred_div, pred_temp], dim=1)  # [B, 3]

        # Gating distribution
        router_logits = self.router(x)               # [B, 3]
        router_weights = F.softmax(router_logits, dim=-1)  # [B, 3]

        # Weighted expert combination
        weighted_expert = torch.sum(expert_stack * router_weights, dim=-1, keepdim=True)  # [B, 1]

        # Concatenate residual input features
        fusion_input = torch.cat([expert_stack, x], dim=-1)  # [B, 3 + input_dim]
        fused_logit = self.fusion(fusion_input).squeeze(-1) + weighted_expert.squeeze(-1)

        return fused_logit, router_weights


class BinaryFocalLoss(_NN_MODULE):
    """
    Binary Focal Loss for severe class imbalance.
    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)
    """
    def __init__(self, alpha: float = 0.75, gamma: float = 2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = torch.sigmoid(logits)
        eps = 1e-8
        probs = torch.clamp(probs, min=eps, max=1.0 - eps)
        p_t = probs * targets + (1.0 - probs) * (1.0 - targets)
        alpha_t = self.alpha * targets + (1.0 - self.alpha) * (1.0 - targets)
        focal_weight = alpha_t * ((1.0 - p_t) ** self.gamma)
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        return (focal_weight * bce).mean()


class PhalitaMoETrainer:
    """Trainer and Evaluator for PhalitaMoE."""

    def __init__(
        self,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        batch_size: int = 64,
        epochs: int = 35,
        focal_gamma: float = 2.0,
        focal_alpha: float = 0.75,
    ):
        self.lr = learning_rate
        self.wd = weight_decay
        self.batch_size = batch_size
        self.epochs = epochs
        self.focal_gamma = focal_gamma
        self.focal_alpha = focal_alpha
        self.temperature = 1.0

    def _slices_to_tensors(self, slices: List[DatasetTemporalSlice]) -> Tuple[torch.Tensor, torch.Tensor]:
        if not slices:
            return torch.empty(0, 128), torch.empty(0)
        X = torch.tensor([s.features for s in slices], dtype=torch.float32)
        y = torch.tensor([s.label for s in slices], dtype=torch.float32)
        return X, y

    def train_moe(self, bundle: DatasetBundle) -> Tuple[PhalitaMoE, Dict[str, Any]]:
        """Train MoE with router load-balancing and Focal Loss."""
        X_train, y_train = self._slices_to_tensors(bundle.train_slices)
        X_val, y_val = self._slices_to_tensors(bundle.val_slices)
        X_calib, y_calib = self._slices_to_tensors(bundle.calib_slices)

        if len(X_train) == 0:
            model = PhalitaMoE()
            return model, {"status": "NO_TRAIN_DATA"}

        model = PhalitaMoE(input_dim=128)
        criterion = BinaryFocalLoss(alpha=self.focal_alpha, gamma=self.focal_gamma)
        optimizer = optim.AdamW(model.parameters(), lr=self.lr, weight_decay=self.wd)

        dataset = torch.utils.data.TensorDataset(X_train, y_train)
        loader = torch.utils.data.DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        history = []
        model.train()
        for epoch in range(self.epochs):
            total_loss = 0.0
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                logits, gates = model(batch_x)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            history.append(total_loss / max(1, len(loader)))

        val_metrics = self.evaluate(model, bundle.val_slices)
        return model, {
            "epochs": self.epochs,
            "loss_history": history,
            "val_metrics": val_metrics,
        }

    def evaluate(self, model: PhalitaMoE, slices: List[DatasetTemporalSlice]) -> Dict[str, Any]:
        """Evaluate MoE with expert attention breakdown."""
        if not slices:
            return {"brier_score": 0.0, "f1_score": 0.0, "expert_shares": [0.33, 0.33, 0.33]}

        X, y = self._slices_to_tensors(slices)
        model.eval()
        with torch.no_grad():
            logits, gates = model(X)
            probs = torch.sigmoid(logits).numpy()
            gate_shares = gates.mean(dim=0).tolist()

        y_np = y.numpy()
        brier = float(((probs - y_np) ** 2).mean())

        preds = (probs >= 0.5).astype(int)
        tp = int(((preds == 1) & (y_np == 1)).sum())
        fp = int(((preds == 1) & (y_np == 0)).sum())
        fn = int(((preds == 0) & (y_np == 1)).sum())
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        return {
            "brier_score": round(brier, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "expert_attention_shares": {
                "structural_d1": round(gate_shares[0], 3),
                "divisional_yogas": round(gate_shares[1], 3),
                "temporal_dasha": round(gate_shares[2], 3),
            },
        }
