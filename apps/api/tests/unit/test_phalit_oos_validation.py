"""
HONEST OUT-OF-SAMPLE VALIDATION FRAMEWORK
==========================================
Walk-forward validation for TPhalitCore.
"""
from __future__ import annotations
import math, random, statistics
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple
import pytest
from apps.api.services.csv_exporter_engine import CSVExporterEngine

# ---- stats helpers ----
def _auc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    if not pos or not neg:
        return 0.5
    wins = 0.0
    for p in pos:
        for n in neg:
            if p > n: wins += 1
            elif p == n: wins += 0.5
    return wins / (len(pos) * len(neg))

def _ranks(xs):
    sorted_idx = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[sorted_idx[j + 1]] == xs[sorted_idx[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[sorted_idx[k]] = avg
        i = j + 1
    return ranks

def _spearman(x, y):
    if len(x) < 3: return 0.0
    rx, ry = _ranks(x), _ranks(y)
    mx = sum(rx) / len(rx)
    my = sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx == 0 or dy == 0: return 0.0
    return num / (dx * dy)

def _perm_pvalue(scores, labels, n=500):
    obs = _auc(scores, labels)
    cnt = 0
    rng = random.Random(0)
    lab = labels[:]
    for _ in range(n):
        rng.shuffle(lab)
        if _auc(scores, lab) >= obs: cnt += 1
    return (cnt + 1) / (n + 1)



# ---- synthetic event cohort ----
def _build_cohort(n=60, seed=7):
    rng = random.Random(seed)
    events = []
    base = datetime(1990, 1, 1, tzinfo=timezone.utc)
    for i in range(n):
        bdt = base + timedelta(days=rng.randint(0, 365 * 60))
        lat = round(8.0 + rng.random() * 30.0, 4)
        lon = round(68.0 + rng.random() * 30.0, 4)
        evt_time = bdt + timedelta(days=rng.randint(15 * 365, 50 * 365))
        # Embed deterministic signal: ~30% positive based on event_time
        # (morning or evening hours, OR weekend)
        rule = (evt_time.hour in (6, 7, 8, 18, 19, 20)) or (evt_time.weekday() in (5, 6))
        events.append({
            "id": i, "birth": bdt, "lat": lat, "lon": lon,
            "event_time": evt_time, "label": 1 if rule else 0,
        })
    return events

# ---- feature extraction ----
def _extract(events):
    engine = CSVExporterEngine()
    feats = []
    for e in events:
        try:
            row = engine.generate_wide_ml_row(
                record_id=e["id"], birth_datetime_utc=e["birth"],
                latitude=e["lat"], longitude=e["lon"],
                gold_return_10min=0.0, gold_return_1hr=0.0,
                target_horizon=int((e["event_time"] - e["birth"]).days),
            )
        except Exception:
            row = {}
        feats.append(row)
    return feats

# ---- walk-forward ----
def _walk_forward(events, feats, n_folds=4):
    order = sorted(range(len(events)), key=lambda i: events[i]["event_time"])
    fold_size = len(order) // (n_folds + 1)
    if fold_size < 2:
        return {"error": "too few events"}
    fold_metrics = []
    all_scores, all_labels = [], []
    for k in range(1, n_folds + 1):
        train_end = fold_size * k
        test_end = min(fold_size * (k + 1), len(order))
        train_idx = [order[i] for i in range(0, train_end)]
        test_idx = [order[i] for i in range(train_end, test_end)]
        if not test_idx or not train_idx: continue
        train_pos = sum(events[i]["label"] for i in train_idx) / len(train_idx)
        test_scores = [feats[i].get("Final_Deterministic_Score", 0.0) for i in test_idx]
        test_labels = [events[i]["label"] for i in test_idx]
        naive_scores = [train_pos] * len(test_idx)
        ph_auc = _auc(test_scores, test_labels)
        naive_auc = _auc(naive_scores, test_labels) if len(set(test_labels)) > 1 else 0.5
        all_scores.extend(test_scores)
        all_labels.extend(test_labels)
        fold_metrics.append({
            "fold": k, "n_test": len(test_idx),
            "n_pos_test": sum(test_labels),
            "base_rate": sum(test_labels) / len(test_labels),
            "phalita_auc": ph_auc, "naive_auc": naive_auc,
        })
    if not all_labels or len(set(all_labels)) < 2:
        return {"error": "no positives in test", "folds": fold_metrics}
    return {
        "folds": fold_metrics,
        "pooled_auc": _auc(all_scores, all_labels),
        "pooled_pvalue": _perm_pvalue(all_scores, all_labels, n=500),
        "n_total": len(all_labels),
        "n_positive": sum(all_labels),
    }

def _feature_ics(feats, labels):
    if len(set(labels)) < 2: return []
    skip = {"RecordID", "TimeJD", "Target_Horizon",
            "Gold_Return_10min", "Gold_Return_1hr",
            "DataNoiseFlag", "RulesNoiseFlag", "ModelNoiseFlag", "UsefulNoiseBand"}
    keys = [k for k in feats[0].keys() if k not in skip]
    out = []
    for k in keys:
        xs = [float(f.get(k, 0.0) or 0.0) for f in feats]
        ic = _spearman(xs, [float(l) for l in labels])
        out.append((k, ic, abs(ic)))
    out.sort(key=lambda r: -r[2])
    return out



# =========================== TESTS ===========================

def test_framework_recovers_known_signal():
    print("\n=== FRAMEWORK SANITY: known-signal recovery ===")
    rng = random.Random(11)
    n = 200
    labels = [1 if rng.random() < 0.3 else 0 for _ in range(n)]
    scores = [float(l) + rng.gauss(0, 0.1) for l in labels]
    auc = _auc(scores, labels)
    p = _perm_pvalue(scores, labels, n=300)
    print(f"  AUC={auc:.3f}  p={p:.4f}")
    assert auc > 0.85, f"framework broken (auc={auc:.3f})"
    assert p < 0.05, f"framework broken (p={p:.4f})"
    print("[OK] framework detects strong signal")


def test_oos_walk_forward():
    print("\n=== OOS WALK-FORWARD: TPhalitCore vs event labels ===")
    events = _build_cohort(n=60, seed=7)
    br = sum(e["label"] for e in events) / len(events)
    print(f"  Events={len(events)}  pos_rate={br:.2%}")
    feats = _extract(events)
    ok = sum(1 for f in feats if f and f.get("Final_Deterministic_Score") is not None)
    print(f"  Features extracted: {ok}/{len(events)}")
    if ok == 0:
        pytest.skip("ephemeris unavailable")
    res = _walk_forward(events, feats, n_folds=4)
    if "error" in res:
        pytest.skip(res["error"])
    print(f"  Pooled AUC={res['pooled_auc']:.3f}  p={res['pooled_pvalue']:.4f}")
    print(f"  Total OOS: {res['n_total']} (pos={res['n_positive']})")
    for fm in res["folds"]:
        print(f"    fold{fm['fold']}: n={fm['n_test']:3d} pos={fm['n_pos_test']:2d} "
              f"base={fm['base_rate']:.2f}  Ph={fm['phalita_auc']:.3f}  "
              f"naive={fm['naive_auc']:.3f}")
    auc, p = res["pooled_auc"], res["pooled_pvalue"]
    if p < 0.05 and auc > 0.55:
        print(f"[VERDICT] SIGNAL: AUC={auc:.3f} p={p:.4f}")
    elif p < 0.05 and auc < 0.45:
        print(f"[VERDICT] ANTI-SIGNAL: AUC={auc:.3f} p={p:.4f}")
    else:
        print(f"[VERDICT] NO OOS SIGNAL: AUC={auc:.3f} p={p:.4f}")
    assert 0 <= auc <= 1
    assert 0 < p <= 1


def test_feature_information_coefficients():
    print("\n=== FEATURE IC: per-feature Spearman ===")
    events = _build_cohort(n=60, seed=13)
    feats = _extract(events)
    labels = [e["label"] for e in events]
    if not feats or not any(feats):
        pytest.skip("no features")
    if len(set(labels)) < 2:
        pytest.skip("no positive labels")
    results = _feature_ics(feats, labels)
    print(f"  Top 10 by |IC|:")
    print(f"  {'Feature':<32} {'IC':>8} {'|IC|':>8}")
    print(f"  {'-'*32} {'-'*8} {'-'*8}")
    for name, ic, a in results[:10]:
        print(f"  {name:<32} {ic:>8.4f} {a:>8.4f}")
    top = results[0] if results else None
    if top and top[2] > 0.20:
        print(f"[VERDICT] '{top[0]}' IC={top[1]:.3f} (suspicious)")
    elif top and top[2] > 0.10:
        print(f"[VERDICT] '{top[0]}' IC={top[1]:.3f} (weak)")
    else:
        print(f"[VERDICT] all |IC| < 0.10 - no linear signal")
    assert len(results) > 0


def test_phalita_vs_constant():
    print("\n=== BASELINE: Phalita vs constant prediction ===")
    events = _build_cohort(n=80, seed=21)
    feats = _extract(events)
    labels = [e["label"] for e in events]
    if len(set(labels)) < 2:
        pytest.skip("no positives")
    ph_scores = [f.get("Final_Deterministic_Score", 0.0) for f in feats]
    ph_auc = _auc(ph_scores, labels)
    const_auc = _auc([1.0] * len(labels), labels)
    lift = ph_auc - const_auc
    print(f"  Phalita AUC={ph_auc:.4f}  Constant={const_auc:.4f}  Lift={lift:+.4f}")
    if lift > 0.05:
        print(f"[VERDICT] Phalita adds {lift:.3f} AUC")
    elif lift < -0.05:
        print(f"[VERDICT] Phalita is {abs(lift):.3f} WORSE than constant")
    else:
        print(f"[VERDICT] Phalita within {abs(lift):.3f} of constant - no value")
    assert 0 <= ph_auc <= 1
