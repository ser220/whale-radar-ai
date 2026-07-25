import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from typing import get_type_hints

import pytest

import app.risk
from app.risk import RiskComponent, RiskFactor, RiskLevel, RiskScore


def build_risk_component() -> RiskComponent:
    return RiskComponent(
        factor=RiskFactor.FUNDING,
        score=42.5,
        level=RiskLevel.MEDIUM,
        reason_code="FUNDING_RATE_ELEVATED",
    )


def test_valid_risk_component_construction() -> None:
    component = build_risk_component()

    assert component.factor is RiskFactor.FUNDING
    assert component.score == 42.5
    assert component.level is RiskLevel.MEDIUM
    assert component.reason_code == "FUNDING_RATE_ELEVATED"


def test_risk_component_fields_are_exact() -> None:
    assert [field.name for field in fields(RiskComponent)] == [
        "factor",
        "score",
        "level",
        "reason_code",
    ]


def test_risk_component_value_equality_and_repeated_construction() -> None:
    first = build_risk_component()
    second = build_risk_component()

    assert first == second
    assert first is not second


def test_risk_component_is_immutable() -> None:
    component = build_risk_component()

    with pytest.raises(FrozenInstanceError):
        component.score = 10.0


def test_risk_component_is_hashable() -> None:
    first = build_risk_component()
    second = build_risk_component()

    assert hash(first) == hash(second)
    assert {first, second} == {first}


def test_risk_factor_members_and_values_are_exact() -> None:
    expected = {
        "FUNDING": "FUNDING",
        "OPEN_INTEREST": "OPEN_INTEREST",
        "LIQUIDITY": "LIQUIDITY",
        "LIQUIDATIONS": "LIQUIDATIONS",
        "CVD": "CVD",
        "WHALE": "WHALE",
        "FLOW": "FLOW",
        "VOLATILITY": "VOLATILITY",
    }

    assert {
        factor.name: factor.value
        for factor in RiskFactor
    } == expected


def test_risk_factor_reconstructs_from_stable_string_values() -> None:
    for factor in RiskFactor:
        assert RiskFactor(factor.value) is factor


def test_risk_component_preserves_supplied_values_exactly() -> None:
    component = RiskComponent(
        factor=RiskFactor.OPEN_INTEREST,
        score=123.75,
        level=RiskLevel.LOW,
        reason_code="  caller supplied reason  ",
    )

    assert component.factor is RiskFactor.OPEN_INTEREST
    assert component.score == 123.75
    assert component.level is RiskLevel.LOW
    assert component.reason_code == "  caller supplied reason  "


def test_reason_code_requires_a_string_without_formatting_policy() -> None:
    with pytest.raises(TypeError, match="reason_code must be a string"):
        RiskComponent(
            factor=RiskFactor.CVD,
            score=1.0,
            level=RiskLevel.LOW,
            reason_code=None,
        )


def test_existing_risk_score_and_risk_level_contracts_are_unchanged() -> None:
    assert [field.name for field in fields(RiskScore)] == [
        "total_score",
        "liquidity_score",
        "funding_score",
        "whale_score",
        "flow_score",
        "volatility_score",
    ]
    assert {
        level.name: level.value
        for level in RiskLevel
    } == {
        "LOW": "LOW",
        "MEDIUM": "MEDIUM",
        "HIGH": "HIGH",
        "EXTREME": "EXTREME",
    }


def test_public_exports_are_minimal_and_resolvable() -> None:
    assert app.risk.__all__ == [
        "RiskComponent",
        "RiskFactor",
        "RiskLevel",
        "RiskScore",
    ]
    assert all(hasattr(app.risk, name) for name in app.risk.__all__)


def test_risk_package_has_no_intelligence_or_decision_imports() -> None:
    package_directory = Path(app.risk.__file__).parent

    for path in package_directory.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.append(node.module)

        assert not any(
            module == "app.intelligence"
            or module.startswith("app.intelligence.")
            or module == "app.decision"
            or module.startswith("app.decision.")
            for module in imported_modules
        )


def test_public_type_hints_resolve_with_python_39_compatible_types() -> None:
    assert get_type_hints(RiskComponent) == {
        "factor": RiskFactor,
        "score": float,
        "level": RiskLevel,
        "reason_code": str,
    }
