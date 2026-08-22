"""
AstroOS — Unit Tests for AstroDSL Parser & Sandbox Evaluator (Priority 9)
"""

import pytest

from apps.api.domain.astro_dsl import (
    AstroDSLLexer,
    AstroDSLParser,
    AstroDSLSyntaxError,
    BinaryOpNode,
    FunctionCallNode,
    LiteralNode,
    parse_astro_dsl,
)
from apps.api.services.astro_dsl_evaluator import (
    AstroDSLEvaluationError,
    AstroDSLEvaluator,
    evaluate_astro_dsl,
)


def test_astro_dsl_lexer_basic():
    source = 'PLANET("Jupiter").house IN [1, 4, 7, 10] AND PLANET("Jupiter").is_combust == FALSE'
    lexer = AstroDSLLexer(source)
    tokens = lexer.tokenize()

    assert len(tokens) > 5
    assert tokens[0].value == "PLANET"
    assert tokens[1].value == "("
    assert tokens[2].value == "Jupiter"


def test_astro_dsl_parser_gajakesari_ast():
    source = 'PLANET("Jupiter").house IN [1, 4, 7, 10]'
    ast = parse_astro_dsl(source)

    assert isinstance(ast, BinaryOpNode)
    assert ast.operator == "IN"
    assert isinstance(ast.left.target, FunctionCallNode)
    assert ast.left.attribute == "house"


def test_astro_dsl_parser_depth_limit_exceeded():
    # Build nested parenthesis exceeding depth limit of 15
    nested = "(" * 20 + "TRUE" + ")" * 20
    with pytest.raises(AstroDSLSyntaxError) as exc_info:
        parse_astro_dsl(nested)
    assert "AST depth limit" in str(exc_info.value)


def test_astro_dsl_evaluator_gajakesari_pass():
    chart_context = {
        "planets": [
            {
                "planet": "JUPITER",
                "house_number": 4,
                "rashi": "Cancer",
                "is_retrograde": False,
                "is_combust": False,
                "sidereal_longitude": 95.5,
            },
            {
                "planet": "MOON",
                "house_number": 1,
                "rashi": "Aries",
                "is_retrograde": False,
                "is_combust": False,
                "sidereal_longitude": 15.2,
            },
        ],
        "planet_strengths": [],
    }

    dsl = 'PLANET("Jupiter").house IN KENDRA_HOUSES AND PLANET("Jupiter").is_combust == FALSE'
    result = evaluate_astro_dsl(dsl, chart_context, rule_id="rule-gajakesari-01")

    assert result.is_satisfied is True
    assert result.evaluated_value is True
    assert result.execution_time_ms >= 0.0
    assert len(result.trace) > 0


def test_astro_dsl_evaluator_custom_yoga_rashi():
    chart_context = {
        "planets": [
            {
                "planet": "MARS",
                "house_number": 10,
                "rashi": "Capricorn",
                "is_retrograde": False,
                "is_combust": False,
            }
        ],
        "planet_strengths": [],
    }

    dsl = 'PLANET("Mars").rashi == "Capricorn" AND PLANET("Mars").house == 10'
    result = evaluate_astro_dsl(dsl, chart_context)

    assert result.is_satisfied is True


def test_astro_dsl_evaluator_unknown_planet_error():
    chart_context = {"planets": [], "planet_strengths": []}
    dsl = 'PLANET("Pluto").house == 1'
    result = evaluate_astro_dsl(dsl, chart_context)

    assert result.is_satisfied is False
    assert result.error_message is not None
    assert "PLUTO" in result.error_message.upper()
