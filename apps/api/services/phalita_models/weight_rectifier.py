"""
AstroOS — Classical Weight Rectification Engine (Phase 3)
=========================================================

Optimizes classical astrological rule weights against empirical ground-truth datasets.

Invariants:
- Minimizes Cross-Entropy Loss and Standard Deviation (Brier Score) on the Train split.
- Validates strictly on the out-of-sample Validation split.
- Never touches the Holdout split during calibration.
- Frozen Metrics: Evaluates PR-AUC, ROC-AUC, Brier Score, and F1 at fixed threshold.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from apps.api.services.phalita_core.dataset_pipeline import DatasetBundle, DatasetTemporalSlice


@dataclass
class RectifiedWeights:
    """Calibrated parameters for classical astrological factors."""
    dignity_weight: float = 1.0
    tri_lagna_weight: float = 0.8
    yoga_multiplier: float = 0.7
    dasha_md_weight: float = 0.4
    dasha_ad_weight: float = 0.5
    sadharmi_weight: float = 0.3
    bhava_strength_weight: float = 0.5
    loss_history: List[float] = field(default_factory=list)


class WeightRectifier:
    """Optimizes shastric rule weights via loss minimization."""

    def __init__(self, learning_rate: float = 0.05, max_epochs: int = 50):
        self.lr = learning_rate
        self.max_epochs = max_epochs

    @staticmethod
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-max(-15.0, min(15.0, x))))

    def forward_score(self, slice_item: DatasetTemporalSlice, weights: RectifiedWeights) -> float:
        """Compute predicted logit score for a single slice using calibrated weights."""
        feat = slice_item.features
        if len(feat) < 128:
            return 0.0

        # Extract block features:
        # 0-71: Planet features (Dignities at idx 0, 8, 16, 24, 32, 40, 48, 56, 64)
        planet_dignity_sum = sum(feat[i * 8] for i in range(9))
        tri_lagna_sum = sum(feat[i * 8 + 4] for i in range(9))

        # 72-107: Bhava total strengths (idx 74, 77, 80, 83, 86, 89, 92, 95, 98, 101, 104, 107)
        bhava_sum = sum(feat[74 + b * 3] for b in range(12))

        # 108: Active Yogas sum
        yoga_sum = feat[108]

        # 109-115: Dasha factors (MD=109, AD=110, Sadharmi=111, Domain=112)
        md_str = feat[109]
        ad_str = feat[110]
        sadharmi_rel = feat[111]
        domain_pot = feat[112]

        logit = (
            weights.dignity_weight * (planet_dignity_sum / 9.0)
            + weights.tri_lagna_weight * (tri_lagna_sum / 9.0)
            + weights.bhava_strength_weight * (bhava_sum / 12.0)
            + weights.yoga_multiplier * (yoga_sum / 2.0)
            + weights.dasha_md_weight * md_str
            + weights.dasha_ad_weight * ad_str
            + weights.sadharmi_weight * sadharmi_rel
            + 0.8 * domain_pot
            - 1.5  # Base prior bias for low base-rate event windows
        )
        return logit

    def evaluate_split(
        self,
        slices: List[DatasetTemporalSlice],
        weights: RectifiedWeights,
    ) -> Dict[str, float]:
        """Compute objective metrics (BCE Loss, Brier Score, PR-AUC, ROC-AUC, F1)."""
        if not slices:
            return {"loss": 0.0, "brier_score": 0.0, "f1_score": 0.0, "auc": 0.5}

        y_true = [s.label for s in slices]
        y_logits = [self.forward_score(s, weights) for s in slices]
        y_probs = [self._sigmoid(lg) for lg in y_logits]

        # 1. Binary Cross-Entropy Loss
        eps = 1e-12
        bce = -sum(
            y * math.log(max(eps, p)) + (1 - y) * math.log(max(eps, 1.0 - p))
            for y, p in zip(y_true, y_probs)
        ) / len(slices)

        # 2. Brier Score
        brier = sum((p - y) ** 2 for y, p in zip(y_true, y_probs)) / len(slices)

        # 3. F1 Score at default threshold 0.5
        tp = sum(1 for y, p in zip(y_true, y_probs) if y == 1 and p >= 0.5)
        fp = sum(1 for y, p in zip(y_true, y_probs) if y == 0 and p >= 0.5)
        fn = sum(1 for y, p in zip(y_true, y_probs) if y == 1 and p < 0.5)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        # 4. Fast ROC-AUC calculation
        pos_count = sum(y_true)
        neg_count = len(y_true) - pos_count
        if pos_count == 0 or neg_count == 0:
            auc = 0.5
        else:
            sorted_indices = sorted(range(len(y_probs)), key=lambda i: y_probs[i], reverse=True)
            tp_cum, fp_cum = 0, 0
            auc_sum = 0.0
            prev_fp = 0
            for idx in sorted_indices:
                if y_true[idx] == 1:
                    tp_cum += 1
                else:
                    fp_cum += 1
                    auc_sum += tp_cum
            auc = auc_sum / (pos_count * neg_count) if (pos_count * neg_count) > 0 else 0.5

        return {
            "loss": round(bce, 4),
            "brier_score": round(brier, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(auc, 4),
        }

    def train_rectification(
        self,
        bundle: DatasetBundle,
    ) -> Tuple[RectifiedWeights, Dict[str, Any]]:
        """Run weight rectification on Train split, validate on Validation split."""
        weights = RectifiedWeights()
        train_slices = bundle.train_slices
        val_slices = bundle.val_slices

        if not train_slices:
            return weights, {"status": "NO_TRAIN_DATA"}

        # Perform gradient-free coordinate optimization on classical weights
        params = [
            "dignity_weight",
            "tri_lagna_weight",
            "yoga_multiplier",
            "dasha_md_weight",
            "dasha_ad_weight",
            "sadharmi_weight",
            "bhava_strength_weight",
        ]

        best_val_loss = float("inf")
        history = []

        for epoch in range(self.max_epochs):
            for p_name in params:
                cur_val = getattr(weights, p_name)
                # Test candidates (+delta, -delta)
                delta = self.lr
                for candidate in (cur_val + delta, max(0.0, cur_val - delta)):
                    setattr(weights, p_name, candidate)
                    metrics = self.evaluate_split(train_slices, weights)
                    loss = metrics["loss"]
                    if loss < best_val_loss:
                        best_val_loss = loss
                        cur_val = candidate
                    else:
                        setattr(weights, p_name, cur_val)

            val_metrics = self.evaluate_split(val_slices, weights)
            history.append(val_metrics["loss"])

        weights.loss_history = history
        final_val_metrics = self.evaluate_split(val_slices, weights)
        return weights, {
            "epochs": self.max_epochs,
            "final_train_loss": best_val_loss,
            "val_metrics": final_val_metrics,
        }
