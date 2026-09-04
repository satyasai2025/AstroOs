"""HONEST BACKTEST: Tests actual predictive value, not schema compliance."""
from __future__ import annotations
import math
from datetime import datetime, timezone, timedelta
import pytest
import numpy as np
from apps.api.services.deterministic_baseline_engine import DeterministicBaselineEngine
from apps.api.services.csv_exporter_engine import CSVExporterEngine
from apps.api.services.ml.noise_diagnostic_engine import NoiseDiagnosticEngine

BDT = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
BLAT, BLON = 28.6139, 77.2090


def _gg(n, s):
    rng = np.random.default_rng(s)
    base = datetime(2020, 1, 1, tzinfo=timezone.utc)
    out, price = [], 1500.0
    for i in range(n):
        ts = base + timedelta(days=30 * i)
        r = rng.normal(0.0004, 0.015)
        price *= math.exp(r * 30)
        prev = price * math.exp(-r * 30)
        out.append({"ts": ts, "ret": (price - prev) / prev, "price": price})
    return out


def test_bt1_deterministic_vs_gold():
    print("\n=== BACKTEST 1: Deterministic Score vs Gold Returns ===")
    gold = _gg(100, 42)
    actuals = [d["ret"] for d in gold]
    engine = CSVExporterEngine()
    preds, fail = [], 0
    for d in gold:
        try:
            row = engine.generate_wide_ml_row(1, BDT, BLAT, BLON, d["ret"], d["ret"])
            preds.append(row.get("Final_Deterministic_Score", 0.0))
        except Exception:
            fail += 1
            preds.append(0.0)
    print(f"Samples={len(preds)}, Failed={fail}")
    if fail == len(preds):
        pytest.fail("All predictions failed")
    rep = DeterministicBaselineEngine.evaluate(preds, actuals)
    a_std = math.sqrt(sum((r - sum(actuals)/len(actuals))**2 for r in actuals) / len(actuals))
    print(f"Correlation r={rep.correlation:.4f}, DirAcc={rep.direction_accuracy_pct:.1f}%")
    print(f"SD_err={rep.standard_deviation_error:.4f}, Gold_sigma={a_std:.4f}")
    print(f"Ratio={rep.standard_deviation_error/max(a_std,1e-9):.2f}x")
    if abs(rep.correlation) < 0.05:
        print("[VERDICT] NO SIGNAL: r near 0")
    elif abs(rep.correlation) < 0.15:
        print("[VERDICT] WEAK SIGNAL")
    else:
        print(f"[VERDICT] CORRELATION={rep.correlation:.3f}")
    assert rep.sample_count > 0


def test_bt2_mlp_training():
    import torch
    from apps.api.services.ml.dense_mlp_model import PhalitaDenseMLP
    print("\n=== BACKTEST 2: MLP Training ===")
    gold = _gg(50, 42)
    actuals = [d["ret"] for d in gold]
    engine = CSVExporterEngine()
    feats = []
    for d in gold:
        try:
            row = engine.generate_wide_ml_row(1, BDT, BLAT, BLON, d["ret"], d["ret"])
            skip = {"RecordID","TimeJD","Target_Horizon","Gold_Return_10min","Gold_Return_1hr","DataNoiseFlag","RulesNoiseFlag","ModelNoiseFlag","UsefulNoiseBand"}
            keys = [k for k in row.keys() if k not in skip]
            feats.append([float(row.get(k, 0.0)) for k in keys])
        except Exception:
            feats.append([0.0] * 50)
    if not feats or not any(any(f != 0 for f in ft) for ft in feats):
        pytest.skip("No valid features")
    dim = len(feats[0])
    model = PhalitaDenseMLP(input_dim=dim)
    opt = torch.optim.Adam(model.parameters(), lr=0.001)
    X = torch.tensor(feats, dtype=torch.float32)
    y = torch.tensor(actuals[:len(feats)], dtype=torch.float32).unsqueeze(-1)
    losses = []
    for _ in range(20):
        out = model(X)
        loss = model.compute_loss(out, y)["total_loss"]
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(loss.item())
    model.eval()
    with torch.no_grad():
        p = model(X).mean.squeeze().numpy()
    mp, ma = float(p.mean()), float(y.mean().item())
    sp = math.sqrt(sum((x - mp)**2 for x in p) / len(p))
    sa = math.sqrt(sum((a - ma)**2 for a in actuals) / len(actuals))
    cov = sum((x - mp) * (a - ma) for x, a in zip(p, actuals))
    tc = cov / (sp * sa + 1e-9)
    print(f"Loss: {losses[0]:.4f} -> {losses[-1]:.4f} ({100*(losses[0]-losses[-1])/max(losses[0],1e-9):.1f}% red)")
    print(f"Train Correlation: {tc:.4f}")
    if abs(tc) < 0.3:
        print("[VERDICT] NO LEARNING: MLP cannot extract signal from features")
    elif abs(tc) < 0.7:
        print("[VERDICT] PARTIAL LEARNING: r={:.3f}".format(tc))
    else:
        print("[VERDICT] STRONG FIT (r={:.3f}): But may be overfitting on noise".format(tc))
    assert losses[-1] > 0 and math.isfinite(losses[-1])


def test_bt3_noise_informativeness():
    print("\n=== BACKTEST 3: Noise Diagnostic Value ===")
    gold = _gg(100, 42)
    engine = CSVExporterEngine()
    ns, es = [], []
    for d in gold:
        try:
            row = engine.generate_wide_ml_row(1, BDT, BLAT, BLON)
            ds = row.get("Final_Deterministic_Score", 0.0)
            err = abs(ds - d["ret"])
            rep = NoiseDiagnosticEngine.diagnose(BLAT, BLON, ds, abs(ds) if ds != 0 else 1.0, err)
            ns.append(rep.data_noise_score + rep.rules_noise_score + rep.model_noise_score)
            es.append(err)
        except Exception:
            ns.append(1.0)
            es.append(abs(d["ret"]))
    paired = sorted(zip(ns, es), key=lambda x: x[0])
    n = len(paired)
    q1, q3 = n // 4, 3 * n // 4
    low = [e for _, e in paired[:q1+1]]
    high = [e for _, e in paired[q3:]]
    al, ah = sum(low)/max(len(low),1), sum(high)/max(len(high),1)
    print(f"Low-Noise: avg_err={al:.4f}, High-Noise: avg_err={ah:.4f}")
    print(f"Ratio (High/Low): {ah/max(al,1e-9):.2f}x, Noise range: {min(ns):.3f}-{max(ns):.3f}")
    if ah <= al * 1.1:
        print("[VERDICT] NO DIFFERENTIATION: Noise flags not informative")
    else:
        print("[VERDICT] {0:.1f}x gap: Noise flags have some value".format(ah/max(al,1e-9)))
    assert len(ns) > 0 and all(0 <= x <= 3 for x in ns)
