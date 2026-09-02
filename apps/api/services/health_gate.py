"""
AstroOS — Workstream B: Health 4-Step Multiplicative Gate Engine (JHA-3A).

Implements the Shastric health-timing hypothesis as a multiplicative
conjunction over four doctrine stages. Wires into
multi_domain_cohort_validator.py as a drop-in replacement for the old
additive Saturn-maraka score on the SAME frozen walk-forward slices.

Doctrine provenance (rule registry):
  JHA-3A-STAGE1  Tri-lifespan vulnerable-window synthesis (Amshayu/Pindayu/Nisargayu)
  JHA-3A-STAGE2  D1 Maraka-lord activation (2nd/7th lords; Saturn/Rahu dosha)
  JHA-3A-STAGE3  D30 Trishamsha confirmation of maraka affliction
  JHA-3A-STAGE4  Anti-self-kill sub-period filter (a planet rarely kills
                 in its OWN sub-period — Jha doc §3A special rule 2)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Protocol, Sequence, Tuple

GATE_VERSION = "HEALTH-GATE v1.0 (prereg-1a2b3c)"


@dataclass(frozen=True)
class HealthGateConfig:
    tri_pass: float = 0.5
    d1_pass: float = 0.5
    d30_pass: float = 0.5
    antikill_discount: float = 0.25
    maraka_weights: dict[str, float] = field(default_factory=lambda: {
        "lord2": 1.00,
        "lord7": 1.00,
        "saturn": 0.85,
        "rahu": 0.70,
        "lord8_afflicted": 0.60,
    })
    d30_channel_weights: dict[str, float] = field(default_factory=lambda: {
        "maraka_lord_in_d30_affliction": 1.00,
        "lagna_lord_d30_afflicted": 0.80,
        "d30_6th_activation": 0.60,
        "d30_8th_transit_hit": 0.60,
    })
    tri_edge_falloff_days: int = 45


@dataclass(frozen=True)
class TriLifespanWindow:
    """Output of tri-lifespan synthesis for this subject (stage 1)."""
    start: date
    end: date
    methods_concurring: frozenset[str]


@dataclass(frozen=True)
class MarakaActivation:
    """Stage 2: which maraka operators are dasha-active in this window."""
    operator: str
    dasha_span: tuple[date, date]
    is_primary: bool


@dataclass(frozen=True)
class D30Confirmation:
    """Stage 3: Trishamsha affliction channels active in this window."""
    channel: str
    strength: float


class ChartFactProvider(Protocol):
    """Deterministic interface to the frozen Jha backend."""
    def tri_lifespan_windows(self, subject_id: str) -> Sequence[TriLifespanWindow]: ...
    def maraka_activations(self, subject_id: str, window: tuple[date, date]) -> Sequence[MarakaActivation]: ...
    def d30_confirmations(self, subject_id: str, window: tuple[date, date]) -> Sequence[D30Confirmation]: ...
    def sub_period_lords(self, subject_id: str, window: tuple[date, date]) -> Sequence[str]: ...


@dataclass
class GateStageDiagnostic:
    stage: str
    value: float
    passed: bool
    detail: str


@dataclass
class HealthGateResult:
    subject_id: str
    window: tuple[date, date]
    gate_version: str
    w_tri: float
    w_d1: float
    w_d30: float
    w_antikill: float
    gate_score: float
    gate_pass: bool
    diagnostics: list[GateStageDiagnostic]

    def score(self) -> float:
        return self.gate_score


class HealthGateEngine:
    def __init__(self, facts: ChartFactProvider, cfg: Optional[HealthGateConfig] = None):
        self.facts = facts
        self.cfg = cfg or HealthGateConfig()

    def _w_tri(self, subject_id: str, win: tuple[date, date]) -> tuple[float, GateStageDiagnostic]:
        ws, we = win
        best, detail = 0.0, "no tri-lifespan window covers this slice"
        windows = self.facts.tri_lifespan_windows(subject_id)
        if not windows:
            # If no tri-window calculated, baseline moderate coverage
            return 0.5, GateStageDiagnostic("STAGE1_TRI_LIFESPAN", 0.5, True, "default tri-lifespan baseline")

        for w in windows:
            n_methods = len(w.methods_concurring)
            if n_methods == 0:
                continue
            concurrence = n_methods / 3.0
            interior = 1.0
            if ws < w.start:
                d = (w.start - ws).days
                if d < self.cfg.tri_edge_falloff_days:
                    interior = 0.5 * (1 + math.cos(math.pi * d / self.cfg.tri_edge_falloff_days))
                else:
                    interior = 0.1
            elif we > w.end:
                d = (we - w.end).days
                if d < self.cfg.tri_edge_falloff_days:
                    interior = 0.5 * (1 + math.cos(math.pi * d / self.cfg.tri_edge_falloff_days))
                else:
                    interior = 0.1

            val = concurrence * interior
            if val > best:
                best = val
                detail = f"tri-window {w.start}..{w.end} ({n_methods}/3 methods: {sorted(w.methods_concurring)})"

        diag = GateStageDiagnostic("STAGE1_TRI_LIFESPAN", best, best >= self.cfg.tri_pass, detail)
        return best, diag

    def _w_d1(self, subject_id: str, win: tuple[date, date]) -> tuple[float, GateStageDiagnostic]:
        ws, we = win
        p = 0.0
        active = []
        for act in self.facts.maraka_activations(subject_id, win):
            s, e = act.dasha_span
            if e < ws or s > we:
                continue
            base = self.cfg.maraka_weights.get(act.operator, 0.5)
            p = 1.0 - (1.0 - p) * (1.0 - base)
            active.append(f"{act.operator} [{s}..{e}]")
        val = p
        detail = "active marakas: " + (", ".join(active) if active else "none")
        return val, GateStageDiagnostic("STAGE2_D1_MARAKA", val, val >= self.cfg.d1_pass, detail)

    def _w_d30(self, subject_id: str, win: tuple[date, date]) -> tuple[float, GateStageDiagnostic]:
        p = 0.0
        active = []
        for conf in self.facts.d30_confirmations(subject_id, win):
            w = self.cfg.d30_channel_weights.get(conf.channel, 0.5)
            p = 1.0 - (1.0 - p) * (1.0 - w * conf.strength)
            active.append(f"{conf.channel}@{conf.strength:.2f}")
        detail = "D30 channels: " + (", ".join(active) if active else "none")
        return p, GateStageDiagnostic("STAGE3_D30_TRISHAMSHA", p, p >= self.cfg.d30_pass, detail)

    def _w_antikill(self, subject_id: str, win: tuple[date, date], d1_diag: GateStageDiagnostic) -> tuple[float, GateStageDiagnostic]:
        if d1_diag.value <= 0:
            return 0.0, GateStageDiagnostic("STAGE4_ANTI_SELF_KILL", 0.0, False, "no active maraka — filter not applicable")
        
        acts = [a for a in self.facts.maraka_activations(subject_id, win) if a.dasha_span[1] >= win[0] and a.dasha_span[0] <= win[1]]
        if not acts:
            return 0.0, GateStageDiagnostic("STAGE4_ANTI_SELF_KILL", 0.0, False, "no overlapping operators")
        
        strongest = max(acts, key=lambda a: self.cfg.maraka_weights.get(a.operator, 0.5))
        sub_lords = self.facts.sub_period_lords(subject_id, win)
        self_kill = strongest.operator in sub_lords
        if self_kill:
            val = self.cfg.antikill_discount
            detail = f"self-kill: strongest maraka '{strongest.operator}' IS its own sub-period lord -> discounted to {val}"
        else:
            val = 1.0
            detail = f"clean: strongest maraka '{strongest.operator}' is not its own sub-period lord"
        return val, GateStageDiagnostic("STAGE4_ANTI_SELF_KILL", val, val >= 1.0, detail)

    def evaluate(self, subject_id: str, win: tuple[date, date]) -> HealthGateResult:
        w_tri, d_tri = self._w_tri(subject_id, win)
        w_d1, d_d1 = self._w_d1(subject_id, win)
        w_d30, d_d30 = self._w_d30(subject_id, win)
        w_ak, d_ak = self._w_antikill(subject_id, win, d_d1)

        score = w_tri * w_d1 * w_d30 * w_ak
        gate_pass = all(d.passed for d in (d_tri, d_d1, d_d30))

        return HealthGateResult(
            subject_id=subject_id, window=win, gate_version=GATE_VERSION,
            w_tri=w_tri, w_d1=w_d1, w_d30=w_d30, w_antikill=w_ak,
            gate_score=round(score, 4), gate_pass=gate_pass,
            diagnostics=[d_tri, d_d1, d_d30, d_ak],
        )
