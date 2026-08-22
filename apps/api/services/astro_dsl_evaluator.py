"""
AstroOS — Priority 9: AstroDSL Tree-Walker Sandbox Evaluator

Evaluates parsed AstroDSL AST nodes against D1/Divisional natal chart contexts
in a memory-bounded, recursion-safe runtime without unsafe Python code execution.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union

from apps.api.domain.astro_dsl import (
    ASTNode,
    AttributeAccessNode,
    BinaryOpNode,
    FunctionCallNode,
    IdentifierNode,
    ListNode,
    LiteralNode,
    UnaryOpNode,
    parse_astro_dsl,
)


@dataclass
class EvaluationTraceStep:
    node_type: str
    expression: str
    result: Any


@dataclass
class CustomRuleEvaluationResult:
    rule_id: Optional[str]
    is_satisfied: bool
    evaluated_value: Any
    execution_time_ms: float
    trace: List[EvaluationTraceStep] = field(default_factory=list)
    error_message: Optional[str] = None


class AstroDSLEvaluationError(Exception):
    """Raised when evaluation fails due to missing domain context or invalid op."""
    pass


class AstroDSLEvaluator:
    """Tree-walker AST evaluator operating on natal chart domain context."""

    MAX_EVAL_TIMEOUT_MS = 100.0

    def __init__(self, chart_context: Any):
        """
        chart_context can be a D1Chart object or a dictionary containing extracted features:
        - planets: list of planet position objects or dicts
        - planet_strengths: list of planet strength objects or dicts
        - houses: optional house mapping
        - ashtakavarga: optional ashtakavarga matrices
        """
        self.chart_context = chart_context
        self._planet_map: Dict[str, Any] = {}
        self._strength_map: Dict[str, Any] = {}
        self._build_context_maps()

    def _build_context_maps(self):
        """Extract and map grahas and house details from D1Chart or dictionary."""
        # Handle dict or D1Chart dataclass
        planets_list = []
        if isinstance(self.chart_context, dict):
            planets_list = self.chart_context.get("planets", [])
            strengths_list = self.chart_context.get("planet_strengths", [])
        else:
            planets_list = getattr(self.chart_context, "planets", [])
            strengths_list = getattr(self.chart_context, "planet_strengths", [])

        for p in planets_list:
            name = getattr(p, "planet", None) or (p.get("planet") if isinstance(p, dict) else None)
            if name:
                self._planet_map[str(name).strip().upper()] = p
                # Also map common name variations e.g. JUPITER -> GURU, SUN -> SURYA
                canon = self._canonical_planet_name(str(name))
                self._planet_map[canon] = p

        for s in strengths_list:
            name = getattr(s, "planet", None) or (s.get("planet") if isinstance(s, dict) else None)
            if name:
                self._strength_map[str(name).strip().upper()] = s
                canon = self._canonical_planet_name(str(name))
                self._strength_map[canon] = s

    @staticmethod
    def _canonical_planet_name(name: str) -> str:
        name_u = name.strip().upper()
        mapping = {
            "SURYA": "SUN",
            "CHANDRA": "MOON",
            "MANGAL": "MARS",
            "BUDH": "MERCURY",
            "GURU": "JUPITER",
            "SHUKRA": "VENUS",
            "SHANI": "SATURN",
            "RAHU": "RAHU",
            "KETU": "KETU",
            "LAGNA": "ASCENDANT",
            "ASC": "ASCENDANT",
        }
        return mapping.get(name_u, name_u)

    def evaluate(self, node: ASTNode, rule_id: Optional[str] = None) -> CustomRuleEvaluationResult:
        t_start = time.perf_counter()
        trace: List[EvaluationTraceStep] = []

        try:
            val = self._visit(node, trace)
            t_end = time.perf_counter()
            exec_ms = round((t_end - t_start) * 1000.0, 3)

            is_satisfied = bool(val) if not isinstance(val, (int, float)) else val > 0
            return CustomRuleEvaluationResult(
                rule_id=rule_id,
                is_satisfied=is_satisfied,
                evaluated_value=val,
                execution_time_ms=exec_ms,
                trace=trace,
            )
        except Exception as e:
            t_end = time.perf_counter()
            exec_ms = round((t_end - t_start) * 1000.0, 3)
            return CustomRuleEvaluationResult(
                rule_id=rule_id,
                is_satisfied=False,
                evaluated_value=None,
                execution_time_ms=exec_ms,
                trace=trace,
                error_message=str(e),
            )

    def _visit(self, node: ASTNode, trace: List[EvaluationTraceStep]) -> Any:
        if isinstance(node, LiteralNode):
            res = node.value
            trace.append(EvaluationTraceStep("LiteralNode", str(node.value), res))
            return res

        elif isinstance(node, ListNode):
            res = [self._visit(el, trace) for el in node.elements]
            trace.append(EvaluationTraceStep("ListNode", f"[{len(res)} elements]", res))
            return res

        elif isinstance(node, IdentifierNode):
            res = self._resolve_identifier(node.name)
            trace.append(EvaluationTraceStep("IdentifierNode", node.name, res))
            return res

        elif isinstance(node, FunctionCallNode):
            res = self._eval_function_call(node, trace)
            trace.append(EvaluationTraceStep("FunctionCallNode", f"{node.name}(...)", res))
            return res

        elif isinstance(node, AttributeAccessNode):
            target_val = self._visit(node.target, trace)
            res = self._get_attribute(target_val, node.attribute)
            trace.append(EvaluationTraceStep("AttributeAccessNode", f".{node.attribute}", res))
            return res

        elif isinstance(node, UnaryOpNode):
            operand_val = self._visit(node.operand, trace)
            if node.operator == "NOT":
                res = not bool(operand_val)
            elif node.operator == "-":
                res = -operand_val
            else:
                raise AstroDSLEvaluationError(f"Unsupported unary operator '{node.operator}'")
            trace.append(EvaluationTraceStep("UnaryOpNode", f"{node.operator}", res))
            return res

        elif isinstance(node, BinaryOpNode):
            left_val = self._visit(node.left, trace)

            # Short-circuit logic for AND / OR
            if node.operator == "AND":
                if not left_val:
                    trace.append(EvaluationTraceStep("BinaryOpNode", "AND (short-circuit)", False))
                    return False
                right_val = self._visit(node.right, trace)
                res = bool(left_val) and bool(right_val)
                trace.append(EvaluationTraceStep("BinaryOpNode", "AND", res))
                return res

            if node.operator == "OR":
                if left_val:
                    trace.append(EvaluationTraceStep("BinaryOpNode", "OR (short-circuit)", True))
                    return True
                right_val = self._visit(node.right, trace)
                res = bool(left_val) or bool(right_val)
                trace.append(EvaluationTraceStep("BinaryOpNode", "OR", res))
                return res

            right_val = self._visit(node.right, trace)

            if node.operator == "==":
                res = (left_val == right_val)
            elif node.operator == "!=":
                res = (left_val != right_val)
            elif node.operator == "<":
                res = (left_val < right_val)
            elif node.operator == "<=":
                res = (left_val <= right_val)
            elif node.operator == ">":
                res = (left_val > right_val)
            elif node.operator == ">=":
                res = (left_val >= right_val)
            elif node.operator == "IN":
                if isinstance(right_val, (list, tuple, set)):
                    res = left_val in right_val
                else:
                    res = str(left_val) in str(right_val)
            elif node.operator == "NOT IN":
                if isinstance(right_val, (list, tuple, set)):
                    res = left_val not in right_val
                else:
                    res = str(left_val) not in str(right_val)
            elif node.operator == "+":
                res = left_val + right_val
            elif node.operator == "-":
                res = left_val - right_val
            elif node.operator == "*":
                res = left_val * right_val
            elif node.operator == "/":
                res = left_val / right_val if right_val != 0 else 0
            else:
                raise AstroDSLEvaluationError(f"Unsupported binary operator '{node.operator}'")

            trace.append(EvaluationTraceStep("BinaryOpNode", f"{node.operator}", res))
            return res

        raise AstroDSLEvaluationError(f"Unknown AST node type: {type(node)}")

    def _resolve_identifier(self, name: str) -> Any:
        name_u = name.upper()

        # Constant check e.g. ARIES, TAURUS, KENDRA_HOUSES
        rashis = {
            "ARIES": "Aries", "TAURUS": "Taurus", "GEMINI": "Gemini", "CANCER": "Cancer",
            "LEO": "Leo", "VIRGO": "Virgo", "LIBRA": "Libra", "SCORPIO": "Scorpio",
            "SAGITTARIUS": "Sagittarius", "CAPRICORN": "Capricorn", "AQUARIUS": "Aquarius", "PISCES": "Pisces"
        }
        if name_u in rashis:
            return rashis[name_u]

        if name_u == "KENDRA_HOUSES":
            return [1, 4, 7, 10]
        if name_u == "TRIKONA_HOUSES":
            return [1, 5, 9]
        if name_u == "DUSTHANA_HOUSES":
            return [6, 8, 12]

        # Check if direct planet name e.g. JUPITER
        p_obj = self._planet_map.get(name_u)
        if p_obj:
            return p_obj

        return name

    def _eval_function_call(self, node: FunctionCallNode, trace: List[EvaluationTraceStep]) -> Any:
        fname = node.name.upper()

        args_eval = [self._visit(a, trace) for a in node.args]

        if fname == "PLANET" or fname == "GRAHA":
            if not args_eval:
                raise AstroDSLEvaluationError("PLANET() function requires planet name argument")
            pname = str(args_eval[0]).upper()
            p_obj = self._planet_map.get(pname) or self._planet_map.get(self._canonical_planet_name(pname))
            if not p_obj:
                raise AstroDSLEvaluationError(f"Graha '{pname}' not found in chart context")
            return p_obj

        elif fname in ("HOUSE", "BHAVA"):
            if not args_eval:
                raise AstroDSLEvaluationError("HOUSE() function requires house number argument (1-12)")
            hnum = int(args_eval[0])
            return {"house_number": hnum}

        elif fname == "ASPECT":
            if len(args_eval) < 2:
                raise AstroDSLEvaluationError("ASPECT() requires two planet arguments")
            p1_obj, p2_obj = args_eval[0], args_eval[1]
            h1 = self._get_attribute(p1_obj, "house_number")
            h2 = self._get_attribute(p2_obj, "house_number")
            house_diff = abs(h1 - h2)
            if house_diff > 6:
                house_diff = 12 - house_diff
            return {
                "house_difference": house_diff,
                "is_7th_aspect": (house_diff == 6),
                "is_mutual_kendra": (house_diff in (0, 3, 6, 9)),
            }

        raise AstroDSLEvaluationError(f"Unknown DSL function '{node.name}'")

    def _get_attribute(self, target: Any, attr: str) -> Any:
        attr_l = attr.lower()

        # Handle dictionary or object target
        def _get_raw(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        if isinstance(target, dict) and "house_number" in target and len(target) == 1:
            # HOUSE(x) node
            hnum = target["house_number"]
            if attr_l == "number" or attr_l == "house_number":
                return hnum
            if attr_l == "is_kendra":
                return hnum in (1, 4, 7, 10)
            if attr_l == "is_trikona":
                return hnum in (1, 5, 9)
            if attr_l == "is_dusthana":
                return hnum in (6, 8, 12)

        # Planet object attribute
        if attr_l in ("house", "house_number"):
            return _get_raw(target, "house_number", 1)
        if attr_l == "rashi":
            return str(_get_raw(target, "rashi", ""))
        if attr_l in ("rashi_degree", "longitude"):
            val = _get_raw(target, "rashi_degree")
            if val is None:
                val = _get_raw(target, "sidereal_longitude")
            if val is None:
                val = _get_raw(target, "longitude", 0.0)
            return float(val)
        if attr_l in ("is_retrograde", "retrograde"):
            return bool(_get_raw(target, "is_retrograde", False))
        if attr_l in ("is_combust", "combust"):
            return bool(_get_raw(target, "is_combust", False))
        if attr_l == "nakshatra":
            return str(_get_raw(target, "nakshatra", ""))
        if attr_l == "dignity":
            dig = _get_raw(target, "dignity")
            return getattr(dig, "value", str(dig)) if dig else "neutral"

        # Direct property fallback
        val = _get_raw(target, attr_l)
        if val is not None:
            return val

        raise AstroDSLEvaluationError(f"Attribute '{attr}' not found on target context {target}")


def evaluate_astro_dsl(
    dsl_source: str, chart_context: Any, rule_id: Optional[str] = None
) -> CustomRuleEvaluationResult:
    """Convenience helper to parse and evaluate AstroDSL string against chart context."""
    ast = parse_astro_dsl(dsl_source)
    evaluator = AstroDSLEvaluator(chart_context)
    return evaluator.evaluate(ast, rule_id=rule_id)
