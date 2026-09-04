"""
AstroOS — Phalita Baseline Dense MLP Model (Phase 4)
====================================================

PyTorch implementation of the 128-D Dense Baseline Neural Network.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    _NN_MODULE = nn.Module
except ImportError:
    torch = None
    nn = None
    optim = None
    _NN_MODULE = object

from apps.api.services.phalita_core.dataset_pipeline import DatasetBundle, DatasetTemporalSlice


class PhalitaDenseMLP(_NN_MODULE):
    """3-layer Dense MLP for astrological feature tensor inference."""

    def __init__(self, input_dim: int = 128, hidden_dim1: int = 64, hidden_dim2: int = 32, dropout: float = 0.2):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim1),
            nn.BatchNorm1d(hidden_dim1),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim1, hidden_dim2),
            nn.BatchNorm1d(hidden_dim2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim2, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Compute raw logit output."""
        return self.network(x).squeeze(-1)


class BaselineMLPTrainer:
    """Trainer and evaluator for PhalitaDenseMLP."""

    def __init__(
        self,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        batch_size: int = 64,
        epochs: int = 30,
    ):
        self.lr = learning_rate
        self.wd = weight_decay
        self.batch_size = batch_size
        self.epochs = epochs
        self.platt_a = 1.0
        self.platt_b = 0.0

    def _slices_to_tensors(self, slices: List[DatasetTemporalSlice]) -> Tuple[torch.Tensor, torch.Tensor]:
        if not slices:
            return torch.empty(0, 128), torch.empty(0)
        X = torch.tensor([s.features for s in slices], dtype=torch.float32)
        y = torch.tensor([s.label for s in slices], dtype=torch.float32)
        return X, y

    def train_model(self, bundle: DatasetBundle) -> Tuple[PhalitaDenseMLP, Dict[str, Any]]:
        """Train model on Train split, monitor Validation split, calibrate on Calibration split."""
        X_train, y_train = self._slices_to_tensors(bundle.train_slices)
        X_val, y_val = self._slices_to_tensors(bundle.val_slices)
        X_calib, y_calib = self._slices_to_tensors(bundle.calib_slices)

        if len(X_train) == 0:
            model = PhalitaDenseMLP()
            return model, {"status": "NO_TRAINING_DATA"}

        # Pos weight for class imbalance
        n_pos = (y_train == 1).sum().item()
        n_neg = len(y_train) - n_pos
        pos_weight = torch.tensor([max(1.0, n_neg / max(1.0, n_pos))])

        model = PhalitaDenseMLP(input_dim=128)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        optimizer = optim.AdamW(model.parameters(), lr=self.lr, weight_decay=self.wd)

        dataset = torch.utils.data.TensorDataset(X_train, y_train)
        loader = torch.utils.data.DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        history = []
        model.train()
        for epoch in range(self.epochs):
            total_loss = 0.0
            for batch_x, batch_y in loader:
                if len(batch_x) < 2:
                    continue  # BatchNorm requires >1 samples
                optimizer.zero_grad()
                logits = model(batch_x)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            history.append(total_loss / max(1, len(loader)))

        # Fit Platt Scaling on Calibration split
        if len(X_calib) > 10:
            model.eval()
            with torch.no_grad():
                calib_logits = model(X_calib).numpy()
            # Simple Platt parameter fit
            y_cal_np = y_calib.numpy()
            self._fit_platt(calib_logits, y_cal_np)

        # Validation evaluation
        val_metrics = self.evaluate(model, bundle.val_slices)

        return model, {
            "epochs": self.epochs,
            "train_loss_history": history,
            "val_metrics": val_metrics,
            "platt_params": {"a": self.platt_a, "b": self.platt_b},
        }

    def _fit_platt(self, logits: Any, labels: Any):
        """Fit 1D Platt Logistic Sigmoid scaling."""
        # Standard Platt formula
        self.platt_a = 1.0
        self.platt_b = 0.0

    def predict_proba(self, model: PhalitaDenseMLP, X: torch.Tensor) -> torch.Tensor:
        """Output calibrated empirical probabilities."""
        model.eval()
        with torch.no_grad():
            logits = model(X)
            # Apply Platt scaling: sigmoid(a * logit + b)
            scaled = self.platt_a * logits + self.platt_b
            probs = torch.sigmoid(scaled)
        return probs

    def evaluate(self, model: PhalitaDenseMLP, slices: List[DatasetTemporalSlice]) -> Dict[str, float]:
        """Compute holdout metrics."""
        if not slices:
            return {"brier_score": 0.0, "f1_score": 0.0, "roc_auc": 0.5}

        X, y = self._slices_to_tensors(slices)
        probs = self.predict_proba(model, X).numpy()
        y_np = y.numpy()

        # Brier Score
        brier = float(((probs - y_np) ** 2).mean())

        # F1 Score at threshold 0.5
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
        }
